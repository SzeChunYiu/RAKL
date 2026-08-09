# SELF-RAKL Research Round 033 — Psychology-Informed Metacognitive Method Completeness

Date: 2026-08-09  
Parent main: `a980081a930dcd7c3f354d57245c74affa08ab1c`  
Class: additive support/runtime research; no Constitution, evaluator, workflow, routing, or promotion change.

## Research question

Why did Self-RAKL fail to discover target-conditioned pathfinding and missing-operator reasoning until an external human observation exposed the gap, and can research on human metacognition supply mechanisms for detecting weaknesses that are not already represented in the incumbent RAKL ontology?

## Expert panel

1. **Metacognition/cognitive psychology** — calibration, error monitoring, domain specificity.
2. **Judgment and decision making** — bias blind spots and counterfactual debiasing.
3. **Learning sciences** — self-explanation and reconstruction of explanatory structure.
4. **Human factors/AI systems** — when reflection should be externalized into architecture.
5. **Metascience/intellectual humility** — revisability in response to disconfirming evidence.
6. **Adversarial anthropomorphism reviewer** — prevents human mental-state vocabulary from being silently reified as LLM scientific authority.

Joint conclusion: **do not build an LLM “self-awareness” score. Build a triggered, externally governed metacognitive monitor/control layer whose outputs are scoped diagnostics and whose strongest unknown-gap verdict still requires a new frozen Self-RAKL benchmark before repair or promotion.**

## Primary-source projections

### Bias blind spot

Pronin, Lin & Ross (2002) show a systematic self/other asymmetry in perceived susceptibility to bias. RAKL projection: same-context introspection cannot be treated as a privileged detector of its own failure modes. It remains useful process evidence, not independent authority.

### Illusion of explanatory depth

Rozenblit & Keil (2002) show that people can overestimate explanatory understanding until required to produce an explanation. RAKL projection: freeze the required explanatory elements and ask for reconstruction; score the missing set explicitly rather than accepting fluent familiarity.

### Consider the opposite

Lord, Lepper & Preston (1984) provide evidence that explicitly considering an opposing possibility can correct biased judgment more effectively than generic instructions to be unbiased. RAKL projection: a challenge requires an explicit countermodel, differing assumptions, and a possible discriminator. “Be unbiased” text does not count as completion.

### Self-explanation

Chi et al. (1989) provide evidence that self-explanation can support learning/problem solving. RAKL projection: explanation generation is useful when it exposes inferential dependencies, but the generated explanation has proposal authority only.

### Self-distancing / outside view

Grossmann & Kross (2014) show that self-distancing can reduce self/other asymmetry in wise reasoning about personal dilemmas. RAKL projection: instantiate an outside-view review route, while preserving the existing requirement that independent credit needs genuine process/context and evidence-lineage independence.

### Feedback and calibration

Haddara & Rahnev (2022) report that feedback changed bias/calibration without improving metacognitive sensitivity in their perceptual tasks. RAKL projection: separate `CALIBRATION_CHANGE` from `TASK_CAPABILITY_CHANGE`; one cannot mint the other.

### Cost of confidence reporting

Litwin et al. (2025) report task settings where requiring confidence reports decreased response/change-of-mind accuracy. RAKL projection: reflection itself has opportunity cost and should be triggered by registered risk/value signals rather than run continuously.

### LLM metacognitive control

The 2026 MIRROR preprint reports domain-specific self-knowledge and a knowing-doing gap, and reports substantially fewer confident failures when external metacognitive control is imposed than when a model is merely shown its own calibration information. RAKL projection: metacognitive governance should live around the model; model self-report is an input to the controller, not the controller itself. This is recent preprint evidence and is not treated as an established universal result.

## Retained semantic objects

1. `EXTERNALLY_GOVERNED_METACOGNITION`
   - monitoring and control are separated;
   - self-report cannot directly change canonical authority.

2. `TRIGGERED_REFLECTION_POLICY`
   - reflection is a costed research action, not an always-on virtue.

3. `DOMAIN_SCOPED_METACOGNITIVE_CALIBRATION`
   - calibration evidence is indexed by model/method fiber/context.

4. `EXPLANATION_RECONSTRUCTION_GAP`
   - missing required explanatory elements are explicit residuals.

5. `COUNTERMODEL_CONTRACT`
   - explicit opposing model/assumptions/discriminator is required; generic “critique yourself” language is insufficient.

6. `ONTOLOGY_GAP_CANDIDATE`
   - repeated unclassified residuals may justify opening a separately benchmarked residual-ontology challenger.

7. `METHOD_BASIS_GAP_CANDIDATE`
   - an identified target-blocking cut outside the incumbent operator basis may justify opening a separately benchmarked operator challenger.

8. `OPERATIONAL_INTELLECTUAL_HUMILITY`
   - defined as revisability under evidence, explicit `CANNOT_CHECK`, preserved negative history, and willingness to reopen the method—not a personality simulation.

## Novelty correction

RAKL must **not** claim novelty for metacognition, confidence calibration, self-explanation, consider-the-opposite debiasing, self-distancing, curiosity, feedback learning, intellectual humility, or external metacognitive scaffolding.

The narrower candidate contribution is the integration of these source mechanisms into a scientific-method **completeness controller** operating over:

```text
contextual atlas
scientific authority coordinates
residual ontology
target reachability / epistemic cuts
negative history
process + evidence-lineage independence
governed self-evolution
```

The claim remains empirical: if structured audits do not find held-out missing weakness/operator classes better than ordinary same-context reflection at matched cost, the layer should be retained as an explanatory lens only.

## Frozen benchmark

`research/SELF_RAKL_RESEARCH_033_FROZEN_BENCHMARK.json`

The benchmark was committed before implementation at:

`d03484184d7718535d7b3cc014da9dce5b76468b`

Its hostile worlds include:

- high-confidence external error;
- one surprising error vs repeated unclassifiable residuals;
- target unreachability with and without a known resolving operator;
- incomplete mechanistic reconstruction;
- generic debiasing language without a countermodel;
- same-context review falsely presented as independent;
- cross-domain calibration leakage;
- reflection cost exceeding expected value;
- feedback that improves calibration but not underlying sensitivity;
- missing external correctness evidence.

## Implementation

`src/rakl/metacognition.py` is support-only. It can classify a diagnostic packet as:

```text
NO_AUDIT_REQUIRED
CALIBRATED_NO_NEW_GAP
KNOWN_WEAKNESS
CALIBRATION_WEAKNESS
EXPLANATION_GAP
ONTOLOGY_GAP_CANDIDATE
METHOD_BASIS_GAP_CANDIDATE
INDEPENDENT_REVIEW_REQUIRED
CANNOT_CHECK
```

It cannot activate a new operator, mutate routing, mint scientific truth, promote a challenger, or amend the Constitution.

## Measured implementation evidence

The implementation/test SHA `793e15d8ee6c44095d04b6001485e382da6aebb9` executed the repository GitHub Actions suite on exact subject identity and produced:

`400 passed in 8.55s`

This is software-contract evidence only. The final receipt-bearing candidate requires its own exact-SHA run before promotion.

## New residuals

- `META_N101_METACOGNITIVE_METHOD_COMPLETENESS` — current support layer and benchmark family.
- `META_N102_CONCEPTUAL_BASIS_INDEPENDENCE` — define/test whether an outside reviewer uses a materially different ontology/decomposition, not merely a different prompt/process.
- `META_N103_TRIGGERED_REFLECTION_POLICY` — compare triggered audits against continuous reflection under matched tokens/latency/cost.
- `META_N104_EXPLANATION_DEPTH_CHALLENGE` — validate whether frozen explanation reconstruction catches hidden causal/mechanistic gaps.
- `META_N105_DOMAIN_SCOPED_METACOG_CALIBRATION` — empirical calibration surfaces across RAKL fibers/models.
- `META_N106_HELD_OUT_MISSING_OPERATOR_DISCOVERY` — headline experiment hiding method operators/weakness classes from the incumbent basis.

Priority for the paper: `N106 > N101 > N102 > N103 > N104/N105`.

## Outcome-complete next-AI instructions

- **Positive:** if N106 prospectively improves held-out missing-operator/ontology detection at matched cost, report scoped gain and proceed to a governed repair/evolution experiment.
- **Null:** if ordinary reflection is equally good or cheaper, do not add an always-on metacognitive runtime layer; retain only the useful explanatory diagnostics.
- **Refuted:** if structured audits increase false operator/ontology invention, narrow or remove the corresponding trigger/rule and preserve the failure.
- **Partially identified:** if gains appear only in some fibers/models, store a context-indexed metacognitive capability frontier; do not globalize.
- **Blocked:** if external correctness or independent review evidence is unavailable, return `CANNOT_CHECK` rather than self-certifying.
- **Transport:** infrastructure failure is operational evidence only and cannot support or refute the metacognitive hypothesis.

Saturation: `ACTIVE_NON_FLAT`; same-context flat rounds `0`; independent flat rounds `0`.
