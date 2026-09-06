import sqlite3
import unittest
import hashlib
import hmac
import json

from package.billing import (
    accept_morning_payment,
    create_checkout_order,
    mark_order_paid,
    parse_morning_payment,
    public_order,
    selected_offer,
    verify_morning_signature,
)


class BillingFlowTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE billing_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_token_hash TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,email TEXT NOT NULL,phone TEXT,
                clinic_name TEXT,language TEXT,country TEXT,billing_address TEXT,
                plan_code TEXT,billing_cycle TEXT,
                amount INTEGER,currency TEXT,status TEXT,provider_session_id TEXT,
                provider_transaction_id TEXT,checkout_url TEXT,receipt_url TEXT,
                next_billing_date TEXT,requester_ip TEXT,user_agent TEXT,
                error_message TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,paid_at TEXT
            );
            CREATE TABLE subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,plan_code TEXT,billing_cycle TEXT,
                status TEXT,provider_subscription_id TEXT UNIQUE,
                current_period_end TEXT,billing_order_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')

    def tearDown(self):
        self.conn.close()

    def test_catalogue_prices(self):
        self.assertEqual(selected_offer('basic', 'monthly')['amount'], 59)
        self.assertEqual(selected_offer('basic', 'annual')['amount'], 590)
        self.assertEqual(selected_offer('professional', 'monthly')['amount'], 89)
        self.assertEqual(selected_offer('professional', 'annual')['amount'], 890)

    def test_paid_webhook_transition_is_idempotent(self):
        order_id, token, _ = create_checkout_order(
            self.conn, full_name='Test Therapist', email='test@example.com',
            phone='', clinic_name='Test Clinic', language='he',
            plan_code='professional', billing_cycle='annual',
            requester_ip='127.0.0.1', user_agent='test',
        )
        self.assertEqual(public_order(self.conn, token)['status'], 'pending')
        paid, created = mark_order_paid(
            self.conn, order_id=order_id, provider_transaction_id='tx-1',
            receipt_url='https://example.test/receipt.pdf',
            next_billing_date='2027-09-04',
        )
        self.assertTrue(created)
        self.assertEqual(paid['status'], 'paid')
        _, created_again = mark_order_paid(
            self.conn, order_id=order_id, provider_transaction_id='tx-1'
        )
        self.assertFalse(created_again)
        subscription = self.conn.execute(
            'SELECT * FROM subscriptions WHERE email=?', ('test@example.com',)
        ).fetchone()
        self.assertEqual(subscription['plan_code'], 'professional')
        self.assertEqual(subscription['billing_cycle'], 'annual')

    def test_signed_morning_payment_is_validated_and_applied(self):
        order_id, _, _ = create_checkout_order(
            self.conn, full_name='Test Therapist', email='test@example.com',
            phone='', clinic_name='Test Clinic', language='he',
            plan_code='basic', billing_cycle='monthly',
            requester_ip='127.0.0.1', user_agent='test',
        )
        raw = json.dumps({
            'id': 'morning-payment-1', 'total': 59,
            'custom': {'careil_order_id': order_id},
            'payer': {'email': 'test@example.com'},
            'transactions': [{'currency': 'ILS'}],
        }, separators=(',', ':')).encode()
        secret = 'webhook-test-secret'
        signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        self.assertTrue(verify_morning_signature(raw, signature, secret))
        payment = parse_morning_payment(raw, 'payment/received')
        paid, created = accept_morning_payment(self.conn, payment)
        self.assertTrue(created)
        self.assertEqual(paid['status'], 'paid')

    def test_morning_payment_rejects_amount_mismatch(self):
        order_id, _, _ = create_checkout_order(
            self.conn, full_name='Test', email='test@example.com', phone='',
            clinic_name='', language='en', plan_code='basic',
            billing_cycle='monthly', requester_ip='', user_agent='',
        )
        raw = json.dumps({
            'id': 'bad-payment', 'total': 58,
            'custom': {'careil_order_id': order_id},
            'transactions': [{'currency': 'ILS'}],
        }).encode()
        with self.assertRaisesRegex(ValueError, 'amount'):
            accept_morning_payment(
                self.conn, parse_morning_payment(raw, 'payment/received')
            )


if __name__ == '__main__':
    unittest.main()
