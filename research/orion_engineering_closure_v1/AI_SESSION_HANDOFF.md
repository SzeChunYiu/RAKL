# AI implementation session handoff

## Mission

Implement the ORION engineering-closure programme from this packet on the real `SzeChunYiu/RAKL` repository. Treat the included code as an executable reference contract, not as permission to bypass incumbent RAKL objects.

Programme issue: **#736**.
Reference baseline: `d0e4ac3109d55ff10a0c32168f369bc57fbf39cd`.

## First action — rebase the research object

The repository may have moved. Before editing:

1. read issue #736 and this packet;
2. inspect commits since the frozen baseline;
3. search for any already-landed equivalent engineering contracts;
4. update `BASELINE.json` via a new addendum rather than rewriting the frozen one;
5. run incumbent tests before implementation.

If an equivalent stronger mechanic already landed, absorb it and mark the corresponding gap `ABSORBED_STRONGER_PARENT` rather than duplicating it.

## Patch nucleus to land first

The complete ZIP handoff contains the following additive patch nucleus:

```text
src/rakl/engineering_state.py
src/rakl/engineering_store.py
schemas/project_snapshot.schema.json
schemas/epistemic_status.schema.json
schemas/state_transition_receipt.schema.json
tests/test_engineering_state.py
tests/test_engineering_store.py
tests/test_engineering_schemas.py
```

Local isolated result when packet was created: **14 passed**. The bundle also contains the complete RAKL-style architecture, gap ledger, hostile test matrix, migration plan, API/Observatory contract, parent atlas, repo-relative overlay, and unified additions-only git patch.

Do not merge until the full repository suite and protected workflow gates are green.

## Required integration work after nucleus

### I1 — Build real ProjectSnapshot adapter

Derive snapshot heads from incumbent objects, not duplicated state:

- exact evidence/archive cutoff;
- semantic/lattice revision;
- `MetricLedger`/evaluation epoch;
- episode store head hash;
- saturation basis fingerprints;
- scientific-authority projection revision.

A snapshot creation function must fail closed if a required head cannot be identified.

### I2 — Build EpistemicStatus adapter

Compose existing:

```text
SaturationVectorReport
KnowledgeSaturationAssessment
active residuals
support_solver route/cut/repair state
hard-gate receipts
required authority
```

into one content-identified status object.

Map controller decisions explicitly. Do not infer next action from a weighted scalar.

### I3 — Wire knowledge saturation into runtime

Repo search at packet freeze showed `assess_knowledge_saturation()` was essentially definition+tests rather than the principal solver control loop. Re-audit. If still true:

```text
knowledge acquisition round
-> assessment
-> bounded saturation hard-gate receipt
-> EpistemicStatus
-> controller admissible actions
```

A native residual/freshness event invalidates only affected fibres/axes.

### I4 — Snapshot-bind solver compilation

A compiled `SupportStructure` / working fibre must record:

```text
project_snapshot_id
compiler/reduction identity
target/problem identity
input atom/relation/chart IDs
required authority
```

A result produced against snapshot `S` cannot mutate head `S' != S` without revalidation/replanning.

### I5 — Production repositories

After interfaces are stable, add production adapters:

- object/blob store preserving raw SHA-256 identity;
- PostgreSQL metadata store;
- durable semantic Atlas/lattice representation;
- metric/residual/saturation/decision persistence.

Use a migration system. Avoid a flag-day rewrite.

### I6 — Workflow engine

Create `ResearchWorkflowEngine` with local deterministic reference mode and durable production mode. Temporal is an acceptable parent, not a mandatory dependency; an alternative must demonstrate equivalent history/replay/failure properties.

Preserve incumbent `RECOVERY_REQUIRED` for external-effect ambiguity.

### I7 — API + read-only Observatory

Expose exact snapshot/status/decision/provenance/run data. Mutations require idempotency + before-snapshot identity and always return transition receipts.

Do not create UI-local saturation/authority scores.

### I8 — Operations/security/recovery

Implement OpenTelemetry-compatible operational tracing, access control, secrets boundary, build provenance, backup/PITR and the hostile assurance matrix.

## Commit discipline

Prefer small, dependency-ordered commits/PRs:

```text
1 contracts + schemas + tests
2 incumbent adapters
3 repository protocols/reference adapters
4 production DB/blob backend
5 epistemic controller integration
6 workflow engine
7 service API
8 observability/security/backup
9 hostile assurance packet
```

Preserve historical negatives and receipts. Never modify a failed predecessor result to make a later repair look successful.

## Stop conditions

Do **not** emit `PRODUCTION_READY_SCOPED` because unit tests pass.

Stop and report a narrower terminal when any of these remain open:

- no clean restore from backup;
- no stale-snapshot/concurrent-writer protection;
- unresolved external-effect retry ambiguity;
- UI/controller status divergence;
- semantic store cannot reconstruct exact snapshot;
- migration parity failure;
- security/secret/build identity open;
- no fresh hostile assurance on the exact release artifact.

## What not to do

- Do not introduce `RAKL_SCORE` or one saturation percentage.
- Do not make a vector DB canonical knowledge.
- Do not replace RAKL `MetricReceipt` authority with OTel metrics.
- Do not allow database/admin privilege to imply scientific authority.
- Do not call multi-host external effects exactly-once without a demonstrated idempotency/transaction boundary.
- Do not globally reopen all knowledge when one residual changes.
- Do not delete old local stores before migration/restore parity is established.
