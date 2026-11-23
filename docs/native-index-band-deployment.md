# Apply the verified index release to the native backend

This operator helper applies the verified November 23, 2026 release (45 new eligible matches; sporting
coverage through November 22) to the actual native PostgreSQL data and active
trading contracts. It does not read or import market-history CSVs.

Run the pinned helper from a checkout/archive containing football/current.json
and football/2026-11-23. The deployed native backend must be available at
/opt/blackbook/index-backend; /etc/blackbook/native.json supplies DATABASE_URL
and the existing internal API/runtime tokens. No Supabase data key is required.

```sh
bash tools/deploy_native_index_release.sh
```

The wrapper verifies the publication and native contract tests, pauses the maker,
applies the normal publication lifecycle, restarts the API and checks the served
catalog date. It restores the maker on success or failure. A failed or interrupted
application can be resumed by rerunning the same pinned release; it must not be
worked around by deleting state. The maker's separate timeout-progress fix should
be installed first.

The planner changes 35 of the 38 contracts from the verified November 15 baseline;
unchanged contracts remain untouched. The existing CSV-pricing adapter clamps
execution marks inside each current band with quote room on both sides. No CSV
history is imported, regenerated or rewritten by this deployment.

The helper validates the 12,405 price rows and 19,787 movement records before
writing. It plans base and pair bands from the verified snapshot, validates each
correction with the backend's normal market-publication validator, and checks
the current runtime version/hash fences for all 38 markets.

It imports the official index dataset using publishIndexPrices, then queues
changed contracts through POST /internal/index-publications. The running
native lifecycle worker publishes to the matching engine, installs terms and
margin/mark data, persists cancellation events, concludes the publication, and
commits the active-market registry. It does not directly edit registry rows,
reset the runtime, change user balances or rewrite positions.

Existing resting orders are handled by the normal publication lifecycle under
the new bands; the market maker can replenish quotes afterward. The batch is
not globally atomic across 38 markets. The helper waits up to three minutes
and verifies all database and matching-engine references/bounds before reporting
success. Exact already-applied bands are skipped. Deterministic correction
contracts make partial retries idempotent; rerun the same pinned helper after an
interruption. A live kickoff band, newer conflicting publication or runtime
version mismatch stops preflight instead of forcing a stale update.

Restart the API afterward to refresh its in-memory official index view. This
restart keeps the durable trading runtime running. Confirm production readiness
before refreshing the website.

The planner and orchestration tests use the real native lifecycle validator and
source snapshots, with mocked database/runtime/queue transports. They do not
contact or mutate a database:

```sh
BLACKBOOK_NATIVE_BACKEND_ROOT=/opt/blackbook/index-backend \
  node tests/native-index-release.test.mjs
```

Tests cover exact base/pair bands, version fences, live/newer-source rejection,
partial/no-op retries, official-feed-before-queue ordering, runtime preflight,
pending timeout and final matching-engine verification. This helper applies
the reviewed November 23 release, bound to its exact manifest hash. It does not
fetch additional matches or migrate the separate manual-match calculator checkpoint.
