"""Standard-library development server for Beacon Time Manager."""
from datetime import date, datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re



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
    """Local development adapter; production uses webapp:application."""
    server_version = "Beacon"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Do not retain client IPs, request URLs, or query strings in app logs.
        pass

    def handle_request(self):
        from webapp import dispatch, response
        if len(self.headers.get_all('Host', [])) != 1:
            result = response(400, {'error':'Invalid host'})
        else:
            result = dispatch(self.command, self.path, self.headers)
        status, headers, body = result
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)
        if self.command not in {'GET','HEAD'}:
            self.close_connection = True

    do_GET = handle_request
    do_HEAD = handle_request
    do_POST = handle_request
    do_PUT = handle_request
    do_DELETE = handle_request
    do_PATCH = handle_request
    do_OPTIONS = handle_request


if __name__ == '__main__':
    print('Beacon Time Manager listening on 127.0.0.1:8000', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
