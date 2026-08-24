import datetime
import json
import string
from flask import session
import random
import time
from flask_mail import Mail, Message

from package.database import DatabaseManager



def store_verification_code(client_key, code, expiration_time):
    """ Store the verification code in the database """
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO verification_codes (user_id, code, expiration_time)
        VALUES (?, ?, ?)
    ''', (client_key, code, expiration_time))
    conn.commit()
    conn.close()

def verify_code(client_key, entered_code):
    # Retrieve the stored code and timestamp from SQLite
    print(client_key)
    print("entered_code",entered_code)

    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    cursor = conn.cursor()

    cursor.execute("""
      SELECT code, expiration_time FROM verification_codes WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (client_key,))
    
    result = cursor.fetchone()
    conn.close()

    print("verify_code: ", result)
    if result:
        stored_code = result['code']
        code_timestamp = result['expiration_time']
        # Convert the string to a datetime object
        code_timestamp = datetime.datetime.strptime(code_timestamp, '%Y-%m-%d %H:%M:%S.%f')
        # Get the current time
        current_time = datetime.datetime.now()

        # Calculate the difference in seconds
        time_difference = (current_time - code_timestamp).total_seconds()        
        # Check if the code has expired (5 minutes expiration)
        if time_difference > 300:  # 5 minutes = 300 seconds
            print("Verification code has expired.")
            return False
        else:
            print("Verification code is still valid.")

        # Compare the stored code with the entered code
        if entered_code == stored_code:
            print("Verification successful.")
            return True
        else:
            print("Incorrect code.")
            return False
    else:
        print("No verification code found for this email.")
        return False
    
