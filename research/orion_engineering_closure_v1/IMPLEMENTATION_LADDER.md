# Dependency-ordered implementation ladder

Do not implement the dashboard first. Do not replace existing stores in one migration. Do not turn a research framework redesign into a framework rewrite.

## Wave E0 — Freeze and parity fixtures

1. Pin the exact implementation branch to the baseline or explicitly record the new head delta.
2. Run the full incumbent test suite before touching protected behavior.
3. Freeze golden fixtures for:
   - one local project record/payload;
   - one episode-store chain;
   - one resumable metric/controller envelope;
   - one saturation vector/report;
   - one v3 state fingerprint;
   - one execution receipt with `RECOVERY_REQUIRED` hostile case.
4. Freeze the new engineering schemas from this packet or version them if changes are required.

**Gate:** implementation may continue only if current fixtures are exactly reproducible.

## Wave E1 — Additive state contracts

Land `engineering_state.py`, schemas and tests first.

Then add narrow adapters from existing objects:

```text
RAKLV3State / evidence archive heads / MetricLedger / episode store / authority projection
   -> ProjectSnapshot
SaturationVectorReport + KnowledgeSaturationAssessment + residual/cut state
   -> EpistemicStatus
```

No production backend yet.

**Gate:** old code remains green; new status view is a projection only.

## Wave E2 — Repository interfaces and reference backend

Land `engineering_store.py` as reference semantics. Extract explicit protocols/interfaces for:

```text
BlobStore
SnapshotRepository
SemanticRepository
MetrologyRepository
TransitionRepository
```

Wrap current local filesystem/CAS/episode stores through adapters instead of deleting them.

**Gate:** local restart, idempotency and stale-writer hostile tests pass.

## Wave E3 — Production persistence

Implement:

- production object-store `BlobStore` adapter;
- PostgreSQL-class transactional metadata backend;
- durable semantic Atlas/lattice schema;
- saturation/metric/residual/controller persistence;
- migration tables/versions.

Use strong uniqueness/foreign-key constraints. Consequential transitions use serializable semantics or an equivalently demonstrated protocol and retry the entire transaction on serialization conflict.

**Gate:** dual-write parity on a frozen corpus; byte/semantic identities match reference backend.

## Wave E4 — Epistemic control integration

Make the existing knowledge controller real runtime input:

```text
assess_knowledge_saturation()
 -> bounded_saturation_artifacts()
 -> persist MetricReceipt/HardGate
 -> EpistemicStatus
 -> admissible action set
```

Bind support-structure compilation to exact `ProjectSnapshot` and persist compiler identity/input IDs.

Solver outcomes persist route/cut/repair and residual transformation before new planning.

**Gate:** planted stale certificate, route-missing and residual-reopen cases all route correctly.

## Wave E5 — Durable workflow engine

Define `ResearchWorkflowEngine`.

Reference engine: deterministic in-process history for tests.
Production engine: Temporal-class durable history or equivalent demonstrated implementation.

Every external Activity has:

```text
activity_id
idempotency key when possible
retry_safe
attempt number
timeout/heartbeat
exact snapshot input
terminal receipt or RECOVERY_REQUIRED
```

**Gate:** kill worker after external side effect but before completion record; system must not silently replay a non-idempotent effect.

## Wave E6 — Service API and Observatory

Add service boundary with optimistic snapshot/idempotency semantics. Build a read-only Observatory first.

UI does not calculate epistemic truth; it renders `EpistemicStatus` and linked receipts.

**Gate:** one status ID has identical control-relevant fields through API, controller and UI projection.

## Wave E7 — Operations/security/provenance

Add:

- OpenTelemetry operational adapter;
- authn/authz/service identities;
- secret-manager references;
- build/release attestation verification;
- backup/PITR;
- deployment manifests and environment identity;
- operator runbooks.

**Gate:** security and restore hostile tests pass on an exact release artifact.

## Wave E8 — Fresh hostile production assurance

Run the entire `HOSTILE_TEST_MATRIX.md` against a clean deployment and frozen release identity. Do not reuse development failures as confirmatory successes.

Allowed terminal:

```text
PRODUCTION_READY_SCOPED
SINGLE_NODE_READY_ONLY
DURABILITY_READY_CONTROL_INTEGRATION_OPEN
CONTROL_READY_DISTRIBUTED_RUNTIME_OPEN
SECURITY_OR_RECOVERY_BLOCKED
PERFORMANCE_ENVELOPE_EXCEEDED
MIGRATION_PARITY_FAILED
CANNOT_CHECK_RESOURCE_BOUND
```
