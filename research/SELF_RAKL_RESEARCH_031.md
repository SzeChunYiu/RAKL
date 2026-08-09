# SELF-RAKL Research 031 — Contextual Method Capability Frontier

Date: 2026-08-09  
Starting `main`: `f7e92b74ad60dd2f8d88b14cbc3d2a4cea1e6b21`

## Trigger

Round 030 formalized two sources of method challengers:

```text
endogenous residual-driven self-challenge
exogenous external-framework method assimilation
```

The user's intended long-run behavior is cumulative learning: RAKL should be able to acquire strong atomic research operators discovered anywhere and add them to its own method repertoire.

The immediate question was whether a "method capability frontier" itself is a defensible novelty claim.

## Panel synthesis

Six same-context expert roles were used for coverage; they do not count as independent review.

1. **Agent-evolution researcher** — searched skill-evolution/frontier methods.
2. **Scientific methodologist** — separated generic optimization from scientific authority governance.
3. **Knowledge-representation researcher** — applied the Knowledge Atlas principle to method comparison.
4. **Evaluation-integrity reviewer** — required blocking validity to precede Pareto optimization.
5. **Systems architect** — checked how an expanding method atlas can remain bounded-context for ordinary LLMs.
6. **Adversarial novelty reviewer** — attempted to destroy the frontier novelty claim.

The broad frontier claim did not survive.

## Material prior-art finding

### EvoSkill — arXiv:2603.02766

EvoSkill already uses a **Pareto frontier of agent programs** to govern skill selection, retains skills based on held-out validation, freezes the underlying model, and reports zero-shot transfer of evolved skills.

Therefore:

```text
Pareto frontier of agent programs
held-out selection of evolved skills
skill-level transfer
```

are not standalone RAKL novelty.

### SkillFoundry — arXiv:2604.03964

SkillFoundry already mines heterogeneous scientific resources into validated executable skills with task scope, inputs/outputs, environment assumptions, provenance and tests and evolves the library through expansion, repair, merge and pruning.

Therefore external scientific skill acquisition/evolving skill libraries are also prior art.

### EvoAgentBench — arXiv:2607.05202

Self-evolution through procedural ability transfer is already an explicit evaluation axis.

### Red Queen Gödel Machine — arXiv:2606.26294

Controlled evaluator/utility evolution is also existing prior art.

## Retained refinement

The candidate RAKL object is therefore not a generic Pareto frontier. It is a **context-indexed, authority-scoped, validity-gated method frontier**.

For each atomic research fiber, RAKL should compare methods only when the following coordinates glue sufficiently for the registered comparison:

```text
operation/fiber
scientific or task context
assumptions
input/output semantics
resource envelope
registered meta-QoIs
scientific authority target
evidence/benchmark scope
```

If two useful methods rely on incompatible assumptions or target different scientific authority, RAKL should not declare a global winner. They remain parallel local method charts.

Only after blocking validity invariants pass can non-blocking quality/cost tradeoffs define a non-dominated set.

## Why this matters for assimilation

This creates a principled interpretation of "learn the strengths of other frameworks".

A new operator can:

```text
DOMINATE LOCALLY
    replace the incumbent in a compatible scope after ordinary promotion

ADD A FRONTIER POINT
    provide a validated tradeoff/capability not dominated in that scope

BE EQUIVALENT
    deduplicate rather than fake method diversity

REMAIN A PARALLEL LOCAL VIEW
    preserve a useful but incompatible method

BE BLOCKED / REJECTED / CANNOT_CHECK
    preserve evidence and do not activate
```

This is more compatible with the Knowledge Atlas principle than one universal "best research method" leaderboard.

## Bounded-context implication

An expanding method atlas does not require an expanding LLM prompt. Store the full operator/provenance/history externally; keep a compact searchable method index; materialize only the selected operator contract and its relevant assumptions/falsifiers for the current atomic step.

Thus cumulative method learning can remain usable by ordinary-context LLMs.

## Novelty boundary

Safe candidate claim:

> RAKL applies contextual comparison and scientific-authority constraints to method assimilation, allowing validated external/internal research operators to expand a local method repertoire without forcing incompatible operators into one global workflow.

Not safe:

> RAKL invents Pareto frontiers for evolved skills.

> RAKL is the first system to learn skills from external scientific resources.

> RAKL has already realized every strength of all external frameworks.

## Required empirical discriminator

Before implementing runtime frontier routing, freeze a benchmark comparing:

```text
global/static Pareto selection
static curated pipeline
uncontrolled all-component aggregation
RAKL contextual authority-scoped method frontier
```

under matched model/tool/token/time resources.

Primary metrics should include:

```text
blocking-validity violations
cross-axis authority leakage
false method duplication
forced-comparison / forced-fusion error
held-out transfer
negative-history resurrection
token/latency cost
validated capability coverage per cost
```

If simpler global Pareto selection performs equally well without higher epistemic failure, the extra RAKL frontier structure does not earn runtime complexity.

## Saturation

```text
state = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The broad novelty claim was refuted/narrowed, and four more specific semantic objects remain to test: validity-gated method frontier, authority-scoped comparability, non-forced parallel method charts, and bounded-context method-atlas materialization.
