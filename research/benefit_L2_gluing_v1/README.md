# benefit_L2_gluing_v1 — frozen design for the L2 benefit experiment (PLAN.md P1.2)

Ladder obligation (research/framework_ladder/ladder.json, L2-GLUING): does retaining
obstructions prevent wrong gluings that a pairwise-only representation admits? This
is exactly Proposition prop:obstruction-blind — proved in `formal/RaklFormal.lean`
(sections `ParityObstruction`, `PairwiseNotLattice`, `ObstructionBlindness`), never
measured. Observable: wrong-gluing rate (WGR). This directory freezes the experiment
BEFORE any result exists. Execution is a separate, later step; nothing in this
directory is a result, and `ladder.json` is untouched.

The corpus instantiates the mechanized impossibility as data: every parity row
(classes G3/G4, including the three-context k=3 world of
`parity_charts_have_no_global_section`) carries a solvable twin with a byte-identical
canonical pairwise record (`covers_agree_on_pairwise_data`). By
`no_pairwise_predicate_decides_global_realizability`, any pairwise-only arm must err
at least once per twin pair; the evaluator verifies both the twin invariant and this
bound (violation ⇒ CANNOT_CHECK). The measured quantity the theorem does NOT settle
— and the run therefore certifies — is the obstruction arm's over-refusal cost (GCA
floor) and the null separations.

## Frozen here

- `PROTOCOL.json` — hypothesis; arm A (pairwise-only compatibility: the
  `TypedCompatibilityComplex` pairwise-witness semantics, obstruction fields present
  and deliberately ignored) and arm B (`rakl.atlas_gluing.evaluate_atlas_gluing` at
  the REPAIRED declared-topology semantics of PR #649 —
  `research/atlas_topology_trust_repair_v1/RECEIPT.md` — pinned by module content
  sha256 `f6f00fceda0628422d597bce06679baf872c207b922e5acac1aea86f2ca12aac`; running
  against the pre-repair module is CANNOT_CHECK); WGR estimator bound to the
  ladder.json L2 observable; GCA over-refusal floor (glueable-case acceptance
  ≥ 0.70 — obstruction retention must not win by refusing to glue); N=400 with
  power sketch and 100 mechanized twin pairs; equal-n suppression null +
  obstruction-block permutation null (stratified by topology signature); frozen
  thresholds (PROMOTE / NEGATIVE / CONDITIONAL) with one attributed revival lever
  each (global-recovery doctrine); cost matching; known_at_design_time declaration
  for the deterministic arms (for the twinned classes the direction is a theorem;
  the run certifies magnitudes, nulls, floors, receipts).
- `EVALUATOR.py` — deterministic, seeded, stdlib-only WGR/GCA/McNemar/null/twin
  machinery, including executable decision-equivalent replicas of BOTH arm rules
  with a drift check, exact exhaustive global-section search (≤ 6 binary
  variables), recomputed-topology logic mirroring the repaired atlas semantics,
  and the twin-bound check. Self-test covers the parity construction itself,
  G6-charge, no-alarm, planted-fail, twin-bound, CANNOT_CHECK, determinism worlds
  (`python3 EVALUATOR.py --selftest`, verified PASS at freeze). CANNOT_CHECK is
  exit code 3, distinct from evaluated (0). sha256
  `b237ca0c5d75d51571b6aa272e1b8dfa43e35e60b4ceda74bd035dfdabfb33dc`, embedded in
  PROTOCOL.json.
- `CORPUS_PLAN.md` — construction procedure for the known-answer atlas corpus (none
  exists in-repo; reuse scan documented). Gold global realizability is computed
  exactly from the hidden world before any arm runs; rendering-faithfulness and
  twin-record checks at generation time; no LLM labeling; 10% human audit that
  never sees arm outputs. Class G6 (glueable but obstruction-record-incomplete)
  charges arm B's fail-closed over-refusal explicitly; class G5 (pairwise
  conflicts) keeps arm A honest. Contains a 5-row worked example marked
  NON-EVIDENTIAL.

## Explicitly NOT done (design-only)

- No corpus generated, no labels minted, no arm executed, no WGR computed, no verdict.
- `research/framework_ladder/ladder.json` untouched; no framework module modified;
  the atlas-topology repair itself lives on `solver/atlas-topology-recompute`
  (PR #649) and is only PINNED here, not merged or altered by this design.
- The worked example in CORPUS_PLAN.md is illustration, not evidence.

## Execution precondition

PR #649 merged to main, or the run environment pinned to the receipted module
content hash. Either way the run receipt must record the live module's sha256 and
verify `_recompute_cover_topology` is present; a hash change beyond the receipted
repair requires a V2 re-freeze BEFORE result access.

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
