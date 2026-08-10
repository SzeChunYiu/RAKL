from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re
from typing import Iterable, Optional


class OWMDRouteKind(str, Enum):
    EXACT_TERMINOLOGY = "EXACT_TERMINOLOGY"
    LEXICAL_VARIANTS = "LEXICAL_VARIANTS"
    FUNCTION_ONLY = "FUNCTION_ONLY"
    HISTORICAL_PRECURSOR = "HISTORICAL_PRECURSOR"
    MATHEMATICAL_EQUIVALENT = "MATHEMATICAL_EQUIVALENT"
    IMPLEMENTATION_ANALOG = "IMPLEMENTATION_ANALOG"
    METHODOLOGICAL_INSPIRATION = "METHODOLOGICAL_INSPIRATION"
    CITATION_NEIGHBORHOOD = "CITATION_NEIGHBORHOOD"
    LITERATURE_BRIDGE = "LITERATURE_BRIDGE"
    ADVERSARIAL_ALTERNATIVE = "ADVERSARIAL_ALTERNATIVE"
    CROSS_LANGUAGE = "CROSS_LANGUAGE"
    FRESHNESS = "FRESHNESS"


DEFAULT_OWMD_ROUTES = frozenset(
    kind for kind in OWMDRouteKind if kind is not OWMDRouteKind.CROSS_LANGUAGE
)


@dataclass(frozen=True)
class FunctionalSignature:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    constraints: tuple[str, ...]
    relations: tuple[str, ...]
    dynamics: tuple[str, ...]
    failure_signatures: tuple[str, ...]

    def __post_init__(self) -> None:
        groups = (
            self.inputs,
            self.outputs,
            self.constraints,
            self.relations,
            self.dynamics,
            self.failure_signatures,
        )
        if any(any(not item.strip() for item in group) for group in groups):
            raise ValueError("functional-signature fields cannot contain empty values")
        if not any(groups):
            raise ValueError("functional signature must expose at least one observable coordinate")


@dataclass(frozen=True)
class CapabilityRequirement:
    function_id: str
    subsystem: str
    description: str
    impact: str
    signature: FunctionalSignature
    core_vocabulary: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.function_id or not self.subsystem or not self.description.strip():
            raise ValueError("capability identity, subsystem and description are required")
        if not self.impact.strip():
            raise ValueError("capability impact is required")


@dataclass(frozen=True)
class CapabilityOwnerRecord:
    function_id: str
    mechanism_id: str
    scope: str
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    failure_semantics: tuple[str, ...]

    def __post_init__(self) -> None:
        required_text = (self.function_id, self.mechanism_id, self.scope)
        if any(not item.strip() for item in required_text):
            raise ValueError("owner identity, mechanism and scope are required")
        required_groups = (
            self.preconditions,
            self.postconditions,
            self.evidence_ids,
            self.test_ids,
            self.failure_semantics,
        )
        if any(not group for group in required_groups):
            raise ValueError(
                "a capability owner must record preconditions, postconditions, evidence, tests and failure semantics"
            )
        if any(any(not item.strip() for item in group) for group in required_groups):
            raise ValueError("capability-owner fields cannot contain empty values")


class AssimilationStatus(str, Enum):
    EQUIVALENT = "EQUIVALENT"
    SUBSUMED = "SUBSUMED"
    COMPLEMENTARY = "COMPLEMENTARY"
    CONFLICTING = "CONFLICTING"
    NOVEL_RESIDUAL = "NOVEL_RESIDUAL"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class MechanismCandidate:
    candidate_id: str
    mechanism_class: str
    source_ids: tuple[str, ...]
    route_ids: tuple[str, ...]
    functional_fit: float
    structural_fit: float
    evidence_quality: float
    novelty_threat: float
    transfer_cost: float
    assimilation: AssimilationStatus
    contradiction_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.mechanism_class:
            raise ValueError("candidate identity and mechanism class are required")
        if not self.source_ids or not self.route_ids:
            raise ValueError("candidate must retain source and discovery-route provenance")
        for value in (
            self.functional_fit,
            self.structural_fit,
            self.evidence_quality,
            self.novelty_threat,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("candidate fit/quality/threat coordinates must be in [0, 1]")
        if self.transfer_cost < 0:
            raise ValueError("transfer_cost cannot be negative")


@dataclass(frozen=True)
class DiscoveryRouteRecord:
    route_id: str
    kind: OWMDRouteKind
    query: str
    completed: bool
    candidate_ids: tuple[str, ...] = ()
    lexically_independent: bool = False
    stable: bool = True
    searched_through: Optional[str] = None
    inapplicable_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.route_id or not self.query.strip():
            raise ValueError("route identity and query are required")
        if not self.completed and not self.inapplicable_reason:
            return
        if self.kind is OWMDRouteKind.FRESHNESS and self.completed:
            if self.searched_through is None:
                raise ValueError("completed freshness route requires searched_through")
            date.fromisoformat(self.searched_through)


class DiscoveryClosureStatus(str, Enum):
    OPEN = "OPEN"
    BOUNDED_CLOSED = "BOUNDED_CLOSED"


@dataclass(frozen=True)
class DiscoveryClosureReport:
    status: DiscoveryClosureStatus
    function_id: str
    owner_mechanism_id: Optional[str]
    explicit_open_fiber: Optional[str]
    missing_route_kinds: tuple[str, ...]
    lexical_independence_passed: bool
    citation_neighborhood_stable: bool
    freshness_cutoff: Optional[str]
    unresolved_candidate_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def absolute_complete(self) -> bool:
        return False


_TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]*")


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.lower()))


def _lexically_independent(
    routes: Iterable[DiscoveryRouteRecord],
    core_vocabulary: Iterable[str],
) -> bool:
    core: set[str] = set()
    for term in core_vocabulary:
        core.update(_tokens(term))
    for route in routes:
        if not route.completed or not route.lexically_independent:
            continue
        if not core.intersection(_tokens(route.query)):
            return True
    return False


def audit_bounded_discovery_closure(
    requirement: CapabilityRequirement,
    routes: Iterable[DiscoveryRouteRecord],
    *,
    owner: Optional[CapabilityOwnerRecord] = None,
    explicit_open_fiber: Optional[str] = None,
    candidates: Iterable[MechanismCandidate] = (),
    independent_omission_review: bool,
    nearest_work_equivalence_audit: bool,
    unresolved_preserved: bool,
    cross_language_applicable: bool = False,
) -> DiscoveryClosureReport:
    observed = tuple(routes)
    by_kind: dict[OWMDRouteKind, list[DiscoveryRouteRecord]] = {}
    for route in observed:
        by_kind.setdefault(route.kind, []).append(route)

    required = set(DEFAULT_OWMD_ROUTES)
    if cross_language_applicable:
        required.add(OWMDRouteKind.CROSS_LANGUAGE)

    missing = tuple(
        sorted(
            kind.value
            for kind in required
            if not any(route.completed or route.inapplicable_reason for route in by_kind.get(kind, ()))
        )
    )
    lexical_ok = _lexically_independent(observed, requirement.core_vocabulary)

    citation_records = by_kind.get(OWMDRouteKind.CITATION_NEIGHBORHOOD, ())
    citation_stable = bool(citation_records) and all(
        (not record.completed) or record.stable for record in citation_records
    )

    freshness_records = [
        route for route in by_kind.get(OWMDRouteKind.FRESHNESS, ()) if route.completed
    ]
    freshness_cutoff = max(
        (route.searched_through for route in freshness_records if route.searched_through),
        default=None,
    )

    candidate_tuple = tuple(candidates)
    unresolved = tuple(
        sorted(
            candidate.candidate_id
            for candidate in candidate_tuple
            if candidate.assimilation is AssimilationStatus.UNRESOLVED
        )
    )

    owner_ok = owner is not None and owner.function_id == requirement.function_id
    open_fiber_ok = bool(explicit_open_fiber and explicit_open_fiber.strip())
    reasons: list[str] = []

    if owner is not None and owner.function_id != requirement.function_id:
        reasons.append("owner_function_mismatch")
    if not (owner_ok or open_fiber_ok):
        reasons.append("function_has_neither_owner_nor_explicit_open_fiber")
    if missing:
        reasons.append("mandatory_expansion_routes_incomplete")
    if not lexical_ok:
        reasons.append("lexical_independence_test_not_satisfied")
    if not citation_stable:
        reasons.append("citation_neighborhood_not_stable")
    if freshness_cutoff is None:
        reasons.append("freshness_scan_missing")
    if not independent_omission_review:
        reasons.append("independent_omission_review_missing")
    if not nearest_work_equivalence_audit:
        reasons.append("nearest_work_equivalence_audit_missing")
    if unresolved and not unresolved_preserved:
        reasons.append("unresolved_candidates_not_preserved_as_fibers")

    status = DiscoveryClosureStatus.BOUNDED_CLOSED if not reasons else DiscoveryClosureStatus.OPEN
    return DiscoveryClosureReport(
        status=status,
        function_id=requirement.function_id,
        owner_mechanism_id=owner.mechanism_id if owner_ok and owner else None,
        explicit_open_fiber=explicit_open_fiber if open_fiber_ok else None,
        missing_route_kinds=missing,
        lexical_independence_passed=lexical_ok,
        citation_neighborhood_stable=citation_stable,
        freshness_cutoff=freshness_cutoff,
        unresolved_candidate_ids=unresolved,
        reasons=tuple(reasons),
    )


class DiscoveryWorkspacePartition(str, Enum):
    NEAR = "NEAR"
    REMOTE = "REMOTE"
    CHALLENGE = "CHALLENGE"
    HISTORICAL = "HISTORICAL"
    FRESH = "FRESH"


@dataclass(frozen=True)
class DiscoveryWorkspaceCandidate:
    candidate_id: str
    partition: DiscoveryWorkspacePartition
    priority: float

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id cannot be empty")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")


@dataclass(frozen=True)
class DiscoveryWorkspaceFrame:
    selected_candidate_ids: tuple[str, ...]
    partition_counts: tuple[tuple[str, int], ...]
    capacity: int


def select_discovery_workspace(
    candidates: Iterable[DiscoveryWorkspaceCandidate],
    *,
    capacity: int,
    reserved_partitions: tuple[DiscoveryWorkspacePartition, ...] = (
        DiscoveryWorkspacePartition.REMOTE,
        DiscoveryWorkspacePartition.CHALLENGE,
        DiscoveryWorkspacePartition.HISTORICAL,
        DiscoveryWorkspacePartition.FRESH,
    ),
) -> DiscoveryWorkspaceFrame:
    if capacity < 1:
        raise ValueError("capacity must be positive")
    if len(set(reserved_partitions)) != len(reserved_partitions):
        raise ValueError("reserved partitions cannot contain duplicates")
    if len(reserved_partitions) > capacity:
        raise ValueError("capacity smaller than mandatory discovery reservations")

    pool = tuple(candidates)
    if len({item.candidate_id for item in pool}) != len(pool):
        raise ValueError("duplicate discovery candidate_id")

    selected: list[DiscoveryWorkspaceCandidate] = []
    selected_ids: set[str] = set()
    for partition in reserved_partitions:
        options = sorted(
            (item for item in pool if item.partition is partition),
            key=lambda item: (-item.priority, item.candidate_id),
        )
        if not options:
            raise ValueError(f"reserved discovery partition has no candidate: {partition.value}")
        chosen = options[0]
        selected.append(chosen)
        selected_ids.add(chosen.candidate_id)

    remaining = sorted(
        (item for item in pool if item.candidate_id not in selected_ids),
        key=lambda item: (-item.priority, item.candidate_id),
    )
    for item in remaining:
        if len(selected) >= capacity:
            break
        selected.append(item)
        selected_ids.add(item.candidate_id)

    counts: dict[str, int] = {}
    for item in selected:
        counts[item.partition.value] = counts.get(item.partition.value, 0) + 1
    return DiscoveryWorkspaceFrame(
        selected_candidate_ids=tuple(item.candidate_id for item in selected),
        partition_counts=tuple(sorted(counts.items())),
        capacity=capacity,
    )


@dataclass(frozen=True)
class HiddenNameBenchmark:
    benchmark_id: str
    withheld_terms: tuple[str, ...]
    required_mechanism_classes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.benchmark_id:
            raise ValueError("benchmark_id cannot be empty")
        if not self.withheld_terms or not self.required_mechanism_classes:
            raise ValueError("hidden-name benchmark requires withheld terms and mechanism classes")


@dataclass(frozen=True)
class HiddenNameBenchmarkReport:
    passed: bool
    missing_mechanism_classes: tuple[str, ...]
    leaked_route_ids: tuple[str, ...]
    reasons: tuple[str, ...]


def evaluate_hidden_name_benchmark(
    benchmark: HiddenNameBenchmark,
    routes: Iterable[DiscoveryRouteRecord],
    candidates: Iterable[MechanismCandidate],
) -> HiddenNameBenchmarkReport:
    route_tuple = tuple(routes)
    candidate_tuple = tuple(candidates)
    withheld_tokens: set[str] = set()
    for term in benchmark.withheld_terms:
        withheld_tokens.update(_tokens(term))

    independent_route_ids = {
        route.route_id
        for route in route_tuple
        if route.completed
        and route.lexically_independent
        and not withheld_tokens.intersection(_tokens(route.query))
    }
    leaked = tuple(
        sorted(
            route.route_id
            for route in route_tuple
            if route.lexically_independent
            and withheld_tokens.intersection(_tokens(route.query))
        )
    )

    found_classes = {
        candidate.mechanism_class
        for candidate in candidate_tuple
        if independent_route_ids.intersection(candidate.route_ids)
    }
    missing = tuple(sorted(set(benchmark.required_mechanism_classes) - found_classes))
    reasons: list[str] = []
    if leaked:
        reasons.append("withheld_name_leaked_into_ontology_independent_route")
    if missing:
        reasons.append("required_mechanism_family_not_retrieved_independently")
    return HiddenNameBenchmarkReport(
        passed=not reasons,
        missing_mechanism_classes=missing,
        leaked_route_ids=leaked,
        reasons=tuple(reasons),
    )
