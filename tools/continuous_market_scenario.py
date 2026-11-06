#!/usr/bin/env python3
"""Reproducible chart scenarios from pinned references, never trade records."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from market_history import FIELDS, all_values, clip, digest, project, seed, stamp, utc, write_json
from project_market_history import WAT, add_volume

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'market-history/2026-11-06'
VERSION = 'market-structure-continuous-v3'
RNG_VERSION = 'market-structure-v2'
STEP = 300
MODES = ('RANGE', 'COMPRESSION', 'TREND_UP', 'TREND_DOWN', 'EXPANSION')


def inputs(directory):
    basis = json.loads((directory / 'basis.json').read_text())
    roster = json.loads((directory / 'instruments.json').read_text())
    context = json.loads((directory / 'context.json').read_text())
    start, end = stamp(basis['scenarioFrom']), stamp(basis['scenarioTo'])
    if start >= end or start % STEP or end % 3600:
        raise ValueError('scenario requires a five-minute start and whole-hour end')
    by_id = {r['entityId']: r for r in basis['rows']}
    if len(by_id) != len(basis['rows']):
        raise ValueError('duplicate basis entities')
    for s, _, entity, _ in roster['clubs'] + roster['athletes']:
        r = by_id[entity]
        if not 0 < r['lowerMicros'] < r['referenceMicros'] < r['upperMicros']:
            raise ValueError(f'invalid starting band: {s}')
        if stamp(r['asOf']) > start or stamp(r['lastSportingEventAt']) > start:
            raise ValueError('basis contains future sporting information')
    return basis, roster, context, by_id, start, end


def sentiment(context, symbol, start):
    """Only completed audited team results; never infer a player's performance."""
    matches = context['recentMatches'].get(symbol, [])
    weighted = total = 0.0
    for m in matches:
        available = stamp(m['availableAt'])
        if available > start:
            continue
        w = math.exp(-(start - available) / (7 * 86400))
        weighted += w * clip(m['goalDifference'] / 3, -1, 1)
        total += w
    return weighted / total if total else 0.0


def checked_continuity(directory, basis, roster):
    continuity = json.loads((directory / 'continuity.json').read_text())
    expected = {s for s, *_ in roster['clubs'] + roster['athletes']}
    expected.update('/'.join(pair) for pair in roster['pairs'])
    if set(continuity['rows']) != expected:
        raise ValueError('continuity checkpoint instrument mismatch')
    sources = dict(basis['sourceFiles'])
    sources[continuity['sourceManifest']] = continuity['sourceManifestSha256']
    for row in continuity['rows'].values():
        sources[row['sourcePath']] = row['sourceSha256']
    for name, checksum in sources.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != checksum:
            raise ValueError('continuity source checksum mismatch')
    prior = json.loads((ROOT / continuity['sourceManifest']).read_text())
    if prior['to'] != continuity['at']:
        raise ValueError('continuity source cutoff mismatch')
    for symbol, row in continuity['rows'].items():
        with (ROOT / row['sourcePath']).open() as f:
            previous = list(csv.DictReader(f))[-1]
        if symbol == 'MUN/MCI':
            inverse = lambda k: str((10**18 + int(previous[k]) // 2) // int(previous[k]))
            previous = {**previous, 'openMicros': inverse('openMicros'), 'closeMicros': inverse('closeMicros'),
                        'highMicros': inverse('lowMicros'), 'lowMicros': inverse('highMicros'),
                        'referenceMicros': inverse('referenceMicros'),
                        'lowerMicros': inverse('upperMicros'), 'upperMicros': inverse('lowerMicros')}
        if any(str(row[k]) != previous[k] for k in FIELDS):
            raise ValueError('continuity checkpoint row mismatch: ' + symbol)
    return continuity


def simulate(directory, end_override=None):
    basis, roster, context, by_id, start, end = inputs(directory)
    continuity = checked_continuity(directory, basis, roster)
    if continuity['at'] != utc(start):
        raise ValueError('continuity checkpoint timestamp mismatch')
    if end_override is not None:
        if not start < end_override <= end or end_override % 3600:
            raise ValueError('invalid end override')
        end = end_override
    bases = [s for s, *_ in roster['clubs'] + roster['athletes']]
    edges = roster['pairs']
    bands = {s: tuple(by_id[e][k] for k in ('referenceMicros', 'lowerMicros', 'upperMicros'))
             for s, _, e, _ in roster['clubs'] + roster['athletes']}
    teams = context['teams']
    rngs = {s: random.Random(seed(RNG_VERSION + '|' + s)) for s in bases}
    shared_rng = random.Random(seed(RNG_VERSION + '|shared'))
    form = {s: sentiment(context, s, start) for s in bases}
    values = {s: int(continuity['rows'][s]['closeMicros']) for s in bases}
    projected = project(values, bands, edges)
    if projected != values:
        raise ValueError('checkpoint does not fit the starting bands and pair constraints')
    for s in bases:
        for key, value in zip(('referenceMicros', 'lowerMicros', 'upperMicros'), bands[s]):
            if int(continuity['rows'][s][key]) != value:
                raise ValueError('checkpoint and starting publication disagree: ' + s)
    timeline = {}
    previous_event = start
    for event in basis['bandTimeline']:
        at = stamp(event['at'])
        if at <= previous_event or at % 3600 or at > end:
            raise ValueError('invalid band timeline order or boundary')
        selected = {r['entityId']: r for r in event['rows']}
        if any(stamp(r['asOf']) > at or stamp(r['lastSportingEventAt']) > at
               or not 0 < r['lowerMicros'] < r['referenceMicros'] < r['upperMicros']
               for r in selected.values()):
            raise ValueError('invalid or future band timeline publication')
        timeline[at] = {s: tuple(selected[e][k] for k in ('referenceMicros', 'lowerMicros', 'upperMicros'))
                        for s, _, e, _ in roster['clubs'] + roster['athletes']}
        previous_event = at
    transitions = []
    states = {}
    for s in bases:
        rng = rngs[s]
        states[s] = dict(until=start, mode='RANGE', fair=math.log(values[s]), pressure=0.,
                         variance=1., shock=0., pullback=0, personality=rng.uniform(.72, 1.35))
    current, ranges = all_values(values, bands, edges)
    points = {s: [p] for s, p in current.items()}
    rows = {s: [] for s in current}
    fixture_times = {s: sorted((stamp(f['kickoff']), f['matchId']) for f in context['fixtures']
                              if teams[s] in (f['homeTeamId'], f['awayTeamId'])) for s in bases}
    # Hourly lookup avoids scanning all schedules for every five-minute sample.
    activity = {}
    for at in range((start // 3600) * 3600, end, 3600):
        for s in bases:
            near = min((abs(at - k) for k, _ in fixture_times[s]), default=10**9)
            activity[s, at] = 1 + .8 * math.exp(-near / 7200)
    bar_start = start
    for at in range(start + STEP, end + STEP, STEP):
        common = shared_rng.gauss(0, 1)
        club_factor = {t: shared_rng.gauss(0, 1) for t in sorted(set(teams.values()))}
        hour_start = ((at - 1) // 3600) * 3600
        if at == start + STEP or (at - STEP) % 3600 == 0:
            form = {s: sentiment(context, s, at - STEP) for s in bases}
        hour = datetime.fromtimestamp(at, WAT).hour
        session = .72 if 2 <= hour <= 7 else 1.22 if 16 <= hour <= 23 else 1.
        for s in bases:
            st, rng = states[s], rngs[s]
            price = math.log(values[s])
            if at >= st['until']:
                previous = st['mode']
                # Compression sometimes releases into expansion; no fixed cycle.
                mode = ('EXPANSION' if previous == 'COMPRESSION' and rng.random() < .65
                        else rng.choices(MODES, weights=(30, 17, 19, 19, 15))[0])
                direction = 1 if mode == 'TREND_UP' else -1 if mode == 'TREND_DOWN' else rng.choice((-1, 1))
                st.update(until=at + rng.randint(3, 30) * 3600, mode=mode,
                          fair=price, pressure=direction * rng.uniform(.000035, .00013))
            mode = st['mode']
            scale = {'RANGE': .85, 'COMPRESSION': .35, 'TREND_UP': 1.,
                     'TREND_DOWN': 1.1, 'EXPANSION': 1.9}[mode]
            # Student-t innovations produce occasional outsized moves. Squared
            # shocks feed subsequent volatility, without smoothing price changes.
            tail = rng.gauss(0, 1) / math.sqrt(rng.gammavariate(2.5, .4)) * math.sqrt(.6)
            innovation = .93 * tail + .28 * club_factor[teams[s]] + .12 * common
            sigma = .00056 * st['personality'] * scale * session
            sigma *= math.sqrt(st['variance']) * activity[s, hour_start]
            shock = sigma * innovation
            st['variance'] = clip(.06 + .84 * st['variance'] + .10 * min(innovation**2, 30), .25, 7.)
            if rng.random() < .0025:
                st['shock'] += rng.choice((-1, 1)) * rng.uniform(.0012, .0045)
                st['variance'] = min(7., st['variance'] + 1.5)
            st['shock'] *= .72
            if mode.startswith('TREND') and rng.random() < .009:
                st['pullback'] = at + rng.randint(3, 18) * STEP
            pressure = st['pressure'] * (-1.5 if at < st['pullback'] else 1.)
            if mode in ('RANGE', 'COMPRESSION'):
                drift = .018 * (st['fair'] - price)
            else:
                drift = pressure + .0015 * (st['fair'] - price)
            # Only results available by this sample contribute to sentiment.
            drift += form[s] * .000018
            r, low, high = bands[s]
            lower, upper = math.log(low), math.log(high)
            distance = min(price - lower, upper - price)
            # Liquidity near a hard limit progressively resists further pressure.
            edge = clip((.003 - distance) / .003, 0, 1)
            drift += edge * .00025 * (1 if price < math.log(r) else -1)
            proposal = price + drift + shock + st['shock']
            # Reflect overshoots rather than clipping many candles to one price.
            while proposal < lower or proposal > upper:
                proposal = 2 * lower - proposal if proposal < lower else 2 * upper - proposal
            values[s] = round(math.exp(clip(proposal, lower + 1e-7, upper - 1e-7)))
        values = project(values, bands, edges)
        current, ranges = all_values(values, bands, edges)
        for s, p in current.items():
            points[s].append(p)
        if at % 3600 == 0:
            for s, ps in points.items():
                r, low, high = ranges[s]
                legs = s.split('/')
                upcoming = [(k, mid) for leg in legs for k, mid in fixture_times[leg] if k >= bar_start]
                match = min(upcoming)[1] if upcoming else ''
                mode = states[s]['mode'] if s in states else 'RELATIVE_VALUE'
                rows[s].append(dict(zip(FIELDS, [utc(bar_start), utc(at), ps[0], max(ps), min(ps),
                                               ps[-1], r, low, high, match, mode])))
            if at in timeline:
                previous_values = dict(current)
                bands = timeline[at]
                # Preserve the market price wherever the new constraints permit
                # it. Never reset every instrument to its new reference.
                values = {s: clip(values[s], bands[s][1] + 32, bands[s][2] - 32) for s in bases}
                values = project(values, bands, edges)
                current, ranges = all_values(values, bands, edges)
                for s in bases:
                    states[s]['fair'] = math.log(values[s])
                    states[s]['shock'] = 0.
                for s, price in current.items():
                    if price != previous_values[s]:
                        transitions.append(dict(symbol=s, at=utc(at), previousCloseMicros=previous_values[s],
                                                nextOpenMicros=price, reason='published band constraints'))
            points = {s: [p] for s, p in current.items()}
            bar_start = at
    basis = {**basis, 'constraintTransitions': transitions}
    return rows, roster, context, basis, start, end


def correlation(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    den = math.sqrt(sum((x - ma)**2 for x in a) * sum((y - mb)**2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den if den else 0.


def diagnostics(rows):
    result = {}
    for s, candles in rows.items():
        returns = [math.log(r['closeMicros'] / r['openMicros']) for r in candles]
        absolute = [abs(r) for r in returns]
        wickless = sum(r['highMicros'] == max(r['openMicros'], r['closeMicros']) and
                       r['lowMicros'] == min(r['openMicros'], r['closeMicros']) for r in candles)
        run = longest = 1
        for a, b in zip(returns, returns[1:]):
            run = run + 1 if a * b > 0 else 1
            longest = max(longest, run)
        result[s] = dict(medianAbsoluteHourlyMovePct=statistics.median(absolute) * 100,
                         returnLag1=correlation(returns[:-1], returns[1:]),
                         absoluteReturnLag1=correlation(absolute[:-1], absolute[1:]),
                         wicklessPct=100 * wickless / len(candles), longestDirectionalRun=longest)
    return result


def export(directory=DEFAULT, end_override=None):
    rows, roster, context, basis, start, end = simulate(directory / 'inputs', end_override)
    volume_context = {'fixtures': context['fixtures'], 'players': {}}
    for s, _, entity, _ in roster['athletes']:
        volume_context['players'][entity] = {'memberships': [
            {'teamId': context['teams'][s], 'from': utc(start), 'to': None}]}
    summary = add_volume(rows, roster, volume_context, start, stamp(context['capturedAt']), end)
    instruments = []
    for s, candles in rows.items():
        p = directory / 'admin' / (s.replace('/', '-') + '.csv')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS + ['volumeUsd'], lineterminator='\n')
            writer.writeheader()
            writer.writerows(candles)
        instruments.append(dict(symbol=s, path=str(p.relative_to(directory)), candles=len(candles), sha256=digest(p)))
    report = diagnostics(rows)
    write_json(directory / 'diagnostics.json', report)
    p = directory / 'weekly-volume.csv'
    with p.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(summary)
    manifest = dict(schema='blackbook.market-ohlcv.release.v1', modelVersion=VERSION,
                    dataOrigin='synthetic scenario; no executions', priceScale=1000000,
                    **{'from': utc(start), 'to': utc(end)}, generatedAt=context['capturedAt'],
                    referenceSourceCommit=basis['sourceCommit'], referenceSourceStatus=basis['sourceStatus'],
                    verifiedReferenceAsOf=basis['latestAsOf'],
                    futureReferencePolicy='published timeline through November 4, then frozen scenario constraints',
                    constraintTransitions=basis['constraintTransitions'],
                    continuityCheckpointSha256=digest(directory / 'inputs/continuity.json'),
                    volumeUnit='USD', volumeScope='38 markets, each counted once',
                    totalCandles=sum(len(c) for c in rows.values()), adminInstruments=instruments,
                    weeklyVolume=summary, weeklyVolumeSha256=digest(p),
                    diagnosticsSha256=digest(directory / 'diagnostics.json'),
                    inputSha256={p.name: digest(p) for p in sorted((directory / 'inputs').glob('*.json'))})
    write_json(directory / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT)
    args = parser.parse_args()
    result = export(args.directory)
    print(json.dumps({k: result[k] for k in ('from', 'to', 'totalCandles')}))
