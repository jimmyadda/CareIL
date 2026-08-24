import hashlib
import sqlite3
import uuid
import json
from flask import g, session
from package.database import DatabaseManager

#Settings
with open('config.json') as config_file:
    config_data = json.load(config_file)
Globalsetting = config_data['Global'] 
# Legacy database filename is read from config for backward compatibility.
# client_key = Globalsetting['DEFAULT_CLIENT_KEY']
# database_filename = get_db_path(client_key,Globalsetting)
# base_db_path = "./databases/"

def database_write(sql,data=None):
    client_key = session['client_key']  # Get the client key from the session
    db_manager = DatabaseManager(client_key)  # Create a DatabaseManager instance
    conn = db_manager.connect_to_db(client_key=client_key)  # Connect to the client's database
    db = conn.cursor()
    row_affected = 0
    if data:
        print(data) #debug
        row_affected = db.execute(sql, data).rowcount
    else:
        row_affected = db.execute(sql).rowcount
    conn.commit()
    return row_affected

def database_read(sql,data=None):
    client_key = session.get("clientKey", "default_client")  # Get the client key from the session
    db_manager = DatabaseManager(client_key)  # Create a DatabaseManager instance
    conn = db_manager.connect_to_db(client_key=client_key)  # Connect to the client's database
    db = conn.cursor()

    if data:
         db.execute(sql, data)
    else:
         db.execute(sql)
    records = db.fetchall()    
    rows = [dict(record) for record in records]

    #db.close()
    #connection.close()
    return rows

def create_account(userpassed):
    userid = userpassed['userid'] #input("userid: ")
    email = userpassed['email'] #input("email: ")
    name = userpassed['name'] #input("name: ")
    password = userpassed['password'] #getpass.getpass("password: ")
    client_key = userpassed['client_key']
    session['client_key'] = client_key
    print("client_key create acc", session['client_key'])    
    salt = str(uuid.uuid1())
    key = hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt.encode('utf-8'),10000).hex()
    sql = f"Insert into users (userid,client_key) Values (:userid,:client_key);"
    record ={
      "userid": userid,
      "client_key" : client_key
    }
    ok = database_write(sql,record)
    sql = f"Insert into accounts (userid,salt,password,email,name,client_key) Values (:userid,:salt,:password,:email,:name,:client_key);"
    record ={
      "userid": userid,
      "salt": salt,
      "password": key,
      "email": email,
      "name": name,
      "client_key" : client_key
    }
    ok = database_write(sql,record)
    return ok
