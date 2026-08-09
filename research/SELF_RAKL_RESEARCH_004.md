# SELF-RAKL Research Round 004

Date: 2026-08-09

Object: `RAKL_METHOD`

Status: `ACTIVE_NON_FLAT`

## Frozen expert panel

This round used five deliberately different lenses before synthesis.

1. **Evaluator-security / formal-methods engineer** mapped everything that can influence a promotion verdict and attacked the trust boundary.
2. **Scientific reproducibility / workflow engineer** inspected commands, configuration, dependencies and runtime environment as causal inputs to evaluation.
3. **Bayesian experimental-design scientist** compared generic information gain with QoI/decision-targeted and misspecification-robust acquisition.
4. **Agent-evaluation researcher** examined scorer, sandbox and information-boundary patterns in current evaluation frameworks.
5. **Adversarial red-team reviewer** attempted to make a hostile candidate look green without preserving the intended frozen evaluator.

The benchmark and predicted hostile outcomes were frozen in `SELF_RAKL_RESEARCH_004_FROZEN_BENCHMARK.json` before the hostile experiment and supporting implementation.

## 1. Native discriminator: a green CI result was successfully gamed

Round 003 protected the obvious workflow/test files by fingerprint. The panel identified an omitted evaluator influence coordinate: `.github/workflows/test.yml` executes plain `pytest`, while test discovery is configured by `pyproject.toml`.

A hostile candidate branch was therefore created from the frozen round-004 benchmark commit. It changed `pyproject.toml` so `testpaths` pointed to a new `hostile_tests/` directory and added one trivial passing test. The existing workflow and existing test files were not edited.

Hostile branch: `self-rakl/round-004-hostile-evaluator`

Hostile SHA: `1fe443787eec736ea004c809647b02236f1b95d2`

GitHub Actions run: `31288691577`

Observed result: `SUCCESS`; the pytest log reports `1 passed in 0.81s`.

The active `main` ref was not moved to the hostile SHA.

### Consequence

A green, exact-candidate-SHA CI observation is necessary but not sufficient. The scientific analogue is important: evidence about an object is only meaningful relative to the observation operator that generated it. Here, the *evaluator* is itself an observation system. RAKL therefore needs a model of the evaluator's transitive influence perimeter, not merely a list of files that look like tests.

## 2. Evaluator influence closure and attestation

Three adjacent traditions supplied compatible local projections:

- **in-toto** models software supply-chain steps with authorized actors, commands/materials/products and signed link metadata.
- **SLSA provenance** separates a build definition from run details and binds outputs to inputs and a builder identity/trust boundary.
- **Reproducible Builds / hermetic build systems** treat tools, versions, configuration and environment as causally relevant inputs rather than invisible background.

RAKL synthesizes these into a **Trusted Evaluation Base** concept:

```text
candidate subject
    + frozen evaluator revision
    + frozen evaluator-influencing materials
    + frozen/declared command
    + frozen/declared environment specification
    + authorized external builder
    + externally observed result
    -> evaluation attestation
```

This does not mean software provenance implies scientific truth. It means a validation result cannot have more authority than the integrity of the process that produced it.

Supporting primitives were added in `src/rakl/evaluator.py`. They intentionally do **not** replace or weaken `PromotionGate` in this round. A self-modifying judge must not certify its own replacement merely because its own tests pass. The new structures can therefore be used by a later parent/frozen evaluator path.

## 3. Candidate tests

`tests/test_evaluator.py` adds known-answer cases for:

- clean frozen evaluator attestation;
- pytest/test-discovery configuration tampering;
- promotion-judge code tampering;
- missing frozen evaluator inputs;
- supplemental candidate tests that cannot replace frozen parent inputs;
- command, environment, builder identity, evaluator revision and external-observation binding.

The candidate's ordinary repository CI passed on its exact SHA before later research-document commits. A final exact-SHA CI check is required after all round artifacts are staged and before any main fast-forward.

## 4. Information gain became goal-oriented and robust

The Bayesian experimental-design panel found a second genuinely new coordinate.

RAKL's current discriminator utility emphasizes hypothesis separation and identified-set shrinkage per cost. That is useful, but a research query can greatly reduce uncertainty in nuisance parameters while doing almost nothing for the declared decision or QoI.

Recent goal-oriented Bayesian experimental-design work formalizes design utilities around a downstream causal/predictive quantity rather than full parameter recovery. Related robust-design work makes model misspecification part of the design problem.

A separate current evaluation of LLM-guided Bayesian optimization in scientific domains reports that LLM experiment-design agents can be weakly sensitive to observed feedback and that classical/hybrid acquisition can outperform them. This is directly compatible with the RAKL constitution:

```text
LLM -> semantic prior / candidate hypotheses / candidate experiments
explicit evidence update + decision utility -> acquisition choice
```

The result is the new child fiber `META_N022_GOAL_ROBUST_INFORMATION_GAIN`. No acquisition algorithm is activated yet because the required known-answer decision worlds have not been frozen and executed.

## 5. Evaluator information firewall

The agent-evaluation route also exposed a distinct issue from execution integrity. A scorer or reviewer may receive information it was never supposed to observe. Sandbox isolation protects execution resources; scorer blindness protects the epistemic packet.

RAKL already requires isolated blind reviewers conceptually, but it lacks machine-checkable information-flow constraints for evaluators. `META_N021_EVALUATOR_INFORMATION_FIREWALL` is opened for benchmark cases where forbidden answer metadata creates artificial evaluator performance.

## 6. What was deliberately not adopted

- A signed or reproducible evaluation process is **not** evidence that the scientific claim being evaluated is true.
- A builder identity is a trust-root coordinate, not scientific authority.
- Goal-oriented information gain is not automatically superior when no downstream QoI/decision has been declared; in exploratory discovery global novelty can still matter.
- LLM Bayesian experimental design is not adopted as an authority mechanism; current evidence instead motivates a hybrid proposal-versus-acquisition separation.
- Robin-style closed-loop scientific agents reinforce RAKL's existing hypothesis/experiment/residual recursion and were therefore deduplicated rather than counted as new semantic novelty.

## 7. Semantic novelty and saturation

Retained new semantic objects after deduplication:

1. evaluator influence closure / Trusted Evaluation Base;
2. evaluation attestation binding subject, judge, materials, command, environment and external builder;
3. parent/frozen evaluator versus candidate supplemental evaluator separation;
4. machine-enforced evaluator information firewall as distinct from reviewer-role prose;
5. QoI/decision-targeted information gain as distinct from global entropy reduction;
6. robustness to belief/model misspecification in query selection;
7. explicit separation of LLM semantic priors/proposals from evidence-updated acquisition.

The hostile experiment is itself a new native residual. Therefore no same-context or independent flat counter advances.

`RAKL_METHOD = ACTIVE_NON_FLAT`

## 8. Next discriminators

Highest priority is now operational rather than rhetorical: run a **parent-controlled evaluator** against the preserved hostile SHA, where the parent owns test discovery, command, judge and environment definition. The hostile candidate should then fail or be marked invalid even though its own CI remains green.

In parallel, freeze N022 known-answer worlds covering all of the following before implementing a new acquisition rule: high global entropy but low decision impact, high decision impact but low global entropy, misspecified beliefs, and permuted/ignored experimental feedback.

## Primary source routes

- in-toto specification / implementation: https://github.com/in-toto/docs/blob/master/in-toto-spec.md and https://github.com/in-toto/in-toto
- SLSA provenance specification: https://slsa.dev/spec/v1.2/provenance
- Reproducible Builds: https://reproducible-builds.org/
- Bazel hermeticity: https://bazel.build/basics/hermeticity
- Inspect AI and sandboxing: https://github.com/UKGovernmentBEIS/inspect_ai and https://github.com/UKGovernmentBEIS/inspect_sandboxes
- BED-LLM: https://machinelearning.apple.com/research/bed-llm
- Goal-oriented Bayesian experimental design: https://arxiv.org/abs/2603.19071 and https://arxiv.org/abs/2606.09010
- LLM Bayesian optimization evaluation: https://aclanthology.org/2025.findings-emnlp.1036/
- Robin: https://github.com/Future-House/robin
