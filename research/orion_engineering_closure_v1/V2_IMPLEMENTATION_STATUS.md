# ORION engineering closure V2 — implementation status

**Date:** 2026-08-15
**Repo re-audit cutoff:** `19dc8d022e5c609d30d075a754f52f58242ce917`
**Programme:** #736
**Terminal:** `REFERENCE_ENGINEERING_RESEARCH_SATURATED__IMPLEMENTATION_RESIDUALS_OPEN`

## What V2 adds beyond V1

The V2 packet is no longer just snapshot/store contracts. It contains an executable single-node reference substrate for:

```text
raw CAS bytes
-> immutable evidence metadata + evidence revision
-> ProjectSnapshot transition
-> append-only semantic mutation batch + semantic revision
-> atomic semantic/evidence head updates (separate pure actions)
-> canonical EpistemicStatus
-> shared controller + Observatory projections
-> control artifact projection store
-> rebuildable semantic index
-> snapshot-bound workflow history
-> API/service facade
-> capacity policy
-> migration parity/import receipts
-> runtime/build + infrastructure identity contracts
-> consistent SQLite online backup
-> closed-world archive verification
-> empty-environment restore + exact reconstruction
```

All state-changing reference actions bind a before-snapshot and an action-payload hash. Pure evidence and pure semantic transitions may not mutate unrelated snapshot heads. Multi-plane changes require a separately content-identified composite action.

## Hostile findings retained

V2 found and repaired 17 distinct reference/design defect classes. See `DEFECT_LEDGER_V2.json`. The important classes include snapshot/status ambiguity, historical leakage, tail truncation, cross-project binding, symlink/archive ambiguity, semantic identity cycles, split metadata transactions, under-bound idempotency, live-WAL backup loss, shared-database cross-tenancy FKs, semantic parent cycles, and effect smuggling.

## Validation at freeze

- engineering suite: **82 passed**;
- post-fix concurrency replay: **4/4** repeated races flat;
- post-fix clean backup/restore/reconstruct: **2/2** flat;
- combined semantic/schema/backup/workflow/control hostile route: **39 passed**, zero new retained defect classes;
- current-repo dedupe route: flat;
- external-parent refresh route: flat.

`RESEARCH_SATURATION_V2.json` evaluates the final eight materially different route families as bounded-flat. This is research-space saturation only.

## What remains genuinely open

The packet does **not** claim production readiness. The strongest remaining fibres require the real repository and/or infrastructure: full Atlas chart/transition/obstruction persistence in the atomic metadata transaction; actual runtime consumption of `EpistemicStatus`; production PostgreSQL/blob/workflow adapters; OTel export; real authn/authz/secrets; PostgreSQL PITR/object-store restore drills; load/SLO measurements; real build provenance verification; and fresh hostile assurance on the exact release artifact.

Those are implementation/deployment residuals, not missing architecture questions.
