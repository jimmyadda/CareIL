# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
import json
from functools import wraps
import flask_login




BASEICS = u'''
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Karin//Therapy Events v1.0//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VTIMEZONE
TZID:Asia/Jerusalem
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0300
TZNAME:CST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTAMP:%(created)s
DTSTART;TZID=Asia/Jerusalem:%(start)s
DTEND;TZID=Asia/Jerusalem:%(end)s
STATUS:CONFIRMED
SUMMARY:%(title)s
DESCRIPTION:%(description)s
ORGANIZER;CN=%(admin)s Reminder:MAILTO:%(admin_mail)s
CLASS:PUBLIC
CREATED:%(created)s
LOCATION:%(location)s
LAST-MODIFIED:%(created)s
UID:%(admin_mail)s
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
        date = datetime.utcnow() + timedelta(hours=8)

    if with_z:
        return date.strftime('%Y%m%dT%H%M%SZ')
    return date.strftime('%Y%m%dT%H%M%SZ')[:-1]


def render_ics(title, description, location, start, end, created,admin,admin_mail):
    data = {
            'title': title,
            'description': description,
            'location': location,
            'start': dateisoformat(start, False),
            'end': dateisoformat(end, False),
            'created': dateisoformat(created),
            'admin': admin,
            'admin_mail': admin_mail
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
