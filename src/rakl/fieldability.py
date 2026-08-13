from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class GeometryArtifactIdentity:
    geometry_id: str
    specification_hash: str
    operator_basis_version: str
    map_revision_hash: str
    chart_id: str

    def __post_init__(self) -> None:
        if not all((self.geometry_id, self.specification_hash, self.operator_basis_version, self.map_revision_hash, self.chart_id)):
            raise ValueError("geometry artifact identity fields are required")

    def matches(self, *, specification_hash: str, operator_basis_version: str, map_revision_hash: str, chart_id: str) -> bool:
        return self.specification_hash == specification_hash and self.operator_basis_version == operator_basis_version and self.map_revision_hash == map_revision_hash and self.chart_id == chart_id


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


def amortization_break_even_queries(*, build_cost: float, extraction_per_query_cost: float, baseline_per_query_cost: float) -> float:
    if min(build_cost, extraction_per_query_cost, baseline_per_query_cost) < 0:
        raise ValueError("costs must be nonnegative")
    advantage = baseline_per_query_cost - extraction_per_query_cost
    if advantage <= 0:
        return inf
    return build_cost / advantage


def stability_adjusted_per_query_cost(*, build_cost: float, extraction_per_query_cost: float, invalidation_hazard_per_query: float) -> float:
    if build_cost < 0 or extraction_per_query_cost < 0:
        raise ValueError("costs must be nonnegative")
    if not 0.0 <= invalidation_hazard_per_query <= 1.0:
        raise ValueError("invalidation hazard must be in [0,1]")
    return extraction_per_query_cost + invalidation_hazard_per_query * build_cost


def profile_supports_routing_claim(profile: FieldabilityProfile, *, min_bounded_branch_success: float, max_false_descent_rate: float) -> bool:
    if not 0 <= min_bounded_branch_success <= 1 or not 0 <= max_false_descent_rate <= 1:
        raise ValueError("thresholds must be in [0,1]")
    return profile.bounded_branch_success is not None and profile.false_descent_rate is not None and profile.bounded_branch_success >= min_bounded_branch_success and profile.false_descent_rate <= max_false_descent_rate
