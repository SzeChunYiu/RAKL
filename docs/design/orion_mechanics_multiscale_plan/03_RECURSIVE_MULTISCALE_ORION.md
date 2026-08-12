# Recursive Multiscale Orion

## 1. Why “fractal” needs precision

The useful scientific hypothesis is not that Orion literally forms a mathematical fractal.

Split the intuition into four testable hypotheses:

1. **Self-similar kernel:** approximately the same solve/verify/residual loop works at multiple scales.
2. **Adaptive scale:** the system benefits from dynamically refining or coarsening reasoning granularity.
3. **Contracted composition:** local solutions can be composed safely only through explicit interfaces.
4. **Emergent residuals:** failures may appear at a higher scale even when every child passes locally.

## 2. Scale kernel

At scale \(s\):

\[
\mathcal O_s=
(X_s,Q_s,\Gamma_s,A_s,V_s,E_s,C_s,I_s)
\]

where:

- `X_s`: scale-local state;
- `Q_s`: local target linked to root QoI;
- `Gamma_s`: scoped context;
- `A_s`: admissible actions;
- `V_s`: verifier;
- `E_s`: residual;
- `C_s`: resource budget;
- `I_s`: interfaces to parent/siblings/children.

## 3. Refinement and coarsening

Refinement:

\[
\rho_{s\to s-1}:
\mathcal O_s
\rightarrow
\{\mathcal O_{s-1}^{(1)},\ldots,\mathcal O_{s-1}^{(k)}\}
\]

Coarsening:

\[
\kappa_{s-1\to s}.
\]

Every transition emits `ScaleTransitionWitness`.

Required fields:

```text
source_scale_id
target_scale_id
reason
root_qoi_projection
preserved_coordinates
lost_or_approximated_coordinates
coverage_change
interface_requirements
inverse_or_roundtrip_test
cost
```

## 4. Round-trip test

Where meaningful:

\[
\kappa(\rho(X)) \approx_Q X.
\]

Do **not** demand literal identity. Demand explicit QoI-relative preservation.

Possible verdicts:

```text
EXACT_QOI_PRESERVING
BOUNDED_QOI_DISTORTION
PARTIALLY_IDENTIFIED
NOT_PRESERVED
CANNOT_CHECK
```

## 5. Scale actions

```text
REFINE_LOCAL
REFINE_GLOBAL_SCOUT
COARSEN_SUMMARY
COARSEN_BY_INVARIANT
MERGE_SIBLINGS
SPLIT_BY_REGIME
SPLIT_BY_INTERFACE
KEEP_SCALE
```

## 6. Exploration floor

The earlier hidden-feature stress test demonstrates a critical failure:

```text
small local residual
does not imply
no unresolved fine-scale structure
```

Therefore introduce `CoverageScoutPolicy`.

It maintains:

```text
coverage_map
unseen-region estimate
mandatory scout budget
last scout epoch
hidden-facet challenge history
```

A scale controller cannot certify saturation solely from local error.

## 7. Multigrid-inspired principle

Different residual modes may require different scales.

This becomes a *testable* Orion rule:

```text
high-frequency/local residual
    -> local refinement may help

low-frequency/global/coherence residual
    -> coarsening or global representation may help
```

Do not hard-code this universally. Encode as a hypothesis with benchmark labels.

## 8. Composition

Every child exposes an interface:

```python
@dataclass(frozen=True)
class SolverInterfaceContract:
    interface_id: str
    producer_atom_id: str
    consumer_atom_id: str

    required_keys: tuple[str, ...]
    provided_keys: tuple[str, ...]
    assumptions: tuple[str, ...]
    invariants: tuple[str, ...]
    uncertainty_semantics: tuple[str, ...]
    verifier_id: str | None
```

A parent is not solved because all children are solved.

Require:

```text
child validity
+
interface compatibility
+
parent invariant
+
complete coverage
```

## 9. Hierarchical verification

Verifying every edge independently may compound false negatives.

Support multiple verification levels:

```text
LOCAL
INTERFACE
SUBTREE
ROOT
```

A `VerificationSchedule` decides where to spend checks.

Benchmark:

```text
verify every edge
verify root only
risk-adaptive hierarchical verification
```

## 10. Emergent residual

Add explicit residual kind:

```text
EMERGENT_COMPOSITION_RESIDUAL
```

Definition:

```text
all selected child sections pass local verification
AND
parent/root invariant fails
AND
failure cannot be assigned to one child without additional evidence
```

This triggers:

```text
interface diagnosis
higher-scale representation search
or new parent-level mechanic
```

It should not automatically blame a child.

## 11. Recursive stopping

A subtree may stop while root continues.

Track:

```text
LOCAL_SOLVED
LOCAL_SATURATED
LOCAL_CANNOT_CHECK
PARENT_REOPENED
ROOT_SOLVED
```

A new parent residual can reopen any implicated child.

## 12. Initial benchmark worlds

Build deterministic worlds with:

1. narrow hidden local feature;
2. broad low-frequency residual invisible to local refiners;
3. independent children with incompatible interfaces;
4. all-local-pass but global parity/invariant failure;
5. representation where coarse view reveals a shortcut;
6. representation where refinement is essential;
7. misleading scale heuristic.

The benchmark must have an oracle optimum or enumerably computable reference policy.
