"""Read-only HTTP/WSGI boundary. Personal planner data is never accepted here."""
from base64 import b64encode
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from threading import BoundedSemaphore
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlparse
import json
import mimetypes
import os
import re

from daily_verse import load_verse
from schedule_source import load_official_schedule

ROOT = Path(__file__).resolve().parent
SPORTS = {'baseball','mens-basketball','womens-basketball','mens-soccer','womens-soccer',
          'volleyball','womens-volleyball','beach-volleyball','softball','mens-cross-country',
          'womens-cross-country','mens-track-and-field','womens-track-and-field','mens-golf','womens-golf','esports'}
PUBLIC_FILES = {'index.html','academic-calendar.js','academic-calendar.json','bible-verses.js',
                'calendar-import.js','privacy-storage.js','planner-views.css','planner-views.js',
                'schedule-pdf.js','theme.css','vendor/jspdf.umd.min.js','assets/beacon-b.png'}
API_SLOTS = BoundedSemaphore(4)


def security_headers():
    html = (ROOT / 'index.html').read_text()
    hashes = ["'sha256-" + b64encode(sha256(script.encode()).digest()).decode() + "'"
              for script in re.findall(r'<script>(.*?)</script>', html, re.S)]
    policy = "default-src 'self'; script-src 'self' " + ' '.join(hashes) + "; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; frame-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    headers = {'Content-Security-Policy': policy, 'X-Content-Type-Options':'nosniff',
               'X-Frame-Options':'DENY', 'Referrer-Policy':'no-referrer',
               'Cross-Origin-Opener-Policy':'same-origin', 'Cross-Origin-Resource-Policy':'same-origin',
               'Permissions-Policy':'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
               'Cache-Control':'no-store'}
    if os.environ.get('BEACON_HTTPS') == '1':
        headers['Strict-Transport-Security'] = 'max-age=31536000'
    return headers


def response(status, body, content_type='application/json', extra=None):
    if not isinstance(body, bytes):
        body = json.dumps(body, ensure_ascii=True).encode()
    headers = {**security_headers(), 'Content-Type':content_type, 'Content-Length':str(len(body))}
    if extra:
        headers.update(extra)
    return status, headers, body


def dispatch(method, target, headers):
    if len(target) > 2048:
        return response(414, {'error':'Request URL is too long'})
    host = headers.get('Host', '')
    try:
        if not re.fullmatch(r'[A-Za-z0-9.-]+(?::[0-9]{1,5})?', host):
            raise ValueError('Invalid host')
        hostname = urlparse('//'+host).hostname.lower()
    except (ValueError, AttributeError):
        return response(400, {'error':'Invalid host'})
    allowed = {'localhost','127.0.0.1'} | {h.strip().lower() for h in os.environ.get('BEACON_ALLOWED_HOSTS','').split(',') if h.strip()}
    if hostname not in allowed:
        return response(400, {'error':'Host is not configured for this site'})
    if method not in {'GET','HEAD'}:
        return response(405, {'error':'This server accepts no planner data or file uploads'}, extra={'Allow':'GET, HEAD'})
    url = urlparse(target)
    if url.path.startswith('/api/'):
        if method != 'GET':
            return response(405, {'error':'Use GET'}, extra={'Allow':'GET'})
        origin = headers.get('Origin')
        if headers.get('Sec-Fetch-Site') == 'cross-site' or (origin and urlparse(origin).netloc.lower() != host.lower()):
            return response(403, {'error':'Cross-site API requests are not allowed'})
        if url.path not in {'/api/schedule','/api/verse'}:
            return response(404, {'error':'Unknown endpoint'})
        params=parse_qs(url.query,keep_blank_values=True)
        if set(params)-({'sport'} if url.path=='/api/schedule' else set()) or any(len(v)!=1 for v in params.values()):
            return response(400, {'error':'Unsupported request parameters'})
        sport = params.get('sport',[''])[0]
        if url.path == '/api/schedule' and sport not in SPORTS:
            return response(400, {'error':'Unknown sport'})
        if not API_SLOTS.acquire(blocking=False):
            return response(429, {'error':'The service is busy. Please retry shortly.'}, extra={'Retry-After':'15'})
        try:
            result = load_verse() if url.path == '/api/verse' else load_official_schedule(sport)
            return response(200, result)
        except HTTPError as error:
            return response(502, {'error':'Official service unavailable', 'detail':f'The source returned HTTP {error.code}. Previously saved events are kept.'})
        except (URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError, UnicodeError):
            return response(502, {'error':'Unable to load the NIV verse. Retry or read it on Bible Gateway.'} if url.path == '/api/verse' else {'error':'The official schedule could not be retrieved or verified. Previously saved events are kept.'})
        finally:
            API_SLOTS.release()
    name = 'index.html' if url.path == '/' else unquote(url.path).removeprefix('/')
    if name not in PUBLIC_FILES:
        return response(404, {'error':'Not found'})
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        return response(404, {'error':'Not found'})
    content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if content_type.startswith('text/') or content_type in {'application/javascript','application/json'}:
        content_type += '; charset=utf-8'
    result = response(200, path.read_bytes(), content_type)
    return (result[0],result[1],b'') if method == 'HEAD' else result


def application(environ, start_response):
    """WSGI entry point for a production server; no request body is read."""
    headers = {'Host':environ.get('HTTP_HOST',''), 'Origin':environ.get('HTTP_ORIGIN',''),
               'Sec-Fetch-Site':environ.get('HTTP_SEC_FETCH_SITE','')}
    target = environ.get('PATH_INFO','/')
    if environ.get('QUERY_STRING'):
        target += '?' + environ['QUERY_STRING']
    try:
        status, outgoing, body = dispatch(environ.get('REQUEST_METHOD','GET'), target, headers)
    except Exception:
        # Return no stack trace, request text, or user data in a public response.
        status, outgoing, body = response(500, {'error':'The service is temporarily unavailable'})
    start_response(f'{status} {HTTPStatus(status).phrase}', list(outgoing.items()))
    return [body]
