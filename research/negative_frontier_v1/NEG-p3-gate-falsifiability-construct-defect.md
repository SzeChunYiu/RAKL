# `NON-FALSIFIABLE -- four of six registered gate conditions satisfied by identity`

**Paper:** III  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-03-method-evolution-mechanics/sections/07a_current_precursor_result.tex:16`

## Receipt

- **`receipt_path`:** `research/paper3_gate_falsifiability_audit_v1/GATE_FALSIFIABILITY_AUDIT.json` — **verified present**
- supporting: `research/paper3_gate_falsifiability_audit_v1/REPAIRED_GATE_FALSIFIABILITY_AUDIT.json`
- supporting: `research/paper3_gate_falsifiability_audit_v1/INTERPRETATION_NARROWING.json`
- supporting: `experiments/paper3/independent_action_oracle_v1.py`

## What happened

A frozen 1,792-case / 14-family minimal-twin benchmark compared typed selective experience against RESET, failure-memory-only, scalar-confidence, provenance-only, untyped whole-state and their strongest composite projection. The governance audit found the harness assigned the gold action and the candidate prediction from the same pure function on the same argument, so exact action accuracy, unsafe-apply rate, CANNOT_CHECK recall and legitimate-apply recall were satisfied BY IDENTITY and could not fail under any perturbation (a black-box probe battery left all four unmoved in 32/32 trials per probe while the two live conditions moved under identical probes). Those four numbers are not reported as candidate measurements.

## One-stage attribution

instrument-construct. Self-grading gold assignment: gold and candidate share one pure function.

## Lever

Already executed. The successor severs gold from candidate via an independently implemented declarative oracle (experiments/paper3/independent_action_oracle_v1.py, statically audited to neither import nor reference the candidate) assigning gold after case freeze on a fresh 2,400-case stratified panel. REPAIRED_GATE_FALSIFIABILITY_AUDIT.json returns FALSIFIABLE on all eight evidence-dependent conditions, with a re-planted self-grading variant reproducing the historical NON-FALSIFIABLE signature and a doctored oracle failing the independence audit.

## Class justification

'The original receipt is preserved verbatim as negative instrument history.' The repair is a separate epoch and is already shipped. What the old benchmark VALIDLY measured (the information-sufficiency / projection-lossiness separation) is retained.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
