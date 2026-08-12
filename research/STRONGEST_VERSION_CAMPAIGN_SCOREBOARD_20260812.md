# Strongest-version campaign scoreboard — 2026-08-12 (V2_EXEC floor after 3476813)

**Tip main at reconstruction:** `496edc5ead136980287ac2e72efb486691945366` (Paper II transport obligations v2 #491; prior #488 V4.4 ingest 3477848, #485 GLM Wave-2 offline freeze)
**Machine-readable:** `research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json`  
**Publication manifest:** `publication/PUBLICATION_SERIES_V2.json`  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED` (false)  
**Wave-2 confirmatory unlock:** **no** (terminal under current protocols)  
**GitHub issue sweep (2026-08-12):** **4 closed** (#478 #479 #459 #464) · **15 open** (#216 #442 #443 #444 #447 #455 #461 #462 #466 #467 #468 #486 #487 #489 #490)

Closed GitHub issues are historical terminals, **not** proof the scientific question was answered.

## Publication series v2 alias (campaign keys unchanged)

Legacy campaign keys (`paper_ii`, `paper_iii`, `paper_v`) remain frozen research namespaces. V2 publication numbers after #477:

| Campaign key | Legacy namespace | V2 # | V2 slug | Manuscript |
|--------------|------------------|------|---------|------------|
| `paper_ii` | `paper2*` | VI | `rakl-scientific-research-engine` | `publication/papers/paper-06-rakl-scientific-research-engine/source/main.tex` |
| `paper_iii` | `paper3*` | II | `structural-mechanics` | `publication/papers/paper-02-structural-mechanics/main.tex` |
| `paper_v` | `paper5*` | III | `method-evolution-mechanics` | `publication/papers/paper-03-method-evolution-mechanics/main.tex` |

## ORACLE chain (receipt-confirmed)

| Jobs | Verdict | Packet / PR |
|------|---------|-------------|
| 3476730 / 3476731 | `MODEL_CAPABILITY_FLOOR_0_5B` | v1.3 |
| 3476742 | `INSTRUMENT_DEFECT` | v1.3_1 |
| 3476756 | `MODEL_CAPABILITY_FLOOR_1_5B` | v1.3_1 / #349 |
| 3476778 (race 3476779) | `MODEL_CAPABILITY_FLOOR_3B` (0/3, parse 3/3) | v1.3_2 / #371 |
| **3476788** | **`MODEL_CAPABILITY_FLOOR_7B`** (1/3, parse 3/3) | v1.3_3 / #374+#378 |
| **3476813** | **`MODEL_CAPABILITY_FLOOR_7B_V2_EXEC`** (2/5, parse 5/5) | V2_0_EXEC / #383+#386 |

## Escalation

- Preregistered staircase: 0.5B → 1.5B → 3B → **7B**, then stop or revisit task/gate.
- V2 sealed-task revisit @ 7B (**3476813**) failed ≥2/3 exact-success gate (**2/5**). Threshold was not lowered after outcomes.
- **Next authorized scale: none.** No 14B/32B.
- Phase-0 / learning staircase / confirmatory Wave-2 model jobs: **unauthorized**.
- Decision: **TERMINAL_STOP__V2_EXEC_GATE_FAIL** with `CAPABLE_MODEL_AVAILABLE=NO_REFUTED`.
- Issue **#379**: close as Wave-2 terminal under current protocols. Successor only if a *pre-outcome* protocol redesign is proposed — not outcome-driven softening.

## Wave 1 lanes

| Lane | Status | PR |
|------|--------|----|
| A ORACLE | FLOOR_7B + V2_EXEC floor recorded | #354/#357/#371/#374/#378/#383/#386 |
| B ALR/A3↔A4 prep | frozen; model jobs blocked | #355 |
| C Paper-III human | BLOCKED_HUMAN freeze | #361 |
| D Paper-V novelty human | BLOCKED_HUMAN freeze | #360 |
| E active-sham | policy frozen; no confirmatory outcomes | #368 |

## Wave 2 blockers (terminal under current protocols)

1. Capable-model gate still closed (`NO_REFUTED`) after V2_0_EXEC 7B ORACLE fail (3476813: 2/5).
2. No Phase-0 RESET/FAILURE_MEMORY/VERIFIED/FULL_RAKL; no confirmatory ALR / A3↔A4 / four-arm model execution.
3. Real humans still absent for Paper III/V independent tracks.
4. Further scale shopping (14B/32B) remains protocol-illegal.

## Remaining actionable non-model lanes

These may proceed **without** a capable model. They do **not** clear `CAPABLE_MODEL_AVAILABLE` or unlock Wave-2 confirmatory model empirics.

| Lane | Status | Notes |
|------|--------|-------|
| Closest-parent / function-matched literature audit | V2 landed | `PRIMARY_SOURCE_AUDIT_V2_RECEIPT.json` — AutoSci/MemClaw/AI-scientists full text; 12 inherited / 10 residual / 1 adopt; confirmatory A3↔A4 still `CANNOT_IDENTIFY`; 3476749 non-confirmatory (upgrade-recall=0) |
| Paper-III human recruitment packet | frozen / open recruitment | `research/paper3_powered_noncircular_human_packet_v1/` (#359/#358) — `BLOCKED_HUMAN`; do not invent annotators; AI_OPERATOR demoted floors already closed |
| Paper-V independent novelty human residual | CLOSED BLOCKED_HUMAN | `research/paper5_independent_novelty_human_residual_v1/ISSUE_353_TERMINAL_RECEIPT.json` (#353) — humans absent; demoted track non-independent |
| Sham matcher unit tests | actionable | `tests/test_paper5_active_sham.py` + `research/paper5_sham_policy_v1/` — instrument-only; confirmatory four-arm binding closed as blocked (#367) |
| Honest TeX / scoreboard narrowing | actionable | Preserve negatives; no promotional lift |
| Pre-outcome protocol redesign (optional) | proposal-only / new issue | #398 closed as leftover under TERMINAL_STOP; any redesign needs a **new** versioned packet + issue, freeze before outcomes, no ≥2/3 softening after 3476813 |

## Explicitly not actionable without capable model

- ExperienceBenchmark learning / CONTENT efficacy claims
- Confirmatory ALR / A3↔A4 / Paper-V four-arm model jobs
- Phase-0 architecture staircase
- 14B/32B ORACLE without new preregistration
- Treating closed #247/#372/#379 as scientific clearance

## Capability-gated leftover closeout (2026-08-12)

Pointer receipts under `research/capability_gated_closeout_20260812/` close ORACLE/capability siblings still open after V2_EXEC GATE_FAIL:

| Issue | Disposition |
|------:|-------------|
| #398 | `TERMINAL_STOP__ORACLE_CAPABILITY_GATE_LEFTOVER` |
| #399 | `BLOCKED_CAPABILITY__CANNOT_IDENTIFY_RAKL_LEARNING` |
| #350 | `BLOCKED_CAPABILITY__CANNOT_EXECUTE_CONFIRMATORY_ALR` |
| #352 | `BLOCKED_CAPABILITY__CANNOT_IDENTIFY_A3_A4` |
| #367 | `BLOCKED_CAPABILITY__CANNOT_BIND_CONFIRMATORY_FOUR_ARM` |

Index: `research/capability_gated_closeout_20260812/CLOSEOUT_INDEX.md`. Ladder parents #247/#356/#372/#379 remain CLOSED. No 14B; no Phase-0; no gate softening.

## Fail-closed framework contract closeout (2026-08-12)

Pointer receipts under `research/fail_closed_framework_closeout_20260812/` close proposal-only contract gaps before protected integration (PR **#480**):

| Issue | Disposition |
|------:|-------------|
| #478 | `FAIL_CLOSED_CONTRACT_RESTORED` — quantifier CONDITIONAL gluing |
| #479 | `FAIL_CLOSED_CONTRACT_RESTORED` — pre-scratch MATERIALIZED requires durable ack |

Index: `research/fail_closed_framework_closeout_20260812/CLOSEOUT_INDEX.md`. No scientific authority; `CAPABLE_MODEL_AVAILABLE` unchanged.

## Framework scaffold closeout (2026-08-12)

PR **#470** (`5b583879`) landed proposal scaffolds; sweep closed as honest terminals (prospective validation / QoI stub still deferred):

| Issue | Disposition | Module |
|------:|-------------|--------|
| #459 | `SCAFFOLD_COMPLETE__PROSPECTIVE_VALIDATION_DEFERRED` | `src/rakl/quantifier_compatibility.py` |
| #464 | `SCAFFOLD_COMPLETE__QOI_NOT_VALIDATED_STUB` | `src/rakl/pre_scratch_fibre_freeze.py` |

Fail-closed contract restoration for overlapping hooks: see fail-closed closeout (#478/#479, PR #480).

## Post-sweep landings (same day, tip advancement)

| PR | Merge SHA | What landed (authority: none unless stated) |
|---:|-----------|-----------------------------------------------|
| #480 | `2834760f4ae9` | Fail-closed quantifier CONDITIONAL + pre-scratch persistence ack |
| #481 | `62e97d545f93` | Mac GLM hosted smoke runner/runbook (connectivity only) |
| #482/#483 | `ac19f760` / `8438f370` | Publication harvest + issue-sweep scoreboard |
| #484 | `53d71ea2` | Terminal receipts for #478/#479 |
| #485 | `4c5e4583` | GLM Wave-2 **offline** freeze receipts — `NO_NEW_GLM_OUTCOME`; no confirmatory GLM runs |
| #488 | `4a3b6b92` | Paper2 V4.4 LUNARC **3477848** native ingest (non-confirmatory; exact_conceptual_pass_arm_count=0 preserved) |
| #491 | `496edc5e` | Paper II executable directional transport obligations v2 (`StructuralWitnessV2`) |

### #488 ingest pointer

- Packet: `research/paper2_microtrial_v4_4/`
- Receipt: `research/paper2_microtrial_v4_4/NATIVE_INGEST_RECEIPT_3477848.json`
- Status: `research/paper2_microtrial_v4_4/NATIVE_EXECUTION_STATUS.json`
- Bundle: `research/paper2_microtrial_v4_4/native_bundles/PAPER2_V4_4_NATIVE_JOB_3477848.tar.gz`
- Do **not** resubmit redundant V4.4 confirmatory jobs against 3477848.

### #491 transport pointer

- Code: `src/rakl/structural_transport_v2.py`
- Oracle smoke: `research/paper2_transport_v2/ORACLE_CONFORMANCE_RESULT.json`
- Known-world ablation: `research/paper2_transport_v2/KNOWN_WORLD_ABLATION_RESULT.json`
- Implements #486 executable obligation semantics (proposal/code lane); does **not** clear #444 empirics.

### #461 exposure scaffold pointer

- `research/training_time_rakl_phase0_1/EXPOSURE_CURVE_HARNESS_SCAFFOLD.json` — pre-outcome harness only; no learner outcomes.

### #444 Paper III objective lane pointer

- `research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/` — directory contract + manifests; `OBJECTIVE_LANE_SCAFFOLD_ONLY`.

## Open issues after tip sync (15)

| Issue | Blocker (honest) |
|------:|------------------|
| #216 | External human reviewers — Paper I |
| #442 | Campaign coordinator — children blocked (#447 capability, #443/#444 empirics) |
| #443 | `CAPABLE_MODEL=NO_REFUTED` / Wave-2 offline freeze only (#485); no confirmatory GLM |
| #444 | Objective lane scaffolded; confirmatory items + independent humans still absent |
| #447 | Stage 0/1 defect preserved; Stage 2 challenger on PR path / tip when merged — still no `CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3` |
| #455 | Paper III training-time extension — conditional on #461 mechanism signal |
| #461 | Instrument + exposure scaffold frozen — no learner outcomes / no mechanism signal |
| #462 | Publication decision gate — conditional Structural Learning Mechanics |
| #466 | Phase 2 adaptive-vs-static — conditional on #461 |
| #467 | Phase 3 train→inference identity — conditional |
| #468 | Phase 4 generalization law — conditional |
| #486 | Transport v2 landed via #491 — close when tip contains #491 and acceptance checked |
| #487 | 2026 nearest-work threat audit — deliverables not yet written |
| #489 | Paper I adversarial epistemic-governance benchmark — not started |
| #490 | NMI-grade flagship story/evidence gate — blocked on #444/#486/#487 |
