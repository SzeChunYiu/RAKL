# Semantic merge matrix

The rule is **KEEP / MODIFY / ALREADY ON MAIN / SUPERSEDE / GATE**, not “copy every file”.

| Input mechanism | Disposition | Integrated form / reason |
|---|---|---|
| Large hardening canonical serialization | **MODIFY** | keep typed serializer, but fix Decimal ambient-context bug, preserve exact float bits, version Unicode semantics |
| Large hardening transition kernel / receipts / workspace / scope / authority domains | **KEEP** | retained in `hardening_overlay/`; local tests green |
| Large hardening release/audit concepts | **KEEP + RECONCILE** | receiving AI must merge with current repository workflows, not replace current CI |
| Small R1 diagnosis refinement | **MODIFY** | implemented as immutable `diagnosis_state_machine.py`, separate from one-shot `mechanic_diagnosis.py` |
| Small R2 geometry nontriviality | **SUPERSEDE** | absorbed into full VTG preregistration and total-cost/constructibility contracts |
| Small R3 edge assurance | **SUPERSEDE** | `EdgeAssuranceReceipt` bound to full `OperationalSubject` |
| Small R4 reachability semantics | **SUPERSEDE** | explicit `ReachabilityQuantifier`; probability/cost fields are quantifier-typed |
| Small R5 abstraction refinement | **SUPERSEDE** | `NavigationAbstractionContract` distinguishes exact quotient / sound overapprox / empirical routing + concrete replay/refine |
| Small R6 geometry learning receipt | **SUPERSEDE** | expanded behavior-policy, support, leakage, OOD, split and reopen provenance |
| Small R7 navigation basin | **SUPERSEDE** | membership/progress/well-founded-rank/goal-minimum/boundary obligations; candidate edges forbidden |
| Small R8 amalgamation | **SUPERSEDE** | root/child hashes + overlap, substitution, assumption discharge, representation, joint obligations, invariant, root replay |
| Small E1 stale path-quotient artifact | **ALREADY ON MAIN** | current base reran against hardened state-indexed independence and charges certification cost |
| Small E2 git-archive `git rev-parse` crash | **ALREADY ON MAIN** | current base falls back to `UNKNOWN` for provenance |
| Small E3 `operational_map.add_edge` quadratic behavior | **ALREADY ON MAIN** | current base has incremental validation index |
| Small E4 missing 8-mechanics quickstart | **ALREADY ON MAIN** | current base includes quickstart smoke |
| Small E5 publication/CI staleness gates | **ALREADY/ONGOING ON MAIN** | do not reapply old workflow wholesale; verify current P3-only register |
| TCSQ source/quotient separation | **KEEP** | existing `semantic_quotient.py` is stronger than the old small patch; do not regress |
| Approximate TCSQ | **DEEPEN** | new composable approximation budget sidecar; downstream composition must be explicit |
| `StructuralWitness` directional mapping | **KEEP + DEEPEN** | preserve current set-inclusion completeness; add load-bearing non-preservation use contract |
| Neural TCSQ | **GATE** | preregister strongest matched parents; development feasibility is not RAKL residual |
| Directional witness neural transfer | **GATE** | require asymmetric scorer/transport and direction/non-preservation/boundary ablations |
| Exact external→training→inference identity reuse | **DEEPEN + GATE** | add exact identity bundle/receipt; efficacy remains fresh empirical question |
| Checkpoint-bound training projection | **KEEP + DEEPEN** | retain current proposal-only semantics; add canonical assurance sidecar and uncertainty/split binding |
| Adaptive structural allocation | **GATE** | blocked until corrected Phase-1 v2 produces valid learner-side signal |
| Cognitive compilation | **DEEPEN + GATE** | add typed proposal→training→fresh assurance→model-promotion state machine; no scientific authority movement |
| VTG / Verified Solution Universe | **INTEGRATE AS SOLVER PROJECTION** | not a parallel truth ontology; uses existing proof DAG, cost geometry, path congruence, navigation quotient, authority firewall |
| Natural/physical search dynamics | **GATE LATE** | no flow/diffusion/Physarum/path-integral experiment until useful local geometry survives Phase 1 |

## Known defect in the small packet itself

Its documented local test command exposes `proposed_modules` on `PYTHONPATH`, while its tests import `rakl.*`. That layout does not collect without additional packaging. The semantic contracts are retained here, but the old package layout is **not** copied as if it were a validated install surface.


## Additional exact-base reconciliation items discovered in the deep pass

| Item | Disposition | Reason |
|---|---|---|
| TCSQ non-finite tolerance | `PATCHED_EXACT_BASE` | `NaN`/`inf` must not satisfy bounded approximation semantics |
| TCSQ conditional forbidden loss | `PATCHED_EXACT_BASE` | forbidden information cannot be hidden behind conditional erasure |
| TCSQ passing-report trust edge | `DEEPENED` | externally resolved verifier/replay receipt required by new production sidecar |
| Scientific-evidence lineage cycles/unresolved parents | `PATCHED_EXACT_BASE` | malformed provenance cannot manufacture independent support roots |
| Cross-module experiment epoch binding | `DEEPENED` | unified manifest checks base + identity + required resolved receipts without flattening authority |
