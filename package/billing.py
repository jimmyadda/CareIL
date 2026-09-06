"""CareIL subscription catalogue and provider-neutral checkout records."""

import hashlib
import hmac
import json
import secrets


PLANS = {
    "basic": {
        "name": "Basic",
        "monthly": 59,
        "annual": 590,
    },
    "professional": {
        "name": "Professional",
        "monthly": 89,
        "annual": 890,
    },
}


def selected_offer(plan_code, billing_cycle):
    plan_code = (plan_code or "").strip().lower()
    billing_cycle = (billing_cycle or "").strip().lower()
    if plan_code not in PLANS or billing_cycle not in {"monthly", "annual"}:
        raise ValueError("Invalid CareIL plan or billing cycle.")
    plan = PLANS[plan_code]
    return {
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "billing_cycle": billing_cycle,
        "amount": plan[billing_cycle],
        "currency": "ILS",
    }


def token_hash(token):
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def create_checkout_order(conn, *, full_name, email, phone, clinic_name,
                          language, plan_code, billing_cycle, requester_ip,
                          user_agent, country='', billing_address=''):
    offer = selected_offer(plan_code, billing_cycle)
    public_token = secrets.token_urlsafe(32)
    cursor = conn.execute(
        """INSERT INTO billing_orders
           (public_token_hash,full_name,email,phone,clinic_name,language,
            country,billing_address,plan_code,billing_cycle,amount,currency,
            status,requester_ip,user_agent)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)""",
        (token_hash(public_token), full_name, email, phone, clinic_name,
         language, country, billing_address, offer["plan_code"],
         offer["billing_cycle"], offer["amount"],
         offer["currency"], requester_ip, user_agent[:500]),
    )
    conn.commit()
    return cursor.lastrowid, public_token, offer


def public_order(conn, public_token):
    if not public_token:
        return None
    return conn.execute(
        "SELECT * FROM billing_orders WHERE public_token_hash=? LIMIT 1",
        (token_hash(public_token),),
    ).fetchone()


def record_checkout_session(conn, order_id, provider_session_id, checkout_url):
    conn.execute(
        """UPDATE billing_orders SET provider_session_id=?, checkout_url=?,
                  status='checkout_created', updated_at=CURRENT_TIMESTAMP
           WHERE order_id=? AND status='pending'""",
        (provider_session_id, checkout_url, order_id),
    )
    conn.commit()


def mark_order_paid(conn, *, order_id, provider_transaction_id,
                    receipt_url=None, next_billing_date=None):
    """Idempotently mark a verified provider transaction as paid."""
    row = conn.execute(
        "SELECT * FROM billing_orders WHERE order_id=?", (order_id,)
    ).fetchone()
    if not row:
        raise ValueError("Unknown billing order.")
    if row["status"] == "paid":
        return row, False
    if row["status"] not in {"pending", "checkout_created", "payment_processing"}:
        raise ValueError("Billing order cannot be paid in its current state.")
    conn.execute(
        """UPDATE billing_orders SET status='paid', provider_transaction_id=?,
                  receipt_url=?, next_billing_date=?, paid_at=CURRENT_TIMESTAMP,
                  updated_at=CURRENT_TIMESTAMP WHERE order_id=?""",
        (provider_transaction_id, receipt_url, next_billing_date, order_id),
    )
    conn.execute(
        """INSERT INTO subscriptions
           (email,plan_code,billing_cycle,status,provider_subscription_id,
            current_period_end,billing_order_id)
           VALUES(?,?,?,'active',?,?,?)
           ON CONFLICT(email) DO UPDATE SET plan_code=excluded.plan_code,
             billing_cycle=excluded.billing_cycle,status='active',
             provider_subscription_id=COALESCE(excluded.provider_subscription_id,
                                                subscriptions.provider_subscription_id),
             current_period_end=excluded.current_period_end,
             billing_order_id=excluded.billing_order_id,
             updated_at=CURRENT_TIMESTAMP""",
        (row["email"], row["plan_code"], row["billing_cycle"], None,
         next_billing_date, order_id),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM billing_orders WHERE order_id=?", (order_id,)
    ).fetchone(), True


def verify_morning_signature(raw_body, signature, secret):
    """Verify Morning's hex HMAC-SHA256 signature over the unmodified body."""
    if not raw_body or not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())


def parse_morning_payment(raw_body, topic):
    """Extract the CareIL order reference from a verified Morning payment event.

    CareIL deliberately accepts only payment/received. That event supports custom
    metadata, which lets us correlate a payment to an exact local order. Matching
    a payer merely by email or amount would be unsafe.
    """
    if topic != "payment/received":
        raise ValueError("Unsupported Morning webhook topic.")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid Morning webhook JSON.") from error

    custom = payload.get("custom") or {}
    order_value = custom.get("careil_order_id") or custom.get("order_id")
    try:
        order_id = int(order_value)
    except (TypeError, ValueError) as error:
        raise ValueError("Morning payment is missing careil_order_id metadata.") from error
    if order_id <= 0:
        raise ValueError("Invalid CareIL order reference.")

    transaction_id = str(payload.get("id") or "").strip()
    if not transaction_id:
        raise ValueError("Morning payment is missing its transaction identifier.")
    try:
        total = round(float(payload.get("total")), 2)
    except (TypeError, ValueError) as error:
        raise ValueError("Morning payment total is invalid.") from error

    transactions = payload.get("transactions") or []
    currency = ""
    if transactions and isinstance(transactions[0], dict):
        currency = str(transactions[0].get("currency") or "").upper()
    payer = payload.get("payer") or {}
    return {
        "order_id": order_id,
        "provider_transaction_id": transaction_id,
        "total": total,
        "currency": currency or "ILS",
        "payer_email": str(payer.get("email") or "").strip().lower(),
        "receipt_url": payload.get("receiptUrl") or payload.get("documentUrl"),
    }


def accept_morning_payment(conn, payment):
    """Validate price/currency/email, then perform the idempotent paid transition."""
    order = conn.execute(
        "SELECT * FROM billing_orders WHERE order_id=?", (payment["order_id"],)
    ).fetchone()
    if not order:
        raise ValueError("Unknown CareIL order.")
    if round(float(order["amount"]), 2) != payment["total"]:
        raise ValueError("Morning payment amount does not match the CareIL order.")
    if str(order["currency"]).upper() != payment["currency"]:
        raise ValueError("Morning payment currency does not match the CareIL order.")
    if payment["payer_email"] and payment["payer_email"] != str(order["email"]).lower():
        raise ValueError("Morning payer email does not match the CareIL order.")
    return mark_order_paid(
        conn,
        order_id=payment["order_id"],
        provider_transaction_id=payment["provider_transaction_id"],
        receipt_url=payment.get("receipt_url"),
    )
