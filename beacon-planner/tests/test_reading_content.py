from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ReadingContentTests(unittest.TestCase):
 def test_year_plan_has_four_readings_each_day_and_attribution(self):
  plan=json.loads((ROOT/'reading-plan.json').read_text())
  self.assertEqual(len(plan['days']),365)
  self.assertTrue(all(len(row)==4 and all(isinstance(ref,str) and ref for ref in row) for row in plan['days']))
  self.assertEqual(plan['days'][0],['Genesis 1','Matthew 1','Ezra 1','Acts 1'])
  self.assertEqual(plan['days'][-1],['2 Chronicles 36','Revelation 22','Malachi 4','John 21'])
  self.assertEqual(plan['license'],'Apache-2.0')
  self.assertIn('Apache License',plan['licenseText'])
 def test_kjv_verses_are_complete_unique_and_sourced(self):
  data=json.loads((ROOT/'daily-verses.json').read_text())
  self.assertEqual(data['translation'],'KJV')
  self.assertEqual(len(data['days']),365)
  self.assertEqual(len({entry['reference'] for entry in data['days']}),365)
  self.assertTrue(all(entry['reference'] and entry['text'] for entry in data['days']))
  self.assertIn('public domain in the United States',data['copyright'])
  self.assertIn('MIT License',data['licenseText'])
  self.assertEqual(data['leapDay']['reference'],'Psalm 118:24')
 def test_all_saved_sports_use_public_sources_and_dates(self):
  paths=list((ROOT/'schedules').glob('*.json'))
  self.assertEqual(len(paths),15)
  for path in paths:
   with self.subTest(sport=path.stem):
    data=json.loads(path.read_text())
    self.assertEqual(data['source'],'https://bushnellbeacons.com/sports/'+path.stem+'/schedule')
    self.assertTrue(data['fetchedAt'])
    self.assertTrue(data['events'])
    self.assertEqual(data.get('skipped',0),0)
if __name__=='__main__':unittest.main()
