# Synthetic OHLCV scenario, November 1–December 30

Generate from the checksum-bound November 1 release, preserving its original
88,388 OHLC/reference/band records and adding synthetic USD traded-notional volume.
All 38 instruments extend to the end of December 30 in Africa/Lagos, exclusive
UTC cutoff `2026-12-30T23:00:00Z`. Output contains 142,766 candles.

```bash
python3 tools/project_market_history.py \
  --output /opt/blackbook/scenarios/2026-12-30 \
  --generated-at 2026-11-01T19:00:00Z
python3 -m unittest discover -s tests -p 'test_project_market_history.py'
```

`prices/` preserves archive instrument identities. `admin/` maps MCI/MUN to the
live catalog's MUN/MCI using inverse OHLC and bounds. It contains 38 import-ready
files; do not count the inverse as an additional market. Columns append
`volumeUsd,dataSource` to the original eleven-column history schema. The backend
OHLCV migration/API change is required before importing these files.

Every historical full WAT week totals $5–15m across the entire exchange scenario.
Volume grows unevenly into December, remaining within the requested $10–50m
terminal range: the last complete week is $27,293,463.59, and the trailing seven
days ending December 30 total $31,516,558.57. Partial weeks are identified, with
actual totals and weekly-equivalent values in `weekly-volume.csv`.

These are synthetic chart scenarios, not executions or revenue. Unknown future
sporting references/bands are frozen at their last verified values. Real future
matches may change those constraints and require regenerating/reconciling the
scenario; future sporting updates are never written to the index publication.

The generator uses persistent momentum and mean reversion, synchronized base/pair
samples, WAT sessions, weekends, available fixture schedules, volatility-weighted
volume, popularity and occasional notional bursts. Every volume value is exact
integer cents; targets apply to the sum of all 38 markets, counted once.
