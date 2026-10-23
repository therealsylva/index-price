#!/usr/bin/env python3
"""Build fixture-conditioned market paths on immutable sporting references/bands."""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from publish import band, load_band_policy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'market-history/2026-10-23'
STEP = 300
HOUR = 3600
SCALE = 1_000_000_000  # 1,000 index points, expressed in micro-units
FIELDS = ['openTime', 'closeTime', 'openMicros', 'highMicros', 'lowMicros',
          'closeMicros', 'referenceMicros', 'lowerMicros', 'upperMicros',
          'nextMatchId', 'regime']


def stamp(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset().total_seconds() != 0:
        raise ValueError('UTC timestamp required')
    return int(d.timestamp())


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')


def clip(value, lower, upper):
    return min(upper, max(lower, value))


def seed(value):
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], 'big')


def pair_band(x, y):
    """Inherit the wider percentage on each side; do not compound extremes."""
    rx, lx, ux = x
    ry, ly, uy = y
    ln, ld = (lx, rx) if lx * ry <= ly * rx else (ly, ry)
    un, ud = (ux, rx) if ux * ry >= uy * rx else (uy, ry)
    return (SCALE * rx // ry, SCALE * rx * ln // (ry * ld),
            (SCALE * rx * un + ry * ud - 1) // (ry * ud))


def project(prices, bands, edges, locked=()):
    """Jointly fit leg premiums so every exact ratio obeys its inherited band."""
    q = {s: math.log(prices[s] / bands[s][0]) for s in prices}
    bounds = {s: (math.log((b[1] + 32) / b[0]), math.log((b[2] - 32) / b[0]))
              for s, b in bands.items()}
    locked = set(locked)
    for s in locked:
        q[s] = 0.0
    for _ in range(120):
        changed = False
        for x, y in edges:
            r, low, high = pair_band(bands[x], bands[y])
            # Use the exact unrounded reference ratio to avoid floor-rounding drift.
            exact_r = SCALE * bands[x][0] / bands[y][0]
            a, b = math.log((low + 64) / exact_r), math.log((high - 64) / exact_r)
            diff = q[x] - q[y]
            error = diff - clip(diff, a, b)
            if abs(error) < 1e-13:
                continue
            changed = True
            if x in locked and y in locked:
                raise ValueError('infeasible locked ratio')
            if x in locked:
                q[y] = clip(q[y] + error, *bounds[y])
            elif y in locked:
                q[x] = clip(q[x] - error, *bounds[x])
            else:
                q[x] = clip(q[x] - error / 2, *bounds[x])
                q[y] = clip(q[y] + error / 2, *bounds[y])
        if not changed:
            break
    values = {s: round(bands[s][0] * math.exp(v)) for s, v in q.items()}
    for s in locked:
        values[s] = bands[s][0]
    for s, v in values.items():
        if not bands[s][1] <= v <= bands[s][2]:
            raise ValueError(f'leg outside band: {s}')
    for x, y in edges:
        _, low, high = pair_band(bands[x], bands[y])
        if not low <= SCALE * values[x] // values[y] <= high:
            raise ValueError(f'pair outside band: {x}/{y}')
    return values


def read_shards(directory, prefix):
    return [r for path in sorted(directory.glob(prefix + '-*.json'))
            for r in json.loads(path.read_text())['rows']]


class Sources:
    def __init__(self, root=ROOT, inputs=DEFAULT / 'inputs'):
        self.root, self.inputs = Path(root), Path(inputs)
        self.roster = json.loads((self.inputs / 'instruments.json').read_text())
        self.context = json.loads((self.inputs / 'context.json').read_text())
        self.names = {s: (n, e, i) for s, n, e, i in self.roster['clubs'] + self.roster['athletes']}
        self.by_entity = {e: s for s, (_, e, _) in self.names.items()}
        self.club_symbols = {s for s, *_ in self.roster['clubs']}
        self.edges = self.roster['pairs']
        self.pairs = [x + '/' + y for x, y in self.edges]
        self.symbols = list(self.names) + self.pairs
        self.anchors = defaultdict(list)
        self.bands = {}
        self.references = {}
        self.events = defaultdict(dict)
        self.reconstructed = []
        self.checkpoints = []
        self.curves = defaultdict(list)
        self.source_files = [self.inputs / 'instruments.json', self.inputs / 'context.json',
                             self.inputs / 'archive-anchors.json', self.root / 'config/publication-v3.json']
        self._anchors()
        self._context()

    def _anchors(self):
        archive = json.loads((self.inputs / 'archive-anchors.json').read_text())
        by_id = {r['entity_id']: r for r in archive['rows']}
        # The sealed selected-entity archive has no sporting moves during Aug 1–16.
        # Refuse silently using a later state if that property changes.
        start = stamp('2026-08-01T00:00:00Z')
        if any(stamp(r['effective_at']) >= start for r in archive['rows']):
            raise ValueError('archive needs chronological replay rather than a baseline-only projection')
        reliability = {}
        for eid, row in by_id.items():
            s = self.by_entity[eid]
            self.bands[s] = (row['reference_micros'], row['lower_micros'], row['upper_micros'])
            self.references[eid] = row['reference_micros']
            reliability[eid] = row['personal_reliability_ppm']
        first_state = self.root / 'state/2026-08-26'
        # snapshot_reference is the August 17 starting reference, NOT the Aug 26 result.
        for row in read_shards(first_state, 'index'):
            eid = row['entity_id']
            if row['kind'] == 'CLUB':
                self.references.setdefault(eid, row['snapshot_reference_micros'])
        for eid, value in self.references.items():
            self.curves[eid].append((start, value))
        state_dates = sorted(p for p in (self.root / 'state').iterdir()
                             if p.is_dir() and p.name <= self.roster['referencePublication'])
        ledger = read_shards(state_dates[-1], 'movements')
        selected_events = defaultdict(list)
        for row in ledger:
            at = stamp(row['kickoff']) + 110 * 60
            if row['entity_id'] in self.by_entity:
                selected_events[row['entity_id']].append(row)
            if row['kind'] == 'CLUB':
                self.curves[row['entity_id']].append((at, row['next_reference_micros']))
        for curve in self.curves.values():
            curve.sort()
        policy = load_band_policy(self.root / 'config/publication-v3.json')
        effective = {e: 20 * r / max(1, 1_000_000 - r) for e, r in reliability.items()}
        prior_cut = stamp('2026-08-17T00:00:00Z')
        current_ref = dict(self.references)
        for directory in state_dates:
            manifest = directory / 'manifest.json'
            self.source_files.extend(sorted(directory.glob('*.json')))
            cut = stamp(json.loads(manifest.read_text())['asOf'])
            saved = {r['entity_id']: r for r in read_shards(directory, 'index')}
            public_dir = self.root / 'football' / directory.name
            self.source_files.extend(sorted(public_dir.glob('*.json')))
            public = {r['entityId']: r for r in read_shards(public_dir, 'snapshot')}
            for eid, symbol in self.by_entity.items():
                events = sorted((r for r in selected_events[eid]
                                 if prior_cut <= stamp(r['kickoff']) < cut),
                                key=lambda r: (r['kickoff'], r['match_id']))
                for event in events:
                    at = stamp(event['kickoff']) + 110 * 60
                    if at >= cut:
                        raise ValueError('checkpoint precedes modeled verification time')
                    if current_ref[eid] != event['previous_reference_micros']:
                        raise ValueError(f'broken reference chain: {symbol}')
                    exposure = 1.0
                    if symbol not in self.club_symbols:
                        appearances = self.context['players'][eid]['appearances']
                        found = [a for a in appearances if a['matchId'] == event['match_id']]
                        if len(found) != 1:
                            raise ValueError(f'missing exposure: {symbol}, {event["match_id"]}')
                        exposure = min(found[0]['minutes'] / 90, 1.0)
                    effective[eid] += exposure
                    density = round((1 - math.exp(-effective[eid] / 30)) * 1_000_000)
                    reference = event['next_reference_micros']
                    lo, hi = band(reference, density, event['profile'], event['kind'],
                                  event['published_log_return_ppm'], policy)
                    self.events[at][symbol] = (reference, lo, hi)
                    self.reconstructed.append({'symbol': symbol, 'matchId': event['match_id'],
                                               'ledgerKickoff': event['kickoff'], 'effectiveAt': utc(at),
                                               'referenceMicros': reference, 'lowerMicros': lo,
                                               'upperMicros': hi, 'densityPpm': density})
                    current_ref[eid] = reference
                saved_row = saved[eid]
                density = round((1 - math.exp(-effective[eid] / 30)) * 1_000_000)
                if events and density != saved_row['density_ppm']:
                    raise ValueError(f'density does not reproduce saved checkpoint: {symbol}, {directory.name}')
                if current_ref[eid] != saved_row['reference_micros']:
                    raise ValueError(f'reference does not reproduce saved checkpoint: {symbol}')
                row = public[eid]
                value = (row['referenceMicros'], row['lowerMicros'], row['upperMicros'])
                self.events[cut][symbol] = value
                self.checkpoints.append({'symbol': symbol, 'effectiveAt': utc(cut),
                                         'referenceMicros': value[0], 'lowerMicros': value[1],
                                         'upperMicros': value[2], 'priceHash': row['priceHash']})
                rel = saved_row['personal_reliability_ppm']
                effective[eid] = 20 * rel / max(1, 1_000_000 - rel)
            prior_cut = cut
        for rows in self.curves.values():
            rows.sort()
        for symbol, b in self.bands.items():
            self.anchors[symbol].append((start, b))
        for at, entries in sorted(self.events.items()):
            for symbol, b in entries.items():
                self.anchors[symbol].append((at, b))

    def _context(self):
        self.fixtures = [{**f, 'at': stamp(f['kickoff'])} for f in self.context['fixtures']]
        self.fixture_by_id = {f['matchId']: f for f in self.fixtures}
        self.by_team = defaultdict(list)
        for f in self.fixtures:
            self.by_team[f['homeTeamId']].append(f)
            self.by_team[f['awayTeamId']].append(f)
        self.results = []
        self.result_by_id = {}
        for r in self.context['results']:
            r = {**r, 'available': stamp(r['availableAt'])}
            self.results.append(r)
            self.result_by_id[r['matchId']] = r

    def reference(self, eid, at):
        curve = self.curves.get(eid, [])
        i = bisect.bisect_right(curve, (at, float('inf'))) - 1
        return curve[i][1] if i >= 0 else 1_000_000_000

    def team(self, symbol, at):
        _, eid, provider_id = self.names[symbol]
        if symbol in self.club_symbols:
            return provider_id
        spans = self.context['players'][eid]['memberships']
        # Resolve membership at NOW, not at the future kickoff. This prevents
        # a later transfer from changing a player's earlier speculation.
        active = [r for r in spans if stamp(r['from']) <= at
                  and (r['to'] is None or at < stamp(r['to']))]
        if not active:
            raise ValueError(f'no team membership at {utc(at)}: {symbol}')
        return max(active, key=lambda r: r['from'])['teamId']

    def context_at(self, symbol, at):
        team = self.team(symbol, at)
        fixtures = self.by_team[team]
        next_game = next((f for f in fixtures if f['at'] + 110 * 60 > at), None)
        completed = [r for r in self.results if r['available'] <= at
                     and at - r['available'] < 30 * 86400
                     and team in (self.fixture_by_id[r['matchId']]['homeTeamId'],
                                  self.fixture_by_id[r['matchId']]['awayTeamId'])]
        weights, form = 0.0, 0.0
        for r in completed:
            f = self.fixture_by_id[r['matchId']]
            margin = r['homeGoals'] - r['awayGoals']
            if f['awayTeamId'] == team:
                margin = -margin
            weight = math.exp(-(at - r['available']) / (8 * 86400))
            form += weight * math.tanh(margin / 2)
            weights += weight
        form /= max(weights, 1)
        individual = 0.0
        participation = 1.0
        if symbol not in self.club_symbols:
            player = self.context['players'][self.names[symbol][1]]
            past = [r for r in player['appearances'] if stamp(r['kickoff']) + 110 * 60 <= at]
            played = [r for r in past if r['minutes'] > 0 and r['rating'] > 0][-5:]
            if played:
                individual = sum(clip((r['rating'] - 7) / 2, -1, 1) for r in played) / len(played)
            if past:
                participation = sum(min(1, r['minutes'] / 90) for r in past[-5:]) / len(past[-5:])
            else:
                participation = .8
            injury = player.get('injury')
            if injury and stamp(injury['availableAt']) <= at:
                cleared = any(stamp(r['kickoff']) > stamp(injury['availableAt']) and r['minutes'] > 0 for r in past)
                if not cleared:
                    participation *= .2
        if not next_game:
            return {'match': '', 'anticipation': 0.0, 'expectation': 0.0, 'form': form,
                    'individual': individual, 'participation': participation, 'phase': 0.0,
                    'importance': 1.0, 'rivalry': False, 'live': False}
        f = next_game
        home = f['homeTeamId'] == team
        opponent = f['awayTeamId'] if home else f['homeTeamId']
        entities = self.context['teams']
        own = entities[str(team)]['entityId']
        opp = entities[str(opponent)]['entityId']
        expectation = math.tanh(.55 * math.log(self.reference(own, at) / self.reference(opp, at))
                                + (.15 if home else -.15))
        rivals = {frozenset((self.names[x][2], self.names[y][2])) for x, y in self.edges
                  if x in self.club_symbols}
        rivalry = frozenset((team, opponent)) in rivals
        importance = 1.45 if 'Champions League' in f['competition'] else 1.0
        if rivalry:
            importance *= 1.5
        hours = (f['at'] - at) / HOUR
        live = hours <= 0
        anticipation = math.exp(-max(0, hours) / 48)
        # This phase uses only the scheduled kickoff, never the match result.
        phase = clip(1 - max(0, hours) / (7 * 24), 0, 1)
        return {'match': f['matchId'], 'anticipation': anticipation, 'expectation': expectation,
                'form': form, 'individual': individual, 'participation': participation,
                'phase': phase, 'importance': importance, 'rivalry': rivalry, 'live': live}


def shape(kind, phase):
    knots = {
        'BULL_FLAG': [(-.5), .1, .65, .39, .46, .30, .85],
        'BEAR_FLAG': [.5, -.1, -.65, -.39, -.46, -.30, -.85],
        'DOUBLE_BOTTOM': [.25, -.60, .12, -.57, .10, .35, .72],
        'DOUBLE_TOP': [-.25, .60, -.12, .57, -.10, -.35, -.72],
        'COMPRESSION': [-.45, .45, -.30, .30, -.15, .15, .02],
        'RANGE': [-.30, .36, -.32, .34, -.30, .36, -.12],
    }[kind]
    x = clip(phase, 0, 1) * (len(knots) - 1)
    i = min(len(knots) - 2, int(x))
    f = x - i
    f = f * f * (3 - 2 * f)
    return knots[i] * (1 - f) + knots[i + 1] * f


def regime(c):
    belief = .55 * c['expectation'] + .30 * c['form'] + .15 * c['individual']
    if c['form'] < -.12 and belief > .03:
        return 'DOUBLE_BOTTOM'
    if c['form'] > .12 and belief < -.03:
        return 'DOUBLE_TOP'
    if belief > .17:
        return 'BULL_FLAG'
    if belief < -.17:
        return 'BEAR_FLAG'
    return 'COMPRESSION' if c['rivalry'] or c['importance'] > 1 else 'RANGE'


def all_values(values, bands, edges):
    out, ranges = dict(values), dict(bands)
    for x, y in edges:
        s = x + '/' + y
        out[s] = SCALE * values[x] // values[y]
        ranges[s] = pair_band(bands[x], bands[y])
    return out, ranges


def generate(sources, start, end):
    if start != stamp('2026-08-01T00:00:00Z') or end <= start:
        raise ValueError('history starts on August 1; end must be later')
    if end > stamp(sources.context['capturedAt']):
        raise ValueError('end exceeds context capture')
    bands = dict(sources.bands)
    values = {s: b[0] for s, b in bands.items()}
    rngs = {s: random.Random(seed('fixture-history-v1|' + s)) for s in sources.names}
    z, velocity, noise = ({s: 0.0 for s in sources.names} for _ in range(3))
    regime_state = {}
    for s in sources.names:
        c = sources.context_at(s, start)
        regime_state[s] = (c['match'], regime(c))
    # The shared grid preserves exact pair OHLC sampling and splits every bar at
    # every band change. There is no candle spanning two incompatible bands.
    times = set(range(start, end, STEP)) | {end}
    times |= {t for t in sources.events if start < t < end}
    for f in sources.fixtures:
        for t in [f['at'], f['at'] + 110 * 60]:
            if start < t < end:
                times.add(t)
    times = sorted(times)
    rows = {s: [] for s in sources.symbols}
    audit = {'sampleCount': 0, 'pairChecks': 0, 'bandChecks': 0, 'recalibrations': 0}
    current, ranges = all_values(values, bands, sources.edges)
    bar_start, bar = start, {s: [p] for s, p in current.items()}
    bar_bands = dict(ranges)
    bar_context = {s: sources.context_at(s, start)['match'] for s in sources.names}
    bar_regimes = {s: regime_state[s][1] for s in sources.names}
    previous_at = start
    for at in times[1:]:
        dt = (at - previous_at) / STEP
        shared = math.sin((at - start) / (HOUR * 9)) * .017 + math.sin((at - start) / (HOUR * 37)) * .025
        for s in sources.names:
            c = sources.context_at(s, at)
            if c['match'] != regime_state[s][0]:
                regime_state[s] = (c['match'], regime(c))
            kind = regime_state[s][1]
            pattern = shape(kind, c['phase'])
            conviction = .50 * c['expectation'] * c['anticipation'] * c['participation']
            conviction += .22 * c['form'] + .14 * c['individual']
            # Same-club participants share a factor; each entity retains its own
            # persistent innovations and reaction speed.
            club_factor = math.sin(at / (HOUR * 5) + (seed(str(sources.team(s, at))) % 1000)) * .026
            target = clip(conviction + .32 * pattern + shared + club_factor, -.83, .83)
            activity = (1 + .55 * c['anticipation'] + (.5 if c['live'] else 0)) * min(1.8, c['importance'])
            decay = .91 ** dt
            noise[s] = decay * noise[s] + rngs[s].gauss(0, .012) * math.sqrt(dt) * activity
            desired = target + noise[s]
            velocity[s] = (.82 ** dt) * velocity[s] + (1 - .82 ** dt) * (desired - z[s]) * .12
            z[s] = clip(z[s] + velocity[s] * dt, -.92, .92)
            r, lo, hi = bands[s]
            values[s] = round(r + z[s] * (hi - r if z[s] >= 0 else r - lo))
        values = project(values, bands, sources.edges)
        current, ranges = all_values(values, bands, sources.edges)
        for s, p in current.items():
            if not ranges[s][1] <= p <= ranges[s][2]:
                raise ValueError(f'sample outside band: {s}, {utc(at)}')
            bar[s].append(p)
        audit['sampleCount'] += 1
        audit['pairChecks'] += len(sources.edges)
        audit['bandChecks'] += len(current)
        # Only an actual change of reference/bounds triggers a reset. Repeated
        # unchanged publication rows do not introduce an artificial price jump.
        changes = {s: b for s, b in sources.events.get(at, {}).items() if b != bands[s]}
        boundary = at % HOUR == 0 or bool(changes) or at == end
        if boundary:
            for s in sources.symbols:
                points = bar[s]
                r, lo, hi = bar_bands[s]
                if s in sources.names:
                    match, kind = bar_context[s], bar_regimes[s]
                else:
                    x, y = s.split('/')
                    match = '|'.join(filter(None, [bar_context[x], bar_context[y]]))
                    kind = 'RELATIVE_VALUE'
                rows[s].append(dict(zip(FIELDS, [utc(bar_start), utc(at), points[0], max(points), min(points), points[-1],
                                                 r, lo, hi, match, kind])))
            if changes:
                bands.update(changes)
                for s in changes:
                    values[s] = bands[s][0]
                    z[s] = velocity[s] = noise[s] = 0.0
                values = project(values, bands, sources.edges, changes)
                audit['recalibrations'] += len(changes)
            current, ranges = all_values(values, bands, sources.edges)
            bar_start = at
            bar = {s: [p] for s, p in current.items()}
            bar_bands = dict(ranges)
            bar_context = {s: sources.context_at(s, at)['match'] for s in sources.names}
            bar_regimes = {s: regime_state[s][1] for s in sources.names}
        # Keep the process state aligned with the constrained leg prices.
        for s in sources.names:
            r, lo, hi = bands[s]
            z[s] = (values[s] - r) / (hi - r if values[s] >= r else r - lo)
        previous_at = at
    return rows, audit


def write_release(sources, output, start, end):
    rows, audit = generate(sources, start, end)
    instruments = []
    for symbol, candles in rows.items():
        filename = symbol.replace('/', '-') + '.csv'
        path = output / 'prices' / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator='\n')
            w.writeheader()
            w.writerows(candles)
        n, e, _ = sources.names.get(symbol, (symbol, 'pair:' + symbol.lower().replace('/', '-'), None))
        instruments.append({'symbol': symbol, 'name': n, 'entityId': e,
                            'kind': 'PAIR' if '/' in symbol else 'CLUB' if symbol in sources.club_symbols else 'PLAYER',
                            'path': 'prices/' + filename, 'candles': len(candles), 'sha256': digest(path)})
    anchors = {'schema': 'blackbook.market-history.anchors.v1',
               'initial': {s: {'referenceMicros': b[0], 'lowerMicros': b[1], 'upperMicros': b[2]}
                           for s, b in sources.bands.items()},
               'reconstructedEvents': sorted(sources.reconstructed, key=lambda r: (r['effectiveAt'], r['symbol'])),
               'publishedCheckpoints': sources.checkpoints}
    write_json(output / 'anchors.json', anchors)
    bound = {str(p.relative_to(sources.root)): digest(p) for p in sources.source_files}
    write_json(output / 'manifest.json', {
        'schema': 'blackbook.market-history.release.v1', 'modelVersion': 'fixture-conditioned-v1',
        'from': utc(start), 'to': utc(end), 'priceScale': 1_000_000,
        'baseIntervalSeconds': HOUR, 'pathSampleSeconds': STEP,
        'barBoundaryPolicy': 'hourly_split_at_band_changes', 'pairScaleMicros': SCALE,
        'instruments': instruments, 'anchorsSha256': digest(output / 'anchors.json'),
        'sourceFiles': bound, 'validation': audit,
    })
    return rows, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--inputs', type=Path, default=DEFAULT / 'inputs')
    parser.add_argument('--from', dest='start', default='2026-08-01T00:00:00Z')
    parser.add_argument('--to', dest='end', default='2026-10-23T16:45:00Z')
    args = parser.parse_args()
    _, audit = write_release(Sources(inputs=args.inputs), args.output, stamp(args.start), stamp(args.end))
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
