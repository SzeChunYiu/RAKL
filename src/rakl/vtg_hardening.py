from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from math import inf
from typing import Tuple

from .math_research_assurance import AssuranceVerdict, ProofReceipt, audit_proof_receipt


def _hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class GeometryConstructibilityClass(str, Enum):
    EXACT_FINITE_ENUMERATION = "EXACT_FINITE_ENUMERATION"
    POLYNOMIAL_REGISTERED_CLASS = "POLYNOMIAL_REGISTERED_CLASS"
    FIXED_PARAMETER_REGISTERED_CLASS = "FIXED_PARAMETER_REGISTERED_CLASS"
    AMORTIZED_PRECOMPUTATION = "AMORTIZED_PRECOMPUTATION"
    APPROXIMATE_LEARNED = "APPROXIMATE_LEARNED"
    ORACLE_EVALUATOR_ONLY = "ORACLE_EVALUATOR_ONLY"
    UNKNOWN_COMPLEXITY = "UNKNOWN_COMPLEXITY"
    UNCOMPUTABLE_OR_UNDECIDABLE_IN_GENERAL = "UNCOMPUTABLE_OR_UNDECIDABLE_IN_GENERAL"


class OperationalEdgeAssuranceClass(str, Enum):
    KERNEL_DERIVATION_EDGE = "KERNEL_DERIVATION_EDGE"
    REPLAY_VALIDATED_OPERATIONAL_EDGE = "REPLAY_VALIDATED_OPERATIONAL_EDGE"
    CANDIDATE_OPERATIONAL_EDGE = "CANDIDATE_OPERATIONAL_EDGE"


class ReplayVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class ReachabilityQuantifier(str, Enum):
    EXISTS_PATH = "EXISTS_PATH"
    POLICY_CONTROLLABLE = "POLICY_CONTROLLABLE"
    ROBUST_FOR_ALL_ADMISSIBLE_OUTCOMES = "ROBUST_FOR_ALL_ADMISSIBLE_OUTCOMES"
    ALMOST_SURE = "ALMOST_SURE"
    PROBABILITY_AT_LEAST = "PROBABILITY_AT_LEAST"
    EXPECTED_COST_BOUNDED = "EXPECTED_COST_BOUNDED"
    ADVERSARIAL_GAME = "ADVERSARIAL_GAME"


class NavigationAbstractionKind(str, Enum):
    EXACT_QUOTIENT = "EXACT_QUOTIENT"
    SOUND_OVERAPPROXIMATION = "SOUND_OVERAPPROXIMATION"
    EMPIRICAL_COMPRESSION = "EMPIRICAL_COMPRESSION"


@dataclass(frozen=True)
class OperationalStateIdentity:
    """Future-relevant state identity for a frozen VTG operational subject."""

    state_id: str
    specification_hash: str
    root_qoi: str
    environment_hash: str
    verifier_subject_hash: str
    local_context_hash: str
    goals_hash: str
    metavariable_state_hash: str
    options_hash: str
    operator_basis_version: str
    chart_id: str
    toolchain_hash: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.state_id,
                self.specification_hash,
                self.root_qoi,
                self.environment_hash,
                self.verifier_subject_hash,
                self.local_context_hash,
                self.goals_hash,
                self.metavariable_state_hash,
                self.options_hash,
                self.operator_basis_version,
                self.chart_id,
                self.toolchain_hash,
            )
        ):
            raise ValueError("operational state identity requires all future-relevant subject coordinates")

    @property
    def content_hash(self) -> str:
        return _hash(
            {
                "schema": "orion.vtg.operational-state.v1",
                "state_id": self.state_id,
                "specification_hash": self.specification_hash,
                "root_qoi": self.root_qoi,
                "environment_hash": self.environment_hash,
                "verifier_subject_hash": self.verifier_subject_hash,
                "local_context_hash": self.local_context_hash,
                "goals_hash": self.goals_hash,
                "metavariable_state_hash": self.metavariable_state_hash,
                "options_hash": self.options_hash,
                "operator_basis_version": self.operator_basis_version,
                "chart_id": self.chart_id,
                "toolchain_hash": self.toolchain_hash,
            }
        )

    def same_frozen_subject_as(self, other: "OperationalStateIdentity") -> bool:
        return (
            self.specification_hash == other.specification_hash
            and self.root_qoi == other.root_qoi
            and self.environment_hash == other.environment_hash
            and self.verifier_subject_hash == other.verifier_subject_hash
            and self.options_hash == other.options_hash
            and self.operator_basis_version == other.operator_basis_version
            and self.chart_id == other.chart_id
            and self.toolchain_hash == other.toolchain_hash
        )


@dataclass(frozen=True)
class OperationalReplayEvidence:
    replay_id: str
    edge_id: str
    source_state_hash: str
    target_state_hash: str
    action_hash: str
    replay_engine: str
    replay_engine_version: str
    result_artifact_hash: str
    verdict: ReplayVerdict

    def __post_init__(self) -> None:
        if not all(
            (
                self.replay_id,
                self.edge_id,
                self.source_state_hash,
                self.target_state_hash,
                self.action_hash,
                self.replay_engine,
                self.replay_engine_version,
                self.result_artifact_hash,
            )
        ):
            raise ValueError("operational replay evidence requires exact subject/action/artifact identity")

    @property
    def passed(self) -> bool:
        return self.verdict is ReplayVerdict.PASS


@dataclass(frozen=True)
class GeometryNontrivialityContract:
    contract_id: str
    geometry_id: str
    constructibility_class: GeometryConstructibilityClass
    construction_cost: float
    coordinate_bits_per_state: int
    global_auxiliary_storage_bytes: int
    local_distance_query_cost: float
    local_action_query_cost: float
    target_dependent: bool
    used_gold_route: bool
    used_gold_distance: bool
    expected_reuse_queries: float | None
    invalidation_hazard_per_query: float | None
    fresh_subject_hashes: Tuple[str, ...] = ()
    leakage_check_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.contract_id or not self.geometry_id:
            raise ValueError("geometry nontriviality contract requires identity")
        if min(
            self.construction_cost,
            self.coordinate_bits_per_state,
            self.global_auxiliary_storage_bytes,
            self.local_distance_query_cost,
            self.local_action_query_cost,
        ) < 0:
            raise ValueError("geometry construction/storage/query costs must be nonnegative")
        if self.expected_reuse_queries is not None and self.expected_reuse_queries < 0:
            raise ValueError("expected reuse must be nonnegative")
        if self.invalidation_hazard_per_query is not None and not 0.0 <= self.invalidation_hazard_per_query <= 1.0:
            raise ValueError("invalidation hazard must be in [0,1]")
        if len(set(self.fresh_subject_hashes)) != len(self.fresh_subject_hashes):
            raise ValueError("fresh subject hashes must be unique")
        if len(set(self.leakage_check_ids)) != len(self.leakage_check_ids):
            raise ValueError("leakage check ids must be unique")

    @property
    def is_oracle_contaminated(self) -> bool:
        return self.used_gold_route or self.used_gold_distance or self.constructibility_class is GeometryConstructibilityClass.ORACLE_EVALUATOR_ONLY

    @property
    def supports_fresh_nontriviality_claim(self) -> bool:
        return (
            not self.is_oracle_contaminated
            and bool(self.fresh_subject_hashes)
            and bool(self.leakage_check_ids)
            and self.constructibility_class
            not in {
                GeometryConstructibilityClass.ORACLE_EVALUATOR_ONLY,
                GeometryConstructibilityClass.UNKNOWN_COMPLEXITY,
                GeometryConstructibilityClass.UNCOMPUTABLE_OR_UNDECIDABLE_IN_GENERAL,
            }
        )

    def estimated_total_cost(self, *, queries: int) -> float:
        if queries < 1:
            raise ValueError("queries must be positive")
        return self.construction_cost + queries * (self.local_distance_query_cost + self.local_action_query_cost)

    def estimated_break_even_queries(self, *, baseline_per_query_cost: float) -> float:
        if baseline_per_query_cost < 0:
            raise ValueError("baseline cost must be nonnegative")
        local = self.local_distance_query_cost + self.local_action_query_cost
        advantage = baseline_per_query_cost - local
        if advantage <= 0:
            return inf
        return self.construction_cost / advantage

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class OperationalEdgeAssuranceReceipt:
    receipt_id: str
    edge_id: str
    assurance_class: OperationalEdgeAssuranceClass
    source_state: OperationalStateIdentity
    target_state: OperationalStateIdentity
    verifier_subject_hash: str
    derivation_statement_hash: str | None = None
    proof_receipt: ProofReceipt | None = None
    replay_evidence: OperationalReplayEvidence | None = None

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.edge_id or not self.verifier_subject_hash:
            raise ValueError("edge assurance requires receipt/edge/verifier identity")
        if self.source_state.state_id == self.target_state.state_id:
            raise ValueError("assurance-bound state transition requires distinct source and target state ids")
        if not self.source_state.same_frozen_subject_as(self.target_state):
            raise ValueError("edge assurance source/target states must share the frozen operational subject")
        if self.source_state.verifier_subject_hash != self.verifier_subject_hash:
            raise ValueError("edge assurance verifier subject does not match operational state subject")
        if self.assurance_class is OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE:
            if self.proof_receipt is None or not self.derivation_statement_hash:
                raise ValueError("kernel derivation edge requires bound proof receipt and derivation statement")
            if self.replay_evidence is not None:
                raise ValueError("kernel derivation edge cannot use replay evidence as its assurance basis")
            if self.proof_receipt.theorem_id != self.edge_id:
                raise ValueError("kernel derivation proof receipt theorem id must match edge id")
            if self.proof_receipt.theorem_statement_hash != self.derivation_statement_hash:
                raise ValueError("kernel derivation statement hash does not match proof receipt")
            report = audit_proof_receipt(self.proof_receipt, require_independent_recheck=False)
            if report.verdict is not AssuranceVerdict.PASS:
                raise ValueError("kernel derivation edge proof receipt did not pass proof audit")
        elif self.assurance_class is OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE:
            if self.replay_evidence is None:
                raise ValueError("replay-validated operational edge requires replay evidence object")
            if self.proof_receipt is not None or self.derivation_statement_hash is not None:
                raise ValueError("replay-validated operational edge cannot masquerade as local proof derivation")
            if self.replay_evidence.edge_id != self.edge_id:
                raise ValueError("replay evidence edge id does not match assurance receipt")
            if self.replay_evidence.source_state_hash != self.source_state.content_hash:
                raise ValueError("replay evidence source state does not match assurance receipt")
            if self.replay_evidence.target_state_hash != self.target_state.content_hash:
                raise ValueError("replay evidence target state does not match assurance receipt")
            if not self.replay_evidence.passed:
                raise ValueError("replay-validated operational edge requires passing replay evidence")
        else:
            if self.proof_receipt is not None or self.replay_evidence is not None:
                raise ValueError("candidate operational edge cannot carry verified assurance evidence")

    @property
    def supports_operational_reachability(self) -> bool:
        return self.assurance_class in {
            OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE,
            OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
        }

    @property
    def supports_local_logical_derivation_claim(self) -> bool:
        return self.assurance_class is OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE

    @property
    def grants_root_theorem_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ReachabilityClaimContract:
    claim_id: str
    subject_hash: str
    quantifier: ReachabilityQuantifier
    policy_id: str | None = None
    probability_lower_bound: float | None = None
    expected_cost_upper_bound: float | None = None
    adversary_model_id: str | None = None
    evidence_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim_id or not self.subject_hash:
            raise ValueError("reachability claim requires identity and subject")
        if self.probability_lower_bound is not None and not 0.0 <= self.probability_lower_bound <= 1.0:
            raise ValueError("probability lower bound must be in [0,1]")
        if self.expected_cost_upper_bound is not None and self.expected_cost_upper_bound < 0:
            raise ValueError("expected cost upper bound must be nonnegative")
        if self.quantifier in {
            ReachabilityQuantifier.POLICY_CONTROLLABLE,
            ReachabilityQuantifier.ROBUST_FOR_ALL_ADMISSIBLE_OUTCOMES,
            ReachabilityQuantifier.ALMOST_SURE,
            ReachabilityQuantifier.PROBABILITY_AT_LEAST,
            ReachabilityQuantifier.EXPECTED_COST_BOUNDED,
            ReachabilityQuantifier.ADVERSARIAL_GAME,
        } and not self.policy_id:
            raise ValueError("policy-level reachability claim requires policy_id")
        if self.quantifier is ReachabilityQuantifier.PROBABILITY_AT_LEAST and self.probability_lower_bound is None:
            raise ValueError("probability reachability claim requires lower bound")
        if self.quantifier is ReachabilityQuantifier.EXPECTED_COST_BOUNDED and self.expected_cost_upper_bound is None:
            raise ValueError("expected-cost reachability claim requires cost bound")
        if self.quantifier is ReachabilityQuantifier.ADVERSARIAL_GAME and not self.adversary_model_id:
            raise ValueError("adversarial reachability claim requires adversary model")

    @property
    def grants_solution_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class NavigationAbstractionReceipt:
    abstraction_id: str
    source_subject_hash: str
    abstract_subject_hash: str
    kind: NavigationAbstractionKind
    abstraction_map_id: str
    concretization_or_lifting_id: str | None
    transition_soundness_verifier_id: str | None
    target_preservation_verifier_id: str | None
    exact_two_way_verifier_id: str | None = None
    refinement_operator_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.abstraction_id, self.source_subject_hash, self.abstract_subject_hash, self.abstraction_map_id)):
            raise ValueError("navigation abstraction requires bound identities")
        if self.kind is NavigationAbstractionKind.EXACT_QUOTIENT:
            if not all(
                (
                    self.concretization_or_lifting_id,
                    self.transition_soundness_verifier_id,
                    self.target_preservation_verifier_id,
                    self.exact_two_way_verifier_id,
                )
            ):
                raise ValueError("exact navigation quotient requires two-way/lifting and preservation verification")
        elif self.kind is NavigationAbstractionKind.SOUND_OVERAPPROXIMATION:
            if not all(
                (
                    self.concretization_or_lifting_id,
                    self.transition_soundness_verifier_id,
                    self.target_preservation_verifier_id,
                    self.refinement_operator_id,
                )
            ):
                raise ValueError("overapproximation requires soundness, concretization, target, and refinement bindings")

    @property
    def abstract_route_requires_concrete_check(self) -> bool:
        return self.kind is not NavigationAbstractionKind.EXACT_QUOTIENT

    @property
    def abstract_no_route_can_mint_impossibility_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class CertifiedNavigationBasin:
    basin_id: str
    geometry_id: str
    subject_hash: str
    state_selector_id: str
    rank_or_value_id: str
    rank_well_foundedness_receipt_id: str
    progress_action_verifier_id: str
    minima_goal_verifier_id: str
    boundary_behavior_id: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.basin_id,
                self.geometry_id,
                self.subject_hash,
                self.state_selector_id,
                self.rank_or_value_id,
                self.rank_well_foundedness_receipt_id,
                self.progress_action_verifier_id,
                self.minima_goal_verifier_id,
                self.boundary_behavior_id,
            )
        ):
            raise ValueError("certified navigation basin requires all theorem-bound identities")

    @property
    def supports_scoped_termination_theorem(self) -> bool:
        return True

    @property
    def supports_global_navigation_claim(self) -> bool:
        return False


@dataclass(frozen=True)
class GeometryLearningReceipt:
    receipt_id: str
    geometry_id: str
    training_subject_hashes: Tuple[str, ...]
    behavior_policy_id: str
    sampling_process_id: str
    label_source_id: str
    coverage_coordinate_ids: Tuple[str, ...]
    unseen_operator_ids: Tuple[str, ...] = ()
    unseen_chart_ids: Tuple[str, ...] = ()
    leakage_check_ids: Tuple[str, ...] = ()
    fresh_test_subject_hashes: Tuple[str, ...] = ()
    structural_assumption_ids: Tuple[str, ...] = ()
    ood_detector_id: str | None = None
    staleness_detector_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.receipt_id, self.geometry_id, self.behavior_policy_id, self.sampling_process_id, self.label_source_id)):
            raise ValueError("geometry learning receipt requires bound identities")
        if not self.training_subject_hashes:
            raise ValueError("geometry learning receipt requires training subjects")
        if not self.coverage_coordinate_ids:
            raise ValueError("geometry learning receipt requires coverage coordinates")
        for values in (
            self.training_subject_hashes,
            self.coverage_coordinate_ids,
            self.unseen_operator_ids,
            self.unseen_chart_ids,
            self.leakage_check_ids,
            self.fresh_test_subject_hashes,
            self.structural_assumption_ids,
        ):
            if len(set(values)) != len(values):
                raise ValueError("geometry learning receipt identifiers must be unique within each coordinate")

    @property
    def has_known_support_gaps(self) -> bool:
        return bool(self.unseen_operator_ids or self.unseen_chart_ids)

    @property
    def supports_fresh_empirical_geometry_claim(self) -> bool:
        return bool(
            self.leakage_check_ids
            and self.fresh_test_subject_hashes
            and self.ood_detector_id
            and self.staleness_detector_id
        )

    @property
    def supports_exact_global_geometry_claim(self) -> bool:
        return False


@dataclass(frozen=True)
class GlobalAmalgamationReceipt:
    receipt_id: str
    root_subject_hash: str
    child_certificate_hashes: Tuple[str, ...]
    overlap_consistency_receipt_ids: Tuple[str, ...]
    assumption_discharge_receipt_ids: Tuple[str, ...]
    substitution_coherence_receipt_ids: Tuple[str, ...]
    parent_invariant_receipt_id: str
    final_verifier_receipt_id: str

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.root_subject_hash:
            raise ValueError("amalgamation receipt requires identity and root subject")
        if not self.child_certificate_hashes:
            raise ValueError("amalgamation requires child certificates")
        if not all(
            (
                self.overlap_consistency_receipt_ids,
                self.assumption_discharge_receipt_ids,
                self.parent_invariant_receipt_id,
                self.final_verifier_receipt_id,
            )
        ):
            raise ValueError("amalgamation requires overlap, assumption, parent invariant and final verifier receipts")
        for values in (
            self.child_certificate_hashes,
            self.overlap_consistency_receipt_ids,
            self.assumption_discharge_receipt_ids,
            self.substitution_coherence_receipt_ids,
        ):
            if len(set(values)) != len(values):
                raise ValueError("amalgamation receipt identifiers must be unique within each coordinate")

    @property
    def ready_for_solution_assembly(self) -> bool:
        return True

    @property
    def grants_root_authority(self) -> bool:
        return False
