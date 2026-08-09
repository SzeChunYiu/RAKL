# RAKL Paper Strategy

Status: publication planning document  
Date: 2026-08-09  
This document does not change active RAKL behavior.

## 1. Recommended paper positioning

Do not position RAKL primarily as another “AI scientist,” multi-agent scaffold, or end-to-end research automation system.

Position it as a **scientific-method layer for LLM-mediated research**: a theory and executable protocol governing how partial source views, hypotheses, experiments, contradictions, residuals, and method changes acquire or fail to acquire epistemic authority.

Recommended working title:

> **RAKL: An Evidence-Governed Recursive Atlas Method for Scientific Research with Large Language Models**

Alternative:

> **Recursive Atomic Knowledge Lattices: A Formal Method for Evidence-Governed LLM Scientific Inquiry**

## 2. Core thesis

Current autonomous-science systems increasingly automate literature search, hypothesis generation, experimentation, data analysis, and manuscript production. The open methodological question is not only whether an agent can execute these stages, but **what rules make its evolving internal research state scientifically defensible**.

RAKL addresses that question by separating:

```text
generation
from
authority
```

and by representing scientific knowledge as a recursively expandable atlas of scoped projections rather than one continuously rewritten answer.

The paper should argue and test that this architecture prevents specific epistemic failure modes that outcome-only evaluation can miss.

## 3. Contribution statement

The introduction should make four contribution classes explicit.

### C1 — Formal epistemic state

Define a RAKL knowledge state containing:

- contextual source/derived charts;
- typed and scoped transition relations;
- hypotheses/mechanisms/identified sets;
- obstructions and residuals;
- evidence/provenance;
- immutable negative history;
- open atomic fibers;
- semantic/lineage saturation state.

### C2 — Evidence-governed update calculus

Define a proposer/evidence separation:

```text
LLM or agent -> proposes
verification/evidence -> authorizes
state transition -> records positive/null/refuted/partial/blocked outcomes
```

No language-model confidence is an authority transition.

### C3 — Recursive inquiry and stopping

Residuals route inquiry into the smallest implicated child fibers. Search and review stop only under semantic, route, and evidence-lineage criteria, and native residuals reopen local saturation.

### C4 — Governed self-application

RAKL applies its own method to RAKL. Method challengers face frozen evaluation and a protected evaluator boundary, creating an experimentally testable form of scientific-method self-improvement rather than unconstrained prompt mutation.

## 4. What the paper must not claim as novel

The related-work section should explicitly credit prior traditions for:

- model pluralism and perspectival realism;
- sheaf/local-to-global consistency;
- AGM-style belief revision and truth maintenance;
- partial identification;
- Bayesian/goal-oriented experiment design;
- POMDP science planning;
- surprise-driven discovery;
- sequential falsification;
- provenance and ontology-guided knowledge construction;
- multi-agent/end-to-end AI scientists;
- semantic stopping.

The novelty argument should be **compositional and operational**, not ingredient-based.

## 5. Closest-system comparison axes

For every compared system, code each feature as:

```text
EXPLICIT
PARTIAL
NOT_ESTABLISHED_IN_REVIEWED_SOURCE
NOT_APPLICABLE
```

Never code an absence as “does not exist” merely because it is absent from an abstract.

Required axes:

1. source/context projection before hypothesis competition;
2. typed representation/equivalence relations;
3. non-forced global synthesis / identified-set output;
4. mechanism authority separated from predictive authority;
5. proposal versus evidence authority separation;
6. exact claim/evidence provenance;
7. null/refutation history preservation;
8. residual-driven recursive decomposition;
9. active experiment/query selection;
10. independent/adversarial review;
11. semantic saturation after deduplication;
12. evidence-lineage independence for saturation;
13. recursively governed method self-improvement;
14. evaluator integrity / frozen benchmark discipline.

Closest comparison set should include, at minimum, AI co-scientist, AI Scientist-v2, Agent Laboratory, Robin, Kosmos, AutoDiscovery, POPPER, PaperQA-style evidence agents, recent POMDP science planning, grounded-fact versus belief planning, and ontology/provenance-based scientific knowledge generation.

## 6. Evaluation program

The paper should not rely on one impressive autonomous discovery story.

### E1 — Known-answer epistemic worlds

Construct worlds where the correct answer is known by design:

- same object under different representations;
- superficially contradictory claims that differ by context;
- genuinely contradictory aligned claims;
- observationally equivalent but mechanistically distinct models;
- QoI-equivalent but globally different models;
- partial-identification worlds;
- shared evidence lineage disguised by different citations;
- missing evidence that requires `CANNOT_CHECK`.

Primary metrics:

```text
false contradiction rate
false merge rate
false split rate
mechanism authority violations
partial-ID coverage
CANNOT_CHECK calibration
negative-history preservation
```

### E2 — Hostile literature worlds

Plant or retrieve papers with:

- terminology aliases;
- scope changes hidden in methods;
- copied datasets across multiple publications;
- derived datasets presented under new identifiers;
- claims unsupported by the cited span;
- conclusions stronger than the experiment identifies.

Measure exact claim-evidence support, omission detection, and authority leakage.

### E3 — Discriminator-selection worlds

Create small hypothesis sets where competing queries/experiments have known separating power and costs.

Compare:

- direct LLM choice;
- random/diversity choice;
- surprise-driven choice;
- Bayesian/goal-oriented design when its assumptions are valid;
- RAKL's scoped decision/mechanism-separation policy.

Do not force Bayesian probabilities in worlds where they are not defensible.

### E4 — Historical time-cutoff rediscovery

Choose scientific episodes with a date-bounded evidence corpus.

Freeze all sources available before a discovery and test whether the method:

- identifies the unresolved set honestly;
- chooses useful next evidence;
- avoids post-cutoff contamination;
- recovers a mechanism or correct identified set.

Historical rediscovery is not proof of novelty, but it tests whether the method behaves scientifically under realistic ambiguity.

### E5 — Long-horizon epistemic integrity

Run repeated rounds to test:

- evidence ignored after contradictory feedback;
- resurrection of refuted ideas;
- accumulation of unsupported claims;
- false saturation;
- repeated counting of dependent evidence;
- context drift;
- evaluator contamination.

### E6 — Self-RAKL safety

Use hostile method challengers that:

- weaken tests;
- alter discovery/configuration;
- exploit evaluator metadata;
- move benchmark thresholds;
- change the evaluated software subject;
- exploit mutable evaluator dependencies.

The method should reject or `CANNOT_CHECK` these attacks while preserving the incumbent.

## 7. Required ablations

A full RAKL run is not sufficient to identify which parts matter.

At minimum ablate:

```text
-A context alignment
-B typed relation algebra
-C authority-layer separation
-D negative-history preservation
-E evidence-lineage saturation
-F residual-targeted recursion
-G external evaluator boundary
-H semantic stopping
```

The main claim is supported only if the relevant ablation increases the failure mode that the component is supposed to control.

## 8. Baseline-control discipline

Because base model capability can dominate agent performance, every empirical comparison should hold constant as much as possible:

```text
base model
tool access
search universe
time/evidence cutoff
token/compute budget
experiment budget
evaluator
task packet
```

When exact equality is impossible, report the mismatch as a limitation rather than treating the systems as globally comparable.

## 9. Paper claims to pre-register

Before running headline experiments, freeze:

1. primary method claim;
2. primary failure-mode metrics;
3. blocking validity criteria;
4. target baselines;
5. ablations;
6. cost accounting;
7. task and evidence cutoffs;
8. contamination policy;
9. stopping policy;
10. analysis plan for positive, null, refuted, partial-ID, and blocked outcomes.

## 10. Recommended paper structure

```text
1. Introduction
2. Why autonomous research needs an epistemic method layer
3. Related work and novelty envelope
4. RAKL theoretical framework
5. Executable RAKL architecture
6. RAKLBench and preregistered evaluation
7. Known-answer and hostile results
8. Scientific case studies / historical rediscovery
9. Self-RAKL experiments
10. Limitations and falsifiers
11. Discussion
```

Theoretical definitions should precede system diagrams. Otherwise reviewers can reasonably interpret RAKL as a bundle of implementation practices.

## 11. Evidence needed for a strong novelty statement

A strong claim such as “RAKL introduces a new LLM scientific research methodology” should wait until all of the following are available:

- independent closest-work review finds no semantically equivalent integrated method;
- theory definitions and proof obligations are stable;
- implementation maps explicitly to theory operators;
- defining invariants pass known-answer and hostile worlds;
- at least one strong baseline or ablation fails in the predicted way;
- process-level gains survive base-model/tool/budget controls;
- independent/adversarial reviewers cannot find an unacknowledged equivalent prior method.

Until then, use:

> **“We propose RAKL, a candidate formal methodology for evidence-governed LLM scientific inquiry.”**

## 12. Publication strategy principle

The paper should make RAKL easy to falsify.

A reviewer should be able to say exactly which result would show that:

- the theoretical contribution is already known;
- the formalism is incoherent;
- the implementation does not instantiate the formalism;
- the controls are empirically unnecessary;
- the method is too costly for the epistemic benefit.

That is stronger than defending novelty rhetorically and is consistent with RAKL's own scientific philosophy.
