from flask import session
from flask_restful import Resource, Api, request
from package.database import DatabaseManager


class Portal(Resource):
    """This contain common api ie noe related to the specific module"""

    def get(self):
        """Retrive the patient,doctor and appointment count for the dashboard page"""
        client_key = session.get("clientKey", "default_client")  # Get the client key from the session
        db_manager = DatabaseManager(client_key)  # Create a DatabaseManager instance
        conn = db_manager.connect_to_db()  # Connect to the client's databas 
                
        getPatientCount=conn.execute("SELECT COUNT(*) AS patient FROM patient").fetchone()
        getDoctorCount = conn.execute("SELECT COUNT(*) AS doctor FROM doctor").fetchone()
        getAppointmentCount = conn.execute("SELECT COUNT(*) AS appointment FROM appointment").fetchone()
        getPatientCount.update(getDoctorCount)
        getPatientCount.update(getAppointmentCount)
        return getPatientCount