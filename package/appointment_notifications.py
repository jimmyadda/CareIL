"""Appointment decision emails sent by the clinic workflow."""

import datetime
import html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

from package.database import DatabaseManager
from package.email_service import (
    careil_logo_attachment,
    encoded_attachment,
    resend_is_configured,
    resend_sender_address,
    send_resend_email,
)
from package.Myutils import render_ics


def _brand_header():
    return ("<div style='padding:14px 18px;border-radius:14px;background:"
            "linear-gradient(135deg,#a3b18a 0%,#588157 100%);'>"
            "<img src='cid:careil-logo' alt='CareIL' style='width:58px;vertical-align:middle'>"
            " <strong style='font:700 20px Arial;color:#102a1c'>CareIL</strong></div>")


def _appointment_data(client_key, pat_id):
    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        patient = conn.execute(
            "SELECT pat_first_name, pat_last_name, pat_email FROM patient WHERE pat_id=?",
            (pat_id,),
        ).fetchone()
        therapist = conn.execute(
            """SELECT doc_first_name, doc_last_name, doc_email, doc_ph_no, doc_address
               FROM doctor ORDER BY doc_id LIMIT 1"""
        ).fetchone()
        duration_row = conn.execute(
            "SELECT value FROM settings WHERE key='APPOINTMENT_DURATION'"
        ).fetchone()
        return patient, therapist, int(duration_row['value']) if duration_row else 60
    finally:
        conn.close()


def _deliver(client_key, recipient, subject, body, attachments=None):
    if resend_is_configured():
        return send_resend_email(
            recipient, subject, body,
            attachments=[careil_logo_attachment(os.path.dirname(os.path.dirname(__file__)))]
            + list(attachments or []),
        )

    conn = DatabaseManager(client_key).connect_to_db(client_key)
    try:
        settings = {row['key']: row['value'] for row in conn.execute(
            "SELECT key, value FROM settings"
        ).fetchall()}
    finally:
        conn.close()
    message = MIMEMultipart('alternative')
    message['From'] = settings.get('MAIL_USERNAME', '')
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html', 'utf-8'))
    with smtplib.SMTP(settings.get('MAIL_SERVER', 'smtp.gmail.com'), int(settings.get('MAIL_PORT', 587))) as smtp:
        smtp.starttls()
        smtp.login(settings.get('MAIL_USERNAME', ''), settings.get('MAIL_PASSWORD', ''))
        smtp.sendmail(message['From'], recipient, message.as_string())


def send_appointment_decision(client_key, pat_id, appointment_date, accepted, language='EN', app_id=None):
    patient, therapist, duration = _appointment_data(client_key, pat_id)
    if not patient or not patient.get('pat_email'):
        return None
    starts = datetime.datetime.strptime(appointment_date, '%Y-%m-%d %H:%M:%S')
    ends = starts + datetime.timedelta(minutes=duration)
    is_hebrew = str(language).upper() == 'HE'
    patient_name = ' '.join(filter(None, [patient.get('pat_first_name'), patient.get('pat_last_name')]))
    therapist_name = ' '.join(filter(None, [therapist.get('doc_first_name'), therapist.get('doc_last_name')])) if therapist else ''
    date_text = starts.strftime('%d/%m/%Y')
    time_text = starts.strftime('%H:%M')
    safe_address = html.escape((therapist or {}).get('doc_address') or '')
    safe_therapist = html.escape(therapist_name)

    if accepted:
        title = 'פגישה טיפולית' if is_hebrew else 'Therapy appointment'
        google_params = urlencode({
            'action': 'TEMPLATE',
            'text': title,
            'dates': starts.strftime('%Y%m%dT%H%M%S') + '/' + ends.strftime('%Y%m%dT%H%M%S'),
            'ctz': 'Asia/Jerusalem',
            'location': (therapist or {}).get('doc_address') or '',
            'details': (f'פגישה עם {therapist_name}' if is_hebrew else f'Appointment with {therapist_name}'),
        })
        calendar_url = 'https://calendar.google.com/calendar/render?' + google_params
        if is_hebrew:
            subject = f'CareIL | הפגישה אושרה ל־{date_text} בשעה {time_text}'
            content = (f"<p>שלום {html.escape(patient_name)},</p><p>בקשת הפגישה אושרה.</p>"
                       f"<p><strong>תאריך:</strong> {date_text}<br><strong>שעה:</strong> {time_text}<br>"
                       f"<strong>משך:</strong> {duration} דקות<br><strong>מטפל/ת:</strong> {safe_therapist}<br>"
                       f"<strong>כתובת:</strong> {safe_address}</p><p><a href='{calendar_url}' "
                       "style='display:inline-block;padding:12px 18px;border-radius:10px;background:#588157;color:white;text-decoration:none'>"
                       "הוספה ליומן Google</a></p><p>מצורף גם קובץ יומן המתאים ל־Apple Calendar, Outlook ויומנים אחרים.</p>")
        else:
            subject = f'CareIL | Appointment confirmed for {date_text} at {time_text}'
            content = (f"<p>Hello {html.escape(patient_name)},</p><p>Your appointment request was accepted.</p>"
                       f"<p><strong>Date:</strong> {date_text}<br><strong>Time:</strong> {time_text}<br>"
                       f"<strong>Duration:</strong> {duration} minutes<br><strong>Therapist:</strong> {safe_therapist}<br>"
                       f"<strong>Address:</strong> {safe_address}</p><p><a href='{calendar_url}' "
                       "style='display:inline-block;padding:12px 18px;border-radius:10px;background:#588157;color:white;text-decoration:none'>"
                       "Add to Google Calendar</a></p><p>A calendar file for Apple Calendar, Outlook and other calendars is also attached.</p>")
        ics = render_ics(
            title=title, description=title, location=(therapist or {}).get('doc_address') or '',
            start=starts, end=ends, created=None, admin=therapist_name or 'CareIL',
            admin_mail=(therapist or {}).get('doc_email') or resend_sender_address(),
            uid=f'careil-appointment-{app_id or pat_id}-{starts.strftime("%Y%m%d%H%M%S")}@careil.net',
        )
        return _deliver(
            client_key, patient['pat_email'], subject, _brand_header() + content,
            [encoded_attachment(ics, 'CareIL-appointment.ics', 'text/calendar')],
        )

    if is_hebrew:
        subject = f'CareIL | בקשת הפגישה ל־{date_text} בשעה {time_text} לא אושרה'
        content = (f"<p>שלום {html.escape(patient_name)},</p><p>בקשת הפגישה לתאריך "
                   f"<strong>{date_text}</strong> בשעה <strong>{time_text}</strong> לא אושרה.</p>"
                   "<p>ניתן להיכנס לפורטל ולבקש מועד אחר.</p>")
    else:
        subject = f'CareIL | Appointment request declined for {date_text} at {time_text}'
        content = (f"<p>Hello {html.escape(patient_name)},</p><p>Your appointment request for "
                   f"<strong>{date_text}</strong> at <strong>{time_text}</strong> was declined.</p>"
                   "<p>You can return to the portal and request another time.</p>")
    return _deliver(client_key, patient['pat_email'], subject, _brand_header() + content)
