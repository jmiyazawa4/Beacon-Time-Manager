"""Standard-library development server for Beacon Time Manager."""
from datetime import date, datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json
import re
from schedule_source import load_official_schedule
from daily_verse import load_verse

SPORTS = {'baseball', 'mens-basketball', 'womens-basketball', 'mens-soccer',
          'womens-soccer', 'volleyball', 'womens-volleyball', 'beach-volleyball', 'softball',
          'mens-cross-country', 'womens-cross-country', 'mens-track-and-field',
          'womens-track-and-field', 'mens-golf', 'womens-golf', 'esports'}
MAX_FEED_BYTES = 2_000_000
PACIFIC = ZoneInfo('America/Los_Angeles')


def unescape(value):
    return re.sub(r'\\([nN,;\\])', lambda m: ' ' if m[1].lower() == 'n' else m[1], value)


def dt(value, params=None):
    """Keep all-day values as dates; resolve floating times in Pacific time."""
    params = params or {}
    if params.get('VALUE') == 'DATE' or re.fullmatch(r'\d{8}', value):
        return datetime.strptime(value, '%Y%m%d').date().isoformat()
    utc = value.endswith('Z')
    value = value.removesuffix('Z')
    parsed = datetime.strptime(value, '%Y%m%dT%H%M%S' if len(value) == 15 else '%Y%m%dT%H%M')
    zone = timezone.utc if utc else ZoneInfo(params.get('TZID', 'America/Los_Angeles'))
    aware = parsed.replace(tzinfo=zone)
    if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != parsed:
        raise ValueError('Nonexistent local time')
    return aware.isoformat()


def parse_ics_result(raw):
    if 'BEGIN:VCALENDAR' not in raw or 'END:VCALENDAR' not in raw:
        raise ValueError('The file is not an iCalendar calendar')
    events, skipped, obj = {}, 0, None
    for line in re.sub(r'\r?\n[ \t]', '', raw).splitlines():
        if line == 'BEGIN:VEVENT':
            obj = {}
        elif line == 'END:VEVENT':
            try:
                if not obj or 'RRULE' in obj or 'RECURRENCE-ID' in obj:
                    raise ValueError('Recurring event not supported')
                start = dt(*obj['DTSTART'])
                title = unescape(obj['SUMMARY'][0]).strip()
                if not title:
                    raise ValueError('Missing event title')
                all_day = len(start) == 10
                end = dt(*obj['DTEND']) if 'DTEND' in obj else None
                if end:
                    if (len(end) == 10) != all_day:
                        raise ValueError('Mixed date and timestamp values')
                    if all_day:
                        valid_end = date.fromisoformat(end) > date.fromisoformat(start)
                    else:
                        valid_end = datetime.fromisoformat(end) > datetime.fromisoformat(start)
                    if not valid_end:
                        raise ValueError('End must follow start')
                elif all_day:
                    end = (date.fromisoformat(start) + timedelta(days=1)).isoformat()
                status = obj.get('STATUS', ('', {}))[0].upper()
                uid = obj.get('UID', (start + title, {}))[0]
                events[uid] = {'id': uid, 'title': title, 'start': start, 'end': end,
                               'location': unescape(obj.get('LOCATION', ('', {}))[0]),
                               'allDay': all_day, 'status': status}
            except (KeyError, ValueError, ZoneInfoNotFoundError):
                skipped += 1
            obj = None
        elif obj is not None and ':' in line:
            key, value = line.split(':', 1)
            name, *parameters = key.split(';')
            params = dict(p.split('=', 1) for p in parameters if '=' in p)
            obj[name.upper()] = (value, {k.upper(): v.strip('"') for k, v in params.items()})
    return {'events': list(events.values()), 'skipped': skipped}


def parse_ics(raw):
    return parse_ics_result(raw)['events']


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/api/verse':
            try:
                return self.send_json(200, load_verse())
            except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
                return self.send_json(502, {'error': 'Unable to load the NIV verse. Retry or read it on Bible Gateway.'})
        if url.path != '/api/schedule':
            return super().do_GET()
        sport = parse_qs(url.query).get('sport', [''])[0]
        if sport not in SPORTS:
            return self.send_json(400, {'error': 'Unknown sport'})
        try:
            result = load_official_schedule(sport)
            self.send_json(200, result)
        except HTTPError as error:
            self.send_json(502, {'error': 'Official schedule unavailable',
                                'detail': f'The athletics site returned HTTP {error.code}. View the official schedule or import an .ics file.'})
        except (URLError, TimeoutError, OSError):
            self.send_json(502, {'error': 'Cannot reach the official schedule',
                                'detail': 'Check the connection or import an official .ics file.'})
        except (ValueError, UnicodeError) as error:
            self.send_json(502, {'error': 'Official schedule could not be verified',
                                'detail': str(error)[:200]})

    def do_POST(self):
        if urlparse(self.path).path != '/api/import':
            return self.send_json(404, {'error': 'Unknown endpoint'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.send_json(400, {'error': 'Invalid content length'})
        if not 0 < length <= MAX_FEED_BYTES:
            return self.send_json(413, {'error': 'Calendar must be between 1 byte and 2 MB'})
        try:
            result = parse_ics_result(self.rfile.read(length).decode('utf-8-sig'))
        except (ValueError, UnicodeError):
            return self.send_json(400, {'error': 'Select a valid .ics calendar file'})
        self.send_json(200, result)

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print('Beacon Time Manager listening on 127.0.0.1:8000', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
