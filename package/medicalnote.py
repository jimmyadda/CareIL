#Tushar Borole
#Python 2.7

from flask import session
from flask_restful import Resource, Api, request
from package.database import DatabaseManager 
class Medicalnotes(Resource):
    """This contain apis to carry out activity with all Medicalnote"""

    
    def get(self):
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)
        """Retrive list of all the Medicalnote"""
        medicalnote = conn.execute("SELECT * FROM medrecords ORDER BY create_date DESC").fetchall()
        return medicalnote

    def getnotebypatient(self,patid):
        """Retrive list of all the Medicalnote"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        patmedicalnotes = conn.execute("""SELECT p.*,m.*,a.appointment_date
            FROM medrecords m
            LEFT JOIN patient p ON m.pat_id = p.pat_id
            LEFT JOIN appointment a ON m.app_id = a.app_id
            WHERE m.pat_id = ? ORDER BY m.create_date DESC""", (patid,)).fetchall()
        return patmedicalnotes 

    def post(self):
        """Add the new medicalnote"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)


        medicalnoteInput = request.get_json(force=True)
        pat_id = medicalnoteInput['pat_id']
        create_date = medicalnoteInput['create_date']
        body = medicalnoteInput['body']
        app_id = medicalnoteInput.get('app_id') or None
        medicalnoteInput['doc_id']=conn.execute('''INSERT INTO medrecords(pat_id,app_id,create_date,body)
            VALUES(?,?,?,?)''', (pat_id, app_id, create_date,body)).lastrowid
        conn.commit()
        return medicalnoteInput

class Medicalnote(Resource):
    """It include all the apis carrying out the activity with the single note"""

    def get(self,id):
        """get the details of the note by the id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        med_note = conn.execute("SELECT * from  medrecords where rec_id = ?",(id,)).fetchall()
        return med_note

    def delete(self, id):
        """Delete the note by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)

        conn.execute("DELETE FROM medrecords WHERE rec_id=?", (id,))
        conn.commit()
        return {'msg': 'sucessfully deleted'}

    def put(self,id):
        """Update the note by its id"""
        client_key = session['client_key']
        db_manager = DatabaseManager(client_key)
        conn = db_manager.connect_to_db(client_key)


        noteInput = request.get_json(force=True)
        pat_id = noteInput['pat_id']
        create_date = noteInput['create_date']
        body = noteInput['body']
        app_id = noteInput.get('app_id') or None
        conn.execute( 
            "UPDATE medrecords SET pat_id=?,app_id=?,create_date=?,body=? WHERE rec_id=?",
            (pat_id, app_id, create_date, body, id))
        conn.commit()
        return noteInput
