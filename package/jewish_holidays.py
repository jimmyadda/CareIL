"""Israel Jewish-holiday dates used by calendars and appointment validation."""

import datetime
import json
import threading
import time
import urllib.parse
import urllib.request


HEBCAL_URL = "https://www.hebcal.com/hebcal"
_CACHE_SECONDS = 24 * 60 * 60
_cache = {}
_cache_lock = threading.Lock()


def _fetch_year(year):
    query = urllib.parse.urlencode({
        "v": 1, "cfg": "json", "year": year, "yt": "G", "month": "x",
        "i": "on", "maj": "on", "min": "on", "mod": "on", "mf": "on",
        "c": "off", "lg": "he",
    })
    request = urllib.request.Request(
        HEBCAL_URL + "?" + query,
        headers={"Accept": "application/json", "User-Agent": "CareIL/1.0"},
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        item["date"]: item.get("hebrew") or item.get("title") or "Holiday"
        for item in payload.get("items", [])
        if item.get("category") == "holiday"
        and len(item.get("date", "")) == 10
    }


def holidays_for_year(year):
    """Return {YYYY-MM-DD: title}, using a 24-hour in-process cache."""
    year = int(year)
    now = time.time()
    with _cache_lock:
        cached = _cache.get(year)
        if cached and now - cached[0] < _CACHE_SECONDS:
            return dict(cached[1])
    try:
        holidays = _fetch_year(year)
    except Exception:
        # A stale cache is safer than losing known holiday blocking during an outage.
        with _cache_lock:
            cached = _cache.get(year)
            if cached:
                return dict(cached[1])
        raise
    with _cache_lock:
        _cache[year] = (now, holidays)
    return dict(holidays)


def holiday_name(value):
    """Return the holiday name for a date/datetime value, or None."""
    if isinstance(value, datetime.datetime):
        day = value.date()
    elif isinstance(value, datetime.date):
        day = value
    else:
        text = str(value or "").strip()[:10]
        try:
            day = datetime.datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return None
    return holidays_for_year(day.year).get(day.isoformat())

