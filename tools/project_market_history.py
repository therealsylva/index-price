#!/usr/bin/env python3
"""Create reproducible, explicitly synthetic OHLC + USD-volume scenario CSVs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from market_history import FIELDS, SCALE, all_values, clip, digest, project, seed, stamp, utc, write_json

WAT = timezone(timedelta(hours=1))
EXTRA = ['volumeUsd', 'dataSource']
VERSION = 'synthetic-ohlcv-scenario-v1'
RAMP_START = stamp('2026-11-01T00:00:00Z')
RAMP_END = stamp('2026-12-30T23:00:00Z')  # all of December 30, Nigeria time
POPULAR = {'BAR': 2.8, 'RMD': 2.7, 'MUN': 2.1, 'MCI': 2.0, 'ARS': 1.8,
           'CHE': 1.7, 'LIV': 1.9, 'MBP': 1.8, 'HLD': 1.8, 'LMY': 1.6}


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def monday(at):
    d = datetime.fromtimestamp(at, WAT).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((d - timedelta(days=d.weekday())).timestamp())


def date_wat(at):
    return datetime.fromtimestamp(at, WAT).strftime('%Y-%m-%d')


def forward(rows, roster, context, start, end):
    """Unknown sporting references stay frozen; only scenario market prices vary."""
    bases = [s for s, *_ in roster['clubs'] + roster['athletes']]
    edges = roster['pairs']
    bands = {s: tuple(int(rows[s][-1][k]) for k in ['referenceMicros', 'lowerMicros', 'upperMicros']) for s in bases}
    values = {s: int(rows[s][-1]['closeMicros']) for s in bases}
    values = project(values, bands, edges)
    teams = {s: provider for s, _, _, provider in roster['clubs']}
    for s, _, entity, _ in roster['athletes']:
        memberships = context['players'][entity]['memberships']
        active = [m for m in memberships if stamp(m['from']) <= start and (m['to'] is None or start < stamp(m['to']))]
        teams[s] = max(active, key=lambda m: m['from'])['teamId']
    rngs = {s: random.Random(seed(VERSION+'|price|'+s)) for s in bases}
    shared_rng = random.Random(seed(VERSION+'|shared'))
    z = {s: (values[s]-bands[s][0])/(bands[s][2]-bands[s][0] if values[s]>=bands[s][0] else bands[s][0]-bands[s][1]) for s in bases}
    noise = dict.fromkeys(bases, 0.0)
    velocity = dict.fromkeys(bases, 0.0)
    state = {s: {'until': start, 'target': z[s], 'speed': .025, 'kind': 'RANGE'} for s in bases}
    shared = 0.0
    bar_start = start
    current, ranges = all_values(values, bands, edges)
    points = {s: [p] for s, p in current.items()}
    previous = start
    for at in range(start+300, end+300, 300):
        at = min(at, end)
        dt = (at-previous)/300
        shared = .98**dt*shared + shared_rng.gauss(0,.005)*math.sqrt(dt)
        for s in bases:
            rng = rngs[s]
            st = state[s]
            if at >= st['until']:
                target = rng.uniform(-.86,.86)
                if rng.random() < .08:
                    target = rng.choice([-1,1])*.98
                st.update(until=at+rng.randint(12,72)*3600, target=target,
                          speed=rng.uniform(.012,.04), kind='TREND_UP' if target>z[s]+.15 else 'TREND_DOWN' if target<z[s]-.15 else 'RANGE')
            # Local session activity and a persistent common-club factor; no fabricated results.
            hour = datetime.fromtimestamp(at,WAT).hour
            session = 1.3 if 15<=hour<=23 else .7 if 2<=hour<=7 else 1.0
            club = math.sin(at/(3600*6)+(seed(str(teams[s]))%1000))*.06
            noise[s] = .97**dt*noise[s]+rng.gauss(0,.014)*math.sqrt(dt)*session
            desired = clip(st['target']+noise[s]+shared+club,-.99,.99)
            velocity[s] = .84**dt*velocity[s]+(1-.84**dt)*(desired-z[s])*st['speed']
            z[s] = clip(z[s]+velocity[s]*dt,-.99,.99)
            r,lo,hi = bands[s]
            values[s] = round(r+z[s]*(hi-r if z[s]>=0 else r-lo))
        values = project(values,bands,edges)
        current,_ = all_values(values,bands,edges)
        for s,p in current.items(): points[s].append(p)
        if at%3600==0 or at==end:
            for s, ps in points.items():
                r,lo,hi = ranges[s]
                kind = state[s]['kind'] if s in state else 'RELATIVE_VALUE'
                rows[s].append(dict(zip(FIELDS,[utc(bar_start),utc(at),ps[0],max(ps),min(ps),ps[-1],r,lo,hi,'','SCENARIO_'+kind])))
            points = {s:[p] for s,p in current.items()}
            bar_start = at
        for s in bases:
            r,lo,hi = bands[s]
            z[s] = (values[s]-r)/(hi-r if values[s]>=r else r-lo)
        previous = at
        if at==end: break


def usd(cents):
    return f'{cents//100}.{cents%100:02d}'


def add_volume(rows, roster, context, cutoff, generated_at, end):
    weeks = defaultdict(list)
    rng = random.Random(seed(VERSION+'|volume'))
    persistence = defaultdict(float)
    # Known schedules only influence activity, never future index values/results.
    teams = {s:provider for s,_,_,provider in roster['clubs']}
    for s,_,entity,_ in roster['athletes']:
        memberships=context['players'][entity]['memberships']
        active=[m for m in memberships if stamp(m['from'])<=cutoff and (m['to'] is None or cutoff<stamp(m['to']))]
        teams[s]=max(active,key=lambda m:m['from'])['teamId']
    fixtures=defaultdict(list)
    for f in context['fixtures']:
        for t in [f['homeTeamId'],f['awayTeamId']]: fixtures[t].append(stamp(f['kickoff']))
    first = min(stamp(v[0]['openTime']) for v in rows.values())
    for s, candles in rows.items():
        for r in candles:
            at, finish = stamp(r['openTime']), stamp(r['closeTime'])
            # Splitting at WAT Monday gives precise weekly accounting, even for boundary bars.
            if monday(at)!=monday(finish-1): raise ValueError('bar crosses WAT week boundary')
            d=datetime.fromtimestamp(at,WAT)
            session = .22 if 2<=d.hour<=7 else .65 if d.hour<13 else 1.5 if 16<=d.hour<=23 else 1.0
            weekend = 1.55 if d.weekday()>=5 else 1.0
            participants = s.split('/')
            kicks=[k for leg in participants for k in fixtures[teams[leg]]]
            proximity=min((abs(at-k) for k in kicks),default=9999999)
            fixture=1+2.3*math.exp(-proximity/(3*3600)) if proximity<86400 else 1.0
            p=int(r['openMicros']); move=abs(int(r['closeMicros'])-p)/p
            spread=(int(r['highMicros'])-int(r['lowMicros']))/p
            volatility=1+min(4,60*move+35*spread)
            persistence[s]=.76*persistence[s]+rng.gauss(0,.28)
            weight=POPULAR.get(s,.65 if '/' in s else 1)*session*weekend*fixture*volatility
            weight*=math.exp(persistence[s]+rng.gauss(0,.60))
            if rng.random()<.012: weight*=rng.uniform(3,11)  # occasional notional bursts
            weight*=(finish-at)/3600
            r['dataSource']='synthetic_history' if finish<=cutoff else 'synthetic_projection'
            weeks[monday(at)].append((s,r,weight))
    summary=[]
    for week,items in sorted(weeks.items()):
        mid=week+3.5*86400
        growth=clip((mid-RAMP_START)/(RAMP_END-RAMP_START),0,1)
        # Historical weeks stay in the requested initial range. Growth is gradual,
        # with week-to-week variation rather than identical weekly steps.
        wrng=random.Random(seed(VERSION+'|week|'+str(week)))
        target=round((10_000_000+22_000_000*growth)*wrng.uniform(.87,1.13)*100)
        covered_start=max(first,week);covered_end=min(end,week+7*86400)
        target=round(target*(covered_end-covered_start)/(7*86400))
        total_weight=sum(w for _,_,w in items)
        allocations=[int(target*w/total_weight) for _,_,w in items]
        remainder=target-sum(allocations)
        for i in range(remainder): allocations[i%len(allocations)]+=1
        for (_,r,_),cents in zip(items,allocations): r['volumeUsd']=usd(cents)
        summary.append({'weekStartWAT':date_wat(week),'coverageFrom':utc(covered_start),'coverageTo':utc(covered_end),
                        'days':(covered_end-covered_start)/86400,'volumeUsd':usd(target),
                        'weeklyEquivalentUsd':usd(round(target*7*86400/(covered_end-covered_start)))})
    return summary


def export(source, output, end, generated_at):
    source=source.resolve();output=output.resolve()
    prior=json.loads((source/'manifest.json').read_text())
    roster=json.loads((source/'inputs/instruments.json').read_text())
    context=json.loads((source/'inputs/context.json').read_text())
    cutoff=stamp(prior['to'])
    if not cutoff<end<=RAMP_END: raise ValueError('end must extend source and be at/before December 30 WAT end')
    if end%3600: raise ValueError('end must be on an hourly boundary')
    if output==source or source in output.parents: raise ValueError('output must not overwrite source')
    rows={}
    for item in prior['instruments']:
        p=source/item['path']
        if digest(p)!=item['sha256']: raise ValueError('source checksum mismatch')
        rows[item['symbol']]=read_csv(p)
    old_counts={s:len(v) for s,v in rows.items()}
    forward(rows,roster,context,cutoff,end)
    summary=add_volume(rows,roster,context,cutoff,generated_at,end)
    instruments=[]
    for item in prior['instruments']:
        s=item['symbol'];p=output/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS+EXTRA,lineterminator='\n');w.writeheader();w.writerows(rows[s])
        instruments.append({**item,'candles':len(rows[s]),'sha256':digest(p),'originalCandles':old_counts[s]})
    # The live catalog uses MUN/MCI. Supply its inverse without double-counting
    # the pair in the 38-instrument aggregate/weekly targets.
    admin=[]
    for item in instruments:
        s=item['symbol'];candles=rows[s];target=s
        if s=='MCI/MUN':
            target='MUN/MCI';candles=[]
            for r in rows[s]:
                v=dict(r)
                inverse=lambda k: str((10**18+int(r[k])//2)//int(r[k]))
                v.update(openMicros=inverse('openMicros'),closeMicros=inverse('closeMicros'),
                         highMicros=inverse('lowMicros'),lowMicros=inverse('highMicros'),
                         referenceMicros=inverse('referenceMicros'),lowerMicros=inverse('upperMicros'),upperMicros=inverse('lowerMicros'))
                candles.append(v)
        p=output/'admin'/(target.replace('/','-')+'.csv');p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS+EXTRA,lineterminator='\n');w.writeheader();w.writerows(candles)
        admin.append({'symbol':target,'archiveSymbol':s,'path':str(p.relative_to(output)),'sha256':digest(p),'candles':len(candles)})
    p=output/'weekly-volume.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
    manifest={'schema':'blackbook.synthetic-ohlcv-scenario.v1','modelVersion':VERSION,
              'from':prior['from'],'to':utc(end),'generatedAt':utc(generated_at),'verifiedReferenceAsOf':roster['referencePublication'],
              'originalPriceCutoff':prior['to'],'sourceManifestSha256':digest(source/'manifest.json'),
              'priceScale':1_000_000,'volumeUnit':'USD','volumeMeaning':'single-counted synthetic traded notional; not margin, deposits or actual executions',
              'volumeScope':'sum of 38 distinct instruments; inverse admin alias is not an additional market',
              'initialWeeklyRangeUsd':[5_000_000,15_000_000],'finalWeeklyRangeUsd':[10_000_000,50_000_000],
              'futureReferencePolicy':'freeze last verified published references and bands; no invented match results',
              'instruments':instruments,'adminInstruments':admin,'weeklyVolume':summary,
              'totalCandles':sum(len(v) for v in rows.values()),'weeklyVolumeSha256':digest(p)}
    write_json(output/'manifest.json',manifest)
    (output/'README.md').write_text('''# BlackBook synthetic OHLCV scenario through December 30, 2026\n\nAll prices and volumes here are SYNTHETIC. They are demo/scenario market data,\nnot actual trades, revenue or verified future sporting performance.\n\nThe 38 `prices/` CSVs preserve every original OHLC/reference/band value through\nNovember 1 08:30 UTC and add USD volume. Further hourly candles extend through\nDecember 30 23:59 Nigeria time (exclusive cutoff December 30 23:00 UTC).\nFuture reference values and bands remain frozen at the last verified publication;\nactual future match updates will require regeneration/reconciliation.\n\nVolume is USD traded notional, counted once per execution scenario, across all\n38 markets combined. Historical full weeks run within $5–15m; weekly activity\ngrows toward $10–50m by December 30. See weekly-volume.csv for actual totals.\nActivity varies with WAT sessions, weekends, known scheduled fixtures, price\nvolatility, market popularity and sporadic bursts. No future result is assumed.\n\n`admin/` is import-ready for the updated admin uploader (13 columns). The\nMCI/MUN archive pair is inverted to the live catalog's MUN/MCI; its volume is\nunchanged and is never counted twice. Each file has fewer than 5,000 candles.\nThe old eleven-column importer cannot accept these files until updated.\n\nUse the supplied batch importer to preview and publish all markets after\ndeploying the OHLCV migration/API patch. Future rows are stored in advance;\npublic charts release only completed candles as time advances.\n''')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'market-history/2026-11-01')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--to',default='2026-12-30T23:00:00Z')
    p.add_argument('--generated-at',required=True)
    a=p.parse_args();m=export(a.source,a.output,stamp(a.to),stamp(a.generated_at))
    print(json.dumps({k:m[k] for k in ['from','to','totalCandles']}))

if __name__=='__main__': main()
