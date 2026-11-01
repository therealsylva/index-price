import csv
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from project_market_history import export, read_csv, stamp
from market_history import FIELDS
ROOT=Path(__file__).resolve().parents[1]

class ProjectionTest(unittest.TestCase):
 def test_full_scenario_preserves_history_bounds_ratios_and_volume(self):
  source=ROOT/'market-history/2026-11-01'
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp)/'scenario'
   m=export(source,out,stamp('2026-12-30T23:00:00Z'),stamp('2026-11-01T19:00:00Z'))
   self.assertEqual(len(m['instruments']),38)
   self.assertEqual(m['totalCandles'],142766)
   rows={i['symbol']:read_csv(out/i['path']) for i in m['instruments']}
   old=json.loads((source/'manifest.json').read_text())
   for i in old['instruments']:
    previous=read_csv(source/i['path']);current=rows[i['symbol']]
    self.assertEqual([{k:str(r[k]) for k in FIELDS} for r in current[:len(previous)]],previous)
    self.assertEqual(current[-1]['closeTime'],m['to'])
    self.assertLess(len(current),5000)
    for n,r in enumerate(current):
     o,h,l,c,ref,lo,hi=[int(r[k]) for k in FIELDS[2:9]]
     self.assertTrue(lo<=l<=min(o,c)<=max(o,c)<=h<=hi)
     self.assertGreaterEqual(Decimal(r['volumeUsd']),0)
     if n>=len(previous):
      self.assertEqual(current[n-1]['closeTime'],r['openTime'])
      self.assertEqual(int(current[n-1]['closeMicros']),o)
      self.assertEqual(r['dataSource'],'synthetic_projection')
   for i in m['instruments']:
    if '/' not in i['symbol']:continue
    x,y=i['symbol'].split('/')
    for a,b,p in zip(rows[x],rows[y],rows[i['symbol']]):
     # Exact synchronized ratios at open and close; high/low come from shared samples.
     for key in ['openMicros','closeMicros']:
      self.assertEqual(int(p[key]),1_000_000_000*int(a[key])//int(b[key]))
   from project_market_history import monday
   actual={}
   for candles in rows.values():
    for r in candles:
     w=monday(stamp(r['openTime']));actual[w]=actual.get(w,Decimal(0))+Decimal(r['volumeUsd'])
   for week in m['weeklyVolume']:
    self.assertEqual(actual[monday(stamp(week['coverageFrom']))],Decimal(week['volumeUsd']))
    if week['coverageTo']<='2026-11-01T23:00:00Z': self.assertTrue(5e6<=float(week['weeklyEquivalentUsd'])<=15e6)
   tail=sum(Decimal(r['volumeUsd']) for candles in rows.values() for r in candles if stamp(r['openTime'])>=stamp(m['to'])-7*86400)
   self.assertTrue(Decimal(10_000_000)<=tail<=Decimal(50_000_000))
   self.assertEqual({i['symbol'] for i in m['adminInstruments']},set(rows)-{'MCI/MUN'}|{'MUN/MCI'})
   self.assertEqual(sum(Decimal(r['volumeUsd']) for i in m['adminInstruments'] for r in read_csv(out/i['path'])),sum(actual.values()))
   # Fixed seed/capture is reproducible, including CSV bytes and manifest hashes.
   other=Path(temp)/'again';again=export(source,other,stamp(m['to']),stamp(m['generatedAt']))
   self.assertEqual(m,again)

if __name__=='__main__':unittest.main()
