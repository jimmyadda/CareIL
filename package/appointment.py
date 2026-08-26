#Python 2.7

import datetime

from flask import current_app, session
from flask_restful import Resource, Api, request
from package.database import DatabaseManager
from package.google_calendar import delete_appointment_event, sync_appointment_event
from package.appointment_notifications import send_appointment_decision


def _single_therapist_id(conn):
    therapist = conn.execute("SELECT doc_id FROM doctor ORDER BY doc_id LIMIT 1").fetchone()
    return therapist["doc_id"] if therapist else None


def _slot_is_available(conn, appointment_date, exclude_pending_id=None):
    confirmed = conn.execute(
        "SELECT 1 FROM appointment WHERE appointment_date=? LIMIT 1",
        (appointment_date,),
    ).fetchone()
    if confirmed:
        return False
    sql = "SELECT 1 FROM pendingappointment WHERE appointment_date=? AND status=0"
    params = [appointment_date]
    if exclude_pending_id is not None:
        sql += " AND app_id<>?"
        params.append(exclude_pending_id)
    return conn.execute(sql + " LIMIT 1", tuple(params)).fetchone() is None


def _slot_is_inside_clinic_hours(conn, appointment_date):
    try:
        requested = datetime.datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return False
    settings = {row['key']: row['value'] for row in conn.execute(
        "SELECT key, value FROM settings WHERE key IN "
        "('AVAILABILITY_DAYS','AVAILABILITY_START','AVAILABILITY_END','APPOINTMENT_DURATION')"
    ).fetchall()}
    allowed_days = {int(day) for day in settings.get('AVAILABILITY_DAYS', '0,1,2,3,4').split(',') if day != ''}
    requested_day = (requested.weekday() + 1) % 7
    start = datetime.datetime.strptime(settings.get('AVAILABILITY_START', '08:00'), '%H:%M').time()
    end = datetime.datetime.strptime(settings.get('AVAILABILITY_END', '18:00'), '%H:%M').time()
    duration = datetime.timedelta(minutes=int(settings.get('APPOINTMENT_DURATION', 60)))
    return requested_day in allowed_days and requested.time() >= start and (requested + duration).time() <= end



class Appointments(Resource):
    """This contain apis to carry out activity with all appiontments"""

    def get(self):
        """Retrive all the appointment and return in form of json"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        appointment = conn.execute("SELECT p.*,d.*,a.* from appointment a LEFT JOIN patient p ON a.pat_id = p.pat_id LEFT JOIN doctor d ON a.doc_id = d.doc_id ORDER BY appointment_date DESC").fetchall()
        return appointment

    def getappointmentsbypatient(self,patid):
        """Retrive list of all the appointment of patient"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        patappointments = conn.execute("SELECT p.*,m.*,d.* from appointment m LEFT JOIN patient p ON m.pat_id = p.pat_id LEFT JOIN doctor d ON m.doc_id = d.doc_id where m.pat_id = ? ORDER BY m.appointment_date DESC", (patid,)).fetchall()
        return patappointments 
    
    def post(self):
        """Create the appoitment by assiciating patient and doctor with appointment date"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        appointment = request.get_json(force=True)
        
        pat_id = appointment['pat_id']
        if session.get('portal_authenticated'):
            pat_id = session.get('portal_pat_id')
            appointment['pat_id'] = pat_id
        pat_Mail = conn.execute("SELECT pat_email FROM patient WHERE pat_id=?",(pat_id,)).fetchall()
        doc_id = _single_therapist_id(conn)
        if doc_id is None:
            return {"error": "Complete the therapist profile before booking appointments."}, 409
        appointment['doc_id'] = doc_id
        appointment['pat_mail'] = pat_Mail
        appointment_date = appointment['appointment_date']
        appointment['app_id'] = conn.execute('''INSERT INTO appointment(pat_id,doc_id,appointment_date) VALUES(?,?,?)''', (pat_id, doc_id,appointment_date)).lastrowid
        conn.commit()
        try:
            sync_appointment_event(client_key, appointment['app_id'])
        except Exception:
            current_app.logger.exception('Google Calendar sync failed for appointment %s', appointment['app_id'])
        return appointment

    
class Appointment(Resource):
    """This contain all api doing activity with single appointment"""

    def get(self,id):
        """retrive a singe appointment details by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        appointment = conn.execute("SELECT * FROM appointment WHERE app_id=?",(id,)).fetchall()
        return appointment

    def delete(self,id):
        """Delete teh appointment by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        try:
            delete_appointment_event(client_key, id)
        except Exception:
            current_app.logger.exception('Google Calendar deletion failed for appointment %s', id)
        conn.execute("DELETE FROM appointment WHERE app_id=?",(id,))
        conn.commit()
        return {'msg': 'sucessfully deleted'}

    def put(self,id):
        """Update the appointment details by the appointment id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        appointment = request.get_json(force=True)
        pat_id = appointment['pat_id']
        doc_id = _single_therapist_id(conn)
        if doc_id is None:
            return {"error": "Complete the therapist profile before updating appointments."}, 409
        appointment['doc_id'] = doc_id
        appointment_date = appointment.get('appointment_date')
        if appointment_date:
            conn.execute("UPDATE appointment SET pat_id=?,doc_id=?,appointment_date=? WHERE app_id=?",
                         (pat_id, doc_id, appointment_date, id))
        else:
            conn.execute("UPDATE appointment SET pat_id=?,doc_id=? WHERE app_id=?",
                         (pat_id, doc_id, id))
        conn.commit()
        try:
            sync_appointment_event(client_key, id)
        except Exception:
            current_app.logger.exception('Google Calendar update failed for appointment %s', id)
        return appointment
    

class RequestAppointments(Resource):
    """This contain apis to carry out activity with all appiontments"""

    def get(self):
        """Retrive all the appointment and return in form of json"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        appointment = conn.execute("SELECT p.*,d.*,a.* from pendingappointment a LEFT JOIN patient p ON a.pat_id = p.pat_id LEFT JOIN doctor d ON a.doc_id = d.doc_id where status = 0 ORDER BY appointment_date DESC").fetchall()
        return appointment

    def getappointmentsbypatient(self,patid):
        """Retrive list of all the appointment of patient"""
        client_key = session.get("clientKey", "default_client")  # Get the client key from the session
        db_manager = DatabaseManager(client_key)  # Create a DatabaseManager instance
        conn = db_manager.connect_to_db()  # Connect to the client's databas         
        patappointments = conn.execute("SELECT p.*,m.*,d.* from pendingappointment m LEFT JOIN patient p ON m.pat_id = p.pat_id LEFT JOIN doctor d ON m.doc_id = d.doc_id where where status = 0 and m.pat_id = ? ORDER BY m.appointment_date DESC", (patid,)).fetchall()
        return patappointments 
    
    def post(self):
        """Create the appoitment by assiciating patient and doctor with appointment date"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
         
        appointment = request.get_json(force=True)
        pat_id = appointment['pat_id']
        if session.get('portal_authenticated'):
            pat_id = session.get('portal_pat_id')
            appointment['pat_id'] = pat_id
        doc_id = _single_therapist_id(conn)
        if doc_id is None:
            return {"error": "Complete the therapist profile before requesting appointments."}, 409
        appointment['doc_id'] = doc_id
        appointment_date = appointment['appointment_date']
        language = str(appointment.get('language') or 'EN').upper()
        try:
            conn.execute('BEGIN IMMEDIATE')
            if not _slot_is_inside_clinic_hours(conn, appointment_date):
                conn.rollback()
                return {"error": "This time is outside the clinic's booking hours."}, 409
            if not _slot_is_available(conn, appointment_date):
                conn.rollback()
                return {"error": "This appointment time is no longer available."}, 409
            appointment['app_id'] = conn.execute(
                '''INSERT INTO pendingappointment(pat_id,doc_id,appointment_date,language)
                   VALUES(?,?,?,?)''',
                (pat_id, doc_id, appointment_date, language),
            ).lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return appointment


class RequestAppointment(Resource):
    """This contain all api doing activity with single appointment"""

    def get(self,id):
        """retrive a singe appointment details by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key) 

        appointment = conn.execute("SELECT * FROM pendingappointment WHERE status = 0 and app_id=?",(id,)).fetchall()
        return appointment

    def delete(self,id):
        """Decline a pending request, retain its audit row, and notify the client."""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        pending = conn.execute(
            "SELECT pat_id, appointment_date, language FROM pendingappointment WHERE app_id=? AND status=0",
            (id,),
        ).fetchone()
        if not pending:
            return {'error': 'Pending appointment request was not found.'}, 404
        conn.execute("UPDATE pendingappointment SET status=2 WHERE app_id=?", (id,))
        conn.commit()
        try:
            send_appointment_decision(
                client_key, pending['pat_id'], pending['appointment_date'], False,
                pending.get('language') or 'EN',
            )
        except Exception:
            current_app.logger.exception('Decline email failed for pending appointment %s', id)
            return {'msg': 'Appointment declined, but the notification email failed.', 'email_sent': False}
        return {'msg': 'Appointment declined and the client was notified.', 'email_sent': True}

    def post(self,id):
        """Atomically accept a pending request, then sync and notify."""
        client_key = session['client_key']
        conn = DatabaseManager(client_key).connect_to_db(client_key)
        try:
            conn.execute('BEGIN IMMEDIATE')
            pending = conn.execute(
                """SELECT pat_id, doc_id, appointment_date, language
                   FROM pendingappointment WHERE app_id=? AND status=0""",
                (id,),
            ).fetchone()
            if not pending:
                conn.rollback()
                return {'error': 'Pending appointment request was not found.'}, 404
            if not _slot_is_available(conn, pending['appointment_date'], exclude_pending_id=id):
                conn.rollback()
                return {'error': 'This appointment time is no longer available.'}, 409
            new_app_id = conn.execute(
                "INSERT INTO appointment(pat_id,doc_id,appointment_date) VALUES(?,?,?)",
                (pending['pat_id'], pending['doc_id'], pending['appointment_date']),
            ).lastrowid
            conn.execute("UPDATE pendingappointment SET status=1 WHERE app_id=?", (id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        google_synced = False
        email_sent = False
        try:
            google_synced = bool(sync_appointment_event(client_key, new_app_id))
        except Exception:
            current_app.logger.exception('Google Calendar sync failed for accepted appointment %s', new_app_id)
        try:
            send_appointment_decision(
                client_key, pending['pat_id'], pending['appointment_date'], True,
                pending.get('language') or 'EN', new_app_id,
            )
            email_sent = True
        except Exception:
            current_app.logger.exception('Confirmation email failed for accepted appointment %s', new_app_id)
        return {
            'msg': 'Appointment accepted.', 'app_id': new_app_id,
            'google_synced': google_synced, 'email_sent': email_sent,
        }

    def approve(self,id):
        """approve teh appointment by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        conn.execute('''INSERT INTO appointment(pat_id,doc_id,appointment_date)
            (SELECT pat_id,doc_id,appointment_date FROM pendingappointment where pat_id=?)''',(id,))
        conn.commit()

        conn.execute("update pendingappointment set status = 1 WHERE app_id=?",(id,))
        conn.commit()
        return {'msg': 'sucessfully deleted'}

    def put(self,id):
        """Update the appointment details by the appointment id"""
        client_key = session.get("clientKey", "default_client")  # Get the client key from the session
        db_manager = DatabaseManager(client_key)  # Create a DatabaseManager instance
        conn = db_manager.connect_to_db()  # Connect to the client's databas 

        appointment = request.get_json(force=True)
        pat_id = appointment['pat_id']
        doc_id = _single_therapist_id(conn)
        if doc_id is None:
            return {"error": "Complete the therapist profile before updating appointments."}, 409
        appointment['doc_id'] = doc_id
        conn.execute("UPDATE pendingappointment SET pat_id=?,doc_id=? WHERE app_id=?",
                     (pat_id, doc_id, id))
        conn.commit()
        return appointment
