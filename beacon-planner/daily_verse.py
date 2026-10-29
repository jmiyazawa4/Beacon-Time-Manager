"""Retrieve the provider's NIV widget data without executing third-party code."""
from html import unescape
from html.parser import HTMLParser
from threading import Lock
from time import monotonic
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import json
import re

ENDPOINT = 'https://www.biblegateway.com/votd/votd.write.callback.js?format=json&version=NIV&callback=BG.votdWriteCallback'
_lock = Lock()
_cached = None
_cached_at = 0


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = PlainText()
    parser.feed(str(value or ''))
    return unescape(''.join(parser.parts)).strip()


def parse_payload(raw):
    match = re.fullmatch(r'\s*BG\.votdWriteCallback\((.*)\);?\s*', raw, re.S)
    payload = json.loads(match[1] if match else raw)
    item = payload.get('votd', payload)
    text = plain(item.get('text') or item.get('content'))
    reference = plain(item.get('display_ref') or item.get('reference'))
    copyright = plain(item.get('copyright'))
    if not text or not reference or not copyright or len(text) > 10000 or len(reference) > 300 or len(copyright) > 3000:
        raise ValueError('Missing NIV text or publisher attribution')
    link = 'https://www.biblegateway.com/passage/?search=' + quote(reference) + '&version=NIV'
    candidate = urlparse(str(item.get('permalink', '')))
    if candidate.scheme == 'https' and candidate.hostname and (candidate.hostname == 'biblegateway.com' or candidate.hostname.endswith('.biblegateway.com')):
        link = candidate.geturl()
    return {'text': text, 'reference': reference, 'copyright': copyright, 'translation': 'NIV', 'link': link}


def load_verse():
    global _cached, _cached_at
    with _lock:
        if _cached and monotonic() - _cached_at < 900:
            return _cached
        request = Request(ENDPOINT, headers={'User-Agent': 'BeaconStudentPlanner/1.0', 'Accept': 'application/javascript,application/json'})
        with urlopen(request, timeout=12) as response:
            raw = response.read(100001)
        if len(raw) > 100000:
            raise ValueError('NIV response exceeds size limit')
        _cached = parse_payload(raw.decode('utf-8-sig'))
        _cached_at = monotonic()
        return _cached
