# Paper 3 AI engineering metrics and figure programme

**Date:** 2026-08-10  
**Paper:** A Shared Structural Substrate for Data-Efficient Learning and Reasoning  
**Status:** preregistered reporting and visualization contract. No empirical efficiency result is asserted here.

## 1. Engineering question

Paper 3 should be written so that an AI engineer can answer, from the figures alone:

> Does a persistent evidence-bearing structural representation reduce the amount of data or inference work needed to reach the same capability, while preserving or improving transfer safety?

The strongest claim requires a **shared object** to contribute in both training/data selection and inference-time reuse. If the training and inference gains require unrelated representations, the unification claim must be split.

## 2. Reader map

| Reader | Question | Primary metric / display |
|---|---|---|
| ML training engineer | How many training tokens/examples/compute are saved at matched OOD capability? | learning curve and tokens-to-target |
| Inference engineer | Does reuse reduce model tokens, latency or search/tool work at matched correctness? | inference Pareto frontier |
| Retrieval/agent researcher | Does structure add signal beyond semantic/skill retrieval? | transfer-validity discrimination plot |
| Safety/reliability reader | Does structural reuse increase invalid or negative transfer? | Q2/Q3 acceptance-rejection matrix and risk plot |
| Systems architect | Is one-time induction worth it after retrieval/adaptation/verification overhead? | cumulative break-even curve |
| Representation-learning reader | Is the effect really tied to cross-domain structural redundancy? | redundancy-response curve and held-out-family analysis |
| Editor/nonspecialist | What is the one-sentence result? | matched capability with paired cost reduction and uncertainty |

## 3. Experimental unit and matched comparison

The experimental unit is the **task or evaluation item**. Repeated seeds are nested replicates, not independent tasks.

Every principal comparison must freeze:

- base model architecture and checkpoint;
- tokenizer;
- training optimizer/schedule where relevant;
- evidence/retrieval corpus;
- task set and held-out domains/families;
- context-window ceiling;
- tool permissions;
- maximum inference budget;
- evaluator and scoring code;
- random seed schedule.

When comparing training-data selection, the selected data may differ but the downstream training recipe must remain matched. When comparing inference reuse, the base model must remain frozen.

## 4. Core metric family A: structural signal beyond semantics

### 4.1 Transfer validity

For each candidate source-target mapping, define `transfer_valid = 1` only when the preregistered target QoI, typed relations, load-bearing invariants and required boundary conditions are preserved for the proposed transfer direction.

### 4.2 Incremental structural information

Compare a strong semantic/skill baseline against a model that adds witnessed structure. Report at least:

- held-out ROC-AUC and PR-AUC for transfer validity;
- held-out log loss or Brier score;
- calibration error;
- likelihood-ratio or predeclared nested-model comparison where assumptions permit;
- Q2 true-accept rate;
- Q3 false-accept rate.

The key engineering quantity is **incremental held-out value**, not raw structural-score accuracy.

### 4.3 Q2/Q3 safety pair

Report both:

`Q2_accept = valid low-semantic/high-structural transfers accepted / all valid Q2`

and

`Q3_false_accept = invalid high-semantic/low-structural transfers accepted / all Q3`.

A model that improves Q2 by accepting most Q3 decoys has failed the mechanism.

## 5. Core metric family B: training/data efficiency

### 5.1 Tokens to capability target

Freeze one or more structural-OOD capability thresholds before the learning curves are inspected.

For method `m`, define

`T_m(q*) = minimum cumulative training tokens required to reach frozen capability q*`.

The headline data-efficiency gain against parent `p` is

`training_token_reduction = 1 - T_RAKL(q*) / T_p(q*)`.

Report the same calculation for examples and, where measurable, training FLOPs/GPU-seconds.

### 5.2 Area under the learning curve

Report a normalized area-under-learning-curve quantity over a frozen token range so that methods that never cross the chosen target are still comparable. The integration grid and interpolation rule must be fixed in advance.

### 5.3 Structural OOD

Training efficiency is only central if capability is evaluated on:

1. **structure-known/domain-new** tasks;
2. **structure-family-held-out** tasks as a harder boundary;
3. ordinary in-domain tasks as a safety/retention check.

A gain only on in-domain accuracy does not support structural amortization.

### 5.4 Redundancy-response effect

Let `rho_S` denote a preregistered uncertainty-aware structural-redundancy level. The mechanism predicts that the RAKL-minus-parent cost advantage should increase as structural redundancy rises while surface-semantic diversity remains controlled.

Report a rank/monotone relationship and uncertainty, not a post-hoc fitted curve chosen for appearance.

## 6. Core metric family C: inference efficiency

### 6.1 Valid task success

Define `valid_success` as task correctness plus passing the registered transfer-validity and verification gates. Invalid transfer followed by a lucky correct answer is not a clean structural-reuse success.

### 6.2 Billable model tokens

Sum provider-reported input and output tokens across all inference calls, including retrieval planning, adaptation, criticism and verification. Report cache-hit and cache-miss tokens separately when available. Do not invent hidden chain-of-thought counts.

### 6.3 Cost per valid solve

For a matched task stratum:

`tokens_per_valid_solve = sum(billable inference tokens) / sum(valid_success)`.

Also report:

- provider cost per valid solve;
- median and p95 wall time;
- tool calls per valid solve;
- retrieval operations/bytes;
- search nodes or candidate expansions when available;
- verification tokens/cost separately.

### 6.4 Matched-capability inference saving

At a frozen success target `q*`, define

`inference_token_reduction = 1 - I_RAKL(q*) / I_parent(q*)`.

The budget schedule and interpolation rule are frozen before outcomes.

## 7. Core metric family D: amortization economics

The paper must not compare only online inference cost.

For a reusable structural library, track:

`C_total(n) = C_induction + C_training_delta + C_storage + C_retrieval(n) + C_adaptation(n) + C_reasoning(n) + C_tools(n) + C_verification(n)`.

For parent `p` and RAKL, report the cumulative difference over reuse count `n`.

### 7.1 Empirical break-even count

The empirical break-even is the smallest `n` for which the upper uncertainty bound on cumulative RAKL cost is no worse than the comparator while capability and invalid-transfer constraints are satisfied.

Report:

- point estimate `n*`;
- interval or sensitivity range;
- no-break-even when the condition is never reached in the registered horizon.

Do not truncate a no-break-even curve to make it appear favorable.

### 7.2 Reuse frequency and cache behavior

Record:

- structural-object cache hit rate;
- mean reuse count per object;
- fraction of objects never reused;
- retrieval false-positive rate;
- mean adaptation/verification overhead per hit.

This shows whether the claimed reusable substrate is actually reused in practice.

## 8. Core metric family E: representation and safety ablations

The shared object carries roles, typed relations, invariants, context, QoI, boundaries, evidence and directionality. The paper should ablate each load-bearing field.

Minimum ablations:

- remove directionality;
- remove QoI;
- remove boundary conditions;
- remove evidence identity;
- remove explicit non-preserved properties;
- replace structural witness with semantic similarity only;
- replace cross-domain object with a domain-specific skill label;
- disable verification after reuse.

Primary ablation outcomes:

- Q2 accept;
- Q3 false accept;
- valid task success;
- tokens per valid solve;
- empirical break-even count.

Ablation is scientifically useful even when an omitted field does not matter. Such a null narrows the object.

## 9. Main-figure plan

All main quantitative figures must use editable vector text, no text boxes over data, no arrows pointing to data points, no point-by-point text annotations, no overlapping marks/labels and no decorative gridlines. Panel letters remain outside the data region.

### Figure 1. Shared structural substrate and experimental logic

**Role:** orientation.  
**Archetype:** schematic-led composite.

Panel a shows one structural object used by both data selection and inference reuse. Panel b shows the Q1-Q4 semantic x structural benchmark. Panel c shows the matched training/inference evaluation and total-cost accounting. This figure carries no empirical performance claim.

### Figure 2. Does structure add information beyond semantics?

**Core conclusion to test:** witnessed structure predicts valid transfer beyond strong semantic/skill controls.

Recommended panels:

- **a** distribution or calibrated score separation for valid versus invalid transfer under the strongest semantic baseline and the structural model;
- **b** Q2 true-accept and Q3 false-accept with uncertainty;
- **c** held-out discrimination/calibration metrics across structure families;
- **d** held-out-family generalization.

Do not label individual examples. Representative cases belong in a separate table.

### Figure 3. Training sample efficiency

**Core conclusion to test:** structural selection reaches matched structural-OOD capability with fewer training tokens/examples.

Recommended panels:

- **a** structural-OOD performance versus cumulative training tokens, mean/median with the registered uncertainty band across seeds;
- **b** tokens-to-target for each method with interval;
- **c** compute-to-target where measured;
- **d** retention on in-domain and genuinely structure-new tasks.

Use the same uncertainty definition across comparable curves.

### Figure 4. Inference efficiency and safe reuse

**Core conclusion to test:** validated structural reuse shifts the task-success versus inference-cost frontier without increasing invalid transfer.

Recommended panels:

- **a** valid success versus billable inference tokens;
- **b** tokens per valid solve;
- **c** median/p95 latency or tool/search work;
- **d** Q2 accept versus Q3 false-accept safety frontier.

No data-point arrows or prose labels. Method identities belong in a shared legend outside dense data.

### Figure 5. Empirical amortization and break-even

**Core conclusion to test:** the one-time structural induction cost is recovered under realistic reuse.

Recommended panels:

- **a** cumulative total cost versus number of downstream uses for RAKL and strongest parent;
- **b** cumulative valid solves versus cumulative cost;
- **c** distribution/sensitivity of break-even count over workloads;
- **d** cost decomposition at a preregistered representative workload.

Do not draw a vertical arrow to `n*`. If a break-even estimate is shown, use a tick/reference line and state the number in the caption/table.

### Figure 6. Mechanism and ablation

**Core conclusion to test:** the gain depends on the scientifically scoped witness rather than an incidental implementation detail.

Use a forest/effect-size plot showing the change from full RAKL when each structural field is removed. Companion panels may show the redundancy-response effect and cross-family heterogeneity.

This figure is the main answer to reviewers who ask whether “structure” is merely another prompt/skill label.

## 10. Extended Data plan

1. per-model replication;
2. per-structure-family learning curves;
3. semantic-baseline calibration variants;
4. extraction-model dependence;
5. human-annotation agreement;
6. structure-library size and cache-hit distribution;
7. source-domain/target-domain matrix;
8. failure taxonomy for invalid transfer;
9. total token decomposition by retrieval/adaptation/reasoning/verification;
10. provider-dollar and GPU-time sensitivity;
11. success-threshold sensitivity;
12. break-even sensitivity to reuse frequency and induction cost;
13. performance on genuinely new structure families;
14. raw paired task-level differences.

## 11. Minimum headline table

For each principal method report:

- model/checkpoint;
- training tokens/examples selected;
- training tokens-to-target;
- structural-OOD success;
- in-domain success;
- Q2 accept;
- Q3 false accept;
- inference billable tokens/run;
- tokens per valid solve;
- tool calls/run;
- median and p95 latency;
- one-time induction cost;
- empirical break-even count or `NO_BREAK_EVEN`.

Every number must bind to an exact result receipt and experiment subject SHA.

## 12. Primary decision logic

The strongest paper claim survives only when all of the following hold:

1. witnessed structure adds held-out predictive value beyond a strong semantic/skill control;
2. Q3 false-accept remains below the preregistered ceiling;
3. structural selection improves training cost-to-structural-OOD capability against a strong parent in at least one declared redundancy regime;
4. frozen-model structural reuse improves inference cost-to-valid-success against a strong parent;
5. the same structural identity/object type is used across the training and inference arms;
6. cumulative total cost reaches a realistic break-even horizon after induction and verification are charged.

If only 1-2 hold, the paper is primarily about **safe structural transfer**. If 1-4 hold but 5 fails, it is two narrower engineering contributions rather than a shared substrate. If 1-5 hold but 6 fails, the representation may be scientifically useful but not economically amortizing.

## 13. Stop/scale rule

Do not authorize a large training run merely because the deterministic Q2/Q3 scaffold passes. Scale only after an independently annotated benchmark and a cheap model-level pilot show material incremental structural signal with acceptable Q3 safety. A null cheap pilot is a successful research outcome because it prevents expensive confirmation theater.