# `NULL (MECH-BOUNDED-SATURATION solve-enablement ablation)`

**Paper:** I (overlay branch publication-overlay-papers-123, PR #704)  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication-overlay-papers-123:publication/papers/paper-01-epistemic-mechanics/sections/06c_current_evidence_update.tex:7`

## Receipt

- **`receipt_path`:** `research/orion_saturation_solve_enablement_v1/receipts/results_v1.json` — **verified present**
- supporting: `research/orion_saturation_solve_enablement_v1/RESULT_V1.md`
- supporting: `research/orion_saturation_solve_enablement_v1/PROTOCOL.json`
- supporting: `research/orion_saturation_solve_enablement_v1/receipts/gate_audit.json`
- supporting: `research/mechanism_benefit_ledger/ledger.json`

## What happened

Non-circular downstream benefit attempt on 112 held-out Mathlib theorem-proving tasks under Lean adjudication. Solve rate 0.357 (saturation arm A, 2256 rounds) vs 0.3125 (matched-budget uniform arm B, 2240 rounds); discordant 8 vs 3; exact McNemar two-sided p=0.2266. Verdict: NULL -- the benefit column does not gain an entry. Mean gold coverage was essentially equal (0.342 vs 0.349), so the arms were genuinely matched.

## One-stage attribution

capability/benefit. The mechanic runs and the design check is clean (no censoring at schedule end, no degenerate single-valued rounds); the downstream solve-enablement effect is simply not resolvable at n=112.

## Lever

'Its frozen revival remains a separate epoch; the original result is not reclassified' (06c:7). The receipt itself is honest that the substituted anchor is 'Mathlib-level lemma proving, not frontier mathematics' and that the operator's stated target is not met and not claimed.

## Class justification

Lean-adjudicated Mathlib tasks run locally and deterministically; a larger held-out set or a sharper retrieval-budget contrast is pure local compute. The original artifact is immutable; the revival is a new epoch.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
