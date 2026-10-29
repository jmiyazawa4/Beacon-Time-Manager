import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import dt, parse_ics_result


def calendar(*events):
    return 'BEGIN:VCALENDAR\r\n' + '\r\n'.join('BEGIN:VEVENT\r\n' + event + '\r\nEND:VEVENT' for event in events) + '\r\nEND:VCALENDAR'


class CalendarTests(unittest.TestCase):
    def test_pacific_seasons_and_dst_boundary(self):
        for value, offset in [('20260115T120000', '-08:00'), ('20260715T120000', '-07:00'),
                              ('20260308T013000', '-08:00'), ('20260308T033000', '-07:00'),
                              ('20261101T003000', '-07:00'), ('20261101T023000', '-08:00')]:
            with self.subTest(value=value):
                self.assertTrue(dt(value).endswith(offset))
        with self.assertRaises(ValueError):
            dt('20260308T023000')

    def test_explicit_timezone_and_utc(self):
        self.assertEqual(dt('20260115T120000', {'TZID': 'America/New_York'}), '2026-01-15T12:00:00-05:00')
        self.assertEqual(dt('20260115T200000Z'), '2026-01-15T20:00:00+00:00')

    def test_all_day_exclusive_end_and_default(self):
        result = parse_ics_result(calendar('UID:one\r\nDTSTART;VALUE=DATE:20260115\r\nDTEND;VALUE=DATE:20260117\r\nSUMMARY:Meet',
                                            'UID:two\r\nDTSTART;VALUE=DATE:20260120\r\nSUMMARY:Meet'))
        self.assertEqual(result['events'][0]['start'], '2026-01-15')
        self.assertEqual(result['events'][0]['end'], '2026-01-17')
        self.assertTrue(result['events'][0]['allDay'])
        self.assertEqual(result['events'][1]['end'], '2026-01-21')

    def test_duplicates_updates_and_cancellation(self):
        result = parse_ics_result(calendar('UID:x\r\nDTSTART:20260115T120000\r\nSUMMARY:Old',
                                            'UID:x\r\nDTSTART:20260116T120000\r\nSUMMARY:Updated\r\nSTATUS:CANCELLED'))
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['events'][0]['title'], 'Updated')
        self.assertEqual(result['events'][0]['status'], 'CANCELLED')

    def test_escaping_folding_and_timezone(self):
        result = parse_ics_result(calendar('DTSTART;TZID=America/Los_Angeles:20260115T120000\r\nSUMMARY:Home\\, visitor\\nGame\r\n continued\r\nLOCATION:Gym\\; court'))
        event = result['events'][0]
        self.assertEqual(event['title'], 'Home, visitor Gamecontinued')
        self.assertEqual(event['location'], 'Gym; court')
        self.assertTrue(event['start'].endswith('-08:00'))

    def test_invalid_and_unsupported_entries_are_reported(self):
        result = parse_ics_result(calendar('DTSTART:20260230T120000\r\nSUMMARY:Invalid date',
                                            'DTSTART:20260115T120000\r\nSUMMARY:Recurring\r\nRRULE:FREQ=WEEKLY',
                                            'DTSTART;TZID=Unknown/Zone:20260115T120000\r\nSUMMARY:Unknown zone',
                                            'DTSTART:20260115T120000\r\nDTEND:20260115T110000\r\nSUMMARY:Invalid end'))
        self.assertEqual(result, {'events': [], 'skipped': 4})
        with self.assertRaises(ValueError):
            parse_ics_result('<html>not a calendar</html>')


if __name__ == '__main__':
    unittest.main()
