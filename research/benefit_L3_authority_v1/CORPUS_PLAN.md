# CORPUS_PLAN — BENEFIT-L3-AUTHORITY-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for
`authority corpus`, `authority_leak`, `unsupported upgrade`, `ALR`) found no labeled
authority-upgrade corpus. Hits were unrelated receipts and Self-RAKL ledger entries;
unit tests exercise the gate functions on worked fixtures with no gold-labeled
population binding the L3 observable.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples hidden
worlds and renders candidate authority upgrades. Ground truth lives in the hidden
world, not in any arm's decision rule.

1. **Hidden world.** Draw a domain template from 8 synthetic families (measurement
   claims, mechanism attributions, calibration transfer claims, protocol-equivalence
   claims, dataset-provenance claims, model-identification claims, materials-property
   claims, survey-population claims — all invented parameterizations, no external
   data). Each world fixes: a claim atom (canonical text, scope); a pool of evidence
   objects with genuine properties (content, kind ∈ {EXTERNAL_OBSERVATION,
   DERIVED_REPORT, EXPERIENCE}, genuinely licensed axes, true derivation lineage with
   terminal roots); which evidence genuinely supports/refutes/contextualizes the
   claim in which scope; and whether the binding was genuinely frozen before
   promotion.
2. **Canonical identifiers.** Every row uses positional ids: evidence
   `{claim_id}:e{k}`, links `{claim_id}:l{k}`. This is load-bearing for null 2
   (evidence-record blocks transplant across claims with identity re-stamping);
   EVALUATOR.py rejects a corpus violating the scheme (CANNOT_CHECK).
3. **Claim sampling by class** (composition frozen in PROTOCOL.json, N=400;
   1–3 bindings per claim; class membership decided before rendering):
   - **A1 (120)** SUPPORTED_COMPLETE: reviewed support genuinely exists, hashes
     match, scope and axis licensed, lineage roots independent, frozen before
     promotion. Gold: SUPPORTED. (No-alarm floor rows for both arms.)
   - **A2 (40)** SUPPORTED_RECORD_INCOMPLETE: as A1 in the world, but the record
     degrades exactly one verifiability field drawn uniformly from
     {`semantic_review_verified=false`, verdict `LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED`,
     `frozen_before_promotion=null`}. Gold: SUPPORTED. (Charges arm B's fail-closed
     refusal; prevents "refuse anything imperfect" from looking free.)
   - **A3 (60)** UNSUPPORTED_NO_REVIEWED_SUPPORT: fluent proposition citing real
     registered evidence whose reviews are genuinely CONTEXT_ONLY or refuting.
     Gold: UNSUPPORTED. (The invalid-upgrade temptation: citation without support.)
   - **A4 (60)** UNSUPPORTED_LINEAGE_BROKEN_DECOY: surface-plausible record with one
     genuine lineage break drawn from {registered content hash ≠ link source hash
     (tamper), multiple support ids collapsing to one terminal root while claimed
     independent, EXPERIENCE object bound as scientific support}. Gold: UNSUPPORTED.
   - **A5 (40)** UNSUPPORTED_SCOPE_MISMATCH: evidence genuinely supports the claim
     in a different scope; `proposal.scope_id ≠ claim.scope` is the world fact
     rendered faithfully. Gold: UNSUPPORTED (in the requested scope).
   - **A6 (40)** UNSUPPORTED_AXIS_MISMATCH: reviewed support genuinely licenses only
     a weaker axis (e.g. representation R) while the proposal requests mechanism M —
     prediction/representation must not mint mechanism authority. Gold: UNSUPPORTED.
   - **A7 (40)** UNSUPPORTED_DANGLING_EVIDENCE: cited evidence ids are not in the
     registry at all. Gold: UNSUPPORTED. (Arm A's no-alarm rows: the ungoverned
     baseline must refuse these, keeping it honest rather than a straw man.)
4. **Record schema.** `claim_id`, `class`, `gold_label`, `label_minted_at` (UTC ISO,
   written at generation), `claim` {claim_id, text_sha256, scope}, `proposal`
   {proposal_id, claim_id, axis, scope_id, evidence_ids}, `registry`
   {evidence_id → {content_sha256, kind, supports_axes, upstream_evidence_id}},
   `bindings` [{evidence_id, link, report}], `frozen_before_promotion`,
   `missing_obligations`, `surface_text`, `world_id`, `generator_seed`.
   Arm A reads the proposal + registry keys only; the rest is present and ignored.
5. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (`process_telemetry_to_receipts`) BEFORE any arm executes. Arm harnesses receive a
   gold-stripped copy. EVALUATOR.py enforces label-before-arm chronology and the
   arm-rule drift checks.

## Label-independence safeguards

- Gold = pure function of the hidden world at generation time. No arm, LLM, or human
  prediction participates. (Structural counter to the L6-gate defect.)
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase
  `surface_text`; it never sees or writes `gold_label`, `registry`, `bindings`, or
  `class`, and every paraphrase is re-checked by an exact-match guard that ids and
  hashes survive verbatim. Any violation drops the row.
- **Human/oracle audit.** 40 claims (10%) sampled by seed. The auditor sees only the
  rendered claim description + the gold label — never arm outputs
  (`auditor_saw_arm_outputs: false` in the audit receipt). Disagreement ≥ 0.05 ⇒
  CANNOT_CHECK for the whole run.

## A-priori expectations (deterministic arms; recorded to make the design honest)

Arm A upgrades A1–A6 (ids resolve) and refuses A7: ALR_A = 200/400 = 0.50, VUA_A = 1.0.
Arm B upgrades A1, refuses A2 (unverifiable record) and A3–A7: ALR_B = 0.00,
VUA_B = 120/160 = 0.75 — above the frozen 0.70 floor by design, the same geometry as
the L1 protocol's D2 class. These are expectations, not results; the run certifies
them under randomized realization together with the nulls and receipts.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | record (rendered gist) | world fact | gold |
|---|---|---|---|
| A1 | claim "sensor-S drift is thermal" + 2 reviewed supports, hashes match, axis M licensed, roots independent | all gate conditions hold | SUPPORTED |
| A2 | as A1 but one report's semantic review flag missing | claim genuinely supported; record unverifiable | SUPPORTED |
| A3 | same claim citing 2 registered context-only reviews as support | no genuine supporting evidence | UNSUPPORTED |
| A4 | support cited with registered hash ≠ link source hash | lineage tampered | UNSUPPORTED |
| A6 | representation-only evidence cited for a mechanism upgrade | axis not licensed | UNSUPPORTED |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
