# Index Price

Public, price-only publications for the Blackbook Football Index.

This repository contains the canonical output needed by price consumers: entity identity, reference price (`R`), lower/upper band (`L`/`U`), density, coverage state, timestamps, versions and price movements. It deliberately excludes scoring code, model components, provider payloads, match identifiers, evidence explanations and trading infrastructure.

## Current publication

- As of: **26 August 2026, 00:00 UTC**
- Entities: **12,250**
- Movement records: **2,383** across **2,175** entities
- Friendlies: **excluded**
- Evidence profile for the 23–26 August batch: **EXTENDED**

`football/current.json` points to the current immutable dated publication. Its manifest commits to every shard with SHA-256; every public row also has its own `priceHash` commitment.

The 72-hour band horizon is rolling operational metadata, not a price expiry. `R` remains the canonical reference until a later verified publication replaces it.

## Consume

Start with [`football/current.json`](football/current.json), verify its `manifestSha256`, then verify each shard against the selected manifest before accepting any price.

## Verify

Requires Node.js 22 or newer:

```sh
node tools/verify.mjs
```

The verifier rejects altered shard hashes, duplicate entities or movements, invalid `L < R < U` bands, count mismatches, unsafe paths and any unexpected row fields. Rejecting extra fields is intentional: this feed must remain price-only.

## Units

All price fields are integer micro-units. Divide `referenceMicros`, `lowerMicros` or `upperMicros` by `1,000,000` for the displayed index value.
