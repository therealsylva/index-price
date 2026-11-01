"""The new release preserves the imported prefix and follows verified updates."""
import copy
import csv
import json

import test_market_history
from market_history import ROOT, DEFAULT, generate, stamp


class ExtendedMarketHistoryTests(test_market_history.MarketHistoryTests):
    release = ROOT / 'market-history/2026-11-01'
    checkpoint_count = 210

    def test_imported_prefix_is_byte_identical_and_joins_without_price_jump(self):
        old = json.loads((DEFAULT / 'manifest.json').read_text())
        new = json.loads((self.release / 'manifest.json').read_text())
        self.assertEqual(old['from'], new['from'])
        self.assertEqual(new['to'], '2026-11-01T08:30:00Z')
        for item in new['instruments']:
            path = item['path']
            prefix = (DEFAULT / path).read_bytes()
            self.assertTrue((self.release / path).read_bytes().startswith(prefix), path)
            with (self.release / path).open() as f:
                rows = list(csv.DictReader(f))
            join = next(i for i, r in enumerate(rows) if r['openTime'] == old['to'])
            self.assertEqual(rows[join-1]['closeMicros'], rows[join]['openMicros'], path)

    def test_extension_replay_and_future_results_do_not_change_prior_prices(self):
        s = self.sources
        start = stamp('2026-10-23T16:45:00Z')
        initial = {}
        for symbol in s.names:
            with (DEFAULT / 'prices' / (symbol + '.csv')).open() as f:
                initial[symbol] = int(list(csv.DictReader(f))[-1]['closeMicros'])
        short, _ = generate(s, start, start+4500, initial)
        longer, _ = generate(s, start, start+8100, initial)
        altered = copy.deepcopy(s)
        for result in altered.results:
            if result['available'] > start+8100:
                result['homeGoals'], result['awayGoals'] = 99, 0
        future_changed, _ = generate(altered, start, start+8100, initial)
        for symbol in s.symbols:
            self.assertEqual(short[symbol], longer[symbol][:len(short[symbol])])
            self.assertEqual(longer[symbol], future_changed[symbol])
