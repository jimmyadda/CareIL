import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_dashboard_contains_google_reminder_form():
    template = (ROOT / 'templates' / 'index.html').read_text(encoding='utf-8')
    assert 'id="googleReminderForm"' in template
    assert "fetch('/google-calendar/reminders'" in template
    assert 'type="datetime-local"' in template
    assert "$('#reminderModal').appendTo(document.body)" in template


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


def test_appointment_calendar_title_includes_client_name_by_default():
    calendar = (ROOT / 'package' / 'google_calendar.py').read_text(encoding='utf-8')
    assert "'Therapy appointment – ' + client_name" in calendar
    assert 'GOOGLE_CALENDAR_INCLUDE_CLIENT_NAME' not in calendar


def test_client_portal_has_visible_and_resilient_appointment_date_picker():
    template = (ROOT / 'templates' / 'portal.html').read_text(encoding='utf-8')
    assert 'id="openAppointmentDate"' in template
    assert 'placeholder="Choose date and time"' in template
    assert 'showAppointmentPicker();' in template
    assert "appointmentDate.attr({type:'datetime-local'" in template


def test_all_booking_screens_share_supported_availability_picker():
    picker = (ROOT / 'static' / 'js' / 'disabledatetime.js').read_text(encoding='utf-8')
    patient_booking = (ROOT / 'static' / 'js' / 'appointmentpatientform.js').read_text(encoding='utf-8')
    appointment_booking = (ROOT / 'static' / 'js' / 'appointment-page-fix.js').read_text(encoding='utf-8')
    assert 'onRenderHour' not in picker
    assert "return [];" in picker
    assert 'availabilityPickerOptions(disabled)' in patient_booking
    assert 'attachBookedSlotGuard($picker, disabled)' in patient_booking
    assert "$.getJSON('/api/appointment-slots')" in patient_booking
    assert "$.getJSON('/api/appointment-slots')" in appointment_booking


def test_picker_highlights_reserved_days_and_uses_selected_day_for_hours():
    picker = (ROOT / 'static' / 'js' / 'disabledatetime.js').read_text(encoding='utf-8')
    styles = (ROOT / 'static' / 'css' / 'booking-picker.css').read_text(encoding='utf-8')
    assert 'picker.viewDate || picker.date' in picker
    assert "toggleClass('has-booking', reserved)" in picker
    assert "picker.hoursDisabled = hours" in picker
    assert "toggleClass('booked-hour', booked)" in picker
    assert "bookedHoursForDate" in picker
    assert "applyDisabledHours(clickedDate)" in picker
    assert "event.stopImmediatePropagation()" in picker
    assert "disabledSlots.has(dateKey(selectedDate)" in picker
    assert 'refreshBookingMarks' in picker
    assert 'td.day.has-booking' in styles
    assert 'span.hour.disabled.booked-hour' in styles


def test_booking_screens_have_explicit_calendar_buttons():
    appointment = (ROOT / 'templates' / 'appointment.html').read_text(encoding='utf-8')
    patient = (ROOT / 'templates' / 'patientform.html').read_text(encoding='utf-8')
    portal = (ROOT / 'templates' / 'portal.html').read_text(encoding='utf-8')
    assert 'open-appointment-picker' in appointment
    assert 'open-appointment-picker' in patient
    assert 'id="openAppointmentDate"' in portal
    assert 'bindAppointmentPickerButtons' in (ROOT / 'static' / 'js' / 'disabledatetime.js').read_text(encoding='utf-8')


def test_booking_screens_use_canonical_slots_and_visible_modal_errors():
    server = (ROOT / 'server.py').read_text(encoding='utf-8')
    picker = (ROOT / 'static' / 'js' / 'disabledatetime.js').read_text(encoding='utf-8')
    appointment_js = (ROOT / 'static' / 'js' / 'appointment-page-fix.js').read_text(encoding='utf-8')
    patient_js = (ROOT / 'static' / 'js' / 'appointmentpatientform.js').read_text(encoding='utf-8')
    templates = [
        (ROOT / 'templates' / name).read_text(encoding='utf-8')
        for name in ('appointment.html', 'patientform.html', 'portal.html')
    ]
    assert "@app.route('/api/appointment-slots', methods=['GET'])" in server
    assert "fetch('/api/appointment-slots'" in picker
    assert "$.getJSON('/api/appointment-slots')" in appointment_js
    assert "$.getJSON('/api/appointment-slots')" in patient_js
    assert 'showAppointmentModalError' in appointment_js
    assert 'showAppointmentModalError' in patient_js
    for template in templates:
        assert 'appointment-inline-error' in template
        assert 'readonly' in template
