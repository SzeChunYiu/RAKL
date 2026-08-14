# RUN_RECEIPT — BENEFIT-L1-COMPOSITION-V1 execution run (results_v1)

Executed 2026-08-14 against the frozen protocol merged in PR #658
(`origin/main@90589790`). Typed outcome: **PROMOTE** (frozen evaluator, exit 0).

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
  `f206d15610afc7fbd0cbc86e1d131f477fa4d02f638a783607b2afe45e3f580c` — computed
  in the run environment: **MATCH**.
- Module pins (PROTOCOL.json arms.B_typed_transition_algebra.module_pins):
  `src/rakl/bridge_composition.py`
  `11a5368dccbdf10dac505915193e7c3f0e830d71cd514aa40889383ffbd47302` — **MATCH**;
  `src/rakl/similarity.py`
  `97dedb16784866649ff01e80075b32d65593788d0455e2179728062e0aeb546e` — **MATCH**.
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: rule-sanity, no-alarm, planted-fail, cannot-check, determinism`
  (exit 0).

## Execution chronology (all UTC)

1. 16:59:11 — corpus generated, labels minted (`label_minted_at`), class
   invariants checked over all 400 chains (PASS), corpus + gold-stripped copy +
   audit sample + hidden-world dump written, sha256 receipts entered into the
   RSHEA chain (`rshea/receipts_step1.json`, epoch `epoch:2b1f659b73374a5f`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 16:59:53 — label audit: 40 seed-sampled chains read in full (surface text +
   gold only, no class field), 0 disagreements. No arm output existed yet
   (`auditor_saw_arm_outputs: false`).
3. 17:00:01 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus.
4. 17:00 — frozen evaluator with `--seed 20260814`; exit 0; verdict PROMOTE.
   RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | declarations | COMPOSED declared | wall clock | peak RSS | tokens |
|-----|--------------|-------------------|-----------|----------|--------|
| A   | 400          | 360               | 0.00013 s | 31,309,824 B | 0 |
| B   | 400          | 120               | 0.00893 s | 31,735,808 B | 0 |

Identical inputs (stripped corpus sha256 `4ee7a0f2…57c08e`); denominator fixed
at N=400 for both arms; refusals counted in the denominator.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (D1=120, D2=40, D3=60, D4=60,
D5=40, D6=40, D7=40), registered seed, arm A verbatim to the frozen
connectivity rule, arm B driving the exact pinned
`rakl.bridge_composition.evaluate_bridge_path` /
`rakl.similarity.SimilarityWitness` functions, both nulls at 1000 draws,
McNemar exact two-sided.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any freeze
  or result access), on corpus-quality grounds: one hidden world per registered
  family (8 worlds); within each (world, hop-count) cell all D1–D6 chains share
  one standard object route and D7 breaks that route via an aliased source id.
  This heavy junction reuse mirrors real corpora where most chains traverse
  standard junctions — and is what gives the frozen contract-permutation null a
  nonzero base rate to measure against (the exact analogue of the L0 corpus
  reusing standard context tuples; without it the null would degenerate to
  all-zero draws and the frozen NEGATIVE branch would fire vacuously).
- **Record→BridgePath encoding chosen so each frozen licensing condition maps
  1:1 onto a module check** (documented in `harness/arm_harness.py`): witness
  relation TRANSFORMABLE_TO; mapping_pairs from junction role inventories with
  chain_input/chain_output pseudo-roles at the endpoints; handoff role_pairs
  (r, r) per consumed role so the module's delivered/consumed check equals the
  frozen consumed⊆delivered condition; the D2-sensitive lineage lives only in
  `BridgeHop.evidence_lineage_ids`; witness bookkeeping fields
  (mapping_admissibility, probe_family) are constant frozen-generator
  declarations. Encoding validated pre-freeze on 18 SYNTHETIC fixtures (all
  class shapes + permuted-contract + edge cases) against the evaluator's frozen
  decision-equivalent replicas — never on corpus rows; the frozen corpus is the
  first and only corpus any arm ever saw. The evaluator's own drift check then
  confirmed decision-equivalence on all 400 real chains (exit 0).
- **RSHEA wiring detail:** as in the L0 run, the shadow controller's status-quo
  action carries the latest (evaluator-step) operator_cost/residual_contraction
  receipts; the full 12-receipt chain remains in the MetricLedger.

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:2b1f659b73374a5f`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l1-composition-v1-run-1`,
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
3. **D2-RECORD-INCOMPLETENESS-MISS** — arm B withholds all 40
   supported-but-record-incomplete chains via fail-closed CANNOT_CHECK
   (VCA_B = 0.75, above the 0.70 floor as the protocol anticipated).
   Pre-registered lever: typed record-repair step (bounded re-query for the
   missing licensing field, cost charged to arm B) via the mechanism-invention
   workflow — optional here since the outcome is PROMOTE, but it remains the
   registered path if the miss must close.

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
