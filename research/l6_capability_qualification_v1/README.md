# l6_capability_qualification_v1 — frozen design for the L6 capability-qualification study

Ladder obligation (research/framework_ladder/ladder.json, L6-METHOD-EVOLUTION):
the benefit obligation "fresh-task lift versus a static-method parent" is
BLOCKED_ON_CAPABILITY_QUALIFICATION — explicitly not a null. The mechanism
benefit ledger calls MECH-METHOD-EVOLUTION "the single largest benefit gap in
the programme". This directory freezes the qualification study BEFORE any
result exists: the study that decides whether a lift experiment would even be
interpretable.

## Frozen here

- `PROTOCOL.json` — the qualification question and claim boundary; the defect
  register this design avoids (L6 "gold label is the prediction" +
  thresholds-at-ceilings; the Paper III model-level experience negative's
  instrument-identifiability defect; the NON_FALSIFIABLE gate findings);
  subject binding (static-method parent, SUBJECT_FREEZE as execution
  precondition, no model shopping per the P3 frontier); the 240-task /
  12-family fresh battery with known-answer or independently-oracled scoring
  only; the instance-level freshness check against the PR #651 seed-corpus
  store at frozen head `7113f24b…`; routing-surface reachability receipts
  (store integrity + query battery + content-sensitivity flip pairs);
  eight qualification coordinates QC1–QC8 with interior frozen thresholds and
  per-coordinate justifications; typed outcomes; the paired four-arm lift
  design sketch with power calculation, matched budgets, and the
  refusal-suppression guard.
- `QUALIFICATION_CRITERIA.md` — human-readable frozen definition of
  "qualified": coordinate table with gates and registered remediation levers;
  gold-independence contract; battery decision; a 3-row worked example marked
  NON-EVIDENTIAL.
- `EVALUATOR.py` — deterministic, seeded-free (pure), stdlib-only typed-outcome
  evaluator. QUALIFIED / NOT_QUALIFIED(coordinate list, each with its
  remediation lever) / CANNOT_CHECK(typed reasons). CANNOT_CHECK is exit code
  3, distinct from evaluated (0) — never conflated with "checked and fine".
  Selftest covers a clean QUALIFIED world, one planted FAIL world per gate
  (every gate demonstrated flippable — the falsifiability countermeasure), the
  typed CANNOT_CHECK worlds, and byte-identical determinism
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze).
  sha256 `7288a8eb4ab2fe921562ef32e40e974b68f410e626a6615800efc53c48da7422`,
  embedded in PROTOCOL.json.

## Merged infrastructure this stands on (consumed, not modified)

- `src/rakl/episode_store.py` + `research/self_rakl_seed_corpus_v1/` (139
  shadow episodes, PR #651) — consumed as SHADOW only, for reachability,
  relevance and freshness receipts.
- Independent-oracle action conformance (PR #634):
  `experiments/paper3/independent_action_oracle_v1.py`,
  `research/paper3_independent_oracle_action_v1/` — its independence contract
  is reused verbatim in shape; its oracle is the family-12 gold source.
- `research/paper3_gate_falsifiability_audit_v1/` — the NON_FALSIFIABLE
  findings the successor gates here are designed to avoid.
- `research/benefit_L0_fcr_v1/` + origin/research/benefit-l0-fcr-run-v1 — the
  executed L0 benefit pattern, followed as house style.
- `research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/` (issue #447) —
  Stage-0/2 instrument discipline consumed; Stages 3–5 remain that lane's
  territory (this protocol requires their subject freeze, or an L6-specific
  one, before execution).

## Explicitly NOT done (design-only)

- No battery generated, no gold minted, no parent executed, no coordinate
  measured, no verdict produced.
- ladder.json untouched; no framework module modified; no PR opened by this
  fiber (parent gates).
- The worked example in QUALIFICATION_CRITERIA.md is illustration, not
  evidence. The evaluator selftest worlds are synthetic and non-evidential.
- Shadow episodes remain PROPOSAL_SHADOW_STORED; nothing here can upgrade
  them.

## Non-claims

Qualification ≠ lift; passing gates ≠ benefit. A QUALIFIED outcome authorizes
exactly one thing: freezing L6-LIFT-V1 as a separate protocol. NOT_QUALIFIED
is intermediate, never terminal — every failing coordinate carries a
registered improvement path (global-recovery doctrine). CANNOT_CHECK is
neither.

## RSHEA binding for the execution run

The run must flow through the pipeline; nothing self-promotes:

1. `process_telemetry_to_receipts` (src/rakl/observability_adapters.py) —
   receipts for subject freeze, battery generation (gold hash before parent
   runs), freshness check, store reachability, parent run, evaluator run.
2. `MetricLedger` (src/rakl/evolution_trace.py) + `build_evaluation_epoch` +
   `process_outcome_gate` (src/rakl/observability_adapters.py) — hard gates
   executed.
3. `shadow_decide` (src/rakl/shadow_controller.py) on the typed verdict.
4. `interpret_controller_for_runtime` (src/rakl/self_hosting_bridge.py) —
   SELECTED → OBJECT_SEARCH_READY, never authority.
5. `surface_governed_proposal` (src/rakl/governed_intervention.py) — any
   ladder.json change requires external GovernanceSignOff in a separate PR;
   sign-off is continuation, never promotion.
6. `serialize_resumable_state` / `restore_resumable_state`
   (src/rakl/runtime_resumption.py); authority stays with
   `assess_resume_readiness` (src/rakl/self_hosting_runtime.py).

Editing EVALUATOR.py or PROTOCOL.json after result access voids the run
(no_post_result_threshold_rescue).
