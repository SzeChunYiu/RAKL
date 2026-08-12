# Proposed Data Models and APIs

The goal is to add the smallest coherent object layer before implementing sophisticated policies.

## 1. New modules

Recommended initial files:

```text
src/rakl/mechanic_deficiency.py
src/rakl/representation_search.py
src/rakl/scale_policy.py
src/rakl/solution_field.py
src/rakl/auxiliary_object.py
src/rakl/mechanics_controller.py
src/rakl/mechanics_telemetry.py
```

Later:

```text
src/rakl/verifier_scheduler.py
src/rakl/cognitive_budget.py
src/rakl/mechanics_atlas.py
```

Do not create a deep new package hierarchy until imports stabilize; the repository currently uses a flat `src/rakl` module style.

## 2. `mechanic_deficiency.py`

```python
class MechanicKind(str, Enum):
    EVIDENCE = "EVIDENCE"
    REPRESENTATION = "REPRESENTATION"
    DECOMPOSITION = "DECOMPOSITION"
    SCALE = "SCALE"
    CONTEXT = "CONTEXT"
    RETRIEVAL = "RETRIEVAL"
    METHOD_OPERATOR = "METHOD_OPERATOR"
    AUXILIARY_OBJECT = "AUXILIARY_OBJECT"
    EXPERIMENT_SELECTION = "EXPERIMENT_SELECTION"
    VERIFICATION = "VERIFICATION"
    COMPOSITION_INTERFACE = "COMPOSITION_INTERFACE"
    MEMORY_VIEW = "MEMORY_VIEW"
    MODEL_TOOL = "MODEL_TOOL"
    COMPUTE_ALLOCATION = "COMPUTE_ALLOCATION"
    STOPPING = "STOPPING"
    ONTOLOGY = "ONTOLOGY"
    IMPLEMENTATION = "IMPLEMENTATION"
    UNKNOWN = "UNKNOWN"
```

```python
class MechanicDiagnosisVerdict(str, Enum):
    NO_GAP = "NO_GAP"
    KNOWN_MECHANIC_WEAKNESS = "KNOWN_MECHANIC_WEAKNESS"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    MECHANIC_GAP_IDENTIFIED = "MECHANIC_GAP_IDENTIFIED"
    DISCRIMINATOR_REQUIRED = "DISCRIMINATOR_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"
```

Key function:

```python
def diagnose_mechanic_deficiency(
    *,
    atom: ProblemAtom,
    fibre: ProblemFibre,
    residuals: tuple[ResidualSignature, ...],
    observable_outcomes: tuple[ObservableOutcome, ...],
    incumbent_capabilities: tuple[MechanicCapability, ...],
) -> MechanicDeficiencyWitness:
    ...
```

V0 can be deterministic rules.

## 3. `representation_search.py`

```python
class RepresentationEffect(str, Enum):
    LINEARIZES = "LINEARIZES"
    CONVEXIFIES = "CONVEXIFIES"
    LOCALIZES = "LOCALIZES"
    DECOUPLES = "DECOUPLES"
    FACTORIZES = "FACTORIZES"
    EXPOSES_SYMMETRY = "EXPOSES_SYMMETRY"
    EXPOSES_INVARIANT = "EXPOSES_INVARIANT"
    REDUCES_DIMENSION = "REDUCES_DIMENSION"
    INCREASES_DIMENSION = "INCREASES_DIMENSION"
    MAKES_COMPOSITION_EXPLICIT = "MAKES_COMPOSITION_EXPLICIT"
    MAKES_COUNTEREXAMPLE_CHEAP = "MAKES_COUNTEREXAMPLE_CHEAP"
    MAKES_VERIFICATION_TRACTABLE = "MAKES_VERIFICATION_TRACTABLE"
    TURNS_GLOBAL_TO_LOCAL = "TURNS_GLOBAL_TO_LOCAL"
    TURNS_PATH_SEARCH_TO_FIELD = "TURNS_PATH_SEARCH_TO_FIELD"
```

```python
@dataclass(frozen=True)
class RepresentationTransform:
    transform_id: str
    input_kinds: tuple[str, ...]
    output_kind: str
    claimed_effects: tuple[RepresentationEffect, ...]
    cost_units: float
    reversible: bool | None
```

Core:

```python
def propose_representations(
    atom: ProblemAtom,
    fibre: ProblemFibre,
    transforms: tuple[RepresentationTransform, ...],
    *,
    budget: float,
) -> tuple[RepresentationCandidate, ...]:
    ...
```

```python
def evaluate_representation_probe(
    candidate: RepresentationCandidate,
    probe: RepresentationProbe,
) -> RepresentationProbeResult:
    ...
```

## 4. `scale_policy.py`

```python
class ScaleAction(str, Enum):
    KEEP = "KEEP"
    REFINE_LOCAL = "REFINE_LOCAL"
    REFINE_GLOBAL_SCOUT = "REFINE_GLOBAL_SCOUT"
    COARSEN = "COARSEN"
    SPLIT_REGIME = "SPLIT_REGIME"
    MERGE = "MERGE"
```

```python
@dataclass(frozen=True)
class ScaleState:
    scale_id: str
    parent_scale_id: str | None
    depth: int
    coverage_coordinates: tuple[str, ...]
    unresolved_coordinates: tuple[str, ...]
    local_residual: float | None
    coverage_risk: float | None
```

```python
def choose_scale_action(
    state: ScaleState,
    residual: ResidualSignature,
    coverage: CoverageReceipt,
    budget: ScaleBudget,
) -> ScaleDecision:
    ...
```

## 5. `solution_field.py`

```python
@dataclass(frozen=True)
class FieldNode:
    node_id: str
    state_hash: str
    representation_id: str
    scale_id: str
    terminal_kind: str | None = None
```

```python
@dataclass(frozen=True)
class FieldEdge:
    edge_id: str
    source_id: str
    target_id: str
    action_id: str

    base_cost: float
    conductance: float
    viability: float | None
    interface_valid: bool | None
    authority_effect: str = "PROPOSAL_ONLY"
```

```python
@dataclass(frozen=True)
class SolutionPotentialField:
    field_id: str
    graph_hash: str
    boundary_hash: str
    node_potentials: tuple[tuple[str, float], ...]
    edge_fluxes: tuple[tuple[str, float], ...]
    construction_cost: float
    exactness: str
```

Functions:

```python
def solve_conductive_field(
    nodes: tuple[FieldNode, ...],
    edges: tuple[FieldEdge, ...],
    boundary: FieldBoundaryCondition,
) -> SolutionPotentialField:
    ...
```

```python
def rank_field_actions(
    field: SolutionPotentialField,
    current_node_id: str,
    *,
    diversity_k: int,
) -> tuple[FieldActionProposal, ...]:
    ...
```

```python
def update_conductance(
    edge: FieldEdge,
    outcome: VerifiedActionOutcome,
    policy: ConductanceUpdatePolicy,
) -> FieldEdge:
    ...
```

## 6. `auxiliary_object.py`

```python
class AuxiliaryObjectKind(str, Enum):
    LEMMA = "LEMMA"
    INVARIANT = "INVARIANT"
    LATENT_VARIABLE = "LATENT_VARIABLE"
    OBSERVABLE = "OBSERVABLE"
    POTENTIAL_FUNCTION = "POTENTIAL_FUNCTION"
    INTERMEDIATE_REPRESENTATION = "INTERMEDIATE_REPRESENTATION"
    SURROGATE = "SURROGATE"
    DECOMPOSITION_INTERFACE = "DECOMPOSITION_INTERFACE"
    DUAL_OBJECT = "DUAL_OBJECT"
    ADJUSTMENT_SET = "ADJUSTMENT_SET"
```

```python
@dataclass(frozen=True)
class AuxiliaryObjectRequest:
    request_id: str
    residual_id: str
    desired_effects: tuple[str, ...]
    admissible_kinds: tuple[AuxiliaryObjectKind, ...]
    falsifiers: tuple[str, ...]
```

## 7. `mechanics_controller.py`

```python
class MetaActionKind(str, Enum):
    ...
```

```python
@dataclass(frozen=True)
class MechanicsDecisionState:
    decision_id: str
    root_problem_id: str
    atom_id: str
    fibre_snapshot_hash: str
    residual_ids: tuple[str, ...]
    diagnosis_witness_id: str
    active_representation_id: str
    active_scale_id: str
    resource_remaining: float
```

```python
@dataclass(frozen=True)
class MechanicsActionProposal:
    action_id: str
    kind: MetaActionKind
    expected_effects: tuple[str, ...]
    required_inputs: tuple[str, ...]
    cost_lower_bound: float
    cost_upper_bound: float | None
    proposal_only: bool = True
```

```python
def plan_next_mechanics_action(
    state: MechanicsDecisionState,
    witness: MechanicDeficiencyWitness,
    candidates: tuple[MechanicsActionProposal, ...],
    *,
    policy: MechanicsPolicy,
) -> MechanicsPlan:
    ...
```

## 8. `mechanics_telemetry.py`

```python
@dataclass(frozen=True)
class MechanicsEpisode:
    episode_id: str
    subject_hash: str
    pre_state_hash: str
    diagnosis_hash: str
    action_hash: str
    outcome_hash: str
    root_effect_hash: str
    verifier_receipt_id: str | None
    resource_receipt_id: str
```

Store JSONL only from explicit serializable fields.

## 9. Stable hashes

Use existing canonical hashing utilities where possible.

Every new object should distinguish:

```text
identity hash
content hash
subject hash
snapshot hash
```

Do not overload one hash for all semantics.

## 10. Failure semantics

Each module must prefer explicit enums over exceptions for scientific outcomes.

Exceptions are for malformed input / programming errors.

Scientific failures return objects such as:

```text
REFUTED
PARTIALLY_IDENTIFIED
CANNOT_CHECK
BLOCKED
NO_BENEFIT
COST_FAILURE
```

## 11. No cross-module authority side effects

New modules should be pure or append-only where practical.

They must not directly mutate canonical authority state.
