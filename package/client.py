from flask_restful import Resource, Api, request
from package.database import DatabaseManager
import flask_login



class ClientUser(flask_login.UserMixin):
    def __init__(self,pat_id,email,name,client_key):
        self.email = email
        self.name = name
        self.id = pat_id
        self.client_key = client_key
        
    def get_dict(self):
        return{'pat_id': self.id,'email': self.email, 'name': self.name, 'client_key' : self.client_key}