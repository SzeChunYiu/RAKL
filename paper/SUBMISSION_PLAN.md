# RAKL Submission Plan

Status: manuscript engineering plan; final venue selection may be revisited after results.

## 1. Preferred positioning

Primary positioning: a **computational scientific methodology for evidence-governed LLM research**, with two linked empirical demonstrations:

1. governed method self-evolution;
2. improved scientific discovery/model construction in a real quant-finance application.

The methods paper should remain intelligible even if the quant application result is null: the application then becomes evidence about where RAKL does and does not improve scientific work rather than a narrative requiring predictive success.

## 2. Candidate venue strategy

The cleanest first target is a top-tier computational-science or machine-intelligence journal that accepts substantial computational methodology plus extensive benchmarking and real scientific applications. The final choice should depend on the observed center of gravity:

- if the strongest result is the scientific-method formalism + broad computational benchmarking + quant application, prioritize a computational-science venue;
- if the strongest result is model/agent capability shaping and governed self-evolution across LLM backbones, prioritize a machine-intelligence venue.

Do not tailor claims to the venue before the registered results are known.

## 3. Main-text story

Use a compact causal story:

```text
Problem: fluent agents lack explicit scientific authority transitions
   -> RAKL formalism
   -> executable bounded-context research architecture
   -> selective failure-mode benchmarks / ablations
   -> governed self-evolution
   -> real quant-finance discovery case
   -> limitations and falsifiers
```

The paper should not read as a chronological repository diary.

## 4. Six primary display items

### Figure 1 — RAKL scientific cognitive architecture

Show the functional researcher state

\[
\mathfrak R_t=(K_t,Z_t,\Omega_t,\Pi_t,G_t,M_t,X_t,R_t)
\]

and the proposal/evidence/state-transition loop.

### Figure 2 — Contextual Knowledge Atlas and scientific authority

Combine:

- local source/derived charts;
- transition maps;
- obstruction/non-forced gluing;
- multi-axis authority poset;
- target support path / missing epistemic cut.

This figure replaces a generic knowledge-graph picture.

### Figure 3 — Defining-controls ablation benchmark

Show full RAKL versus registered ablations on their predicted failure modes:

```text
false contradiction
false merge
authority leakage
negative-history loss
false saturation
hidden-gap miss
context cost
```

### Figure 4 — Governed self-evolution lineage

Show method generations, including failed/meta-overfit generations:

```text
M0 -> M1 -> M2 -> ...
```

with development gain, fresh assurance gain, blocking failures, cost and challenger source.

### Figure 5 — Quant-finance scientific application

Show the causal application architecture:

```text
microstructure evidence ----\
                            -> descriptive spot atlas
 global crypto state -------/          |
                                        -> predictive 5m/15m spot path
                                                   |
                                         oracle / contract transform
                                                   |
                                           downstream Polymarket
```

Polymarket must be visually downstream from spot validation.

### Figure 6 — Matched LLM and spot-prediction results

One composite publication display may contain:

- matched workflow competence profile;
- 5m/15m predictive proper-score/calibration/transport result;
- scientific value per token/cost.

If journal format makes the composite too dense, move cost/robustness to Extended Data and keep the main display focused on the two preregistered headline outcomes.

## 5. Extended data / supplementary figures

Recommended:

1. closest-work component matrix;
2. evidence-lineage saturation example;
3. bounded-context compression/reconstruction curve;
4. method-assimilation lifecycle;
5. detailed hidden-defect confusion matrix;
6. all self-evolution generations and nulls;
7. spot descriptive atlas across contexts;
8. full predictive baseline ladder and ablations;
9. leave-day/coin/venue transport;
10. release/provenance graph.

## 6. Result-slot closeout

`paper/RAKL_MANUSCRIPT.md` contains blocking tokens of the form:

```text
[[RESULT:...]]
```

No submission artifact is ready while any blocking result token remains. Each slot must be filled from an exact machine-readable result receipt, not from manual copy/paste of notebook output.

Required headline slots currently include:

```text
E1_KNOWN_ANSWER
E3_MATCHED_WORKFLOW
E4_SELF_EVOLUTION
E2_SPOT_PREDICTIVE
```

## 7. Statistical reporting

For every primary comparison report:

```text
estimand
population and cutoff
base model / configuration
tools / resources
paired or independent design
sample size and effective clusters
point estimate
confidence interval / uncertainty method
multiplicity policy
material threshold
MDE or power where applicable
negative/null result branch
cost accounting
```

Do not report only p-values or only model averages.

## 8. Real quant case

The quant application should report both:

### Descriptive result

A multiscale contextual atlas of spot movement at 5m/15m with event-level supporting structure, including which representations survive, which mechanisms remain only partially identified, and what observations/contexts block stronger claims.

### Predictive result

A frozen target-aligned tournament on identical causal rows, centered on

\[
\Delta_{joint}=\min(R_D,R_G)-R_{DG}.
\]

The publication remains scientifically valid if the result is `MICRO_PARENT_WINS`, `GLOBAL_PARENT_WINS`, `SIMPLE_BASELINE_WINS`, `UNDERPOWERED` or `REFUTED`; those outcomes change the conclusion rather than invalidate the study.

## 9. Reproducibility package

Final submission package should bind:

```text
RAKL source SHA
polymarket_crypto source SHA
frozen preregistrations
benchmark/task packets
base-model identifiers/configuration
source/data manifests and acquisition instructions
transformation code/environment
result receipts
figure/table source data
manuscript source
rendered manuscript
artifact manifest
```

A fresh-machine reproduction should be attempted by an independent context before submission.

## 10. Required disclosure and authorship cleanup

Before submission add:

```text
author affiliation
ORCID
corresponding-author information
competing interests
data availability
code availability
LLM/AI assistance disclosure
acknowledgements/funding
```

Language models must be described as tools rather than authors.

## 11. Submission gate

The project is `SUBMISSION_READY` only when:

1. all blocking manuscript result slots have exact receipts;
2. primary ablations/baselines are complete or the claim has been narrowed before unblinding additional evidence;
3. the quant application has untouched/forward evidence;
4. self-evolution has fresh assurance evidence;
5. independent novelty, statistics/method and artifact reviews are complete;
6. figures/tables regenerate from receipts;
7. final artifact manifest verifies;
8. no unresolved blocking validity issue is hidden behind a scalar performance gain.
