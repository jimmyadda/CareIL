import base64
from collections import defaultdict
from email import encoders
from email.mime.base import MIMEBase
import hmac
import html
import pathlib
from pydoc import text
import random
import secrets
import shutil
import string
from bs4 import BeautifulSoup
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from flask import Flask, abort, current_app, g, jsonify,flash,render_template,request,redirect, send_from_directory, session, url_for
import flask_login
import sqlite3
import datetime
import uuid
import hashlib
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restful import Resource, Api
from mail import get_Mail_settings, send_notification, update_Mail_setting
from package.decorators import admin_only
from package.patient import Patients, Patient
from package.doctor import Doctors, Doctor
from package.appointment import Appointments, Appointment,RequestAppointments,RequestAppointment
from package.common import Common
from package.User import User
from package.client import ClientUser
from package.medicalnote import Medicalnote,Medicalnotes
from flask_mail import Mail, Message
from create_account import create_account
from package.database import DatabaseManager
from package.google_calendar import (
    connection_status as google_calendar_connection_status,
    create_oauth_flow,
    disconnect as disconnect_google_calendar,
    is_configured as google_calendar_is_configured,
    save_connection as save_google_calendar_connection,
    sync_all_upcoming as sync_all_google_appointments,
)
from package.morning import (
    MorningError,
    PAYMENT_TYPES as MORNING_PAYMENT_TYPES,
    connection_status as morning_connection_status,
    disconnect as disconnect_morning,
    issue_receipt as issue_morning_receipt,
    save_connection as save_morning_connection,
)
from package.email_service import (
    careil_logo_attachment,
    encoded_attachment,
    resend_is_configured,
    resend_sender_address,
    send_resend_email,
)
from package.legal_documents import (
    DOCUMENTS as LEGAL_DOCUMENTS,
    LEGAL_EFFECTIVE_DATE,
    LEGAL_VERSION,
)
from package.landing_content import LANDING_CONTENT
from package.content_he import HEBREW_ARTICLES, HEBREW_FAQ
from package.Myutils import render_ics
import json
from package.Auth2fa import store_verification_code,verify_code

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

api = Api(app)
# Routes API
api.add_resource(Patients, '/patientapi')
api.add_resource(Patient, '/patientapi/<int:id>')
api.add_resource(Doctors, '/doctorapi')
api.add_resource(Doctor, '/doctorapi/<int:id>')
api.add_resource(Appointments, '/appointmentapi')
api.add_resource(Appointment, '/appointmentapi/<int:id>')
api.add_resource(RequestAppointments, '/appointmentrequestapi')
api.add_resource(RequestAppointment, '/appointmentrequestapi/<int:id>')
api.add_resource(Medicalnotes, '/medicalnoteapi')
api.add_resource(Medicalnote, '/medicalnoteapi/<int:id>')
api.add_resource(Common, '/common') 


with open('Translate.json',encoding="utf8") as Translate_file:
    Translate_data = json.load(Translate_file)

#Settings
with open('config.json') as config_file:
    config_data = json.load(config_file)
Globalsetting = config_data['Global'] 

 # Set up Flask-Mail
mail_settings = config_data['mail_settings']
app.config['MAIL_SERVER'] = mail_settings['MAIL_SERVER']  # Use your email provider's SMTP server
app.config['MAIL_PORT'] = mail_settings['MAIL_PORT']
app.config['MAIL_USE_TLS'] = mail_settings['MAIL_USE_TLS']
app.config['MAIL_USERNAME'] = os.environ.get('THERAPY_MAIL_USERNAME', mail_settings.get('MAIL_USERNAME', ''))
app.config['MAIL_PASSWORD'] = os.environ.get('THERAPY_MAIL_PASSWORD', mail_settings.get('MAIL_PASSWORD', ''))
mail = Mail(app) 



# Initialize DatabaseManager
db_manager = DatabaseManager()
# Ensure the default database is created at startup
db_manager.create_default_database()

SECRET_KEY = os.environ.get('THERAPY_SECRET_KEY', 'change-this-development-key')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('THERAPY_HTTPS', '').lower() in ('1', 'true', 'yes')
path = os.getcwd()

UPLOAD_FOLDER = os.path.join(path, 'uploads')
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


#Logs
handler = logging.FileHandler('LogFile.log') # creates handler for the log file
app.logger.addHandler(handler) # Add it to the built-in logger
app.logger.setLevel(logging.DEBUG)         # Set the log level to debug
logger = app.logger

EMAIL_LOGO_CID = "careil-logo"

def email_brand_header():
    return ("<div style='display:flex;align-items:center;gap:12px;margin:0 0 22px;"
            "padding:14px 18px;border-radius:14px;"
            "background:linear-gradient(135deg,#a3b18a 0%,#588157 100%);'>"
            "<img src='cid:careil-logo' alt='CareIL' "
            "style='display:block;width:64px;height:auto;'>"
            "<strong style='font:700 20px Arial,sans-serif;color:#102a1c;'>CareIL</strong>"
            "</div>")

def attach_email_logo(message):
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'therapy-hands-logo-email.png')
    with open(logo_path, 'rb') as logo_file:
        logo = MIMEImage(logo_file.read(), _subtype='png')
    logo.add_header('Content-ID', '<careil-logo>')
    logo.add_header('Content-Disposition', 'inline', filename='careil.png')
    message.attach(logo)
#Log in 
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
#region Main App
base_db_path = "./databases/"

@login_manager.user_loader
def load_user(userid):  #or client patid
    user=None
    clientKey = session.get('client_key')
    if not clientKey:
        return None
    try:
        users = database_read(f"select * from accounts where userid='{userid}';",client_key=clientKey)
        client = database_read(f"select * from patient where pat_id='{userid}';",client_key=clientKey)
    except FileNotFoundError:
        # A deployment, database rename, or removed tenant can leave an old
        # browser cookie pointing at a database that no longer exists.
        session.pop('client_key', None)
        return None
    if (len(users) == 1 and bool(users[0].get('email_verified'))
            and not users[0].get('deletion_requested_at')):
        user = User(users[0]['userid'],users[0]['email'],users[0]['name'],users[0]['client_key'])
    if len(client)==1:
        user = ClientUser(client[0]['pat_id'],client[0]['pat_email'],client[0]['pat_first_name'],client[0]['client_key'])
    if user:
        session['client_key'] = user.client_key
        user.id = userid
        return user
    else:
        return None

def generate_client_key(user_id):
    # Use SHA-256 to generate a consistent hash
    return f"client_{hashlib.sha256(user_id.encode()).hexdigest()}" 

def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

def _legal_operator_context():
    support_email = os.environ.get('CAREIL_SUPPORT_EMAIL', 'support@careil.net')
    privacy_email = os.environ.get('CAREIL_PRIVACY_EMAIL', 'privacy@careil.net')
    return {
        'operator_name': os.environ.get('CAREIL_LEGAL_NAME', 'CareIL'),
        'operator_address': os.environ.get('CAREIL_LEGAL_ADDRESS', ''),
        'support_email': support_email,
        'privacy_email': privacy_email,
        'accessibility_email': os.environ.get('CAREIL_ACCESSIBILITY_EMAIL', support_email),
    }

def _visitor_ip_address():
    forwarded = request.headers.get('X-Forwarded-For', '')
    return (forwarded.split(',')[0].strip() if forwarded else request.remote_addr) or ''

def _record_legal_acceptances(conn, userid, language='en', marketing=False):
    audit = (
        userid, LEGAL_VERSION, language, _visitor_ip_address(),
        request.headers.get('User-Agent', '')[:500],
    )
    for document_type in ('privacy', 'terms', 'dpa'):
        conn.execute(
            """INSERT INTO legal_acceptances
               (userid, document_type, document_version, language, ip_address, user_agent)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (audit[0], document_type, audit[1], audit[2], audit[3], audit[4]),
        )
    conn.execute(
        'UPDATE accounts SET marketing_consent=? WHERE userid=?',
        (1 if marketing else 0, userid),
    )
    conn.commit()

def _database_client_key(filename):
    if not filename.startswith('CareIL_') or not filename.endswith('.db'):
        return None
    return filename[len('CareIL_'):-3]

def _cleanup_expired_workspaces():
    """Purge expired demos and accounts whose 24-hour recovery window ended."""
    base_path = pathlib.Path(db_manager.base_db_path)
    if not base_path.is_dir():
        return
    now = _utc_now()
    for db_path in base_path.glob('CareIL_*.db'):
        client_key = _database_client_key(db_path.name)
        if not client_key or client_key == Globalsetting['DEFAULT_CLIENT_KEY']:
            continue
        should_remove = False
        if client_key.startswith('demo_'):
            modified = datetime.datetime.fromtimestamp(db_path.stat().st_mtime, datetime.timezone.utc)
            should_remove = now - modified >= datetime.timedelta(hours=2)
        else:
            try:
                conn = sqlite3.connect(str(db_path))
                row = conn.execute(
                    "SELECT deletion_purge_at FROM accounts "
                    "WHERE deletion_purge_at IS NOT NULL LIMIT 1"
                ).fetchone()
                conn.close()
                if row and row[0]:
                    purge_at = datetime.datetime.fromisoformat(str(row[0])).replace(
                        tzinfo=datetime.timezone.utc
                    )
                    should_remove = now >= purge_at
            except (sqlite3.Error, OSError, ValueError):
                current_app.logger.exception('Could not inspect tenant cleanup state')
        if not should_remove:
            continue
        upload_path = pathlib.Path(app.config['UPLOAD_FOLDER']) / client_key
        try:
            db_path.unlink(missing_ok=True)
            if upload_path.is_dir():
                shutil.rmtree(upload_path)
            current_app.logger.info('Permanently removed expired CareIL workspace: %s', client_key)
        except OSError:
            current_app.logger.exception('Could not remove expired CareIL workspace')

@app.before_request
def careil_workspace_lifecycle():
    last_cleanup = app.config.get('LAST_WORKSPACE_CLEANUP')
    now = _utc_now()
    if not last_cleanup or now - last_cleanup >= datetime.timedelta(minutes=5):
        app.config['LAST_WORKSPACE_CLEANUP'] = now
        _cleanup_expired_workspaces()

    client_key = session.get('client_key', '')
    if not client_key.startswith('demo_'):
        return None
    blocked_endpoints = {
        'send_appointment', 'upload', 'upload_page', 'mail_settings',
        'google_calendar_connect', 'google_calendar_callback',
        'google_calendar_sync_now', 'google_calendar_disconnect',
        'create_portal_invitation', 'request_account_deletion',
    }
    if request.endpoint in blocked_endpoints:
        return render_template('demo-blocked.html'), 403
    return None

@app.after_request
def protect_private_pages_from_indexing(response):
    public_paths = {'/', '/he', '/robots.txt', '/sitemap.xml'}
    public_legal = request.path.startswith('/legal/') or request.path.startswith('/he/legal/')
    public_content = request.path == '/he/faq' or request.path.startswith('/he/articles')
    if (request.path not in public_paths and not public_legal and not public_content
            and not request.path.startswith('/static/')):
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@app.before_request
def require_current_legal_acceptance():
    allowed = {
        'legal_document', 'legal_acceptance', 'logout_page', 'service_worker',
        'robots_txt', 'sitemap_xml', 'restore_deleted_account',
        'restore_account_after_login', 'hebrew_articles', 'hebrew_article',
        'hebrew_faq',
    }
    if request.endpoint in allowed or request.path.startswith('/static/'):
        return None
    if not flask_login.current_user.is_authenticated:
        return None
    user = flask_login.current_user.get_dict()
    client_key = session.get('client_key', '')
    if 'userid' not in user or client_key.startswith('demo_'):
        return None
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        rows = conn.execute(
            """SELECT DISTINCT document_type FROM legal_acceptances
               WHERE userid=? AND document_version=?
               AND document_type IN ('privacy','terms','dpa')""",
            (user['userid'], LEGAL_VERSION),
        ).fetchall()
    finally:
        conn.close()
    if len(rows) < 3:
        return redirect(url_for('legal_acceptance'))
    return None

def ensure_single_therapist(client_key, user_data):
    """Create the one therapist profile required by appointment records."""
    conn = db_manager.connect_to_db(client_key=client_key)
    try:
        userid = user_data.get('userid', '')
        existing = conn.execute("SELECT doc_id FROM doctor WHERE userid=? LIMIT 1", (userid,)).fetchone()
        if existing:
            return existing['doc_id']

        # Older databases may have the single therapist row without the
        # account link. Attach it to the authenticated account instead of
        # creating a duplicate therapist.
        unlinked = conn.execute("SELECT doc_id FROM doctor LIMIT 1").fetchone()
        if unlinked:
            conn.execute("UPDATE doctor SET userid=? WHERE doc_id=?", (userid, unlinked['doc_id']))
            conn.commit()
            return unlinked['doc_id']

        full_name = (user_data.get('name') or user_data.get('userid') or 'Therapist').strip()
        name_parts = full_name.split(None, 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        cursor = conn.execute(
            """INSERT INTO doctor
               (doc_first_name, doc_last_name, doc_email, doc_ph_no, doc_address, userid)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (first_name, last_name, user_data.get('email', ''), '', '', userid)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
 
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
    #connection.commit()
    conn.commit()
    #db.close()
    #connection.close()

    return row_affected

def database_read(sql,data=None,client_key=None):
    if data and not client_key:
        if "userid" in data:
            client_key = generate_client_key(data['userid'])
            session['client_key'] =  client_key
    if client_key :#'client_key' in session:
         Curr_ClientKey = client_key  #Curr_ClientKey = session['client_key']
    else:
        Curr_ClientKey = Globalsetting['DEFAULT_CLIENT_KEY']
    print(Curr_ClientKey)
    conn = db_manager.connect_to_db(client_key=Curr_ClientKey)  # Connect to the client's database
    
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

@app.teardown_appcontext
def close_db(exception=None):
    """
    Close the database connection at the end of each request.
    """
    db_manager.close_db_connection(exception)


#region index,login,register
@app.route("/")
def index_page():
    if not flask_login.current_user.is_authenticated:
        return render_template('landing.html', lang='en', t=LANDING_CONTENT['en'])
    logger.info(str(flask_login.current_user.get_dict()) + " Has Logged in")
    user = flask_login.current_user.get_dict()
    apps = Appointments()
    appointments = apps.get()
    return render_template(
        '/index.html', Translate_data=Translate_data, user=user,
        appointments=appointments, demo=session.get('client_key', '').startswith('demo_')
    )

@app.route("/he")
def landing_hebrew_page():
    if flask_login.current_user.is_authenticated:
        return redirect('/')
    return render_template('landing.html', lang='he', t=LANDING_CONTENT['he'])


@app.route('/he/articles')
def hebrew_articles():
    return render_template('content-hub-he.html', articles=HEBREW_ARTICLES)


@app.route('/he/articles/<slug>')
def hebrew_article(slug):
    article = HEBREW_ARTICLES.get(slug)
    if not article:
        abort(404)
    schema = {
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': article['title'], 'description': article['description'],
        'inLanguage': 'he-IL',
        'mainEntityOfPage': f'https://www.careil.net/he/articles/{slug}',
        'author': {'@type': 'Organization', 'name': 'CareIL'},
        'publisher': {'@type': 'Organization', 'name': 'CareIL'},
    }
    return render_template('article-he.html', article=article, slug=slug, schema=schema)


@app.route('/he/faq')
def hebrew_faq():
    schema = {
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'inLanguage': 'he-IL',
        'mainEntity': [
            {
                '@type': 'Question', 'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer},
            }
            for question, answer in HEBREW_FAQ
        ],
    }
    return render_template('faq-he.html', faq=HEBREW_FAQ, schema=schema)


def _access_token_hash(token):
    return hashlib.sha256(str(token).encode('utf-8')).hexdigest()


def _central_database():
    return db_manager.connect_to_db(Globalsetting['DEFAULT_CLIENT_KEY'])


def _approved_access_request(token):
    if not token:
        return None
    conn = _central_database()
    try:
        return conn.execute(
            """SELECT * FROM access_requests
               WHERE token_hash=? AND status='approved' AND used_at IS NULL
                 AND token_expires_at > CURRENT_TIMESTAMP LIMIT 1""",
            (_access_token_hash(token),),
        ).fetchone()
    finally:
        conn.close()


def _careil_owner():
    if not flask_login.current_user.is_authenticated:
        return False
    user = flask_login.current_user.get_dict()
    allowed_ids = {
        value.strip().lower() for value in (
            os.environ.get('CAREIL_OWNER_USERIDS', '') + ',' + os.environ.get('CAREIL_OWNER_USERID', '')
        ).split(',')
        if value.strip()
    }
    allowed_emails = {
        value.strip().lower() for value in (
            os.environ.get('CAREIL_OWNER_EMAILS', '') + ',' + os.environ.get('CAREIL_OWNER_EMAIL', '')
        ).split(',')
        if value.strip()
    }
    return ((user.get('userid') or '').lower() in allowed_ids
            or (user.get('email') or '').lower() in allowed_emails)


def _access_csrf_token():
    if not session.get('access_admin_csrf'):
        session['access_admin_csrf'] = secrets.token_urlsafe(32)
    return session['access_admin_csrf']


def _send_access_email(recipient, subject, content):
    return send_resend_email(
        recipient,
        subject,
        email_brand_header() + content,
        attachments=[careil_logo_attachment(os.path.dirname(__file__))],
    )


@app.route('/request-access', methods=['GET', 'POST'])
def request_access():
    language = 'he' if request.values.get('lang') == 'he' else 'en'
    if request.method == 'GET':
        return render_template('request-access.html', lang=language, submitted=False, alert='')

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    clinic_name = request.form.get('clinic_name', '').strip()
    note = request.form.get('note', '').strip()
    if not full_name or not email or '@' not in email:
        return render_template(
            'request-access.html', lang=language, submitted=False,
            alert='Please provide your name and a valid email address.',
        ), 400

    conn = _central_database()
    try:
        recent_ip_count = conn.execute(
            """SELECT COUNT(*) AS count FROM access_requests
               WHERE requester_ip=? AND created_at >= datetime('now','-1 day')""",
            (_visitor_ip_address(),),
        ).fetchone()['count']
        if recent_ip_count >= 5:
            return render_template(
                'request-access.html', lang=language, submitted=False,
                alert='Too many requests were submitted. Please try again tomorrow.',
            ), 429
        existing = conn.execute(
            """SELECT request_id FROM access_requests
               WHERE email=? AND status IN ('pending','approved') AND used_at IS NULL
               ORDER BY request_id DESC LIMIT 1""",
            (email,),
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO access_requests
                   (full_name,email,phone,clinic_name,note,language,requester_ip,user_agent)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (full_name, email, phone, clinic_name, note, language,
                 _visitor_ip_address(), request.headers.get('User-Agent', '')[:500]),
            )
            conn.commit()
    finally:
        conn.close()

    owner_email = os.environ.get('CAREIL_OWNER_EMAIL', '').strip()
    if owner_email and resend_is_configured() and not existing:
        try:
            _send_access_email(
                owner_email, 'CareIL | New access request',
                f'<p>A new CareIL access request was received from <strong>{html.escape(full_name)}</strong> '
                f'({html.escape(email)}).</p><p><a href="{url_for("careil_access_requests", _external=True)}">Review request</a></p>',
            )
        except Exception:
            current_app.logger.exception('Could not notify CareIL owner about access request')
    return render_template('request-access.html', lang=language, submitted=True, alert='')


@app.route('/careil-admin/access-requests')
@flask_login.login_required
def careil_access_requests():
    if not _careil_owner():
        abort(403)
    conn = _central_database()
    try:
        rows = conn.execute(
            "SELECT * FROM access_requests ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return render_template(
        'access-requests-admin.html', requests=rows,
        csrf_token=_access_csrf_token(), message=request.args.get('message', ''),
    )


@app.route('/careil-admin/access-requests/<int:request_id>/<action>', methods=['POST'])
@flask_login.login_required
def careil_access_request_action(request_id, action):
    if not _careil_owner():
        abort(403)
    if not hmac.compare_digest(request.form.get('csrf_token', ''), session.get('access_admin_csrf', '')):
        abort(400)
    if action not in {'approve', 'decline'}:
        abort(404)
    conn = _central_database()
    try:
        row = conn.execute(
            "SELECT * FROM access_requests WHERE request_id=? AND used_at IS NULL",
            (request_id,),
        ).fetchone()
        if not row:
            return redirect(url_for('careil_access_requests', message='Request is no longer available.'))
        if action == 'decline':
            conn.execute(
                "UPDATE access_requests SET status='declined', declined_at=CURRENT_TIMESTAMP, token_hash=NULL, token_expires_at=NULL WHERE request_id=?",
                (request_id,),
            )
            conn.commit()
            try:
                _send_access_email(
                    row['email'], 'CareIL | Access request update',
                    '<p>Thank you for your interest in CareIL. Your access request was not approved at this time.</p>',
                )
            except Exception:
                current_app.logger.exception('Could not send access decline email')
            return redirect(url_for('careil_access_requests', message='Request declined.'))

        raw_token = secrets.token_urlsafe(48)
        expires = (_utc_now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            """UPDATE access_requests SET status='approved', token_hash=?, token_expires_at=?,
                      approved_at=CURRENT_TIMESTAMP, declined_at=NULL WHERE request_id=?""",
            (_access_token_hash(raw_token), expires, request_id),
        )
        conn.commit()
    finally:
        conn.close()
    registration_url = url_for('registration_page', token=raw_token, _external=True)
    try:
        _send_access_email(
            row['email'], 'CareIL | Your registration was approved',
            f'<p>Hello {html.escape(row["full_name"])},</p><p>Your CareIL access request was approved.</p>'
            f'<p><a href="{registration_url}" style="display:inline-block;padding:12px 18px;border-radius:10px;background:#588157;color:white;text-decoration:none">Create your CareIL account</a></p>'
            '<p>This private registration link is valid for seven days and can be used once.</p>',
        )
    except Exception:
        current_app.logger.exception('Could not send approved registration link')
        return redirect(url_for('careil_access_requests', message='Approved, but email delivery failed. Approve again to issue a new link.'))
    return redirect(url_for('careil_access_requests', message='Approved and registration link sent.'))

@app.route("/register", methods=['GET'])
def registration_page():
    supplied_token = request.args.get('token', '')
    if supplied_token:
        invitation = _approved_access_request(supplied_token)
        if not invitation:
            return render_template('registration-forbidden.html'), 403
        session['approved_registration_token'] = supplied_token
        return redirect(url_for('registration_page'))
    token = session.get('approved_registration_token', '')
    invitation = _approved_access_request(token)
    if not invitation:
        return render_template('registration-forbidden.html'), 403
    return render_template(
        'register.html', alert="", verification_step=0, email_step=0,
        invitation=invitation, registration_token=token,
    )

@app.route("/register", methods=['POST'])
def registration_request():
    registration_token = session.get('approved_registration_token', '')
    invitation = _approved_access_request(registration_token)
    if not invitation:
        return render_template('registration-forbidden.html'), 403
    form = dict(request.values)
    form['name'] = invitation['full_name']
    form['email'] = invitation['email']
    required_legal = ('accept_privacy', 'accept_terms', 'accept_dpa')
    if not all(request.form.get(field) == 'yes' for field in required_legal):
        return render_template(
            'register.html',
            alert='You must accept the Privacy Policy, Terms of Service and Data Processing Agreement.',
            verification_step=0,
            email_step=0,
            invitation=invitation,
            registration_token=registration_token,
        ), 400
    folderid="0"
    if 'folderid' in request.values:
        folderid = request.values['folderid']
    id="1"
    if 'id' in request.values:
        id = request.values['id']
    reg_email = request.values.get('email', '').strip()
    if reg_email:
        # Generate a unique client_key (e.g., UUID or hash)
        #client_key = f"client_{hash(form['userid'])}"
        client_key = generate_client_key(form['userid'])         
        form['client_key'] = client_key
        # Check if the client key/database already exists
        db_path = db_manager.get_db_path(client_key)
        if os.path.exists(db_path):
            return {"error": f"Client with key '{client_key}' already exists."}, 400
        # Create the client-specific database
        db_manager.create_client_database(client_key)  
        session['client_key'] =  client_key
        #create new connection
        checkconn= db_manager.connect_to_db(client_key)
        ok = create_account(form)
        ensure_single_therapist(client_key, form)
        _record_legal_acceptances(
            checkconn,
            form['userid'],
            language=request.form.get('legal_language', 'en'),
            marketing=request.form.get('marketing_consent') == 'yes',
        )
        checkconn.close()
        session['formData'] = form
        print('ok:' ,ok)
        if ok == 1: 
            central_conn = _central_database()
            try:
                central_conn.execute(
                    """UPDATE access_requests SET status='registered', used_at=CURRENT_TIMESTAMP,
                              token_hash=NULL WHERE request_id=? AND token_hash=? AND used_at IS NULL""",
                    (invitation['request_id'], _access_token_hash(registration_token)),
                )
                central_conn.commit()
            finally:
                central_conn.close()
            session.pop('approved_registration_token', None)
            logger.info("New User Created: "+ form['name'])
            session['pending_verification_userid'] = form['userid']
            session['verification_step'] = 0
            session['email_step'] = 1               
            return render_template('register.html',alert="", verification_step=session['verification_step'], email_step=session['email_step'])          
        else:
            return redirect(f"/error") 
    else:
         return render_template('/register.html',alert = "Please insert valid email to register!", verification_step=0, email_step=0) 

@app.route("/login", methods=['GET'])
def login_page():
    return render_template('login.html',alert ="")

@app.route("/login", methods=['POST'])
def login_request():    
    form = dict(request.values)
    client_key = generate_client_key(form['userid'])    
    form['client_key'] = client_key          
    users = database_read("select * from accounts where userid=:userid",form,client_key=client_key)    
    formid = form['userid']
    if users :
        if len(users) == 1: #user name exist, password not checked
            salt = users[0]['salt']
            saved_key = users[0]['password']
            generated_key = hashlib.pbkdf2_hmac('sha256',form['password'].encode('utf-8'),salt.encode('utf-8'),10000).hex()            
            if saved_key == generated_key: #password match
                session['client_key'] = client_key
                if users[0].get('deletion_requested_at'):
                    flask_login.logout_user()
                    if (users[0].get('deletion_purge_at') or '') <= _utc_now().strftime('%Y-%m-%d %H:%M:%S'):
                        return render_template(
                            '/login.html',
                            alert='This account recovery period has expired.',
                        ), 410
                    session['pending_restore_client_key'] = client_key
                    session['pending_restore_userid'] = formid
                    return render_template(
                        'account-deletion-pending.html',
                        purge_at=users[0].get('deletion_purge_at'),
                    )
                if not bool(users[0].get('email_verified')):
                    flask_login.logout_user()
                    session['pending_verification_userid'] = formid
                    session['email_step'] = 1
                    session['verification_step'] = 0
                    return render_template(
                        'register.html',
                        alert="Please verify your email before signing in.",
                        verification_step=0,
                        email_step=1,
                    )
                user = load_user(formid)                 
                logger.info(f"Login successfull - '{formid}'  date: {str(datetime.datetime.now())}")
                # Store client_key in the session
                session['client_key'] = user.client_key            
                ensure_single_therapist(client_key, users[0])
                flask_login.login_user(user)
                return redirect('/')                        
            else: #password incorrect
                logger.info(f"Login Failed - '{formid}'  date: {str(datetime.datetime.now())}")
                return render_template('/login.html',alert = "Invalid user/password. please try again.") 
        else: #user name does not exist
            logger.info(f"Login Failed - '{formid}'  date: {str(datetime.datetime.now())}")
            return render_template('/login.html',alert = "Invalid user/password. please try again.")
        

@app.route('/enter_email', methods=['POST'])
def enter_email():
    client_key = session.get('client_key')
    pending_userid = session.get('pending_verification_userid')
    if not client_key or not pending_userid:
        flash("Your session expired. Please log in and try again.", "warning")
        return redirect(url_for('login_page'))

    email = request.form.get('email', '').strip()
    if not email:
        flash("Please enter a valid email address.", "danger")
        return redirect(url_for('registration_page'))
    session['email'] = email
    database_write(
        "UPDATE accounts SET email=? WHERE userid=?",
        (email, pending_userid),
    )
    
    # Generate a random verification code
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Store the verification code in the database with an expiration time (e.g., 10 minutes from now)
    expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
    store_verification_code(client_key, verification_code, expiration_time)

    # Send the verification code email
    if not send_verification_code(email, verification_code):
        session['email_step'] = 1
        session['verification_step'] = 0
        return render_template(
            'register.html',
            alert="The verification email could not be sent. Please try again.",
            verification_step=0,
            email_step=1,
        )

    # Store the code in the session to verify later
    session['verification_code'] = verification_code
    session['email_step'] = 0
    session['verification_step'] = 1
    return render_template(
        'register.html',
        alert="",
        email=email,
        verification_step=1,
        email_step=0,
    )

# Route for 2FA verification (User enters verification code)
@app.route('/verify', methods=['POST'])
def verify():
    client_key = session.get('client_key')
    pending_userid = session.get('pending_verification_userid')
    if not client_key or not pending_userid:
        flash("Your verification session expired. Please log in again.", "warning")
        return redirect(url_for('login_page'))

    entered_code = request.form.get('verification_code', '').strip()
    if not entered_code:
        return render_template(
            'register.html',
            alert="Please enter the verification code.",
            email=session.get('email', ''),
            verification_step=1,
            email_step=0,
        )

    # Verify the entered code
    print("entered_code",entered_code)
    if verify_code(client_key, entered_code):
        database_write(
            "UPDATE accounts SET email_verified=1 WHERE userid=?",
            (pending_userid,),
        )
        user = load_user(pending_userid)
        if not user:
            flash("The account could not be loaded after verification. Please sign in.", "warning")
            return redirect(url_for('login_page'))
        flask_login.login_user(user)
        session.pop('pending_verification_userid', None)
        session.pop('verification_code', None)
        session['verification_step'] = 0
        session['email_step'] = 0
        flash("Email verified successfully!", "success")
        return redirect('/')
    else:
        return render_template(
            'register.html',
            alert="Incorrect or expired code. Please try again.",
            email=session.get('email', ''),
            verification_step=1,
            email_step=0,
        )

@app.route("/logout")
@flask_login.login_required
def logout_page():
    session.pop('client_key', None)
    flask_login.logout_user()
    return redirect("/")

@app.route('/demo/start', methods=['POST'])
def start_demo():
    flask_login.logout_user()
    session.clear()
    demo_databases = list(pathlib.Path(db_manager.base_db_path).glob('CareIL_demo_*.db'))
    if len(demo_databases) >= 50:
        return render_template(
            'landing.html', demo_error='The demo is busy. Please try again shortly.'
        ), 503
    client_key = 'demo_' + uuid.uuid4().hex
    db_manager.create_client_database(client_key)
    conn = db_manager.connect_to_db(client_key)
    try:
        userid = 'demo-' + uuid.uuid4().hex[:10]
        salt = str(uuid.uuid4())
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', secrets.token_bytes(24), salt.encode('utf-8'), 10000
        ).hex()
        conn.execute(
            "INSERT INTO users (userid, client_key) VALUES (?, ?)",
            (userid, client_key),
        )
        conn.execute(
            """INSERT INTO accounts
               (userid, salt, password, email, name, client_key, email_verified, is_demo)
               VALUES (?, ?, ?, ?, ?, ?, 1, 1)""",
            (userid, salt, password_hash, 'demo@careil.net', 'Demo Therapist', client_key),
        )
        cursor = conn.execute(
            """INSERT INTO doctor
               (doc_first_name, doc_last_name, doc_ph_no, doc_email, doc_address, userid)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('Demo', 'Therapist', '', 'demo@careil.net', 'CareIL Demo Clinic', userid),
        )
        doctor_id = cursor.lastrowid
        demo_clients = [
            ('Noa', 'Levi', '1001', '050-000-0001', 'noa@example.test', 'Haifa'),
            ('Daniel', 'Cohen', '1002', '050-000-0002', 'daniel@example.test', 'Tel Aviv'),
            ('Maya', 'Israel', '1003', '050-000-0003', 'maya@example.test', 'Jerusalem'),
        ]
        patient_ids = []
        for first, last, insurance, phone, email, address in demo_clients:
            patient = conn.execute(
                """INSERT INTO patient
                   (pat_first_name, pat_last_name, pat_insurance_no, pat_ph_no,
                    pat_email, pat_address, client_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (first, last, insurance, phone, email, address, client_key),
            )
            patient_ids.append(patient.lastrowid)
        tomorrow = (_utc_now() + datetime.timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        ).strftime('%Y-%m-%d %H:%M:%S')
        next_week = (_utc_now() + datetime.timedelta(days=7)).replace(
            hour=16, minute=30, second=0, microsecond=0
        ).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "INSERT INTO appointment (pat_id, doc_id, appointment_date) VALUES (?, ?, ?)",
            (patient_ids[0], doctor_id, tomorrow),
        )
        conn.execute(
            "INSERT INTO appointment (pat_id, doc_id, appointment_date) VALUES (?, ?, ?)",
            (patient_ids[1], doctor_id, next_week),
        )
        conn.commit()
    finally:
        conn.close()
    session['client_key'] = client_key
    user = User(userid, 'demo@careil.net', 'Demo Therapist', client_key)
    flask_login.login_user(user)
    return redirect('/')

@app.route('/robots.txt')
def robots_txt():
    body = "User-agent: *\nAllow: /$\nDisallow: /admin/\nDisallow: /portal/\nDisallow: /login\nDisallow: /register\nSitemap: https://www.careil.net/sitemap.xml\n"
    return current_app.response_class(body, mimetype='text/plain')


@app.route('/apple-touch-icon.png')
@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon():
    """Serve the iOS home-screen icon at Apple's conventional root paths."""
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'),
        'apple-touch-icon.png',
        mimetype='image/png',
        max_age=86400,
    )

@app.route('/legal/<document_key>')
@app.route('/he/legal/<document_key>')
def legal_document(document_key):
    if document_key not in LEGAL_DOCUMENTS:
        abort(404)
    lang = 'he' if request.path.startswith('/he/') else 'en'
    labels = {
        'en': {
            'privacy': 'Privacy Policy', 'terms': 'Terms of Service',
            'dpa': 'Data Processing Agreement', 'cookies': 'Cookie Policy',
            'accessibility': 'Accessibility', 'refunds': 'Cancellation & Refunds',
            'subprocessors': 'Subprocessors', 'security': 'Security & Retention',
        },
        'he': {
            'privacy': 'מדיניות פרטיות', 'terms': 'תנאי שימוש',
            'dpa': 'נספח עיבוד מידע', 'cookies': 'מדיניות עוגיות',
            'accessibility': 'נגישות', 'refunds': 'ביטול והחזרים',
            'subprocessors': 'ספקי משנה', 'security': 'אבטחה ושמירה',
        },
    }
    canonical_path = f"{'/he' if lang == 'he' else ''}/legal/{document_key}"
    alternate_path = f"{'/legal' if lang == 'he' else '/he/legal'}/{document_key}"
    return render_template(
        'legal.html', document=LEGAL_DOCUMENTS[document_key][lang],
        document_key=document_key, lang=lang,
        navigation=list(labels[lang].items()), version=LEGAL_VERSION,
        effective_date=LEGAL_EFFECTIVE_DATE, canonical_path=canonical_path,
        alternate_path=alternate_path, **_legal_operator_context()
    )

@app.route('/legal/accept', methods=['GET', 'POST'])
@flask_login.login_required
def legal_acceptance():
    user = flask_login.current_user.get_dict()
    if 'userid' not in user:
        abort(403)
    if request.method == 'POST':
        if not all(request.form.get(field) == 'yes' for field in (
                'accept_privacy', 'accept_terms', 'accept_dpa')):
            return render_template(
                'legal-acceptance.html', user=user, version=LEGAL_VERSION,
                error='All three required documents must be accepted.'
            ), 400
        conn = DatabaseManager(user['client_key']).connect_to_db(user['client_key'])
        try:
            _record_legal_acceptances(
                conn, user['userid'], request.form.get('legal_language', 'en'),
                request.form.get('marketing_consent') == 'yes'
            )
        finally:
            conn.close()
        return redirect('/')
    return render_template(
        'legal-acceptance.html', user=user, version=LEGAL_VERSION, error=''
    )

@app.route('/sitemap.xml')
def sitemap_xml():
    urls = [
        'https://www.careil.net/', 'https://www.careil.net/he',
        'https://www.careil.net/he/articles', 'https://www.careil.net/he/faq',
    ]
    urls.extend(
        f'https://www.careil.net/he/articles/{slug}' for slug in HEBREW_ARTICLES
    )
    for key in LEGAL_DOCUMENTS:
        urls.extend([
            f'https://www.careil.net/legal/{key}',
            f'https://www.careil.net/he/legal/{key}',
        ])
    entries = ''.join(
        f'<url><loc>{url}</loc><changefreq>monthly</changefreq></url>' for url in urls
    )
    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + entries + '</urlset>')
    return current_app.response_class(body, mimetype='application/xml')

@app.route('/admin/danger-zone')
@flask_login.login_required
@admin_only
def danger_zone():
    user = flask_login.current_user.get_dict()
    return render_template('danger-zone.html', user=user)

@app.route('/account/delete', methods=['POST'])
@flask_login.login_required
@admin_only
def request_account_deletion():
    user = flask_login.current_user.get_dict()
    if session.get('client_key', '').startswith('demo_'):
        return render_template('demo-blocked.html'), 403
    confirmation = request.form.get('confirmation', '').strip()
    password = request.form.get('password', '')
    if confirmation != 'DELETE CAREIL':
        return render_template(
            'danger-zone.html', user=user,
            error='Type DELETE CAREIL exactly to continue.'
        ), 400
    accounts = database_read(
        'SELECT * FROM accounts WHERE userid=?',
        (user['userid'],), client_key=user['client_key']
    )
    if len(accounts) != 1:
        abort(404)
    account = accounts[0]
    candidate = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), account['salt'].encode('utf-8'), 10000
    ).hex()
    if not hmac.compare_digest(candidate, account['password']):
        return render_template(
            'danger-zone.html', user=user, error='The password is incorrect.'
        ), 400

    token = secrets.token_urlsafe(40)
    requested_at = _utc_now()
    purge_at = requested_at + datetime.timedelta(hours=24)
    database_write(
        """UPDATE accounts SET deletion_requested_at=?, deletion_purge_at=?,
           deletion_token_hash=? WHERE userid=?""",
        (
            requested_at.strftime('%Y-%m-%d %H:%M:%S'),
            purge_at.strftime('%Y-%m-%d %H:%M:%S'),
            hashlib.sha256(token.encode('utf-8')).hexdigest(),
            user['userid'],
        ),
    )
    restore_url = url_for(
        'restore_deleted_account', client_key=user['client_key'], token=token,
        _external=True
    )
    if resend_is_configured() and user.get('email'):
        try:
            send_resend_email(
                user['email'], 'CareIL | Account deletion requested',
                email_brand_header()
                + '<p>Your CareIL workspace is suspended and scheduled for permanent deletion in 24 hours.</p>'
                + f'<p><a href="{restore_url}">Undo account deletion</a></p>'
                + '<p>If you requested deletion, no action is needed.</p>',
                attachments=[careil_logo_attachment(os.path.dirname(__file__))],
            )
        except Exception:
            current_app.logger.exception('Could not send account restoration email')
    flask_login.logout_user()
    session.clear()
    return render_template('account-deletion-requested.html', purge_at=purge_at)

def _valid_restore_client_key(client_key):
    if not client_key.startswith('client_'):
        return False
    digest = client_key[len('client_'):]
    return len(digest) == 64 and all(char in string.hexdigits for char in digest)

@app.route('/account/restore/<client_key>/<token>')
def restore_deleted_account(client_key, token):
    if not _valid_restore_client_key(client_key):
        abort(404)
    try:
        conn = DatabaseManager(client_key).connect_to_db(client_key)
    except FileNotFoundError:
        return render_template('account-restore-result.html', restored=False), 410
    try:
        account = conn.execute(
            "SELECT deletion_purge_at, deletion_token_hash FROM accounts "
            "WHERE deletion_token_hash IS NOT NULL LIMIT 1"
        ).fetchone()
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        now_text = _utc_now().strftime('%Y-%m-%d %H:%M:%S')
        if (not account or not hmac.compare_digest(
                account.get('deletion_token_hash') or '', token_hash)
                or account.get('deletion_purge_at', '') <= now_text):
            return render_template('account-restore-result.html', restored=False), 410
        conn.execute(
            """UPDATE accounts SET deletion_requested_at=NULL,
               deletion_purge_at=NULL, deletion_token_hash=NULL"""
        )
        conn.commit()
    finally:
        conn.close()
    return render_template('account-restore-result.html', restored=True)

@app.route('/account/restore', methods=['POST'])
def restore_account_after_login():
    client_key = session.get('pending_restore_client_key')
    userid = session.get('pending_restore_userid')
    if not client_key or not userid or not _valid_restore_client_key(client_key):
        return redirect(url_for('login_page'))
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        account = conn.execute(
            "SELECT deletion_purge_at FROM accounts WHERE userid=? LIMIT 1",
            (userid,),
        ).fetchone()
        if (not account or not account.get('deletion_purge_at')
                or account['deletion_purge_at'] <= _utc_now().strftime('%Y-%m-%d %H:%M:%S')):
            session.clear()
            return render_template('account-restore-result.html', restored=False), 410
        conn.execute(
            """UPDATE accounts SET deletion_requested_at=NULL,
               deletion_purge_at=NULL, deletion_token_hash=NULL WHERE userid=?""",
            (userid,),
        )
        conn.commit()
    finally:
        conn.close()
    session.clear()
    flash('Your CareIL account was restored. You can sign in now.', 'success')
    return redirect(url_for('login_page'))

#endregion

#region General Route

@app.route("/error")
def error_page():
    return "there was an Error"

@app.route("/calendar")
@flask_login.login_required
def calendar_page():
    user = flask_login.current_user.get_dict()
    apps = Appointments()
    appointments = apps.get()
    duration = int(_availability_settings(user['client_key'])['APPOINTMENT_DURATION'])
    return render_template('calendar.html',user=user,appointments=appointments,appointment_duration=duration)

@app.route('/service-worker.js')
def service_worker():
    response = send_from_directory(app.static_folder, 'service-worker.js')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/send-mail', methods=['GET',"POST"])
def send_appointment(notification=''):
    user = flask_login.current_user.get_dict()    
    #Mail settings
    client_key = user['client_key']
    mail_settings = get_Mail_settings(client_key)
    app.config.update(mail_settings)
    mail = Mail(app)
    data = dict(request.values)
    my_lang = data['lang']
    print(my_lang)    
    pat_data =  database_read(f"select * from patient where pat_id= '{data['id']}';",client_key=client_key)
    doc_id = data['doc_id']
    doc_data =  database_read(f"select * from doctor where doc_id= '{doc_id}';",client_key=client_key)
    pat_id = pat_data[0]['pat_id']
    pat_email = pat_data[0]['pat_email']
    doc_fullname = doc_data[0]['doc_first_name']+" " + doc_data[0]['doc_last_name'] 
    pat_fullname = pat_data[0]['pat_first_name']+" "+pat_data[0]['pat_last_name']
    doc_address = doc_data[0]['doc_address']
    #gmail_url = add Appointment to calendar
    if my_lang=='HE':
        subject = "CareIL | פגישת טיפול עם: " + doc_fullname
    else:
        subject = "CareIL | Appointment with: " + doc_fullname
    sender_email = resend_sender_address() if resend_is_configured() else str(mail_settings['MAIL_USERNAME'])
    receiver_email = pat_email
    
    #Build Msg
    # Email content
    #Portal_url = request.host_url + f"/clients/client_login"
    base_url = request.host_url + "/portal"
    Portal_url = generate_patient_portal_url(base_url, pat_id, client_key)
    appointmentDuration = data['appointment_date']

    format = "%Y-%m-%dT%H:%M:%S.%fZ"
    Varformat = "%Y-%m-%d %H:%M:%S"

    date_obj = datetime.datetime.strptime(appointmentDuration, Varformat)
    duration = int(_availability_settings(client_key)['APPOINTMENT_DURATION'])
    time_change = datetime.timedelta(minutes=duration)
    appointmentEnd = date_obj + time_change 
    
    if my_lang=='HE':
        notification = 'נשמח לראותך '
        email_body = '''
                    <div id='App_mail' style="text-align: right;direction: rtl;" >
                    <b>נושא :</b> {Subject}<br>
                    <b>מטופל :</b> {Patient}<br>
                    <b>תאריך פגישה :</b> {Appointment Date}<br>
                    <br>
                    <b></b><br>
                    {note}
                    </div>
                    <!-- Button code -->
                    ''' 
    else:
        notification = 'We will be happy to see you. '
        email_body = '''
                    <div id='App_mail' style="text-align: right;direction: rtl;" >
                    <b>Subject :</b> {Subject}<br>
                    <b>Client:</b> {Patient}<br>
                    <b>Appointment date :</b> {Appointment Date}<br>
                    <br>
                    <b></b><br>
                    {note}
                    </div>
                    <!-- Button code -->
                    ''' 
    # Email data
    email_data = {
            'Subject': subject,    
            'Patient': pat_fullname,
            'Appointment Date': data['appointment_date'],
            'note': notification
            }          
    
    email_content = email_brand_header() + email_body.format(**email_data)
    email_content += f"<br><p><a href={Portal_url}>Log In to Portal</a></p>"

   

    # Create MIME message ICS File
    if my_lang=='HE':
        desc = u'פגישת טיפול'
    else:
        desc = u'Therapy session'        
    ics = render_ics(
            title=desc,
            description=desc,
            location= doc_address,
            start= date_obj,
            end= appointmentEnd,
            created=None,
            admin=sender_email,
            admin_mail=sender_email
        )
    if resend_is_configured():
        send_resend_email(
            receiver_email,
            subject,
            email_content,
            attachments=[
                careil_logo_attachment(os.path.dirname(__file__)),
                encoded_attachment(ics, "calendar.ics", "text/calendar"),
            ],
        )
        print('Email sent through Resend!')
        return redirect(f"/appointment")

    message = MIMEMultipart('related')    
    message['From'] = sender_email
    message['To'] = receiver_email    
    message['Subject'] = str(subject)
    message.attach(MIMEText(email_content,'html',_charset='utf-8')) 
    message.attach(MIMEText(email_content,'text/calendar',_charset='utf-8'))    
    attach_email_logo(message)
    #calendar
    
    attachment = MIMEBase('text', 'calendar; name=calendar.ics; method=REQUEST; charset=UTF-8')
    attachment.set_payload(ics.encode('utf-8'))
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename=%s' % "calendar.ics")
    
    message.attach(attachment)
    # Connect to the SMTP server and send the email
    with smtplib.SMTP(mail_settings['MAIL_SERVER'], 587) as server:
        server.starttls()
        server.login(mail_settings['MAIL_USERNAME'], mail_settings['MAIL_PASSWORD'])        
        server.sendmail(sender_email, receiver_email, message.as_string().encode("UTF-8"))
        server.close()
    print('Email sent!')
    return redirect(f"/appointment")

def _google_calendar_redirect_uri():
    return os.environ.get('GOOGLE_REDIRECT_URI') or url_for('google_calendar_callback', _external=True)


def _google_calendar_return_path(value):
    """Allow OAuth to return only to known local CareIL pages."""
    allowed = {'/calendar', '/admin/google-calendar', '/admin/adminPanel'}
    return value if value in allowed else '/admin/google-calendar'


@app.route('/admin/google-calendar')
@admin_only
def google_calendar_settings():
    user = flask_login.current_user.get_dict()
    configured = google_calendar_is_configured()
    connected = google_calendar_connection_status(user['client_key'], user['userid']) if configured else None
    return render_template(
        'google-calendar.html', user=user, configured=configured, connected=connected
    )


@app.route('/google-calendar/connect')
@admin_only
def google_calendar_connect():
    if not google_calendar_is_configured():
        return redirect(url_for('google_calendar_settings', error='Google credentials are not configured'))
    return_path = _google_calendar_return_path(request.args.get('next'))
    session['google_oauth_return'] = return_path
    try:
        code_verifier = secrets.token_urlsafe(64)
        flow = create_oauth_flow(
            _google_calendar_redirect_uri(), code_verifier=code_verifier
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline', include_granted_scopes='true',
            prompt='select_account consent'
        )
    except ImportError:
        return redirect(url_for('google_calendar_settings', error='Install the Google Calendar dependencies first'))
    session['google_oauth_state'] = state
    session['google_oauth_code_verifier'] = code_verifier
    return redirect(authorization_url)


@app.route('/google-calendar/callback')
@admin_only
def google_calendar_callback():
    expected_state = session.pop('google_oauth_state', None)
    code_verifier = session.pop('google_oauth_code_verifier', None)
    if not expected_state or request.args.get('state') != expected_state:
        abort(400, description='Invalid Google OAuth state')
    if not code_verifier:
        abort(400, description='Google OAuth session expired. Please connect again.')
    flow = create_oauth_flow(
        _google_calendar_redirect_uri(), state=expected_state,
        code_verifier=code_verifier
    )
    public_callback_url = _google_calendar_redirect_uri()
    authorization_response = public_callback_url
    if request.query_string:
        authorization_response += '?' + request.query_string.decode('utf-8')
    flow.fetch_token(authorization_response=authorization_response)
    user = flask_login.current_user.get_dict()
    save_google_calendar_connection(user['client_key'], user['userid'], flow.credentials)
    try:
        synced = sync_all_google_appointments(user['client_key'])
    except Exception:
        current_app.logger.exception('Initial Google Calendar sync failed')
        synced = 0
    return_path = _google_calendar_return_path(session.pop('google_oauth_return', None))
    if return_path == '/calendar':
        return redirect(url_for('calendar_page', connected='1', synced=synced))
    return redirect(url_for('google_calendar_settings', connected='1', synced=synced))


@app.route('/google-calendar/sync', methods=['POST'])
@admin_only
def google_calendar_sync_now():
    user = flask_login.current_user.get_dict()
    return_to_calendar = request.form.get('next') == '/calendar'
    if not google_calendar_is_configured():
        return redirect(url_for(
            'google_calendar_settings',
            error='Google Calendar credentials are not configured yet.'
        ))
    if not google_calendar_connection_status(user['client_key'], user['userid']):
        destination = '/calendar' if return_to_calendar else '/admin/google-calendar'
        return redirect(url_for('google_calendar_connect', next=destination))
    try:
        synced = sync_all_google_appointments(user['client_key'])
        if return_to_calendar:
            return redirect(url_for('calendar_page', synced=synced))
        return redirect(url_for('google_calendar_settings', synced=synced))
    except Exception:
        current_app.logger.exception('Manual Google Calendar sync failed')
        if return_to_calendar:
            return redirect(url_for('calendar_page', sync_error='Calendar sync failed. Reconnect Google Calendar.'))
        return redirect(url_for('google_calendar_settings', error='Calendar sync failed. Reconnect Google Calendar.'))


@app.route('/google-calendar/disconnect', methods=['POST'])
@admin_only
def google_calendar_disconnect():
    user = flask_login.current_user.get_dict()
    disconnect_google_calendar(user['client_key'], user['userid'])
    return redirect(url_for('google_calendar_settings', disconnected='1'))


def _morning_csrf_token():
    if not session.get('morning_csrf'):
        session['morning_csrf'] = secrets.token_urlsafe(32)
    return session['morning_csrf']


def _valid_morning_csrf():
    return hmac.compare_digest(
        request.form.get('csrf_token', ''), session.get('morning_csrf', '')
    )


@app.route('/admin/morning', methods=['GET', 'POST'])
@admin_only
def morning_settings():
    user = flask_login.current_user.get_dict()
    client_key = user['client_key']
    if request.method == 'POST':
        if not _valid_morning_csrf():
            abort(400)
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()
        environment = request.form.get('environment', 'production')
        if not client_id or not client_secret:
            return redirect(url_for('morning_settings', error='Enter both Morning API key values.'))
        try:
            save_morning_connection(client_key, client_id, client_secret, environment)
        except MorningError as error:
            current_app.logger.warning('Morning connection failed: %s', error)
            return redirect(url_for('morning_settings', error=str(error)))
        return redirect(url_for('morning_settings', connected='1'))
    return render_template(
        'morning-settings.html', user=user,
        connected=morning_connection_status(client_key),
        csrf_token=_morning_csrf_token(),
    )


@app.route('/admin/morning/disconnect', methods=['POST'])
@admin_only
def morning_disconnect():
    if not _valid_morning_csrf():
        abort(400)
    user = flask_login.current_user.get_dict()
    disconnect_morning(user['client_key'])
    return redirect(url_for('morning_settings', disconnected='1'))


@app.route('/patients/<int:pat_id>/appointments/<int:app_id>/receipt', methods=['POST'])
@flask_login.login_required
def create_appointment_receipt(pat_id, app_id):
    if not _valid_morning_csrf():
        abort(400)
    user = flask_login.current_user.get_dict()
    try:
        result = issue_morning_receipt(
            user['client_key'], pat_id, app_id,
            request.form.get('amount'),
            request.form.get('payment_type', type=int),
            request.form.get('payment_date', ''),
            'he' if request.form.get('language') == 'he' else 'en',
        )
        flash(
            'Receipt issued successfully' + (f' (#{result["number"]})' if result.get('number') else '') + '.',
            'success',
        )
    except MorningError as error:
        flash(str(error), 'danger')
    except Exception:
        current_app.logger.exception('Morning receipt creation failed')
        flash('The receipt could not be issued. Please try again or check Morning Settings.', 'danger')
    return redirect(url_for('patient_folder_Load', id=pat_id) + '#appointments')


@app.route('/admin/mail-settings', methods=['GET', 'POST'])
@admin_only
def mail_settings():

    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)

    if request.method == 'POST':
        # Update each setting from the form data
        for key in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USERNAME', 'MAIL_PASSWORD']:
            if key in request.form and (key != 'MAIL_PASSWORD' or request.form[key]):
                update_Mail_setting(key, request.form[key])        
        flash("Mail settings updated successfully!", "success")
        return redirect(url_for('mail_settings'))

    # Fetch current settings to display in the form
    settings = get_Mail_settings(client_key)
    conn.close()
    return render_template('mail_settings.html', settings=settings)

@app.route('/SendNotification', methods=['POST'])
def Send_mail_Notification():
    data = dict(request.values)
    client_key = session['client_key']
    patien_id = database_read(f"select pat_id from patient WHERE pat_email ='{data['pat_email']}' order by pat_date desc LIMIT 1;",client_key=client_key)
    patien_data =  database_read(f"select * from patient WHERE pat_email ='{data['pat_email']}' order by pat_date desc LIMIT 1;",client_key=client_key)
    clinic_data =  database_read(f"select * from clinicinfo LIMIT 1;",client_key=client_key)
    data['client_key'] = client_key
    data['pat_id'] = patien_id[0]['pat_id']
    data['patien_data'] = patien_data
    data['clinic_data'] = clinic_data
    send_notification(data)
    return "ok"

@app.route('/admin/clinic-info', methods=['GET'])
@admin_only
def get_clinic_info():
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    clinic_info = {}
    result = database_read("SELECT name, address, phone, email, website FROM clinicinfo LIMIT 1",client_key=client_key)
    if not result:
        return render_template('clinic-info.html', clinic=None, error="Clinic information not found"), 404
    return render_template('clinic-info.html', clinic=result[0])

@app.route('/admin/clinic-info', methods=['POST'])
@admin_only
def update_clinic_info():
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    data = dict(request.values)
    cursor = conn.cursor()
  # Validate the input
    required_fields = ['name', 'address', 'phone', 'email']
    for field in required_fields:
        if field not in data or not data[field]:
             jsonify({"error": f"{field} is required"}), 400
    name =  data.get('name')
    address =  data.get('address')
    phone =  data.get('phone')
    email =  data.get('email')
    website =  data.get('website')
    # Construct the raw SQL update query
    clinic = database_read("SELECT * FROM clinicinfo LIMIT 1",client_key=client_key)
    if clinic:
        #Update
        query = f"UPDATE clinicinfo SET name ='{name}',address = '{address}',phone = '{phone}',email = '{email}',website = '{website}' WHERE id = 1"
        updateClinic = database_write(query,data)
        if updateClinic == 1 :
            flash("Clinic information updated successfully!", "success")
            return render_template('clinic-info.html', clinic=data)
    else:
      query = f"INSERT into  clinicinfo (name,address,phone,email,website) VALUES('{name}','{address}','{phone}','{email}','{website}');"
      ok = database_write(query,data)
      if ok == 1:
          flash("New Clinic information updated successfully!", "success")
          return render_template('clinic-info.html', clinic=data)

@app.route('/admin/adminPanel', methods=['GET'])
@admin_only
def admin_panel():
    return render_template('adminPanel.html', careil_owner=_careil_owner())

def _availability_settings(client_key):
    defaults = {
        'AVAILABILITY_DAYS': '0,1,2,3,4',
        'AVAILABILITY_START': '08:00',
        'AVAILABILITY_END': '18:00',
        'APPOINTMENT_DURATION': '60',
    }
    conn = db_manager.connect_to_db(client_key=client_key)
    try:
        rows = conn.execute(
            "SELECT key, value FROM settings WHERE key IN (?, ?, ?, ?)",
            tuple(defaults.keys())
        ).fetchall()
        for row in rows:
            defaults[row['key']] = row['value']
        return defaults
    finally:
        conn.close()

@app.route('/api/availability', methods=['GET'])
def availability_api():
    client_key = session.get('client_key')
    if not client_key:
        return jsonify({'error': 'Clinic context is required.'}), 401
    settings = _availability_settings(client_key)
    return jsonify({
        'days': [int(day) for day in settings['AVAILABILITY_DAYS'].split(',') if day != ''],
        'start': settings['AVAILABILITY_START'],
        'end': settings['AVAILABILITY_END'],
        'duration': int(settings['APPOINTMENT_DURATION'])
    })

@app.route('/admin/availability', methods=['GET', 'POST'])
@admin_only
def availability_settings():
    client_key = session['client_key']
    if request.method == 'POST':
        selected_days = request.form.getlist('days')
        start = request.form.get('start', '08:00')
        end = request.form.get('end', '18:00')
        duration = request.form.get('duration', '60')
        if not selected_days or start >= end:
            flash('Choose at least one day and make sure the end time is after the start time.', 'danger')
        else:
            conn = db_manager.connect_to_db(client_key=client_key)
            try:
                values = {
                    'AVAILABILITY_DAYS': ','.join(selected_days),
                    'AVAILABILITY_START': start,
                    'AVAILABILITY_END': end,
                    'APPOINTMENT_DURATION': duration,
                }
                for key, value in values.items():
                    conn.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (key, value)
                    )
                conn.commit()
                flash('Availability saved.', 'success')
            finally:
                conn.close()
            return redirect(url_for('availability_settings'))
    settings = _availability_settings(client_key)
    return render_template(
        'availability.html',
        settings=settings,
        selected_days=settings['AVAILABILITY_DAYS'].split(',')
    )

#endregion

#region file add/delete/upload handeling

@app.route("/new-folder", methods=["POST"])
@flask_login.login_required
def create_new_folder():
    form = dict(request.values)
    id = str(uuid.uuid1())
    form['id'] = id
    sql = f"INSERT into folders (userid,id,name) VALUES (:userid,:id,:name);"
    ok = database_write(sql,form)
    if ok == 1:
       return "OK" 
    else:
       return "ERROR"

@app.route('/upload', methods=['POST'])
def upload(): 
        user = flask_login.current_user.get_dict() 
        data=  dict(request.values)
        clientKey = user['client_key'][:10]
        UPLOAD_FOLDER = os.path.join(path, 'uploads',clientKey)
        print(UPLOAD_FOLDER)
        if not os.path.isdir(UPLOAD_FOLDER):
            print("no dir")
            os.mkdir(UPLOAD_FOLDER)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 

        id = data['id']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file :                           
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            create = datetime.datetime.now().strftime("%Y-%m-%d")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            sql = f"INSERT into Patientfiles (pat_id,filename,filepath,createdate,userid) VALUES ('{id}','{filename}','{filepath}','{create}','{user['userid']}');"
            
            print("Upload_Sql",sql)
            ok = database_write(sql,data)
            if ok == 1:
               print('File successfully uploaded')
               return redirect(f"/patientform?id={id}")            
            else:
               return "ERROR"
        else:
            print('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(request.url)

@app.route("/upload", methods=['GET'])
def upload_page():
    id = request.args.get('id')
    user = flask_login.current_user.get_dict()
    client_key = session['client_key'] 
    patientdata = database_read(f"select * from patient where pat_id= '{id}';",client_key = client_key)
    print("patientdata",patientdata)
    return render_template('upload.html',patientdata=patientdata)

@app.route('/delete_file', methods=['DELETE'])
@flask_login.login_required
def delete_file():
    user = flask_login.current_user.get_dict()
    data=  dict(request.values)
    clientKey = user['client_key'][:10]
    print("data",data)
    id = data['id']
    filename =  data['filename']
    sql = f"Delete from Patientfiles where pat_id ='{id}' and filename = '{filename}';"
    ok = database_write(sql,data)
    if ok == 1:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(filepath)
        print('File successfully Deleted')
        return render_template('patientform.html')                         
    else:
        return "ERROR" 

@app.route('/download_file/<path:filename>',methods=['GET',"POST"])
@flask_login.login_required
def download_file(filename):
    user = flask_login.current_user.get_dict()
    data=  dict(request.values)   
    client_key = session['client_key'] 
    myfile =  database_read(f"select * from Patientfiles where filename= '{filename}';" ,client_key = client_key)
    if myfile:
        str_path = myfile[0]['filepath']
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for name in files:            
                # As we need to get the provided python file, 
                # comparing here like this
                if name == filename:  
                    path = os.path.abspath(os.path.join(root, name))
                    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
                    return send_from_directory(uploads, filename)
    else:
         return "Error"

@app.route('/delete_folder', methods=['DELETE'])
@flask_login.login_required
def delete_folder():    
    data=  dict(request.values)
    user = flask_login.current_user.get_dict() 
    id = data['folderid']
    sql = f"Delete from folders where id = '{id}';"
    print(sql)
    ok = database_write(sql,data)
    if ok == 1:
        print('project successfully Deleted')
        #Log
        logger.info(f"Project deleted - '{data['foldername']}' has been Sent by: {user['userid']} date: {str(datetime.datetime.now())}")
        return "OK"            
    else:
        return "ERROR" 
    
#endregion
   
#region Therapy Routes
@app.route("/doctor", methods=['GET'])
@app.route("/therapist", methods=['GET'])
@app.route("/myprofile", methods=['GET'])
@admin_only
def doctor_Page():
    id = request.args.get('id')
    user = flask_login.current_user.get_dict()
    return render_template('doctor.html',Translate_data=Translate_data,user=user)

@app.route("/patient", methods=['GET'])
@flask_login.login_required
def patient_Page():
    id = request.args.get('id')
    user = flask_login.current_user.get_dict()
    return render_template('patient.html',Translate_data=Translate_data,user=user)

@app.route("/appointment", methods=['GET'])
@admin_only
def appointment_Page():
        id = request.args.get('id')
        user = flask_login.current_user.get_dict()
        return render_template('appointment.html',Translate_data=Translate_data,user=user)

@app.route("/patientform", methods=['GET'])
@flask_login.login_required
def patient_folder_Load():
    id = request.args.get('id', type=int)
    if id is None:
        flash("Please select a patient first.", "warning")
        return redirect(url_for('patient_Page'))
    client_key = session['client_key']
    messages = database_read(f"select * from messages where pat_id= '{id}';",client_key=client_key)
    user = flask_login.current_user.get_dict()    
    patientdata = database_read(f"select * from patient where pat_id= '{id}';",client_key=client_key)
    tasksfiles = database_read(f"select * from Patientfiles where pat_id= '{id}';",client_key=client_key) #id = pat_id
    diagnosis_types = database_read(
        "SELECT diagnosis_type_id, name FROM diagnosis_types ORDER BY name",
        client_key=client_key
    )
    patient_diagnoses = database_read(
        """SELECT pd.diagnosis_id, pd.diagnosed_on, pd.notes, dt.name
           FROM patient_diagnoses pd
           JOIN diagnosis_types dt ON dt.diagnosis_type_id = pd.diagnosis_type_id
           WHERE pd.pat_id = ? ORDER BY COALESCE(pd.diagnosed_on, pd.created_at) DESC""",
        (id,), client_key=client_key
    )
    questionnaire_templates = database_read(
        "SELECT template_id, title, instructions, questions_json FROM questionnaire_templates ORDER BY title",
        client_key=client_key
    )
    patient_questionnaires = database_read(
        """SELECT questionnaire_id, title, status, assigned_at, completed_at, answers_json
           FROM patient_questionnaires WHERE pat_id = ? ORDER BY assigned_at DESC""",
        (id,), client_key=client_key
    )
    for questionnaire in patient_questionnaires:
        try:
            questionnaire['response'] = json.loads(questionnaire.get('answers_json') or '{}')
        except (TypeError, ValueError):
            questionnaire['response'] = {}
    data = request.values
    if 'id' in request.values:
     id = request.values['id']
     #json.loads(data)
    if 'noteid' in request.values:
        noteid = request.values['noteid']
        med = Medicalnote()
        mednote = med.get(noteid)
    pat_id = id
    apps = Appointments()
    appointments = apps.getappointmentsbypatient(pat_id)
    now_value = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summaries_by_appointment = {
        row['app_id']: row['rec_id']
        for row in database_read(
            "SELECT rec_id, app_id FROM medrecords WHERE pat_id = ? AND app_id IS NOT NULL",
            (pat_id,), client_key=client_key
        )
    }
    for appointment in appointments:
        appointment['is_past'] = str(appointment.get('appointment_date') or '') < now_value
        appointment['summary_rec_id'] = summaries_by_appointment.get(appointment.get('app_id'))
    receipts_by_appointment = {
        row['app_id']: row
        for row in database_read(
            """SELECT app_id, document_number, document_url, amount, status
               FROM morning_receipts WHERE pat_id = ?""",
            (pat_id,), client_key=client_key
        )
    }
    for appointment in appointments:
        appointment['receipt'] = receipts_by_appointment.get(appointment.get('app_id'))
    notes = Medicalnotes()
    pat_mednotes = notes.getnotebypatient(pat_id)    
    length = len(pat_mednotes)
    for i in range(length):
        # GET ONLY TEXT from DB
        test= pat_mednotes[i]['body']       
        data = json.loads(test)        
        content_html = data.get('content', '')
        soup = BeautifulSoup(content_html, 'html.parser')
        text = soup.get_text() 
        # Get text and split by <br> tag
        text_list = [tag.get_text() for tag in soup.find_all(['div', 'br'])] 
        if len(text_list)> 1:     
            text_with_separators = ','.join(text_list)       
            pat_mednotes[i]["text"]=text_with_separators 
        else:
            pat_mednotes[i]["text"]=text
    session['patientdata'] = patientdata
    print("patientdata",patientdata)
    if not patientdata:
        abort(404)
    return render_template(
        'patientform.html', Translate_data=Translate_data, user=user,
        patient=patientdata[0], patientdata=patientdata, messages=messages,
        appointments=appointments, pat_mednotes=pat_mednotes, tasksfiles=tasksfiles,
        diagnosis_types=diagnosis_types, patient_diagnoses=patient_diagnoses,
        questionnaire_templates=questionnaire_templates,
        patient_questionnaires=patient_questionnaires,
        morning_connected=bool(morning_connection_status(client_key)),
        morning_payment_types=MORNING_PAYMENT_TYPES,
        morning_csrf_token=_morning_csrf_token(),
        today=datetime.date.today().isoformat(), alert=""
    )

@app.route("/patientform", methods=["POST"])
@flask_login.login_required
def update_patien():
    user = flask_login.current_user.get_dict()
    client_key =  user['client_key']
    form = dict(request.values)
    id = form['pat_id']
    sql = "UPDATE patient SET pat_first_name =:pat_first_name, pat_last_name =:pat_last_name, pat_ph_no =:pat_ph_no, pat_address=:pat_address, pat_email =:pat_email, pat_insurance_no =:pat_insurance_no where pat_id =:pat_id"
    ok = database_write(sql,form)   
    if ok == 1:
        patientdata = database_read(f"select * from patient where pat_id= '{id}';",client_key=client_key)
        message = 'Success'
        return render_template('patientform.html',user=user,patient=patientdata,message=message)
    else:
       return "ERROR"

@app.route('/api/patients/<int:pat_id>/diagnoses', methods=['POST'])
@flask_login.login_required
@admin_only
def add_patient_diagnosis(pat_id):
    client_key = session['client_key']
    payload = request.get_json(silent=True) or {}
    diagnosis_type_id = payload.get('diagnosis_type_id')
    new_type = str(payload.get('new_type') or '').strip()
    if not diagnosis_type_id and not new_type:
        return jsonify({'error': 'Select or enter a diagnosis type.'}), 400
    manager = DatabaseManager(client_key)
    conn = manager.connect_to_db(client_key)
    try:
        if not conn.execute("SELECT 1 FROM patient WHERE pat_id = ?", (pat_id,)).fetchone():
            return jsonify({'error': 'Patient not found.'}), 404
        if new_type:
            conn.execute("INSERT OR IGNORE INTO diagnosis_types(name) VALUES (?)", (new_type,))
            row = conn.execute(
                "SELECT diagnosis_type_id FROM diagnosis_types WHERE name = ? COLLATE NOCASE",
                (new_type,)
            ).fetchone()
            diagnosis_type_id = row['diagnosis_type_id']
        else:
            row = conn.execute(
                "SELECT diagnosis_type_id FROM diagnosis_types WHERE diagnosis_type_id = ?",
                (diagnosis_type_id,)
            ).fetchone()
            if not row:
                return jsonify({'error': 'Diagnosis type not found.'}), 404
        cursor = conn.execute(
            """INSERT INTO patient_diagnoses
               (pat_id, diagnosis_type_id, diagnosed_on, notes) VALUES (?, ?, ?, ?)""",
            (pat_id, diagnosis_type_id, payload.get('diagnosed_on') or None,
             str(payload.get('notes') or '').strip() or None)
        )
        conn.commit()
        return jsonify({'ok': True, 'diagnosis_id': cursor.lastrowid})
    finally:
        conn.close()

@app.route('/api/patients/<int:pat_id>/diagnoses/<int:diagnosis_id>', methods=['DELETE'])
@flask_login.login_required
@admin_only
def delete_patient_diagnosis(pat_id, diagnosis_id):
    updated = database_write(
        "DELETE FROM patient_diagnoses WHERE diagnosis_id = ? AND pat_id = ?",
        (diagnosis_id, pat_id)
    )
    if updated != 1:
        return jsonify({'error': 'Diagnosis not found.'}), 404
    return jsonify({'ok': True})

@app.route('/api/patients/<int:pat_id>/questionnaires', methods=['POST'])
@flask_login.login_required
@admin_only
def assign_patient_questionnaire(pat_id):
    client_key = session['client_key']
    payload = request.get_json(silent=True) or {}
    template_id = payload.get('template_id') or None
    title = str(payload.get('title') or '').strip()
    instructions = str(payload.get('instructions') or '').strip()
    questions = payload.get('questions') or []
    questions = [str(question).strip() for question in questions if str(question).strip()]
    manager = DatabaseManager(client_key)
    conn = manager.connect_to_db(client_key)
    try:
        patient = conn.execute(
            "SELECT pat_id, pat_first_name, pat_last_name, pat_email FROM patient WHERE pat_id = ?",
            (pat_id,)
        ).fetchone()
        if not patient:
            return jsonify({'error': 'Patient not found.'}), 404
        if template_id:
            template = conn.execute(
                "SELECT * FROM questionnaire_templates WHERE template_id = ?", (template_id,)
            ).fetchone()
            if not template:
                return jsonify({'error': 'Questionnaire template not found.'}), 404
            title = template['title']
            instructions = template.get('instructions') or ''
            questions_json = template['questions_json']
        else:
            if not title or not questions:
                return jsonify({'error': 'Enter a title and at least one question.'}), 400
            questions_json = json.dumps(questions, ensure_ascii=False)
            if payload.get('save_template'):
                try:
                    cursor = conn.execute(
                        """INSERT INTO questionnaire_templates
                           (title, instructions, questions_json, created_by) VALUES (?, ?, ?, ?)""",
                        (title, instructions or None, questions_json,
                         flask_login.current_user.get_id())
                    )
                    template_id = cursor.lastrowid
                except sqlite3.IntegrityError:
                    return jsonify({'error': 'A questionnaire template with this title already exists.'}), 409
        cursor = conn.execute(
            """INSERT INTO patient_questionnaires
               (pat_id, template_id, title, instructions, questions_json)
               VALUES (?, ?, ?, ?, ?)""",
            (pat_id, template_id, title, instructions or None, questions_json)
        )
        questionnaire_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    sent = False
    if payload.get('send'):
        if not patient.get('pat_email'):
            return jsonify({'error': 'Questionnaire assigned, but the patient has no email address.',
                            'questionnaire_id': questionnaire_id}), 400
        token, expires_at = _create_portal_invitation(
            pat_id, client_key, flask_login.current_user.get_id(), lifetime_minutes=10080
        )
        portal_url = url_for('portal_invitation_access', token=token, _external=True)
        patient_name = html.escape(' '.join(filter(None, [patient.get('pat_first_name'), patient.get('pat_last_name')])))
        safe_title = html.escape(title)
        subject = 'CareIL | Questionnaire available in your secure portal'
        body = (email_brand_header() + f'<p>Hello {patient_name},</p>'
                f'<p>A new questionnaire, <strong>{safe_title}</strong>, is waiting for you.</p>'
                f'<p><a href="{portal_url}">Open the secure portal and complete it</a></p>'
                f'<p>This one-time link is valid for 7 days and expires at {expires_at} UTC.</p>')
        try:
            _send_patient_email(client_key, patient['pat_email'], subject, body)
            sent = True
        except Exception:
            current_app.logger.exception('Failed to send questionnaire invitation')
            return jsonify({'error': 'Questionnaire assigned, but the email could not be sent.',
                            'questionnaire_id': questionnaire_id}), 502
    return jsonify({'ok': True, 'questionnaire_id': questionnaire_id, 'sent': sent})

@app.route("/patientnotes" , methods=['GET'])
@flask_login.login_required
def patientnotes_page():
    user = flask_login.current_user.get_dict()
    data = request.values
    if 'id' in request.values:
     id = request.values['id']
     #json.loads(data)
    if 'noteid' in request.values:
        noteid = request.values['noteid']
        med = Medicalnote()
        mednote = med.get(noteid)
    pat_id = data['id']
    appointments = database_read(
        """SELECT a.*, m.rec_id AS summary_rec_id
           FROM appointment a
           LEFT JOIN medrecords m ON m.app_id = a.app_id AND m.pat_id = a.pat_id
           WHERE a.pat_id = ? AND a.appointment_date < DATETIME('now','localtime')
           ORDER BY a.appointment_date DESC""",
        (pat_id,), client_key=client_key
    )
    notes = Medicalnotes()
    pat_mednotes = notes.getnotebypatient(pat_id)
    #TEST GET ONLY TEXT
    test= pat_mednotes[0]['body']
    data = json.loads(test)
    content_html = data.get('content', '')
    soup = BeautifulSoup(content_html, 'html.parser')
    text = soup.get_text()
    print("text",text) 
    # Get text and split by <br> tag
    text_list = [tag.get_text() for tag in soup.find_all(['div'])]
    if len(text_list)>0:
        text_with_separators = ','.join(text_list)
        pat_mednotes[0]["text"]=text_with_separators
    else:
        pat_mednotes[0]["text"]=text
    return render_template('patientnotes.html',Translate_data=Translate_data,user=user,pat_mednotes=pat_mednotes)

@app.route("/medicalnote" , methods=['GET'])
@flask_login.login_required
@admin_only
def medicalnote_page():
    user = flask_login.current_user.get_dict()
    client_key = session['client_key']
    pat_id = request.args.get('id', type=int)
    if pat_id is None:
        flash("Please select a patient before creating a medical note.", "warning")
        return redirect(url_for('patient_Page'))
    patients = database_read("SELECT * FROM patient WHERE pat_id = ?", (pat_id,), client_key=client_key)
    if not patients:
        abort(404)
    appointments = database_read(
        """SELECT a.*, m.rec_id AS summary_rec_id
           FROM appointment a
           LEFT JOIN medrecords m ON m.app_id = a.app_id AND m.pat_id = a.pat_id
           WHERE a.pat_id = ? AND a.appointment_date < DATETIME('now','localtime')
           ORDER BY a.appointment_date DESC""",
        (pat_id,), client_key=client_key
    )
    texteditor = ""
    pat_mednotes=""
    selected_app_id = request.args.get('app_id', type=int)
    if selected_app_id and not any(row['app_id'] == selected_app_id for row in appointments):
        abort(400)
    if request.args.get('noteid'):
        noteid = request.args.get('noteid', type=int)
        med = Medicalnote()
        mednote = med.get(noteid)
        # notes = Medicalnotes()
        # pat_mednotes = notes.getnotebypatient(pat_id)   
        pat_mednotes = database_read("SELECT * FROM medrecords WHERE pat_id = ? AND rec_id = ?", (pat_id, noteid), client_key=client_key)
        if not pat_mednotes:
            abort(404)
        texteditor = json.loads(pat_mednotes[0]['body'] or '{}')
        session['textineditor'] = texteditor.get('content', '')
        selected_app_id = pat_mednotes[0].get('app_id') or selected_app_id
    else:
        session['textineditor'] = " "
    return render_template('medicalnote.html',Translate_data=Translate_data,user=user,patient=patients[0],appointments=appointments,pat_mednotes=pat_mednotes,texteditor=texteditor,selected_app_id=selected_app_id)

@app.route("/medicalnote" , methods=['POST'])
@flask_login.login_required
def updatemedicalnote():
    user = flask_login.current_user.get_dict()
    data = dict(request.values)
    client_key = session['client_key']
    id = data['pat_id']
    contentbdy = data['content']
    app_id = data.get('app_id') or None
    if app_id:
        appointment = database_read(
            """SELECT app_id FROM appointment
               WHERE app_id = ? AND pat_id = ?
                 AND appointment_date < DATETIME('now','localtime')""",
            (app_id, id), client_key=client_key
        )
        if not appointment:
            abort(400)
    if 'noteid' in request.values:
        noteid = request.values['noteid']
        #update
        print("update:", noteid)
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        sql = "UPDATE medrecords SET pat_id = ?, app_id = ?, create_date = ?, body = ? WHERE rec_id = ? AND pat_id = ?"
        ok = database_write(sql, (id, app_id, now, contentbdy, noteid, id))
        if ok == 1:
            return jsonify({'ok': True, 'rec_id': int(noteid)})
        else:
            return "ERROR"
    else:
        #New   
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        if app_id:
            existing = database_read(
                "SELECT rec_id FROM medrecords WHERE pat_id = ? AND app_id = ? LIMIT 1",
                (id, app_id), client_key=client_key
            )
            if existing:
                return jsonify({'error': 'A summary already exists for this appointment.', 'rec_id': existing[0]['rec_id']}), 409
        sql = "INSERT INTO medrecords (pat_id, app_id, create_date, body) VALUES (?, ?, ?, ?)"
        ok = database_write(sql, (id, app_id, now, contentbdy))
        if ok == 1:
            return jsonify({'ok': True})
        else:
            return "ERROR"

@app.route('/templates', methods=['GET'])
@flask_login.login_required
def get_templates_options():
    client_key = session['client_key']
    template = database_read(f"select rec_id,appointment_type from recordstamplates;",client_key=client_key)
    print("template",template)
    return jsonify({'templates': template})

@app.route('/Addappointment_type', methods=['POST'])
@flask_login.login_required
def create_type():
    data = request.json
    client_key = session['client_key']
    if not data.get('name'):
        return jsonify({"error": "Name is required"}), 400
    new_type = data['name']    
    try:
        sql = "INSERT INTO recordstamplates (appointment_type) VALUES (?)"
        ok = database_write(sql, (new_type,))
        if ok==1:
            return jsonify({"message": "appointment type created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "appointment type created"}), 201

# Load template by appointment type
@app.route('/api/templates/<appointment_type>', methods=['GET'])
@flask_login.login_required
def get_template(appointment_type):
    client_key = session['client_key']
    template = database_read(
        "SELECT template FROM recordstamplates WHERE appointment_type = ?",
        (appointment_type,),
        client_key=client_key
    )
    if template:
        return jsonify({'template_text': template[0].get('template') or ''})
    return jsonify({'error': 'Template not found'}), 404

# Save or update a template
@app.route('/api/templates', methods=['POST'])
@flask_login.login_required
def save_template():
    data = request.get_json(silent=True) or {}
    client_key = session['client_key']
    appointment_type = (data.get('appointment_type') or '').strip()
    template_text = data.get('template_text')
    if not appointment_type or template_text is None:
        return jsonify({'error': 'Missing required fields'}), 400

    existing = database_read(
        "SELECT rec_id FROM recordstamplates WHERE appointment_type = ?",
        (appointment_type,),
        client_key=client_key
    )
    if existing:
        database_write(
            "UPDATE recordstamplates SET template = ? WHERE appointment_type = ?",
            (template_text, appointment_type)
        )
    else:
        database_write(
            "INSERT INTO recordstamplates (appointment_type, template) VALUES (?, ?)",
            (appointment_type, template_text)
        )
    return jsonify({'message': 'Template saved successfully'})
    
@app.route("/message" , methods=['GET'])
@flask_login.login_required
def message_page():
    user = flask_login.current_user.get_dict()
    data = request.values
    client_key = session['client_key']
    pat_id = data['patid']
    app_id = 0
    if 'app_id' in request.values:
        app_id =  data['app_id']
    if 'mark' in request.values:
        #Can Close messages only from portal
        pat_sign = session.get('client_key_signature')
        recid = data['rec_id']
        sql = f"update messages SET status=1 where rec_id = '{recid}';"
        ok = database_write(sql,data)
        if ok == 1:
            return redirect(url_for('get_portal'))
        else:
            return "ERROR"
        
    if 'rec_id' in request.values:
        recid = request.values['rec_id']   
        pat_messages = database_read(f"select * from messages where pat_id= '{pat_id}' and rec_id = '{recid}';",client_key=client_key)
    else:
        pat_messages = database_read(f"select * from messages where pat_id= '{pat_id}' ;",client_key=client_key)
        return render_template('message.html',user=user,pat_messages=pat_messages,pat_id=pat_id)

@app.route("/message" , methods=['POST'])
@flask_login.login_required
def updatemessages():
    user = flask_login.current_user.get_dict()
    data = dict(request.values)
    id = data['pat_id']
    app_id = 0
    if 'app_id' in request.values:
        app_id =  data['app_id']
    msg = data['msg']
    if 'rec_id' in request.values:
        recid = request.values['rec_id']
        #update
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        sql = f"update messages SET pat_id= '{id}', create_date= '{now}' ,message = '{msg}',app_id='{app_id}' where rec_id = '{recid}';"
        ok = database_write(sql,data)
        if ok == 1:
            return render_template('medicalnote.html',user=user,data=data)
        else:
            return "ERROR"
    else:
        #New   
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        sql = f"INSERT into messages (pat_id,create_date,message,app_id,status) VALUES  ('{id}','{now}','{msg}','{app_id}','0');"
        ok = database_write(sql,data)
        if ok == 1:
            return render_template('message.html',user=user,data=data)
        else:
            return "ERROR"
#endregion

#region Clients Routes

# Function to generate the signature
def generate_signature(pat_id, client_key, expires):
    data = f"{pat_id}:{client_key}:{expires}"
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()

def generate_patient_portal_url(base_url, pat_id, client_key):
    expires = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).timestamp())
    signature = generate_signature(pat_id, client_key, expires)
    return f"{base_url}?pat_id={pat_id}&client_key={client_key}&expires={expires}&signature={signature}"

def _portal_token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def _create_portal_invitation(pat_id, client_key, created_by, lifetime_minutes=30):
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.datetime.now(datetime.timezone.utc) +
                  datetime.timedelta(minutes=lifetime_minutes)).strftime('%Y-%m-%d %H:%M:%S')
    manager = DatabaseManager(client_key)
    conn = manager.connect_to_db(client_key)
    try:
        conn.execute(
            "INSERT INTO portal_invitations (pat_id, token_hash, expires_at, created_by) VALUES (?, ?, ?, ?)",
            (pat_id, _portal_token_hash(token), expires_at, created_by)
        )
        conn.commit()
    finally:
        conn.close()
    return token, expires_at

def _send_patient_email(client_key, recipient, subject, body):
    """Send a branded patient email using Resend or the clinic SMTP fallback."""
    if resend_is_configured():
        return send_resend_email(
            recipient, subject, body,
            attachments=[careil_logo_attachment(os.path.dirname(__file__))]
        )
    settings = get_Mail_settings(client_key)
    sender = str(settings.get('MAIL_USERNAME') or '')
    if not sender:
        raise RuntimeError('Mail settings are not configured')
    message = MIMEMultipart('related')
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html', _charset='utf-8'))
    attach_email_logo(message)
    port = int(settings.get('MAIL_PORT') or 587)
    with smtplib.SMTP(settings['MAIL_SERVER'], port) as smtp:
        if str(settings.get('MAIL_USE_TLS', 'True')).lower() in ('1', 'true', 'yes'):
            smtp.starttls()
        smtp.login(sender, settings['MAIL_PASSWORD'])
        smtp.sendmail(sender, recipient, message.as_string().encode('utf-8'))

def _find_portal_invitation(token):
    """Find an opaque invitation without exposing the tenant key in its URL."""
    token_hash = _portal_token_hash(token)
    manager = DatabaseManager()
    if not os.path.isdir(manager.base_db_path):
        return None
    for filename in os.listdir(manager.base_db_path):
        if not filename.endswith('.db'):
            continue
        client_key = _database_client_key(filename) or filename[:-3]
        try:
            conn = manager.connect_to_db(client_key)
            invitation = conn.execute(
                "SELECT * FROM portal_invitations WHERE token_hash = ? LIMIT 1", (token_hash,)
            ).fetchone()
            conn.close()
        except (sqlite3.Error, OSError):
            continue
        if invitation:
            invitation['client_key'] = client_key
            return invitation
    return None

@app.route('/api/patients/<int:pat_id>/portal-invitations', methods=['POST'])
@flask_login.login_required
@admin_only
def create_portal_invitation(pat_id):
    client_key = session['client_key']
    patient_rows = database_read(
        "SELECT pat_id, pat_first_name, pat_last_name, pat_email FROM patient WHERE pat_id = ?",
        (pat_id,), client_key=client_key
    )
    if not patient_rows:
        return jsonify({'error': 'Patient not found'}), 404
    patient = patient_rows[0]
    action = (request.get_json(silent=True) or {}).get('action', 'copy')
    if action not in ('copy', 'send'):
        return jsonify({'error': 'Invalid action'}), 400
    settings = None
    if action == 'send':
        if not patient.get('pat_email'):
            return jsonify({'error': 'This patient does not have an email address'}), 400
        settings = get_Mail_settings(client_key)
        if not resend_is_configured() and not str(settings.get('MAIL_USERNAME') or ''):
            return jsonify({'error': 'Mail settings are not configured'}), 400
    token, expires_at = _create_portal_invitation(
        pat_id, client_key, flask_login.current_user.get_id()
    )
    portal_url = url_for('portal_invitation_access', token=token, _external=True)
    if action == 'send':
        sender = str(settings.get('MAIL_USERNAME') or '')
        name = ' '.join(filter(None, [patient.get('pat_first_name'), patient.get('pat_last_name')]))
        subject = 'CareIL | Your secure client portal link'
        body = (email_brand_header() + f'<p>Hello {name},</p><p>Use the secure link below to open your client portal. '
                f'The link expires in 30 minutes and can be used once.</p>'
                f'<p><a href="{portal_url}">Open client portal</a></p>')
        if resend_is_configured():
            try:
                send_resend_email(
                    patient['pat_email'],
                    subject,
                    body,
                    attachments=[careil_logo_attachment(os.path.dirname(__file__))],
                )
                return jsonify({'url': portal_url, 'expires_at': expires_at, 'sent': True})
            except Exception:
                current_app.logger.exception('Failed to send portal invitation through Resend')
                database_write(
                    "UPDATE portal_invitations SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
                    (_portal_token_hash(token),)
                )
                return jsonify({'error': 'The portal email could not be sent. Check the Resend settings.'}), 502
        message = MIMEMultipart('related')
        message['From'] = sender
        message['To'] = patient['pat_email']
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html', _charset='utf-8'))
        attach_email_logo(message)
        try:
            port = int(settings.get('MAIL_PORT') or 587)
            with smtplib.SMTP(settings['MAIL_SERVER'], port) as smtp:
                if str(settings.get('MAIL_USE_TLS', 'True')).lower() in ('1', 'true', 'yes'):
                    smtp.starttls()
                smtp.login(sender, settings['MAIL_PASSWORD'])
                smtp.sendmail(sender, patient['pat_email'], message.as_string().encode('utf-8'))
        except Exception:
            current_app.logger.exception('Failed to send portal invitation')
            database_write(
                "UPDATE portal_invitations SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
                (_portal_token_hash(token),)
            )
            return jsonify({'error': 'The portal email could not be sent. Check the mail settings.'}), 502
    return jsonify({'url': portal_url, 'expires_at': expires_at, 'sent': action == 'send'})

@app.route('/api/patients/<int:pat_id>/portal-invitations/revoke', methods=['POST'])
@flask_login.login_required
@admin_only
def revoke_portal_invitations(pat_id):
    updated = database_write(
        "UPDATE portal_invitations SET revoked_at = CURRENT_TIMESTAMP "
        "WHERE pat_id = ? AND used_at IS NULL AND revoked_at IS NULL",
        (pat_id,)
    )
    return jsonify({'revoked': updated})

@app.route('/portal/access')
def portal_invitation_access():
    token = request.args.get('token', '')
    invitation = _find_portal_invitation(token) if token else None
    if not invitation:
        return render_template('clientlogin.html', alert='This portal link is invalid.'), 403
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    if invitation.get('used_at') or invitation.get('revoked_at') or invitation['expires_at'] < now:
        return render_template('clientlogin.html', alert='This portal link has expired or has already been used.'), 403
    client_key = invitation['client_key']
    manager = DatabaseManager(client_key)
    conn = manager.connect_to_db(client_key)
    try:
        changed = conn.execute(
            "UPDATE portal_invitations SET used_at = CURRENT_TIMESTAMP "
            "WHERE invitation_id = ? AND used_at IS NULL AND revoked_at IS NULL AND expires_at >= ?",
            (invitation['invitation_id'], now)
        ).rowcount
        conn.commit()
    finally:
        conn.close()
    if changed != 1:
        return render_template('clientlogin.html', alert='This portal link is no longer available.'), 403
    session.clear()
    session['portal_authenticated'] = True
    session['portal_pat_id'] = invitation['pat_id']
    session['client_key'] = client_key
    return redirect(url_for('get_portal'))

# Function to validate the signature
def is_valid_signature(pat_id, client_key, expires, signature):
    try:
        if int(expires) < int(datetime.datetime.now(datetime.timezone.utc).timestamp()):
            return False
    except (TypeError, ValueError):
        return False
    expected_signature = generate_signature(pat_id, client_key, expires)
    return hmac.compare_digest(expected_signature, signature)   
     
@app.route("/clients/client_login", methods=['GET'])
def clientlogin_page():
    return render_template('/clientlogin.html',alert = "")      

@app.route("/clients/client_login", methods=['POST'])
def clientlogin_request():
    client_key = session["client_key"]
    form = dict(request.values)
    breakpoint()
    users = database_read(f"select * from patient where pat_email='{form['pat_mail']}' and pat_insurance_no='{form['pat_id']}';",client_key)
    print(users)
    print('users',users[0]['pat_id'])
    clientid= users[0]['pat_id']
    if len(users) >= 1: #user name exist, password not checked
        user = load_user(clientid)        
        flask_login.login_user(user)  
        return redirect(f"/portal?patid={clientid}") 
    else: #Invalid Email 
           return render_template('/clientlogin.html',alert = "Invalid Email/ID Number. please try again.")      
    
@app.route("/portal",methods=["GET"])
def get_portal():
    pat_id = session.get('portal_pat_id') if session.get('portal_authenticated') else None
    client_key = session.get('client_key') if pat_id else None
    expires = request.args.get("expires")
    signature = request.args.get("signature")
    appointment_dates= {}
    if not pat_id:
        pat_id = request.args.get("pat_id")
        client_key = request.args.get("client_key")
        if not pat_id or not client_key or not expires or not signature:
            return jsonify({"error": "Missing or expired portal access"}), 401
        if not is_valid_signature(pat_id, client_key, expires, signature):
            return jsonify({"error": "Invalid signature"}), 403
        session['portal_authenticated'] = True
        session['portal_pat_id'] = pat_id
    #user = flask_login.current_user.get_dict()
    session['client_key'] = client_key 
    if signature:
        session['client_key_signature'] = signature
    patientdata = database_read(f"select * from patient where pat_id= '{pat_id}';",None,client_key=client_key)
    patientmessages = database_read(f"select * from messages where status = 0 and pat_id= '{pat_id}';",None,client_key=client_key)
    lastappointment = database_read(f"SELECT *  FROM appointment where pat_id='{pat_id}' and appointment_date < DATETIME('now') order by appointment_date desc LIMIT 1;",None,client_key=client_key)
    nextappointment = database_read(f"SELECT *  FROM appointment where pat_id='{pat_id}' and appointment_date >= DATETIME('now') order by appointment_date  asc LIMIT 1;",None,client_key=client_key)
    if lastappointment:
        appointment_dates["lastappointment"] = lastappointment[0]["appointment_date"]
    if nextappointment:
        appointment_dates["nextappointment"] = nextappointment[0]["appointment_date"]
    apps = Appointments()
    appointments = apps.getappointmentsbypatient(pat_id)
    allappointments = apps.get()
    pendingappointments = database_read(
        "SELECT appointment_date FROM pendingappointment WHERE status=0",
        client_key=client_key,
    )
    portal_questionnaires = database_read(
        """SELECT questionnaire_id, title, instructions, questions_json, status,
                  assigned_at, completed_at
           FROM patient_questionnaires WHERE pat_id = ? ORDER BY assigned_at DESC""",
        (pat_id,), client_key=client_key
    )
    for questionnaire in portal_questionnaires:
        try:
            questionnaire['questions'] = json.loads(questionnaire.get('questions_json') or '[]')
        except (TypeError, ValueError):
            questionnaire['questions'] = []
    pending_count = len(patientmessages)
    session['patientdata'] = patientdata
    return render_template(
        'portal.html', patientdata=patientdata, patientmessages=patientmessages,
        allappointments=allappointments + pendingappointments, appointments=appointments,
        appointment_dates=appointment_dates, pending_count=pending_count,
        portal_questionnaires=portal_questionnaires, alert=""
    )

@app.route('/portal/questionnaires/<int:questionnaire_id>/submit', methods=['POST'])
def portal_submit_questionnaire(questionnaire_id):
    pat_id = session.get('portal_pat_id') if session.get('portal_authenticated') else None
    client_key = session.get('client_key')
    if not pat_id or not client_key:
        return jsonify({'error': 'Portal session expired'}), 401
    rows = database_read(
        """SELECT questionnaire_id, questions_json, status
           FROM patient_questionnaires WHERE questionnaire_id = ? AND pat_id = ?""",
        (questionnaire_id, pat_id), client_key=client_key
    )
    if not rows:
        abort(404)
    if rows[0]['status'] == 'completed':
        return jsonify({'error': 'This questionnaire was already submitted.'}), 409
    try:
        questions = json.loads(rows[0]['questions_json'] or '[]')
    except (TypeError, ValueError):
        questions = []
    respondent_name = str(request.form.get('respondent_name') or '').strip()
    if not respondent_name or request.form.get('declaration') != 'yes':
        return jsonify({'error': 'Name and confirmation are required.'}), 400
    answers = []
    for index, question in enumerate(questions):
        answer = str(request.form.get(f'answer_{index}') or '').strip()
        if not answer:
            return jsonify({'error': 'Please answer every question.'}), 400
        answers.append({'question': question, 'answer': answer})
    response_record = {
        'answers': answers,
        'respondent_name': respondent_name,
        'declaration_accepted': True,
        'submitted_user_agent': request.headers.get('User-Agent', '')[:500]
    }
    updated = database_write(
        """UPDATE patient_questionnaires
           SET answers_json = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
           WHERE questionnaire_id = ? AND pat_id = ? AND status = 'assigned'""",
        (json.dumps(response_record, ensure_ascii=False), questionnaire_id, pat_id)
    )
    if updated != 1:
        return jsonify({'error': 'Questionnaire could not be submitted.'}), 409
    return jsonify({'ok': True})

@app.route('/portal/messages/<int:message_id>/read', methods=['POST'])
def portal_mark_message_read(message_id):
    pat_id = session.get('portal_pat_id') if session.get('portal_authenticated') else None
    client_key = session.get('client_key')
    if not pat_id or not client_key:
        return jsonify({'error': 'Portal session expired'}), 401
    updated = database_write(
        "UPDATE messages SET status = 1 WHERE rec_id = ? AND pat_id = ? AND status = 0",
        (message_id, pat_id)
    )
    if updated != 1:
        return jsonify({'error': 'Message not found'}), 404
    return jsonify({'message': 'Marked as read'})

@app.route('/portal/logout')
def portal_logout():
    session.clear()
    return redirect('/')

@app.route('/get-message/<int:message_id>', methods=['GET'])
def get_message(message_id):
    pat_id = session.get('portal_pat_id') if session.get('portal_authenticated') else None
    client_key = session.get('client_key')
    if not pat_id or not client_key:
        return jsonify({'error': 'Portal session expired'}), 401
    mymessages = database_read(
        "SELECT create_date, message FROM messages WHERE rec_id = ? AND pat_id = ?",
        (message_id, pat_id), client_key=client_key
    )
    if mymessages:
        return jsonify(mymessages)
    else:
        return jsonify({"error": "Message not found"}), 404
    

@app.route("/checkdate",methods=["POST"])
#@flask_login.login_required
def chekappointmentdate():
    data=  dict(request.values)
    #handel...
    print(data)
    #user = flask_login.current_user.get_dict() 
    id = data['pat_id']
    if session.get('portal_authenticated'):
        id = str(session.get('portal_pat_id'))
    datetocheck = data['appointmentdate']    
    client_key = session.get('client_key')
    try:
        requested_at = datetime.datetime.strptime(datetocheck, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return "ERROR", 400

    availability = _availability_settings(client_key)
    allowed_days = {int(day) for day in availability['AVAILABILITY_DAYS'].split(',') if day != ''}
    # JavaScript uses Sunday=0; Python uses Monday=0.
    requested_day = (requested_at.weekday() + 1) % 7
    start_time = datetime.datetime.strptime(availability['AVAILABILITY_START'], '%H:%M').time()
    end_time = datetime.datetime.strptime(availability['AVAILABILITY_END'], '%H:%M').time()
    if requested_day not in allowed_days or not (start_time <= requested_at.time() < end_time):
        return "ERROR"

    appoinmentindate = database_read(
        """SELECT app_id FROM appointment WHERE appointment_date = ?
           UNION ALL
           SELECT app_id FROM pendingappointment
           WHERE appointment_date = ? AND status = 0
           LIMIT 1""",
        (datetocheck, datetocheck),
        client_key=client_key
    )
    if len(appoinmentindate) >= 1:
       return "ERROR"             
    else:
        return "OK" 

@app.route("/postmsg",methods=["GET","POST"])
def postmsg():
    data=  dict(request.values)
    app_id = data['app_id']
    appointment = RequestAppointment()
    patapp = appointment.get(app_id)
    if patapp:
        pat_id=patapp[0]['pat_id']
        app_date = patapp[0]['appointment_date']
        msg="בקשתך לטיפול בתאריך : {app_date}  לא אושרה יש לבקש תאריך נוסף, יום נפלא".format(app_date=app_date)
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        sql = f"INSERT into messages (pat_id,create_date,message,app_id) VALUES  ('{pat_id}','{now}','{msg}','{app_id}');"
        ok = database_write(sql,data)
        print('msg sent!',ok)
        return redirect(f"/appointment")  
    else:
        return "No Patient appointment"    
#endregion

def send_verification_code(email, verification_code):
    
    sender_email = resend_sender_address() if resend_is_configured() else app.config['MAIL_USERNAME']
    print(sender_email)
    """ Send the verification code to the user's email """
    msg = Message('CareIL | Your Verification Code', 
                  sender=sender_email, 
                  recipients=[email])
    msg.body = f'Your verification code is: {verification_code}. it will be valid for the next 5 Minutes.'
    msg.html = (email_brand_header() + '<p>Your verification code is:</p>'
                f'<p style="font-size:24px;font-weight:700;letter-spacing:4px;">{verification_code}</p>'
                '<p>It will be valid for the next 5 minutes.</p>')
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'therapy-hands-logo-email.png')
    with open(logo_path, 'rb') as logo_file:
        msg.attach(
            'careil.png', 'image/png', logo_file.read(),
            disposition='inline', headers=[['Content-ID', '<careil-logo>']]
        )
  
    
    try:
        if resend_is_configured():
            send_resend_email(
                email,
                'CareIL | Your Verification Code',
                msg.html,
                text=msg.body,
                attachments=[careil_logo_attachment(os.path.dirname(__file__))],
            )
        else:
            mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    app.run(
        host=Globalsetting.get("host", "127.0.0.1"),
        port=int(Globalsetting.get("port", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    )
