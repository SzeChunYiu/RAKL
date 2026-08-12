# Orion Mechanics-of-Mechanics Implementation Plan

**Status:** implementation specification / challenger research plan  
**Planning snapshot:** `SzeChunYiu/RAKL` `main` at `94a35f168e81c57cb678c8d324f4d6190cb3fc46`  
**Date:** 2026-08-12  
**Authority:** proposal-only. Nothing in this package grants scientific, target, method, or promotion authority.

## Mission

Extend Orion from a sophisticated but substantially pre-specified research pipeline into a governed adaptive solver that can diagnose and change the **mechanics by which it solves a problem**.

The target loop is:

```text
problem
-> current representation / decomposition / scale / method
-> attempt
-> externally observable residual
-> diagnose deficient solver mechanic
-> run discriminating checks
-> select or construct a challenger mechanic
-> execute under matched resources
-> verify root-level effect
-> retain / narrow / reject
```

The new layer must be able to reason about at least:

```text
REPRESENTATION
DECOMPOSITION
SCALE
RETRIEVAL
OPERATOR / METHOD
AUXILIARY OBJECT
EXPERIMENT
VERIFIER
COMPOSITION INTERFACE
MEMORY VIEW
MODEL / TOOL
COMPUTE ALLOCATION
STOPPING / EXPLORATION
```

## Core design idea

Do not search only for:

```text
candidate answer
```

Search over:

```text
candidate answer
+
candidate way of finding the answer
```

A provisional solver state is

\[
Z_t =
(G_t,R_t,D_t,S_t,K_t,M_t,O_t,H_t,V_t,C_t,E_t)
\]

where:

- `G`: root goal / QoI
- `R`: representation
- `D`: decomposition
- `S`: reasoning scale
- `K`: active knowledge/context
- `M`: memory / experience
- `O`: operator or method basis
- `H`: search/control policy
- `V`: verification/falsification policy
- `C`: compute/resource allocation
- `E`: residual/obstruction

The meta-controller selects a **meta-action** that changes one of these coordinates.

## The lightning / natural path-finding idea

Treat it as a serious challenger, not a metaphorical truth.

Real negative lightning leaders propagate in steps and commonly branch. They do not know a final optimal path in advance. A more useful abstraction is:

```text
global boundary conditions
-> a field
-> local front growth
-> branching / competition
-> conductivity reinforcement
-> eventual channel exploitation
```

The proposed Orion analogue is:

```text
discrete path search in problem space
         ↓ lift
construct a solvability field over a representation space
         ↓
local gradient/front dynamics reveal promising actions
         ↓
branch when uncertainty is high
         ↓
increase conductance after verified progress
         ↓
retain failed branches as resistance/negative history
```

The scientific question is not “can Orion imitate lightning?” It is:

> Can Orion construct a representation in which a cheap local signal predicts verified global progress well enough to replace a meaningful fraction of combinatorial search?

That question is testable.

## Package map

1. `01_DESIGN_CONSTITUTION.md` — non-negotiable invariants.
2. `02_MECHANICS_OF_MECHANICS_ARCHITECTURE.md` — overall meta-controller.
3. `03_RECURSIVE_MULTISCALE_ORION.md` — fractal/multiscale architecture.
4. `04_SOLUTION_FIELD_LIGHTNING_CHALLENGER.md` — field-guided path formation.
5. `05_REPRESENTATION_LIFTING_AND_SOLVABILITY_GEOMETRY.md` — representation search.
6. `06_DATA_MODELS_AND_APIS.md` — proposed Python objects and APIs.
7. `07_REPO_INTEGRATION_MAP.md` — where this attaches to current RAKL/Orion.
8. `08_IMPLEMENTATION_SEQUENCE.md` — implementation order and exit criteria.
9. `09_TEST_AND_BENCHMARK_PLAN.md` — deterministic/unit/property/fresh tests.
10. `10_EXPERIMENT_MATRIX.md` — scientific ablations.
11. `11_MECHANICS_ATLAS_AND_HIGHER_DIMENSION_ASSIMILATION.md` — learn from whole families of theories.
12. `12_RISK_AND_FAILURE_REGISTRY.md` — how this can fail.
13. `13_ACCEPTANCE_AND_PROMOTION_GATES.md` — what evidence permits which claim.
14. `14_REFERENCE_MAP.md` — source map and extracted mechanisms.
15. `15_IMPLEMENTER_CHECKLIST.md` — concrete coding checklist.
16. `16_SPARK_TO_MECHANIC_PROTOCOL.md` — formal intake process for “random ideas.”
17. `17_OPEN_RESEARCH_QUESTIONS.md` — unresolved questions that should remain explicit.

## Implementation philosophy

### 1. Wrap; do not rewrite

The first implementation should wrap current primitives such as:

- `ProblemAtom`
- `ProblemFibre`
- `ProblemDecomposition`
- `LocalSection`
- `GluingReport`
- `ResidualSignature`
- current search controller
- missing-operator evaluator
- metacognitive auditor
- saturation tracker
- epistemic search
- evidence/authority gates

Do not replace these until isolated experiments show a strict reason.

### 2. Challenger first

Every new mechanic begins as:

```text
PROPOSAL_ONLY
```

It gets no authority and is not wired into default runtime behavior.

### 3. Cheap known worlds first

Before an LLM-mediated benchmark, test the algorithms on deterministic worlds where:

- the true solution is known;
- the optimal route is known or computable;
- hidden facets can be controlled;
- representation changes can be made exactly;
- resource cost is measurable;
- leakage can be ruled out.

### 4. Separate scientific questions

Do not use one end-to-end benchmark to infer everything.

Measure separately:

```text
diagnosis quality
specialist advantage
representation effect
scale selection
field quality
interface validity
verification scheduling
compute allocation
root-level task effect
```

## Recommended first implementation target

Implement the minimal loop:

```text
MechanicDeficiencyWitness
        ↓
RepresentationCandidate / ScaleAction / OperatorAction
        ↓
MechanicsController
        ↓
one deterministic challenger environment
        ↓
MechanicsEpisode telemetry
```

Then add `SolutionPotentialField`.

Do **not** start with a learned latent model. First prove that the object model and evaluation semantics work in explicit finite graphs.

## Definition of success

The project succeeds only if one or more new mechanics produce **verified root-level improvement under matched cost** on fresh tasks.

Interesting but insufficient outcomes include:

- prettier latent spaces;
- smoother fields;
- high routing accuracy without task gain;
- better local subproblem scores without root progress;
- more candidate diversity without verified resolution;
- fewer failures caused only by over-abstention;
- a field that requires knowing the answer to construct.

All of these should be recorded as results, not hidden.
