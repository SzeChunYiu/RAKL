# `INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE`

**Paper:** III  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication/papers/paper-03-method-evolution-mechanics/sections/07b_structural_learning_cautionary.tex:13`
- `publication/papers/paper-03-method-evolution-mechanics/sections/07b_structural_learning_cautionary.tex:10`

## Receipt

- **`receipt_path`:** `research/paper4_allocator_attribution_v1/README.md` — **verified present**
- supporting: `research/paper4_conceptual_absorption_v1/ABSORPTION_RECEIPT.json`
- supporting: `research/paper3_stale_feasibility_v1/FEASIBILITY_RECEIPT.json`

## What happened

A three-tier ceiling analysis showed that NO equal-budget allocation policy, however optimal, could have reached the instrument's own registered material-effect gate of 0.05: a greedy-oracle policy achieved +0.0015 (lower bound), local search found +0.0045 (lower bound), and a harm-free-relaxation upper bound caps every policy at ~0.0246 -- a factor of two below the gate. Stated with its tightness caveat, because an earlier stronger version of this bound was itself found invalid and corrected before use. Conventional power analysis was silent throughout: bootstrap intervals were ~0.0016 wide, amply 'powered' for an effect the instrument could not generate. An independent lane that tuned allocation policies on the same instrument class plateaued at the same constructive ceiling and stopped.

## One-stage attribution

instrument-construct (admissibility, distinct from falsifiability). The instrument cannot EXPRESS the effect it is gating. Manuscript: 'Falsifiability audit asks whether a gate CAN FAIL; admissibility analysis asks whether the instrument CAN EXPRESS the effect it is gating.'

## Lever

The mechanic itself is the deliverable and is specified in executable form: compute the instrument's oracle ceiling before an allocation comparison and require it to clear a pre-frozen multiple of the minimum detectable effect, emitting INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE -- and spending nothing -- otherwise, failing closed to CANNOT_CHECK when the oracle is not computable. The named open application: Paper III's own fresh-task lift protocol, whose 0.05 gate has no recorded ceiling qualification.

## Class justification

Ceiling computation is deterministic simulation over frozen worlds. Nothing hosted or accelerated is required, and the highest-value application (qualifying the Stage-4 0.05 gate) is pure local computation that gates an expensive external spend.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
