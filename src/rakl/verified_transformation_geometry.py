"""Typed contracts for Verified Transformation Geometry (VTG).

VTG is a solver/search projection over already-governed RAKL objects, not a
parallel truth ontology.  The contracts here make explicit the layers that are
otherwise easy to conflate:

  exact transition topology -> discovered operational map -> quotient/atlas
  -> routing geometry/potential -> search policy/trajectory -> proof DAG/constellation

Only the repository's existing verifier/authority path may mint theorem or
scientific authority.  Every object in this module returns False for authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class EdgeAssuranceClass(str, Enum):
    KERNEL_DERIVATION = "KERNEL_DERIVATION"
    REPLAY_VALIDATED_OPERATIONAL = "REPLAY_VALIDATED_OPERATIONAL"
    CANDIDATE_OPERATIONAL = "CANDIDATE_OPERATIONAL"


class ReachabilityQuantifier(str, Enum):
    EXISTS_PATH = "EXISTS_PATH"
    POLICY_CONTROLLABLE = "POLICY_CONTROLLABLE"
    ROBUST_FOR_ALL_ADMISSIBLE_OUTCOMES = "ROBUST_FOR_ALL_ADMISSIBLE_OUTCOMES"
    ALMOST_SURE = "ALMOST_SURE"
    PROBABILITY_AT_LEAST = "PROBABILITY_AT_LEAST"
    EXPECTED_COST_BOUNDED = "EXPECTED_COST_BOUNDED"
    ADVERSARIAL_GAME = "ADVERSARIAL_GAME"


class AbstractionClass(str, Enum):
    EXACT_QUOTIENT = "EXACT_QUOTIENT"
    SOUND_OVERAPPROXIMATION = "SOUND_OVERAPPROXIMATION"
    EMPIRICAL_ROUTING_VIEW = "EMPIRICAL_ROUTING_VIEW"


class ConstructibilityClass(str, Enum):
    EXACT_FINITE_ENUMERATION = "EXACT_FINITE_ENUMERATION"
    POLYNOMIAL_REGISTERED_CLASS = "POLYNOMIAL_REGISTERED_CLASS"
    FIXED_PARAMETER = "FIXED_PARAMETER"
    AMORTIZED_PRECOMPUTATION = "AMORTIZED_PRECOMPUTATION"
    APPROXIMATE_LEARNED = "APPROXIMATE_LEARNED"
    ORACLE_EVALUATOR_ONLY = "ORACLE_EVALUATOR_ONLY"
    UNKNOWN = "UNKNOWN"


class GeometryUseVerdict(str, Enum):
    READY_FOR_FRESH_ROUTING_TEST = "READY_FOR_FRESH_ROUTING_TEST"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
    INVALID = "INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class AbstractRouteVerdict(str, Enum):
    CONCRETE_ROUTE_VERIFIED = "CONCRETE_ROUTE_VERIFIED"
    SPURIOUS_ROUTE_REFINE = "SPURIOUS_ROUTE_REFINE"
    CANNOT_CHECK = "CANNOT_CHECK"


class AmalgamationVerdict(str, Enum):
    READY_FOR_ROOT_AUTHORITY_GATE = "READY_FOR_ROOT_AUTHORITY_GATE"
    CONFLICT = "CONFLICT"
    INCOMPLETE = "INCOMPLETE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class OperationalSubject:
    """Exact operational world in which topology/geometry statements live."""

    environment_hash: str
    logic_or_kernel_version: str
    elaborator_or_tool_version: str
    options_hash: str
    operator_basis_hash: str
    transition_semantics_hash: str
    operational_map_revision_hash: str
    chart_catalog_hash: str
    cost_model_hash: str

    def __post_init__(self) -> None:
        values = tuple(getattr(self, name) for name in self.__dataclass_fields__)
        if any(not value.strip() for value in values):
            raise ValueError("operational subject must bind every semantic/version coordinate")


@dataclass(frozen=True)
class ResolvedOperationalReceipt:
    """Output adapter for an actual replay/verifier resolution.

    This object grants no epistemic/theorem authority; it only prevents routing
    consumers from treating a caller-named receipt ID as if it had been resolved.
    Production wiring should construct it from the repository's protected/replay
    verifier rather than from untrusted request data.
    """

    receipt_id: str
    subject: OperationalSubject
    resolver_id: str
    resolver_artifact_hash: str
    passed: bool

    def __post_init__(self) -> None:
        if any(not x for x in (self.receipt_id, self.resolver_id, self.resolver_artifact_hash)):
            raise ValueError("resolved operational receipt requires receipt/resolver identity")

    @property
    def grants_authority(self) -> bool:
        return False


def _resolution_matches(
    receipt_id: str | None,
    subject: OperationalSubject,
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    if not receipt_id:
        return False
    return any(
        item.receipt_id == receipt_id and item.subject == subject and item.passed
        for item in resolutions
    )


@dataclass(frozen=True)
class EdgeAssuranceReceipt:
    edge_id: str
    subject: OperationalSubject
    source_state_hash: str
    target_state_hash: str
    assurance: EdgeAssuranceClass
    verifier_or_replay_receipt_id: str | None
    premise_state_hashes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.edge_id or not self.source_state_hash or not self.target_state_hash:
            raise ValueError("edge/source/target identity required")
        if self.assurance is not EdgeAssuranceClass.CANDIDATE_OPERATIONAL and not self.verifier_or_replay_receipt_id:
            raise ValueError("validated edge requires verifier/replay receipt")
        if len(set(self.premise_state_hashes)) != len(self.premise_state_hashes):
            raise ValueError("premise state hashes must be unique")

    @property
    def declares_validated_operational_edge(self) -> bool:
        return self.assurance is not EdgeAssuranceClass.CANDIDATE_OPERATIONAL

    @property
    def grants_theorem_authority(self) -> bool:
        return False


def edge_ready_for_navigation(
    edge: EdgeAssuranceReceipt,
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    return edge.declares_validated_operational_edge and _resolution_matches(
        edge.verifier_or_replay_receipt_id, edge.subject, resolutions
    )


@dataclass(frozen=True)
class ReachabilityClaim:
    claim_id: str
    subject: OperationalSubject
    start_state_hash: str
    target_region_hash: str
    quantifier: ReachabilityQuantifier
    policy_or_strategy_id: str | None = None
    probability_threshold: float | None = None
    expected_cost_bound: float | None = None
    evidence_receipt_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim_id or not self.start_state_hash or not self.target_region_hash:
            raise ValueError("reachability claim identities required")
        if self.quantifier is not ReachabilityQuantifier.EXISTS_PATH and not self.policy_or_strategy_id:
            raise ValueError("non-existential reachability requires policy/strategy identity")
        if self.quantifier is ReachabilityQuantifier.PROBABILITY_AT_LEAST:
            if self.probability_threshold is None or not 0 <= self.probability_threshold <= 1:
                raise ValueError("probability threshold in [0,1] required")
        elif self.probability_threshold is not None:
            raise ValueError("probability threshold only valid for PROBABILITY_AT_LEAST")
        if self.quantifier is ReachabilityQuantifier.EXPECTED_COST_BOUNDED:
            if self.expected_cost_bound is None or not isfinite(self.expected_cost_bound) or self.expected_cost_bound < 0:
                raise ValueError("finite nonnegative expected cost bound required")
        elif self.expected_cost_bound is not None:
            raise ValueError("expected cost bound only valid for EXPECTED_COST_BOUNDED")

    @property
    def grants_target_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class NavigationAbstractionContract:
    abstraction_id: str
    subject: OperationalSubject
    concrete_subject_hash: str
    abstract_subject_hash: str
    abstraction_map_id: str
    concretization_relation_id: str
    abstraction_class: AbstractionClass
    forward_soundness_receipt_id: str | None
    route_lifting_receipt_id: str | None = None
    backward_completeness_receipt_id: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.abstraction_id,
            self.concrete_subject_hash,
            self.abstract_subject_hash,
            self.abstraction_map_id,
            self.concretization_relation_id,
        )
        if any(not x for x in required):
            raise ValueError("concrete/abstract semantics required")
        if self.abstraction_class is not AbstractionClass.EMPIRICAL_ROUTING_VIEW and not self.forward_soundness_receipt_id:
            raise ValueError("sound/exact abstraction requires forward-soundness receipt")
        if self.abstraction_class is AbstractionClass.EXACT_QUOTIENT and not (
            self.route_lifting_receipt_id and self.backward_completeness_receipt_id
        ):
            raise ValueError("exact quotient requires route lifting and backward completeness")

    @property
    def abstract_impossibility_is_sound(self) -> bool:
        return self.abstraction_class is AbstractionClass.EXACT_QUOTIENT and bool(self.backward_completeness_receipt_id)


@dataclass(frozen=True)
class AbstractRouteCheck:
    route_id: str
    abstraction_id: str
    concrete_replay_receipt_id: str | None = None
    counterexample_or_spurious_id: str | None = None
    refinement_request_id: str | None = None

    @property
    def verdict(self) -> AbstractRouteVerdict:
        if self.concrete_replay_receipt_id:
            return AbstractRouteVerdict.CONCRETE_ROUTE_VERIFIED
        if self.counterexample_or_spurious_id and self.refinement_request_id:
            return AbstractRouteVerdict.SPURIOUS_ROUTE_REFINE
        return AbstractRouteVerdict.CANNOT_CHECK

    @property
    def grants_solution_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class CostVector:
    formalization: float = 0.0
    construction: float = 0.0
    compute: float = 0.0
    verifier: float = 0.0
    model: float = 0.0
    storage: float = 0.0

    def __post_init__(self) -> None:
        for value in self.as_tuple():
            if not isfinite(value) or value < 0:
                raise ValueError("cost coordinates must be finite and nonnegative")

    def as_tuple(self) -> tuple[float, ...]:
        return (self.formalization, self.construction, self.compute, self.verifier, self.model, self.storage)


@dataclass(frozen=True)
class GeometryLearningReceipt:
    receipt_id: str
    geometry_id: str
    subject: OperationalSubject
    training_subject_hashes: tuple[str, ...]
    behavior_policy_ids: tuple[str, ...]
    sampling_process_id: str
    label_source_id: str
    code_hash: str
    model_or_algorithm_hash: str
    train_split_hash: str
    dev_split_hash: str
    fresh_split_hash: str
    seen_operator_ids: tuple[str, ...]
    seen_chart_ids: tuple[str, ...]
    seen_scale_ids: tuple[str, ...]
    fresh_gold_route_accessed: bool
    fresh_gold_distance_accessed: bool
    fresh_labels_accessed_during_selection: bool
    support_diagnostic_id: str
    ood_detector_id: str | None
    exploration_reopen_policy_id: str

    def __post_init__(self) -> None:
        required = (
            self.receipt_id,
            self.geometry_id,
            self.training_subject_hashes,
            self.behavior_policy_ids,
            self.sampling_process_id,
            self.label_source_id,
            self.code_hash,
            self.model_or_algorithm_hash,
            self.train_split_hash,
            self.dev_split_hash,
            self.fresh_split_hash,
            self.support_diagnostic_id,
            self.exploration_reopen_policy_id,
        )
        if any(not x for x in required):
            raise ValueError("geometry learning receipt requires full provenance/support binding")
        if len({self.train_split_hash, self.dev_split_hash, self.fresh_split_hash}) != 3:
            raise ValueError("train/dev/fresh split identities must be distinct")
        for name in ("training_subject_hashes", "behavior_policy_ids", "seen_operator_ids", "seen_chart_ids", "seen_scale_ids"):
            values = getattr(self, name)
            if len(values) != len(set(values)) or any(not x for x in values):
                raise ValueError(f"{name} must contain unique nonempty identities")

    @property
    def leakage_free_for_fresh_claim(self) -> bool:
        return not (
            self.fresh_gold_route_accessed
            or self.fresh_gold_distance_accessed
            or self.fresh_labels_accessed_during_selection
        )

    def support_contains(self, *, operator_id: str, chart_id: str, scale_id: str) -> bool:
        return operator_id in self.seen_operator_ids and chart_id in self.seen_chart_ids and scale_id in self.seen_scale_ids

    @property
    def grants_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class GeometryArtifact:
    geometry_id: str
    subject: OperationalSubject
    learning_receipt_id: str | None
    constructibility: ConstructibilityClass
    build_cost: CostVector
    expected_reuse: float | None
    invalidation_horizon_uses: float | None
    baseline_total_cost: float | None = None
    geometry_total_cost: float | None = None
    total_cost_accounting_receipt_id: str | None = None
    fieldability_identity_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.geometry_id:
            raise ValueError("geometry identity required")
        for value in (self.expected_reuse, self.invalidation_horizon_uses, self.baseline_total_cost, self.geometry_total_cost):
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError("reuse/horizon/total-cost values must be finite and nonnegative")
        if self.constructibility is ConstructibilityClass.APPROXIMATE_LEARNED and not self.learning_receipt_id:
            raise ValueError("learned geometry requires learning receipt")
        # Exact/admissible/consistent heuristic theorems are owned by the existing
        # ``rakl.fieldability.GeometryArtifactIdentity`` / CertificationWitness
        # surface. This sidecar may bind that identity hash but does not define a
        # second certification ontology.
        if self.fieldability_identity_hash is not None and not self.fieldability_identity_hash.strip():
            raise ValueError("fieldability identity hash must be omitted or nonempty")

    def stale_for(self, subject: OperationalSubject) -> bool:
        return subject != self.subject

    @property
    def demonstrates_net_cost_gain(self) -> bool:
        return (
            self.total_cost_accounting_receipt_id is not None
            and self.baseline_total_cost is not None
            and self.geometry_total_cost is not None
            and self.geometry_total_cost < self.baseline_total_cost
        )

    @property
    def solver_usable(self) -> bool:
        return self.constructibility is not ConstructibilityClass.ORACLE_EVALUATOR_ONLY

    @property
    def grants_authority(self) -> bool:
        return False


def assess_geometry_for_fresh_routing(
    artifact: GeometryArtifact,
    *,
    current_subject: OperationalSubject,
    learning_receipt: GeometryLearningReceipt | None = None,
) -> GeometryUseVerdict:
    if artifact.stale_for(current_subject):
        return GeometryUseVerdict.INVALID
    if not artifact.solver_usable:
        return GeometryUseVerdict.DEVELOPMENT_ONLY
    if artifact.constructibility is ConstructibilityClass.UNKNOWN:
        return GeometryUseVerdict.CANNOT_CHECK
    if artifact.constructibility is ConstructibilityClass.APPROXIMATE_LEARNED:
        if learning_receipt is None or artifact.learning_receipt_id != learning_receipt.receipt_id:
            return GeometryUseVerdict.CANNOT_CHECK
        if learning_receipt.geometry_id != artifact.geometry_id or learning_receipt.subject != artifact.subject:
            return GeometryUseVerdict.INVALID
        if not learning_receipt.leakage_free_for_fresh_claim:
            return GeometryUseVerdict.INVALID
    return GeometryUseVerdict.READY_FOR_FRESH_ROUTING_TEST


@dataclass(frozen=True)
class NavigationBasinCertificate:
    basin_id: str
    subject: OperationalSubject
    basin_subject_hash: str
    membership_checker_id: str
    membership_soundness_receipt_id: str
    progress_action_checker_id: str
    progress_soundness_receipt_id: str
    well_founded_rank_receipt_id: str
    goal_minimum_receipt_id: str
    boundary_semantics_id: str
    boundary_soundness_receipt_id: str
    admitted_edge_assurance_floor: EdgeAssuranceClass

    def __post_init__(self) -> None:
        required = (
            self.basin_id,
            self.basin_subject_hash,
            self.membership_checker_id,
            self.membership_soundness_receipt_id,
            self.progress_action_checker_id,
            self.progress_soundness_receipt_id,
            self.well_founded_rank_receipt_id,
            self.goal_minimum_receipt_id,
            self.boundary_semantics_id,
            self.boundary_soundness_receipt_id,
        )
        if any(not x for x in required):
            raise ValueError("navigation basin requires every theorem obligation")
        if self.admitted_edge_assurance_floor is EdgeAssuranceClass.CANDIDATE_OPERATIONAL:
            raise ValueError("certified basin cannot admit candidate-only edges")

    @property
    def grants_theorem_authority(self) -> bool:
        return False


def navigation_basin_ready_for_use(
    basin: NavigationBasinCertificate,
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    receipt_ids = (
        basin.membership_soundness_receipt_id,
        basin.progress_soundness_receipt_id,
        basin.well_founded_rank_receipt_id,
        basin.goal_minimum_receipt_id,
        basin.boundary_soundness_receipt_id,
    )
    return all(_resolution_matches(rid, basin.subject, resolutions) for rid in receipt_ids)


@dataclass(frozen=True)
class PortalWitness:
    portal_id: str
    subject: OperationalSubject
    source_chart_id: str
    target_chart_id: str
    source_statement_hash: str
    target_statement_hash: str
    preserved_properties: frozenset[str]
    non_preserved_properties: frozenset[str]
    boundary_receipt_ids: tuple[str, ...]
    verifier_receipt_id: str
    inverse_or_roundtrip_receipt_id: str | None = None

    def __post_init__(self) -> None:
        if any(not x for x in (self.portal_id, self.source_chart_id, self.target_chart_id, self.source_statement_hash, self.target_statement_hash, self.verifier_receipt_id)):
            raise ValueError("portal requires chart/statement/verifier identity")
        if self.preserved_properties & self.non_preserved_properties:
            raise ValueError("property cannot be both preserved and non-preserved")

    def declares_preservation_for(self, properties: frozenset[str]) -> bool:
        return not bool(properties & self.non_preserved_properties) and properties <= self.preserved_properties

    @property
    def grants_theorem_authority(self) -> bool:
        return False


def portal_ready_for_use(
    portal: PortalWitness,
    properties: frozenset[str],
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    if not portal.declares_preservation_for(properties):
        return False
    required = (portal.verifier_receipt_id,) + portal.boundary_receipt_ids
    return all(_resolution_matches(rid, portal.subject, resolutions) for rid in required)


@dataclass(frozen=True)
class SearchTrajectoryReceipt:
    trajectory_id: str
    subject: OperationalSubject
    start_state_hash: str
    terminal_state_hash: str
    edge_ids: tuple[str, ...]
    policy_id: str
    verified_terminal_receipt_id: str | None = None

    @property
    def is_proof_certificate(self) -> bool:
        return False

    @property
    def declares_verified_terminal(self) -> bool:
        return bool(self.verified_terminal_receipt_id)


def trajectory_terminal_is_resolved(
    trajectory: SearchTrajectoryReceipt,
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    return _resolution_matches(trajectory.verified_terminal_receipt_id, trajectory.subject, resolutions)


@dataclass(frozen=True)
class SolutionConstellationBinding:
    constellation_id: str
    root_statement_hash: str
    proof_dag_hash: str
    root_verifier_receipt_id: str
    trajectory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.constellation_id or not self.root_statement_hash or not self.proof_dag_hash or not self.root_verifier_receipt_id:
            raise ValueError("solution constellation requires proof DAG and root verification")


@dataclass(frozen=True)
class AmalgamationReceipt:
    amalgamation_id: str
    root_subject_hash: str
    child_certificate_hashes: tuple[str, ...]
    overlap_compatibility_receipt_ids: tuple[str, ...]
    substitution_coherence_receipt_id: str | None
    assumption_discharge_receipt_ids: tuple[str, ...]
    representation_compatibility_receipt_ids: tuple[str, ...]
    joint_obligation_receipt_ids: tuple[str, ...]
    parent_invariant_receipt_id: str | None
    root_verifier_receipt_id: str | None
    conflict_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.amalgamation_id or not self.root_subject_hash or not self.child_certificate_hashes:
            raise ValueError("root/child identity required")
        if len(self.child_certificate_hashes) != len(set(self.child_certificate_hashes)):
            raise ValueError("child certificate hashes must be unique")

    @property
    def verdict(self) -> AmalgamationVerdict:
        if self.conflict_ids:
            return AmalgamationVerdict.CONFLICT
        if not self.overlap_compatibility_receipt_ids or not self.assumption_discharge_receipt_ids or not self.representation_compatibility_receipt_ids or not self.joint_obligation_receipt_ids:
            return AmalgamationVerdict.INCOMPLETE
        if not self.substitution_coherence_receipt_id or not self.parent_invariant_receipt_id:
            return AmalgamationVerdict.CANNOT_CHECK
        if not self.root_verifier_receipt_id:
            return AmalgamationVerdict.INCOMPLETE
        return AmalgamationVerdict.READY_FOR_ROOT_AUTHORITY_GATE

    @property
    def grants_authority(self) -> bool:
        return False


def amalgamation_ready_for_root_gate(
    receipt: AmalgamationReceipt,
    subject: OperationalSubject,
    resolutions: tuple[ResolvedOperationalReceipt, ...],
) -> bool:
    if receipt.verdict is not AmalgamationVerdict.READY_FOR_ROOT_AUTHORITY_GATE:
        return False
    required = (
        *receipt.overlap_compatibility_receipt_ids,
        receipt.substitution_coherence_receipt_id,
        *receipt.assumption_discharge_receipt_ids,
        *receipt.representation_compatibility_receipt_ids,
        *receipt.joint_obligation_receipt_ids,
        receipt.parent_invariant_receipt_id,
        receipt.root_verifier_receipt_id,
    )
    return all(rid is not None and _resolution_matches(rid, subject, resolutions) for rid in required)


@dataclass(frozen=True)
class SolveProjection:
    """Problem-conditioned routing view ``pi_solve``; never ``pi_epi``."""

    projection_id: str
    subject: OperationalSubject
    problem_hash: str
    assumptions_hash: str
    target_region_hash: str
    abstraction_ids: tuple[str, ...]
    geometry_id: str | None
    reachability_claim_ids: tuple[str, ...]
    policy_id: str | None
    projection_frozen_before_outcome_access: bool | None

    def __post_init__(self) -> None:
        if not self.projection_id or not self.problem_hash or not self.assumptions_hash or not self.target_region_hash:
            raise ValueError("solve projection identities required")

    @property
    def ready_for_routing_experiment(self) -> bool:
        return self.projection_frozen_before_outcome_access is True

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_proof_authority(self) -> bool:
        return False
