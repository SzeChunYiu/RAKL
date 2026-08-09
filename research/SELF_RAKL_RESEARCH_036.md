# SELF-RAKL Research Round 036 — Constructive Invention Engine and Positive-Goal Loop

Date: 2026-08-09  
Status: implementation / method-basis expansion

## Trigger

The user clarified that the `polymarket_crypto` application is not intended to stop after evaluating a fixed menu of existing models. The application objective is stronger:

```text
use RAKL to discover or construct a working spot-movement mechanism/formalism
and a successful predictive spot model;
failed candidate theories are not accepted as project closure.
```

This does **not** authorize evidence fabrication, target leakage, post-result threshold rescue, selective reporting, or relabeling a failed test as a positive result. It changes the search/stopping semantics: negative candidate results become inputs to continued mechanism invention rather than terminal project conclusions.

Round 035 remains frozen. Round 036 is an additive method/objective contract.

## Audit result

The pre-Round-036 architecture already contained strong epistemic machinery:

- knowledge fibers and contextual projections;
- compatibility-constrained global lattice;
- GLUE/JUMP similarity algebra;
- generator transport and witnessed analogy;
- residual-driven recursion;
- metacognitive method-basis gap detection;
- capability shaping and governed self-evolution.

However, mechanism/formalism invention remained too implicit. The documentation instructed the LLM to derive a new formalism, while the executable core primarily validated, glued, transported and ranked already-materialized candidates. Mathematical objects were often stored as strings rather than as manipulable structures.

## New method objects

Round 036 adds:

```text
src/rakl/formalism.py
src/rakl/invention.py
src/rakl/constructive_lattice.py
src/rakl/math_oracles.py
src/rakl/invention_benchmark.py
schemas/formalism.schema.json
skills/rakl-core/workflows/mechanism-invention.md
research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json
```

and extends the Knowledge Fiber schema and RAKL workflow manifest.

## 1. Typed formalism intermediate representation

A certifying candidate can now be represented as typed objects containing:

```text
symbols with roles/domains/units/availability
equation ASTs
mechanism nodes and edges
observation maps
assumptions
regimes
invariants
limit cases
symmetries
boundary conditions
parent formalism ids
invention move ids
evidence lineage
```

This allows RAKL to operate on mathematical/mechanistic structure rather than relying only on display text.

## 2. Constructive invention algebra

The initial operator basis includes:

```text
COMPOSE / RECOMBINE
ADD/REMOVE_LATENT_STATE
SPLIT/MERGE_REGIME
CHANGE_CLOCK
COARSE_GRAIN / FINE_GRAIN
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

Every move is a typed delta with explicit residual targets, provenance, chronology and parent lineage.

## 3. Residual-to-operator routing

Residual signatures are typed across distributional, temporal, regime, tail, volatility, cross-asset, cross-venue, flow/liquidity, observation, clock, causal, identifiability, calibration, transport, predictive and unclassified failure classes.

Each class maps to a diverse initial operator family. This is a search prior, not an authority rule. Persistent unclassified residuals can trigger method-basis expansion through the existing metacognitive/self-evolution machinery.

## 4. Candidate population and Pareto tournament

RAKL now supports candidate theory populations evaluated on:

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

A Pareto frontier is retained rather than reducing scientific quality to one fit statistic.

## 5. Positive-goal contract

`PositiveGoalContract` makes the user's intended stopping semantics executable:

```text
GOAL_ACHIEVED
```

is the only successful closure state.

A failed candidate returns:

```text
CANDIDATE_REJECTED_CONTINUE
```

rather than a negative scientific project closure. The goal thresholds must be frozen before candidate results and cannot be weakened post hoc.

The Polymarket/crypto application is bound by:

`research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json`

## 6. Constructive Knowledge State

`ConstructiveKnowledgeState` binds residuals, candidate formalisms, invention moves, theory scores and the positive-goal contract directly to an executable `KnowledgeFiber`.

Registration of a candidate does not promote it. It only places the typed object inside the constructive search state. Authority remains governed by verification/promotion layers.

## 7. Mathematical verification

The first automatic mathematical oracle is dimensional consistency over the typed expression tree. It can infer dimensions through addition/subtraction, products/ratios, powers, derivatives, integrals, expectations/sums, and registered dimensionless functions.

This is intentionally only the first oracle. Future operator fibers should add symbolic simplification, invariant checking, stability/well-posedness solvers, differentiability/support constraints, stochastic-process validity and theorem/proof backends where appropriate.

## 8. Invention capability benchmark

A new hidden-world benchmark distinguishes plausible generation from demonstrated invention capability.

World families include:

```text
RECONSTRUCTION
NOVEL_COMPOSITION
CROSS_DOMAIN_TRANSFER
ADVERSARIAL_RESIDUAL
```

The hidden target signature must remain unavailable to the proposer; thresholds are frozen; the candidate is frozen before target exposure; a separate evaluator scores structural recovery and target validation.

A `NOVEL_COMPOSITION` world additionally requires recovery of a combination not supplied as one source component.

## Positive-result search semantics

The intended application loop is now:

```text
knowledge lattice
-> typed candidate population
-> formal + empirical verification
-> structured residual
-> GLUE/JUMP expansion
-> constructive invention operators
-> mutated/recombined typed candidates
-> theory tournament
-> positive-goal evaluation
-> repeat unless GOAL_ACHIEVED
```

If every current candidate fails, the project remains active. RAKL reopens the implicated object fibers and, when necessary, evolves its own invention-operator basis.

## Important limit

RAKL can guarantee persistence of the search procedure and integrity of the success definition. It cannot logically guarantee that a finite dataset contains enough information to identify a true mechanism or that nature provides exploitable predictive information at the registered horizons.

The framework therefore forbids a false guarantee while still implementing the requested operational rule: **do not accept failure of the current candidate set as project closure.**

## New atomic fibers

1. `META_N107_FORMALISM_IR_EXPRESSIVENESS` — test whether the typed IR can faithfully encode target-domain and alien-domain formalisms.
2. `META_N108_INVENTION_OPERATOR_COVERAGE` — hidden-world ablations of the constructive operator basis.
3. `META_N109_MATH_ORACLE_EXPANSION` — symbolic, stability, stochastic and proof/checking backends.
4. `META_N110_POSITIVE_GOAL_SEARCH_POLICY` — compare mutation/recombination/operator-selection policies under fixed budgets.
5. `META_N111_SPOT_MECHANISM_CONSTRUCTIVE_LATTICE` — instantiate the Round-036 machinery on the real crypto spot residuals.
6. `META_N112_INVENTION_ASSURANCE_RESERVE` — fresh hidden mechanism/formalism worlds withheld from operator development.

## Saturation

`ACTIVE_NON_FLAT`.

The main architectural gap identified in Round 035 has been converted into executable method objects, but their invention power still requires hidden-world and real-case evidence. No capability claim is promoted merely because the code exists.
