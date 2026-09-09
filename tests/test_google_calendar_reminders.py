import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_dashboard_contains_google_reminder_form():
    template = (ROOT / 'templates' / 'index.html').read_text(encoding='utf-8')
    assert 'id="googleReminderForm"' in template
    assert "fetch('/google-calendar/reminders'" in template
    assert 'type="datetime-local"' in template


def test_reminder_api_and_private_calendar_event_exist():
    server = (ROOT / 'server.py').read_text(encoding='utf-8')
    calendar = (ROOT / 'package' / 'google_calendar.py').read_text(encoding='utf-8')
    assert "@app.route('/google-calendar/reminders', methods=['POST'])" in server
    assert "'visibility': 'private'" in calendar
    assert "'method': 'popup'" in calendar
    assert "'careil_type': 'reminder'" in calendar


def test_reminder_translations_exist():
    translations = json.loads((ROOT / 'Translate.json').read_text(encoding='utf-8'))
    for language in ('EN', 'HE'):
        for key in ('dashboardReminderAction', 'reminderTitle', 'reminderName', 'reminderSave'):
            assert translations[language][key]
