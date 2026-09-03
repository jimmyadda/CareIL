import hashlib
import os
import re
import tempfile
import unittest
from unittest.mock import patch

import server
from test_saas_features import temporary_manager


class AccessApprovalFlowTest(unittest.TestCase):
    def setUp(self):
        server.app.config.update(TESTING=True, SECRET_KEY='access-approval-test')
        server.app.config.pop('LAST_WORKSPACE_CLEANUP', None)
        self.client = server.app.test_client()

    def test_access_request_creates_only_central_pending_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            with patch.object(server, 'db_manager', manager), \
                    patch.dict(os.environ, {'CAREIL_OWNER_EMAIL': ''}):
                response = self.client.post('/request-access', data={
                    'full_name': 'New Therapist',
                    'email': 'new@example.com',
                    'phone': '0500000000',
                    'clinic_name': 'New Clinic',
                    'plan': 'professional',
                    'lang': 'en',
                })
                self.assertEqual(response.status_code, 200)
                conn = manager.connect_to_db('default_client')
                saved = conn.execute('SELECT * FROM access_requests').fetchone()
                conn.close()
                database_files = [name for name in os.listdir(manager.base_db_path) if name.endswith('.db')]
            self.assertEqual(saved['status'], 'pending')
            self.assertEqual(saved['email'], 'new@example.com')
            self.assertEqual(saved['preferred_plan'], 'professional')
            self.assertEqual(database_files, ['CareIL_default_client.db'])

    def test_only_approved_unexpired_unused_hash_opens_registration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            token = 'private-approved-token'
            conn = manager.connect_to_db('default_client')
            conn.execute(
                """INSERT INTO access_requests
                   (full_name,email,status,token_hash,token_expires_at)
                   VALUES(?,?,'approved',?,datetime('now','+7 days'))""",
                ('New Therapist', 'new@example.com', hashlib.sha256(token.encode()).hexdigest()),
            )
            conn.commit()
            conn.close()
            with patch.object(server, 'db_manager', manager):
                accepted_link = self.client.get('/register?token=' + token)
                allowed = self.client.get('/register')
                denied = self.client.get('/register?token=wrong-token')
            self.assertEqual(accepted_link.status_code, 302)
            self.assertEqual(allowed.status_code, 200)
            self.assertIn(b'new@example.com', allowed.data)
            self.assertEqual(denied.status_code, 403)

    def test_owner_approval_emails_workable_link_and_stores_only_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            conn = manager.connect_to_db('default_client')
            request_id = conn.execute(
                "INSERT INTO access_requests(full_name,email,status) VALUES(?,?,'pending')",
                ('New Therapist', 'new@example.com'),
            ).lastrowid
            conn.commit()
            conn.close()
            with self.client.session_transaction() as browser_session:
                browser_session['access_admin_csrf'] = 'csrf-test'
            with patch.object(server, 'db_manager', manager), \
                    patch.object(server, '_careil_owner', return_value=True), \
                    patch.object(server, '_send_access_email') as send_email, \
                    patch.dict(server.app.config, {'LOGIN_DISABLED': True}):
                response = self.client.post(
                    f'/careil-admin/access-requests/{request_id}/approve',
                    data={'csrf_token': 'csrf-test'},
                )
                email_html = send_email.call_args.args[2]
                token = re.search(r'/register\?token=([^&\"]+)', email_html).group(1)
                link_response = self.client.get('/register?token=' + token)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(link_response.status_code, 302)
            conn = manager.connect_to_db('default_client')
            saved = conn.execute(
                'SELECT status, token_hash FROM access_requests WHERE request_id=?',
                (request_id,),
            ).fetchone()
            conn.close()
            self.assertEqual(saved['status'], 'approved')
            self.assertEqual(saved['token_hash'], hashlib.sha256(token.encode()).hexdigest())
            self.assertNotIn(token, saved['token_hash'])


if __name__ == '__main__':
    unittest.main()
