import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from package import morning
from test_saas_features import temporary_manager


class MorningReceiptTest(unittest.TestCase):
    def _clinic(self, manager):
        manager.create_default_database()
        conn = manager.connect_to_db('default_client')
        doctor_id = conn.execute('''
            INSERT INTO doctor(doc_first_name,doc_last_name,doc_ph_no,doc_email,doc_address,userid)
            VALUES('Karin','Adda','','karin@example.com','Haifa','karin')
        ''').lastrowid
        patient_id = conn.execute('''
            INSERT INTO patient(pat_first_name,pat_last_name,pat_insurance_no,pat_ph_no,pat_email,pat_address,client_key)
            VALUES('Noa','Levi','123','0500000000','noa@example.com','Haifa','default_client')
        ''').lastrowid
        session_date = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
        app_id = conn.execute(
            'INSERT INTO appointment(pat_id,doc_id,appointment_date) VALUES(?,?,?)',
            (patient_id, doctor_id, session_date + ' 16:00:00'),
        ).lastrowid
        conn.commit()
        conn.close()
        return patient_id, app_id, session_date

    def test_connection_is_validated_and_encrypted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            manager.create_default_database()
            with patch.object(morning, 'DatabaseManager', return_value=manager), \
                    patch.object(morning, '_request_json', return_value={'accessToken': 'token'}), \
                    patch.dict(os.environ, {'THERAPY_SECRET_KEY': 'stable-test-secret'}):
                morning.save_connection('default_client', 'client-id', 'client-secret', 'sandbox')
            conn = manager.connect_to_db('default_client')
            saved = conn.execute('SELECT * FROM morning_connections').fetchone()
            conn.close()
            self.assertEqual(saved['environment'], 'sandbox')
            self.assertNotIn('client-id', saved['client_id_encrypted'])
            self.assertNotIn('client-secret', saved['client_secret_encrypted'])

    def test_receipt_uses_patient_and_session_date_and_prevents_duplicate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            pat_id, app_id, session_date = self._clinic(manager)
            calls = []

            def api(url, method='GET', payload=None, token=None, timeout=25):
                calls.append((url, method, payload, token))
                if url.endswith('/idp/v1/oauth/token'):
                    return {'accessToken': 'access-token'}
                return {
                    'id': 'morning-document-id', 'number': 40017,
                    'url': {'he': 'https://example.test/receipt.pdf'},
                }

            with patch.object(morning, 'DatabaseManager', return_value=manager), \
                    patch.object(morning, '_request_json', side_effect=api), \
                    patch.dict(os.environ, {'THERAPY_SECRET_KEY': 'stable-test-secret'}):
                morning.save_connection('default_client', 'client-id', 'client-secret', 'sandbox')
                result = morning.issue_receipt(
                    'default_client', pat_id, app_id, 350, 4,
                    datetime.date.today().isoformat(), 'he',
                )
                with self.assertRaisesRegex(morning.MorningError, 'already been issued'):
                    morning.issue_receipt(
                        'default_client', pat_id, app_id, 350, 4,
                        datetime.date.today().isoformat(), 'he',
                    )

            document_call = [call for call in calls if call[0].endswith('/documents')][0]
            token_call = [call for call in calls if call[0].endswith('/idp/v1/oauth/token')][0]
            self.assertEqual(token_call[0], 'https://api.sandbox.morning.dev/idp/v1/oauth/token')
            self.assertEqual(document_call[0], 'https://sandbox.d.greeninvoice.co.il/api/v1/documents')
            payload = document_call[2]
            expected_date = datetime.date.fromisoformat(session_date).strftime('%d/%m/%Y')
            self.assertEqual(payload['type'], 400)
            self.assertEqual(payload['client']['name'], 'Noa Levi')
            self.assertEqual(payload['client']['emails'], ['noa@example.com'])
            self.assertEqual(payload['income'][0]['price'], 350)
            self.assertIn(expected_date, payload['income'][0]['description'])
            self.assertEqual(payload['payment'][0]['type'], 4)
            self.assertEqual(result['number'], 40017)
            conn = manager.connect_to_db('default_client')
            saved = conn.execute('SELECT * FROM morning_receipts WHERE app_id=?', (app_id,)).fetchone()
            conn.close()
            self.assertEqual(saved['status'], 'issued')
            self.assertEqual(saved['morning_document_id'], 'morning-document-id')


if __name__ == '__main__':
    unittest.main()
