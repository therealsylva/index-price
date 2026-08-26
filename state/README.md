# Calculator checkpoint

`current.json` selects the immutable, hash-committed detailed state consumed by
the next update. Each dated manifest commits to index and cumulative sporting
movement shards. These are calculation inputs, not the public API contract;
public consumers should continue to use `football/current.json`.

The initial checkpoint is the accepted 26 August 2026 RC3.1 Extended forward
candidate from [`index-backend` PR #13](https://github.com/therealsylva/index-backend/pull/13)
that produced the current price-only publication. Raw licensed provider payloads
are not stored here.

When materialized as canonical JSON, the initial checkpoint commitments are:

- detailed index: `e46d4665f971406ac4ba428d08197a49c2413bd69e9ddcf47830600b0f252c92`
- movement ledger: `9db97cd9fcd4eec4cd6afde79f3a41bce121980aff4eb92daf6929a01b20a18f`
