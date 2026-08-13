from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from math import inf


class GeometryCertificationClass(str, Enum):
    EXACT_COST_TO_GO = "EXACT_COST_TO_GO"
    VERIFIED_ROUTE_UPPER_BOUND = "VERIFIED_ROUTE_UPPER_BOUND"
    ADMISSIBLE_LOWER_BOUND = "ADMISSIBLE_LOWER_BOUND"
    CONSISTENT_HEURISTIC = "CONSISTENT_HEURISTIC"
    EMPIRICAL_RANKER = "EMPIRICAL_RANKER"
    UNCERTIFIED = "UNCERTIFIED"


def geometry_certification_subject_hash(
    *,
    geometry_id: str,
    specification_hash: str,
    root_qoi: str,
    operator_basis_version: str,
    map_revision_hash: str,
    chart_id: str,
    verifier_subject_hash: str,
    cost_algebra_id: str,
    construction_version: str,
) -> str:
    """Canonical hash of the geometry subject a certification witness binds.

    The certification class is a theorem about the function named by exactly
    these coordinates (audit I5); the class itself is what is being certified,
    so it is not part of the subject.
    """
    payload = {
        "schema": "orion.fieldability.certification_subject.v1",
        "geometry_id": geometry_id,
        "specification_hash": specification_hash,
        "root_qoi": root_qoi,
        "operator_basis_version": operator_basis_version,
        "map_revision_hash": map_revision_hash,
        "chart_id": chart_id,
        "verifier_subject_hash": verifier_subject_hash,
        "cost_algebra_id": cost_algebra_id,
        "construction_version": construction_version,
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CertificationWitness:
    """Verifier-bound witness for a geometry certification class (audit I5).

    ``EXACT_COST_TO_GO`` / ``ADMISSIBLE_LOWER_BOUND`` / ``CONSISTENT_HEURISTIC``
    are theorems about a function relative to a cost algebra and map revision.
    Without a witness naming the checker and the exact subject it checked, a
    ``certification_class`` is a self-declaration and licenses nothing
    (the same closure pattern as the coverage-completeness certificate, U4).
    """

    witness_id: str
    verifier_id: str
    subject_hash: str
    certified_class: GeometryCertificationClass

    def __post_init__(self) -> None:
        if not all((self.witness_id, self.verifier_id, self.subject_hash)):
            raise ValueError("certification witness requires witness/verifier/subject identities")
        if self.certified_class is GeometryCertificationClass.UNCERTIFIED:
            raise ValueError("a certification witness for UNCERTIFIED is meaningless; omit the witness instead")

    @property
    def grants_target_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class GeometryArtifactIdentity:
    """Version binding for a routing geometry.

    Budget is intentionally not part of intrinsic geometry identity. Budget
    belongs to feasible reachability/control. Geometry is instead bound to the
    subject, operator basis, map revision, representation, verifier semantics,
    cost algebra, and construction version from which its path values are defined.

    ``certification_class`` records the DECLARED strongest geometry property.
    Claim-bearing properties (``supports_exact_cost_claim``,
    ``is_theorem_certified_heuristic_class``) read the WITNESSED class
    (audit I5): without a ``certification_witness`` bound to this identity's
    subject hash the effective class is UNCERTIFIED, and the properties fail
    closed. It does not itself prove an A*/optimality theorem; downstream
    algorithms must still satisfy their own assumptions.
    """

    geometry_id: str
    specification_hash: str
    root_qoi: str
    operator_basis_version: str
    map_revision_hash: str
    chart_id: str
    verifier_subject_hash: str
    cost_algebra_id: str
    construction_version: str
    certification_class: GeometryCertificationClass = GeometryCertificationClass.UNCERTIFIED
    certification_witness: CertificationWitness | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.geometry_id,
                self.specification_hash,
                self.root_qoi,
                self.operator_basis_version,
                self.map_revision_hash,
                self.chart_id,
                self.verifier_subject_hash,
                self.cost_algebra_id,
                self.construction_version,
            )
        ):
            raise ValueError("geometry artifact identity fields are required")
        if self.certification_witness is not None:
            if self.certification_witness.subject_hash != self.certification_subject_hash:
                raise ValueError(
                    "certification witness subject_hash does not match this geometry's "
                    "certification subject hash (audit I5)"
                )
            if self.certification_witness.certified_class is not self.certification_class:
                raise ValueError(
                    "certification witness certifies a different class than the declared "
                    "certification_class (audit I5)"
                )

    @property
    def certification_subject_hash(self) -> str:
        return geometry_certification_subject_hash(
            geometry_id=self.geometry_id,
            specification_hash=self.specification_hash,
            root_qoi=self.root_qoi,
            operator_basis_version=self.operator_basis_version,
            map_revision_hash=self.map_revision_hash,
            chart_id=self.chart_id,
            verifier_subject_hash=self.verifier_subject_hash,
            cost_algebra_id=self.cost_algebra_id,
            construction_version=self.construction_version,
        )

    @property
    def witnessed_certification_class(self) -> GeometryCertificationClass:
        """Effective class: the declared class only when a bound witness backs it."""
        if self.certification_witness is None:
            return GeometryCertificationClass.UNCERTIFIED
        return self.certification_class

    @property
    def supports_exact_cost_claim(self) -> bool:
        return self.witnessed_certification_class is GeometryCertificationClass.EXACT_COST_TO_GO

    @property
    def is_theorem_certified_heuristic_class(self) -> bool:
        return self.witnessed_certification_class in {
            GeometryCertificationClass.EXACT_COST_TO_GO,
            GeometryCertificationClass.ADMISSIBLE_LOWER_BOUND,
            GeometryCertificationClass.CONSISTENT_HEURISTIC,
        }

    def matches(
        self,
        *,
        specification_hash: str,
        root_qoi: str,
        operator_basis_version: str,
        map_revision_hash: str,
        chart_id: str,
        verifier_subject_hash: str,
        cost_algebra_id: str,
        construction_version: str,
    ) -> bool:
        return (
            self.specification_hash == specification_hash
            and self.root_qoi == root_qoi
            and self.operator_basis_version == operator_basis_version
            and self.map_revision_hash == map_revision_hash
            and self.chart_id == chart_id
            and self.verifier_subject_hash == verifier_subject_hash
            and self.cost_algebra_id == cost_algebra_id
            and self.construction_version == construction_version
        )


@dataclass(frozen=True)
class FieldabilityProfile:
    identity: GeometryArtifactIdentity
    build_cost: float
    baseline_per_query_cost: float | None = None
    extraction_per_query_cost: float | None = None
    invalidation_hazard_per_query: float | None = None
    local_alignment: float | None = None
    greedy_success: float | None = None
    bounded_branch_success: float | None = None
    route_stretch: float | None = None
    false_descent_rate: float | None = None
    ood_failure_rate: float | None = None
    verifier_calls_per_query: float | None = None

    def __post_init__(self) -> None:
        nonnegative = (self.build_cost, self.baseline_per_query_cost, self.extraction_per_query_cost, self.invalidation_hazard_per_query, self.route_stretch, self.verifier_calls_per_query)
        if any(value is not None and value < 0 for value in nonnegative):
            raise ValueError("fieldability cost/rate magnitudes must be nonnegative")
        probabilities = (self.invalidation_hazard_per_query, self.local_alignment, self.greedy_success, self.bounded_branch_success, self.false_descent_rate, self.ood_failure_rate)
        if any(value is not None and not 0.0 <= value <= 1.0 for value in probabilities):
            raise ValueError("fieldability probability coordinates must be in [0,1]")

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def amortization_break_even_queries(
    *,
    build_cost: float,
    extraction_per_query_cost: float,
    baseline_per_query_cost: float,
    invalidation_hazard_per_query: float = 0.0,
) -> float:
    """Renewal-reward break-even under the module's Bernoulli rebuild model (audit U6).

    The long-run per-query advantage of the field is
    ``baseline - extraction - hazard * build`` (the hazard term prices expected
    rebuilds, matching ``stability_adjusted_per_query_cost``); the field pays
    off only when that advantage is positive, in which case break-even is
    ``build / advantage``. ``invalidation_hazard_per_query=0`` recovers the
    hazard-free special case. Assumes stationary, commensurable scalar costs;
    this is a registered development proxy, not the VTG path-cost algebra.
    """
    if min(build_cost, extraction_per_query_cost, baseline_per_query_cost) < 0:
        raise ValueError("costs must be nonnegative")
    if not 0.0 <= invalidation_hazard_per_query <= 1.0:
        raise ValueError("invalidation hazard must be in [0,1]")
    advantage = baseline_per_query_cost - extraction_per_query_cost - invalidation_hazard_per_query * build_cost
    if advantage <= 0:
        return inf
    return build_cost / advantage


def stability_adjusted_per_query_cost(*, build_cost: float, extraction_per_query_cost: float, invalidation_hazard_per_query: float) -> float:
    """Bernoulli rebuild model used only as a registered development proxy."""
    if build_cost < 0 or extraction_per_query_cost < 0:
        raise ValueError("costs must be nonnegative")
    if not 0.0 <= invalidation_hazard_per_query <= 1.0:
        raise ValueError("invalidation hazard must be in [0,1]")
    return extraction_per_query_cost + invalidation_hazard_per_query * build_cost


def profile_supports_routing_claim(
    profile: FieldabilityProfile,
    *,
    min_bounded_branch_success: float,
    max_false_descent_rate: float,
    max_ood_failure_rate: float | None = None,
    max_route_stretch: float | None = None,
) -> bool:
    """Development-level routing screen, never authority or optimality proof."""
    if not 0 <= min_bounded_branch_success <= 1 or not 0 <= max_false_descent_rate <= 1:
        raise ValueError("thresholds must be in [0,1]")
    if max_ood_failure_rate is not None and not 0 <= max_ood_failure_rate <= 1:
        raise ValueError("max_ood_failure_rate must be in [0,1]")
    if max_route_stretch is not None and max_route_stretch < 0:
        raise ValueError("max_route_stretch must be nonnegative")
    if profile.bounded_branch_success is None or profile.false_descent_rate is None:
        return False
    if profile.bounded_branch_success < min_bounded_branch_success or profile.false_descent_rate > max_false_descent_rate:
        return False
    if max_ood_failure_rate is not None and (profile.ood_failure_rate is None or profile.ood_failure_rate > max_ood_failure_rate):
        return False
    if max_route_stretch is not None and (profile.route_stretch is None or profile.route_stretch > max_route_stretch):
        return False
    return True
