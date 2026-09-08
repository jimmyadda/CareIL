import pathlib
import datetime
from unittest.mock import patch

from package.jewish_holidays import holiday_name


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_calendar_loads_jewish_holiday_integration():
    template = (ROOT / 'templates' / 'calendar.html').read_text(encoding='utf-8')
    assert '/static/jewish-holidays.js?v=1' in template
    assert 'CareILJewishHolidays.add(calendar, isHebrew)' in template
    assert 'Hebcal.com' in template


def test_jewish_holiday_source_uses_israel_schedule_and_expected_categories():
    source = (ROOT / 'static' / 'jewish-holidays.js').read_text(encoding='utf-8')
    for setting in ("i: 'on'", "maj: 'on'", "min: 'on'", "mod: 'on'", "mf: 'on'"):
        assert setting in source
    assert "item.category === 'holiday'" in source
    assert 'calendar.addHolidays(holidays, false, true)' in source


def test_holiday_lookup_matches_the_requested_date():
    with patch('package.jewish_holidays.holidays_for_year', return_value={'2026-09-14': 'ראש השנה'}):
        assert holiday_name(datetime.datetime(2026, 9, 14, 10, 0)) == 'ראש השנה'
        assert holiday_name('2026-09-15 10:00:00') is None


def test_portal_disables_holidays_and_server_validates_them():
    picker = (ROOT / 'static' / 'js' / 'disabledatetime.js').read_text(encoding='utf-8')
    portal = (ROOT / 'templates' / 'portal.html').read_text(encoding='utf-8')
    server = (ROOT / 'server.py').read_text(encoding='utf-8')
    assert "datesDisabled: holidayDates" in picker
    assert "/api/jewish-holidays" in picker
    assert "Jewish holidays" in portal
    assert "if holiday_name(requested_at)" in server
