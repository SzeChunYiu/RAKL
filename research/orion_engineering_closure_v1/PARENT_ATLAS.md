# Strongest engineering parent atlas

The goal is assimilation, not framework replacement. Each parent supplies one local chart of the engineering object. ORION keeps stronger RAKL authority/provenance semantics where they already exist.

## P1 — Durable workflow history / Temporal-class architecture

Primary sources:

- https://docs.temporal.io/
- https://docs.temporal.io/workflow-execution
- https://docs.temporal.io/activity-definition

### Mechanic to absorb

A durable workflow execution persists state/history and reconstructs progress by replay after worker or infrastructure failure. External activities are separately retriable units.

### Critical difference witness

Temporal documentation explicitly recommends idempotent Activities because an Activity may execute more than once; a worker can finish an external action and crash before recording completion. The workflow may *observe* one completion while the side effect happened multiple times.

RAKL already has the correct semantic precursor in `RECOVERY_REQUIRED`. Preserve it.

### Transfer obligation

ORION must distinguish:

```text
workflow-state committed once under one history
!=
external effect executed exactly once
```

A production workflow adapter may use Temporal or another demonstrated durable-history engine, but it may not erase non-idempotent ambiguity.

---

## P2 — Serializable transactional metadata / PostgreSQL-class architecture

Primary sources:

- https://www.postgresql.org/docs/current/transaction-iso.html
- https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html

### Mechanic to absorb

Serializable isolation admits concurrent commits only when the result is compatible with a serial execution. Serialization failures require the application to retry the complete transaction, including the logic that selected the writes.

### Critical difference witness

A database transaction protects database state; it does not establish RAKL scientific authority and does not automatically roll back external effects.

### Transfer obligation

Consequential ORION state transitions should either:

- commit atomically against an exact project snapshot; or
- return typed conflict/retry/recovery semantics.

No last-writer-wins for semantic/saturation/controller state.

---

## P3 — Distributed observability / OpenTelemetry-class architecture

Primary sources:

- https://opentelemetry.io/docs/
- https://opentelemetry.io/docs/specs/otel/context/
- https://opentelemetry.io/docs/specs/otel/logs/

### Mechanic to absorb

Execution-scoped immutable context can propagate across boundaries and correlate traces, metrics and logs.

### Critical difference witness

OpenTelemetry operational telemetry is not RAKL scientific metrology. An OTel metric cannot silently become a `MetricReceipt`, hard gate, or evolution-evidence object.

### Transfer obligation

Every runtime trace should carry stable ORION correlation identifiers and may reference RAKL receipt IDs, while maintaining authority separation.

---

## P4 — Interoperable provenance / W3C PROV

Primary source:

- https://www.w3.org/TR/prov-o/

### Mechanic to absorb

PROV models Entities, Activities and Agents and links them through usage, generation, derivation, association and attribution.

### Critical difference witness

RAKL evidence identity is more typed than generic provenance. `IDENTICAL_TO`, `VERSION_OF`, `DERIVED_FROM`, authority layers, observation contracts and saturation-lineage identity must not collapse into one generic edge.

### Transfer obligation

Provide an export/import projection from RAKL provenance into PROV-like interoperable vocabulary. Do not make PROV the internal authority engine.

---

## P5 — Software supply-chain provenance / SLSA v1.2

Primary sources:

- https://slsa.dev/spec/v1.2/
- https://slsa.dev/spec/v1.2/provenance

### Mechanic to absorb

SLSA provenance records verifiable information about where, when and how software artifacts were produced and can bind build outputs back to source/build inputs.

### Critical difference witness

RAKL's current execution receipt can bind a declared runner/model/version but does not prove executable bytes correspond to an independently attested build artifact.

### Transfer obligation

Release/runtime identity should bind source revision, build provenance/attestation, executable digest, environment/dependency identity and deployment release identity before claiming a production assurance terminal.

---

# Parent synthesis

The compatible composite is:

```text
RAKL exact evidence + authority semantics
+ serializable canonical metadata state
+ durable workflow history/replay
+ explicit idempotency/recovery boundary
+ correlated operational observability
+ interoperable provenance projection
+ release/build provenance
```

None of the parents alone supplies the complete ORION object. The integration must be tested as a local-to-global gluing problem, including obstructions at external side effects, stale saturation, migrations and authority transport.
