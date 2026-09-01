# Index Price

Deterministic football-index calculation and public price-only publications.

This repository owns the repeatable path from a declared batch of completed
sporting data to the next canonical price publication. A routine update should
require new data plus a batch manifest—not a new date-specific program.

The current publication is **1 September 2026, 00:00 UTC**: 12,334 entities and
4,934 movement records across 2,948 changed entities. It incorporates 20
eligible completed matches from 30–31 August; friendlies are excluded.

## Update prices

Requires Python 3.11+ and Node.js 22+. Copy and edit the example batch manifest,
listing the exact FotMob match IDs expected in the window:

```sh
cp examples/update-batch.example.json /tmp/update-batch.json
```

Then run the same command for every batch:

```sh
python3 tools/update.py \
  --matches /path/to/new-match-json \
  --archive-root /path/to/restored-calibration-archive \
  --batch /tmp/update-batch.json \
  --dry-run
```

Remove `--dry-run` only after reviewing the candidate summary. The command:

1. validates the exact UTC window and expected match IDs;
2. advances the saved RC3.1 state using only completed in-scope matches;
3. projects the candidate into price-only shards;
4. verifies hashes, schemas, bands, movements, and counts in a staging area;
5. writes the immutable dated publication, audit receipt, next calculator state,
   and finally advances `football/current.json`.

It refuses an incomplete or unexpected batch, a broken price chain, a reference
change without a movement, a future event, or an attempt to overwrite a dated
publication. Additive entity debuts must start from the canonical 1,000
reference; existing entities cannot disappear from a later publication. Raw
provider payloads stay outside this repository.

The batch format is standardized by
[`schemas/update-batch.v1.schema.json`](schemas/update-batch.v1.schema.json).
The current operator example is
[`examples/update-batch.example.json`](examples/update-batch.example.json).

## What is public and reproducible

- `tools/compute.py` is the versioned FotMob adapter and accepted incremental
  RC3.1 Extended forward-bridge calculator.
- `tools/publish.py` deterministically creates the public feed and row hashes.
- `tools/update.py` is the single transactional operator command.
- `config/native-policy-v2.json` is the audit-bound RC3.1 policy package.
- `config/publication-v3.json` contains the exact public band parameters.
- `state/current.json` selects an immutable, hash-committed detailed checkpoint
  and cumulative movement ledger needed to calculate the next batch.
- `updates/YYYY-MM-DD/` records each future batch manifest, receipt, audit, and
  human-readable summary without storing licensed source payloads.

The current provider bridge remains explicit about its limitations in each
receipt: available progression proxies, current-window fallback baselines,
saved-price initialization for the unpublished result-rating state, and held
unresolved player identities. An unresolved identity is never guessed.

This workflow standardizes and exposes the accepted bridge; it does not enable
production automatic reference movement or waive the policy package's separate
activation and shadow-market gates.

## Consume prices

Runtime clients should start with `football/current.json`, verify its
`manifestSha256`, and then verify each shard selected by that manifest. All
prices are integer micro-units; divide by `1,000,000` for display.

The production frontend should still consume the backend API/WebSocket, not poll
GitHub. The backend is the serving and market-runtime layer; this repository is
the transparent calculation, checkpoint, audit, and canonical publication
layer. Keeping those roles separate avoids turning a source repository into a
runtime API while still making price formation inspectable and replayable.

`automaticReferenceMovement: false` means trading activity cannot move the
official sporting reference automatically. A verified sporting batch run by
this calculator can produce the next reviewed reference publication.

## Verify and test

```sh
npm test
```

The regression suite checks that the checked-in detailed state reproduces every
current public reference and movement, and that the band code reproduces every
changed entity declared by the active manifest. It also creates the same
synthetic publication twice, checks byte determinism, and verifies the staged
feed with the public verifier.

To verify only the current public publication:

```sh
node tools/verify.mjs
```

The verifier rejects altered hashes, duplicate entities or movements, invalid
`L < R < U` bands, count mismatches, unsafe paths, and unexpected public fields.
