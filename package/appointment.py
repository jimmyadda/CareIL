#Python 2.7

from flask import current_app, session
from flask_restful import Resource, Api, request
from package.database import DatabaseManager
from package.google_calendar import delete_appointment_event, sync_appointment_event


def _single_therapist_id(conn):
    therapist = conn.execute("SELECT doc_id FROM doctor ORDER BY doc_id LIMIT 1").fetchone()
    return therapist["doc_id"] if therapist else None



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
        appointment['app_id'] = conn.execute('''INSERT INTO pendingappointment(pat_id,doc_id,appointment_date)
            VALUES(?,?,?)''', (pat_id, doc_id,appointment_date)).lastrowid
        conn.commit()
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
        """Delete teh appointment by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        print("deleterequet",id)
        conn.execute("DELETE FROM pendingappointment WHERE app_id=?",(id,))
        conn.commit()
        return {'msg': 'sucessfully deleted'}

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
