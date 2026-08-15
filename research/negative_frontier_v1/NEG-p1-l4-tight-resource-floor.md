# `both arms fail on the deliberately tight resource floor (sr_a_tight = sr_b_tight = 0.0)`

**Paper:** I (overlay branch publication-overlay-papers-123, PR #704)  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication-overlay-papers-123:publication/papers/paper-01-epistemic-mechanics/sections/06c_current_evidence_update.tex:3`

## Receipt

- **`receipt_path`:** `research/benefit_L4_navigation_v1/results_v1/evaluator_report.json` — **verified present**
- supporting: `research/benefit_L4_navigation_v1/PROTOCOL.json`
- supporting: `research/benefit_L4_navigation_v1/EVALUATOR.py`
- supporting: `research/benefit_L4_navigation_v1/README.md`

## What happened

L4 distil-and-navigate: 400 worlds, 310 primary, seed 20260814. Arm B (distil-and-navigate) solves every registered medium/loose-budget primary world (sr_b = 1.0) against sr_a = 0.3226 for budgeted lexical raw reading, McNemar p=1.2e-63 with discordant 210/0, and both null models (random acquisition q95 0.297, index permutation q95 0.290) sit far below. The reported negative half: on the deliberately tight worlds BOTH arms score 0.0 (sr_a_tight = 0.0, sr_b_tight = 0.0). The manuscript describes this as a '60-world resource floor'; the receipt records the tight-stratum solve rates but not the stratum size in its summary block, so the count is quoted from the manuscript and not independently confirmed here.

## One-stage attribution

power/resource-envelope, by construction. The tight stratum was deliberately built below the budget any arm needs; it is a designed floor, not an instrument defect.

## Lever

No repair is proposed and none is implied -- the floor is intentional. It is inventoried because it bounds the L4 positive: the mechanism's advantage does not extend to the tight-budget regime, which is precisely the regime a global-recovery claim would need.

## Class justification

Extending the mechanism into the tight-budget regime is deterministic local work on the same frozen generator. Any such attempt is a new epoch and must not rescore results_v1.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
