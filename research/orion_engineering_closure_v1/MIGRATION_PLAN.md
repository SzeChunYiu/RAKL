# Additive migration plan

## Principle

Do not make production engineering invalidate the scientific history it is meant to preserve.

Historical local paths, receipt IDs, hashes and benchmark fingerprints stay immutable. The new substrate imports or references them; it does not rewrite them to look native.

## M0 — Freeze

- capture exact incumbent commit and full test result;
- freeze local store fixture directories;
- hash raw fixture files;
- record v1/v2/v3 state fingerprints where applicable.

## M1 — Interface wrappers

Introduce repository protocols around existing behavior:

```text
CanonicalPayloadStore -> BlobStore adapter
Episode JSONL store -> EpisodeRepository adapter
MetricLedger/resumption envelope -> MetrologyRepository adapter
TypedKnowledgeLattice -> SemanticRepository adapter (in-memory first)
```

No data moves yet.

## M2 — Dual write

On a frozen non-production corpus:

1. execute incumbent operation;
2. write incumbent local format;
3. write new production repository in same logical operation;
4. compare identities and rehydrated semantic values;
5. refuse promotion of the backend when any coordinate diverges.

Do not use dual write for authority-bearing production state until parity is established.

## M3 — Historical import

Import existing:

- project records and content-addressed blobs;
- episode store records;
- metric/evolution receipts;
- existing research artifacts that are registered canonical evidence.

Each import batch emits an immutable import receipt containing source paths, source digests, destination IDs, counts, failures and code/schema version.

## M4 — Shadow reads

For each read surface:

```text
incumbent read -> user/controller result
production read -> shadow comparison only
```

Compare exact IDs, ordering where semantic, relation sets, saturation inputs and authority bindings. Derived retrieval rankings may differ only where an explicit ranking contract allows it.

## M5 — Restore/replay gate

Before cutover:

- restore production DB/blob store from backup into clean environment;
- replay workflow/state transitions to frozen snapshot;
- verify project head/snapshot/metric/episode/evidence identities;
- run hostile concurrency and stale-certificate tests.

## M6 — Authoritative read cutover

Switch one surface at a time. Keep rollback path and incumbent data readable until a separately frozen retirement decision.

## M7 — Retirement

A local format may be declared non-authoritative only after:

- historical import completeness is proven for registered scope;
- restore from production backup passes;
- no production consumer relies on legacy write behavior;
- compatibility readers remain for historical receipts where needed.
