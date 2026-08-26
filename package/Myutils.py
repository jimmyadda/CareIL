# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import json
from functools import wraps
import flask_login
from zoneinfo import ZoneInfo




BASEICS = u'''
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CareIL//Appointment Calendar v1.0//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
DTSTAMP:%(created)s
DTSTART:%(start)s
DTEND:%(end)s
STATUS:CONFIRMED
SUMMARY:%(title)s
DESCRIPTION:%(description)s
ORGANIZER;CN=%(admin)s:MAILTO:%(admin_mail)s
CLASS:PUBLIC
CREATED:%(created)s
LOCATION:%(location)s
LAST-MODIFIED:%(created)s
UID:%(uid)s
END:VEVENT
END:VCALENDAR
'''
# created, start, end, title, description, location, admin_mail
# date format: 20150108T073253Z
# DTSTART: 20150113T190000
# DTEND: 20150113T220000
# GEO:25.02;121.44
#Settings
with open('config.json') as config_file:
    config_data = json.load(config_file)
Globalsetting = config_data['Global'] 
  
mail_settings = config_data['mail_settings']
sender_email= str(mail_settings['MAIL_USERNAME'])

def dateisoformat(date=None, with_z=True):
    if not date:
        date = datetime.now(timezone.utc)

    if with_z:
        if date.tzinfo is None:
            date = date.replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
        date = date.astimezone(timezone.utc)
        return date.strftime('%Y%m%dT%H%M%SZ')
    return date.strftime('%Y%m%dT%H%M%SZ')[:-1]


def _ics_text(value):
    return str(value or '').replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')


def render_ics(title, description, location, start, end, created,admin,admin_mail,uid=None):
    data = {
            'title': _ics_text(title),
            'description': _ics_text(description),
            'location': _ics_text(location),
            'start': dateisoformat(start),
            'end': dateisoformat(end),
            'created': dateisoformat(created),
            'admin': _ics_text(admin),
            'admin_mail': admin_mail,
            'uid': uid or ('careil-%s-%s' % (dateisoformat(start, False), admin_mail))
            }
    return BASEICS % data



if __name__ == '__main__':
    print(render_ics(
            title=u'testcal',
            description=u'test calendar',
            location=u'Haifa,Israel',
            start=datetime(2024, 3, 3, 10,30),
            end=datetime(2024, 3, 3, 11, 00),
            created=None,
            admin= 'Karin Adda',
            admin_mail= sender_email
            ))
