# BLACKBOOK INDEX PRICE UPDATE CANON
## Operational Handoff Instructions for Any Future Model

**Status:** Canonical operational instruction
**Purpose:** Allow another model/agent to perform the normal Blackbook index-price update workflow without relying on previous conversation memory.

---

# 1. PRIME DIRECTIVE

You are operating the Blackbook Index Price update pipeline.

Your job is to:

1. Determine the latest already-published index state.
2. Determine which newly completed football matches are eligible.
3. Obtain and verify the canonical match/event data.
4. Reconcile the data before scoring.
5. Apply the **currently canonical Blackbook methodology**.
6. Recalculate affected player and club index state.
7. Generate the new price/reference artifacts.
8. Run all required validation/audit checks.
9. Publish/update repository artifacts only when the production gates permit it.
10. Report exactly what changed.

**Never invent a missing value. Never silently substitute a methodology version. Never treat a data gap as zero performance. Never activate production reference movement merely because a calculation succeeded.**

The repository is the source of truth for the currently implemented methodology.

---

# 2. METHODOLOGY VERSION CONTROL

Before doing anything else, inspect the current policy.

The canonical policy currently specifies:

- Schema: `blackbook.index.rc3.1.native-policy.v2`
- Methodology: `blackbook-football-index-v0.3-rc3.1.1`
- Parameter policy: `blackbook-football-rc3.1-policy-v2`
- Implementation: `NATIVE_RUST_RC3_1`
- Runtime module: `engines/index/src/sporting/rc3.rs`

The policy currently says parameter closure is complete, production release is not authorized, production reference movement is disabled, production publication is disabled, and an independent activation gate is required.

Therefore:

**A successful calculation is NOT automatically a production publication.**

### Absolute version rule

Do not revive RC2.1, revive old RC2.2 scoring, mix RC2 and RC3 parameters, use an old research scorer because it is easier, invent replacement coefficients, or alter the policy during a routine update.

If the repository's current canonical policy has changed, follow the new policy.

If there is disagreement between an old conversation instruction and the current canonical repository policy, stop and investigate rather than guessing.

---

# 3. TOOLS / SYSTEMS USED

## A. GitHub

Primary repository access.

Use GitHub to inspect `therealsylva/index-price`, current branch/state, methodology/configuration, previous update artifacts, match-audit artifacts, generated pricing artifacts, tests, and PRs/commits when applicable.

Important repository areas include:

```text
config/
updates/
engines/
recovery/
```

Always verify exact paths against the current repository.

Current canonical policy file:

```text
config/native-policy-v2.json
```

## B. Web research

Use web search to establish what actually happened in the football world, especially to find completed matches after the last update, check whether a league actually played, resolve schedule/results discrepancies, and independently check suspicious or incomplete source data.

Do not infer that "no new matches exist" merely because the repository contains no new match file.

## C. Canonical data/adapters

The scoring engine does not accept arbitrary web snippets as authoritative scoring facts.

The current policy requires a `VERSIONED_CANONICAL_ADAPTER_ENVELOPE` with the required evidence class and completeness/reconciliation requirements.

Current source-authority requirements include E2 evidence, a primary completeness watermark, and a reconciliation policy. Material disagreement or a missing required counter produces `DATA_HOLD`. Provider packet boundaries have no scoring authority.

Web research is primarily for discovering/verifying the football event universe. Actual scoring input must pass the canonical data boundary.

---

# 4. FIRST STEP: FIND THE LAST UPDATE

Never start by looking for today's matches.

First establish the latest published state. Find the most recent update directory, match audit, publication artifact, price snapshot, update manifest, and associated commit/PR where applicable.

Record:

```text
last_update_timestamp
last_update_commit
last_update_artifact
last_processed_match
last_processed_match_timestamp
methodology_version
parameter_version
```

Do not confuse:

```text
last repository ingestion
```

with:

```text
last production publication
```

or with:

```text
last football match played
```

These are three separate concepts.

---

# 5. DETERMINE THE MATCH CUTOFF

Once the last processed state is known, establish the precise cutoff and search forward from that point.

For every candidate match determine:

```text
competition
match_id
effective_utc
home team
away team
completion status
final score
data availability
eligibility
```

Only completed matches can enter a normal completed-match update.

---

# 6. DETERMINE ELIGIBILITY

Do not simply collect every football match. Use the current policy/repository coverage.

The current empirical baseline covers:

- La Liga
- Ligue 1
- Premier League
- Serie A

Always inspect current configuration before assuming this remains the production scope.

For every candidate classify:

```text
ELIGIBLE
INELIGIBLE
DATA_HOLD
```

Do not accidentally include lower divisions, youth football, women's football, friendlies, unrelated competitions, domestic cups, or international matches unless the current canonical configuration explicitly makes them eligible.

The repository policy is authoritative.

---

# 7. BUILD THE MATCH AUDIT

Create/update the match-audit dataset before calculating prices.

At minimum record:

```text
match_id
competition
effective_utc
home_team
away_team
status
eligibility
source
source_version
final_score
data_completeness
reconciliation_status
```

The audit should answer:

> What happened, where did we get it from, and are we allowed to score it?

Do not jump directly from a web search result to an index price.

---

# 8. DATA RECONCILIATION

For every eligible match:

1. Establish the primary match identity.
2. Establish the final result.
3. Establish the event timeline.
4. Establish player attribution where applicable.
5. Establish verified player exposure.
6. Compare available evidence.
7. Resolve revisions.
8. Produce the canonical event stream.

If sources disagree materially:

```text
DATA_HOLD
```

If a required counter is missing:

```text
DATA_HOLD
```

If a field has zero authority under the policy, retain it for audit but do not give it scoring weight.

---

# 9. ACTIVE REVISION RULE

The current policy uses:

```text
HIGHEST_VALID_REVISION_REPLACES_PRIOR_HEAD_BY_REPLAY
```

A corrected/revised event is not simply appended as another event. The valid revision replaces the previous active head and the affected state is replayed.

**Never double-count corrected events.**

---

# 10. COVERAGE PROFILE

The current policy has two principal profiles:

```text
BASIC
EXTENDED
```

Basic requires `SCORE_TIMELINE`.

Extended requires:

```text
DEEPER_PLAY_BY_PLAY
EXTENDED_PLAYER_STATS
SCORE_TIMELINE
```

The profile is frozen from provider capabilities before the first priced fact.

If Extended cannot recover a required capability, the policy allows:

```text
EXTENDED → BASIC
```

with accepted facts retained, reference movement disabled, and the band widened.

Do not create two separate indexes because one match is Basic. The policy requires `ONE_INDEX_NOT_TWO`.

---

# 11. SCORING RULE

The current RC3.1 policy uses canonical positive/negative scoring units.

```text
each canonical positive fact = +1
each canonical adverse fact = -1
```

before cohort normalization.

Every verified regulation/extra-time scorer goal is one goal.

Player and club ledgers are separate and non-addable.

Do not score the same provider action twice.

---

# 12. EVENT PRECEDENCE

One provider action gets **one exclusive scoring row**.

Current precedence includes:

```text
ACTIVE REVISION
        ↓
ONE PROVIDER ACTION = ONE SCORING ROW
        ↓
OWN GOAL
        ↓
GOAL
        ↓
SHOT ON TARGET NON-GOAL
        ↓
OFFICIAL ASSIST
        ↓
KEY PASS
        ↓
SET-PIECE DELIVERY
        ↓
PROGRESSIVE PASS
        ↓
ORDINARY PASS
        ↓
PROGRESSIVE CARRY
        ↓
OTHER POSSESSION EVENTS
```

Disciplinary precedence includes:

```text
STRAIGHT RED > SECOND YELLOW > PENALTY CONCEDED > YELLOW > ORDINARY FOUL
```

The exact canonical ordering in the policy must be followed.

---

# 13. CURRENT SCORING EVENT FAMILIES

The current policy contains scoring rows including:

### Attack
```text
goal
shot_on_target_non_goal
```

### Creation
```text
official_assist
key_pass_non_assist
```

### Progression
```text
completed_progressive_pass
failed_progressive_pass
progressive_carry
failed_progressive_carry
```

### Control
```text
ordinary_pass_completed
ordinary_pass_failed
successful_dribble
possession_lost
ball_recovery
```

### Defence
```text
tackle_won
interception
block
clearance
own_goal
```

### Goalkeeping
```text
save
cross_claimed
goal_conceded
```

### Set pieces
```text
penalty_won
penalty_missed
set_piece_delivery_completed
set_piece_delivery_failed
```

### Discipline
```text
yellow_card
second_yellow_dismissal
straight_red
foul_committed
penalty_conceded
```

These are currently bound RC3.1 policy rows, not suggestions. Always read the current policy before execution.

---

# 14. NORMALIZATION

Raw event counts are NOT directly converted into price changes.

The current policy normalizes performance using historical cohorts.

Important current parameters include:

```text
history lookback: 720 days
minimum effective matches: 30
center: pre-window cohort median
scale: 1.4826 × pre-window cohort MAD
fallback: population SD
fallback: 1
smooth: 2.5 × tanh(raw_z / 2.5)
```

Metric-rate basis:

```text
SIGNED_ALLOCATED_UNITS × 5400
--------------------------------
VERIFIED_ACTIVE_SECONDS
```

Cohort hierarchy:

```text
verified role + competition
        ↓
verified role + all supported competitions
        ↓
entity type + all supported competitions
```

If all tiers are insufficient:

```text
DATA_HOLD
```

The current cell does not enter its own cohort.

---

# 15. PLAYER COMPONENT WEIGHTS

Do not invent weights.

The current policy defines component weights for attack, creation, progression, control, defence, and goalkeeping.

Examples from the current policy:

```text
Attack:
goal outcome                 70%
shot on target non-goal      30%

Creation:
official assist              60%
key pass                     40%

Progression:
progressive pass net         65%
progressive carry net        35%
```

The complete values must always be read from the current canonical policy.

---

# 16. FROM PERFORMANCE TO INDEX STATE

After event scoring and normalization:

1. Calculate affected component metrics.
2. Calculate entity-level component values.
3. Calculate the new state.
4. Apply the canonical deterministic transformation.
5. Preserve unaffected entities.
6. Generate the new index state.
7. Generate corresponding price/reference artifacts.

Do not manually edit prices because a player "had a great game." The price is an output of the deterministic pipeline.

---

# 17. INITIAL REFERENCE AND DISPLAY SCALE

Current display configuration:

```text
initial reference = 1000
macro base = 100
macro log elasticity = 0.10
macro state clip = [-5, +5]
```

Current arithmetic:

```text
fixed-point log-return scale = 1,000,000,000,000
seconds per 90 = 5400
rounding = NEAREST_EVEN
```

Ordered summation:

```text
ASCENDING_CANONICAL_TERM_ID_SIGNED_INT128
```

This matters for deterministic reproducibility.

Do not replace canonical fixed-point behavior with casual floating-point arithmetic.

---

# 18. BANDS

Bands are not the same thing as the reference price.

Blackbook separates:

```text
REFERENCE
MARKET/OBSERVED PRICE
BAND
```

The band provides an allowed range around the current reference state.

Current principal horizon:

```text
72 hours
```

Comparison horizons:

```text
24 hours
168 hours
```

Read exact band methodology from current policy/configuration.

Never interpret the band as a statistical confidence interval. It is an operational pricing/range mechanism.

---

# 19. REFERENCE MOVEMENT

The current repository policy explicitly says:

```text
production_reference_movement = false
production_publication = false
```

Therefore, while production movement is disabled:

**You may calculate what the new reference WOULD be without actually moving the production reference.**

A successfully scored match does not authorize production movement.

A passing test does not authorize production movement.

A newly calculated price does not authorize production movement.

Only the independent activation gate can authorize it.

---

# 20. PRICE UPDATE WORKFLOW

The standard sequence is:

```text
1. Inspect current repository state
        ↓
2. Read canonical policy
        ↓
3. Identify last published/processed state
        ↓
4. Determine cutoff
        ↓
5. Search actual football results after cutoff
        ↓
6. Enumerate candidate matches
        ↓
7. Apply competition eligibility
        ↓
8. Build match audit
        ↓
9. Obtain canonical event data
        ↓
10. Reconcile sources
        ↓
11. Freeze coverage profile
        ↓
12. Resolve revisions
        ↓
13. Generate canonical event ledger
        ↓
14. Score events
        ↓
15. Normalize against historical cohorts
        ↓
16. Recalculate affected entities
        ↓
17. Generate reference/pricing output
        ↓
18. Calculate/validate bands
        ↓
19. Run tests
        ↓
20. Run reconciliation/audit checks
        ↓
21. Check production activation gates
        ↓
22. Publish only if authorized
        ↓
23. Record exact update summary
```

---

# 21. TESTING

Testing is mandatory.

### Data integrity

- no duplicate matches;
- no duplicate canonical events;
- no unresolved material disagreement;
- no missing required counters;
- correct final scores;
- correct match identity.

### Scoring integrity

- one provider action → one scoring row;
- revisions replace previous active heads;
- own goals follow precedence;
- assists are not simultaneously scored as key passes;
- set-piece tags do not create additive scoring;
- player and club ledgers remain separate.

### Numerical integrity

- deterministic output;
- fixed-point arithmetic;
- correct rounding;
- ordered summation;
- no NaN/Inf;
- no unexplained price jumps.

### Regression integrity

Run the repository's existing test suite. Do not replace canonical tests with an ad-hoc calculation.

---

# 22. OUTPUT AUDIT

Every update should produce enough information to answer:

```text
What matches were added?
What matches were excluded?
Why were they excluded?
What data source was used?
Was the data complete?
Which entities changed?
How many players changed?
How many clubs changed?
What were the old prices?
What are the new calculated prices?
What was the movement?
Were any entities held?
Were any matches held?
Did tests pass?
Was production publication enabled?
Was reference movement enabled?
```

The update should be reproducible from repository artifacts.

---

# 23. CALCULATED VS PUBLISHED

Always report these separately.

Example:

```text
Calculated:
+27 player prices
+8 club prices

Production reference:
UNCHANGED

Reason:
production_reference_movement=false
```

Do not say "The index moved +2.4%" if the production reference did not actually move.

Instead say:

> The calculated reference change was +2.4%; production reference movement remains disabled.

---

# 24. WHEN THERE ARE NO NEW MATCHES

Do not manufacture an update.

If there are no eligible matches after the cutoff:

```text
new eligible matches = 0
```

That is a legitimate update result.

But verify against the actual football calendar. Do not infer "no matches" solely because the repository has no new file.

Correct procedure:

```text
repo cutoff
+
actual football results
+
eligibility policy
=
new eligible match count
```

---

# 25. WHEN THERE ARE DATA PROBLEMS

Use explicit states.

### DATA_HOLD

Use when material sources disagree, a required counter is missing, required historical normalization support is unavailable, or canonical data cannot be established.

Do not guess.

### NOT_OBSERVED_BY_PROFILE

Use when the profile legitimately does not observe a field.

This is different from zero. Do not convert "not observed" into zero.

### ACCEPT_WITH_AUDIT_NULL

Use for fields explicitly designated zero-authority by policy.

---

# 26. DO NOT MAKE METHODOLOGY CHANGES DURING AN UPDATE

A routine update is a data operation, not a methodology research session.

Never decide during an update:

- new weights;
- new scoring events;
- new leagues;
- new band widths;
- new normalization windows;
- new coefficients;
- new price mechanics.

If a methodology problem is discovered:

```text
STOP
DOCUMENT
RAISE THE ISSUE
DO NOT SILENTLY PATCH THE METHODOLOGY
```

Methodology changes require their own controlled process.

---

# 27. GIT WORKFLOW

When repository changes are required:

1. Inspect current branch/state.
2. Do not overwrite unrelated work.
3. Create a focused branch if the workflow calls for one.
4. Make only the required update changes.
5. Run tests.
6. Inspect the diff.
7. Confirm generated artifacts.
8. Commit with a descriptive message.
9. Open/update the appropriate PR if required.
10. Do not merge unless explicitly authorized.

Never use a destructive reset to "clean things up" without understanding the current repository state.

Never delete another agent's work because it looks old.

---

# 28. REPORTING FORMAT

After every update, provide:

```text
BLACKBOOK INDEX UPDATE
──────────────────────

Methodology:
RC3.1 / <exact current version>

Cutoff:
<timestamp>

New candidate matches:
<N>

New eligible matches:
<N>

Excluded:
<N>

Held:
<N>

Matches processed:
<N>

Players recalculated:
<N>

Clubs recalculated:
<N>

Calculated movements:
<summary>

Production reference movement:
ENABLED / DISABLED

Production publication:
ENABLED / DISABLED

Tests:
PASS / FAIL

Audit:
PASS / DATA_HOLD

Commit:
<sha>

Status:
<COMPLETE / HOLD / BLOCKED>
```

If nothing happened:

```text
New eligible matches: 0

No index recalculation required.
Production state unchanged.
```

---

# 29. FINAL SAFETY RULES

### RULE 1
**Repository policy beats memory.**

### RULE 2
**Canonical methodology beats old methodology.**

### RULE 3
**Verified data beats inference.**

### RULE 4
**DATA_HOLD beats fabricated completeness.**

### RULE 5
**A missing observation is not automatically zero.**

### RULE 6
**A calculated reference is not automatically a published reference.**

### RULE 7
**A passing test is not production authorization.**

### RULE 8
**Never double-count revised events.**

### RULE 9
**Never score one provider action twice.**

### RULE 10
**Never change methodology during a routine price update.**

### RULE 11
**Never claim that no matches occurred without checking the actual football calendar when the cutoff is current.**

### RULE 12
**Every published number must be traceable back through the event ledger, normalization state, methodology version, and source evidence.**

---

# 30. DEFAULT DECISION TREE

When asked:

> "Update the Blackbook index."

Execute:

```text
READ POLICY
   ↓
CHECK CURRENT VERSION
   ↓
CHECK LAST UPDATE
   ↓
CHECK ACTUAL FOOTBALL RESULTS
   ↓
FILTER ELIGIBLE MATCHES
   ↓
AUDIT DATA
   ↓
RECONCILE
   ↓
DATA_HOLD IF NECESSARY
   ↓
SCORE USING CURRENT POLICY
   ↓
NORMALIZE
   ↓
RECALCULATE
   ↓
VALIDATE
   ↓
CHECK PRODUCTION GATES
   ↓
PUBLISH ONLY IF AUTHORIZED
   ↓
REPORT
```

If anything is ambiguous:

```text
DO NOT GUESS.
INSPECT THE REPOSITORY.
```

That is the core operating principle.

---

# 31. CURRENT CANONICAL STATE AT HANDOFF

At the time this canon was written, the repository's canonical policy reports:

```text
schema:
blackbook.index.rc3.1.native-policy.v2

methodology:
blackbook-football-index-v0.3-rc3.1.1

parameter:
blackbook-football-rc3.1-policy-v2

implementation:
NATIVE_RUST_RC3_1

module:
engines/index/src/sporting/rc3.rs

status:
PARAMETER_CLOSED_IMPLEMENTED_REFERENCE_DISABLED

production_reference_movement:
false

production_publication:
false

independent_activation_gate_required:
true
```

The policy also explicitly says the implementation does **not** import the historical research scorer.

Therefore the canonical production calculation must follow the native RC3.1 implementation rather than resurrecting an older research implementation.

---

# END OF CANON

**If another model follows this document, its first action should always be to inspect the current repository policy and current update state. It must never assume that the values in this handoff remain unchanged forever.**
