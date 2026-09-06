"""CareIL subscription catalogue and provider-neutral checkout records."""

import hashlib
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
                          user_agent):
    offer = selected_offer(plan_code, billing_cycle)
    public_token = secrets.token_urlsafe(32)
    cursor = conn.execute(
        """INSERT INTO billing_orders
           (public_token_hash,full_name,email,phone,clinic_name,language,
            plan_code,billing_cycle,amount,currency,status,requester_ip,user_agent)
           VALUES(?,?,?,?,?,?,?,?,?,?,'pending',?,?)""",
        (token_hash(public_token), full_name, email, phone, clinic_name,
         language, offer["plan_code"], offer["billing_cycle"], offer["amount"],
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
