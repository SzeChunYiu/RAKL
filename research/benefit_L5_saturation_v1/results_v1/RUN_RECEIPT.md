# RUN_RECEIPT — BENEFIT-L5-SATURATION-V1 execution run (results_v1)

Executed 2026-08-14 against the frozen protocol merged in PR #674
(`origin/main@9052b523`). Typed outcome: **PROMOTE** (frozen evaluator, exit 0).

## Environment

- Host: macOS 26.4 (Darwin 25.4.0), Apple Silicon; Python 3.13 (system `python3`).
- No network access used by generator, arms, or evaluator (stdlib + `src/rakl` only).
- Local scope honored: generator/arms/evaluator only; no xdist, no full test suite.
- Worktree: isolated git worktree of /Users/billy/RAKL, branch
  `research/benefit-l3-l4-l5-runs-v1` from `origin/main@9052b523`.

## Seeds

- Registered seed **20260814** used for: corpus generator (single
  `random.Random` stream), audit sampling, and `EVALUATOR.py --seed`.
- No other randomness sources.

## Pin verification (all BEFORE any execution, re-verified inside every step)

- `EVALUATOR.py` frozen hash in PROTOCOL.json:
  `b3e739d8b8a02121d11568f2de718bea6cdacbbbb888d8f0e074db49b83fec7f` — computed
  in the run environment: **MATCH**.
- Module pin (PROTOCOL.json arms.B_saturation_stopping.module_pins):
  `src/rakl/epistemic_saturation.py`
  `aac384c41999c44facc526a9a32a306ac71eeab9d008fe5248500fcddb423546` — **MATCH**.
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: rule-sanity, trap-attribution, guard, no-alarm, planted-fail,
  cannot-check, determinism` (exit 0).

## Execution chronology (all UTC)

1. 18:44:22 — corpus generated, labels minted (`label_minted_at`; gold basis,
   t_complete and per-round gate facts are pure functions of the hidden world),
   structural class invariants checked over all 400 worlds (PASS; world-fact
   checks only, no arm rule executed), corpus + gold-stripped copy + audit
   sample + hidden-world summary written, sha256 receipts entered into the
   RSHEA chain (`rshea/receipts_step1.json`, epoch `epoch:993a9c4d39c806bd`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 18:44:47 — label audit: 40 seed-sampled worlds checked in full against the
   rendered stream (union of newly-retained ids == gold basis; last
   first-arrival == t_complete; closure gate first true exactly at t_complete,
   or never for null-t_complete worlds; surface description agrees), 0
   disagreements. No arm output existed yet (`auditor_saw_arm_outputs: false`).
3. 18:45:04 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus. Arm B calls the exact pinned
   `rakl.epistemic_saturation.audit_bounded_epistemic_saturation`
   (`required_consecutive_flat_rounds=2`) incrementally after every round
   under a per-world frozen `SaturationBasis`.
4. 18:45–18:51 — frozen evaluator with `--seed 20260814` (both nulls at 1000
   draws); exit 0; verdict PROMOTE. RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | worlds | early stops | mean stop round | wall clock | peak RSS | tokens |
|-----|--------|-------------|-----------------|-----------|----------|--------|
| A   | 400    | 0           | 24.00           | 0.00005 s | 57,212,928 B | 0 |
| B   | 400    | 317         | 15.53           | 0.21664 s | 57,950,208 B | 0 |

Identical inputs (stripped corpus sha256 `7e14c963…55bb7cbb`); T_MAX = 24 for
every world; collection machinery identical across arms (every observable
difference is a stop-time difference); early stops counted in every denominator.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (S1=140, S2=60, S3=60, S4=60,
S5=40, S6=40), T_MAX=24 everywhere, registered seed, arm A verbatim (stop at
T_MAX always), arm B driving the exact pinned
`audit_bounded_epistemic_saturation` with `required_consecutive_flat_rounds=2`,
both nulls at 1000 draws, exact one-sided binomial non-inferiority with no
offset credit, all seven frozen gates evaluated by the frozen evaluator.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any
  freeze or result access), documented at the top of
  `harness/generate_corpus.py`: `new_fact_ids` = newly-retained deduplicated
  first arrivals (repeats/paraphrases rendered as items contributing zero
  growth — the S5 semantics); discovery genuinely closes at t_complete with
  all gate facts true from that round and truthfully mixed before
  (bounded_discovery_closed always false pre-closure); S4 traps are the FIRST
  flat window in their world so bare flat-counting demonstrably stops in
  them; S6 last arrivals in rounds 22–24 with closure never true; distractor
  items fill 1–3 per round through T_MAX.
- **Record→framework-object encoding uses registered semantics only**
  (documented in `harness/arm_harness.py`): fact counts enter one growth
  coordinate and non-fact substantive updates another, so `growth.total`
  equals the frozen replica's growth_total; the rendered
  `operator_order_stable` gate fact becomes a flat/unit substantive-difference
  vector in `OperatorOrderAudit`; the per-world `SaturationBasis` is frozen
  before round 1 and every round carries its fingerprint; the optional
  `required_freshness_cutoff` channel is unexercised, as frozen. Encoding
  validated pre-freeze on 8 SYNTHETIC fixtures (all class shapes plus
  blocking-fiber and non-fact-growth edge cases) against the evaluator's
  frozen decision-equivalent replica — never on corpus rows; the frozen
  corpus is the first and only corpus any arm ever saw. The evaluator's own
  drift check then confirmed stop-round equivalence on all 400 real worlds
  (exit 0).
- **RSHEA wiring detail:** as in the L0–L4 runs, the shadow controller's
  status-quo action carries the latest (evaluator-step)
  operator_cost/residual_contraction receipts; the full 12-receipt chain
  remains in the MetricLedger.

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:993a9c4d39c806bd`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l5-saturation-v1-run-1`,
  **not actionable** (no external `GovernanceSignOff` exists; sign-off would be
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
   (mechanically valid: pre-arm, stream+gold only; partially machine-assisted
   per the receipt's method field; but not independent human review).
   Independent re-audit recommended before governance continuation.
2. **SYNTHETIC-SCOPE** — benefit certified on the seeded known-answer streams
   only; LLM-arm and real-literature-stream follow-ups remain registered and
   open.
3. **FRESHNESS-CHANNEL-UNEXERCISED** — the audit's `required_freshness_cutoff`
   channel was not exercised (as frozen); the pre-registered lever (typed
   freshness-horizon extension via the mechanism-invention workflow) remains
   available but was not needed at this outcome.
4. **GATE-FACT-PROVENANCE** — the rendered per-round gate facts are truthful
   projections of the synthetic hidden world by construction; on natural
   streams the audit's gate inputs would themselves need evidence discipline —
   a scope note carried to the registered natural-corpus follow-up.

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
