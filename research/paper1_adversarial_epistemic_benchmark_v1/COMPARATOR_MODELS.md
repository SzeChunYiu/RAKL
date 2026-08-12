# Comparator state models (#489)

Status: `PROJECTION_SUFFICIENCY_IMPLEMENTED__BEHAVIOURAL_RESPONDERS_PENDING`

The first implemented comparison is deliberately architectural rather than behavioural. Each comparator receives the **strongest fair canonical state projection compatible with its abstraction**. The question is whether that representation preserves enough information to distinguish minimal-twin scientific worlds that require different canonical updates. This does not ask an LLM to infer coordinates the architecture does not store.

| ID | Model | Frozen projection in v1 |
|----|-------|-------------------------|
| A | TEXT_MEMORY_ONLY | transition type, retrieval count, salience, scalar confidence, active/version |
| B | PROVENANCE_ONLY | transition type, clean lineage, root count/independence, active/version |
| C | SCALAR_CONFIDENCE | transition type, scalar confidence, active/version |
| D | PAIRWISE_COMPATIBILITY_ONLY | transition type, pairwise compatibility, active/version |
| E | MAJORITY_OR_REVIEWER_VOTE | transition type, vote counts, active/version |
| F | SIMPLE_TRANSACTIONAL_STATE | transition type, active/version, provenance/root count, supersession |
| G | RAKL_TYPED_AUTHORITY | all registered typed coordinates in the twin panel |

Implementation: `src/rakl/epistemic_projection_benchmark.py`.

Result: `PROJECTION_SUFFICIENCY_RESULT_V1.json`.

## Fairness / claim boundary

This benchmark proves only an information distinction on the constructed minimal-twin panel. If a projection maps two worlds requiring different actions to the same state, no deterministic policy over that projection can be correct on both. It does **not** show that a language model given unrestricted raw prose could not infer the missing scientific fact, nor that RAKL is empirically superior on natural research tasks.

Behavioural implementations of these comparator architectures remain a later #489 coordinate and must be evaluated on the already-existing hidden-label authority panels without weakening their abstraction or giving RAKL privileged answer-bearing information.
