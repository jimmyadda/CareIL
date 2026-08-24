#Tushar Borole
#Python 2.7

from flask import session
from flask_login import current_user
from flask_restful import Resource, Api, request
from package.database import DatabaseManager
class Doctors(Resource):
    """This contain apis to carry out activity with all doctors"""

    def get(self):
        """Retrive list of all the doctor"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        # Each client database has one therapist profile. Clients also use
        # this read endpoint to display their therapist in the portal.
        doctors = conn.execute("SELECT * FROM doctor ORDER BY doc_date DESC").fetchall()
        return doctors



    def post(self):
        """Create the clinic therapist only when no profile exists yet."""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        userid = current_user.get_id()
        existing = conn.execute("SELECT doc_id FROM doctor WHERE userid=? LIMIT 1", (userid,)).fetchone()
        if existing:
            return {"error": "This clinic already has a therapist profile."}, 409

        doctorInput = request.get_json(force=True)
        doc_first_name=doctorInput['doc_first_name']
        doc_last_name = doctorInput['doc_last_name']
        doc_email = doctorInput['doc_email']
        doc_ph_no = doctorInput['doc_ph_no']
        doc_address = doctorInput['doc_address']
        doc_userid = userid
        doctorInput['doc_id']=conn.execute('''INSERT INTO doctor(doc_first_name,doc_last_name,doc_email,doc_ph_no,doc_address,userid)
            VALUES(?,?,?,?,?,?)''', (doc_first_name, doc_last_name,doc_email,doc_ph_no,doc_address,doc_userid)).lastrowid
        account_name = (doc_first_name + " " + doc_last_name).strip()
        conn.execute(
            "UPDATE accounts SET name=?, email=?, phone_number=? WHERE userid=?",
            (account_name, doc_email, doc_ph_no, userid)
        )
        conn.commit()
        return doctorInput

class Doctor(Resource):
    """It include all the apis carrying out the activity with the single doctor"""


    def get(self,id):
        """get the details of the docktor by the doctor id"""

        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        doctor = conn.execute(
            "SELECT * FROM doctor WHERE doc_id=? AND userid=?",
            (id, current_user.get_id())
        ).fetchall()
        return doctor

    def delete(self, id):
        """The clinic therapist is retained to preserve appointment history."""
        return {"error": "The clinic therapist profile cannot be deleted."}, 409

    def put(self,id):
        """Update the doctor by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        doctorInput = request.get_json(force=True)
        doc_first_name=doctorInput['doc_first_name']
        doc_last_name = doctorInput['doc_last_name']
        doc_email = doctorInput['doc_email']
        doc_ph_no = doctorInput['doc_ph_no']
        doc_address = doctorInput['doc_address']
        userid = current_user.get_id()
        conn.execute(
            "UPDATE doctor SET doc_first_name=?,doc_last_name=?,doc_email=?,doc_ph_no=?,doc_address=? WHERE doc_id=? AND userid=?",
            (doc_first_name, doc_last_name,doc_email, doc_ph_no, doc_address, id, userid))
        account_name = (doc_first_name + " " + doc_last_name).strip()
        conn.execute(
            "UPDATE accounts SET name=?, email=?, phone_number=? WHERE userid=?",
            (account_name, doc_email, doc_ph_no, userid)
        )
        conn.commit()
        return doctorInput
