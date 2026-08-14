# benefit_L5_saturation_v1 — frozen design for the L5 benefit experiment

Ladder obligation (research/framework_ladder/ladder.json, L5-SATURATION): does
stopping on the saturation rule beat stopping arbitrarily at matched budget?
Observable: set-completeness IoU, plus budget saved. This directory freezes the
experiment BEFORE any result exists. Execution is a separate, later step; nothing in
this directory is a result, and `ladder.json` is untouched.

## Frozen here

- `PROTOCOL.json` — hypothesis; arm A (budget-exhaustion stopping at the frozen
  T_MAX = 24 rounds — the strongest honest comparator for a completeness
  observable; arbitrary stopping at matched budget is realized rigorously as
  null 1) and arm B (`rakl.epistemic_saturation.audit_bounded_epistemic_saturation`
  with required_consecutive_flat_rounds = 2, applied incrementally; collection
  machinery identical across arms so every difference is a stop-time difference);
  IoU/completeness estimators bound to the ladder.json L5 observable; the exact
  frozen PROMOTE conjunction the obligation demands (completeness loss confidently
  < 0.05 by exact one-sided binomial at p < 0.001 with no offset credit, mean IoU
  deficit ≤ 0.02, mean budget saved ≥ 0.10 with strict saving on ≥ 50% of worlds,
  equal-budget superiority via null 1); premature-stop floor on the late-complete
  class (C_B ≥ 0.70 on S3 — the over-refusal analogue charged against arm B);
  zero-early-stop guard on the uncertifiable-basis class; bare-flatness attribution
  gate (the audit's non-flatness conjuncts must beat flat-counting by ≥ 0.10 on the
  trap class, making the L5 mechanism itself load-bearing); N=400 with power
  sketch; budget-permutation null + round-signal permutation null; frozen
  thresholds with one attributed revival lever each; module content pin for
  `epistemic_saturation.py`.
- `EVALUATOR.py` — deterministic, seeded, stdlib-only IoU/completeness/savings
  machinery, including executable decision-equivalent replicas of BOTH stop rules
  and the bare-flatness ablation, with a drift check (arm stop ≠ replica ⇒
  CANNOT_CHECK). Self-test covers rule-sanity, trap-attribution (full audit
  survives the false-flat window, bare flatness demonstrably does not), the
  uncertifiable-basis guard, no-alarm, planted-fail, CANNOT_CHECK, determinism
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze). CANNOT_CHECK is
  exit code 3, distinct from evaluated (0). sha256
  `b3e739d8b8a02121d11568f2de718bea6cdacbbbb888d8f0e074db49b83fec7f`, embedded in
  PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer stream corpus
  (none exists in-repo; reuse scan documented, p5_p6_saturation_v1 distinguished).
  Finite relevant-fact basis + distractor stream as world facts; truthful per-round
  audit-gate facts (during a false-flat trap window, bounded discovery is genuinely
  open); classes covering standard/early/late completion, the false-flat trap,
  repeat-heavy dedup stress, and the uncertifiable basis. Gold basis and completion
  round are minted by the generator before any arm runs; no LLM labeling; 10%
  human audit that never sees arm outputs. Contains a 5-row worked example marked
  NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no IoU computed, no verdict.
- `research/framework_ladder/ladder.json` untouched; no framework module modified.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.
- The audit's freshness-horizon channel (required_freshness_cutoff) is deliberately
  unexercised in V1; it is the pre-registered CONDITIONAL revival lever.

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
