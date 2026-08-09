# Constructive Invention in RAKL

Status: Round-036 candidate method layer  
Date: 2026-08-09

## 1. Why this layer exists

RAKL already knows how to decompose an object, build contextual knowledge fibers, GLUE compatible projections, JUMP to witnessed analogues, discriminate surviving hypotheses, preserve residuals, and recursively improve the method.

Those capabilities are necessary but not sufficient for a research programme whose objective is to **construct a mechanism or formalism that does not already exist as one retrieved representation**.

Before Round 036, the phrase “derive a new formalism” was largely a governed LLM cognition step. Round 036 externalizes that step into explicit objects and operators.

The core extension is:

\[
(\Gamma,\mathcal O,\mathcal V,\mathcal R,\mathcal G),
\]

where:

- `Gamma` is the compatibility-constrained Knowledge Lattice;
- `O` is the constructive invention-operator basis;
- `V` is the formal/empirical verification stack;
- `R` is the structured residual field;
- `G` is an immutable positive-goal contract when the task is goal-seeking.

## 2. Typed formalism IR

`src/rakl/formalism.py` defines a small formal intermediate representation.

A candidate is no longer only a prose mechanism name or LaTeX string. It can contain:

```text
FormalSymbol
FormalExpression AST
FormalEquation
MechanismGraph
ObservationMap
Invariant
LimitCase
Formalism
```

Expression nodes currently include:

```text
SYMBOL
CONSTANT
ADD / SUB / MUL / DIV / POW / NEG
FUNCTION
DERIVATIVE
EXPECTATION
SUM
INTEGRAL
PIECEWISE
```

This is intentionally small enough to audit and large enough to act as a translation target for LLMs, symbolic-regression systems, CAS/proof systems, simulation code and domain-specific solvers.

## 3. Mechanism representation

A mechanism is represented as a graph whose nodes may be entities, states, latent states, observables, shocks, clocks or regimes. Typed edges include:

```text
CAUSES
MEDIATES
MODULATES
CONSTRAINS
OBSERVES
FEEDBACK
COUPLES
SWITCHES
```

A mechanistic claim therefore has explicit ancestry and directional structure rather than relying on a narrative label.

## 4. Constructive invention algebra

`src/rakl/invention.py` defines a first operator basis.

An `InventionMove` is a typed delta. It can add/remove symbols, equations, mechanism nodes/edges, assumptions, regimes and symmetries while preserving:

```text
move id
operator type
rationale
targeted residual ids
source fiber ids
source analogy/witness ids
freeze chronology
```

The current basis contains structural, dynamical, abstraction, causal and representational transforms. It is deliberately extensible: if persistent residuals expose a missing operation, RAKL's metacognitive layer should open a method-basis gap and benchmark a challenger operator.

## 5. Residual-driven search

A candidate failure is converted into a `ResidualSignature` rather than a generic loss value.

The initial residual ontology covers:

```text
distribution
temporal structure
regime structure
tails
volatility
cross-asset
cross-venue
flow/liquidity
observation process
clock
causal structure
identifiability
calibration
transport
prediction
unclassified structure
```

Each class activates a diverse operator prior. This is only a routing prior: operator proposals still require formalization and validation.

The loop is:

\[
T^{(k)}
\xrightarrow{\text{test}}
R^{(k)}
\xrightarrow{\text{fiber reopening + GLUE/JUMP}}
\mathcal O_k
\xrightarrow{\text{typed mutation/recombination}}
\{T_j^{(k+1)}\}.
\]

## 6. Constructive Knowledge State

`src/rakl/constructive_lattice.py` binds the invention objects to a live `KnowledgeFiber`.

It registers:

```text
residual signatures
candidate theories
invention moves
candidate score vectors
positive-goal contract
goal assessments
```

back into the fiber's dimensional state. This makes the Knowledge Lattice a generator of new candidate theory objects rather than only an atlas of retrieved knowledge.

Registration does not imply authority or promotion.

## 7. Candidate tournament

A candidate score vector currently contains:

\[
(C_D,C_R,P,I,F,B,N,K),
\]

with coordinates for descriptive coverage, residual closure, predictive value, identification, falsifiability, robustness, novelty and complexity.

RAKL retains a Pareto frontier. This avoids silently converting all scientific goals into one goodness-of-fit scalar.

## 8. Mathematical oracles

`src/rakl/math_oracles.py` implements the first automatic oracle: dimensional consistency.

It propagates symbolic dimensions through the formal expression tree and fails closed when an operator's dimension rule is unknown.

This layer is intentionally modular. Future oracle fibers should add, where relevant:

```text
symbolic simplification / equivalence
support/domain constraints
stability / bifurcation analysis
stochastic-process validity
conservation/invariant solvers
causal graph consistency
identifiability analysis
proof assistants / theorem checking
numerical convergence / stiffness checks
```

## 9. Hidden-world invention benchmark

`src/rakl/invention_benchmark.py` evaluates invention separately from validation of a known candidate.

A certifying trial withholds the target structure from the proposer, freezes evidence and thresholds, freezes the candidate before target exposure, and uses a separate evaluator.

Worlds include:

```text
RECONSTRUCTION
NOVEL_COMPOSITION
CROSS_DOMAIN_TRANSFER
ADVERSARIAL_RESIDUAL
```

`NOVEL_COMPOSITION` is especially important. It requires a candidate to recover a registered combination that was not handed to the proposer as a complete source component.

Passing this benchmark supports only a scoped invention-capability claim for the frozen worlds and resource boundary. It does not imply universal scientific creativity.

## 10. Positive-goal semantics

For a goal-seeking project, `PositiveGoalContract` defines immutable success requirements.

The only successful terminal verdict is:

```text
GOAL_ACHIEVED
```

A failed candidate produces:

```text
CANDIDATE_REJECTED_CONTINUE
```

The distinction is essential:

> RAKL may refuse to accept failure of the current candidate set as project closure, while still refusing to manufacture a positive result.

If data, tools or identifiability are insufficient, the state is `CANNOT_CHECK` or an explicit block, not a false positive.

## 11. Polymarket/crypto binding

The stronger search semantics for the real case are frozen in:

`research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json`

Round 035 remains immutable. Round 036 changes what happens **after a candidate fails**: the mechanism-invention loop is mandatory until the positive goal is achieved or execution is blocked by an explicitly recorded evidence/resource boundary.

## 12. What remains external

This implementation creates the theory language, constructive operators, routing, state, goal semantics, dimensional oracle and invention benchmarks. It does not pretend to contain every scientific solver.

CAS systems, symbolic regression, numerical simulation, theorem provers, causal/identification solvers and domain-specific statistical pipelines are treated as verification/generation resources that plug into the typed contracts.

RAKL's job is to ensure those resources are invoked on explicit candidate identities with preserved ancestry, evidence scope, residual targets and promotion rules.
