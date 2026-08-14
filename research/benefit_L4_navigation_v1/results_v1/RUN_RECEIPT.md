# RUN_RECEIPT — BENEFIT-L4-NAVIGATION-V1 execution run (results_v1)

Executed 2026-08-14 against the frozen protocol merged in PR #674
(`origin/main@9052b523`). Typed outcome: **PROMOTE** (frozen evaluator, exit 0).

## Execution-binding determination (read FIRST, before any execution)

PROTOCOL.json `execution_binding.execution_precondition` requires the separate
L4 gate-falsifiability audit of `src/rakl/support_solver.py` to have landed
before the execution run, else the verdict is capped at CONDITIONAL regardless
of metrics. Determination: **SATISFIED AS WRITTEN — no cap applies.**

- The merged sweep receipt `research/solver_gate_falsifiability_sweep_v1/SWEEP.json`
  (PR #645, commit `f6c3bda7`, on `origin/main` before this run's base) audits
  step `7_navigation`, gate `support_solver.solve`: classification
  **FALSIFIABLE**, no-alarm control OK (`intact_evidence_passes: true`,
  `checked_before_probes: true`), 5/5 probes SENSITIVE at both seeds, zero
  insensitive probes.
- `src/rakl/support_solver.py` at the sweep commit is byte-identical
  (sha256 `180548b1…fd374c6`) to this protocol's module pin and to the run
  environment, so the landed audit covers exactly the pinned semantics.

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
  `2dd3726fc99354c1fe70704843ac628946cb00eeb15955747fcb8494eebe418d` — computed
  in the run environment: **MATCH**.
- Module pin (PROTOCOL.json arms.B_distil_and_navigate.module_pins):
  `src/rakl/support_solver.py`
  `180548b10a4465194c0aefd458a55e78dd23e00a9d8a7e4eb64ca6bd4fd374c6` — **MATCH**.
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: rule-sanity, obstruction, no-alarm, planted-fail,
  cannot-check, determinism` (exit 0).

## Execution chronology (all UTC)

1. 18:36:10 — corpus generated, labels minted (`label_minted_at`; gold =
   exact admissible-route search over the full fact set using the frozen
   evaluator's own navigation core loaded by file path, so gold semantics and
   evaluation semantics cannot diverge), S* computed by exact minimal set
   cover, structural class invariants checked over all 400 worlds (PASS;
   world-fact checks only, no arm policy executed), rendering-faithfulness
   re-check PASS, corpus + gold-stripped copy + audit sample + hidden-world
   dump written, sha256 receipts entered into the RSHEA chain
   (`rshea/receipts_step1.json`, epoch `epoch:bc8cd601c2278c86`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 18:36:24 — label audit: 40 seed-sampled worlds read in full (surface text +
   gold only, no class/S* fields), 0 disagreements. No arm output existed yet
   (`auditor_saw_arm_outputs: false`).
3. 18:36:39 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus. Arm B drives the exact pinned
   `rakl.support_solver.solve` on every partial structure (both arms' connect
   rule is realized through the same pinned module).
4. 18:37–18:52 — frozen evaluator with `--seed 20260814` (both nulls at 1000
   full policy re-runs over the primary set); exit 0; verdict PROMOTE.
   RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | declarations | SOLVED declared | wall clock | peak RSS | tokens |
|-----|--------------|-----------------|-----------|----------|--------|
| A   | 400          | 100             | 0.03813 s | 35,717,120 B | 0 |
| B   | 400          | 310             | 0.01947 s | 34,816,000 B | 0 |

Identical inputs (stripped corpus sha256 `fdb41ef0…c31e25d0`); budget_units
identical across arms per world; COST_READ=1.0, COST_DISTIL=2.0 (all
distillation cost charged to arm B); refusals counted in every denominator.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (N1=120, N2=60, N3=60, N4=40,
N5=60, N6=30, N7=30), frozen budget classes (2/4/8 * S*), registered seed,
arm A verbatim to the frozen lexical-reading policy, arm B driving the exact
pinned `rakl.support_solver.solve`, both nulls at 1000 draws, McNemar exact
two-sided, FSR/SFH/LOOSE gates all evaluated by the frozen evaluator.

Prose-vs-executable notes (recorded, not reconciled; the frozen EXECUTABLE
rule governs per the protocol's own drift-check clause and
no_post_result_threshold_rescue):

- **Primary-set arithmetic.** PROTOCOL.json `corpus.primary_set_size` records
  270 (= N1+N3+N5+N6), but the frozen `EVALUATOR.py primary_set()` — the
  hash-bound executable definition — selects ALL gold-SOLVABLE MEDIUM/LOOSE
  worlds, which includes N4 (n_primary = 310). Verdict-invariant: delta_SR =
  0.778 on the 270 subset vs 0.677 on the executable 310 set; same discordant
  structure (b=210, c=0), same PROMOTE branch either way.
- **CUT-with-no-repair guidance.** The protocol prose offers "the
  EpistemicCut" as arm-B guidance when no unobstructed relaxed route exists;
  cut elements in that state are obstruction ids (no endpoints, matching no
  index tokens). The frozen executable replica (`need_atoms`) uses the
  frontier construction, and the declaration drift check binds the harness to
  it. The harness therefore maps the module's `SolveReport` as: REACHED ->
  SOLVED; CUT with a MinimalRepair -> repair-element endpoints + goal; CUT
  with repair None / UNREACHABLE_IN_PRINCIPLE -> forward+backward frontier +
  {start, goal}. Documented in `harness/arm_harness.py`.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any
  freeze or result access), documented at the top of
  `harness/generate_corpus.py`: chain packing (2 edges/source, S* = ceil(h/2)),
  distractor counts (D = 3*S*+1 base, heavier in N5) that make lexical reading
  structurally budget-starved at MEDIUM while LOOSE funds a full read; every
  edge in exactly one source and every obstruction declared by the source
  carrying the first edge of the route it obstructs with a private cover atom —
  which makes false solves structurally impossible for policy-honest arms, so
  the FSR gate checks machinery, not luck; N7 split between under-licensed and
  goal-disconnected modes with S* fixed a priori to the un-broken sibling's
  cover.
- **Arm encoding validated pre-freeze on 8 SYNTHETIC fixtures** (all class
  shapes: deep chain at 3 budgets, shallow, distractor-heavy, obstructed
  decoy, both unsolvable modes) against the evaluator's frozen
  decision-equivalent policies — never on corpus rows; the frozen corpus is
  the first and only corpus any arm ever saw. The evaluator's own drift check
  then confirmed decision-equivalence on all 400 real worlds (exit 0).
- **RSHEA wiring detail:** as in the L0/L1/L2/L3 runs, the shadow controller's
  status-quo action carries the latest (evaluator-step)
  operator_cost/residual_contraction receipts; the full 12-receipt chain
  remains in the MetricLedger.

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:bc8cd601c2278c86`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l4-navigation-v1-run-1`,
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
   (mechanically valid: pre-arm, text+gold only; but not independent human
   review). Independent re-audit recommended before governance continuation.
2. **SYNTHETIC-SCOPE** — benefit certified on the seeded known-answer corpus
   only; LLM-arm and natural-corpus follow-ups remain registered and open.
3. **TIGHT-BUDGET-SCOPE** — no benefit at TIGHT budgets (both arms 0/60 on
   N2); the promotable claim is budget-conditional (>= 4*S*) exactly as
   frozen. Pre-registered lever if TIGHT must be addressed: guidance-quality
   measurement at COST_DISTIL = 1.0 as a V2 re-freeze, never a post-hoc rescue.
4. **GATE-FALSIFIABILITY-CLOSED** — the execution precondition is closed by
   the merged sweep receipt (see the determination section); other solver-step
   gates keep their own open items in that sweep.

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
