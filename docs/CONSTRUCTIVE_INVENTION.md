# Constructive Invention in RAKL

Status: Round-036 candidate method layer  
Date: 2026-08-09

## Purpose

RAKL's original epistemic machinery could decompose objects, build Knowledge Fibers, GLUE projections, JUMP to distant analogues, diagnose residuals and govern promotion. Round 036 adds the missing constructive layer required when the goal is not merely to compare known models but to **discover or construct a working mechanism, mathematics or formalism**.

The constructive system is:

\[
(\Gamma_T,\mathcal O,\mathcal C,\mathcal S,\mathcal V,\mathcal R,\mathcal G),
\]

where:

- `Gamma_T` — typed, compatibility-witnessed Knowledge Lattice;
- `O` — constructive invention operators;
- `C` — mechanism-to-formalism compiler and symbolic discovery operators;
- `S` — residual-driven candidate-population search controller;
- `V` — formal, mathematical, statistical and empirical verification stack;
- `R` — structured residual field;
- `G` — immutable positive-goal plus exact hard-gate contract.

## Typed Knowledge Lattice

`src/rakl/typed_lattice.py` promotes useful lattice coordinates from semantic strings into first-class atoms:

```text
observable / representation
mechanism node / mechanism edge
equation / expression
assumption / regime / observation model
coarse-graining operator
invariant / symmetry / falsifier
data product / inference method / QoI
causal relation / failure motif / analogy motif
```

Pairwise compatibility requires an explicit witness with relation, scope condition and evidence. Strict constructive paths reject unknown or incompatible pairs. A compatible path can be transformed into a residual-specific `LatticeSynthesisSeed` carrying typed equations/mechanism fragments, source fibers, evidence lineage and applicable invention operators.

This is the point at which the Knowledge Lattice becomes an explicit generator of theory-construction inputs rather than only an atlas.

## Typed Formalism IR

`src/rakl/formalism.py` represents candidate theories as machine-manipulable objects:

```text
FormalSymbol
FormalExpression AST
FormalEquation
MechanismGraph
ObservationMap
Invariant / LimitCase
Formalism
```

Expression nodes include symbols, constants, arithmetic, powers, functions, derivatives, expectations, sums, integrals and piecewise expressions.

## Constructive Invention Algebra

`src/rakl/invention.py` defines typed mutation/recombination operators including:

```text
COMPOSE / RECOMBINE
ADD/REMOVE_LATENT_STATE
SPLIT/MERGE_REGIME
CHANGE_CLOCK
COARSE/FINE_GRAIN
GENERALIZE / SPECIALIZE / TAKE_LIMIT / DUALIZE
STOCHASTICIZE / DETERMINIZE
ADD/REMOVE_FEEDBACK
ADD/REMOVE_COUPLING
ADD_INTERACTION
RELAX/STRENGTHEN_ASSUMPTION
ADD_INVARIANT
ADD/BREAK_SYMMETRY
NONLINEARIZE / LINEARIZE
IMPORT_ANALOGICAL_MOTIF
CHANGE_OBSERVATION_MAP
EXPLAIN_RESIDUAL
```

Every move targets registered residuals, preserves parent lineage and must be frozen before certifying evaluation.

## Mechanism-to-equation compilation

`src/rakl/mechanism_compiler.py` prevents a mechanism graph from merely sitting next to unrelated equations.

Influential graph edges are bound to explicit `InteractionLaw` objects and compiled into registered state-evolution equations. Missing influential edge laws produce `CANNOT_CHECK`; post-result interaction laws are rejected. This creates explicit ancestry:

```text
mechanism edge
-> interaction law
-> state evolution equation
-> observable projection
```

## Native symbolic law discovery

`src/rakl/symbolic_discovery.py` provides a bounded data-driven mathematical invention operator.

It:

- enumerates a frozen expression grammar;
- evaluates candidate expressions on a training-only partition;
- deduplicates observationally equivalent forms;
- searches nonlinear interactions;
- fits affine wrappers and two-basis linear combinations;
- emits typed `FormalEquation` candidates;
- preserves the rule that untouched/forward validation is still required.

Symbolic discovery therefore supplements LLM proposals rather than granting authority to training fit.

## Structured residuals and search controller

Candidate failure is represented by typed residual signatures spanning distribution, time, regimes, tails, volatility, cross-asset/venue state, flow/liquidity, observation, clocks, causality, identifiability, calibration, transport and prediction.

`src/rakl/search_controller.py` plans diverse operator families across active residuals, tracks retry counts and candidate budgets, preserves Pareto-surviving parents and routes mathematical moves toward symbolic/solver-first generation.

Budget exhaustion is `RESOURCE_BLOCK_NONTERMINAL`. It never becomes a negative project success state.

## Candidate tournament

Candidate theories are maintained on a Pareto frontier across:

```text
descriptive coverage
residual closure
predictive value
identification
falsifiability
robustness
novelty
complexity
```

No single fit statistic can average away a blocking scientific defect.

## Mathematical and formal oracles

Current built-in oracles include:

- typed symbol/expression/mechanism structural validation;
- dimensional consistency;
- exact local rank-condition identifiability;
- exact 1D/2D continuous/discrete local stability tests;
- covariance positive-semidefinite validation for bounded dimensions;
- stochastic transition-matrix validation;
- exact-candidate verification packet binding.

Harder systems fail closed to specialist CAS, numerical, causal, stochastic or proof backends rather than receiving an implicit pass.

## Hidden-world invention benchmark

`src/rakl/invention_benchmark.py` tests invention as a capability rather than assuming it from fluent output. It supports:

```text
RECONSTRUCTION
NOVEL_COMPOSITION
CROSS_DOMAIN_TRANSFER
ADVERSARIAL_RESIDUAL
```

Targets remain hidden from the proposer, thresholds and evidence are frozen, and a separate evaluator checks structural recovery plus target validation. Novel-composition worlds require recovery of combinations not supplied as complete source components.

## Positive goal and exact hard gates

`PositiveGoalContract` supplies frozen multi-objective thresholds. `src/rakl/hard_gates.py` supplies non-compensatory gates.

For the Polymarket/crypto spot application, hard gates include the Round-035 predictive requirements plus typed formalism, descriptive-axis coverage, mechanism ancestry, structured residual closure, falsifier execution, strict availability, exact candidate binding, independent review and integrity.

The only successful project closure is:

```text
GOAL_ACHIEVED
```

Failed candidates become `CANDIDATE_REJECTED_CONTINUE`; missing evidence becomes `CANNOT_CHECK`; exhausted finite compute becomes a nonterminal resource block.

## End-to-end runtime

`src/rakl/invention_runtime.py` coordinates the complete loop:

```text
typed lattice
-> synthesis seed / generation request
-> typed candidate
-> mechanism compilation / symbolic discovery as needed
-> formal + empirical verification
-> numeric goal + hard gates
-> typed residual on failure
-> reopen implicated fibers
-> next diverse invention round
-> repeat
```

The public facade is `rakl.invention_api`.

## Polymarket/crypto binding

The stronger stopping/search semantics are frozen in:

`research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json`

Round 035 remains immutable. Round 036 changes what happens after a candidate fails: failure of the current candidate family is not project closure; it becomes input to the next constructive round or, if the operator basis itself is exhausted, a RAKL method-basis evolution problem.

## Integrity boundary

A persistent positive objective does not imply a promise that finite data contain an identifiable or predictive mechanism. RAKL can guarantee the **search/closure semantics**—it will not declare current failure to be success—but it cannot truthfully manufacture information absent from the evidence.

Forbidden shortcuts remain:

```text
fabricated evidence or citations
target leakage
post-result threshold rescue
selective deletion of failed candidates
hidden multiplicity
analogy authority leak
in-sample fit relabeled as predictive success
descriptive fit relabeled as mechanism without ancestry
```

The objective is persistent constructive discovery with a hard positive closure condition, not significance by construction.
