# AI implementation session handoff — ORION engineering closure V2

## Mission

Land and integrate the V2 ORION engineering-closure reference substrate into the real `SzeChunYiu/RAKL` repository without creating a second scientific-authority system.

Programme issue: **#736**.
Frozen V1 baseline: `d0e4ac3109d55ff10a0c32168f369bc57fbf39cd`.
Latest repo re-audit cutoff used by this packet: `19dc8d022e5c609d30d075a754f52f58242ce917`.

**Current packet terminal:** `REFERENCE_ENGINEERING_RESEARCH_SATURATED__IMPLEMENTATION_RESIDUALS_OPEN`.

The research/design question is bounded-flat across the final registered route families. This does **not** authorize `PRODUCTION_READY_SCOPED`; real-repository integration and real infrastructure assurance remain open.

## Read first

1. `V2_IMPLEMENTATION_STATUS.md`
2. `DEFECT_LEDGER_V2.json`
3. `RESEARCH_SATURATION_V2.json`
4. `CLOSURE_ASSESSMENT_V2.json`
5. `PARENT_ABSORPTION_V2.md`
6. `POSTGRES_SCHEMA_DRAFT.sql`
7. issue #736

Before applying code, inspect current main from the cutoff above and absorb any stronger equivalent mechanic that landed later. Never duplicate an already stronger parent.

## What V2 already implements locally

The additive overlay contains an executable single-node reference substrate for:

```text
exact raw-byte BlobStore semantics
immutable evidence metadata + deterministic evidence revision
ProjectSnapshot lineage
StateTransitionRequest/Receipt with action-payload identity
snapshot CAS + exact idempotent replay
append-only typed semantic atom/relation versions
previewable semantic mutation batches
single-transaction semantic batch + snapshot + transition commit
single-transaction evidence metadata + snapshot + transition commit
canonical EpistemicStatus
shared controller/Observatory status projections
snapshot-bound control projections
snapshot-bound disposable solver views
rebuildable exact/lexical semantic index
durable hash-chained workflow history
explicit retry-safe / RECOVERY_REQUIRED activity semantics
versioned in-process service/API facade
non-compensatory capacity policy
migration parity/import receipts
infrastructure capability + secret-reference contracts
runtime artifact/build identity contract
consistent online SQLite backup
closed-world backup archive verification
empty-environment restore + reconstruction
operator diagnostics
engineering closure + research saturation evaluators
```

### Load-bearing semantics discovered during hostile implementation

Do not regress these:

- one snapshot + target + fibre has exactly one canonical `EpistemicStatus`;
- historical semantic state may not see future fibres;
- workflow history needs an externally sealed head to detect clean tail truncation;
- snapshot IDs are project-bound in all integrated stores;
- semantic/evidence content identity cannot hash the after-snapshot ID, or an identity cycle forms;
- semantic/evidence mutation + project-head + transition receipt commit atomically in the reference SQLite metadata transaction;
- idempotency identity binds the **intended effect** through `action_payload_hash`, not just the action verb;
- a pure semantic action cannot smuggle evidence/metric/episode/authority changes, and a pure evidence action cannot smuggle semantic/control changes;
- exact evidence bytes are written/verified before evidence metadata commits; an orphan content blob is safe, metadata pointing to absent/corrupt bytes is not;
- copying a live WAL-mode SQLite main file is not a valid backup primitive; use the SQLite online backup API;
- backup archives are closed-world: no duplicate or unmanifested members;
- shared-database production FKs must be project-scoped;
- new semantic fibre parents are topologically ordered and cycles fail at preview.

`DEFECT_LEDGER_V2.json` preserves all 17 findings and their repairs.

## Local validation at packet freeze

```text
82 / 82 engineering tests passed
4 / 4 repeated post-fix concurrent-writer races flat
2 / 2 repeated post-fix clean backup/restore/reconstruct runs flat
39 / 39 combined semantic/schema/backup/workflow/control hostile tests flat
8 materially different final research routes flat
```

This is same-context reference validation, not independent release assurance.

## First implementation wave on the real repo

### R1 — Rebase and deduplicate

- Compare current main against the packet cutoff.
- Search for equivalent `ProjectSnapshot`, `EpistemicStatus`, transactional state, durable workflow and Atlas persistence work.
- Add a new baseline addendum; do not rewrite frozen V1/V2 research artifacts.
- Run the incumbent full suite before touching protected code.

### R2 — Land contracts + reference backends

Prefer additive commits in dependency order:

```text
engineering_state.py / schemas
engineering_store.py / engineering_blob.py
engineering_evidence_store.py
engineering_semantic_store.py / adapters / index
engineering_control_store.py
engineering_atomic.py
engineering_service.py / engineering_api.py
engineering_workflow.py
backup / migration / security / release / capacity / doctor
research packet + hostile tests
```

Adapt imports/package layout to current main rather than forcing the overlay's paths if the refactor has moved incumbent objects.

### R3 — Replace declared heads with incumbent-derived heads

`ProjectSnapshot` must derive, not invent:

```text
evidence cutoff/revision from canonical archive/evidence metadata
semantic revision from durable Atlas/lattice state
metric ledger head + EvaluationEpoch
EpisodeStore head
saturation basis fingerprints/certificates
scientific-authority projection revision
controller epoch
```

Fail closed when any required coordinate cannot be identified.

### R4 — Complete E3: full Atlas persistence

The local reference store persists fibres/atoms/compatibility witnesses but intentionally leaves one E3 residual: the full contextual Atlas chart/transition/obstruction plane is only specified in `POSTGRES_SCHEMA_DRAFT.sql`.

Implement project-scoped, append/version-oriented persistence for:

```text
AtlasChart
OverlapTransition
GluingObstructionCertificate / equivalent obstruction record
```

Bind it into the same semantic revision and atomic metadata transition. Do not make graph/vector indexes canonical.

### R5 — Complete E9: wire real control loop

Re-audit `assess_knowledge_saturation()` usage. Wire the real principal runtime:

```text
knowledge acquisition / normalization
-> persist semantic/control delta
-> affected saturation recomputation
-> bounded-saturation hard-gate receipt
-> EpistemicStatus
-> admissible controller action
-> snapshot-bound solver-view compilation
-> solve/cut/repair
-> residual event
-> reopen only implicated fibres/axes
```

The graph solver itself may consume status metadata for planning but does not gain authority to certify knowledge completeness.

### R6 — Production repository backend

Translate the reference transaction semantics into the production metadata store. `POSTGRES_SCHEMA_DRAFT.sql` is a design artifact, not a migration ready to run blindly.

Required production behavior:

- project-scoped identities/FKs;
- serializable or equivalently strong consequential metadata transitions;
- retry the complete read/plan/write transaction on serialization conflict;
- no last-writer-wins for epistemic/controller state;
- content-addressed blob writes are separately idempotent; orphan blobs are tolerable, missing referenced blobs are not;
- exact import/migration receipts and shadow-read parity before cutover.

### R7 — Production workflow engine

Keep the reference semantics:

```text
durable history
snapshot binding
stable workflow/activity/invocation identity
attempt history
retry-safe declaration
external-effect ambiguity -> RECOVERY_REQUIRED
expected sealed history head for tail-loss detection
```

A Temporal-class durable history/replay engine is an acceptable parent, not mandatory. Do not promise distributed exactly-once external side effects unless a demonstrated transaction/idempotency boundary actually provides it.

### R8 — Service, Observatory, OTel and security

- Network transport may wrap `EngineeringServiceFacade`; it cannot weaken snapshot/idempotency requirements.
- Both controller and UI consume the exact same `status_id`; no UI-local saturation score.
- Export operational traces/logs/metrics through an OpenTelemetry-compatible adapter while leaving RAKL `MetricReceipt` semantics unchanged.
- Bind workload identity/authz/secrets/build provenance as **infrastructure** authority only.

### R9 — Migration, restore, load and hostile release assurance

Before any production terminal, execute the full hostile matrix on the exact candidate artifact. Include:

```text
concurrent semantic/evidence writers
worker death around external effect
stale controller decision replay
basis fingerprint change
DB failover during transition
blob outage/corruption
index destruction/rebuild
live backup/PITR
restore into empty environment
partial migration + rollback
secret rotation
release artifact/provenance mismatch
load/SLO/capacity envelope
```

A failed release candidate remains a preserved negative; do not threshold-shop it into readiness.

## Current open fibres to prioritize

`CLOSURE_ASSESSMENT_V2.json` is machine-readable. The strongest residuals are:

- E3 — full Atlas chart/transition/obstruction persistence integrated atomically;
- E4/E9 — real incumbent metrology/saturation/controller heads and principal runtime wiring;
- E6 — production multi-worker durable workflow backend;
- E10/E11 — network API + production read-only Observatory;
- E12 — actual OpenTelemetry export adapter;
- E13 — real authn/authz/secret-manager enforcement;
- E15 — PostgreSQL PITR/object-store restore drills;
- E17 — measured load/SLO envelope;
- E18 — fresh hostile assurance on exact production release;
- E19 — real build provenance verifier;
- E20 — live production runbook/operator drill.

## Forbidden shortcuts

- No `RAKL_SCORE` / one saturation percentage.
- No vector DB or prompt as canonical knowledge.
- No OTel metric as a substitute for RAKL metric authority.
- No database/admin/workload credential as scientific authority.
- No silent whole-project knowledge resaturation after one local residual.
- No multi-plane state change under an action payload that names only one plane.
- No file copy of a live transactional database as a backup claim.
- No “exactly once” language for external effects without a demonstrated boundary.
- No `PRODUCTION_READY_SCOPED` from unit/reference tests alone.

## Allowed terminal now

The packet itself supports only:

`REFERENCE_ENGINEERING_RESEARCH_SATURATED__IMPLEMENTATION_RESIDUALS_OPEN`

A future production terminal must be earned on an exact deployed/release identity with fresh restore/replay/concurrency/security/load assurance.
