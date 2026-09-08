import datetime
import hmac
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import server
from package.database import DatabaseManager


def temporary_manager(temp_dir):
    base = os.path.join(temp_dir, 'databases')
    config_path = os.path.join(temp_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump({
            'Global': {
                'BASE_DB_PATH': base,
                'DEFAULT_CLIENT_KEY': 'default_client',
                'DEFAULT_DB_PATH': os.path.join(base, 'CareIL_default_client.db'),
            }
        }, config_file)
    return DatabaseManager(config_file=config_path)


class SaasFeatureTest(unittest.TestCase):
    def setUp(self):
        server.app.config.update(TESTING=True, SECRET_KEY='saas-feature-test-key')
        server.app.config.pop('LAST_WORKSPACE_CLEANUP', None)
        self.client = server.app.test_client()

    def test_logged_out_home_is_searchable_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Calm clinic management for therapists', response.data)
        self.assertIn(b'/demo/start', response.data)
        self.assertIn(b'href="/he"', response.data)
        self.assertIn(b'class="login-link" href="/login">Log in', response.data)
        self.assertIn(b'class="nav-cta" href="/request-access">Sign up', response.data)
        self.assertIn(b'/static/img/product-dashboard.webp', response.data)
        self.assertIn(b'/static/img/product-clients-mobile.webp', response.data)
        self.assertNotIn('—'.encode('utf-8'), response.data)
        self.assertNotIn('X-Robots-Tag', response.headers)

    def test_hebrew_landing_page_is_rtl_searchable_and_translated(self):
        response = self.client.get('/he')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lang="he" dir="rtl"', response.data)
        self.assertIn('עבודת הקליניקה שלך'.encode('utf-8'), response.data)
        self.assertIn('class="login-link" href="/login">כניסה'.encode('utf-8'), response.data)
        self.assertIn('class="nav-cta" href="/request-access?lang=he">הרשמה'.encode('utf-8'), response.data)
        self.assertIn(b'/static/img/product-dashboard.webp', response.data)
        self.assertIn(b'/static/img/product-clients-mobile.webp', response.data)
        self.assertNotIn('—'.encode('utf-8'), response.data)
        self.assertIn(b'hreflang="he"', response.data)
        self.assertIn(b'href="/"', response.data)
        self.assertNotIn('X-Robots-Tag', response.headers)

    def test_demo_creates_an_isolated_seeded_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            with patch.object(server, 'db_manager', manager):
                response = self.client.post('/demo/start')
                self.assertEqual(response.status_code, 302)
                with self.client.session_transaction() as browser_session:
                    client_key = browser_session['client_key']
                self.assertTrue(client_key.startswith('demo_'))
                conn = manager.connect_to_db(client_key)
                account = conn.execute('SELECT email_verified, is_demo FROM accounts').fetchone()
                client_count = conn.execute('SELECT COUNT(*) AS count FROM patient').fetchone()['count']
                appointment_count = conn.execute('SELECT COUNT(*) AS count FROM appointment').fetchone()['count']
                conn.close()
                self.assertEqual(account['email_verified'], 1)
                self.assertEqual(account['is_demo'], 1)
                self.assertEqual(client_count, 3)
                self.assertEqual(appointment_count, 2)

    def test_existing_account_schema_migrates_without_deleting_data(self):
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE accounts (userid TEXT PRIMARY KEY, name TEXT)')
        conn.execute("INSERT INTO accounts(userid, name) VALUES('Karin', 'Karin')")
        DatabaseManager.ensure_account_verification_schema(conn)
        DatabaseManager.ensure_legal_acceptance_schema(conn)
        columns = {row[1] for row in conn.execute('PRAGMA table_info(accounts)')}
        saved = conn.execute("SELECT userid, name FROM accounts WHERE userid='Karin'").fetchone()
        legal_tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='legal_acceptances'"
        ).fetchone()[0]
        conn.close()
        self.assertTrue({
            'email_verified', 'deletion_requested_at', 'deletion_purge_at',
            'deletion_token_hash', 'is_demo', 'marketing_consent'
        }.issubset(columns))
        self.assertEqual(legal_tables, 1)
        self.assertEqual(saved, ('Karin', 'Karin'))

    def test_public_legal_pages_are_bilingual_and_searchable(self):
        english = self.client.get('/legal/privacy')
        hebrew = self.client.get('/he/legal/privacy')
        self.assertEqual(english.status_code, 200)
        self.assertEqual(hebrew.status_code, 200)
        self.assertIn(b'Privacy Policy', english.data)
        self.assertIn('מדיניות פרטיות'.encode('utf-8'), hebrew.data)
        self.assertNotIn('X-Robots-Tag', english.headers)

    def test_whatsapp_webhook_verifies_signatures_and_deduplicates_events(self):
        payload = {
            'entry': [{'changes': [{'field': 'messages', 'value': {
                'metadata': {'phone_number_id': 'test-phone-id'},
                'statuses': [{'id': 'wamid.test', 'status': 'delivered',
                              'timestamp': '1788800000', 'recipient_id': '972501234567'}],
            }}]}],
        }
        raw_payload = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = 'sha256=' + hmac.new(
            b'meta-test-secret', raw_payload, hashlib.sha256
        ).hexdigest()
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            with patch.object(server, 'db_manager', manager), patch.dict(os.environ, {
                'WHATSAPP_WEBHOOK_VERIFY_TOKEN': 'verify-test-token',
                'META_APP_SECRET': 'meta-test-secret',
            }):
                verified = self.client.get(
                    '/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token='
                    'verify-test-token&hub.challenge=123456'
                )
                rejected = self.client.post(
                    '/webhooks/whatsapp', data=raw_payload,
                    content_type='application/json',
                    headers={'X-Hub-Signature-256': 'sha256=wrong'},
                )
                first = self.client.post(
                    '/webhooks/whatsapp', data=raw_payload,
                    content_type='application/json',
                    headers={'X-Hub-Signature-256': signature},
                )
                second = self.client.post(
                    '/webhooks/whatsapp', data=raw_payload,
                    content_type='application/json',
                    headers={'X-Hub-Signature-256': signature},
                )
                conn = manager.connect_to_db(manager.default_client_key)
                rows = conn.execute(
                    'SELECT * FROM whatsapp_webhook_events'
                ).fetchall()
                conn.close()
        self.assertEqual(verified.data, b'123456')
        self.assertEqual(rejected.status_code, 401)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['delivery_status'], 'delivered')
        self.assertNotIn('972501234567', json.dumps(rows))

    def test_owner_whatsapp_test_sends_without_storing_recipient(self):
        class FakeMetaResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"messages":[{"id":"wamid.test-outbound"}]}'

        captured = {}

        def fake_urlopen(api_request, timeout):
            captured['url'] = api_request.full_url
            captured['body'] = json.loads(api_request.data.decode('utf-8'))
            captured['authorization'] = api_request.headers.get('Authorization')
            captured['timeout'] = timeout
            return FakeMetaResponse()

        with self.client.session_transaction() as browser_session:
            browser_session['whatsapp_test_csrf'] = 'whatsapp-csrf-test'
        with patch.object(server, '_careil_owner', return_value=True), \
                patch.object(server.urllib.request, 'urlopen', side_effect=fake_urlopen), \
                patch.dict(server.app.config, {'LOGIN_DISABLED': True}), \
                patch.dict(os.environ, {
                    'WHATSAPP_ACCESS_TOKEN_TEST': 'private-test-token',
                    'WHATSAPP_PHONE_NUMBER_ID_TEST': '123456789',
                    'WHATSAPP_API_VERSION': 'v26.0',
                }):
            response = self.client.post('/careil-admin/whatsapp-test', data={
                'csrf_token': 'whatsapp-csrf-test',
                'phone': '050-123-4567',
            })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'wamid.test-outbound', response.data)
        self.assertEqual(captured['url'], 'https://graph.facebook.com/v26.0/123456789/messages')
        self.assertEqual(captured['body']['to'], '972501234567')
        self.assertEqual(captured['body']['template']['name'], 'hello_world')
        self.assertEqual(captured['authorization'], 'Bearer private-test-token')
        self.assertNotIn(b'value="972501234567"', response.data)

    def test_whatsapp_test_requires_owner_and_valid_csrf(self):
        with patch.dict(server.app.config, {'LOGIN_DISABLED': True}), \
                patch.object(server, '_careil_owner', return_value=False):
            forbidden = self.client.get('/careil-admin/whatsapp-test')
        with patch.dict(server.app.config, {'LOGIN_DISABLED': True}), \
                patch.object(server, '_careil_owner', return_value=True):
            bad_csrf = self.client.post('/careil-admin/whatsapp-test', data={
                'csrf_token': 'wrong', 'phone': '+972501234567',
            })
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(bad_csrf.status_code, 400)

    def test_owner_can_assign_registered_clinic_professional_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            client_key = 'client_' + hashlib.sha256(b'Karin').hexdigest()
            manager.create_client_database(client_key)
            conn = manager.connect_to_db(client_key)
            conn.execute(
                """INSERT INTO accounts
                   (userid, name, email, client_key, plan_code, email_verified)
                   VALUES(?, ?, ?, ?, 'basic', 1)""",
                ('Karin', 'Karin Adda', 'karin@example.com', client_key),
            )
            conn.commit()
            conn.close()
            with self.client.session_transaction() as browser_session:
                browser_session['clinic_plan_csrf'] = 'plan-csrf-test'
            with patch.object(server, 'db_manager', manager), \
                    patch.object(server, '_careil_owner', return_value=True), \
                    patch.dict(server.app.config, {'LOGIN_DISABLED': True}):
                page = self.client.get('/careil-admin/clinics')
                changed = self.client.post(
                    f'/careil-admin/clinics/{client_key}/plan',
                    data={
                        'csrf_token': 'plan-csrf-test',
                        'plan_code': 'professional',
                    },
                )
            conn = manager.connect_to_db(client_key)
            account = conn.execute(
                "SELECT plan_code, plan_updated_at FROM accounts WHERE userid='Karin'"
            ).fetchone()
            conn.close()
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Karin Adda', page.data)
        self.assertEqual(changed.status_code, 302)
        self.assertEqual(account['plan_code'], 'professional')
        self.assertTrue(account['plan_updated_at'])

    def test_hebrew_content_and_faq_are_public_and_searchable(self):
        articles = self.client.get('/he/articles')
        faq = self.client.get('/he/faq')
        article = self.client.get('/he/articles/nihul-klinika-pratit')
        emotional_therapy = self.client.get('/he/articles/tipul-rigshi-klinika')
        sitemap = self.client.get('/sitemap.xml')
        self.assertEqual(articles.status_code, 200)
        self.assertEqual(faq.status_code, 200)
        self.assertEqual(article.status_code, 200)
        self.assertEqual(emotional_therapy.status_code, 200)
        self.assertNotIn('X-Robots-Tag', articles.headers)
        self.assertNotIn('X-Robots-Tag', faq.headers)
        self.assertIn(b'FAQPage', faq.data)
        self.assertIn('איך לנהל קליניקה פרטית'.encode('utf-8'), article.data)
        self.assertIn(b'/he/articles/nihul-klinika-pratit', sitemap.data)
        self.assertIn('טיפול רגשי'.encode('utf-8'), emotional_therapy.data)
        self.assertIn('מטפלת רגשית'.encode('utf-8'), emotional_therapy.data)
        self.assertIn(b'/he/articles/tipul-rigshi-klinika', sitemap.data)

    def test_hebrew_landing_title_and_footer_branding(self):
        response = self.client.get('/he')
        self.assertIn('CareIL | ניהול קליניקה למטפלים'.encode('utf-8'), response.data)
        self.assertIn(b'Care Israel', response.data)
        self.assertNotIn(b'Care I Love', response.data)
        self.assertIn(b'/he/articles', response.data)
        self.assertIn(b'/he/faq', response.data)

    def test_bilingual_plans_and_essential_cookie_notice(self):
        english = self.client.get('/plans')
        hebrew = self.client.get('/he/plans')
        self.assertEqual(english.status_code, 200)
        self.assertEqual(hebrew.status_code, 200)
        self.assertIn(b'Full plan comparison', english.data)
        self.assertIn('השוואה מלאה בין החבילות'.encode('utf-8'), hebrew.data)
        self.assertIn(b'Automatic transactional emails', english.data)
        self.assertIn(b'Issue receipts through Morning', english.data)
        self.assertIn(b'/request-access?plan=professional', english.data)
        self.assertIn(b'data-cookie-notice', english.data)
        self.assertNotIn(b'Accept all', english.data)

    def test_expired_demo_cleanup_only_removes_demo_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            manager.create_client_database('demo_expired')
            demo_path = manager.get_db_path('demo_expired')
            old_time = (
                datetime.datetime.now().timestamp()
                - datetime.timedelta(hours=3).total_seconds()
            )
            os.utime(demo_path, (old_time, old_time))
            with server.app.app_context(), patch.object(server, 'db_manager', manager):
                server._cleanup_expired_workspaces()
            self.assertFalse(os.path.exists(demo_path))
            self.assertTrue(os.path.exists(manager.get_db_path('default_client')))


if __name__ == '__main__':
    unittest.main()
