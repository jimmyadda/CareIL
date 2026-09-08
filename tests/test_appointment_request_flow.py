import base64
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask, session

from package.appointment import RequestAppointment, RequestAppointments
from package.appointment_notifications import send_appointment_decision
from package.database import DatabaseManager


def temporary_manager(temp_dir):
    base = os.path.join(temp_dir, 'databases')
    config_path = os.path.join(temp_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump({'Global': {
            'BASE_DB_PATH': base,
            'DEFAULT_CLIENT_KEY': 'default_client',
            'DEFAULT_DB_PATH': os.path.join(base, 'CareIL_default_client.db'),
        }}, config_file)
    manager = DatabaseManager(config_file=config_path)
    manager.create_default_database()
    return manager


class AppointmentRequestFlowTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'appointment-flow-test'

    @staticmethod
    def seed(manager):
        conn = manager.connect_to_db('default_client')
        conn.execute(
            "INSERT INTO accounts(userid,password,salt,name,email,client_key,email_verified) "
            "VALUES('karin','x','x','Karin','karin@example.com','default_client',1)"
        )
        conn.execute(
            "INSERT INTO doctor(doc_first_name,doc_last_name,doc_ph_no,doc_email,doc_address,userid) "
            "VALUES('Karin','Adda','1','karin@example.com','Clinic','karin')"
        )
        conn.execute(
            "INSERT INTO patient(pat_first_name,pat_last_name,pat_insurance_no,pat_ph_no,pat_email,pat_address) "
            "VALUES('Test','Client','1','1','client@example.com','Home')"
        )
        conn.commit()
        conn.close()

    def test_pending_request_reserves_slot_and_approval_is_atomic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = temporary_manager(temp_dir)
            self.seed(manager)
            manager_factory = lambda client_key=None: manager
            payload = {'pat_id': 1, 'appointment_date': '2026-08-31 10:00:00', 'language': 'HE'}
            with patch('package.appointment.DatabaseManager', manager_factory):
                with self.app.test_request_context(json=payload):
                    session['client_key'] = 'default_client'
                    first = RequestAppointments().post()
                with self.app.test_request_context(json=payload):
                    session['client_key'] = 'default_client'
                    second = RequestAppointments().post()
                self.assertEqual(second[1], 409)

                with patch('package.appointment.sync_appointment_event', return_value=True), \
                        patch('package.appointment.send_appointment_decision') as notify:
                    with self.app.test_request_context(json={'action': 'approve'}):
                        session['client_key'] = 'default_client'
                        approved = RequestAppointment().post(first['app_id'])

            self.assertTrue(approved['google_synced'])
            self.assertTrue(approved['email_sent'])
            notify.assert_called_once()
            conn = manager.connect_to_db('default_client')
            self.assertEqual(conn.execute('SELECT COUNT(*) AS n FROM appointment').fetchone()['n'], 1)
            self.assertEqual(conn.execute(
                'SELECT status FROM pendingappointment WHERE app_id=?', (first['app_id'],)
            ).fetchone()['status'], 1)
            conn.close()

    def test_confirmation_has_exact_time_duration_google_link_and_ics(self):
        patient = {'pat_first_name': 'Test', 'pat_last_name': 'Client', 'pat_email': 'client@example.com'}
        therapist = {
            'doc_first_name': 'Karin', 'doc_last_name': 'Adda',
            'doc_email': 'karin@example.com', 'doc_ph_no': '1', 'doc_address': 'Haifa',
        }
        with patch('package.appointment_notifications._appointment_data', return_value=(patient, therapist, 75)), \
                patch('package.appointment_notifications._deliver') as deliver:
            send_appointment_decision(
                'client_test', 1, '2026-08-31 10:00:00', True, 'EN', app_id=42
            )
        body = deliver.call_args.args[3]
        attachment = deliver.call_args.args[4][0]
        ics = base64.b64decode(attachment['content']).decode('utf-8')
        self.assertIn('<strong>Time:</strong> 10:00', body)
        self.assertIn('<strong>Duration:</strong> 75 minutes', body)
        self.assertIn('dates=20260831T100000%2F20260831T111500', body)
        self.assertIn('DTSTART:20260831T070000Z', ics)
        self.assertIn('DTEND:20260831T081500Z', ics)
        self.assertIn('UID:careil-appointment-42-', ics)


if __name__ == '__main__':
    unittest.main()
