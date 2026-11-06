import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from continuous_market_scenario import DEFAULT, checked_continuity, export, sentiment
from market_history import pair_band, stamp


class ContinuousScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((DEFAULT / 'manifest.json').read_text())
        cls.basis = json.loads((DEFAULT / 'inputs/basis.json').read_text())
        cls.checkpoint = json.loads((DEFAULT / 'inputs/continuity.json').read_text())
        cls.rows = {}
        for item in cls.manifest['adminInstruments']:
            with (DEFAULT / item['path']).open() as f:
                cls.rows[item['symbol']] = list(csv.DictReader(f))

    def test_join_to_existing_history_and_no_november_five_reset(self):
        self.assertEqual(len(self.rows), 38)
        self.assertEqual(self.manifest['totalCandles'], 54378)
        self.assertEqual(self.manifest['from'], '2026-11-01T08:30:00Z')
        self.assertEqual(self.manifest['to'], '2026-12-30T23:00:00Z')
        for symbol, rows in self.rows.items():
            self.assertEqual(len(rows), 1431)
            expected = int(self.checkpoint['rows'][symbol]['closeMicros'])
            # The old inverse alias rounds twice; the new direct ratio floors once.
            tolerance = 1 if symbol == 'MUN/MCI' else 0
            self.assertLessEqual(abs(int(rows[0]['openMicros']) - expected), tolerance)
            self.assertEqual(rows[0]['openTime'], self.checkpoint['at'])
            self.assertEqual(rows[-1]['closeTime'], self.manifest['to'])
            for previous, current in zip(rows, rows[1:]):
                self.assertEqual(previous['closeTime'], current['openTime'])
                if current['openTime'] != '2026-11-04T00:00:00Z':
                    self.assertEqual(previous['closeMicros'], current['openMicros'])

    def test_correct_published_band_timeline_and_ohlc(self):
        roster = json.loads((DEFAULT / 'inputs/instruments.json').read_text())
        entities = {s: e for s, _, e, _ in roster['clubs'] + roster['athletes']}
        initial = {r['entityId']: r for r in self.basis['rows']}
        latest = {r['entityId']: r for r in self.basis['bandTimeline'][0]['rows']}
        fields = ('referenceMicros', 'lowerMicros', 'upperMicros')
        for symbol, rows in self.rows.items():
            for row in rows:
                source = initial if row['openTime'] < '2026-11-04T00:00:00Z' else latest
                if symbol in entities:
                    expected = tuple(source[entities[symbol]][k] for k in fields)
                else:
                    x, y = symbol.split('/')
                    expected = pair_band(tuple(source[entities[x]][k] for k in fields),
                                         tuple(source[entities[y]][k] for k in fields))
                self.assertEqual(tuple(int(row[k]) for k in fields), expected)
                o, h, low, c = (int(row[k]) for k in ('openMicros', 'highMicros', 'lowMicros', 'closeMicros'))
                self.assertTrue(expected[1] <= low <= min(o, c) <= max(o, c) <= h <= expected[2])
                self.assertTrue(0 < stamp(row['closeTime']) - stamp(row['openTime']) <= 3600)
            if '/' in symbol:
                x, y = symbol.split('/')
                for a, b, row in zip(self.rows[x], self.rows[y], rows):
                    for field in ('openMicros', 'closeMicros'):
                        self.assertEqual(int(row[field]), 10**9 * int(a[field]) // int(b[field]))

    def test_only_audited_constraint_transitions_break_price_continuity(self):
        actual = []
        for symbol, rows in self.rows.items():
            for previous, current in zip(rows, rows[1:]):
                if previous['closeMicros'] != current['openMicros']:
                    actual.append((symbol, current['openTime'], int(previous['closeMicros']), int(current['openMicros'])))
        audited = [(r['symbol'], r['at'], r['previousCloseMicros'], r['nextOpenMicros'])
                   for r in self.manifest['constraintTransitions']]
        self.assertEqual(sorted(actual), sorted(audited))
        self.assertTrue(all(r[1] == '2026-11-04T00:00:00Z' for r in actual))

    def test_replay_hashes_and_volume(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copytree(DEFAULT / 'inputs', target / 'inputs')
            replay = export(target)
            self.assertEqual(replay, self.manifest)
            for item in replay['adminInstruments']:
                self.assertEqual((target / item['path']).read_bytes(), (DEFAULT / item['path']).read_bytes())
        from project_market_history import monday
        totals = {}
        for rows in self.rows.values():
            for row in rows:
                week = monday(stamp(row['openTime']))
                totals[week] = totals.get(week, Decimal(0)) + Decimal(row['volumeUsd'])
        for week in self.manifest['weeklyVolume']:
            self.assertEqual(totals[monday(stamp(week['coverageFrom']))], Decimal(week['volumeUsd']))
        for item in self.manifest['adminInstruments']:
            self.assertEqual(hashlib.sha256((DEFAULT / item['path']).read_bytes()).hexdigest(), item['sha256'])

    def test_checkpoint_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copytree(DEFAULT / 'inputs', target, dirs_exist_ok=True)
            path = target / 'continuity.json'
            checkpoint = json.loads(path.read_text())
            checkpoint['rows']['RMD']['closeMicros'] = str(int(checkpoint['rows']['RMD']['closeMicros']) + 1)
            path.write_text(json.dumps(checkpoint))
            roster = json.loads((target / 'instruments.json').read_text())
            with self.assertRaisesRegex(ValueError, 'checkpoint row mismatch'):
                checked_continuity(target, self.basis, roster)

    def test_results_do_not_influence_price_before_availability(self):
        at = stamp('2026-11-04T00:00:00Z')
        context = {'recentMatches': {'X': [{'availableAt': '2026-11-04T00:00:00Z', 'goalDifference': 3}]}}
        self.assertEqual(sentiment(context, 'X', at - 1), 0.)
        self.assertEqual(sentiment(context, 'X', at), 1.)


if __name__ == '__main__':
    unittest.main()
