import datetime
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
