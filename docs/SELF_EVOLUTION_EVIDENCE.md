# Evidence for Governed RAKL Self-Evolution

Status: publication/support theory. This document does not amend the Constitution, alter promotion, or claim that RAKL has already demonstrated open-ended empirical self-improvement.

## 1. Why "self-evolving" needs an evidence definition

A method variant that improves the benchmark used to design it has shown **local optimization**, not necessarily evolution in a scientifically meaningful sense.

Current automated-agent design and self-improvement work already demonstrates:

- automatic invention and recombination of agentic systems (ADAS / Meta Agent Search);
- recursive self-modification under empirical evaluation (Darwin Gödel Machine and descendants);
- evaluator-driven code evolution (AlphaEvolve family);
- self-evolving scientific skill libraries compiled from heterogeneous resources (SkillFoundry);
- ability-transfer benchmarks for procedural agent self-evolution (EvoAgentBench);
- co-evolution of agents and evaluators under changing utilities (Red Queen Gödel Machine).

RAKL therefore must not claim novelty from the bare fact that it can edit itself, accumulate skills, or combine agent modules.

The paper's stronger question is:

> **What evidence licenses the claim that an evidence-governed scientific method has improved itself rather than merely overfit its own evaluation loop?**

## 2. Two coupled learning channels

RAKL has two sources of candidate method change.

### Endogenous self-challenge

The current method discovers a residual and proposes a challenger to one of its own atomic fibers:

```text
routing
search
claim extraction
ontology normalization
equivalence detection
contradiction diagnosis
experiment selection
synthesis
review
memory
context compilation
benchmarking
stopping
software architecture
```

### Exogenous method assimilation

An external framework is decomposed into atomic operators and treated as local evidence about the meta-object:

> how should this scientific-research operation be performed?

The operator then passes through the existing method-assimilation process:

```text
external mechanism
-> atomic decomposition
-> normalization/deduplication
-> authority envelope
-> transition witness
-> shadow eligibility
-> frozen evaluation
-> narrow promotion / parallel view / rejection
```

The two channels deliberately converge on the **same governed evaluation path**. External reputation and internal authorship provide no promotion authority.

## 3. Local improvement versus scoped evolution

Let method version `M_t` produce a challenger `M_{t+1}` on frozen development packet `D_t`.

A positive development delta

\[
\Delta_D(M_{t+1},M_t)>0
\]

with blocking invariants clean is called **local improvement**.

That alone is insufficient for a self-evolution claim.

Let `A_t` be a separately declared assurance packet that was frozen before the mutation, hidden from the proposer during optimization, and evaluated through a separate/protected evaluator.

RAKL records **scoped evolution evidence** only when:

\[
\Delta_D>0,
\]

\[
\Delta_A>0,
\]

and all blocking conditions remain clean under matched or explicitly comparable resources.

The claim is always scoped to:

```text
parent method version
child method version
development task distribution
assurance task distribution
base model(s)
tool/resource envelope
evidence cutoff
evaluator identity
benchmark identity
```

There is intentionally no global state called `EVOLVED`.

## 4. Meta-overfitting is a first-class negative result

If a challenger improves the development packet but regresses on registered assurance metrics, RAKL records:

```text
META_OVERFIT
```

The negative result remains in immutable method history.

Examples include:

- a search router tuned to one literature domain that degrades another;
- a compression policy that lowers tokens but drops counterevidence on held-out tasks;
- a reviewer configuration that improves one planted-flaw suite but misses a different flaw family;
- a self-evolution policy that learns to exploit one evaluator rather than improving scientific reasoning.

## 5. Assurance capacity is consumable

A supposedly held-out benchmark stops being strongly independent when the optimizer repeatedly observes its score.

RAKL therefore treats a blind assurance set as a bounded **assurance reserve**.

For assurance packet `A` with preregistered optimizer-visible exposure budget `b_A`, let

\[
e_A(t)
\]

be the number of prior optimizer-visible evaluations.

Fresh assurance requires

\[
e_A(t)<b_A.
\]

After the reserve is consumed, the same packet may still show **observed transfer**, but it cannot independently certify unlimited later generations. A fresh/rotated assurance packet is required for a new strong evolution claim.

This imports a lesson from adaptive data analysis into self-evolving agents: repeated access to evaluation information is itself an information channel.

## 6. Method capability frontier rather than one super-agent

RAKL should not assume that assimilating more methods means concatenating them into one globally dominant workflow.

For atomic fiber `f` and context `gamma`, define the validated candidate set

\[
\mathcal M_{f,\gamma}^{(t)}.
\]

Each method has a vector of registered meta-QoIs such as validity, semantic recall, contradiction detection, information gain, token cost, latency and tool requirements, subject to blocking invariants.

RAKL maintains a **context-indexed non-dominated frontier**

\[
\mathcal F_{f,\gamma}^{(t)} \subseteq \mathcal M_{f,\gamma}^{(t)}.
\]

A new internal or external method can therefore:

```text
DOMINATE_INCUMBENT      -> candidate replacement under that context
ADD_FRONTIER_POINT      -> retain as a complementary validated method
EQUIVALENT              -> deduplicate / corroborate
PARALLEL_LOCAL_VIEW     -> retain under incompatible assumptions or scope
BLOCK / REJECT          -> preserve as negative method history
CANNOT_CHECK            -> do not activate
```

This is the rigorous interpretation of "absorbing strengths": **expand the validated capability frontier without forcing incompatible strengths into one monolithic agent.**

## 7. Stronger top-tier paper experiment

A headline Self-RAKL experiment should run multiple generations with three data planes:

```text
DEVELOPMENT
  repeatedly available to proposer/evolution loop

TRANSFER
  held-out tasks used to diagnose generalization

ASSURANCE
  fresh/blind reserve used sparingly for publication-level evolution claims
```

For generation `g`, report:

```text
method diff
source of challenger: INTERNAL or EXTERNAL
meta-fiber changed
development delta
transfer delta
assurance status / exposure count
blocking invariant results
cost delta
whether the new method replaced, complemented or failed to enter the frontier
```

At minimum compare:

```text
no self-evolution
unconstrained self-editing
development-only benchmark evolution
RAKL governed self-evolution
RAKL governed self-evolution + external method assimilation
```

## 8. Strong falsifiers

The paper's self-evolution claim is weakened or refuted if:

1. gains disappear on blind held-out assurance tasks;
2. repeated assurance reuse explains the apparent improvement;
3. improvements require changing the evaluator or weakening falsifiers;
4. gains do not transfer across task families or model backbones where transfer was preregistered;
5. cumulative method growth increases cost without corresponding epistemic benefit;
6. uncontrolled aggregation performs as well as governed assimilation;
7. negative-history constraints do not reduce resurrection of failed method ideas;
8. an existing prior framework is semantically equivalent to the full governed evolution protocol.

## 9. Publication wording

Until prospective multi-generation transfer experiments exist, use:

> **RAKL implements a governed mechanism for recursive method evolution and external method assimilation; its ability to produce transferable multi-generation improvement is a preregistered empirical claim, not yet assumed.**

If the experiments succeed, a stronger wording becomes defensible:

> **RAKL can recursively improve its scientific-research policy while preserving evidence safeguards, and can assimilate validated operators from external frameworks into a context-indexed method frontier.**
