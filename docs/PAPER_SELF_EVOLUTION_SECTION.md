# Paper Insert — Governed Open-Ended Method Evolution

Status: paper-ready drafting support. Claims marked prospective remain unvalidated until the registered experiments are run.

## Candidate contribution statement

**Governed open-ended method evolution.** RAKL treats the scientific method itself as a versioned research object. Candidate improvements may arise endogenously from residuals in RAKL's own operation or exogenously by decomposing external research frameworks into atomic method operators. Both sources enter the same evidence-governed path: semantic normalization, compatibility analysis, authority scoping, frozen development evaluation, blind/fresh transfer assurance, narrow promotion, and immutable supersession history. RAKL therefore seeks to accumulate validated research capabilities without granting promotion authority to the proposer or forcing incompatible methods into one global workflow.

This contribution must be distinguished from prior automatic agent design, recursive self-improvement, evaluator-driven program evolution, and evolving skill libraries. RAKL does **not** claim invention of agent self-modification, procedural skill transfer, modular skill packages, or automatic recombination of agent architectures. Its candidate contribution is a scientific-method-specific governance layer that asks whether a method change has acquired enough evidence to be called a transferable improvement.

## Formal self-evolution evidence

Let `M_t` be the incumbent method, `M_{t+1}` a proposed successor, `D_t` a frozen development packet and `A_t` a separately frozen assurance packet. A positive development result is

\[
\Delta_D(M_{t+1},M_t)>0.
\]

This is **local method improvement**, not yet evidence of self-evolution.

RAKL records scoped evolution evidence only when

\[
\Delta_D>0,\qquad \Delta_A>0,
\]

and:

\[
\text{BlockingClean}
\land \text{CandidateIdentityVerified}
\land \text{HistoryPreserved}
\land \text{AssuranceFrozenBeforeMutation}
\land \text{AssuranceBlind}
\land \text{EvaluatorSeparated}
\land \text{ResourcesComparable}.
\]

The resulting authority is not `METHOD_IS_GLOBALLY_BETTER`; it is a scoped certificate over the parent, child, development/assurance distributions, model/tool/resource envelope, evidence cutoff and evaluator identity.

## Adaptive assurance reserve

A fixed holdout ceases to provide strong independent assurance when repeated optimizer-visible evaluations leak information about it. RAKL therefore attaches an exposure budget to an assurance packet. Once exhausted, additional positive results may demonstrate observed transfer but cannot independently certify another generation. Fresh or rotated assurance tasks are required for subsequent strong claims.

## External method assimilation as evolution

For an external framework `X`, RAKL does not import `X` wholesale. It decomposes

\[
X\rightarrow\{m_1,m_2,\ldots,m_k\}
\]

into atomic operators associated with specific fibers. Each operator is assigned an input/output contract, context, assumptions, provenance, failure modes, authority envelope, transition witness and benchmark identity.

An operator may become:

```text
EQUIVALENT_TO_INCUMBENT
PARALLEL_LOCAL_VIEW
ELIGIBLE_FOR_SHADOW
BLOCK
REJECT
CANNOT_CHECK
```

and only a later governed promotion can activate it.

Thus RAKL can learn a strong retrieval mechanism from one framework, a falsification operator from another, a world-state representation from a third and a formal checker from a fourth without pretending that those entire frameworks share one ontology or one epistemic authority model.

## Context-indexed method capability frontier

The target of evolution is not a maximum-size super-agent. For research fiber `f` and context `gamma`, RAKL maintains the non-dominated validated method set

\[
\mathcal F_{f,\gamma}^{(t)}.
\]

A new method can expand the frontier by being better under an existing context or by providing a validated capability under a previously uncovered context. Incompatible but useful methods can coexist.

This supplies a precise interpretation of cumulative learning:

> RAKL aims to improve the *available validated capability frontier* where evidence permits, not to assert that every successor globally dominates every ancestor.

## Self-RAKL headline experiment

A top-tier evaluation should run multiple method generations and compare:

1. fixed RAKL with no self-improvement;
2. unconstrained self-editing;
3. benchmark-only self-improvement;
4. governed RAKL self-improvement;
5. governed RAKL self-improvement plus external method assimilation.

Separate development, transfer and fresh/blind assurance planes. Report per generation:

```text
method diff
source of challenger: INTERNAL or EXTERNAL
meta-fiber changed
development delta
transfer delta
assurance status / exposure count
blocking invariant results
cost delta
frontier disposition
```

Primary outcomes should include registered meta-QoI gain, held-out transfer, blocking-invariant failures, meta-overfit frequency, assurance consumption, negative-history resurrection, frontier expansion, cost per validated improvement and cross-model/backbone transfer.

## Required negative-result reporting

The paper must report generations classified as:

```text
SCOPED_EVOLUTION_EVIDENCE
TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
LOCAL_IMPROVEMENT_ONLY
META_OVERFIT
NO_IMPROVEMENT
BLOCKED
CANNOT_CHECK
```

A null or failed generation is scientifically useful evidence and remains visible in the lineage plot.

## Novelty boundary

Closest prior art already covers automatic agent design, archive-based agent discovery, recursive self-modification, evolving evaluators, validated scientific skill libraries and ability-transfer benchmarking. Therefore the paper should not say simply "RAKL is self-evolving."

The candidate novelty claim is instead:

> **RAKL couples endogenous self-challenge and exogenous method assimilation to an evidence-governed scientific state transition protocol, where transferable method improvement requires fresh scoped assurance and incompatible strengths remain contextual method-frontier points rather than being forcibly merged.**

This claim remains falsifiable by a semantically equivalent prior method or by failure of prospective multi-generation transfer experiments.
