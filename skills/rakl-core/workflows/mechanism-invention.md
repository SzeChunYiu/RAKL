# Workflow — Mechanism / Formalism Invention

Use when existing representations do not close a registered scientific residual, or when the goal explicitly requires discovery/construction of a working mechanism rather than comparison of a fixed model menu.

## Governing objective

RAKL is goal-seeking but fail-closed.

```text
candidate failure != project closure
candidate failure -> residual -> new invention round
```

A positive goal may be declared mandatory. The success thresholds must be frozen before the evaluated results. RAKL must never fabricate evidence, alter observations, relabel an unresolved result as positive, or weaken the success thresholds after seeing failures.

When the mathematical or research router has selected `LIFT`, invention is **inverse-constrained** by the frozen `MissingTransformationSpecification`. Do not interpret “existing attempts failed” as permission for arbitrary novelty.

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

When entered from semantic-shortcut `LIFT`, additionally require:

```text
obstruction-transformation review id/hash
bounded exhaustion witness
multiple residual failure ids
repeated residual feature(s)
MissingTransformationSpecification:
  must_preserve
  must_break
  must_expose
  must_reduce
  allowed_representation_changes
  forbidden_shortcuts
  validation_obligations
  falsifiers
```

A missing or weak LIFT specification routes back to obstruction–transformation review rather than to unconstrained invention.

## Inverse invention target

Before generating a new object, convert the residual into a transformation contract.

Instead of asking only:

> What new object might solve this?

ask:

> What transformation would have to exist to move the current obstruction into a state the incumbent reasoning basis can solve?

Represent the desired operator schematically as:

```text
current obstruction O
  -- T? -->
tractable state O'
```

The repeated failure structure constrains `T?`:

```text
preserve load-bearing invariants
break the repeated obstruction feature
expose a relation/coordinate hidden in the incumbent representation
reduce a registered search/verification burden
avoid forbidden losses such as weakening the target
```

The proposer may invent a new representation, auxiliary object, invariant, coordinate system, transformation, decomposition, lemma family, operator, notation, algorithm, observation map, or other reusable reasoning primitive. “Tool” is therefore broader than software: it is a reusable transformation that can reduce reasoning/search cost under explicit preconditions.

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

For a LIFT-driven candidate, also record which `MissingTransformationSpecification` clauses the delta claims to satisfy and what observation/proof would falsify each clause.

## Lattice-guided generation

For each residual:

1. identify implicated fibers and missing coordinates;
2. construct the compatible local lattice slice;
3. confirm the upstream obstruction–transformation review has already attempted direct SEARCH, witnessed JUMP and compatible GLUE before LIFT;
4. retrieve any remaining GLUE alternatives and witnessed JUMP motifs as negative controls against premature invention;
5. if LIFT is valid, compile the missing-transformation specification into explicit generator constraints;
6. select several non-equivalent invention operators capable of satisfying those constraints;
7. generate a candidate family rather than one preferred narrative;
8. preserve parent candidate ids, source residual ids, shortcut-review id and complete move lineage;
9. predeclare measurable implications and falsifiers before native evaluation.

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

For LIFT-driven invention also include:

```text
missing-transformation specification id
residual failure ids
claimed preserve/break/expose/reduce clauses
representation changes used
forbidden-loss audit
target-specific validation obligations
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

For LIFT candidates, explicitly test whether the new representation/operator actually preserves each required invariant, breaks the repeated residual feature, exposes the promised coordinate, reduces the registered burden, and avoids every forbidden loss. Solving one development case is insufficient for reusable-tool promotion.

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

For new reasoning primitives also track:

```text
target search-cost reduction
transfer to neighboring/fresh problems
compression of previously complex structure
exceptions / broken preconditions
verification debt introduced
```

Maintain a Pareto frontier. A predictive winner is not automatically a mechanism; a compact mechanism is not automatically the best predictor. A candidate that solves one target by definition but has no reusable scope is not automatically a useful new tool.

## Positive-goal loop

The project closes positively only when one exact candidate satisfies the frozen goal contract and required verification/review gates.

If a candidate fails:

```text
FAILED CANDIDATE
-> retain negative receipt
-> classify residual structure
-> update failure lattice
-> compare residual with prior LIFT-driving residuals
-> reopen implicated fibers / obstruction-transform review when structure changed
-> select new constrained operators
-> generate/mutate/recombine candidate population
-> freeze predictions/falsifiers
-> verify
-> execute native test
-> reevaluate positive-goal contract
```

A failed invented tool can sharpen the missing-transformation specification. It must not be deleted merely because it was unsuccessful.

If the current invention basis cannot generate a plausible candidate for a persistent residual, do **not** immediately declare a new method-basis gap. First verify that the upstream SEARCH/JUMP/GLUE exhaustion witness remains valid under the new residual evidence. Only when the epistemic cut is identified, the earlier semantic routes are boundedly exhausted/blocked, and the incumbent invention-operator basis cannot satisfy the missing-transformation specification should RAKL open a `METHOD_BASIS_GAP_CANDIDATE` and evolve the invention-operator basis itself under the self-evolution protocol.

## Consolidation into knowledge

A successful invented transformation feeds back into RAKL only at the authority actually earned:

```text
successful target candidate
-> target validation / proof
-> fresh or neighboring transfer tests where reuse is claimed
-> scoped ResearchTool candidate
-> obstruction-transformation episode with source/target lineage
-> future SEARCH/JUMP retrieval
```

Thus invention changes the future search geometry only after validation. A new primitive does not become globally valid because it shortened one proof.

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
entering LIFT after one failure
calling unbounded retrieval failure evidence of human-knowledge exhaustion
inventing a tool that solves the target only by weakening/redefining it
promoting a new representation without target-equivalence/forbidden-loss checks
```

The intended behavior is persistent scientific search, not guaranteed statistical significance or novelty by construction.
