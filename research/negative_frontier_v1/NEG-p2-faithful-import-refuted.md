# `registered refutation of the faithful import -- false impossibility certificates on all four repairable/open-world/budget arms`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/04_typed_refusal.tex:41`
- `publication/papers/paper-02-structural-mechanics/sections/04_typed_refusal.tex:45`
- `publication/papers/paper-02-structural-mechanics/sections/04_typed_refusal.tex:49`

## Receipt

- **`receipt_path`:** `research/paper2_causal_transport_absorption_v1/RECEIPT.json` — **verified present**
- Located by grepping for the verdict vocabulary the section uses (`CERTIFIABLY_IMPOSSIBLE`, `MERELY_UNLICENSED`) across research/ experiments/ src/, after `find -iname '*refusal*'` returned nothing -- the lane is filed under its parent's name (causal transport absorption), not under 'typed refusal'. Verified: the receipt's `arms` array carries ARM-1..ARM-8 with per-arm `challenger_A` / `challenger_B` / `ground_truth`, and the planted sweep records planted_pass_cases 178 / planted_fail_cases 178.
- supporting: `research/paper2_causal_transport_absorption_v1/PROTOCOL.json`
- supporting: `research/paper2_causal_transport_absorption_v1/AMENDMENT_01.json`
- supporting: `research/paper2_causal_transport_absorption_v1/MECHANIC_CANDIDATE.json`
- supporting: `research/paper2_causal_transport_absorption_v1/SOURCE_VERIFICATION.json`
- supporting: `src/rakl/transfer_impossibility.py`

## What happened

Eight frozen arms. Arm A, a FAITHFUL import of the completeness parent's refusal semantics, emitted a false impossibility certificate on every repairable, open-world and budget-limited arm -- all four. That is the registered refutation of the import, designed in advance as the falsifying test. Arm B, the ADAPTED gate that re-derives the strong verdict from the parent's actual preconditions, emitted no false certificate, fired the strong verdict on exactly the three witness-independent structural arms, and differed from the import on four arms; all three registered falsifiers failed to fire. Two sweeps under hard gates: a 600-case randomized proposition sweep with zero disagreements against an oracle criterion (288 with source relations, 18 discriminating via a non-canonical role mapping), and a planted known-answer sweep of 178 planted-pass / 178 planted-fail with zero failures (seed 20260814). All five hard gates passed. Verified in the receipt: ARM-1_REPAIRABLE_ROLE_MAP and ARM-3_REPAIRABLE_BOUNDARY both show challenger_A=CERTIFIABLY_IMPOSSIBLE against ground_truth=MERELY_UNLICENSED with A_correct=false and B_correct=true; ARM-4_STRUCTURAL_RELATION and its siblings show both challengers agreeing with a CERTIFIABLY_IMPOSSIBLE ground truth.

## One-stage attribution

mapping. The import failed precisely where 'the refusal cause is witness-local' -- surface analogy carried the parent's verdict without its preconditions. Manuscript: 'refusal semantics cannot be imported from the completeness parent by surface analogy'.

## Lever

Already executed and successful: the adapted typed refusal, which re-derives the strong verdict from the parent's actual preconditions, is exact on the registered design. This is the programme's clearest worked example of assimilation-by-adaptation rather than import. Open residuals the section names itself: same-context evaluation with no independent reproduction; the transfer is not peer-reviewed even though the source theorem is; and the exponential presentation-space cost means the bounded-exhaustion path must be MEASURED, not assumed, in any deployment claim.

## Class justification

A deliberately constructed refutation that already produced its successor in the same epoch. It is negative history of the IMPORT, not a live open problem -- the live residual is the unmeasured bounded-exhaustion cost, which belongs to the adapted gate.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
