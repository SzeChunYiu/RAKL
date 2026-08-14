# CORPUS_PLAN — BENEFIT-L1-COMPOSITION-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for
`unsupported_composition`, `composition corpus`, `chain corpus`) found no labeled
composition-chain corpus. `tests/test_bridge_composition.py` holds unit fixtures for
`evaluate_bridge_path` (single worked paths, no gold-labeled population);
`research/framework_ladder/ladder.json` registers the unsupported-composition-rate
observable but binds no data.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples hidden
worlds and renders composition chains. Ground truth lives in the hidden world, not in
any arm's decision rule — this is what makes gold labels non-tautological for arm B.

1. **Hidden world.** Draw a domain template from 8 synthetic families (reaction
   pathway transfer, sensor-calibration chains, translation pipelines, unit-system
   bridges, model-reduction chains, protocol version lineages, supply-chain custody,
   coordinate-frame transforms — all invented parameterizations, no external data).
   Each world fixes: a set of named objects; a set of true typed transitions between
   them, each with genuine relation content (which invariants the step actually
   preserves, which regimes it actually holds in, what its true error contribution
   is, which roles it delivers at its target); and per-object role inventories.
2. **Chain sampling by class** (composition frozen in PROTOCOL.json, N=400; hop
   count 2–4 drawn per chain; class membership decided before rendering):
   - **D1 (120)** SUPPORTED_COMPLETE: every consecutive interface matches, all six
     licensing conditions genuinely hold in the world, and the rendered contract is
     complete. Gold: SUPPORTED. (No-alarm floor rows for both arms.)
   - **D2 (40)** SUPPORTED_RECORD_INCOMPLETE: as D1 in the world (the chain is
     genuinely supported), but the rendered record omits exactly one licensing field
     drawn uniformly from {one hop's `error_bound`, one handoff's
     `compatibility_passed`, one hop's `evidence_lineage_ids`}. Gold: SUPPORTED.
     (Charges arm B's fail-closed refusal; prevents "refuse anything imperfect"
     from looking free.)
   - **D3 (60)** UNSUPPORTED_INVARIANT_BROKEN: interfaces connect, but a claimed
     end-to-end invariant is genuinely broken at one interior hop (that hop's
     witness lists it as `not_preserved` — the world fact). Mixed weaker relations
     minting a stronger relation. Gold: UNSUPPORTED.
   - **D4 (60)** UNSUPPORTED_REGIME_DISJOINT: interfaces connect, per-hop contracts
     individually complete, but the hops' regime sets have empty intersection in the
     world. Gold: UNSUPPORTED.
   - **D5 (40)** UNSUPPORTED_ROLE_HANDOFF_BROKEN: interfaces connect by name, but at
     one junction the roles the next hop consumes are not delivered by the prior hop
     (world fact: the shared name hides a role mismatch — possible aliasing).
     Gold: UNSUPPORTED.
   - **D6 (40)** UNSUPPORTED_ERROR_OVERFLOW: every hop individually fine, but the
     true accumulated error exceeds the frozen chain tolerance under the declared
     additive rule. Gold: UNSUPPORTED.
   - **D7 (40)** UNSUPPORTED_DISCONNECTED: one consecutive pair fails to connect
     even syntactically (target/source identifiers differ). Gold: UNSUPPORTED.
     (Arm A's no-alarm rows: the untyped baseline must refuse these, keeping it an
     honest baseline rather than a straw man.)
3. **Rendering.** Deterministic templates with seeded lexical variation banks produce
   a `surface_text` chain description. Machine fields are emitted alongside:
   `skeleton` (per-hop `source_id`/`target_id`) and `contract` (per-hop `regime`,
   `preserved`, `not_preserved`, `evidence_lineage_ids`, `error_bound`,
   `error_semantics_id`; per-junction `junction_id`, `roles_delivered`,
   `roles_consumed`, `compatibility_passed`; chain-level `claimed_invariants`,
   `max_accumulated_error`, `error_composition_rule`). Arm A reads the skeleton
   only; the contract is present in its input and deliberately ignored.
4. **Record schema.** `chain_id`, `class`, `gold_label`, `label_minted_at` (UTC ISO,
   written at generation), `skeleton`, `contract`, `surface_text`, `world_id`,
   `generator_seed`.
5. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (`process_telemetry_to_receipts`) BEFORE any arm executes. Arm harnesses receive a
   gold-stripped copy. EVALUATOR.py enforces label-before-arm chronology and the
   arm-rule drift checks.

## Label-independence safeguards

- Gold = pure function of the hidden world at generation time. No arm, LLM, or human
  prediction participates. (Structural counter to the L6-gate defect.)
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase
  `surface_text`; it never sees or writes `gold_label`, `skeleton`, `contract`, or
  `class`, and every paraphrase is re-checked by an exact-match guard that endpoint
  identifiers and contract mentions survive verbatim. Any violation drops the row.
- **Human/oracle audit.** 40 chains (10%) sampled by seed. The auditor sees only the
  rendered chain description + the gold label — never arm outputs
  (`auditor_saw_arm_outputs: false` in the audit receipt). Disagreement ≥ 0.05 ⇒
  CANNOT_CHECK for the whole run.

## A-priori expectations (deterministic arms; recorded to make the design honest)

Arm A accepts D1–D6 (connected) and refuses D7: UCR_A = 200/400 = 0.50, VCA_A = 1.0.
Arm B accepts D1, refuses D2 (incomplete record) and D3–D7: UCR_B = 0.00,
VCA_B = 120/160 = 0.75 — above the frozen 0.70 floor by design, exactly as the L0
protocol's C2 class sat above its TCR floor. These are expectations, not results; the
run certifies them under randomized realization together with the nulls and receipts.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | chain (rendered gist) | world fact | gold |
|---|---|---|---|
| D1 | cal-A → cal-B → cal-C, invariant "linearity" preserved each hop, regimes overlap, errors 0.01+0.02 ≤ 0.1 | all six conditions hold | SUPPORTED |
| D2 | as D1 but hop 2's error bound missing from the record | chain genuinely supported; record incomplete | SUPPORTED |
| D3 | model-X → reduced-X → surrogate-X claiming end-to-end "mass conservation" | hop 2 genuinely breaks mass conservation | UNSUPPORTED |
| D4 | protocol-v1 → v2 → v3, hop regimes {lab} and {field} | regime intersection empty | UNSUPPORTED |
| D5 | frame-G → frame-L → frame-S; junction delivers role "attitude" but next hop consumes "position" | role handoff broken behind a shared name | UNSUPPORTED |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
