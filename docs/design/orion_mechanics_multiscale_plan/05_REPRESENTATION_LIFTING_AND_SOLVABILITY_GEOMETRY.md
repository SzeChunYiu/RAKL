# Representation Lifting and Solvability Geometry

## 1. Representation becomes an action

Current systems often treat representation as input formatting or passive metadata.

Orion should treat:

```text
CHANGE_REPRESENTATION
```

as a first-class solver action.

## 2. Representation candidate

```python
@dataclass(frozen=True)
class RepresentationCandidate:
    representation_id: str
    source_object_hash: str
    transform_id: str
    coordinates: tuple[str, ...]
    claimed_effects: tuple["RepresentationEffect", ...]
    assumptions: tuple[str, ...]
    inverse_status: str
    decode_verifier_id: str | None
    proposal_only: bool = True
```

## 3. Effect vocabulary

Start with a closed enum:

```text
LINEARIZES
CONVEXIFIES
LOCALIZES
DECOUPLES
FACTORIZES
EXPOSES_SYMMETRY
EXPOSES_INVARIANT
EXPOSES_CAUSAL_ORDER
REDUCES_DIMENSION
INCREASES_DIMENSION
REMOVES_NUISANCE
MAKES_COMPOSITION_EXPLICIT
MAKES_CONSTRAINTS_EXPLICIT
MAKES_COUNTEREXAMPLE_CHEAP
MAKES_VERIFICATION_TRACTABLE
TURNS_GLOBAL_TO_LOCAL
TURNS_PATH_SEARCH_TO_FIELD
```

A representation can claim multiple effects, but claims are proposal-only until measured.

## 4. Representation witness

```python
@dataclass(frozen=True)
class RepresentationTransitionWitness:
    witness_id: str
    source_representation_id: str
    target_representation_id: str

    preserved: tuple[str, ...]
    not_preserved: tuple[str, ...]
    unknown_preservation: tuple[str, ...]

    reconstruction_available: bool | None
    reconstruction_error_bound: float | None
    downstream_verifier_id: str | None
```

## 5. Solvability geometry hypothesis

We want an embedding:

\[
\phi : X \to Z
\]

with metric \(d_Z\) such that distance and direction encode **solver reachability**.

A strong but testable property:

\[
d_Z(\phi(x),\phi(y))
\approx
\text{minimal verified cost to transform }x\to y.
\]

We do not expect this to hold globally.

Instead record scope:

```text
task family
mechanic family
representation regime
cost definition
verifier
```

## 6. Field-ready representation criteria

A representation is `FIELD_READY` only if all hold on a benchmark:

1. **Local action separability:** different action consequences are distinguishable.
2. **Progress alignment:** local field direction predicts actual progress.
3. **Decode validity:** field-space paths decode to executable actions.
4. **Low enough construction cost.**
5. **Fresh transfer:** geometry does not exist only on memorized tasks.

## 7. Higher-dimensional lifting

“Go one dimension higher” should become an explicit search operator family.

Examples of generic mechanism patterns to learn from:

```text
nonlinear -> lifted linear
nonconvex -> lifted convex
discrete -> continuous relaxation
global constraint -> local compatibility conditions
path enumeration -> potential/value field
raw state -> invariant coordinates
many correlated variables -> sufficient statistic
surface form -> structural/operator graph
```

Do not copy the donor method as a whole. Record the **transformation effect**.

## 8. Representation search algorithm V0

Input:

```text
ProblemAtom
ProblemFibre
active residual
candidate transforms
resource ceiling
```

Process:

```text
for transform in admissible transforms:
    apply transform
    validate preservation contract
    run cheap probe suite
    estimate effect vector
    reject obvious regressions
return Pareto frontier of representations
```

Probe suite can measure:

```text
search branching factor
constraint locality
verifier availability
operator applicability
residual separability
field alignment
decode cost
```

## 9. V1: representation portfolio

Instead of one representation, maintain:

```text
R = {R_1, ..., R_k}
```

Allow different mechanics to work in different charts.

This composes naturally with current atlas/gluing semantics.

## 10. V2: representation transitions as paths

A solution may require:

```text
R0
-> R1 expose invariant
-> R2 decompose
-> R3 solve locally
-> R4 reconstruct
```

Now representation search itself is a graph problem.

The mechanics controller may apply the solution-field machinery to this graph.

## 11. Failure modes

```text
REPRESENTATION_LOSS
REPRESENTATION_FALSE_EQUIVALENCE
LIFT_OVERHEAD_DOMINATES
DECODE_FAILURE
VERIFIER_UNAVAILABLE_IN_TARGET_CHART
LOCALITY_ILLUSION
FIELD_ALIGNMENT_OVERFIT
REPRESENTATION_CYCLE
REPRESENTATION_BLOAT
```

## 12. Benchmark construction

Create pairs where the same underlying problem has representations with known effects:

- SAT clauses versus factor graph;
- grid path versus distance-transform field;
- polynomial system versus lifted monomial variables;
- nonlinear finite-state dynamics versus known linearizing coordinates;
- equation solving with/without substitution exposing linear form;
- graph connectivity with/without contracted components;
- proof search with/without a helper lemma;
- composition problem with/without explicit interface variables.

The aim is not to show that “representation matters.” The aim is to test whether Orion can **select or construct** the useful representation.
