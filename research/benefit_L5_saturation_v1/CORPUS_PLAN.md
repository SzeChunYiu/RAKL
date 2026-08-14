# CORPUS_PLAN — BENEFIT-L5-SATURATION-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for
`saturation corpus`, `set-completeness`, `IoU`) found no labeled stopping-rule
corpus. `research/p5_p6_saturation_v1/` is a research-packet study (packets/results,
no gold-labeled stream population); Self-RAKL ledger hits are unrelated; unit tests
exercise `audit_bounded_epistemic_saturation` on worked fixtures only.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples hidden
worlds and renders 24-round retrieval streams. Ground truth lives in the hidden
world, not in any arm's decision rule.

1. **Hidden world.** A finite relevant-fact basis F* of 6–14 canonical fact ids
   drawn from 8 synthetic retrieval families (literature sweeps, sensor-log sweeps,
   registry crawls, archive scans — invented parameterizations, no external data);
   a delivery schedule assigning each basis fact a first-arrival round; a distractor
   stream (items with no fact id); repeat/paraphrase items re-delivering an
   already-seen canonical fact id; and truthful per-round audit facts: whether
   bounded discovery is genuinely closed at that round (all routes of the declared
   family exhausted), route-coverage stability, omission/nearest-work audit
   outcomes, operator-order stability, and open blocking fibers.
2. **T_MAX = 24 rounds for every world** (frozen; makes the budget-permutation null
   well-defined). t_complete = the round at which the last basis fact arrives.
3. **World sampling by class** (composition frozen in PROTOCOL.json, N=400):
   - **S1 (140)** STANDARD: t_complete ~ mid-stream (rounds 8–16), gate facts turn
     true once discovery genuinely closes, long distractor tail. Savings available.
   - **S2 (60)** EARLY_COMPLETE: t_complete ∈ rounds 3–6. Maximal savings potential.
   - **S3 (60)** LATE_COMPLETE: t_complete ∈ rounds 21–23. Savings ≈ 0 by
     construction; the premature-stop floor class (stopping early here loses the
     basis; C_B on S3 ≥ 0.70 is a frozen PROMOTE gate).
   - **S4 (60)** FALSE_FLAT_TRAP: an interior window of ≥ 2 consecutive
     zero-growth rounds BEFORE t_complete, during which
     `bounded_discovery_closed` is genuinely false (unexhausted routes remain —
     the world fact the audit's non-flatness conjuncts read). Basis facts arrive
     after the trap. The discriminating class: bare flat-counting stops in the
     trap; the full audit does not. Feeds the frozen attribution gate.
   - **S5 (40)** REPEAT_HEAVY: after t_complete the stream re-delivers paraphrases
     of seen facts (same canonical id) plus distractors. Tests that growth is
     semantic (retained-new-after-dedup), not item-count; savings available.
   - **S6 (40)** UNCERTIFIABLE_BASIS: relevant facts keep arriving through round 24
     and bounded discovery never closes. Correct behavior: never certify
     saturation, save nothing. Any early stop on S6 is a frozen hard fail.
4. **Record schema.** `world_id`, `class`, `gold_basis`, `t_complete` (null for S6),
   `label_minted_at` (UTC ISO, written at generation), `rounds` (24 ×
   {new_fact_ids, other_substantive_updates, gates{bounded_discovery_closed,
   route_coverage_stable, omission_audit_passed, nearest_work_audit_passed,
   operator_order_stable}, blocking_fibers}), `generator_seed`. Rendered gate facts
   are truthful projections of the hidden world — never tuned to any stop rule.
5. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (`process_telemetry_to_receipts`) BEFORE any arm executes. Arm harnesses receive
   a copy stripped of `gold_basis` and `t_complete`. EVALUATOR.py enforces
   label-before-arm chronology and the stop-rule drift checks.

## Label-independence safeguards

- Gold = pure function of the hidden world at generation time. No arm, LLM, or human
  prediction participates. (Structural counter to the L6-gate defect.)
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase item
  surface text; it never sees or writes `gold_basis`, `t_complete`, canonical fact
  ids, or gate facts, and an exact-match guard verifies canonical ids survive
  verbatim. Any violation drops the row.
- **Human/oracle audit.** 40 worlds (10%) sampled by seed. The auditor sees only the
  rendered stream + the gold basis/completion round — never arm outputs
  (`auditor_saw_arm_outputs: false`). Disagreement ≥ 0.05 ⇒ CANNOT_CHECK.

## A-priori expectations (deterministic arms; recorded to make the design honest)

Arm A stops at 24 everywhere: complete on S1–S5, complete on S6 up to what the
stream delivered, savings 0. Arm B is expected to stop ≈ t_complete + 2 on
S1/S2/S5 (savings ≈ 0.25–0.75), ≈ 24 on S3 (savings ≈ 0, floor holds), survive the
S4 trap via the gate conjuncts (bare flatness demonstrably does not), and never stop
early on S6. Directionally: non-inferior completeness, mean savings well above 0.10,
attribution delta on S4 large. These are expectations, not results; exact magnitudes,
nulls, and receipts are what the run certifies.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | stream (rendered gist) | world fact | correct stop behavior |
|---|---|---|---|
| S1 | basis of 8 facts lands by round 11; rounds 12+ distractors, gates true from 12 | discovery closed at 12 | stop ≈ 13 |
| S2 | basis of 6 facts lands by round 4 | discovery closed at 5 | stop ≈ 6 |
| S3 | last basis fact arrives round 22 | discovery open till 22 | stop ≈ 24 |
| S4 | flat rounds 7–9 with `bounded_discovery_closed=false`, facts resume round 10 | trap window not closed | do NOT stop in trap |
| S6 | new facts through round 24, closure never true | basis uncertifiable | never stop |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
