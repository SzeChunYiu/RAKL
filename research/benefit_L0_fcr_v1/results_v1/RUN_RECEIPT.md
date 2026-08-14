# RUN_RECEIPT — BENEFIT-L0-FCR-V1 execution run (results_v1)

Executed 2026-08-14 against the frozen protocol merged in PR #644
(`origin/main@600cfc92`). Typed outcome: **PROMOTE** (frozen evaluator, exit 0).

## Environment

- Host: macOS 26.4 (Darwin 25.4.0), Apple Silicon; Python 3.13.12 (system `python3`).
- No network access used by generator, arms, or evaluator (stdlib + `src/rakl` only).
- Local scope honored: generator/arms/evaluator only; no xdist, no full test suite.
- Worktree: isolated git worktree of /Users/billy/RAKL, branch
  `research/benefit-l0-fcr-run-v1` from `origin/main@600cfc92`.

## Seeds

- Registered seed **20260814** used for: corpus generator (single
  `random.Random` stream), audit sampling, and `EVALUATOR.py --seed`.
- No other randomness sources.

## Evaluator hash verification

- Frozen hash in PROTOCOL.json:
  `536ba0e21899207449de8333446fa9c67ed50b51f048f93ac68f2ba8d4afb273`
- Computed before any execution AND re-verified inside step 3:
  `536ba0e21899207449de8333446fa9c67ed50b51f048f93ac68f2ba8d4afb273` — **MATCH**.
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: no-alarm, planted-fail, cannot-check, determinism` (exit 0).

## Execution chronology (all UTC)

1. 13:06:47 — corpus generated, labels minted (`label_minted_at`), class
   invariants checked over all 400 rows (PASS), corpus + gold-stripped copy +
   audit sample + hidden-world dump written, sha256 receipts entered into the
   RSHEA chain (`rshea/receipts_step1.json`, epoch `epoch:edf5f97c5b7b8f44`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 13:07:44 — label audit: 40 seed-sampled pairs read in full (surface texts +
   gold only), 0 disagreements. No arm output existed yet
   (`auditor_saw_arm_outputs: false`).
3. 13:08:13 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus.
4. 13:09 — frozen evaluator with `--seed 20260814`; exit 0; verdict PROMOTE.
   RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | declarations | CONTRADICTION declared | wall clock | peak RSS | tokens |
|-----|--------------|------------------------|-----------|----------|--------|
| A   | 400          | 320                    | 0.00006 s | 29,032,448 B | 0 |
| B   | 400          | 90                     | 0.00307 s | 28,016,640 B | 0 |

Identical inputs (stripped corpus sha256 `8b548ab5…ca01883`); denominator fixed
at N=400 for both arms; withheld declarations counted in the denominator.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (C1=90, C2=30, C3=120, C4=80,
C5=80), registered seed, arms implemented verbatim from PROTOCOL.json (arm B
driving the exact bound `rakl.core` functions), both nulls at 1000 draws,
McNemar exact two-sided.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any freeze
  or result access), on corpus-quality grounds: one world instance per
  registered family (8 worlds x 50 pairs); per world 2 load-bearing coordinates
  with 2 values each (distinct 4-point value grid per facet); heavy
  within-world reuse of standard context tuples (mirrors real corpora where
  most reports share standard conditions — this is also what gives the
  context-permutation null a nonzero base rate to measure against); exact
  integer unit factors (x10/x100/x1000/identity) so C4 equivalence is exact.
- **Pre-freeze generator fix:** the built-in class-invariant checker caught an
  inexact C4 conversion in the first generator draft (material-hardness family
  used a x0.1 factor breaking one-decimal exactness). Fixed to an exact x10
  unit direction (HV -> dHV) BEFORE any freeze, arm execution, or result
  access; the frozen corpus is the first and only corpus any arm ever saw.
- **RSHEA wiring detail:** `build_status_quo_action` requires unique component
  names, so the shadow controller's status-quo action carries the latest
  (evaluator-step) operator_cost/residual_contraction receipts; the full
  12-receipt chain remains in the MetricLedger. Control-plane wiring only; the
  evaluator report predates it and is byte-identical on re-run (deterministic).

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:edf5f97c5b7b8f44`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l0-fcr-v1-run-1`, **not
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
   (mechanically valid: pre-arm, texts+gold only; but not independent human
   review). Independent re-audit recommended before governance continuation.
2. **SYNTHETIC-SCOPE** — benefit certified on the seeded known-answer corpus
   only; LLM-arm and natural-corpus follow-ups remain registered and open.
3. **C2-DISTRACTOR-MISS** — arm B withholds all 30 distractor-context true
   contradictions (TCR_B = 0.75, above the 0.70 floor as the protocol
   anticipated). Pre-registered lever: per-facet load-bearing relevance map via
   the mechanism-invention workflow (protocol follow-up R4/CONDITIONAL note) —
   optional here since the outcome is PROMOTE, but it remains the registered
   path if the miss must close.

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
