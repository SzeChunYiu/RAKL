# RAKL Quantitative Evaluation Model

Status: candidate measurement architecture; research-only; no scalar score can override blocking scientific invariants.
Date: 2026-08-09

## 1. Why RAKL needs a measurement model

A publish-grade research framework cannot be evaluated only by final-answer accuracy or by the number of modules it contains. RAKL claims to shape scientific reasoning, reduce epistemic failure modes, improve resource efficiency, support discovery, and recursively improve its own method. Each claim therefore needs a distinct observable and a frozen comparison protocol.

The measurement object is a **context-indexed research competence tensor**, not a universal intelligence score.

For system architecture `A`, base model `M`, domain `d`, research fiber `f`, task class `t`, resource profile `b`, and evidence cutoff `c`, define

\[
\mathbf Q(A,M;d,f,t,b,c)
=
(V,E,D,X,P,G,L,R,C),
\]

where the coordinates are defined below.

## 2. Core competence coordinates

### V — epistemic validity

Measures whether conclusions have the authority actually supported by evidence.

Primary diagnostics:

\[
ALR=\frac{\text{unsupported authority upgrades}}{\text{authority transitions attempted}},
\]

\[
FCR=\frac{\text{false contradictions}}{\text{comparable claim pairs}},
\]

\[
FMR=\frac{\text{false merges/equivalences}}{\text{equivalence decisions}},
\]

plus identified-set coverage, source hallucination rate and blocking-invariant violations.

Blocking validity violations are never compensated by high scores elsewhere.

### E — evidence use and revision

Measures whether evidence changes the epistemic state appropriately.

\[
EUR=\frac{\text{decisive counterevidence events producing licensed revision}}{\text{decisive counterevidence events}},
\]

\[
NHR=\frac{\text{relevant prior negative-history items recovered}}{\text{relevant negative-history items}},
\]

and evidence-lineage independence accuracy.

### D — discovery capability

Discovery is decomposed into grounded novelty, discriminability and prospective usefulness.

Suggested metrics:

```text
valid-hypothesis rate
grounded-novelty rate
discriminating-hypothesis rate
time-cutoff rediscovery rate
prospective hypothesis ranking against later outcomes
novel target/path discovery recall
```

A hypothesis is not successful merely because it is linguistically novel.

### X — explanatory/mechanistic competence

Measures whether the system reconstructs mechanisms rather than merely predicts labels.

Known-answer worlds can measure:

```text
mechanism recovery accuracy
assumption recovery
causal-direction accuracy
observation-model correctness
latent-process recovery
explanation-gap rate
```

For compressed learned states, define a compression-reconstruction curve

\[
Q_{rec}(\rho),
\]

where `rho` indexes retained context/storage and `Q_rec` is held-out explanation/prediction quality.

The area under this curve is a diagnostic of how much reusable scientific structure has been learned per unit of active context.

### P — experimental planning and active inquiry

Measures whether proposed experiments actually discriminate scientific alternatives.

Where ground truth is available:

\[
Sep(a)=\min_{z_i\ne z_j}d(\mathcal Y(z_i,a),\mathcal Y(z_j,a)),
\]

or use expected information gain when calibrated probability models are justified.

Normalize by cost:

\[
PE=\frac{\text{mechanism separation or identified-set shrinkage}}{\text{experiment cost}}.
\]

Also measure main-experiment completeness, ablation completeness, resource/configuration validity and reproducibility.

### G — metacognition and gap discovery

Measures whether RAKL identifies weaknesses, missing ontology classes and missing operators.

For hidden-gap tasks:

\[
Precision_{gap}=\frac{\text{correctly proposed real gaps}}{\text{all gap proposals}},
\]

\[
Recall_{gap}=\frac{\text{correctly detected hidden gaps}}{\text{true hidden gaps}},
\]

plus false-operator invention rate and time/cost to diagnosis.

Calibration metrics such as Brier score or ECE may be used only where probabilistic forecasts are explicitly elicited and comparable.

### L — learning, transfer and self-evolution

For parent method `A_t` and challenger `A_{t+1}`, define development and fresh-assurance gains separately:

\[
\Delta_D = Q_D(A_{t+1})-Q_D(A_t),
\]

\[
\Delta_A = Q_A(A_{t+1})-Q_A(A_t).
\]

Strong scoped self-evolution evidence requires positive transfer/fresh assurance with all blocking invariants clean.

Additional diagnostics:

```text
cross-domain transfer gain
cross-model/backbone transfer gain
meta-overfit frequency
cost per validated method improvement
external-method assimilation gain
negative-transfer frequency
```

### R — robustness and reproducibility

Measure variation across:

```text
model backbones
context budgets
random seeds
search providers/tool availability
domains
task wording
execution environments
```

Report failure distributions, not only means. Exact artifact identity and provenance are separate reproducibility coordinates.

### C — engineering efficiency

Measure scientific value per compute/context/storage cost.

Core diagnostics include:

\[
TokenEfficiency=\frac{\text{valid decision/discovery value}}{\text{input+output tokens}},
\]

\[
ContextDensity=\frac{\text{mandatory+useful epistemic coverage}}{\text{active-context tokens}},
\]

\[
StorageAmplification=\frac{\text{canonical archive bytes}}{\text{active working-set bytes}},
\]

plus latency, monetary cost, retrieval cost, cache hit rate, and reproducible valid-result throughput.

## 3. Research taste / agenda selection

For a candidate goal `g`, evaluate a vector rather than one aesthetic score:

\[
\mathbf A(g)=(I,N,T,S,C,R),
\]

where `I` is importance, `N` unresolved novelty, `T` tractability, `S` mechanism/decision separation potential, `C` cost and `R` risk.

Known-answer or retrospective historical tasks can test whether the system ranks high-leverage questions above irrelevant but easy questions. Human/expert evaluation is appropriate for dimensions that have no objective oracle, but evaluator identity and inter-rater reliability must be reported.

## 4. Pathfinding and missing-corner metrics

For target `tau`, let `H*` be the true minimal support hypergraph and `B*` the true minimal epistemic cut in known-answer worlds.

Measure:

\[
PathRecall=\frac{|H_{pred}\cap H^*|}{|H^*|},
\]

\[
CutRecall=\frac{|B_{pred}\cap B^*|}{|B^*|},
\]

and false bridge/unsupported-edge rate.

In real science where the true support graph is not known, use adjudicated evidence packets and prospective target validation.

## 5. Saturation quality

RAKL should be rewarded for stopping when additional search is no longer decision-relevant, not for reading the most papers.

Measure:

```text
semantic novelty yield per search cost
false saturation rate
unnecessary-search cost after effective closure
native-residual reopening recall
independent-lineage saturation precision
```

A literature-saturated but scientifically unresolved task is not counted as closed.

## 6. No universal scalar objective

The primary result should be a Pareto profile under blocking constraints:

\[
\max \mathbf Q
\quad \text{s.t.}\quad
\Lambda_{validity}=1.
\]

A weighted scalar may be used for a declared application only after weights and normalization are frozen. It must never allow a validity regression to be hidden by efficiency or novelty gain.

## 7. Statistical design

For matched framework comparisons:

```text
same base model/version
same evidence universe and cutoff
same tools or explicitly resource-sensitive attribution
same token/time/monetary budget
same hidden task labels
same evaluator
randomized task order
multiple independent seeds where stochastic
predeclared primary metrics
confidence intervals / effect sizes
correction for multiple primary hypotheses when appropriate
```

Use paired designs where the same task is evaluated under baseline and RAKL conditions. Report null and negative effects.

## 8. Capability tensor as the optimization target

A normal LLM should not be expected to be uniformly strong. RAKL's engineering objective is to learn a policy

\[
\Pi^*(a\mid f,\gamma,M,b)
\]

that chooses the smallest admissible scaffold/operator giving the best competence vector for that atomic operation and context.

This turns framework optimization into a measurable contextual control problem rather than architecture accumulation.

## 9. Publication minimum

A strong paper should report, at minimum:

```text
process validity metrics
discovery/hypothesis metrics
experiment-design metrics
self-evolution transfer metrics
context/cost efficiency
ablation selectivity
cross-model robustness
real-case-study outcomes
artifact/reproducibility evidence
```

The paper should not claim general scientific superiority if improvement is limited to a subset of these coordinates or domains.
