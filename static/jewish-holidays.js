(function (window) {
  'use strict';

  const HOLIDAY_BACKGROUND = '#eef3e5';
  const HOLIDAY_TEXT = '#4f5d27';

  function hebcalUrl(startYear, numberOfYears, isHebrew) {
    const params = new URLSearchParams({
      v: '1',
      cfg: 'json',
      year: String(startYear),
      yt: 'G',
      month: 'x',
      ny: String(numberOfYears),
      i: 'on',
      maj: 'on',
      min: 'on',
      mod: 'on',
      mf: 'on',
      c: 'off',
      lg: isHebrew ? 'he' : 'en'
    });
    return 'https://www.hebcal.com/hebcal?' + params.toString();
  }

  function toCalendarHolidays(items, isHebrew) {
    if (!Array.isArray(items)) return [];

    return items
      .filter(function (item) {
        return item && item.category === 'holiday' && /^\d{4}-\d{2}-\d{2}$/.test(item.date || '');
      })
      .map(function (item) {
        const parts = item.date.split('-').map(Number);
        return {
          day: parts[2],
          month: parts[1],
          year: parts[0],
          title: isHebrew && item.hebrew ? item.hebrew : item.title,
          backgroundColor: HOLIDAY_BACKGROUND,
          textColor: HOLIDAY_TEXT
        };
      });
  }

  async function addJewishHolidays(calendar, isHebrew, fetchImpl) {
    const request = fetchImpl || window.fetch.bind(window);
    const currentYear = new Date().getFullYear();
    const response = await request(hebcalUrl(currentYear - 1, 3, isHebrew), {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) throw new Error('Hebcal returned HTTP ' + response.status);

    const payload = await response.json();
    const holidays = toCalendarHolidays(payload.items, isHebrew);
    calendar.addHolidays(holidays, false, true);
    return holidays.length;
  }

  window.CareILJewishHolidays = {
    hebcalUrl: hebcalUrl,
    toCalendarHolidays: toCalendarHolidays,
    add: addJewishHolidays
  };
})(window);
