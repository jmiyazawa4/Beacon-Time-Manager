"""Maintainer-only manual refresh of public official season snapshots."""
from argparse import ArgumentParser
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'beacon-planner'))
from schedule_source import load_official_schedule
SPORTS=['baseball','mens-basketball','womens-basketball','mens-soccer','womens-soccer','womens-volleyball','beach-volleyball','softball','mens-cross-country','womens-cross-country','mens-track-and-field','womens-track-and-field','mens-golf','womens-golf','esports']

def main():
 parser=ArgumentParser(description=__doc__)
 parser.add_argument('--sport',choices=SPORTS,action='append')
 args=parser.parse_args();failed=[]
 for sport in args.sport or SPORTS:
  try:
   data=load_official_schedule(sport)
   if data.get('skipped'):raise ValueError('Some source entries could not be verified; review the source before publishing')
   data.update(available=True,note='Saved official season schedule. Dates may change; confirm with the official athletics site.')
   path=ROOT/'beacon-planner/schedules'/(sport+'.json');path.parent.mkdir(exist_ok=True)
   path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
   print(sport,len(data['events']),'events saved',flush=True)
  except Exception as error:
   failed.append(sport);print(sport,'not updated:',type(error).__name__,str(error)[:180],flush=True)
 if failed:raise SystemExit('Existing snapshots preserved for failed updates: '+', '.join(failed))
if __name__=='__main__':main()
