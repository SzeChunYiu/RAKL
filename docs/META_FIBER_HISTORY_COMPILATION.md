# Historical meta-fiber ledger compilation

RAKL treats its meta-fiber history as an append-only evidence object rather than a mutable list of names. The active compiler is `rakl.meta_history.compile_meta_fiber_history`.

## Identity contract

A numeric namespace slot such as `META_N091` is a representation coordinate, not sufficient evidence that two full identifiers denote the same method object. Canonical identity is reconstructed from immutable declaration/update/reference events plus explicit source-scoped reconciliations. Semantic similarity never auto-merges identities.

The compiler automatically discovers `research/META_FIBER_BACKLOG*.json` and `research/META_FIBER_REGISTRY_RECONCILIATION*.json`. A reconciliation may additionally bind an exact historical source only after its Git blob identity matches the bytes currently in the repository. Forward aliases are source-scoped: fixing one historical occurrence never rewrites every equal-looking string globally.

## Legacy schemas

Immutable history contains several serialization forms. The compiler accepts only observed structural witnesses:

- `fiber_id` under declaration containers such as `items`, `fibers`, and `new_fibers`;
- legacy `id` under the explicit `new_fibers` container;
- a first otherwise-undefined full identifier carrying an explicit `problem`, `question`, or `purpose` as its declaration;
- ordinary state/update records as updates, not new identities.

Unknown contract-bearing shapes fail closed as `CANNOT_CHECK`. A missing definition remains an orphan unless a later reconciliation supplies either a verified canonical identity mapping or an explicit non-retroactive orphan disposition.

## Obstructions remain evidence

Namespace collisions, orphan references, source-identity mismatches, malformed artifacts, ambiguous reconciliation scope, and chronology errors are retained in the issue ledger. Reconciliation changes only the issue's resolution state; it does not erase the historical failure.

Round 041 exposed a second real namespace collision: Round 027/027B had already allocated N091/N092 to post-promotion ref-state attestation and PR executed-subject binding, while Round 030 later reused those slots for scoped self-evolution evidence and adaptive assurance reserve. The later concepts are now reconciled forward to N123/N124. The earlier N091/N092 identities remain canonical and unchanged.

Two long priority-list tokens were also found to be historical scope qualifiers rather than independently defined fibers: `META_N024_INTEGRATION_SUBJECT_IDENTITY_WORKFLOW_ACTIVATION` and `META_N015_CLAIM_EVIDENCE_PROVENANCE_REAL_UTILITY`. They are preserved as resolved orphan-history entries; no retroactive fibers were invented.

## Authority boundary

A clean historical ledger may support registry bookkeeping. It cannot by itself grant scientific truth, target authority, method promotion, independent-review credit, or framework-saturation authority.

## Reopen triggers

Reopen the compiler if a canonical fiber is intentionally declared in a new machine-readable schema the parser cannot classify, if canonical declarations move outside the registered ledger plane, if a new source-scoped collision/orphan appears, or if a simpler deterministic representation can preserve the same hostile-world guarantees at lower complexity.
