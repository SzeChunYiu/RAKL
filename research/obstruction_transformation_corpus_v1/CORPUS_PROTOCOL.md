# Obstruction–Transformation Episode Corpus Protocol v1

**Issue:** #402  
**Status:** `TRANSFORMATION_MEMORY / PROVENANCE_FIRST / COVERAGE_MEASURED / NO_SYNTHETIC_AUTHORITY`  
**Ontology:** frozen before seed collection (`ONTOLOGY_VERSION.json`)

## Unit of storage

```text
O = relational obstruction (structural fingerprint)
T = transformation under explicit preconditions
O' = observed/verified changed relations
```

## Authority

| Class | Meaning |
|-------|---------|
| PROPOSAL_ONLY | Default for synthetic/generated/model-summarized candidates |
| SOURCE_EVENT_VERIFIED | Underlying source checked for exact O/T/O' |
| VERIFIED_LOCAL | In-repo/local event with verification receipt |
| PROOF_BACKED | Proof binds the transformation effect |
| SUPERSEDED | History/negative; not a strict viable route |

Synthetic candidates **cannot** become strict verified SEARCH/JUMP routes by default.

## Phases covered by this seed release

0. Ontology/identity/authority/provenance/hash/leakage rules frozen  
1. Heterogeneous seed lanes populated (structural diversity, not equal paper counts)  
2. Two-stage extraction pattern recorded; only local RAKL events verified in v1  
3. Structural dedup/equivalence report emitted  
4. Coverage metrology emitted (scoped to registered source universe)  
5. Disjoint splits frozen for #401 (`SPLIT_MANIFEST.json`)  
6. Retrieval metrics registered but **not** scored confirmatory here (#401 owns efficacy)

## Non-claims

- Not complete knowledge  
- Not theorem/scientific authority  
- Not #401 confirmatory efficacy  
- Proposal-only episodes guide search only
