from functools import wraps
import json
import sqlite3
from flask import session
import flask_login

from package.database import DatabaseManager

#Settings
with open('config.json') as config_file:
    config_data = json.load(config_file)
Globalsetting = config_data['Global'] 
  
mail_settings = config_data['mail_settings']

database_filename = str(Globalsetting['database'])  # Preserve configured legacy database paths.

def database_write(sql,data=None):
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    db = conn.cursor()
    row_affected = 0
    if data:
        row_affected = db.execute(sql, data).rowcount
    else:
        row_affected = db.execute(sql).rowcount
    db.commit()
    db.close()


    return row_affected

def database_read(sql,data=None):
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    db = conn.cursor()

    if data:
         db.execute(sql, data)
    else:
         db.execute(sql)
    records = db.fetchall()    
    rows = [dict(record) for record in records]

    db.close()
    return rows


def admin_only(func):    
    @wraps(func)
    def decorated_function(*args, **kws):
            admin_users = database_read("select * from accounts")
            user = flask_login.current_user.get_dict()
            is_admin= False
            
            if 'userid' in user:
                if any(tag['userid'] == user['userid'] for tag in admin_users):
                    print("in admin user")
                    is_admin= True

            if 'pat_id' in user:
                if any(tag['userid'] == user['pat_id'] for tag in admin_users):
                    print("in admin clientuser")
                    is_admin = True

            if is_admin:
                return func(*args, **kws)
            else:
                return "You don't have authorization to view this page - HTTP Error 403.", 403

    return decorated_function
