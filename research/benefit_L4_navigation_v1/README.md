# benefit_L4_navigation_v1 — frozen design for the L4 benefit experiment

Ladder obligation (research/framework_ladder/ladder.json, L4-NAVIGATION): does
navigating a distilled support structure solve more than reading raw sources at
matched total budget? The ladder names this the load-bearing open question and calls
the raw-reading comparator arm C; this protocol instantiates it deterministically as
arm A. Observable: verified solve rate (SR) at matched budget. This directory
freezes the experiment BEFORE any result exists. Execution is a separate, later
step; nothing in this directory is a result, and `ladder.json` is untouched.

## Frozen here

- `PROTOCOL.json` — hypothesis with an explicit budget-conditionality clause
  (PROMOTE applies ONLY at budgets ≥ 4·S*, classes MEDIUM/LOOSE; TIGHT is a
  registered honest-cost read outside the claim); arm A (budgeted lexical raw
  reading at 1.0/source, sharing arm B's connect rule so the contrast isolates
  acquisition ordering and cost) and arm B (`rakl.support_solver.solve`-driven
  distil→saturate→navigate→connect at 2.0/source — a deliberately conservative 2×
  distillation charge — with epistemic-cut/repair/frontier-directed acquisition);
  SR estimator over the primary set (gold SOLVABLE, MEDIUM+LOOSE, n=270) with
  world-truth route verification; FSR false-solve guard (FSR_B must be 0); SFH
  honest-cost floor (SR_B ≥ 0.70 on shallow single-hop worlds where distillation
  cannot pay off — the over-refusal analogue charged against arm B); LOOSE
  non-inferiority gate; N=400 with power sketch; equal-budget random-acquisition
  null + source-index permutation null; frozen thresholds with one attributed
  revival lever each; module content pin for `support_solver.py`; execution
  precondition noting the outstanding L4 gate-falsifiability audit (verdict capped
  at CONDITIONAL if it has not landed).
- `EVALUATOR.py` — deterministic, seeded, stdlib-only SR/FSR/McNemar/null
  machinery, including executable decision-equivalent replicas of BOTH budgeted
  acquisition policies and a faithful reimplementation of the navigation core
  (licensed Dijkstra with obstruction rejection on the assembled atom set, bounded
  relaxed enumeration, minimal repair) with a drift check (arm output ≠ replica ⇒
  CANNOT_CHECK). Declared routes are verified against the FULL world (unread
  obstructions included); hallucinated or under-licensed routes are false solves.
  Self-test covers rule-sanity (including both arms honestly falling for the
  lexical decoy first), obstruction rejection, no-alarm, planted-fail,
  CANNOT_CHECK, determinism (`python3 EVALUATOR.py --selftest`, verified PASS at
  freeze). CANNOT_CHECK is exit code 3, distinct from evaluated (0). sha256
  `2dd3726fc99354c1fe70704843ac628946cb00eeb15955747fcb8494eebe418d`, embedded in
  PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer multi-hop world
  corpus (none exists in-repo; reuse scan documented, navigation_dynamics_parallel_v1
  distinguished). Hidden support hypergraphs with buried mid-chain sources, lexical
  distractor traps, obstruction decoys, exact S* by minimal set cover, budget
  classes TIGHT/MEDIUM/LOOSE = 2/4/8·S*, and an unsolvable guard class. Gold
  solvability is minted by the generator before any arm runs; no LLM labeling; 10%
  human audit that never sees arm outputs. Contains a 5-row worked example marked
  NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no SR computed, no verdict.
- `research/framework_ladder/ladder.json` untouched; no framework module modified.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.
- The L4 gate-falsifiability audit of support_solver.py (readiness: NOT_AUDITED) is
  not performed here; it is a registered execution precondition/residual.

## RSHEA binding for the execution run

The run must flow through the pipeline; nothing self-promotes:

1. `process_telemetry_to_receipts` (src/rakl/observability_adapters.py) — receipts
   for corpus-freeze (hash before arms), arm A run, arm B run, evaluator run.
2. `MetricLedger` (src/rakl/evolution_trace.py) + `build_evaluation_epoch` +
   `process_outcome_gate` (src/rakl/observability_adapters.py) — hard gates executed.
3. `shadow_decide` (src/rakl/shadow_controller.py) on the typed verdict.
4. `interpret_controller_for_runtime` (src/rakl/self_hosting_bridge.py) —
   SELECTED → OBJECT_SEARCH_READY, never authority.
5. `surface_governed_proposal` (src/rakl/governed_intervention.py) — any
   `benefit_measured` flip in ladder.json requires external GovernanceSignOff in a
   separate PR; sign-off is continuation, never promotion.
6. `serialize_resumable_state` / `restore_resumable_state`
   (src/rakl/runtime_resumption.py); authority stays with `assess_resume_readiness`
   (src/rakl/self_hosting_runtime.py).

Editing EVALUATOR.py or PROTOCOL.json after result access voids the run
(no_post_result_threshold_rescue).
