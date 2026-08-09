# Workflow — Mechanism / Formalism Invention

Use when existing representations do not close a registered scientific residual, or when the goal explicitly requires discovery/construction of a working mechanism rather than comparison of a fixed model menu.

## Governing objective

RAKL is goal-seeking but fail-closed.

```text
candidate failure != project closure
candidate failure -> residual -> new invention round
```

A positive goal may be declared mandatory. The success thresholds must be frozen before the evaluated results. RAKL must never fabricate evidence, alter observations, relabel an unresolved result as positive, or weaken the success thresholds after seeing failures.

## Inputs

Require:

```text
current typed formalism/mechanism
relevant knowledge fibers
compatibility-constrained lattice slice
registered residual signature(s)
source/evidence lineage
frozen positive-goal contract
available verification oracles
data/observation boundary
```

## Constructive invention algebra

Generate multiple typed candidate deltas using applicable operators, including:

```text
COMPOSE / RECOMBINE
ADD_LATENT_STATE / REMOVE_LATENT_STATE
SPLIT_REGIME / MERGE_REGIME
CHANGE_CLOCK
COARSE_GRAIN / FINE_GRAIN
GENERALIZE / SPECIALIZE / TAKE_LIMIT / DUALIZE
STOCHASTICIZE / DETERMINIZE
ADD_FEEDBACK / REMOVE_FEEDBACK
ADD_COUPLING / REMOVE_COUPLING
ADD_INTERACTION
RELAX_ASSUMPTION / STRENGTHEN_ASSUMPTION
ADD_INVARIANT
ADD_SYMMETRY / BREAK_SYMMETRY
NONLINEARIZE / LINEARIZE
IMPORT_ANALOGICAL_MOTIF
CHANGE_OBSERVATION_MAP
EXPLAIN_RESIDUAL
```

Do not treat these as prose prompts only. Every invention must materialize a typed delta containing added/removed symbols, equations, mechanism nodes/edges, assumptions, regimes or symmetries plus provenance and targeted residual ids.

## Lattice-guided generation

For each residual:

1. identify implicated fibers and missing coordinates;
2. construct the compatible local lattice slice;
3. retrieve GLUE alternatives and witnessed JUMP motifs;
4. select several non-equivalent invention operators;
5. generate a candidate family rather than one preferred narrative;
6. preserve parent candidate ids and complete move lineage;
7. predeclare measurable implications and falsifiers before native evaluation.

The proposer may be an LLM, symbolic search system, numerical optimizer, specialist solver or human. The proposer never grants authority.

## Typed theory object

Each candidate should contain at minimum:

```text
symbols with roles/domains/units/availability
equation ASTs
mechanism graph
observation map
assumptions
regime scope
invariants / symmetries
limit cases / boundary conditions
falsifiers
parent formalism ids
invention move ids
evidence lineage
```

Text-only equations or mechanism labels are insufficient for a certifying invention lane.

## Verification stack

Bind every verification receipt to the exact formalism id. Required checks should include, when applicable:

```text
symbol/type integrity
dimensional consistency
limiting cases
invariants and conservation constraints
stability / well-posedness
identifiability
simulation sanity
clock/availability/leakage checks
falsifier execution
native out-of-sample prediction
calibration
transport
```

A missing check is `CANNOT_CHECK`, not a pass.

## Candidate tournament

Evaluate candidates on a vector rather than one fit statistic:

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

Maintain a Pareto frontier. A predictive winner is not automatically a mechanism; a compact mechanism is not automatically the best predictor.

## Positive-goal loop

The project closes positively only when one exact candidate satisfies the frozen goal contract and required verification/review gates.

If a candidate fails:

```text
FAILED CANDIDATE
-> retain negative receipt
-> classify residual structure
-> reopen implicated fibers
-> select new operators
-> generate/mutate/recombine candidate population
-> freeze predictions/falsifiers
-> verify
-> execute native test
-> reevaluate positive-goal contract
```

If the current method basis cannot generate a plausible candidate for a persistent residual, open a `METHOD_BASIS_GAP_CANDIDATE` and evolve the invention-operator basis itself under the RAKL self-evolution protocol.

## Integrity boundary

RAKL may be persistent about the objective, but not dishonest about the evidence.

Forbidden shortcuts include:

```text
post-result threshold rescue
target leakage
changing clocks/populations after outcome inspection
selectively dropping failed candidates
unregistered multiplicity
inventing measurements or citations
promoting an analogy as target evidence
calling a descriptive fit a mechanism without ancestry
calling in-sample fit predictive success
```

The intended behavior is persistent scientific search, not guaranteed statistical significance by construction.
