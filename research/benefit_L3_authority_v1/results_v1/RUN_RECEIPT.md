# RUN_RECEIPT — BENEFIT-L3-AUTHORITY-V1 execution run (results_v1)

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
  `3be90012a5c3179e899e505e65b4a098610128e104199d68fd759edd4ce61a4b` — computed
  in the run environment: **MATCH**.
- Module pins (PROTOCOL.json arms.B_certificate_gated_upgrade.module_pins),
  all **MATCH** against the working tree:
  `src/rakl/authority_ledger.py` `3a045599…2458d26`;
  `src/rakl/evidence_binding_certificate.py` `0057fdc6…535a11e`;
  `src/rakl/claim_evidence.py` `85e845b2…c21dd8e23`;
  `src/rakl/v3_scientific_authority.py` `722faea3…47495d97`;
  `src/rakl/v3_authority.py` `77da0496…6badfdd`;
  `src/rakl/epistemic_noninterference.py` `66019b2d…ca72cfb`
  (full 64-hex values in RESULTS.json `module_pin_verification`).
- `EVALUATOR.py --selftest` in this environment BEFORE the run:
  `SELFTEST PASS: rule-sanity, no-alarm, planted-fail, cannot-check, transplant,
  determinism` (exit 0).

## Execution chronology (all UTC)

1. 18:18:32 — corpus generated, labels minted (`label_minted_at`), structural
   class invariants checked over all 400 claims (PASS; world-fact checks only,
   no arm rule executed), corpus + gold-stripped copy + audit sample +
   hidden-world dump written, sha256 receipts entered into the RSHEA chain
   (`rshea/receipts_step1.json`, epoch `epoch:ecb4394bbe43e658`).
   `freeze_manifest.json` records `arms_executed_yet: false`.
2. 18:19:07 — label audit: 40 seed-sampled claims read in full (surface text +
   gold only, no class field), 0 disagreements. No arm output existed yet
   (`auditor_saw_arm_outputs: false`).
3. 18:19:17 — `arm_run_started_at`. Arm A then arm B, each a separate process
   over the byte-identical gold-stripped corpus.
4. 18:19 — frozen evaluator with `--seed 20260814`; exit 0; verdict PROMOTE.
   RSHEA binding executed (see below).

## Cost matching (PROTOCOL.json arms.cost_matching)

| arm | declarations | UPGRADE declared | wall clock | peak RSS | tokens |
|-----|--------------|------------------|-----------|----------|--------|
| A   | 400          | 360              | 0.00010 s | 31,850,496 B | 0 |
| B   | 400          | 120              | 0.00962 s | 31,899,648 B | 0 |

Identical inputs (stripped corpus sha256 `be08b6cb…43adf261`); denominator fixed
at N=400 for both arms; refusals counted in the denominator. Arm B's 120
upgrades are realized ledger state: 120 active `AuthorityLedger` certificates.

## Deviations

**None.** The protocol was executed as written: frozen thresholds, frozen
estimator, N=400 with the registered composition (A1=120, A2=40, A3=60, A4=60,
A5=40, A6=40, A7=40), registered seed, arm A verbatim to the frozen syntactic
reference-resolution rule, arm B driving the exact pinned
`rakl.evidence_binding_certificate.evaluate_evidence_binding_for_promotion` /
`rakl.authority_ledger.AuthorityLedger.commit_verified` functions, both nulls at
1000 draws, McNemar exact two-sided.

Implementation notes (not deviations; recorded for audit):

- **Degrees of freedom in CORPUS_PLAN.md resolved a priori** (before any freeze
  or result access), on corpus-quality grounds, documented in
  `harness/generate_corpus.py`: one hidden world per claim row; classes
  seed-shuffled across ids; valid evidence blocks license their requested axis
  plus each other axis with probability 1/2 (this keeps the frozen
  evidence-record permutation null non-degenerate — a transplanted valid block
  can license a receiving claim's axis; observed null-2 mean 0.184, q05 0.16 —
  the exact analogue of the L1 corpus reusing standard junctions); A2/A3/A4
  variants drawn uniformly from their registered sets, with A4 root-collapse
  forcing >= 2 bindings as its definition requires.
- **Record→framework-object encoding uses bookkeeping constants only**
  (documented in `harness/arm_harness.py`): ClaimAtom.text carries the record's
  claim text digest (the frozen corpus schema stores text_sha256, not raw
  text); ClaimEvidenceLink.selector is a constant span; AuthorityProposal.
  proposition is a constant tag — none of these fields participates in any
  verdict branch of the pinned module. Encoding validated pre-freeze on 14
  SYNTHETIC fixtures (all class shapes/variants + transplant edge cases)
  against the evaluator's frozen decision-equivalent replicas — never on corpus
  rows; the frozen corpus is the first and only corpus any arm ever saw. The
  evaluator's own drift check then confirmed decision-equivalence on all 400
  real claims (exit 0).
- **RSHEA wiring detail:** as in the L0/L1/L2 runs, the shadow controller's
  status-quo action carries the latest (evaluator-step)
  operator_cost/residual_contraction receipts; the full 12-receipt chain
  remains in the MetricLedger.

## RSHEA binding (executed, per README.md)

- `process_telemetry_to_receipts`: 4 telemetry events (corpus-freeze, arm A,
  arm B, evaluator) -> 12 receipts, sequence 0–11, one epoch.
- `build_evaluation_epoch`: `epoch:ecb4394bbe43e658`, bound to PROTOCOL.json
  sha256, the frozen evaluator sha256, and the harness content hashes.
- `MetricLedger`: 12 receipts, strictly increasing sequence, lineage valid.
- `process_outcome_gate`: 4/4 PASS — **executed**; any FAIL halts the run as
  CANNOT_CHECK before any verdict is read (see step3 code path).
- `shadow_decide`: SELECTED, `acted_upon=false`.
- `interpret_controller_for_runtime`: OBJECT_SEARCH_READY,
  `grants_authority=false`, `governance_required_for_promotion=true`.
- `surface_governed_proposal`: `proposal:benefit-l3-authority-v1-run-1`,
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
3. **A2-RECORD-INCOMPLETENESS-MISS** — arm B withholds all 40
   supported-but-record-incomplete claims via fail-closed CANNOT_CHECK
   (VUA_B = 0.75, above the 0.70 floor as the protocol anticipated).
   Pre-registered lever: typed record-repair step (bounded re-query for the
   missing verification field, cost charged to arm B) via the
   mechanism-invention workflow — optional here since the outcome is PROMOTE,
   but it remains the registered path if the miss must close.
4. **ASSESS-TRANSFER-V2-FAIL-OPEN** — the ladder L3 readiness defect remains a
   separate open P-item; this run neither uses, measures, repairs, nor excuses
   it (PROTOCOL.json explicit_non_target).

This run grants no scientific authority (`grants_scientific_authority: false`).
Any `benefit_measured` flip in `research/framework_ladder/ladder.json` requires
a separate governed PR carrying these RSHEA receipts plus external
GovernanceSignOff.
