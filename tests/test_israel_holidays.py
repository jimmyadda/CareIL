import datetime
import unittest

from package.israel_holidays import holiday_dates, holiday_name, holiday_records, is_holiday


class IsraelHolidayTest(unittest.TestCase):
    def test_september_2026_holidays_are_available_in_both_languages(self):
        records = {item['date']: item for item in holiday_records(2026, 2026)}
        self.assertEqual(records['2026-09-12']['name_he'], 'ראש השנה')
        self.assertEqual(records['2026-09-21']['name_en'], 'Yom Kippur')
        self.assertIn('2026-09-26', holiday_dates(2026, 2026))

    def test_holiday_check_accepts_date_datetime_and_iso_text(self):
        self.assertTrue(is_holiday(datetime.date(2026, 9, 21)))
        self.assertTrue(is_holiday(datetime.datetime(2026, 9, 21, 10, 0)))
        self.assertEqual(holiday_name('2026-09-21', 'he'), 'יום כיפור')
        self.assertFalse(is_holiday('2026-09-22'))


if __name__ == '__main__':
    unittest.main()
