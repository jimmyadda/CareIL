#Tushar Borole
#Python 2.7

from flask import session
import flask_login
from flask_restful import Resource, Api, request
from package.database import DatabaseManager


class Common(Resource):
    """This contain common api ie noe related to the specific module"""

    def get(self):
        """Retrive the patient,doctor and appointment count for the dashboard page"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        
        getPatientCount=conn.execute("SELECT COUNT(*) AS patient FROM patient").fetchone()
        getDoctorCount = conn.execute("SELECT COUNT(*) AS doctor FROM doctor").fetchone()
        getAppointmentCount = conn.execute("SELECT COUNT(*) AS appointment FROM appointment").fetchone()
        getPatientCount.update(getDoctorCount)
        getPatientCount.update(getAppointmentCount)
        return getPatientCount




