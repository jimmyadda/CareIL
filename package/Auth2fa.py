import datetime
import hmac

from package.database import DatabaseManager



def store_verification_code(client_key, code, expiration_time):
    """ Store the verification code in the database """
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM verification_codes WHERE user_id = ?", (client_key,))
    cursor.execute('''
        INSERT INTO verification_codes (user_id, code, expiration_time)
        VALUES (?, ?, ?)
    ''', (client_key, code, expiration_time))
    conn.commit()
    conn.close()

def verify_code(client_key, entered_code):
    # Retrieve the stored code and timestamp from SQLite

    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    cursor = conn.cursor()

    cursor.execute("""
      SELECT code, expiration_time FROM verification_codes WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (client_key,))
    
    result = cursor.fetchone()
    if result:
        stored_code = result['code']
        code_timestamp = result['expiration_time']
        # Convert the string to a datetime object
        code_timestamp = datetime.datetime.strptime(code_timestamp, '%Y-%m-%d %H:%M:%S.%f')
        # Get the current time
        current_time = datetime.datetime.now()

        if current_time > code_timestamp:
            cursor.execute("DELETE FROM verification_codes WHERE user_id = ?", (client_key,))
            conn.commit()
            conn.close()
            return False

        # Compare the stored code with the entered code
        if hmac.compare_digest(str(entered_code), str(stored_code)):
            cursor.execute(
                "DELETE FROM verification_codes WHERE user_id = ?",
                (client_key,),
            )
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    else:
        conn.close()
        return False
    
