# CORPUS_PLAN — BENEFIT-L0-FCR-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for `FCR`,
`false_contradiction`, `contradiction corpus`) found no labeled comparable-claim-pair
corpus. `tests/test_core.py::test_context_difference_prevents_false_contradiction` is a
2-item worked example; `research/RAKL_DUAL_HEADLINE_PREREGISTRATION_034.json` registers
`false_contradiction_rate` as a metric but binds no data.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples hidden
worlds and renders claim pairs. Ground truth lives in the hidden world, not in any
arm's decision rule — this is what makes gold labels non-tautological for arm B.

1. **Hidden world.** Draw a domain template from 8 synthetic families (material
   hardness, dose–response, species range, order-book depth, thermal conductivity,
   incidence rate, solubility, stellar luminosity — all invented parameterizations,
   no external data). Each world fixes: an object, 2–4 facets, for each facet a value
   function over a context space of the seven standard coordinates
   (population, scale, horizon, observation_model, units, assumptions, intervention),
   and a declared set of **load-bearing** coordinates per facet (the coordinates the
   value function actually depends on). Non-load-bearing coordinates are distractors.
2. **Pair sampling by class** (composition frozen in PROTOCOL.json, N=400):
   - **C1 (90)** TRUE_CONTRADICTION_ALIGNED: same facet, identical context tuple, one
     source reports a corrupted observation → incompatible values. Gold: CONTRADICTION.
   - **C2 (30)** TRUE_CONTRADICTION_DISTRACTOR: as C1, but a non-load-bearing
     coordinate differs textually between the two contexts. The world says the values
     still genuinely conflict. Gold: CONTRADICTION. (Charges arm B's any-difference
     withholding; prevents "excuse everything" from looking free.)
   - **C3 (120)** CONTEXT_DEPENDENT_DIFFERENCE: values differ because a load-bearing
     coordinate differs. Gold: CONTEXT_DEPENDENT_DIFFERENCE.
   - **C4 (80)** EQUIVALENT_UNIT: same world value rendered under two unit systems /
     representations (units coordinate differs; conversion is exact). Gold: EQUIVALENT.
   - **C5 (80)** SAME_VALUE_RESTATED: identical canonical value and context, surface
     paraphrase differs. Gold: EQUIVALENT. (No-alarm floor rows.)
3. **Rendering.** Deterministic sentence templates with seeded lexical variation banks
   produce `surface_text_left/right`. Machine fields (`facet_*`, `value_*`,
   `context_*`) are emitted alongside; canonical `value_*` strings are what arm A
   compares (naive text comparison at the value level, the strongest honest naive arm).
4. **Record schema.** `pair_id`, `class`, `gold_label`, `label_minted_at` (UTC ISO,
   written at generation), machine fields, surface texts, `world_id`, `generator_seed`.
5. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (process_telemetry_to_receipts) BEFORE any arm executes. Arm harnesses receive a
   gold-stripped copy. EVALUATOR.py enforces label-before-arm chronology.

## Label-independence safeguards

- Gold = pure function of the hidden world at generation time. No arm, LLM, or human
  prediction participates. (Structural counter to the L6-gate defect.)
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase
  `surface_text_*` fields; it never sees or writes `gold_label`, `value_*`,
  `context_*`, or `class`, and every paraphrase is re-checked by an exact-match guard
  that canonical values and context mentions survive verbatim. Any violation drops the row.
- **Human/oracle audit.** 40 pairs (10%) sampled by seed. The auditor sees only the two
  surface texts + the gold label — never arm outputs (`auditor_saw_arm_outputs: false`
  in the audit receipt). Disagreement ≥ 0.05 ⇒ CANNOT_CHECK for the whole run.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | left claim | right claim | gold |
|---|---|---|---|
| C1 | "Alloy AX-3 hardness is 210 HV (annealed, 25C)" | "Alloy AX-3 hardness is 340 HV (annealed, 25C)" | CONTRADICTION |
| C2 | "Alloy AX-3 hardness is 210 HV (annealed, 25C, lab-A protocol)" | "Alloy AX-3 hardness is 340 HV (annealed, 25C, lab-B protocol)" — protocols declared observationally identical by the world | CONTRADICTION |
| C3 | "Alloy AX-3 hardness is 210 HV (annealed)" | "Alloy AX-3 hardness is 385 HV (cold-worked)" | CONTEXT_DEPENDENT_DIFFERENCE |
| C4 | "Yield strength 250 MPa" | "Yield strength 36.3 ksi" | EQUIVALENT |
| C5 | "The sample is visibly red" | "Observers label the specimen red" | EQUIVALENT |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
