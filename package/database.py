import json
import os
import sqlite3

from flask import current_app, g, session


class DatabaseManager:
    
    def __init__(self,client_key=None, config_file="config.json"):
        """
        Initialize the DatabaseManager instance.

        :param config_file: Path to the JSON configuration file.
        """
        # Load configuration from config.json
        with open(config_file) as config_file:
            self.config = json.load(config_file)
            self.global_settings = self.config["Global"]
        print("Self",client_key)
        self.base_db_path = self.global_settings["BASE_DB_PATH"]
        self.default_client_key = self.global_settings["DEFAULT_CLIENT_KEY"]
        self.default_db_path = self.global_settings["DEFAULT_DB_PATH"]

    def get_db_path(self, client_key=None):
        """
        Get the database path for a given client key.

        :param client_key: The client key (optional). If None, uses the default client key.
        :return: Path to the database file.
        """
        client_key = client_key or self.default_client_key
        if client_key == self.default_client_key:
            return self.default_db_path
        return os.path.join(self.base_db_path, f"CareIL_{client_key}.db")

    @staticmethod
    def dict_factory(cursor, row):
        """This is an function use to fonmat the json when retirve from the  myswl database"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def connect_to_db(self, client_key=None):
        """
        Connect to the database for the given client key and return the connection.

        :param client_key: The client key (optional). If None, uses the default client key.
        :raises FileNotFoundError: If the database file does not exist.
        :return: SQLite connection object.
        """
        
        db_path = self.get_db_path(client_key)
        print("connectto db",db_path)
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file '{db_path}' does not exist.")

        conn = sqlite3.connect(db_path)
        self.ensure_account_verification_schema(conn)
        self.ensure_portal_invitation_schema(conn)
        self.ensure_google_calendar_schema(conn)
        #conn.row_factory = sqlite3.Row  # Enable dict-like row access
        conn.row_factory = self.dict_factory
        return conn

    @staticmethod
    def ensure_account_verification_schema(conn):
        """Add persistent email-verification state to existing account databases."""
        account_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        }
        if account_columns and 'email_verified' not in account_columns:
            conn.execute(
                "ALTER TABLE accounts ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()

    @staticmethod
    def ensure_google_calendar_schema(conn):
        """Add Google Calendar connection and event mapping storage."""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS google_calendar_connections (
                userid TEXT PRIMARY KEY,
                refresh_token_encrypted TEXT NOT NULL,
                calendar_id TEXT NOT NULL DEFAULT 'primary',
                connected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES accounts(userid)
            )
        ''')
        appointment_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(appointment)").fetchall()
        }
        if 'google_event_id' not in appointment_columns:
            conn.execute("ALTER TABLE appointment ADD COLUMN google_event_id TEXT")
        conn.commit()

    @staticmethod
    def ensure_portal_invitation_schema(conn):
        """Create secure portal invitation storage in existing databases."""
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS portal_invitations (
            invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at DATETIME NOT NULL,
            used_at DATETIME,
            revoked_at DATETIME,
            created_by TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pat_id) REFERENCES patient(pat_id),
            FOREIGN KEY (created_by) REFERENCES accounts(userid)
        );
        CREATE INDEX IF NOT EXISTS idx_portal_invitations_patient
            ON portal_invitations(pat_id);
        CREATE INDEX IF NOT EXISTS idx_portal_invitations_active
            ON portal_invitations(token_hash, expires_at)
            WHERE used_at IS NULL AND revoked_at IS NULL;
        ''')
        conn.commit()

    def create_client_database(self, client_key):
        """
        Create a database for a specific client key if it does not exist.

        :param client_key: The client key for which to create the database.
        """
        client_db_path = self.get_db_path(client_key)
        if not os.path.exists(client_db_path):
            os.makedirs(self.base_db_path, exist_ok=True)
            conn = sqlite3.connect(client_db_path)
            self.initialize_database_schema(conn)
            conn.close()

    def create_default_database(self):
        """
        Create the default database if it does not exist.
        """
        default_db_path = self.get_db_path(self.default_client_key)
        if not os.path.exists(default_db_path):
            os.makedirs(self.base_db_path, exist_ok=True)
            conn = sqlite3.connect(default_db_path)
            self.initialize_database_schema(conn)
            conn.close()

    def initialize_database_schema(self, conn):
        """
        Initialize the database schema with required tables.
        """
        cursor = conn.cursor()
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS accounts (
            userid TEXT PRIMARY KEY,
            password TEXT,
            salt TEXT, 
            phone_number TEXT,
            email TEXT,
            name TEXT,
            client_key TEXT,
            email_verified INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS users (
            userid TEXT PRIMARY KEY,
            client_key TEXT
        );
        CREATE TABLE IF NOT EXISTS patient (
            pat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_first_name TEXT NOT NULL,
            pat_last_name TEXT NOT NULL,
            pat_insurance_no TEXT NOT NULL,
            pat_ph_no TEXT NOT NULL,
            pat_date DATE DEFAULT (datetime('now','localtime')),
            pat_email TEXT NOT NULL,
            pat_dob DATE,
            pat_address TEXT NOT NULL,
            client_key TEXT
        );

        CREATE TABLE IF NOT EXISTS doctor (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_first_name TEXT NOT NULL,            
            doc_last_name TEXT NOT NULL,
            doc_ph_no TEXT NOT NULL,
            doc_email TEXT NOT NULL,
            doc_date DATE DEFAULT (datetime('now','localtime')),
            doc_address TEXT NOT NULL,
            userid TEXT NOT NULL, 
            FOREIGN KEY (userid) REFERENCES accounts(userid)
        );

        CREATE TABLE IF NOT EXISTS appointment (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER NOT NULL,
            doc_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            FOREIGN KEY(pat_id) REFERENCES patient(pat_id),
            FOREIGN KEY(doc_id) REFERENCES doctor(doc_id)
        );

        CREATE TABLE IF NOT EXISTS medrecords (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER NOT NULL,
            create_date DATE NOT NULL,
            body TEXT,
            FOREIGN KEY(pat_id) REFERENCES patient(pat_id)
        );

        CREATE TABLE IF NOT EXISTS recordstamplates (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_type TEXT,
            template TEXT
        );
                             
        CREATE TABLE if not exists Patientfiles
        ("pat_id"	TEXT,
        "filename"	TEXT,
        "filepath"	TEXT,
        "createdate" TEXT,
        "userid"	TEXT);
                             
        CREATE TABLE if not exists messages
        ("rec_id"	INTEGER,
        "pat_id"	INTEGER NOT NULL,
        "create_date"	DATE NOT NULL,
        "message"	TEXT,
        "app_id"	INTEGER,
        "status"	INTEGER DEFAULT 0,
        PRIMARY KEY("rec_id" AUTOINCREMENT)); 

        CREATE TABLE if not exists  pendingappointment
            ("app_id"	INTEGER,
            "pat_id"	INTEGER NOT NULL,
            "doc_id"	INTEGER NOT NULL,
            "appointment_date"	DATE NOT NULL,
            "status"	INTEGER DEFAULT 0,
            FOREIGN KEY("doc_id") REFERENCES "doctor"("doc_id"),
            FOREIGN KEY("pat_id") REFERENCES "patient"("pat_id"),
            PRIMARY KEY("app_id" AUTOINCREMENT)); 
           
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT
            );
          INSERT INTO settings (key, value) VALUES 
            ('MAIL_SERVER', 'smtp.gmail.com'),
            ('MAIL_PORT', '587'),
            ('MAIL_USE_TLS', 'True'),
            ('MAIL_USERNAME', ''),
            ('MAIL_PASSWORD', '');  
          
            CREATE TABLE clinicinfo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            website TEXT NOT NULL);     
     
            CREATE TABLE verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code TEXT,
                expiration_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES doctor(doc_id)
            );

            CREATE TABLE IF NOT EXISTS portal_invitations (
                invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pat_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                used_at DATETIME,
                revoked_at DATETIME,
                created_by TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pat_id) REFERENCES patient(pat_id),
                FOREIGN KEY (created_by) REFERENCES accounts(userid)
            );

            CREATE INDEX IF NOT EXISTS idx_portal_invitations_patient
                ON portal_invitations(pat_id);

            CREATE INDEX IF NOT EXISTS idx_portal_invitations_active
                ON portal_invitations(token_hash, expires_at)
                WHERE used_at IS NULL AND revoked_at IS NULL;
        ''')
        conn.commit()

    def get_db_connection(self):
        """
        Get the current database connection based on the session client key.
        """
        if "db" not in g:
            client_key = session.get("clientKey", self.default_client_key)
            g.db = self.connect_to_db(client_key)
        return g.db

    def close_db_connection(self, exception=None):
        """
        Close the database connection at the end of the request.
        """
        db = g.pop("db", None)
        if db is not None:
            db.close()

