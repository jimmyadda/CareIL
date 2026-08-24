import os
import sqlite3
import json

from flask import g, session


def dict_factory(cursor, row):
    """This function formats the JSON when retrieving from the SQLite database."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def initialize_database_schema(conn):
    """
    Initialize database schema for the given connection.
    """
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    ("userid" TEXT PRIMARY KEY,
    "password" TEXT,
    "salt" TEXT,
    "email" TEXT,
    "name" TEXT,
    "client_key" TEXT);''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS patient
    (pat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_first_name TEXT NOT NULL,
    pat_last_name TEXT NOT NULL,
    pat_insurance_no TEXT NOT NULL,
    pat_ph_no TEXT NOT NULL,
    pat_date DATE DEFAULT (datetime('now','localtime')),
    pat_email TEXT NOT NULL,
    pat_dob DATE,
    pat_address TEXT NOT NULL);''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS doctor
    (doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_first_name TEXT NOT NULL,
    doc_last_name TEXT NOT NULL,
    doc_ph_no TEXT NOT NULL,
    doc_date DATE DEFAULT (datetime('now','localtime')),
    doc_address TEXT NOT NULL);''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS appointment
    (app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_id INTEGER NOT NULL,
    doc_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    FOREIGN KEY(pat_id) REFERENCES patient(pat_id),
    FOREIGN KEY(doc_id) REFERENCES doctor(doc_id));''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS medrecords
    (rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_id INTEGER NOT NULL,
    create_date DATE NOT NULL,
    body TEXT,
    FOREIGN KEY(pat_id) REFERENCES patient(pat_id));''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Patientfiles
    (pat_id TEXT,
    filename TEXT,
    filepath TEXT,
    createdate TEXT,
    userid TEXT);''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
    (rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_id INTEGER NOT NULL,
    create_date DATE NOT NULL,
    message TEXT,
    app_id INTEGER,
    status INTEGER DEFAULT 0);''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pendingappointment
    (app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pat_id INTEGER NOT NULL,
    doc_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    status INTEGER DEFAULT 0,
    FOREIGN KEY(doc_id) REFERENCES doctor(doc_id),
    FOREIGN KEY(pat_id) REFERENCES patient(pat_id));''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS recordstamplates
    (rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_type TEXT NOT NULL,
    template TEXT);''')

    conn.commit()

def create_client_database(client_key):
    """
    Create a new SQLite database for the client and return its file path.
    """
    base_db_path = "./databases/"
    # Ensure the base directory exists
    if not os.path.exists(base_db_path):
        os.makedirs(base_db_path)

    database_filename = os.path.join(base_db_path, f"TherapyManager_{client_key}.db")
    
    if not os.path.exists(database_filename):
        conn = sqlite3.connect(database_filename)
        initialize_database_schema(conn)
        conn.close()
        print(f"Database for client '{client_key}' created.")
    else:
        print(f"Database for client '{client_key}' already exists.")
    
    return database_filename

def create_default_database(global_settings):
    """
    Create the default database using the default client key.
    """
    default_client_key = global_settings['DEFAULT_CLIENT_KEY']
    return create_client_database(default_client_key)

def get_db_path(client_key, global_settings):
    """
    Get the database path for the given client key.
    """
    if client_key == "default_client":
        return create_default_database(global_settings)
    else:
        return create_client_database(client_key)

def connect_to_db(client_key):   
    base_db_path = "./databases/"
    database_filename = os.path.join(base_db_path, f"TherapyManager_{client_key}.db")
    try:
        # Create a connection to the SQLite database
        conn = sqlite3.connect(database_filename)
        conn.row_factory = sqlite3.Row  # Optional: Return rows as dictionaries
        print(f"Connected to the database at {database_filename}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None
    
# Load settings from the configuration file
with open('config.json') as config_file:
    config_data = json.load(config_file)
    global_settings = config_data['Global']

client_key = 'default_client'
# # Connect to the database
conn = connect_to_db(client_key)

