# RUN_RECEIPT — BENEFIT-L2-GLUING-V1 execution run (results_v1)

Executed 2026-08-14 against the frozen protocol merged in PR #658
(`origin/main@90589790`, which also carries the PR #649 repaired
`atlas_gluing.py`). Typed outcome: **PROMOTE** (frozen evaluator, exit 0).

## Environment

- Host: macOS 26.4 (Darwin 25.4.0), Apple Silicon; Python 3.13 (system `python3`).
- No network access used by generator, arms, or evaluator (stdlib + `src/rakl` only).
- Local scope honored: generator/arms/evaluator only; no xdist, no full test suite.
- Worktree: isolated git worktree of /Users/billy/RAKL, branch
  `research/benefit-l1-l2-runs-v1` from `origin/main@90589790`.

## Seeds

- Registered seed **20260814** used for: corpus generator (single
  `random.Random` stream), audit sampling, and `EVALUATOR.py --seed`.
- No other randomness sources.

## Pin verification (all BEFORE any execution, re-verified inside every step)

- `EVALUATOR.py` frozen hash in PROTOCOL.json:
  `b237ca0c5d75d51571b6aa272e1b8dfa43e35e60b4ceda74bd035dfdabfb33dc` — computed
  in the run environment: **MATCH**.
- Module pin (PROTOCOL.json arms.B.module_pins): `src/rakl/atlas_gluing.py`
  `f6f00fceda0628422d597bce06679baf872c207b922e5acac1aea86f2ca12aac` — **MATCH**
  (the PR #649 repaired content, now merged to origin/main, so the pin
  provenance's "NOT yet on origin/main" caveat is resolved with the SAME hash;
  no semantic re-verification beyond the receipt's described repair was needed).
- Semantic precondition of the pin rule: `_recompute_cover_topology` present in
  the run-environment module — **VERIFIED** (checked at every step).
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: parity-construction, g6-charge, no-alarm, planted-fail,
  twin-bound, cannot-check, determinism` (exit 0).

## Execution chronology (all UTC)

1. 17:13:00 — corpus generated, labels minted (`label_minted_at`) by exact
   exhaustive satisfiability of the rendered constraint tables, class invariants
   checked over all 400 atlases (PASS — including rendering faithfulness,
   pairwise-flag honesty, holonomy-flag honesty, twin byte-identity, and the
   simple-cycle witness-path invariant), corpus + gold-stripped copy + audit
   sample + hidden-world dump written, sha256 receipts entered into the RSHEA
   chain (`rshea/receipts_step1.json`, epoch `epoch:f12417658669d881`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 17:13:52 — label audit: 40 seed-sampled atlases read in full (surface text +
   gold only; no class or twin fields), each label cross-verified against the
   printed chart tables (assignments row-by-row, disjoint overlaps, cycle
   parity), 0 disagreements. No arm output existed yet
   (`auditor_saw_arm_outputs: false`).
3. 17:14:08 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus.
4. 17:14 — frozen evaluator with `--seed 20260814`; exit 0; verdict PROMOTE
   (twin invariant byte-verified on 100 pairs; impossibility bound held).
   RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | declarations | GLUE declared | wall clock | peak RSS | tokens |
|-----|--------------|---------------|-----------|----------|--------|
| A   | 400          | 340           | 0.00012 s | 32,276,480 B | 0 |
| B   | 400          | 200           | 0.01813 s | 33,046,528 B | 0 |

Identical inputs (stripped corpus sha256 `12963ac4…f3644c`); arm B's extra
holonomy + exhaustive existence computation is the treatment under test and is
charged above; denominator fixed at N=400 for both arms; refusals counted in
the denominator.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (G1=100, G2=100, G3=60,
G4=40, G5=60, G6=40; 100 twin pairs), registered seed, arm A verbatim to the
frozen pairwise rule, arm B driving the exact pinned
`rakl.atlas_gluing.evaluate_atlas_gluing`, both nulls at 1000 draws, McNemar
exact two-sided, twin bound enforced by the frozen evaluator.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any freeze
  or result access), on corpus-quality grounds: 7 cyclic templates (4 triangle
  + one each k=4/5/6, parity families with their even-parity twins and the G6
  rows sharing cells) and 4 acyclic PATH templates (G1/G5). Surface identities
  are drawn from seeded per-TEMPLATE banks shared by every row of a cell — this
  realizes CORPUS_PLAN's "seeded-permuted so surface form carries no class
  signal" (all classes in a cell share names) while keeping the frozen
  obstruction-permutation null's topology-signature strata populated and mixed
  (per-row unique names would collapse every stratum to one row and degenerate
  the null to all-zero draws — the L2 analogue of L0's standard-context-tuple
  reuse). Tree covers are paths so the declared transition set is exactly the
  variable-sharing structure (no undeclared overlaps).
- **Arm B computes its own obstruction inputs from the rendered record, never
  from gold** (documented in `harness/arm_harness.py`): cover topology
  recomputed with the module's own multigraph semantics and declared
  truthfully; witness `composition_consistent` = the arm's own holonomy
  computation (joint satisfiability of the cycle-path charts' rendered tables);
  `global_exists` = exhaustive assignment search over all rendered tables;
  uniqueness recorded as unchecked (gold concerns existence). The generator
  guarantees the record's holonomy flag equals cycle-chart satisfiability, so
  the module arm and the frozen record-reading replica agree; the evaluator's
  drift check confirmed decision-equivalence on all 400 real atlases (exit 0).
- **Pre-freeze fixture sweep finding:** on a degenerate back-and-forth witness
  walk (XY→YZ→XY) the repaired module is STRICTER than the frozen replica (its
  GF(2) cycle-rank check refuses where the replica's simpler path check glues).
  Resolved BEFORE any freeze by adding a generator invariant (witness paths
  must be simple closed cycles), keeping the two decision-equivalent on the
  entire corpus family; recorded as a typed residual for a V2 replica
  tightening. Fixture validation used SYNTHETIC triangles/paths only — never
  corpus rows; the frozen corpus is the first and only corpus any arm ever saw.
- **RSHEA wiring detail:** as in the L0/L1 runs, the shadow controller's
  status-quo action carries the latest (evaluator-step) receipts; the full
  12-receipt chain remains in the MetricLedger.

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:f12417658669d881`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l2-gluing-v1-run-1`, **not
  actionable** (no external `GovernanceSignOff` exists; sign-off would be
  continuation, never promotion).
- `serialize_resumable_state`/`restore_resumable_state`: envelope written and
  restored; content hashes verified round-trip.
- Authority remains with `assess_resume_readiness`; not invoked (no resume or
  archive change attempted). **ladder.json untouched.**

## Artifact hashes

See `freeze_manifest.json` (pre-arm freeze) and `RESULTS.json`
`corpus_hash_receipts` (full set including post-run outputs).

## Residuals (typed)

1. **AUDIT-INDEPENDENCE** — audit performed by the same-context session agent
   (mechanically valid: pre-arm, text+gold only, table-verified; but not
   independent human review). Independent re-audit recommended before
   governance continuation.
2. **SYNTHETIC-SCOPE** — benefit certified on the seeded known-answer corpus
   only; LLM-arm, natural-corpus, and uniqueness-layer follow-ups remain
   registered and open.
3. **G6-RECORD-INCOMPLETENESS-MISS** — arm B withholds all 40
   supported-but-witness-incomplete atlases via fail-closed CANNOT_CHECK
   (GCA_B ≈ 0.83, above the 0.70 floor as the protocol anticipated).
   Pre-registered lever: typed record-repair step (bounded re-query for the
   missing witness evidence, cost charged to arm B) via the mechanism-invention
   workflow — optional here since the outcome is PROMOTE, but it remains the
   registered path if the miss must close.
4. **MODULE-STRICTER-THAN-REPLICA-BOUNDARY** — degenerate witness walks
   diverge (module refuses via GF(2) rank; replica glues). Excluded from the
   corpus family by a generator invariant; a V2 protocol should tighten the
   replica's path check to the rank semantics.

Scope line (kept verbatim from the frozen protocol): a NEGATIVE here would NOT
refute the Lean theorems (they are about representability, not about these
arms); it would refute the claim that the shipped machinery converts the
theorem into measured benefit. The observed PROMOTE is correspondingly scoped:
it certifies benefit conversion by the shipped machinery on this corpus, not
any new mathematical fact.

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
