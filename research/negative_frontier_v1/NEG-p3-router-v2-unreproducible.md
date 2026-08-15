# `CANNOT_CHECK (21-family / 2,688-case router validation is unreproducible; NOT a refutation)`

**Paper:** III  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication/papers/paper-03-method-evolution-mechanics/sections/04b_obstruction_transformation_memory.tex:71`

## Receipt

- **`receipt_path`:** `research/paper3_gate_falsifiability_audit_v1/UNREPRODUCIBLE_V2_RESULT.json` — **verified present**
- **Search scope:** For the failed-first-instrument sub-item: `grep -rln 'load.bearing' research/ experiments/` (widened from research/paper3_*/ after review) returns 15 files, none of which records a routing-validation instrument rejected for non-load-bearing mutations; the nearest hits are unrelated (MECHANIC_PROMOTION_MATRIX.json, NEAREST_WORK_AUDIT.json, STAGE4_GATE_FALSIFIABILITY_AUDIT.json). Recorded as 'could not locate', not 'absent'.
- supporting: `research/paper3_publication_validation_v2/PROTOCOL_FREEZE.json`
- supporting: `research/paper3_publication_closeout_v1/FINAL_RECEIPT.json`

## What happened

A 21-family, 2,688-case adversarial validation of the strict typed router was previously quoted for the routing plane. A repository audit found that although its protocol freeze survives, no harness, no case set and no result artifact for it exists anywhere in the repository or its history. The receipt records its own search-scope justification (git log --all -S over four v2-distinctive family tokens and the metric name; git show --stat of the single matching commit; enumeration of every file ever added under experiments/paper3/*; repo-wide grep for '2688'). Status CANNOT_CHECK, not refutation. The audit also records a structural prediction, made before any such harness exists, that the instrument shares the self-grading gold-assignment defect confirmed in the sibling harness -- its four registered thresholds sit exactly at the ceilings its metrics could not leave. The paper does not cite the numbers as evidence. Separately preserved: the FAILED FIRST validation instrument for this plane, rejected because two intended mutations were not load-bearing (receipt for that sub-item NOT located; see receipt_search_scope).

## One-stage attribution

extraction/provenance. The quoted numbers exist as written text and never as a generated artifact.

## Lever

Build the harness and case set under the frozen protocol, with gold assignment severed from the candidate (the repaired-oracle pattern of experiments/paper3/independent_action_oracle_v1.py), and re-execute. The audit's structural prediction that the old instrument was self-grading is itself a falsifiable claim the rebuild would test.

## Class justification

Deterministic typed-router validation; the protocol freeze already exists and only a harness plus case generator are missing. No model, no accelerator, no annotation.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
