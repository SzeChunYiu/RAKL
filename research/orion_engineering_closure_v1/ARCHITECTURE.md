# Target engineering architecture

## 1. Five canonical/derived planes

```text
┌────────────────────────────────────────────────────────────┐
│ 1. Evidence plane                                         │
│ exact raw bytes, datasets, code snapshots, stdout/stderr  │
│ content-addressed; checksum verified                      │
└──────────────────────────┬─────────────────────────────────┘
                           │ evidence bindings
┌──────────────────────────▼─────────────────────────────────┐
│ 2. Provenance + event plane                              │
│ ingestion/extraction/normalization/research rounds        │
│ executions/episodes/controller/evolution/audit events     │
└──────────────────────────┬─────────────────────────────────┘
                           │ state transitions
┌──────────────────────────▼─────────────────────────────────┐
│ 3. Semantic state plane                                  │
│ fibres / atoms / charts / relations / obstructions       │
│ residuals / identity-lineage / authority references      │
└──────────────────────────┬─────────────────────────────────┘
                           │ measured by exact basis
┌──────────────────────────▼─────────────────────────────────┐
│ 4. Metrology + control plane                             │
│ metric definitions/receipts, saturation certificates     │
│ hard gates, self-model, controller decisions             │
└──────────────────────────┬─────────────────────────────────┘
                           │ compile from ProjectSnapshot
┌──────────────────────────▼─────────────────────────────────┐
│ 5. Working-view plane — disposable                       │
│ target fibre / support graph / indexes / context packet  │
│ caches / dashboard materializations                      │
└────────────────────────────────────────────────────────────┘
```

A vector index, full-text index, graph projection, prompt packet or UI read model must be rebuildable from the canonical planes. Loss of a working view may cause latency or `CANNOT_CHECK`; it may not delete knowledge.

## 2. ProjectSnapshot

`ProjectSnapshot` is the consistency boundary for consequential reads. It binds the heads/revisions of:

- evidence cutoff;
- semantic state revision;
- metric ledger;
- episode store;
- saturation measurement bases;
- authority projection;
- controller epoch.

A compiled solver view and a controller decision must name the exact snapshot they observed. If the project head changes before a write, the writer replans or records a typed recovery/conflict outcome.

## 3. EpistemicStatus

`EpistemicStatus` is the canonical status read model. The controller, dashboard and audit system consume the same content-identified object.

Required coordinates:

```text
project snapshot
target + fibre
per-axis bounded flatness
recent retained novelty
independent flat route families
route required/covered/missing sets
active residuals
freshness
required authority
available support paths
blocking cuts
hard gates
next-action class
reasons
metric receipts
basis fingerprints
```

It never claims absolute completeness and never grants scientific authority.

## 4. StateTransitionReceipt

Every consequential mutation records:

```text
before snapshot
requested action
idempotency key
process identity
read/write sets
produced artifacts
metric/residual deltas
after snapshot when committed
COMMITTED / ABORTED / RETRY_REQUIRED / RECOVERY_REQUIRED / CANNOT_CHECK
reasons
```

The reference SQLite implementation uses a project-head compare-and-swap. The production repository should preserve these semantics under a stronger multi-worker transaction backend.

## 5. Database ownership

Recommended source-of-truth backend: a relational transactional store with strong constraints/versioning. Initial production implementation should use PostgreSQL-class semantics; SQLite remains a local reference backend.

Canonical metadata families:

```text
projects / snapshots
evidence_records / blob_bindings
fibres / atoms / atom_versions
relations / relation_witnesses
atlas_charts / transitions / obstructions
identity_assertions / lineage_edges
residuals / residual_events
research_rounds / novelty_events
saturation_bases / saturation_certificates
metric_definitions / metric_receipts
hard_gate_observations / controller_decisions
executions / execution_events
episodes / lessons / tools
evolution_variants / promotion_events
state_transition_receipts
```

Use foreign keys, uniqueness constraints, immutable IDs and explicit supersession/version events. Do not mutate a historical receipt to make it match a newer schema.

## 6. Canonical bytes

Preserve the existing SHA-256 raw-byte identity contract through a `BlobStore` interface:

```text
put_if_absent(bytes) -> digest
get_verified(digest) -> bytes
exists_verified(digest)
stat(digest)
```

Local filesystem and production object-storage adapters must return the same identity for the same bytes. Compression/encryption/tiering must not change raw-content identity.

## 7. Workflow execution

Separate deterministic workflow history from external activities.

A durable workflow state transition can be replayed. External activities require:

```text
stable invocation identity
idempotency key when possible
retry_safe declaration
timeout / heartbeat / lease
attempt history
terminal receipt or RECOVERY_REQUIRED
```

Do not promise distributed exactly-once side effects.

## 8. Saturation/controller/solver loop

```text
knowledge acquisition / extraction
    ↓
persist evidence + semantic delta
    ↓
new ProjectSnapshot
    ↓
recompute only affected saturation axes
    ↓
persist saturation certificate + hard gate receipts
    ↓
EpistemicStatus
    ↓
controller selects admissible next action
    ↓
compile target-conditioned solver view from exact snapshot
    ↓
solve → route OR epistemic cut / minimal repair
    ↓
persist outcome + residual transformation
    ↓
reopen implicated fibres/axes only
```

The low-level solver may inspect status metadata for planning. It may not certify that the knowledge universe is complete.

## 9. Operational observability

Propagate one immutable runtime correlation context:

```text
project_id
snapshot_id
workflow_id
activity/invocation_id
research_round_id / episode_id
target/fibre_id
evaluation_epoch_id
controller_decision_id
```

Operational traces/metrics/logs remain separate from RAKL `MetricReceipt` authority.

## 10. Security boundary

Infrastructure authorization and epistemic authority are different types.

- authentication answers who/what may invoke infrastructure;
- authorization answers which service operation is permitted;
- RAKL authority answers what scientific/control claims an artifact may support.

A privileged infrastructure identity must never mint scientific authority by being privileged.
