# Mechanics-of-Mechanics Architecture

## 1. Problem

The existing solver has many strong operators, but the choice of **which solver mechanic should change next** is not yet a single explicit research object.

The new layer should diagnose whether failure is caused by:

```text
bad evidence
bad representation
bad decomposition
wrong scale
wrong search route
wrong method/operator
missing auxiliary object
bad verifier
bad composition interface
model/tool floor
resource floor
ontology gap
stopping error
```

and then select a discriminating action.

## 2. Core object: MechanicDeficiencyWitness

A witness is not an introspective opinion. It is a bounded, auditable diagnosis packet.

Provisional structure:

```python
@dataclass(frozen=True)
class MechanicDeficiencyWitness:
    witness_id: str
    root_problem_id: str
    root_qoi_id: str
    fibre_snapshot_hash: str

    observed_residual_ids: tuple[str, ...]
    candidate_causes: tuple[MechanicCauseCandidate, ...]
    ruled_out_causes: tuple[str, ...]
    unresolved_causes: tuple[str, ...]

    discriminating_actions: tuple[DiscriminatingAction, ...]
    required_external_evidence: tuple[str, ...]
    chronology_hash: str

    verdict: MechanicDiagnosisVerdict
```

Candidate cause:

```python
@dataclass(frozen=True)
class MechanicCauseCandidate:
    mechanic: MechanicKind
    support_features: tuple[str, ...]
    contradiction_features: tuple[str, ...]
    confidence_kind: str  # calibrated_probability / set_member / heuristic_only
    score: float | None
```

## 3. Mechanic taxonomy

Initial enum:

```text
EVIDENCE
REPRESENTATION
DECOMPOSITION
SCALE
CONTEXT
RETRIEVAL
METHOD_OPERATOR
AUXILIARY_OBJECT
EXPERIMENT_SELECTION
VERIFICATION
COMPOSITION_INTERFACE
MEMORY_VIEW
MODEL_TOOL
COMPUTE_ALLOCATION
STOPPING
ONTOLOGY
IMPLEMENTATION
UNKNOWN
```

Do not allow automatic invention of arbitrary new enum members at runtime. Unknown residuals go to `UNKNOWN` / ontology-gap handling.

## 4. Diagnosis workflow

```text
observe failed / partial / costly attempt
        ↓
extract external residual features
        ↓
map known failure signatures
        ↓
generate candidate mechanic causes
        ↓
find cheapest action that separates surviving causes
        ↓
execute discriminator
        ↓
update witness
        ↓
if identified:
    construct mechanic action
else:
    CANNOT_CHECK / PARTIALLY_IDENTIFIED
```

This is deliberately analogous to scientific differential diagnosis.

## 5. Meta-actions

```python
class MetaActionKind(Enum):
    KEEP_MECHANIC = ...
    CHANGE_REPRESENTATION = ...
    REFINE_DECOMPOSITION = ...
    COARSEN_DECOMPOSITION = ...
    REFINE_SCALE = ...
    COARSEN_SCALE = ...
    CHANGE_RETRIEVAL = ...
    CHANGE_OPERATOR = ...
    INVENT_AUXILIARY_OBJECT = ...
    RUN_DISCRIMINATOR = ...
    SWITCH_VERIFIER = ...
    REPAIR_INTERFACE = ...
    CHANGE_MEMORY_VIEW = ...
    SWITCH_MODEL_TOOL = ...
    REALLOCATE_COMPUTE = ...
    EXPLORE_COVERAGE = ...
    STOP_COMMIT = ...
    STOP_CANNOT_CHECK = ...
```

## 6. Decision objective

Do not require calibrated probabilities everywhere.

If calibrated:

\[
a^* =
\arg\max_a
\frac{
\mathbb E[\Delta R_{\rm root}(a)]
}{
C(a)
}
\]

where \(\Delta R_{\rm root}\) is **verified** root-residual reduction.

If probabilities are not justified, use set-valued dominance:

```text
remove impossible actions
remove authority-violating actions
remove actions dominated on all observed coordinates
prefer actions that separate surviving causes
retain explicit exploration branch
```

## 7. Diagnosis quality versus specialist quality

These must be measured separately.

Let:

- \(q\): probability/correctness of identifying the relevant mechanic;
- \(p_m\): success when the correct specialist mechanic is used;
- \(p_w\): success when the wrong specialist is used;
- \(p_0\): incumbent generic continuation.

The router is useful only if:

\[
q p_m + (1-q)p_w > p_0.
\]

Therefore benchmarks must report:

```text
cause-identification accuracy
action-selection accuracy
specialist conditional success
wrong-specialist success
end-to-end success
```

## 8. Controller architecture

```text
MechanicsController
│
├── ResidualExtractor
├── MechanicDiagnosisEngine
├── DiscriminatorPlanner
├── ActionPortfolio
│    ├── RepresentationSearch
│    ├── ScalePolicy
│    ├── Existing SearchController
│    ├── AuxiliaryObjectSearch
│    ├── SolutionField
│    ├── VerifierScheduler
│    └── ComputeRouter
├── RootProgressEvaluator
└── MechanicsEpisodeRecorder
```

The existing search controller should be one action family inside this layer, not deleted.

## 9. Mechanics episode

Every run records:

```text
state-before
witness
candidate meta-actions
selection rationale
resource ceiling
action result
root result
verification result
counterfactual baseline result if benchmarked
state-after
```

This becomes training data later.

## 10. Learning later

Only after deterministic and fixed-policy versions pass should Orion learn:

```text
P(mechanic deficiency | observable state)
E(root gain | state, meta-action)
cost prediction
field initialization
representation-effect prediction
```

The first version should be explicit/rule-based enough to audit.
