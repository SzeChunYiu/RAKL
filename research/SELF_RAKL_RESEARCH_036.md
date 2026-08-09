# SELF-RAKL Research Round 036 — Constructive Invention Engine and Positive-Goal Loop

Date: 2026-08-09  
Status: implementation / method-basis expansion

## Trigger

The `polymarket_crypto` application objective is stronger than evaluating a fixed model menu:

```text
use RAKL to discover or construct a working spot-movement mechanism/formalism
and a successful predictive spot model;
failed candidate theories are not accepted as project closure.
```

This changes search/stopping semantics, not evidence standards. It does not authorize evidence fabrication, leakage, post-result threshold rescue, selective reporting, or relabeling failure as a positive.

Round 035 remains frozen. Round 036 is additive.

## Pre-Round-036 gap

RAKL already had Knowledge Fibers, contextual projections, the compatibility lattice, GLUE/JUMP, generator transport, residual recursion, metacognition and governed self-evolution. But “derive a new formalism” was still too dependent on an LLM producing a plausible candidate in prose. The executable system was stronger at validation and epistemic organization than constructive scientific invention.

## Round-036 method objects

Round 036 now adds:

```text
src/rakl/formalism.py                 typed mathematical/mechanism IR
src/rakl/typed_lattice.py             typed lattice atoms + compatibility-witnessed paths
src/rakl/invention.py                 constructive operators, residuals, tournament, goal contract
src/rakl/constructive_lattice.py      candidate/residual state bound to KnowledgeFiber
src/rakl/mechanism_compiler.py        mechanism edge -> interaction law -> state equation
src/rakl/symbolic_discovery.py        bounded native symbolic-law discovery
src/rakl/math_oracles.py              dimensional consistency
src/rakl/formal_oracles.py            identifiability/stability/stochastic validity
src/rakl/hard_gates.py                exact non-compensatory positive gates
src/rakl/search_controller.py         autonomous residual-driven generation scheduler
src/rakl/invention_benchmark.py       hidden-world invention capability tests
src/rakl/invention_runtime.py         end-to-end positive-goal invention coordinator
src/rakl/invention_api.py             public facade
schemas/formalism.schema.json
schemas/typed-lattice.schema.json
skills/rakl-core/workflows/mechanism-invention.md
research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json
```

The Knowledge Fiber schema and workflow manifest are also extended.

## 1. Typed constructive Knowledge Lattice

RAKL now distinguishes the semantic/raw fiber dimensions from a constructive typed lattice. First-class atom kinds include observables, representations, mechanism nodes/edges, equations/expressions, assumptions, regimes, observation models, coarse-graining operators, invariants, symmetries, falsifiers, data products, inference methods, QoIs, causal relations, failure motifs and analogy motifs.

Compatibility is witnessed pairwise. Strict synthesis paths reject missing/incompatible relations. A compatible path becomes a residual-specific synthesis seed with typed payload references, evidence lineage, source fibers, conditions and candidate invention operators.

This closes the gap between “knowledge lattice as atlas” and “knowledge lattice as theory-construction substrate.”

## 2. Typed formalism and mechanism IR

Candidate theories are represented with symbols, expression ASTs, equations, mechanism graphs, observation maps, assumptions, regimes, invariants, limits, symmetries, boundary conditions and invention lineage.

Text-only equations or mechanism labels are insufficient for a certifying invention lane.

## 3. Constructive invention algebra

The operator basis includes composition/recombination; latent-state and regime changes; clock/coarse-graining changes; generalization/specialization/limits/duality; stochasticization; feedback/coupling/interaction changes; assumption changes; invariants/symmetries; nonlinearization; analogical motif import; observation-map changes; and residual-explanation moves.

Every move is a frozen typed delta tied to residual ids and parent candidate lineage. Exact shared ancestry is deduplicated during recombination; conflicting objects under one identity are rejected.

## 4. Mechanism compiler

A mechanism graph is not accepted as mechanistic mathematics merely because equations appear elsewhere in the candidate. Influential mechanism edges must be bound to formal `InteractionLaw` objects and compiled into state-evolution equations. Missing influential edge laws are `CANNOT_CHECK`; post-result laws are rejected.

This produces explicit ancestry:

```text
mechanism edge -> interaction law -> state equation -> observation
```

## 5. Native symbolic mathematical discovery

RAKL now has a bounded symbolic discovery operator rather than relying exclusively on LLM equation proposals.

The operator searches a frozen expression grammar on training-only data, including nonlinear products/ratios/powers/functions, deduplicates observationally equivalent expressions, fits affine wrappers and two-basis combinations, and emits typed structural equations.

Discovery fit has no predictive authority until untouched/forward validation.

## 6. Residual-driven autonomous search

Goal failures are automatically converted into typed residual signatures. Residual kinds route to diverse invention operators.

`SearchController` schedules multiple operator families, tracks retries and proposal counts, preserves Pareto parents and prioritizes symbolic/solver generation for mathematical moves.

If a finite search allocation is exhausted, the state is:

```text
RESOURCE_BLOCK_NONTERMINAL
```

not project failure or success. A renewable budget can resume the same search identity. If all registered operators are exhausted against a persistent residual, the next state is a RAKL `METHOD_BASIS_GAP_CANDIDATE` problem.

## 7. Candidate tournament

Candidates remain on a Pareto frontier across descriptive coverage, residual closure, predictive value, identification, falsifiability, robustness, novelty and complexity. No single fit statistic is allowed to hide a blocking defect.

## 8. Formal and mathematical verification

Built-in machine-checkable oracles now include:

```text
formal symbol/expression/mechanism integrity
dimensional consistency
local sensitivity-rank identifiability
1D/2D continuous-time Hurwitz stability
1D/2D discrete-time Jury/Schur stability
small covariance positive-semidefinite validity
transition-matrix stochastic validity
exact-candidate verification binding
```

Unsupported higher-dimensional or domain-specific problems return `CANNOT_CHECK` and route to specialist symbolic, numerical, causal, stochastic or proof backends.

## 9. Exact positive hard gates

The normalized candidate score is not enough for closure. `hard_gates.py` requires exact non-compensatory gates.

The Polymarket/crypto contract includes typed formalism, registered descriptive-axis coverage, mechanism ancestry, residual closure, falsifier execution, full-history teacher non-vacuity, identical causal rows, strict availability, frozen 5m/15m target, predeclared materiality, multiplicity-aware inference, positive untouched/forward LCB, calibration, transport, mechanism/prediction authority linkage, formal verification, exact candidate binding, independent review, evidence lineage and no blocking integrity failure.

One failed hard gate rejects the candidate and continues the search. It cannot be averaged away.

## 10. Hidden-world invention benchmark

RAKL distinguishes plausible proposal generation from evidence of invention capability using withheld-target worlds:

```text
RECONSTRUCTION
NOVEL_COMPOSITION
CROSS_DOMAIN_TRANSFER
ADVERSARIAL_RESIDUAL
```

Novel-composition worlds require recovering a combination not supplied as one complete source component. Target exposure, chronology contamination or evaluator non-independence invalidates the trial.

## 11. End-to-end runtime

`InventionRuntime` unifies the closure state:

```text
typed lattice
-> synthesis seed / generation request
-> candidate formalism
-> mechanism compilation and/or symbolic discovery
-> verification
-> numeric goal + exact hard gates
-> typed residual if not positive
-> reopen fibers / schedule next diverse invention round
-> repeat
```

`GOAL_ACHIEVED` is the only successful terminal state.

## Polymarket/crypto binding

The application is bound by:

`research/RAKL_POLYMARKET_CRYPTO_POSITIVE_GOAL_CONTRACT_036.json`

Round 035 remains immutable. Round 036 changes the continuation semantics after failure of a candidate family.

## Integrity limit

RAKL can make persistence and closure semantics absolute: current model failure, literature saturation or finite-budget exhaustion are not accepted as successful closure.

RAKL cannot logically force a finite dataset to contain information that is not there. The framework therefore refuses a fake guarantee while still implementing the requested operational rule: **continue constructive discovery until the positive contract passes, or record a nonterminal evidence/resource/method-basis block that can be reopened.**

## Remaining external-resource fibers

The core framework-level invention gaps identified in the audit are now represented and implemented. Remaining capability expansion is primarily specialist-resource integration and empirical evidence:

1. `META_N107_FORMALISM_IR_EXPRESSIVENESS` — hostile encoding tests for richer mathematics.
2. `META_N108_INVENTION_OPERATOR_COVERAGE` — hidden-world ablations and operator-basis evolution.
3. `META_N109_SPECIALIST_ORACLE_BACKENDS` — higher-dimensional stability, stochastic-process, CAS and proof backends.
4. `META_N110_SEARCH_POLICY_LEARNING` — compare/learn operator-selection policies under equal budgets.
5. `META_N111_SPOT_MECHANISM_CONSTRUCTIVE_LATTICE` — instantiate on real crypto spot data/residuals.
6. `META_N112_INVENTION_ASSURANCE_RESERVE` — fresh hidden worlds withheld from development.

## Saturation

`ACTIVE_NON_FLAT`.

Implementation completeness is not scientific capability evidence. Round 036 must still pass hidden-world invention benchmarks and the real quant-finance case before any strong invention claim is promoted.
