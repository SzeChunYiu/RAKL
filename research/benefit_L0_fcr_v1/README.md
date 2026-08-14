# benefit_L0_fcr_v1 — frozen design for the L0 benefit experiment (PLAN.md P1.1)

Ladder obligation (research/framework_ladder/ladder.json, L0-OBJECT): does
context-aligned projection reduce false contradiction rate (FCR) versus naive text
comparison? This directory freezes the experiment BEFORE any result exists.

## Frozen here

- `PROTOCOL.json` — hypothesis; arm A (naive value comparison, context ignored) and
  arm B (`rakl.core.Projection`/`Context`/`compare_contexts`, FORMAL_SYSTEM_SPECIFICATION
  §5 contradiction predicate); FCR estimator bound to
  docs/RAKL_QUANTITATIVE_EVALUATION_MODEL.md §2 (coordinate V); N=400 with power
  sketch; equal-n suppression null + context-permutation null; TCR suppression guard;
  frozen thresholds (PROMOTE / NEGATIVE / CONDITIONAL) with follow-up rules
  (global-recovery: NEGATIVE and CONDITIONAL each get one attributed revival);
  cost matching (identical inputs, zero tokens both arms, time/RSS receipted).
- `EVALUATOR.py` — deterministic, seeded, stdlib-only FCR/TCR/McNemar/null machinery.
  Self-test covers no-alarm, planted-fail, CANNOT_CHECK, determinism worlds
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze). CANNOT_CHECK is exit
  code 3, distinct from evaluated (0) — never conflated with "checked and fine".
  sha256 `536ba0e21899207449de8333446fa9c67ed50b51f048f93ac68f2ba8d4afb273`,
  embedded in PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer corpus (none exists
  in-repo; reuse scan documented). Gold labels are minted by the hidden-world
  generator before any arm runs; no LLM labeling; 10% human audit that never sees arm
  outputs. Contains a 5-row worked example marked NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no FCR computed, no verdict.
- ladder.json untouched; no framework module modified.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.

## RSHEA binding for the execution run

The run must flow through the pipeline; nothing self-promotes:

1. `process_telemetry_to_receipts` (src/rakl/observability_adapters.py) — receipts for
   corpus-freeze (hash before arms), arm A run, arm B run, evaluator run.
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
