# Meta-Fiber Registry Reconciliation

RAKL treats its own method registry as evidence-bearing state. A registry identifier is therefore not merely a label: ambiguity in fiber identity can corrupt ownership, supersession, closure, and saturation accounting.

## Identity rule

A meta-fiber has two separate identity surfaces:

1. the full identifier, for example `META_N104_EXPLANATION_DEPTH_CHALLENGE`; and
2. the numeric namespace slot, for example `META_N104`.

Distinct concepts may not silently occupy the same numeric slot. Likewise, reusing the same full identifier for materially different questions is a definition conflict.

Semantic similarity is not identity. The same principle used by GLUE applies recursively to RAKL itself: two records may only be treated as one fiber through an explicit, provenance-bearing reconciliation relation. A language model may propose that relation; the registry validator never infers it from names or descriptions.

## Explicit reconciliation

A collision may be repaired by introducing a new collision-free canonical identifier and a predeclared alias from the historical identifier to that new identifier. The original record remains immutable negative/history evidence. The alias does not rewrite the old source and does not grant scientific, method, target, or saturation authority.

The support layer distinguishes:

- `CONSISTENT`;
- `CONSISTENT_WITH_RECONCILIATION_HISTORY`;
- `CONFLICTED`;
- `CANNOT_CHECK`; and
- `TRIAL_INVALID`.

It checks full-ID definition conflicts, numeric-slot reuse, source-identity conflicts, undefined references, alias and supersession cycles, missing alias targets, and alias chronology. Input order is normalized so the report is deterministic.

## External projections

The design is intentionally conservative and is not claimed as a novel identifier system. W3C PROV distinguishes entities, revisions, specializations, and provenance bundles; its cross-bundle work notes that a URI alone does not identify a particular description in a particular provenance context. DataCite uses explicit version relations such as `IsNewVersionOf`/`IsPreviousVersionOf` rather than silently replacing version identity. OBO Foundry requires stable, uniquely mapped ontology identifiers. RAKL imports the narrower lesson that identity, version/revision, aliasing, and provenance must remain explicit.

## Current live collision

Round 033 canonically defined `META_N101` through `META_N106` for metacognitive fibers. Round 034 later reused the same numeric slots for six distinct senior-researcher architecture concepts. Round 035B preserves both source artifacts and reconciles the later concepts onto collision-free slots `META_N108` through `META_N113`. `META_N100_RESEARCH_AGENDA_AND_SCIENTIFIC_TASTE` and `META_N107_DUAL_HEADLINE_REAL_EXPERIMENT_PROGRAM` remain unchanged because those slots were not previously allocated in the registered sequence.

The repair closes the observed collision. It does not yet prove that every historical backlog/delta file can be automatically compiled into one authoritative registry; that broader compiler remains an open child of `META_N069_META_FIBER_REGISTRY_RECONCILIATION`.
