from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class DiscoveryRouteKind(str, Enum):
    IN_DOMAIN = "IN_DOMAIN"
    FUNCTION_FIRST = "FUNCTION_FIRST"
    ADJACENT_DISCIPLINE = "ADJACENT_DISCIPLINE"
    INTERACTION_ANALOG = "INTERACTION_ANALOG"
    ADVERSARIAL_PRIOR_ART = "ADVERSARIAL_PRIOR_ART"


DEFAULT_EXTERNAL_DISCOVERY_ROUTES = frozenset(
    {
        DiscoveryRouteKind.IN_DOMAIN,
        DiscoveryRouteKind.FUNCTION_FIRST,
        DiscoveryRouteKind.ADJACENT_DISCIPLINE,
        DiscoveryRouteKind.INTERACTION_ANALOG,
        DiscoveryRouteKind.ADVERSARIAL_PRIOR_ART,
    }
)


@dataclass(frozen=True)
class DiscoveryRouteObservation:
    route_id: str
    kind: DiscoveryRouteKind
    query_intent: str
    candidate_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.route_id or not self.query_intent.strip():
            raise ValueError("route identity and query intent are required")
        if any(not candidate for candidate in self.candidate_ids):
            raise ValueError("candidate ids cannot contain empty values")


@dataclass(frozen=True)
class ExogenousCandidate:
    candidate_id: str
    source_family: str
    facets: frozenset[str]

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.source_family:
            raise ValueError("candidate identity and source family are required")
        if not self.facets:
            raise ValueError("candidate must expose at least one normalized facet")

    @classmethod
    def from_facets(
        cls,
        candidate_id: str,
        source_family: str,
        facets: Iterable[str],
    ) -> "ExogenousCandidate":
        normalized = frozenset(item.strip().lower() for item in facets if item.strip())
        return cls(candidate_id, source_family, normalized)


class DiscoveryCoverageVerdict(str, Enum):
    COVERAGE_COMPLETE_CANDIDATE_SEEN = "COVERAGE_COMPLETE_CANDIDATE_SEEN"
    COVERAGE_COMPLETE_CANDIDATE_NOT_RELEVANT = "COVERAGE_COMPLETE_CANDIDATE_NOT_RELEVANT"
    EXOGENOUS_CONCEPT_MISS = "EXOGENOUS_CONCEPT_MISS"
    ROUTE_COVERAGE_INCOMPLETE = "ROUTE_COVERAGE_INCOMPLETE"


@dataclass(frozen=True)
class DiscoveryCoverageReport:
    verdict: DiscoveryCoverageVerdict
    covered_route_kinds: tuple[str, ...]
    missing_route_kinds: tuple[str, ...]
    overlapping_facets: tuple[str, ...]
    candidate_seen: bool
    reasons: tuple[str, ...]

    @property
    def permits_external_discovery_saturation(self) -> bool:
        return self.verdict in {
            DiscoveryCoverageVerdict.COVERAGE_COMPLETE_CANDIDATE_SEEN,
            DiscoveryCoverageVerdict.COVERAGE_COMPLETE_CANDIDATE_NOT_RELEVANT,
        }


def audit_exogenous_candidate(
    target_facets: Iterable[str],
    routes: Iterable[DiscoveryRouteObservation],
    candidate: ExogenousCandidate,
    *,
    required_route_kinds: frozenset[DiscoveryRouteKind] = DEFAULT_EXTERNAL_DISCOVERY_ROUTES,
) -> DiscoveryCoverageReport:
    normalized_target = frozenset(item.strip().lower() for item in target_facets if item.strip())
    observed = tuple(routes)
    covered = frozenset(route.kind for route in observed)
    missing = required_route_kinds - covered
    seen_ids = {candidate_id for route in observed for candidate_id in route.candidate_ids}
    candidate_seen = candidate.candidate_id in seen_ids
    overlap = tuple(sorted(normalized_target & candidate.facets))

    if missing:
        return DiscoveryCoverageReport(
            DiscoveryCoverageVerdict.ROUTE_COVERAGE_INCOMPLETE,
            tuple(sorted(kind.value for kind in covered)),
            tuple(sorted(kind.value for kind in missing)),
            overlap,
            candidate_seen,
            (
                "external discovery cannot claim scoped saturation while required route classes are unsearched",
                "function-first and adjacent-domain routes prevent the current ontology from defining its own search boundary",
            ),
        )

    if overlap and not candidate_seen:
        return DiscoveryCoverageReport(
            DiscoveryCoverageVerdict.EXOGENOUS_CONCEPT_MISS,
            tuple(sorted(kind.value for kind in covered)),
            (),
            overlap,
            False,
            (
                "a later exogenous candidate overlaps registered target functions but was absent from all completed routes",
                "record this as a search-coverage false negative and reopen external-framework discovery",
            ),
        )

    if candidate_seen:
        verdict = DiscoveryCoverageVerdict.COVERAGE_COMPLETE_CANDIDATE_SEEN
        reasons = ("candidate was surfaced by the registered route ensemble",)
    else:
        verdict = DiscoveryCoverageVerdict.COVERAGE_COMPLETE_CANDIDATE_NOT_RELEVANT
        reasons = ("candidate was not surfaced but exposes no normalized target-function overlap",)

    return DiscoveryCoverageReport(
        verdict,
        tuple(sorted(kind.value for kind in covered)),
        (),
        overlap,
        candidate_seen,
        reasons,
    )


def function_first_query_intents(target_facets: Iterable[str]) -> tuple[str, ...]:
    """Create domain-agnostic search intents from capabilities, not framework names."""

    facets = tuple(dict.fromkeys(item.strip().lower() for item in target_facets if item.strip()))
    if not facets:
        raise ValueError("at least one target facet is required")
    joined = ", ".join(facets)
    return (
        f"systems that implement these functions regardless of domain: {joined}",
        f"human or software workflows with analogous interaction mechanics: {joined}",
        f"adjacent disciplines that solve the same information-organization problem: {joined}",
        f"prior art that would narrow novelty if it already provides: {joined}",
    )
