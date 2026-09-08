import base64
import datetime
import hashlib
import os

from package.database import DatabaseManager


SCOPES = ['https://www.googleapis.com/auth/calendar.events']
TOKEN_URI = 'https://oauth2.googleapis.com/token'


def is_configured():
    return bool(os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET'))


def _client_config():
    return {
        'web': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': TOKEN_URI,
        }
    }


def create_oauth_flow(redirect_uri, state=None, code_verifier=None):
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        _client_config(), scopes=SCOPES, state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = redirect_uri
    return flow


def _fernet():
    from cryptography.fernet import Fernet

    secret = os.environ.get('THERAPY_SECRET_KEY', 'change-this-development-key').encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _encrypt_token(token):
    return _fernet().encrypt(token.encode('utf-8')).decode('ascii')


def _decrypt_token(token):
    return _fernet().decrypt(token.encode('ascii')).decode('utf-8')


def save_connection(client_key, userid, credentials):
    if not credentials.refresh_token:
        raise ValueError('Google did not return a refresh token. Reconnect and grant consent again.')
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        conn.execute('''
            INSERT INTO google_calendar_connections
                (userid, refresh_token_encrypted, calendar_id, connected_at, updated_at)
            VALUES (?, ?, 'primary', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(userid) DO UPDATE SET
                refresh_token_encrypted=excluded.refresh_token_encrypted,
                calendar_id='primary',
                updated_at=CURRENT_TIMESTAMP
        ''', (userid, _encrypt_token(credentials.refresh_token)))
        conn.commit()
    finally:
        conn.close()


def connection_status(client_key, userid):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        row = conn.execute('''
            SELECT calendar_id, connected_at, updated_at
            FROM google_calendar_connections WHERE userid=?
        ''', (userid,)).fetchone()
        return row
    finally:
        conn.close()


def disconnect(client_key, userid):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        conn.execute('DELETE FROM google_calendar_connections WHERE userid=?', (userid,))
        conn.commit()
    finally:
        conn.close()


def _calendar_service(connection):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials(
        token=None,
        refresh_token=_decrypt_token(connection['refresh_token_encrypted']),
        token_uri=TOKEN_URI,
        client_id=os.environ['GOOGLE_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
        scopes=SCOPES,
    )
    return build('calendar', 'v3', credentials=credentials, cache_discovery=False)


def _parse_appointment_datetime(value):
    text = str(value).strip().replace('Z', '')
    for date_format in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.datetime.strptime(text, date_format)
        except ValueError:
            continue
    return datetime.datetime.fromisoformat(text)


def sync_appointment_event(client_key, app_id):
    """Create or update one confirmed appointment in the connected primary calendar."""
    if not is_configured():
        return None
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        appointment = conn.execute('''
            SELECT a.app_id, a.appointment_date, a.google_event_id,
                   p.pat_first_name, p.pat_last_name,
                   d.doc_address, d.userid
            FROM appointment a
            JOIN patient p ON p.pat_id=a.pat_id
            JOIN doctor d ON d.doc_id=a.doc_id
            WHERE a.app_id=?
        ''', (app_id,)).fetchone()
        if not appointment:
            return None
        connection = conn.execute('''
            SELECT * FROM google_calendar_connections WHERE userid=?
        ''', (appointment['userid'],)).fetchone()
        if not connection:
            return None

        start = _parse_appointment_datetime(appointment['appointment_date'])
        duration_row = conn.execute(
            "SELECT value FROM settings WHERE key='APPOINTMENT_DURATION'"
        ).fetchone()
        try:
            duration = int(duration_row['value']) if duration_row else 60
        except (TypeError, ValueError):
            duration = 60
        end = start + datetime.timedelta(minutes=duration)
        timezone = os.environ.get('THERAPY_TIMEZONE', 'Asia/Jerusalem')
        include_name = os.environ.get('GOOGLE_CALENDAR_INCLUDE_CLIENT_NAME', '').lower() in ('1', 'true', 'yes')
        client_name = ' '.join(filter(None, [appointment['pat_first_name'], appointment['pat_last_name']]))
        body = {
            'summary': ('Therapy appointment – ' + client_name) if include_name else 'Therapy appointment',
            'description': 'Appointment managed by CareIL.',
            'location': appointment['doc_address'] or '',
            'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': end.isoformat(), 'timeZone': timezone},
            'extendedProperties': {'private': {'careil_app_id': str(app_id)}},
        }
        service = _calendar_service(connection)
        calendar_id = connection['calendar_id'] or 'primary'
        event_id = appointment['google_event_id']
        if event_id:
            try:
                event = service.events().update(
                    calendarId=calendar_id, eventId=event_id, body=body
                ).execute()
            except Exception as error:
                if getattr(error, 'resp', None) is None or error.resp.status not in (404, 410):
                    raise
                event = service.events().insert(calendarId=calendar_id, body=body).execute()
        else:
            event = service.events().insert(calendarId=calendar_id, body=body).execute()
        conn.execute('UPDATE appointment SET google_event_id=? WHERE app_id=?', (event['id'], app_id))
        conn.commit()
        return event['id']
    finally:
        conn.close()


def delete_appointment_event(client_key, app_id):
    if not is_configured():
        return
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        row = conn.execute('''
            SELECT a.google_event_id, d.userid
            FROM appointment a JOIN doctor d ON d.doc_id=a.doc_id
            WHERE a.app_id=?
        ''', (app_id,)).fetchone()
        if not row or not row['google_event_id']:
            return
        connection = conn.execute(
            'SELECT * FROM google_calendar_connections WHERE userid=?', (row['userid'],)
        ).fetchone()
        if not connection:
            return
        try:
            _calendar_service(connection).events().delete(
                calendarId=connection['calendar_id'] or 'primary',
                eventId=row['google_event_id'],
            ).execute()
        except Exception as error:
            if getattr(error, 'resp', None) is None or error.resp.status not in (404, 410):
                raise
    finally:
        conn.close()


def sync_all_upcoming(client_key):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        rows = conn.execute('''
            SELECT app_id FROM appointment
            WHERE datetime(appointment_date) >= datetime('now', '-1 day')
            ORDER BY appointment_date
        ''').fetchall()
    finally:
        conn.close()
    synced = 0
    for row in rows:
        if sync_appointment_event(client_key, row['app_id']):
            synced += 1
    return synced
