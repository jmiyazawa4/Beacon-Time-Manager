import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from daily_verse import parse_payload


class DailyVerseTests(unittest.TestCase):
    def fixture(self):
        return {'votd': {'text': '<b>Test fixture, not Scripture.</b>', 'display_ref': 'Fixture reference', 'copyright': 'Fixture publisher attribution', 'permalink': 'https://www.biblegateway.com/'}}

    def test_jsonp_payload_preserves_attribution(self):
        result = parse_payload('BG.votdWriteCallback(' + json.dumps(self.fixture()) + ');')
        self.assertEqual(result['translation'], 'NIV')
        self.assertEqual(result['text'], 'Test fixture, not Scripture.')
        self.assertEqual(result['copyright'], 'Fixture publisher attribution')

    def test_missing_attribution_is_rejected(self):
        fixture = self.fixture()
        del fixture['votd']['copyright']
        with self.assertRaises(ValueError):
            parse_payload(json.dumps(fixture))

    def test_payload_is_never_executed_and_links_are_restricted(self):
        with self.assertRaises(ValueError):
            parse_payload('BG.votdWriteCallback({}); alert("unexpected");')
        fixture = self.fixture()
        fixture['votd']['permalink'] = 'javascript:alert(1)'
        self.assertTrue(parse_payload(json.dumps(fixture))['link'].startswith('https://www.biblegateway.com/passage/'))


if __name__ == '__main__':
    unittest.main()
