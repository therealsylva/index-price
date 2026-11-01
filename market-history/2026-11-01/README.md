# Market-price history through 1 November 2026

38 CSV files: 15 clubs, 15 players, 8 pairs. Full coverage is 1 August 2026
00:00 UTC to 1 November 2026 08:30 UTC (09:30 Nigeria time), 88,388 bars.
The first 79,686 bars, through 23 October 16:45 UTC, are byte-identical to the
previous imported release. The extension adds 8,702 bars; there is no price
jump at the join. Import this complete release, not just its extension.

These are synthetic market-price candles, not actual trades or volume. The
reference prices and asymmetric bands come from the verified sporting ledger
and exact saved publication checkpoints through the 31 October matches.
Intermediate reference changes use the existing kickoff-plus-110-minute
verification convention; actual final-whistle/ingestion times are unavailable.
No live-band transition is asserted without a recorded publication.

Refreshed schedules, results and selected-player appearances are bound in
`inputs/context.json`, with provider URL/checksum receipts. New results and
player statistics are visible only after modeled completion. The model uses
opponents, form, anticipation, momentum, pullbacks and mean reversion; it does
not interpolate toward future results. Pair prices are exact synchronized
constituent ratios and inherit the widest constituent band per side.

Reproduce offline from repository root:

```bash
python3 tools/market_history.py \
  --output /tmp/blackbook-history-20261101 \
  --inputs market-history/2026-11-01/inputs \
  --from 2026-10-23T16:45:00Z --to 2026-11-01T08:30:00Z \
  --prefix market-history/2026-10-23
npm test
```

The manifest commits every CSV, anchor and source file. This release replaces
the selected chart archive only; it creates no trades, positions or balances.
