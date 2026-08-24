#Tushar Borole
#Python 2.7

import json
from flask import jsonify, session
from flask_restful import Resource, Api, request
from mail import send_mail
from package.database import DatabaseManager  # Import the DatabaseManager class

notification = "ברוכים הבאים לקליניקה! על מנת להשאר מעודכנים ניתן להתחבר לכתובת /n http://127.0.0.1:5000/login *פרטי ההתחברות הם המייל ומספר הת.ז It contain all the api carryign the activity with aand specific patient"""

class Patients(Resource):

    def get(self):
        """Api to retive all the patient from the database"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        patients = conn.execute("SELECT * FROM patient  ORDER BY pat_date DESC").fetchall()
        return patients
        # patients = conn.execute("SELECT * FROM patient  ORDER BY pat_date DESC").fetchall()
        # patients = json.dumps(patients, indent=4)
        # print("patients",patients)
        # return jsonify(patients) 

    def post(self):
        """api to add the patient in the database"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        patientInput = request.get_json(force=True)

        pat_first_name=patientInput['pat_first_name']
        pat_last_name = patientInput['pat_last_name']
        pat_insurance_no = patientInput['pat_insurance_no']
        pat_dob = patientInput['pat_dob']
        pat_ph_no = patientInput['pat_ph_no']
        pat_email = patientInput['pat_email']
        pat_address = patientInput['pat_address']
        patientInput['pat_id']=conn.execute('''INSERT INTO patient(pat_first_name,pat_last_name,pat_insurance_no,pat_dob,pat_ph_no,pat_email,pat_address,client_key)
            VALUES(?,?,?,?,?,?,?,?)''', (pat_first_name, pat_last_name, pat_insurance_no,pat_dob,pat_ph_no,pat_email,pat_address,client_key)).lastrowid
        conn.commit()
        #send_mail(notification)
        return patientInput

class Patient(Resource):
    """It contains all apis doing activity with the single patient entity"""

    def get(self,id):
        """api to retrive details of the patient by it id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        patient = conn.execute("SELECT * FROM patient WHERE pat_id=?",(id,)).fetchone()
        print("PatientAPI patid: ",patient)
        return patient

    def delete(self,id):
        """api to delete the patiend by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        conn.execute("DELETE FROM patient WHERE pat_id=?",(id,))
        conn.commit()
        return {'msg': 'sucessfully deleted'}

    def put(self,id):
        """api to update the patient by it id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        patientInput = request.get_json(force=True)
        print(patientInput)

        pat_first_name = patientInput['pat_first_name']
        pat_last_name = patientInput['pat_last_name']
        pat_insurance_no = patientInput['pat_insurance_no']
        pat_dob = patientInput['pat_dob']
        pat_ph_no = patientInput['pat_ph_no']
        pat_email = patientInput['pat_email']
        pat_address = patientInput['pat_address']
        conn.execute("UPDATE patient SET pat_first_name=?,pat_last_name=?,pat_insurance_no=?,pat_dob=?,pat_ph_no=?,pat_email=?,pat_address=? WHERE pat_id=?",
                     (pat_first_name, pat_last_name, pat_insurance_no,pat_dob,pat_ph_no,pat_email,pat_address,id))
        conn.commit()
        return patientInput