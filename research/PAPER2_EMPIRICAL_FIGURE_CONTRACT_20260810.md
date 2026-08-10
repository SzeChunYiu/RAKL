# Paper 2 empirical metric and figure contract

**Date:** 2026-08-10  
**Paper:** RAKL architecture / matched scientific-process evaluation  
**Status:** preregistered reporting contract; no empirical superiority numbers are asserted here.

## 1. Publication question

The empirical paper must answer a narrower question than whether RAKL can run a research workflow:

> At matched model capability and evidence access, does explicit epistemic control improve the reliability-cost frontier of LLM-mediated scientific research?

The reporting layer must therefore show **scientific validity and resource cost together**. A lower token count is not a win if it is obtained by skipping evidence, verification or contradiction handling.

## 2. Reader map

Different readers should be able to find one decisive visual answer without reading the whole architecture.

| Reader | Primary question | Main display |
|---|---|---|
| AI systems engineer | Does RAKL buy more valid work per token, dollar and second? | reliability-cost Pareto plot |
| Scientific-methods reader | Does RAKL reduce scientifically dangerous process failures? | defect/risk effect-size plot |
| Retrieval/agent researcher | Is the gain architecture rather than simply more evidence access? | architecture x evidence-access interaction plot |
| Discovery researcher | Does open-world mechanism discovery find functionally relevant work beyond lexical search? | discovery-budget curve |
| Editor/nonspecialist | What is the single empirical headline and its uncertainty? | one paired headline effect with raw task-level distribution |

## 3. Frozen measurement units

### 3.1 Valid scientific success

For each task-run, define `valid_scientific_success = 1` only when the final answer/task outcome is correct **and** every preregistered hard scientific-process gate passes. The gate vector includes, where applicable:

- no unsupported authority upgrade;
- no unresolved contradiction hidden by synthesis;
- required evidence roots present;
- estimand/QoI and context aligned;
- negative history preserved;
- hidden defect correctly detected or explicitly blocked;
- evaluator/corpus identity valid.

Report the individual gate coordinates as well as the conjunction. Do not hide a safety failure inside an average quality score.

### 3.2 Billable token cost

`billable_tokens` is the sum of provider-reported input and output tokens over **all** model calls in the run, including planner, critic, verifier and recovery calls. Report cached and uncached input separately if the provider exposes them. Do not invent hidden chain-of-thought token counts that the provider does not expose.

Also record:

- retrieval query tokens where separately billed;
- embedding/reranking tokens where separately billed;
- tool-call count;
- retrieved bytes/documents;
- wall time;
- provider currency cost at the frozen price sheet;
- deterministic preprocessing time and any one-time index/atlas construction cost.

### 3.3 Cost per valid success

For a matched stratum `s`,

`tokens_per_valid_success(s) = sum(billable_tokens) / sum(valid_scientific_success)`.

The same denominator is used for dollars and wall time. If a method has zero valid successes in a stratum, the cost-per-success value is infinite rather than silently omitted.

### 3.4 Matched token reduction

When two arms reach the same preregistered success target `q*`, define

`token_reduction_at_target = 1 - T_RAKL(q*) / T_parent(q*)`,

where `T(q*)` is the token budget required to reach the frozen target. Interpolation is allowed only when the budget schedule and interpolation rule were registered before outcomes were inspected.

### 3.5 Process-risk metrics

Report at minimum:

- hidden scientific-defect detection rate;
- unsupported authority-upgrade rate;
- counterevidence uptake rate;
- negative-history recovery rate;
- mandatory-evidence omission rate;
- false block rate;
- missed block rate;
- evaluator/corpus identity failure rate;
- ontology-conditioned discovery miss rate.

For binary outcomes report numerator, denominator and uncertainty. Do not report only percentages.

## 4. Statistical contract

The experimental unit is the **task**, not an individual model message. Repeated seeds/runs are nested inside task and model condition.

Primary comparisons are paired by:

- task;
- base model/version;
- evidence-access arm;
- resource ceiling;
- evaluator;
- seed schedule where stochasticity is present.

Report effect sizes and 95% intervals. Use task-level paired bootstrap intervals for descriptive contrasts and a preregistered hierarchical model for architecture x evidence-access interaction. Do not treat repeated messages from one task as independent replicates.

The paper should distinguish confirmatory outcomes from exploratory diagnostics. Multiplicity correction applies to the registered confirmatory family.

## 5. Main-figure plan

All quantitative figures use editable vector text, no opaque text boxes, no arrows pointing to data points, no prose callouts inside the data region, and no overlapping labels. Panel letters live outside the data region. Raw values remain available as source data.

### Figure 1. System and evaluation contract

**Role:** orientation, not empirical proof.  
**Archetype:** schematic-led composite.

Show the controlled scientific-state loop and the matched architecture x evidence-access design. Keep the architecture schematic free of quantitative claims.

### Figure 2. Reliability-cost frontier

**Core conclusion to test:** RAKL changes the valid-scientific-success versus resource-cost frontier.

Panels:

- **a** valid scientific success versus total billable tokens;
- **b** valid scientific success versus provider cost;
- **c** valid scientific success versus wall time;
- **d** paired task-level token difference at the frozen success target.

Use one point/interval per architecture within each evidence-access arm, plus a clearly defined Pareto frontier. Do not annotate individual points with text. Method names belong in a legend outside dense data or in fixed-axis labels.

Primary numbers to report in the text:

- absolute success-rate difference;
- relative/absolute token change at matched validity;
- cost per valid success;
- fraction of task strata in which RAKL is Pareto-dominated or Pareto-dominant.

### Figure 3. Scientific-process failure profile

**Core conclusion to test:** any gain comes from fewer scientifically consequential process failures, not merely longer reasoning.

Use an effect-size/forest style plot for the registered risk coordinates. Each row shows RAKL minus parent risk with a 95% interval. A second panel may show raw numerator/denominator counts.

Required rows include unsupported authority upgrade, missed hidden defect, mandatory-evidence omission, failed counterevidence uptake, negative-history loss and false/missed block.

No radar charts. No text labels over marks.

### Figure 4. Architecture x evidence-access interaction

**Core conclusion to test:** architecture contributes beyond simply granting more evidence.

Use small multiples or an interaction plot over `public`, `curated` and `complete sealed` evidence arms. The primary y-axis is valid scientific success. A companion panel shows tokens per valid success.

The figure must make it visually possible to distinguish:

- evidence ceiling;
- architecture effect at fixed evidence;
- whether the architecture effect disappears with complete evidence;
- whether RAKL simply consumes more evidence/tool calls.

### Figure 5. Prospective OWMD discovery-budget curve

**Core conclusion to test:** function-first/open-world routing improves discovery of relevant hidden mechanisms under a fixed search budget.

Panels:

- valid hidden-mechanism recall versus search/tool budget;
- false-discovery/irrelevant-route rate versus budget;
- recall split by lexical distance or hidden-name condition;
- optional paired improvement over the strongest query-expansion/search parent.

Do not label individual discovered papers or points inside the plot. Examples belong in the legend/caption or a separate table.

## 6. Extended Data / supplementary figures

Reserve main-paper space for the causal evidence chain. Put the following in Extended Data unless they become central after results:

1. per-model replication;
2. per-evidence-topology strata;
3. token decomposition by planner/retriever/verifier/recovery;
4. latency distribution and p95 tail;
5. tool-call/retrieval-volume decomposition;
6. ablations for provenance, negative history, context/QoI gate and evaluator identity;
7. calibration/reliability plots for block decisions;
8. sensitivity to success threshold and budget schedule;
9. raw-task paired scatter or slopegraph when useful;
10. failure taxonomy with representative textual examples in a table rather than plot annotations.

## 7. Minimum headline table

The empirical manuscript should contain one compact table with, for every principal arm:

- number of tasks;
- number of seeds;
- valid scientific success rate;
- billable tokens/run;
- tokens per valid success;
- provider cost/valid success;
- median and p95 wall time;
- unsupported authority-upgrade rate;
- hidden-defect detection rate;
- QOI/context failure rate where applicable.

Every quantity must have an exact machine-readable source receipt.

## 8. Figure QA rules

Before any empirical figure is accepted into the manuscript:

1. render at final physical size;
2. inspect every panel separately;
3. verify 5 pt minimum rendered glyph size and editable PDF/SVG text;
4. verify no text overlaps marks, intervals, axes or neighboring panels;
5. verify no `annotate`/arrow callouts to data;
6. verify no opaque text `bbox` masks;
7. verify uncertainty definitions are consistent across comparable panels;
8. verify all axis labels include units where a physical/cost unit exists;
9. verify every plotted aggregate maps to task/seed-level source data;
10. verify the caption states `n`, unit of replication, center and interval definition.

## 9. Publication decision rule

A publishable empirical claim requires a matched result, not merely a successful architecture demo.

The central RAKL efficiency claim is supported only if a strong parent is beaten on at least one preregistered validity-cost frontier without a compensating scientifically material failure coordinate. A pure token reduction accompanied by lower valid success, higher unsupported-authority upgrades or higher hidden-defect miss rate is not a positive result.

A null result should remain publishable as a bounded result if it is sufficiently powered and reveals which RAKL mechanisms do or do not add value.