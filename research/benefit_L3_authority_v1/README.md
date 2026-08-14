# benefit_L3_authority_v1 — frozen design for the L3 benefit experiment

Ladder obligation (research/framework_ladder/ladder.json, L3-AUTHORITY): does the
authority boundary reduce unsupported authority upgrades versus an ungoverned arm?
Observable: ALR (authority-leak rate). This directory freezes the experiment BEFORE
any result exists. Execution is a separate, later step; nothing in this directory is
a result, and `ladder.json` is untouched.

## Frozen here

- `PROTOCOL.json` — hypothesis; arm A (ungoverned upgrade: syntactic evidence-id
  resolution, evidence-record content present and deliberately ignored) and arm B
  (`rakl.evidence_binding_certificate.evaluate_evidence_binding_for_promotion`
  feeding `rakl.authority_ledger.AuthorityLedger.commit_verified`; UPGRADE only on
  VALID_FOR_PROMOTION_CHALLENGER, fail-closed); ALR estimator bound to the
  ladder.json L3 observable; VUA over-refusal floor (valid-upgrade acceptance
  ≥ 0.70 — the boundary must not win by starving legitimate promotion); N=400 with
  power sketch; equal-n suppression null + evidence-record-permutation null
  (stratified by binding arity, canonical positional ids re-stamped); frozen
  thresholds (PROMOTE / NEGATIVE / CONDITIONAL) with one attributed revival lever
  each (global-recovery doctrine); module content pins for all six load-bearing
  arm-B modules; cost matching (identical inputs, zero tokens both arms, time/RSS
  receipted); known_at_design_time declaration for the deterministic arms; an
  explicit non-target note fencing off the separate assess_transfer_v2 fail-open
  defect (this experiment neither uses nor excuses it).
- `EVALUATOR.py` — deterministic, seeded, stdlib-only ALR/VUA/McNemar/null
  machinery, including executable decision-equivalent replicas of BOTH arm rules
  with a drift check (arm output ≠ replica ⇒ CANNOT_CHECK) and the identity
  re-stamping transplant the permutation null requires. Self-test covers
  rule-sanity, no-alarm, planted-fail, CANNOT_CHECK, transplant, determinism
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze). CANNOT_CHECK is
  exit code 3, distinct from evaluated (0) — never conflated with "checked and
  fine". sha256 `3be90012a5c3179e899e505e65b4a098610128e104199d68fd759edd4ce61a4b`,
  embedded in PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer upgrade corpus
  (none exists in-repo; reuse scan documented). Gold supportedness is minted by the
  hidden-world generator before any arm runs; no LLM labeling; 10% human audit that
  never sees arm outputs. Class A2 (supported but record-unverifiable) charges arm
  B's fail-closed over-refusal explicitly; class A7 (dangling ids) keeps arm A
  honest; classes A3–A6 realize the invalid-upgrade temptations and lineage-broken
  decoys (tamper, root collapse, experience-as-science, scope leak, axis leak).
  Contains a 5-row worked example marked NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no ALR computed, no verdict.
- `research/framework_ladder/ladder.json` untouched; no framework module modified.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.
- The assess_transfer_v2 fail-open (ladder L3 readiness evidence) is not touched.

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
