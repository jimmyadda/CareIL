import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import hashlib
import hmac
import json
import sqlite3
from flask import redirect, request, session
import flask_login
from flask_mail import Mail, Message
import os
import smtplib
import logging

from package.database import DatabaseManager
from package.email_service import (
    careil_logo_attachment,
    resend_is_configured,
    send_resend_email,
)
SECRET_KEY = os.environ.get('THERAPY_SECRET_KEY', 'change-this-development-key')

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



def get_Mail_settings(Pclient_key):
    client_key = Pclient_key
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()    
    return {row[0]: row[1] for row in rows}

def update_Mail_setting(key, value):
    client_key = session['client_key']
    db_manager = DatabaseManager(client_key)
    conn = db_manager.connect_to_db(client_key)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()

# Function to generate the signature
def generate_signature(pat_id, client_key, expires):
    data = f"{pat_id}:{client_key}:{expires}"
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()
    
def generate_patient_portal_url(base_url, pat_id, client_key):
    expires = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).timestamp())
    signature = generate_signature(pat_id, client_key, expires)
    return f"{base_url}?pat_id={pat_id}&client_key={client_key}&expires={expires}&signature={signature}"

###globals
path = os.getcwd()
database_filename = "Tasker.db"
#Mail Settings
#with open('config.json') as config_file:


#DB functions
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
    conn.commit()
    db.close()
    conn.close()

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
    conn.close()
    return rows

def send_mail(notification='',PclineKey=None):
    form = session['formData']
    user = flask_login.current_user.get_dict() 
    
    mail_settings = get_Mail_settings(PclineKey)

    task_url = request.host_url + f"/main?folderid={form['folderid']}&id={form['id']}"
    assignTo_mail = database_read(f"select email from accounts WHERE name ='{form['assignto']}' order by name;")
    Project_data= database_read(f"select name from folders WHERE id ='{form['folderid']}' order by name;")
    #Create Main
    projname= Project_data[0]['name']
    subject="CareIL | Task Number: [#" +form['id']+" ] - " +form['title']
    sender_email= str(mail_settings['MAIL_USERNAME'])
    receiver_email = str(assignTo_mail[0]['email'])
    #Build Msg
    # Email content
    email_body = '''
                <b>Subject:</b> {Subject}<br>
                <b>Reported By:</b> {Reported By}<br>
                <b>Assigned To:</b> {Assigned To}<br>
                <b>Project:</b> {Project}<br>
                <b>TaskID:</b> {TaskID}<br>
                <b>Category:</b> {Category}<br>
                <b>Priority:</b> {Priority}<br>
                <b>Status:</b> {Status}<br>
                <b>Date Created:</b> {Date Created}<br>
                <br>
                <b>Description:</b><br>
                {Description}
                '''
        # Email data
    email_data = {
        'Subject': subject,    
        'Reported By': user['userid'],
        'Assigned To': form['assignto'],
        'Project': projname,
        'TaskID': form['id'],
        'Category': form['category'],
        'Priority': form['priority'],
        'Status': form['status'],
        'Date Created': form['created'],
        'Description': form['desc']
        }
    email_content = email_brand_header() + email_body.format(**email_data)
    email_content += f"<br><p><a href={task_url}>Go to Task</a></p>"
    if resend_is_configured():
        send_resend_email(
            receiver_email,
            subject,
            email_content,
            attachments=[careil_logo_attachment(os.path.dirname(__file__))],
        )
        print('Email sent through Resend!')
        return redirect(f"/main?folderid={form['folderid']}&id={form['id']}")
    # Create MIME message
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = receiver_email    
    message['Subject'] = str(subject)
    message.attach(MIMEText(email_content, 'html',_charset='utf-8'))
    attach_email_logo(message)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(mail_settings['MAIL_SERVER'], 587) as server:
        server.starttls()
        server.login(mail_settings['MAIL_USERNAME'], mail_settings['MAIL_PASSWORD'])
        server.sendmail(sender_email, receiver_email, message.as_string().encode("UTF-8"))
        server.close()
    print('Email sent!')
    #Log
    return redirect(f"/main?folderid={form['folderid']}&id={form['id']}")

def send_notification(data):
    form = data

    patient_data = data['patien_data'][0]
    clinic_data = data['clinic_data'][0]
    lang = data['lang']

    patientname = patient_data['pat_first_name']
    clinic_name = clinic_data['name']
    clinic_add = clinic_data['address']
    clinic_phone = clinic_data['phone']
    clinic_mail= clinic_data['email']
    clinic_website = clinic_data['website']
    

   #heb Email..
    Heb_Notification='''
    שלום {patientname} ,

ברוכים הבאים ל[שם המרפאה שלכם]! אנו שמחים וגאים לצרף אתכם לקהילת המטופלים שלנו. הצוות שלנו מחויב להעניק לכם את הטיפול האיכותי ביותר בסביבה מקצועית, חמה וידידותית.

הנה מה שתוכלו לצפות מאיתנו:

    טיפול מותאם אישית: אנו נעבוד יחד איתכם כדי לענות על הצרכים הבריאותיים הייחודיים שלכם.
    צוות מקצועי: צוות המטפלים המיומן שלנו כאן כדי ללוות אתכם בכל שלב בדרך.
    נוחות מירבית: קביעת תורים גמישה, משאבים מקוונים ותקשורת קלה ונוחה איתנו.

השלבים הבאים עבורכם:

    אם עדיין לא קבעתם את התור הראשון שלכם, נשמח שתתקשרו אלינו למספר {clinic_phone} או תבקרו באתר שלנו בכתובת {clinic_website}.
    אם יש לכם שאלות או שאתם זקוקים לעזרה, אל תהססו לפנות אלינו.

אנו כאן כדי לעזור לכם להגיע ליעדים הבריאותיים שלכם. בין אם מדובר בבדיקה שגרתית, בטיפול מסוים או במעקב מתמשך, אנו מחויבים להעניק לכם חוויה נוחה וחיובית.

תודה על האמון שנתתם בנו. אנחנו מצפים לראותכם בקרוב!

    {clinic_name}
    {clinic_add}
    {clinic_phone} | {clinic_mail} | {clinic_website}'''.format(patientname=patientname,
    clinic_name=clinic_name,clinic_website=clinic_website,clinic_add=clinic_add,
    clinic_phone=clinic_phone,clinic_mail=clinic_mail) 
    
    
    Eng_notification = '''
    Dear {patientname},

    Welcome to "{clinic_name}"! We are thrilled to have you join our community of patients.\n 
    Our team is dedicated to providing you with the highest quality of care in a warm, professional,\n 
    and friendly environment.\n

    Here is what you can expect from us:\n
    Personalized Care: We will work with you to meet your unique health needs.\n
    Experienced Team: Our skilled healthcare providers are here to support you every step of the way.
    Convenience: Flexible appointment scheduling, online resources, and an easy way to stay in touch with us.\n\n

    Your Next Steps:\n

     * If you have nםt scheduled your first appointment yet, 
        please call us at {clinic_phone} or visit our website at {clinic_website}.\n
     
     * Feel free to reach out if you have any questions or need assistance.\n

    \n We are here to help you achieve your health goals. Whether you are visiting for a check-up, 
    a specific treatment, or ongoing care, we are committed to making your experience comfortable and positive.

    \nThank you for trusting us with your care. We look forward to seeing you soon!

    \nWarm regards,\n\n

    {clinic_name}
    {clinic_add}
    {clinic_phone} | {clinic_mail} | {clinic_website}'''.format(patientname=patientname,
    clinic_name=clinic_name,clinic_website=clinic_website,clinic_add=clinic_add,
    clinic_phone=clinic_phone,clinic_mail=clinic_mail)
    subject = ""
    Eng_subject="CareIL | Welcome to {clinic_name}".format(clinic_name=clinic_name)
    Heb_subject ="CareIL | ברוכים הבאים ל{clinic_name}".format(clinic_name=clinic_name)
    if lang=="HE":
        notification = Heb_Notification
        subject=Heb_subject
    else:
        notification = Eng_notification
        subject = Eng_subject

    client_key = session['client_key']
    mail_settings = get_Mail_settings(client_key)


     
    assignTo_mail = form['pat_email']
    #url
    base_url = request.host_url + "/portal"
    pat_id = form['pat_id']
    client_key = form['client_key']
    patient_url = generate_patient_portal_url(base_url, pat_id, client_key)


    sender_email= str(mail_settings['MAIL_USERNAME'])
    receiver_email = str(assignTo_mail) 
    email_body = '''
                <b>Subject:</b> {Subject}<br>                              
                <br>
                <b>Note:</b><br>
                {note}
                ''' 
    # Email data
    email_data = {
            'Subject': subject,    
            'note': notification
            } 
    email_content = email_brand_header() + email_body.format(**email_data)
    email_content += f"<br><p><a href={patient_url}>Go to patient page</a></p>"
    if resend_is_configured():
        send_resend_email(
            receiver_email,
            subject,
            email_content,
            attachments=[careil_logo_attachment(os.path.dirname(__file__))],
        )
        print('Email sent through Resend!')
        return "ok"
    # Create MIME message
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = receiver_email    
    message['Subject'] = str(subject)
    message.attach(MIMEText(email_content, 'html',_charset='utf-8'))
    attach_email_logo(message)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(mail_settings['MAIL_SERVER'], 587) as server:
        server.starttls()
        server.login(mail_settings['MAIL_USERNAME'], mail_settings['MAIL_PASSWORD'])
        server.sendmail(sender_email, receiver_email, message.as_string().encode("UTF-8"))
        server.close()
    print('Email sent!')
    return "ok"
