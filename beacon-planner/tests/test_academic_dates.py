from datetime import date, timedelta
from pathlib import Path
import json
import unittest

DATA = json.loads((Path(__file__).resolve().parents[1] / 'academic-calendar.json').read_text())


def on(day):
    return [event for event in DATA['events'] if event['start'] <= day < event['end']]


class AcademicDateTests(unittest.TestCase):
    def test_unique_valid_ranges(self):
        self.assertTrue(DATA['verified'])
        events = DATA['events']
        self.assertEqual(len({event['id'] for event in events}), len(events))
        self.assertEqual(len(events), 54)
        for event in events:
            self.assertLess(date.fromisoformat(event['start']), date.fromisoformat(event['end']))
            self.assertTrue(event['appliesTo'])

    def test_holidays_and_inclusive_break_boundaries(self):
        expected = {'2026-09-07','2026-11-11','2026-11-26','2027-01-18','2027-03-26','2027-05-31','2027-07-05'}
        self.assertEqual({e['start'] for e in DATA['events'] if e['kind']=='holiday'}, expected)
        self.assertTrue(any(e['title']=='Thanksgiving Holiday' for e in on('2026-11-27')))
        self.assertFalse(any(e['title']=='Thanksgiving Holiday' for e in on('2026-11-28')))
        for i in range(7):
            day = (date(2027,3,22)+timedelta(days=i)).isoformat()
            self.assertTrue(any(e['title']=='Spring Break' for e in on(day)),day)
        self.assertFalse(any(e['title']=='Spring Break' for e in on('2027-03-29')))
        self.assertEqual({e['kind'] for e in on('2027-03-26') if e['kind'] in ('holiday','break')},{'holiday','break'})

    def test_subterm_deadlines_are_distinct_and_labeled(self):
        for day,scope in [('2026-09-04','Fall 2026 full term'),('2026-09-01','Fall 2026 Session 1 (8 weeks)'),('2026-10-27','Fall 2026 Session 2 (8 weeks)'),('2027-01-22','Spring 2027 full term'),('2027-01-19','Spring 2027 Session 1 (8 weeks)'),('2027-03-16','Spring 2027 Session 2 (8 weeks)'),('2027-05-21','Summer 2027 full term'),('2027-05-18','Summer 2027 Session 1 (7 weeks)'),('2027-07-06','Summer 2027 Session 2 (7 weeks)')]:
            entries=[e for e in on(day) if e['title'].startswith('Last Day to Add/Drop Classes')]
            self.assertTrue(any(scope in e['title'] for e in entries),(day,scope))

    def test_interterm_and_supplied_commencement(self):
        self.assertTrue(any(e['title']=='Interterm 2026' for e in on('2027-01-10')))
        self.assertFalse(any(e['title']=='Interterm 2026' for e in on('2027-01-11')))
        self.assertTrue(any(e['title']=='Commencement' and 'Summer 2027 full term' in e['appliesTo'] for e in on('2027-12-10')))
        self.assertEqual(len([e for e in on('2026-09-07') if e['title']=='Labor Day Holiday']),1)


if __name__ == '__main__':
    unittest.main()
