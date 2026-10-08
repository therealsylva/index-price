# Single-match comparison population

`manual-baselines.json` supplies the Extended comparison statistics that a
single match cannot establish on its own. It was extracted, without calculating
prices, from the first 30 accepted September matches in the October 6 audit.
Fresh completed FotMob payloads were checked against the accepted match IDs,
kickoff timestamps and scores. Their newly captured hashes are recorded in
`matchFiles`; they are not claimed to be byte-identical to the original capture.
The population is frozen at September 8 and bound to the existing parameter
package. Shared metrics continue to prefer the sealed historical baselines.
Every retained comparison cell has at least 30 match-equivalent observations.

The backend runtime verifies the population checksum in its `bootstrap-manifest.json`.
The calculator rejects a match earlier than this population, invalid cells,
duplicate matches and changes older than an entity's last accepted event.
Receipts include the comparison-file hash and distinguish the prior population
from a current-batch fallback. Daily batch calculations retain their existing
behavior.

`apps/api/tests/fixtures/fotmob-5802945.json` contains the completed Marseille
1–2 PSG source and a compact projection of the verified September 1 checkpoint.
The integration test calculates both clubs and 30 mapped players, leaves the
unresolved appearance held, checks the unaffected entity, and exercises actual
Postgres migrations, candidate persistence, paired publications, the completion
delay and worker restart. Publication receipts are acknowledged by the test;
the Rust publication protocol has its own execution tests. No production data
or published pointer is changed by this verification.

Run `npm test` in this repository for calculator and publication checks.
Run `npm run check:api` in [index-backend](https://github.com/therealsylva/index-backend/pull/22) for the real match and database proof.
