import configparser
import icalendar
import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from io import BytesIO
from datetime import datetime, timedelta
from threading import Lock

config = configparser.ConfigParser()
config.read('config.ini')
endpoint = config.get('api', 'endpoint')
base_path = config.get('api', 'base_path')

if base_path.endswith("/") and len(base_path) > 1:
    base_path = base_path[:-1]

print(f"Merged calendar will be available at {base_path}/{endpoint}/cal.ics")

app = FastAPI(
    root_path=base_path,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

def get_calendar_urls():
    links = config.get('calendars', 'urls').splitlines()
    return [link.strip() for link in links if link != '']

def merge_calendars(urls):
    merged_calendar = icalendar.Calendar()
    merged_calendar.add('prodid', '-//cal2busy//')
    merged_calendar.add('version', '2.0')

    keys_to_keep = [
        'UID', 'DTSTART', 'DTEND', 'RRULE', 'EXDATE',
        'RECURRENCE-ID', 'SUMMARY', 'DTSTAMP', 'SEQUENCE'
    ]

    extra_components_to_keep = [
        # "DAYLIGHT", "STANDARD", "VCALENDAR"
    ]

    for url in urls:
        if url.startswith('webcal'):
            url = url.replace('webcal', 'http')
        response = requests.get(url)
        if response.status_code == 200:
            calendar = icalendar.Calendar.from_ical(response.content)
            for component in calendar.walk():
                if component.name == 'VEVENT':
                    new_event = icalendar.Event()
                    for key in keys_to_keep:
                        if key in component:
                            new_event[key] = component[key]
                    new_event['SUMMARY'] = 'Busy'
                    merged_calendar.add_component(new_event)
                elif component.name in extra_components_to_keep:
                    merged_calendar.add_component(component)
    return merged_calendar

# In-memory cache variables
_cached_calendar_bytes = None
_cached_timestamp = None
_cache_lock = Lock()
CACHE_DURATION = timedelta(minutes=15)

@app.get(f"/{endpoint}/cal.ics", response_class=StreamingResponse)
def get_merged_calendar():
    global _cached_calendar_bytes, _cached_timestamp

    with _cache_lock:
        now = datetime.utcnow()
        if _cached_calendar_bytes and _cached_timestamp and (now - _cached_timestamp < CACHE_DURATION):
            ics_bytes = _cached_calendar_bytes
        else:
            urls = get_calendar_urls()
            merged_calendar = merge_calendars(urls)
            ics_bytes = merged_calendar.to_ical()
            _cached_calendar_bytes = ics_bytes
            _cached_timestamp = now

    return StreamingResponse(BytesIO(ics_bytes), media_type="text/calendar", headers={
        "Content-Disposition": "attachment; filename=merged_calendar.ics"
    })
