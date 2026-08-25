import hashlib
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import server
from package.User import User


class RegistrationFlowTest(unittest.TestCase):
    def setUp(self):
        server.app.config.update(TESTING=True, SECRET_KEY='registration-flow-test-key')
        self.client = server.app.test_client()

    def _verification_session(self):
        with self.client.session_transaction() as browser_session:
            browser_session['client_key'] = 'client_test'
            browser_session['pending_verification_userid'] = 'Jimmy'

    @patch.object(server.flask_login, 'login_user')
    @patch.object(server, 'ensure_single_therapist')
    @patch.object(server, 'create_account', return_value=1)
    def test_registration_does_not_log_in_before_verification(
        self, create_account, ensure_single_therapist, login_user
    ):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.object(server.db_manager, 'get_db_path', return_value=os.path.join(temp_dir, 'new.db')), \
                patch.object(server.db_manager, 'create_client_database'), \
                patch.object(server.db_manager, 'connect_to_db', return_value=Mock()):
            response = self.client.post('/register', data={
                'name': 'Jimmy Adda',
                'email': 'jimmy@example.com',
                'userid': 'Jimmy',
                'password': 'test-password',
                'accept_privacy': 'yes',
                'accept_terms': 'yes',
                'accept_dpa': 'yes',
                'legal_language': 'en',
            })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/enter_email', response.data)
        login_user.assert_not_called()

    def test_registration_rejects_missing_required_legal_acceptance(self):
        response = self.client.post('/register', data={
            'name': 'Jimmy Adda',
            'email': 'jimmy@example.com',
            'userid': 'Jimmy',
            'password': 'test-password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Privacy Policy', response.data)

    @patch.object(server, 'database_read')
    def test_unverified_account_cannot_log_in(self, database_read):
        salt = 'test-salt'
        password = 'test-password'
        saved_key = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt.encode(), 10000
        ).hex()
        database_read.return_value = [{
            'userid': 'Jimmy',
            'salt': salt,
            'password': saved_key,
            'email': 'jimmy@example.com',
            'name': 'Jimmy Adda',
            'client_key': 'client_test',
            'email_verified': 0,
        }]

        response = self.client.post('/login', data={
            'userid': 'Jimmy',
            'password': password,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/enter_email', response.data)
        self.assertIn(b'Please verify your email', response.data)

    @patch.object(server, 'send_verification_code', return_value=True)
    @patch.object(server, 'store_verification_code')
    @patch.object(server, 'database_write')
    def test_email_send_displays_code_form(
        self, database_write, store_verification_code, send_verification_code
    ):
        self._verification_session()

        response = self.client.post('/enter_email', data={
            'email': 'jimmy@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="verification_code"', response.data)
        self.assertIn(b'action="/verify"', response.data)
        self.assertNotIn(b'action="/login"', response.data)

    @patch.object(server.flask_login, 'login_user')
    @patch.object(server, 'load_user')
    @patch.object(server, 'database_write')
    @patch.object(server, 'verify_code', return_value=True)
    def test_valid_code_activates_and_logs_in(
        self, verify_code, database_write, load_user, login_user
    ):
        self._verification_session()
        load_user.return_value = User(
            'Jimmy', 'jimmy@example.com', 'Jimmy Adda', 'client_test'
        )

        response = self.client.post('/verify', data={
            'verification_code': 'ABC123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/'))
        database_write.assert_any_call(
            'UPDATE accounts SET email_verified=1 WHERE userid=?',
            ('Jimmy',),
        )
        login_user.assert_called_once_with(load_user.return_value)


if __name__ == '__main__':
    unittest.main()
