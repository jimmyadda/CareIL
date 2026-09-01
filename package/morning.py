import base64
import datetime
import hashlib
import json
import os
import urllib.error
import urllib.request

from cryptography.fernet import Fernet, InvalidToken

from package.database import DatabaseManager


PRODUCTION_BASE_URL = 'https://api.greeninvoice.co.il/api/v1'
SANDBOX_BASE_URL = 'https://sandbox.d.greeninvoice.co.il/api/v1'
PRODUCTION_AUTH_URL = 'https://api.morning.co'
SANDBOX_AUTH_URL = 'https://api.sandbox.morning.dev'
PAYMENT_TYPES = {
    1: 'Cash',
    2: 'Cheque',
    3: 'Credit card',
    4: 'Bank transfer',
    5: 'PayPal',
    10: 'Payment app',
    11: 'Other',
}


class MorningError(RuntimeError):
    pass


def _fernet():
    secret = os.environ.get('THERAPY_SECRET_KEY', 'change-this-development-key').encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _encrypt(value):
    return _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def _decrypt(value):
    try:
        return _fernet().decrypt(value.encode('ascii')).decode('utf-8')
    except InvalidToken as error:
        raise MorningError('The saved Morning credentials cannot be decrypted. Check THERAPY_SECRET_KEY.') from error


def _base_url(environment):
    return SANDBOX_BASE_URL if environment == 'sandbox' else PRODUCTION_BASE_URL


def _auth_url(environment):
    return SANDBOX_AUTH_URL if environment == 'sandbox' else PRODUCTION_AUTH_URL


def _request_json(url, method='GET', payload=None, token=None, timeout=25):
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode('utf-8', errors='replace')
        try:
            detail = json.loads(raw)
            message = detail.get('error_description') or detail.get('message') or detail.get('error') or raw
        except (ValueError, AttributeError):
            message = raw
        raise MorningError(f'Morning API returned {error.code}: {message}') from error
    except urllib.error.URLError as error:
        raise MorningError(f'Could not reach Morning: {error.reason}') from error


def _access_token(client_id, client_secret, environment):
    response = _request_json(
        _auth_url(environment) + '/idp/v1/oauth/token',
        method='POST',
        payload={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        },
    )
    token = response.get('accessToken')
    if not token:
        raise MorningError('Morning did not return an access token.')
    return token


def save_connection(client_key, client_id, client_secret, environment='production'):
    environment = 'sandbox' if environment == 'sandbox' else 'production'
    # Validate before replacing a working connection.
    _access_token(client_id, client_secret, environment)
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        conn.execute('''
            INSERT INTO morning_connections
                (connection_id, client_id_encrypted, client_secret_encrypted, environment)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(connection_id) DO UPDATE SET
                client_id_encrypted=excluded.client_id_encrypted,
                client_secret_encrypted=excluded.client_secret_encrypted,
                environment=excluded.environment,
                updated_at=CURRENT_TIMESTAMP
        ''', (_encrypt(client_id), _encrypt(client_secret), environment))
        conn.commit()
    finally:
        conn.close()


def connection_status(client_key):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        row = conn.execute('''
            SELECT environment, connected_at, updated_at
            FROM morning_connections WHERE connection_id=1
        ''').fetchone()
        return row
    finally:
        conn.close()


def disconnect(client_key):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        conn.execute('DELETE FROM morning_connections WHERE connection_id=1')
        conn.commit()
    finally:
        conn.close()


def _credentials(conn):
    row = conn.execute('SELECT * FROM morning_connections WHERE connection_id=1').fetchone()
    if not row:
        raise MorningError('Connect the clinic to Morning in Settings before issuing a receipt.')
    return _decrypt(row['client_id_encrypted']), _decrypt(row['client_secret_encrypted']), row['environment']


def issue_receipt(client_key, pat_id, app_id, amount, payment_type, payment_date, language='he'):
    if payment_type not in PAYMENT_TYPES:
        raise MorningError('Please select a supported payment method.')
    try:
        amount = round(float(amount), 2)
    except (TypeError, ValueError) as error:
        raise MorningError('Receipt amount must be a valid number.') from error
    if amount <= 0:
        raise MorningError('Receipt amount must be greater than zero.')
    try:
        parsed_payment_date = datetime.datetime.strptime(payment_date, '%Y-%m-%d').date()
    except (TypeError, ValueError) as error:
        raise MorningError('Payment date must use YYYY-MM-DD format.') from error
    if parsed_payment_date > datetime.date.today():
        raise MorningError('Payment date cannot be in the future.')

    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        appointment = conn.execute('''
            SELECT a.app_id, a.appointment_date, a.pat_id,
                   p.pat_first_name, p.pat_last_name, p.pat_email,
                   p.pat_ph_no, p.pat_address
            FROM appointment a
            JOIN patient p ON p.pat_id=a.pat_id
            WHERE a.app_id=? AND a.pat_id=?
        ''', (app_id, pat_id)).fetchone()
        if not appointment:
            raise MorningError('The appointment does not belong to this client.')
        session_start = str(appointment['appointment_date'])
        try:
            session_date = datetime.datetime.fromisoformat(session_start.replace('Z', '')).date()
        except ValueError as error:
            raise MorningError('The appointment date is invalid.') from error
        if session_date > datetime.date.today():
            raise MorningError('A receipt can only be issued for a completed appointment.')
        existing = conn.execute(
            "SELECT * FROM morning_receipts WHERE app_id=? AND status='issued'", (app_id,)
        ).fetchone()
        if existing:
            raise MorningError('A receipt has already been issued for this appointment.')

        description = (
            f'פגישה טיפולית בתאריך {session_date.strftime("%d/%m/%Y")}'
            if language == 'he'
            else f'Therapy session on {session_date.strftime("%d/%m/%Y")}'
        )
        client_id, client_secret, environment = _credentials(conn)
        conn.execute('''
            INSERT INTO morning_receipts
                (app_id, pat_id, amount, payment_type, payment_date, session_date,
                 description, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL)
            ON CONFLICT(app_id) DO UPDATE SET
                amount=excluded.amount, payment_type=excluded.payment_type,
                payment_date=excluded.payment_date, description=excluded.description,
                status='pending', error_message=NULL
            WHERE morning_receipts.status != 'issued'
        ''', (app_id, pat_id, amount, payment_type, payment_date, session_date.isoformat(), description))
        conn.commit()

        payload = {
            'type': 400,
            'date': payment_date,
            'lang': 'he' if language == 'he' else 'en',
            'currency': 'ILS',
            'vatType': 0,
            'signed': True,
            'attachment': True,
            'description': description,
            'client': {
                'name': ' '.join(filter(None, [appointment['pat_first_name'], appointment['pat_last_name']])),
                'emails': [appointment['pat_email']] if appointment['pat_email'] else [],
                'phone': appointment['pat_ph_no'] or '',
                'address': appointment['pat_address'] or '',
                'country': 'IL',
                'add': False,
            },
            'income': [{
                'description': description,
                'quantity': 1,
                'price': amount,
                'currency': 'ILS',
                'vatType': 0,
            }],
            'payment': [{
                'date': payment_date,
                'type': payment_type,
                'price': amount,
                'currency': 'ILS',
            }],
        }
        try:
            token = _access_token(client_id, client_secret, environment)
            result = _request_json(_base_url(environment) + '/documents', method='POST', payload=payload, token=token)
        except Exception as error:
            conn.execute(
                "UPDATE morning_receipts SET status='failed', error_message=? WHERE app_id=?",
                (str(error)[:1000], app_id),
            )
            conn.commit()
            raise
        urls = result.get('url') or {}
        document_url = urls.get('he') or urls.get('origin') or urls.get('en')
        conn.execute('''
            UPDATE morning_receipts
            SET morning_document_id=?, document_number=?, document_url=?, status='issued',
                error_message=NULL, issued_at=CURRENT_TIMESTAMP
            WHERE app_id=?
        ''', (result.get('id'), result.get('number'), document_url, app_id))
        conn.commit()
        return {
            'id': result.get('id'),
            'number': result.get('number'),
            'url': document_url,
            'description': description,
        }
    finally:
        conn.close()
