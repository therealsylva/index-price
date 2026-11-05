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
from market_history import pair_band, stamp
from market_structure_scenario import DEFAULT, export, inputs


class MarketStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((DEFAULT / 'manifest.json').read_text())
        cls.rows = {}
        for item in cls.manifest['adminInstruments']:
            with (DEFAULT / item['path']).open() as f:
                cls.rows[item['symbol']] = list(csv.DictReader(f))

    def test_complete_import_schema_continuity_bounds_and_hashes(self):
        m = self.manifest
        self.assertEqual(len(self.rows), 38)
        self.assertEqual(m['totalCandles'], 51072)
        self.assertEqual(m['from'], '2026-11-04T23:00:00Z')
        self.assertEqual(m['to'], '2026-12-30T23:00:00Z')
        for name, expected in m['inputSha256'].items():
            self.assertEqual(hashlib.sha256((DEFAULT / 'inputs' / name).read_bytes()).hexdigest(), expected)
        for item in m['adminInstruments']:
            self.assertEqual(hashlib.sha256((DEFAULT / item['path']).read_bytes()).hexdigest(), item['sha256'])
            rows = self.rows[item['symbol']]
            self.assertEqual(len(rows), 1344)
            self.assertEqual(rows[0]['openTime'], m['from'])
            self.assertEqual(rows[-1]['closeTime'], m['to'])
            for i, row in enumerate(rows):
                self.assertEqual(len(row), 12)
                o, h, low, c, ref, lower, upper = [int(row[k]) for k in
                    ('openMicros', 'highMicros', 'lowMicros', 'closeMicros', 'referenceMicros', 'lowerMicros', 'upperMicros')]
                self.assertTrue(lower <= low <= min(o, c) <= max(o, c) <= h <= upper)
                self.assertTrue(lower < ref < upper)
                self.assertEqual(stamp(row['closeTime']) - stamp(row['openTime']), 3600)
                self.assertGreater(Decimal(row['volumeUsd']), 0)
                if i:
                    self.assertEqual(rows[i-1]['closeMicros'], row['openMicros'])
                    self.assertEqual(rows[i-1]['closeTime'], row['openTime'])

    def test_exact_pair_prices_and_inherited_bands(self):
        for symbol, rows in self.rows.items():
            if '/' not in symbol:
                continue
            x, y = symbol.split('/')
            for a, b, pair in zip(self.rows[x], self.rows[y], rows):
                for field in ('openMicros', 'closeMicros'):
                    self.assertEqual(int(pair[field]), 10**9 * int(a[field]) // int(b[field]))
                fields = ('referenceMicros', 'lowerMicros', 'upperMicros')
                expected = pair_band(tuple(int(a[k]) for k in fields), tuple(int(b[k]) for k in fields))
                self.assertEqual(tuple(int(pair[k]) for k in fields), expected)
                # Shared-sample extrema must lie inside the outer bounds implied
                # by hourly constituent extrema, never fabricated independently.
                self.assertGreaterEqual(int(pair['lowMicros']), 10**9 * int(a['lowMicros']) // int(b['highMicros']))
                self.assertLessEqual(int(pair['highMicros']), 10**9 * int(a['highMicros']) // int(b['lowMicros']))

    def test_volume_accounting_and_nonmechanical_distribution(self):
        from project_market_history import monday
        totals = {}
        for candles in self.rows.values():
            for row in candles:
                w = monday(stamp(row['openTime']))
                totals[w] = totals.get(w, Decimal(0)) + Decimal(row['volumeUsd'])
        for week in self.manifest['weeklyVolume']:
            self.assertEqual(totals[monday(stamp(week['coverageFrom']))], Decimal(week['volumeUsd']))
        trailing = sum(Decimal(r['volumeUsd']) for candles in self.rows.values() for r in candles
                       if stamp(r['openTime']) >= stamp(self.manifest['to']) - 7 * 86400)
        self.assertTrue(Decimal(10_000_000) <= trailing <= Decimal(50_000_000))
        diagnostics = json.loads((DEFAULT / 'diagnostics.json').read_text())
        # Broad regression bounds distinguish stochastic candle paths from the
        # previous smoothed target follower without selecting a specific chart.
        for symbol, report in diagnostics.items():
            self.assertLess(abs(report['returnLag1']), .35, symbol)
            self.assertLess(report['wicklessPct'], 30, symbol)
            self.assertGreater(report['absoluteReturnLag1'], .05, symbol)
            self.assertGreater(report['medianAbsoluteHourlyMovePct'], .04, symbol)

    def test_replay_matches_every_checked_in_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copytree(DEFAULT / 'inputs', target / 'inputs')
            replay = export(target)
            self.assertEqual(replay, self.manifest)
            for item in replay['adminInstruments']:
                self.assertEqual((target / item['path']).read_bytes(), (DEFAULT / item['path']).read_bytes())

    def test_future_basis_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            shutil.copytree(DEFAULT / 'inputs', target / 'inputs')
            path = target / 'inputs/basis.json'
            basis = json.loads(path.read_text())
            basis['rows'][0]['asOf'] = '2026-11-06T00:00:00Z'
            path.write_text(json.dumps(basis))
            with self.assertRaisesRegex(ValueError, 'future sporting'):
                inputs(target / 'inputs')


if __name__ == '__main__':
    unittest.main()
