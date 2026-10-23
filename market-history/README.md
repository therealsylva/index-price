# Fixture-conditioned market price history

The [23 October release](2026-10-23/manifest.json) contains a separate complete
price file for each approved launch instrument: **15 clubs, 15 athletes and 8
pairs**, from **1 August 2026 00:00 UTC through 23 October 2026 16:45 UTC**.
Atlético Madrid is included. The manifest enumerates every file, its exact
coverage, candle count, integer price scale and SHA-256 checksum.

## Read the files

`2026-10-23/prices/SYMBOL.csv` contains hourly OHLC bars. A bar is split whenever
any constituent's reference or bounds change, so some bars are shorter than an
hour. Every bar has an exclusive `closeTime`; the next bar begins at that time.
The final bar ends at the release cutoff. A single bar never straddles two band
regimes. Prices are integer micro-units: divide by **1,000,000** for display.
There are no fabricated trade IDs, fills, balances or volume fields.

| Field | Meaning |
| --- | --- |
| `openTime`, `closeTime` | UTC bar boundaries |
| `openMicros`, `highMicros`, `lowMicros`, `closeMicros` | Market-price OHLC sampled from the common five-minute path |
| `referenceMicros` | Sporting reference active throughout the bar |
| `lowerMicros`, `upperMicros` | Permitted price limits active throughout the bar |
| `nextMatchId` | Upcoming/in-progress fixture at bar open; pairs include both legs' context |
| `regime` | Context-selected market formation; pairs use `RELATIVE_VALUE` |

The generated market paths are produced by `tools/market_history.py`. The
canonical `football/`, `state/`, calculator and publication pointers are inputs
and remain untouched. This release is a reviewable historical data addition;
it does not activate trading or replace an execution ledger. No extra display
label is embedded in the price files.

## Fixture context and chart structure

The process evolves chronologically, rather than interpolating toward the next
known match result. The next scheduled opponent, home/away status, time to
kickoff, rivalry and competition determine anticipation and activity. Past
results and past player ratings/minutes determine form and participation only
after their modeled completion time. Player membership is selected at the
historical timestamp: for example, Rodri uses Manchester City's fixtures before
18 August and Barcelona's thereafter. Osimhen uses Galatasaray's schedule.

Persistent momentum, mean reversion, shared club/market factors and small
entity-specific innovations evolve around context-selected targets. Bull/bear
flags, repeated range boundaries, compression and double-bottom/top formations
provide trends, pullbacks, retests and consolidation. Formations are selected
from information then available, rather than being fitted to the next outcome.
Each instrument has its own seed and path; extending the requested end date
leaves the completed-bar prefix unchanged.

The schedules were captured on 23 October. They preserve reported historical
kickoffs but are **not an archive of when each fixture or reschedule was
originally announced**. Home/away and opponent effects are modeled beliefs,
not historical betting odds. Unmapped opponents use a neutral 1,000 reference;
there is no guessed canonical entity mapping. Current aggregate season totals
and current injury status without a timestamp are not used to shape the past.
The latest timestamped injury report is applied only from its recorded date,
with subsequent recorded participation clearing the modeled absence.

## Reference and band reconstruction

1. `inputs/archive-anchors.json` projects the selected entities' last states
   before 1 August from the sealed, SHA-256-verified calibration archive. Those
   references reproduce the forward ledger's 17 August starting prices. None
   of the selected entities has an intervening August 1–16 sporting movement
   in the sealed archive; there are no invented reference changes in this gap.
2. The cumulative detailed movement ledger supplies every accepted match's
   previous/new reference and published log return. The recorded kickoff is
   retained in `anchors.json`. The history places verification **110 minutes
   after kickoff** (a declared nominal 105-minute match plus five minutes),
   rather than using a final result at kickoff. Actual final-whistle and
   ingestion timestamps are not available in that ledger. This clock is a
   reconstruction convention, not a claim about actual trade/publication time.
3. Recorded player minutes reconstruct the effective-observation count and
   density with the same formula and batch checkpoint resets as `compute.py`.
   The existing `publish.band` function then reconstructs each event's band
   from its reference, density, profile, kind and published signal. The tool
   fails if reconstructed density or reference differs from a saved checkpoint.
4. All five dated public snapshots supply their **exact** published bounds and
   references at their publication cuts. Intermediate per-match bands are
   replay reconstructions, not assertions that an intermediate public snapshot
   was saved. The full event and checkpoint audit is in `anchors.json`.
5. At a reference/band change, the affected leg starts at its new reference.
   The preceding bar closes under its old bounds and the next bar opens under
   its new bounds. The resulting gap is retained. Repeated unchanged snapshot
   rows do not reset market prices.

No unsourced live-band widening is invented. The paths use the archived,
reconstructed or saved publication bounds described above. These bounds persist
until superseded; the 72-hour sizing horizon does not expire a band.

## Pair consistency

The eight pairs are BAR/RMD, MCI/MUN, INT/ACM, BAY/BVB, ARS/CHE, MBP/HLD,
MBP/LMY and VJR/RAPH. Every pair sample is calculated as
`floor(1,000,000,000 × numeratorPriceMicros / denominatorPriceMicros)`.
Thus the displayed ratio is scaled to 1,000 points.

A pair inherits the wider constituent percentage separately on each side,
using the existing market-lifecycle rule; dividing opposite band extremes
would incorrectly compound the band. Joint projection constrains the leg
premiums before pair calculation. This keeps all eight ratios inside their
inherited bands **without independently inventing or clipping pair prices**.
Recalibrating legs are fixed at their references during this projection.
OHLC extrema are taken from synchronized intrabar ratio samples, not from
dividing unrelated leg highs/lows. Open and close ratios are reproducible
from the corresponding leg CSV rows.

## Reproduce and validate

Python 3.11+ and the repository inputs are sufficient; regeneration is offline:

```sh
python3 tools/market_history.py --output /tmp/market-history-check
# Compare the generated manifest, anchors and prices with the dated release.
npm test
```

`inputs/context.json` contains the minimal fixture schedule, dated results,
player appearances, membership intervals, relevant timestamped report and source
URL/hash receipts. Full provider payloads are excluded. The manifest binds the
checked-in inputs, all five saved state/publication sets and the band policy.
`anchors.json` also records the sealed archive and snapshot provenance through
its bound input file. The standard test suite verifies source and output hashes,
coverage, OHLC/band constraints, the exact 38-instrument roster, all published
checkpoints, pair endpoints/bands, transfer timing, prefix stability, and
non-visibility of future results/appearance statistics.
