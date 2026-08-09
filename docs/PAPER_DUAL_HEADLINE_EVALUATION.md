# Paper Evaluation Strategy — Two Headline Claims

Status: preregistration-oriented paper planning; prospective empirical claims remain unvalidated until executed.
Date: 2026-08-09

## 1. Why the paper needs two independent headline demonstrations

RAKL makes two conceptually different claims:

1. **Method evolution:** an evidence-governed research framework can diagnose and improve parts of its own method while preserving evaluator separation, negative history and fresh transfer evidence.
2. **Scientific capability shaping:** the same base LLM can perform scientific discovery/reasoning more reliably when embedded in the RAKL architecture than under simpler matched workflows.

These should be evaluated separately. A framework that improves its own benchmark is not thereby a better scientist, and a framework that solves one discovery task well has not thereby demonstrated self-evolution.

## 2. Study A — Governed self-evolution

### Conditions

Compare at least:

```text
A0 fixed RAKL, no method updates
A1 generic self-reflection/self-editing
A2 development-benchmark-only evolution
A3 governed RAKL self-evolution
A4 governed RAKL evolution + external method assimilation
```

### Hidden-deficit construction

The initial method should contain known hidden deficits that are not named to the optimizing agent. Examples include omitted context splitting, missing evidence-lineage control, missing epistemic-cut reasoning, missing measurement/calibration reasoning or missing experiment-design operator.

Development tasks may reveal symptoms but not the operator label.

### Evaluation planes

Use three non-collapsed planes:

```text
DEVELOPMENT — optimizer-visible; may be reused
TRANSFER — unseen tasks testing reuse/generalization
ASSURANCE — fresh/blind reserve required for strong evolution claims
```

Assurance exposure is budgeted; repeated visibility consumes its independence value.

### Primary outcomes

```text
hidden weakness/operator detection precision and recall
fresh-assurance meta-QoI gain
meta-overfit frequency
blocking-invariant failure rate
negative-history preservation
cost per validated capability addition
cross-model transfer of learned operator
external-framework assimilation success/rejection accuracy
```

### Strong positive result

A strong result is not monotonic development score. It is repeated generations where governed RAKL produces positive fresh transfer more often than unconstrained/self-reflection baselines while producing fewer blocking failures and false operator inventions.

### Falsifier

If generic self-reflection or unconstrained self-editing achieves equal or better fresh transfer at lower cost without increased validity failures, the governed self-evolution layer has not earned its complexity.

## 3. Study B — Better scientific discovery with the same LLM

### Matched-system conditions

Use the exact same base model/version and freeze the evidence/tool budget.

Compare:

```text
B0 direct LLM / strong prompt
B1 retrieval-augmented LLM
B2 strong generic agentic workflow
B3 RAKL full system
B4 RAKL ablations
```

Where external systems cannot be run under matched resource conditions, use reproducible open implementations or restrict the claim to the matched baselines actually executed.

### Evaluation tiers

#### Tier 1 — known-answer mechanistic worlds

Synthetic/generated worlds with exact truth allow measurement of mechanism recovery, false contradictions, false merges, authority leakage, target reachability, epistemic cuts, experiment-selection regret and false saturation.

#### Tier 2 — retrospective real-science discovery

Use time-cutoff or retrospective-context-regression tasks. Provide only evidence available before the target conclusion; remove the published conclusion/hypothesis and retrospective causal wording. Evaluate whether the system reconstructs grounded, discriminating and testable hypotheses that agree with later evidence.

This is stronger than ordinary question answering because the conclusion is withheld.

#### Tier 3 — prospective real scientific case studies

Select real unresolved scientific tasks with public data/tools and domain-expert oversight. Freeze the evidence cutoff, hypothesis set, predictions and experimental/analysis plan before revealing new outcome data or running the registered validation.

At least one case should exercise a RAKL-specific mechanism such as cross-domain bridge discovery, missing-corner localization, mechanism separation, evidence-lineage correction or post-saturation formalism invention.

### Primary outcomes

```text
valid and grounded hypothesis rate
discriminating/testable hypothesis quality
mechanism or latent-process recovery
evidence uptake after counterevidence
experimental-plan completeness and configuration validity
authority leakage
false contradiction/merge/saturation
scientific value or mechanism separation per token/cost
```

### Falsifier

If RAKL does not outperform simpler matched workflows on the registered epistemic failure modes, or if gains disappear after cost matching, the scientific-capability claim must be narrowed or rejected.

## 4. Selective ablations

A strong methods paper should show that each claimed mechanism selectively prevents its registered failure mode.

Expected relationships include:

\[
RAKL-ContextAlignment \Rightarrow \uparrow FalseContradiction,
\]

\[
RAKL-AuthorityPoset \Rightarrow \uparrow CrossAxisAuthorityLeakage,
\]

\[
RAKL-NegativeHistory \Rightarrow \uparrow RefutedClaimResurrection,
\]

\[
RAKL-LineageSaturation \Rightarrow \uparrow FalseIndependence/FalseSaturation,
\]

\[
RAKL-Metacognition \Rightarrow \downarrow HiddenGapDetection,
\]

\[
RAKL-BoundedContext \Rightarrow \uparrow Cost \text{ or } \downarrow MandatoryEvidenceRecall.
\]

These are preregistered hypotheses, not assumed truths.

## 5. Real example requirement

For a first-tier journal, a purely architectural/software result is substantially less persuasive than a demonstration on real science. The recommended evidence ladder is:

```text
known-answer worlds
    +
retrospective real discoveries
    +
prospective real case study
```

The prospective case need not necessarily require a wet lab if a scientifically meaningful public-data or simulation result can be independently validated, but stronger external experimental validation materially strengthens the discovery claim.

## 6. Demonstrating 'experience becomes ability'

After a learning phase, remove most source text from active context and test held-out tasks using only the compact canonical atlas and procedural operator library.

Compare the compression-reconstruction curve and transfer performance before and after experience consolidation.

A positive result would show that RAKL is not merely repeatedly rereading the corpus: learned structure and procedures remain useful under much smaller active context.

## 7. Cross-model evidence

The framework should be tested across multiple capability tiers rather than one flagship model. At minimum use a compact/open or lower-cost model, a mid-tier model and a high-capability model, with exact versions frozen at execution time.

The strongest practical result would be evidence that RAKL reduces scientific-process failures for ordinary models and that some learned operators transfer across model backbones.

Do not require every model to improve: heterogeneous or negative effects are scientifically informative and should be reported.

## 8. Suggested headline figures

```text
Figure A — RAKL functional researcher state / cognitive architecture
Figure B — quantitative competence tensor and blocking constraints
Figure C — multi-generation self-evolution lineage with fresh-assurance gains/failures
Figure D — matched discovery benchmark across models and ablations
Figure E — selective failure-mode ablation map
Figure F — compression-reconstruction / token-efficiency curve
Figure G — real case-study epistemic path, missing corner, experiment and outcome
```

## 9. Publication claim boundary

If both studies succeed prospectively, the paper can support two distinct claims:

> RAKL provides evidence-governed, transferable self-improvement of scientific method components under scoped assurance.

and

> Under matched model, evidence, tools and resource budgets, RAKL changes the scientific error profile of an LLM and improves registered discovery/reasoning outcomes on specified domains/tasks.

Neither result alone authorizes a claim of universal scientific intelligence.
