# Workflow — Self-RAKL

Use when evaluating or improving the RAKL research method itself.

## Object

```text
RAKL_METHOD
```

Self-application is **not** self-authorization. RAKL may be both the research instrument and the research object, but a challenger still requires evidence from a protected evaluator and fresh tasks outside the challenger's write authority.

## Current method-surface inventory

Use the canonical 24-surface registry in `src/rakl/method_specs.py` rather than maintaining a shorter informal list inside this workflow.

Before proposing a new method surface, ask whether the problem is already owned by an existing surface and only lacks implementation or empirical validation.

## Bootstrap acceptance question

A mature RAKL should be able to perform:

```text
current RAKL
-> research RAKL as the target object
-> search same-domain + cross-domain method knowledge
-> normalize/deduplicate until route families are flat or blocked
-> run method-completeness challenge
-> localize a previously unlabelled weakness
-> attribute the failure cause
-> route existing method OR assimilate/invent a candidate operator
-> freeze candidate + discriminator
-> development validation
-> fresh assurance
-> narrow promotion or retained negative result
```

A same-context run that finds and repairs a real weakness is useful **first-sign evidence only**. Strong self-evolution evidence requires the frozen bootstrap benchmark in `research/SELF_RAKL_BOOTSTRAP_BENCHMARK_041.json` and fresh assurance.

## Minimum search route families

Do not claim method-search saturation after reading only LLM-agent papers. Before a strong flatness claim, cover or explicitly block at least:

```text
scientific method / philosophy of science / metascience
metacognition / self-regulated learning / expert learning
active learning / experiment design / optimal control
formal methods / truth maintenance / belief revision / provenance
knowledge representation / local-to-global consistency
causal inference / identification / partial identification
information retrieval / databases / memory / context compression
software reliability / reproducibility / supply-chain provenance
self-improving agents / program evolution / skill learning
scientific visualization / human factors / communication
at least two domain-specific non-LLM research workflows
```

For every route:

1. extract atomic mechanisms, not framework reputations;
2. normalize semantic equivalents;
3. preserve assumptions, resource requirements and evidence scope;
4. record genuinely new operators, corroboration, novelty corrections and negative findings;
5. repeat from materially different query vocabulary until semantic gain is flat or the route is explicitly blocked.

Search-budget exhaustion while new semantic objects are still arriving is `NOT_SATURATED`.

## Failure attribution before self-modification

A project failure does not automatically imply that RAKL needs a new operator. Classify at least:

```text
MISSING_EVIDENCE_OR_MEASUREMENT
IMPLEMENTATION_DEFECT
STOCHASTIC_OR_UNDERPOWERED_RESULT
WRONG_EXISTING_STRATEGY_OR_ROUTING
ONTOLOGY_OR_CONTEXT_GAP
METHOD_BASIS_GAP
OBJECTIVE_OR_EVALUATOR_DEFECT
```

Only a supported `METHOD_BASIS_GAP` routes directly to operator assimilation/invention. Missing evidence routes to evidence acquisition; implementation defects route to code repair; uncertain cases require a discriminating challenge.

## Candidate construction

For an external candidate, use the method-assimilation contract. For a new candidate, use constructive invention. In both cases freeze before result access:

```text
candidate id
parent/incumbent lineage
scope/context
I/O contract
assumptions/preconditions
failure modes
scientific authority it may and may not create
predicted improvement
falsifiers
resource budget
benchmark/evaluator identity
```

Semantic renaming of an incumbent method is not improvement.

## Evaluation chronology

1. Freeze incumbent source/evidence cutoff and resource profile.
2. Freeze development benchmark and blocking meta-QoIs.
3. Freeze candidate identity before candidate outcomes are revealed.
4. Run development known-answer and hostile worlds.
5. If development improves, execute a **fresh assurance** task/realization not used to design the repair.
6. Compare fixed RAKL, generic reflection, unconstrained self-editing and governed RAKL under matched resources when the claim is comparative.
7. Preserve every failed, null, blocked and meta-overfit generation.
8. Promote only through the normal protected method-change gate.

Development improvement

\[
\Delta_D > 0
\]

is local optimization only. Strong scoped evolution evidence also requires

\[
\Delta_A > 0
\]

on fresh assurance with all blocking invariants clean.

If \(\Delta_D>0\) but \(\Delta_A<0\), record `META_OVERFIT`.

Repeated disclosure of assurance scores consumes the assurance reserve. Rotate or refresh assurance rather than adapt indefinitely against one held-out set.

## Output minimum

Every Self-RAKL run should produce:

```text
incumbent exact identity
method surface/fiber under challenge
search route coverage + semantic flatness state
weakness/residual and epistemic cut
failure attribution
candidate source: endogenous / external / implementation repair / no change
frozen benchmark/evaluator identity
candidate exact identity
negative-history delta
development delta
fresh-assurance delta or CANNOT_CHECK
resource/cost delta
blocking invariant results
verdict
next reopen trigger
```

## Safety

- The self-improver may not change evaluation criteria after seeing its own result.
- The proposer cannot be the only authority certifying its repair.
- Same-context role separation is not independent review.
- A method-search saturation claim is local to the registered source/query/evidence universe.
- `NO_IMPROVEMENT` is a valid result; do not force a change merely to demonstrate recursion.
- Constitutional changes remain proposal-only under separate amendment governance.
