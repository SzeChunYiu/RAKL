# RAKL Problem-Solving Algebra

Status: reference planning layer  
Date: 2026-08-10

## 1. Scope

The phrase **problem-solving algebra** names a typed composition system for reusable research moves. It is not a claim that all reasoning methods form one global mathematical lattice or a total algebra with universally defined operations.

The operational substrate is a directed typed state-transition system with local partial orders/lattices only where meet/join obligations are actually satisfied.

A problem state is

\[
S=(\sigma,F,O,R,B,H,\tau),
\]

where:

- `sigma` is a structured problem signature;
- `F` is the set of currently licensed or candidate facts used for planning;
- `O` is the set of open verification/proof obligations;
- `R` is the active representation set — **explicitly provisional**: membership in `R` is a
  pursuit-state commitment, not a scientific claim, and a material residual may reopen it
  (recursive framework audit, `FORMAL_SYSTEM_SPECIFICATION.md` §8.1);
- `B` is the explicit obstruction set;
- `H` is the applied-operator history;
- `tau` is the terminal status.

A reusable operator is

\[
T=(\mathrm{Pre},\mathrm{Transform},\mathrm{Post},B_T,C_T,D_T,R_T,F_T),
\]

with preconditions, symbolic transformation, postconditions, targeted blockers, cost, verification debt, boundary risk and failure modes.

The implementation is `src/rakl/problem_solving_algebra.py`.

## 2. Why this is not one global lattice

Different methods are frequently incomparable. A Fourier transform and a minimal-counterexample argument do not in general have a unique least upper bound. Two representation changes may be mutually incompatible. Some moves are directional and non-invertible. Some consume information. Some introduce obligations that cannot be discharged in the original domain.

RAKL therefore uses:

```text
typed directed transition system
+ local relation-specific partial orders/lattices
+ explicit obstructions when composition fails
```

This follows the same rule used elsewhere in RAKL: never call a structure a lattice merely because it is graph-shaped.

## 3. Problem signatures

A `ProblemSignature` records the dimensions that should condition method retrieval:

```text
objects
relations
quantifiers
symmetries
domain
goal type
constraints
```

The signature is not assumed complete. Residuals can open missing signature coordinates.

## 4. Operator families

The reference vocabulary includes:

```text
goal transforms
representation changes
decomposition
reduction
invariant search
relaxation
extremal/order moves
symmetry operations
local-global moves
computational search
formal verification
novelty search
meta/discovery operators
```

A domain-specific method is treated as a specialization of one or more typed operators, not as evidence that the ontology is complete.

## 5. Obstruction-guided path search

RAKL does not assume that a problem has a pre-stored solution path. The planner searches reusable path fragments conditioned on the current blockers.

The reference path objective is a transparent heuristic of the form

\[
J(\pi)=C(\pi)+2D(\pi)+2R(\pi)+|B_{\rm remain}|-3|B_{\rm relieved}|,
\]

where `C` is modeled cost, `D` verification debt, `R` boundary risk, and the final terms reward explicit obstruction relief.

This is a planning score, not a probability that a theorem is true.

`search_operator_paths` performs bounded best-first search. It returns candidate research routes only.

## 6. Non-commutativity and partial composition

Operator composition is partial. For example:

```text
formalize target -> formal proof search
```

is licensed after the first move produces the required formal-statement fact. Reversing the order is not licensed.

Consequently

\[
T_2\circ T_1
\]

may exist while

\[
T_1\circ T_2
\]

does not.

This non-commutativity is an intended property, not an implementation defect.

## 7. Planning transitions cannot mint authority

`apply_operator_symbolic` changes a **planning projection**. It can add candidate facts, representations and obligations and can model the removal of a search blocker. It can never set a terminal result.

Terminal outcomes include:

```text
PROOF
COUNTEREXAMPLE
INDEPENDENCE_RELATIVE
REFORMULATED
PARTIAL_RESULT
OPEN
```

A non-open outcome requires a `TerminalCertificate` with explicit scope, artifact identity and `verified=True`.

This prevents the path planner from confusing "a route looks complete" with "the mathematical/scientific claim is established."

## 8. Mathematical-research specialization

`src/rakl/math_research_runtime.py` compiles the mathematical assurance state into blockers and then invokes the problem-solving algebra.

The assurance coordinates remain non-compensatory:

```text
specification alignment
proof truth
verifier trust
bounded novelty
research value
```

The planner can suggest how to attack missing coordinates. It cannot promote them.

## 9. Default mathematical path motifs

The default atlas contains representative moves including:

```text
change representation
introduce auxiliary object
search invariant
decompose problem
reformulate ill-posed target
formalize target
audit formalization alignment
counterexample-first search
formal proof search
verify proof artifact
search prior art
review research value
```

This is a seed grammar. Self-RAKL may propose additional operators when repeated residuals show that the basis is insufficient. New operators require explicit contracts and frozen transfer tests before becoming canonical defaults.

Reformulation is bidirectional: a supported reformulation may **reopen the parent** state —
staling descendant closure certificates while keeping their evidence addressable — rather
than merely terminating the current path and starting a sibling. Ascent requires a supported
parent challenge plus at least two distinct failed local repair families
(`src/rakl/recursive_framework_audit.py`).

## 10. Claim boundary

The reference implementation establishes typed planning semantics, fail-closed terminal closure and executable conformance tests. It does **not** establish that this operator basis is universally complete, that its heuristic is globally optimal, or that it improves discovery productivity on open mathematics. Those are empirical coordinates for later evaluation.
