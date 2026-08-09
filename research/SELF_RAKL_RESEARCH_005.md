# SELF_RAKL_RESEARCH_005

## Scope

Round 005 recursively applied RAKL to evaluator integrity, saturation independence, and experiment selection. The Constitution was unchanged. The active `PromotionGate` was not replaced.

## Expert panel

The round used five preassigned lenses before the native experiment:

1. CI/evaluator-security engineer: separate trusted judge code from candidate-controlled execution and attack the trust boundary.
2. Scientific-reproducibility engineer: bind observation to parent/candidate revisions and evaluator-affecting inputs.
3. Research-synthesis statistician: attack false independence caused by shared evidence lineage.
4. Decision-theoretic experimental-design scientist: compare global information gain with QoI/decision-targeted and misspecification-robust design.
5. Adversarial red-team reviewer: construct a green candidate result that the trusted observer should reject.

## Frozen discriminator

Before implementation, `SELF_RAKL_RESEARCH_005_FROZEN_BENCHMARK.json` predicted that a candidate could redirect pytest discovery to a trivial-only directory and still obtain green candidate-controlled CI, while a separately trusted parent observer should reject the evaluator-input change without executing candidate code.

## Supporting implementation

The candidate added `src/rakl/parent_evaluator.py`, hostile known-answer tests, and `.github/workflows/trusted-parent-evaluator.yml`.

The parent observer has a deliberately narrow authority boundary. It runs the evaluator implementation from the trusted default-branch revision, checks out the candidate only as passive data, uses `contents: read`, disables persisted checkout credentials, and compares parent-owned evaluator inputs by content hash. Candidate-added tests are supplemental: they may exist, but cannot edit, delete, replace, or symlink a parent-owned test or evaluator input.

Candidate SHA `b8287ad05dcaf3242c354178617df7977e1826d2` ran 59 tests successfully before promotion. `main` remained the frozen incumbent during the verdict, the candidate was a non-divergent fast-forward, and only then was `main` advanced. The resulting main push CI also succeeded.

## Native hostile experiment

After the trusted observer existed on `main`, a fresh hostile branch changed only `pyproject.toml` so pytest discovered `hostile_tests`, then added one trivial passing test. Pull request 1 was explicitly marked as a negative-control experiment and never intended for merge.

The candidate-controlled pull-request test succeeded with `1 passed in 0.71s`.

The separately trusted `workflow_run` observer then checked out trusted parent `b8287ad05dcaf3242c354178617df7977e1826d2` and hostile source head `f4e5a5ac563a067a39a17d91469e41401fdaaeb4`, verified both revisions, and rejected the candidate because `pyproject.toml` differed from the parent-owned evaluator input. The hostile PR was closed unmerged and its branch remains negative evidence.

This is a direct native demonstration that candidate-controlled green CI and parent-controlled evaluator integrity are different projections. Neither should be silently promoted into the other.

## Residual discovered inside the positive experiment

The PR test run exposed a second identity coordinate. Its Actions API `head_sha` was the source-head candidate `f4e5a5ac...`, but `actions/checkout` actually executed synthesized merge commit `33a8f0aea308ab6b26410f85dbb074159ed8517e`. The parent observer inspected source head `f4e5a5ac...`.

Therefore `exact candidate SHA` is underspecified for pull-request evaluation. RAKL now opens `META_N024_INTEGRATION_SUBJECT_IDENTITY`: source head, base revision, synthesized integration/merge revision, and actually executed revision must be recorded separately. Round 005 does not claim this residual is solved.

## Independent research route: evidence lineage

Meta-analysis methodology supplies a useful projection for RAKL saturation. Published items are not necessarily independent evidence units. Reuse of a sample, control group, dataset, partial data, or upstream evidence can cause double counting and overstated precision. RAKL's current `ResearchRound.independent: bool` does not represent this ancestry.

The retained challenger is `META_N023_EVIDENCE_LINEAGE_INDEPENDENCE`: future independent-flat counting should depend on evidence lineage, not merely different papers, agents, route names, repositories, or wording. This is research-only in round 005; saturation behavior was not changed without an executable frozen parent benchmark for the new rule.

## Independent research route: goal-robust information gain

Recent goal-oriented Bayesian experimental-design work reinforces the distinction between reducing global parameter uncertainty and reducing uncertainty that changes a declared predictive or decision QoI. Robust/generalized/maximin Bayesian-design work adds the complementary warning that ordinary information-gain policies can be brittle under misspecified models or likelihoods.

This reinforces `META_N022_GOAL_ROBUST_INFORMATION_GAIN` but does not activate a new acquisition policy. RAKL must first freeze worlds with nuisance uncertainty, decision-relevant uncertainty, model misspecification, and ignored/permuted feedback.

## Security scope

Official GitHub guidance treats `workflow_run` as a potentially privileged context and warns against running untrusted code there. The round therefore uses candidate checkout only as passive data and executes trusted parent code with read-only repository permission. This reduces one important attack surface but is not a proof of complete sandbox or supply-chain security. Third-party action identity, runner image, Git client behavior, GitHub platform semantics, and future evaluator dependencies remain part of the wider Trusted Evaluation Base.

## Saturation verdict

`RAKL_METHOD = ACTIVE_NON_FLAT`.

The round retained at least three non-duplicate semantic objects: passive parent-controlled evaluator integrity validated by a native hostile experiment; evidence-lineage-aware independence for saturation; and integration-subject identity separating source head from synthesized/executed revision. Goal-robust information gain was reinforcing rather than counted as a wholly new fiber because it was already opened in round 004.

Same-context flat rounds: 0. Independent flat rounds: 0. The native integration-identity residual explicitly reopens evaluator integrity work.

## Next AI

First freeze executable known-answer worlds for `META_N024_INTEGRATION_SUBJECT_IDENTITY` and make the observer bind source head, base, synthesized integration revision/tree, and actual executed revision without trusting candidate-produced metadata. Then freeze `META_N023_EVIDENCE_LINEAGE_INDEPENDENCE` worlds before changing `SaturationTracker`. In parallel, continue `META_N022` with decision-QoI and misspecification stress tests. Preserve PR 1 and `self-rakl/round-005-hostile-evaluator` as negative evidence.
