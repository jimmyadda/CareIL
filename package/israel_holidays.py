"""Israel public-holiday dates used by the calendar and booking validation."""

import datetime
from functools import lru_cache

import holidays


@lru_cache(maxsize=64)
def _year_holidays(year, language):
    return holidays.country_holidays('IL', years=[int(year)], language=language)


def holiday_name(value, language='en_US'):
    day = value.date() if isinstance(value, datetime.datetime) else value
    if not isinstance(day, datetime.date):
        try:
            day = datetime.date.fromisoformat(str(value)[:10])
        except (TypeError, ValueError):
            return None
    return _year_holidays(day.year, language).get(day)


def is_holiday(value):
    return holiday_name(value) is not None


def holiday_records(start_year, end_year):
    records = []
    for year in range(int(start_year), int(end_year) + 1):
        hebrew = _year_holidays(year, 'he')
        english = _year_holidays(year, 'en_US')
        for day in sorted(set(hebrew) | set(english)):
            records.append({
                'date': day.isoformat(),
                'name_he': hebrew.get(day) or english.get(day),
                'name_en': english.get(day) or hebrew.get(day),
            })
    return records


def holiday_dates(start_year, end_year):
    return [record['date'] for record in holiday_records(start_year, end_year)]
