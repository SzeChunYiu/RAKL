# benefit_L1_composition_v1 — frozen design for the L1 benefit experiment (PLAN.md P1.2)

Ladder obligation (research/framework_ladder/ladder.json, L1-TRANSITION): does typed
composition prevent unsupported chains an untyped baseline admits? Observable:
unsupported-composition rate (UCR). This directory freezes the experiment BEFORE any
result exists. Execution is a separate, later step; nothing in this directory is a
result, and `ladder.json` is untouched.

## Frozen here

- `PROTOCOL.json` — hypothesis; arm A (untyped chaining: syntactic endpoint
  connectivity, contracts present and deliberately ignored) and arm B
  (`rakl.bridge_composition.evaluate_bridge_path`, the six licensing conditions of
  FORMAL_SYSTEM_SPECIFICATION §4, fail-closed); UCR estimator bound to the
  ladder.json L1 observable; VCA over-refusal floor (valid-composition acceptance
  ≥ 0.70 — typed licensing must not win by refusing to compose); N=400 with power
  sketch; equal-n suppression null + contract-permutation null (stratified by hop
  count); frozen thresholds (PROMOTE / NEGATIVE / CONDITIONAL) with one attributed
  revival lever each (global-recovery doctrine); module content pins for
  `bridge_composition.py` and `similarity.py`; cost matching (identical inputs,
  zero tokens both arms, time/RSS receipted); known_at_design_time declaration for
  the deterministic arms.
- `EVALUATOR.py` — deterministic, seeded, stdlib-only UCR/VCA/McNemar/null
  machinery, including executable decision-equivalent replicas of BOTH arm rules
  with a drift check (arm output ≠ replica ⇒ CANNOT_CHECK). Self-test covers
  rule-sanity, no-alarm, planted-fail, CANNOT_CHECK, determinism worlds
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze). CANNOT_CHECK is
  exit code 3, distinct from evaluated (0) — never conflated with "checked and
  fine". sha256 `f206d15610afc7fbd0cbc86e1d131f477fa4d02f638a783607b2afe45e3f580c`,
  embedded in PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer chain corpus (none
  exists in-repo; reuse scan documented). Gold supportedness is minted by the
  hidden-world generator before any arm runs; no LLM labeling; 10% human audit that
  never sees arm outputs. Class D2 (supported but record-incomplete) charges arm B's
  fail-closed over-refusal explicitly; class D7 (disconnected) keeps arm A honest.
  Contains a 5-row worked example marked NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no UCR computed, no verdict.
- `research/framework_ladder/ladder.json` untouched; no framework module modified.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.

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
