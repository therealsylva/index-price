"""Causal context, exact pair constraints, and checked-in release invariants."""
import copy
import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from market_history import DEFAULT, ROOT, SCALE, Sources, generate, pair_band, project, stamp


class MarketHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = Sources()

    def test_exact_launch_roster_and_checkpoint_replay(self):
        s = self.sources
        self.assertEqual(len(s.club_symbols), 15)
        self.assertEqual(len(s.names), 30)
        self.assertEqual(len(s.edges), 8)
        self.assertIn('ATM', s.names)
        self.assertNotIn(['RMD', 'LMY'], s.edges)
        self.assertEqual(len(s.checkpoints), 150)
        # Sources construction also verifies every reference chain and exact
        # saved density after replaying the recorded minutes for each batch.
        for row in s.checkpoints:
            self.assertLess(row['lowerMicros'], row['referenceMicros'])
            self.assertLess(row['referenceMicros'], row['upperMicros'])

    def test_result_and_appearance_are_not_visible_before_completion(self):
        s = copy.deepcopy(self.sources)
        at = stamp('2026-08-20T14:00:00Z')
        before = {symbol: s.context_at(symbol, at) for symbol in s.names}
        for row in s.results:
            if row['available'] > at:
                row['homeGoals'], row['awayGoals'] = 99, 0
        for player in s.context['players'].values():
            for row in player['appearances']:
                if stamp(row['kickoff']) + 110 * 60 > at:
                    row['rating'], row['minutes'] = 10, 90
        after = {symbol: s.context_at(symbol, at) for symbol in s.names}
        self.assertEqual(before, after)
        # A known result does change the contextual belief after its release.
        # Find a selected club fixture to exercise a direct post-result effect.
        event = next(r for r in s.results if s.fixture_by_id[r['matchId']]['homeTeamId'] == 8634)
        old = s.context_at('BAR', event['available'])
        event['homeGoals'], event['awayGoals'] = 0, 99
        self.assertNotEqual(old['form'], s.context_at('BAR', event['available'])['form'])

    def test_transfer_context_switches_at_effective_date(self):
        s = self.sources
        self.assertEqual(s.team('ROD', stamp('2026-08-17T23:59:59Z')), 8456)
        self.assertEqual(s.team('ROD', stamp('2026-08-18T00:00:00Z')), 8634)
        self.assertEqual(s.team('OSI', stamp('2026-08-01T00:00:00Z')), 8637)

    def test_joint_projection_keeps_exact_ratios_and_reference_resets(self):
        bands = {'A': (1_000_000_000, 970_000_000, 1_030_000_000),
                 'B': (2_000_000_000, 1_940_000_000, 2_060_000_000),
                 'C': (3_000_000_000, 2_910_000_000, 3_090_000_000)}
        edges = [('A', 'B'), ('A', 'C')]
        p = project({'A': 1_029_999_900, 'B': 1_940_000_100, 'C': 2_910_000_100}, bands, edges)
        for x, y in edges:
            _, lo, hi = pair_band(bands[x], bands[y])
            self.assertLessEqual(lo, SCALE * p[x] // p[y])
            self.assertLessEqual(SCALE * p[x] // p[y], hi)
        p = project(p, bands, edges, ['A'])
        self.assertEqual(p['A'], bands['A'][0])

    def test_generation_is_stable_when_requested_end_extends(self):
        start = stamp('2026-08-01T00:00:00Z')
        short, _ = generate(self.sources, start, start + 7200)
        longer, _ = generate(self.sources, start, start + 10800)
        for symbol in self.sources.symbols:
            self.assertEqual(short[symbol], longer[symbol][:2])
        # Schedule changes should actually affect price, not just a context tag.
        altered = copy.deepcopy(self.sources)
        for rows in altered.by_team.values():
            for f in rows:
                f['at'] += 6 * 86400
        different, _ = generate(altered, start, start + 7200)
        self.assertNotEqual(short['BAR'][-1]['closeMicros'], different['BAR'][-1]['closeMicros'])

    def test_release_hashes_full_coverage_ohlc_and_pair_endpoints(self):
        manifest = json.loads((DEFAULT / 'manifest.json').read_text())
        self.assertEqual(len(manifest['instruments']), 38)
        for name, checksum in manifest['sourceFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), checksum, name)
        self.assertEqual(hashlib.sha256((DEFAULT / 'anchors.json').read_bytes()).hexdigest(), manifest['anchorsSha256'])
        by_symbol = {}
        for instrument in manifest['instruments']:
            path = DEFAULT / instrument['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), instrument['sha256'])
            with path.open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), instrument['candles'])
            self.assertEqual(rows[0]['openTime'], manifest['from'])
            self.assertEqual(rows[-1]['closeTime'], manifest['to'])
            for i, row in enumerate(rows):
                self.assertLess(stamp(row['openTime']), stamp(row['closeTime']))
                self.assertLessEqual(stamp(row['closeTime']) - stamp(row['openTime']), 3600)
                if i:
                    self.assertEqual(rows[i-1]['closeTime'], row['openTime'])
                    if instrument['kind'] != 'PAIR' and any(rows[i-1][k] != row[k] for k in ['referenceMicros', 'lowerMicros', 'upperMicros']):
                        self.assertEqual(row['openMicros'], row['referenceMicros'])
                o, h, low, c, r, lo, hi = (int(row[k]) for k in ['openMicros', 'highMicros', 'lowMicros', 'closeMicros', 'referenceMicros', 'lowerMicros', 'upperMicros'])
                self.assertLess(lo, r)
                self.assertLess(r, hi)
                self.assertLessEqual(lo, low)
                self.assertLessEqual(low, min(o, c))
                self.assertLessEqual(max(o, c), h)
                self.assertLessEqual(h, hi)
            by_symbol[instrument['symbol']] = rows
        for x, y in self.sources.edges:
            for a, b, pair in zip(by_symbol[x], by_symbol[y], by_symbol[x+'/'+y], strict=True):
                self.assertEqual(a['openTime'], pair['openTime'])
                for key in ['openMicros', 'closeMicros']:
                    self.assertEqual(SCALE * int(a[key]) // int(b[key]), int(pair[key]))
                bp = pair_band(tuple(int(a[k]) for k in ['referenceMicros','lowerMicros','upperMicros']),
                               tuple(int(b[k]) for k in ['referenceMicros','lowerMicros','upperMicros']))
                self.assertEqual(bp, tuple(int(pair[k]) for k in ['referenceMicros','lowerMicros','upperMicros']))


if __name__ == '__main__':
    unittest.main()
