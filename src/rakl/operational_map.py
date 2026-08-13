from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Tuple


def _hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class MapEdgeStatus(str, Enum):
    VERIFIED_APPLICABLE = "VERIFIED_APPLICABLE"
    VERIFIED_TRANSITION = "VERIFIED_TRANSITION"
    CANDIDATE_UNVERIFIED = "CANDIDATE_UNVERIFIED"
    BLOCKED_PRECONDITION = "BLOCKED_PRECONDITION"
    REFUTED_IN_SCOPE = "REFUTED_IN_SCOPE"
    FAILED_ATTEMPT_NOT_REFUTED = "FAILED_ATTEMPT_NOT_REFUTED"
    REPRESENTATION_DEPENDENT = "REPRESENTATION_DEPENDENT"
    STALE_NEEDS_RECHECK = "STALE_NEEDS_RECHECK"
    UNKNOWN = "UNKNOWN"


# Applicability is not the same statement as a verified state transition. Only
# materialized/replay-verified transitions may witness operational reachability.
VERIFIED_TRAVERSABLE = frozenset({MapEdgeStatus.VERIFIED_TRANSITION})


class MapReachabilityVerdict(str, Enum):
    VERIFIED_ROUTE_FOUND = "VERIFIED_ROUTE_FOUND"
    NO_VERIFIED_ROUTE_MAP_INCOMPLETE = "NO_VERIFIED_ROUTE_MAP_INCOMPLETE"
    NO_VERIFIED_ROUTE_COVERAGE_COMPLETE = "NO_VERIFIED_ROUTE_COVERAGE_COMPLETE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CoverageCompletenessCertificate:
    """Certificate that a registered operational map is closed in scope.

    This is deliberately weaker than a proof of mathematical impossibility or
    theorem unprovability. It only binds an enumerated map to a frozen
    problem/operator/chart subject and an external closure checker.
    """

    certificate_id: str
    problem_state_hash: str
    operator_basis_version: str
    chart_id: str
    closure_subject_hash: str
    closure_verifier_id: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.certificate_id,
                self.problem_state_hash,
                self.operator_basis_version,
                self.chart_id,
                self.closure_subject_hash,
                self.closure_verifier_id,
            )
        ):
            raise ValueError("coverage completeness certificate requires bound subject and verifier identities")

    def matches(self, *, problem_state_hash: str, operator_basis_version: str, chart_id: str) -> bool:
        return (
            self.problem_state_hash == problem_state_hash
            and self.operator_basis_version == operator_basis_version
            and self.chart_id == chart_id
        )

    @property
    def grants_mathematical_impossibility_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class OperationalEdge:
    """One statused transition instance.

    ``operator_id`` names the transformation coordinate of the paper's
    Sigma_Theta(x, T, y) relation (audit U3). It is optional for backward
    compatibility, but anonymous edges cannot be distinguished by operator, so
    conflicting epistemic statuses on the same (source, target, scope) key with
    anonymous operators fail closed at receipt validation.
    """

    edge_id: str
    source_state_id: str
    target_state_id: str
    status: MapEdgeStatus
    scope: str
    verification_id: str | None = None
    failure_id: str | None = None
    representation_id: str | None = None
    operator_id: str | None = None

    def __post_init__(self) -> None:
        if not self.edge_id or not self.source_state_id or not self.target_state_id or not self.scope:
            raise ValueError("operational edge requires id, endpoints, and scope")
        if self.status in {MapEdgeStatus.VERIFIED_APPLICABLE, MapEdgeStatus.VERIFIED_TRANSITION} and not self.verification_id:
            raise ValueError("verified applicability/transition status requires verification_id")
        if self.status is MapEdgeStatus.REFUTED_IN_SCOPE and not self.failure_id:
            raise ValueError("refuted edge requires failure/evidence identity")

    @property
    def transition_instance_key(self) -> tuple[str, str, str, str | None]:
        return (self.source_state_id, self.target_state_id, self.scope, self.operator_id)


def canonical_edge_set_hash(edges: Iterable[OperationalEdge]) -> str:
    """Canonical multiset hash of an edge enumeration (certificate excluded).

    This is the exact subject a ``CoverageCompletenessCertificate`` must bind:
    coverage completeness is a Moore-closure property of the enumeration, so the
    certificate's ``closure_subject_hash`` must equal this value (audit U4).
    """
    rows = sorted(
        json.dumps(
            {
                "edge_id": e.edge_id,
                "source": e.source_state_id,
                "target": e.target_state_id,
                "status": e.status.value,
                "scope": e.scope,
                "verification_id": e.verification_id,
                "failure_id": e.failure_id,
                "representation_id": e.representation_id,
                "operator_id": e.operator_id,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        for e in edges
    )
    return _hash({"schema": "orion.operational_map.edge_set.v1", "edges": rows})


_VERIFIED_POLARITY = frozenset({MapEdgeStatus.VERIFIED_TRANSITION, MapEdgeStatus.VERIFIED_APPLICABLE})


def _contradiction_error(key: tuple[str, str, str, str | None]) -> ValueError:
    return ValueError(
        "contradictory epistemic statuses for transition instance "
        f"(source={key[0]!r}, target={key[1]!r}, scope={key[2]!r}, operator={key[3]!r}): "
        "verified and refuted-in-scope cannot coexist; name distinct operator_ids "
        "if these are different operators"
    )


class _EdgeIndex:
    """Incremental validation index for one linear ``add_edge`` chain.

    Rebuilding the duplicate-id set and per-key status map on every
    ``add_edge`` made incremental map construction quadratic (engineering
    audit P1: 8k edges = 2.36 s). The index is shared along a single
    ``add_edge`` chain and extended in O(1) per edge; ``length`` records how
    many edges it currently covers, so a receipt whose edge count disagrees
    (e.g. a second branch grown from the same parent) rebuilds instead of
    trusting entries that belong to another branch.
    """

    __slots__ = ("length", "edge_ids", "statuses_by_key")

    def __init__(self, edges: Tuple[OperationalEdge, ...]) -> None:
        self.edge_ids: set[str] = set()
        self.statuses_by_key: dict[tuple[str, str, str, str | None], set[MapEdgeStatus]] = {}
        for edge in edges:
            self.edge_ids.add(edge.edge_id)
            self.statuses_by_key.setdefault(edge.transition_instance_key, set()).add(edge.status)
        self.length = len(edges)


# Handshake between add_edge (which validates the appended edge incrementally)
# and OperationalMapReceipt.__post_init__ (which may then skip the O(n)
# re-scan for that exact, already-validated edge tuple). Identity-checked.
_PREVALIDATED_EDGE_TUPLES: list[Tuple[OperationalEdge, ...]] = []


@dataclass(frozen=True)
class OperationalMapReceipt:
    map_id: str
    problem_state_hash: str
    operator_basis_version: str
    chart_id: str
    edges: Tuple[OperationalEdge, ...] = ()
    coverage_coordinates: Tuple[str, ...] = ()
    unknown_coordinates: Tuple[str, ...] = ()
    coverage_certificate: CoverageCompletenessCertificate | None = None

    def __post_init__(self) -> None:
        if not self.map_id or not self.problem_state_hash or not self.operator_basis_version or not self.chart_id:
            raise ValueError("operational map requires map/problem/operator-basis/chart identity")
        prevalidated = (
            bool(_PREVALIDATED_EDGE_TUPLES)
            and _PREVALIDATED_EDGE_TUPLES[-1] is self.edges
            and self.coverage_certificate is None
        )
        if not prevalidated:
            ids = [edge.edge_id for edge in self.edges]
            if len(ids) != len(set(ids)):
                raise ValueError("operational edge ids must be unique")
            # Consistency integrity constraint (audit U3): at most one epistemic
            # polarity per transition-instance key (source, target, scope,
            # operator). Anonymous operators cannot disambiguate a contradiction
            # from a multi-operator reading, so they fail closed too.
            statuses_by_key: dict[tuple[str, str, str, str | None], set[MapEdgeStatus]] = {}
            for edge in self.edges:
                statuses_by_key.setdefault(edge.transition_instance_key, set()).add(edge.status)
            for key, statuses in statuses_by_key.items():
                if MapEdgeStatus.REFUTED_IN_SCOPE in statuses and statuses & _VERIFIED_POLARITY:
                    raise _contradiction_error(key)
        if len(set(self.coverage_coordinates)) != len(self.coverage_coordinates):
            raise ValueError("coverage coordinates must be unique")
        if len(set(self.unknown_coordinates)) != len(self.unknown_coordinates):
            raise ValueError("unknown coordinates must be unique")
        if self.coverage_certificate is not None:
            if self.unknown_coordinates:
                raise ValueError("coverage certificate is incompatible with declared unknown coordinates")
            if not self.coverage_certificate.matches(
                problem_state_hash=self.problem_state_hash,
                operator_basis_version=self.operator_basis_version,
                chart_id=self.chart_id,
            ):
                raise ValueError("coverage certificate subject does not match operational map")
            # Moore-closure binding (audit U4): the certificate must certify
            # exactly this edge enumeration, not merely this subject triple.
            if self.coverage_certificate.closure_subject_hash != canonical_edge_set_hash(self.edges):
                raise ValueError(
                    "coverage certificate closure_subject_hash is not the canonical hash "
                    "of this map's edge enumeration"
                )

    @property
    def coverage_complete(self) -> bool:
        return self.coverage_certificate is not None

    @property
    def content_hash(self) -> str:
        return _hash({
            "schema": "orion.operational_map.v3",
            "map_id": self.map_id,
            "problem_state_hash": self.problem_state_hash,
            "operator_basis_version": self.operator_basis_version,
            "chart_id": self.chart_id,
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source": e.source_state_id,
                    "target": e.target_state_id,
                    "status": e.status.value,
                    "scope": e.scope,
                    "verification_id": e.verification_id,
                    "failure_id": e.failure_id,
                    "representation_id": e.representation_id,
                    "operator_id": e.operator_id,
                }
                for e in self.edges
            ],
            "coverage_coordinates": list(self.coverage_coordinates),
            "unknown_coordinates": list(self.unknown_coordinates),
            "coverage_certificate_id": None if self.coverage_certificate is None else self.coverage_certificate.certificate_id,
        })

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class MapReachabilityReport:
    verdict: MapReachabilityVerdict
    route_edge_ids: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    @property
    def establishes_mathematical_impossibility(self) -> bool:
        # Absence of a route in a complete registered operator basis and chart is
        # not theorem falsity, and is not even proof-system unprovability unless
        # a separate completeness theorem/certificate licenses that lift.
        return False

    @property
    def establishes_no_route_under_registered_map(self) -> bool:
        return self.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE


def _edge_index_for(receipt: OperationalMapReceipt) -> _EdgeIndex:
    index: _EdgeIndex | None = getattr(receipt, "_edge_index", None)
    if index is not None and index.length == len(receipt.edges):
        return index
    index = _EdgeIndex(receipt.edges)
    object.__setattr__(receipt, "_edge_index", index)
    return index


def add_edge(receipt: OperationalMapReceipt, edge: OperationalEdge) -> OperationalMapReceipt:
    """Return a new receipt with ``edge`` appended.

    Any coverage-completeness certificate is DROPPED (audit U4): completeness is
    a closure property of the exact edge enumeration, so a mutated enumeration
    is uncertified until the closure checker re-issues a certificate bound to
    the new canonical edge-set hash.

    Validation semantics are identical to full receipt construction (unique
    edge ids; audit-U3 polarity consistency per transition-instance key), but
    checked incrementally against a shared per-chain index so building a map
    edge-by-edge is linear, not quadratic (engineering audit P1).
    """
    index = _edge_index_for(receipt)
    if edge.edge_id in index.edge_ids:
        raise ValueError(f"duplicate operational edge id: {edge.edge_id}")
    key = edge.transition_instance_key
    existing = index.statuses_by_key.get(key)
    if existing is not None:
        merged = existing | {edge.status}
        if MapEdgeStatus.REFUTED_IN_SCOPE in merged and merged & _VERIFIED_POLARITY:
            raise _contradiction_error(key)
    new_edges = receipt.edges + (edge,)
    _PREVALIDATED_EDGE_TUPLES.append(new_edges)
    try:
        new_receipt = replace(receipt, edges=new_edges, coverage_certificate=None)
    finally:
        _PREVALIDATED_EDGE_TUPLES.pop()
    # Extend the shared chain index and hand it to the new receipt.
    index.edge_ids.add(edge.edge_id)
    index.statuses_by_key.setdefault(key, set()).add(edge.status)
    index.length += 1
    object.__setattr__(new_receipt, "_edge_index", index)
    return new_receipt


def verified_reachability(
    receipt: OperationalMapReceipt,
    *,
    start_state_id: str,
    target_state_id: str,
) -> MapReachabilityReport:
    if not start_state_id or not target_state_id:
        return MapReachabilityReport(MapReachabilityVerdict.CANNOT_CHECK, reasons=("start_or_target_missing",))
    if start_state_id == target_state_id:
        return MapReachabilityReport(MapReachabilityVerdict.VERIFIED_ROUTE_FOUND, reasons=("start_equals_target",))

    # Scope-uniform composition only (audit U2): each edge is verified relative
    # to its scope, and a route is a composite claim verified only in the meet
    # of its edge scopes. Scopes carry no registered meet-semilattice here, so
    # the only nonempty meet the model can name is scope equality; routes are
    # therefore searched within one scope at a time. A mixed-scope path is not
    # a verified route in any scope.
    adjacency_by_scope: dict[str, dict[str, list[OperationalEdge]]] = {}
    for edge in receipt.edges:
        if edge.status in VERIFIED_TRAVERSABLE:
            adjacency_by_scope.setdefault(edge.scope, {}).setdefault(edge.source_state_id, []).append(edge)

    def _scope_route(adjacency: dict[str, list[OperationalEdge]]) -> tuple[str, ...] | None:
        queue = deque([start_state_id])
        parent: dict[str, tuple[str, str]] = {}
        seen = {start_state_id}
        found = False
        while queue:
            current = queue.popleft()
            for edge in adjacency.get(current, ()):
                nxt = edge.target_state_id
                if nxt in seen:
                    continue
                seen.add(nxt)
                parent[nxt] = (current, edge.edge_id)
                if nxt == target_state_id:
                    found = True
                    queue.clear()
                    break
                queue.append(nxt)
        if not found:
            return None
        route: list[str] = []
        node = target_state_id
        while node != start_state_id:
            prev, edge_id = parent[node]
            route.append(edge_id)
            node = prev
        route.reverse()
        return tuple(route)

    for scope in sorted(adjacency_by_scope):
        route = _scope_route(adjacency_by_scope[scope])
        if route is not None:
            return MapReachabilityReport(
                MapReachabilityVerdict.VERIFIED_ROUTE_FOUND,
                route,
                ("route_uses_verified_transition_edges_only", f"route_scope_uniform:{scope}"),
            )

    incomplete = {
        MapEdgeStatus.CANDIDATE_UNVERIFIED,
        MapEdgeStatus.FAILED_ATTEMPT_NOT_REFUTED,
        MapEdgeStatus.REPRESENTATION_DEPENDENT,
        MapEdgeStatus.STALE_NEEDS_RECHECK,
        MapEdgeStatus.UNKNOWN,
    }
    if not receipt.coverage_complete or receipt.unknown_coordinates or any(edge.status in incomplete for edge in receipt.edges):
        return MapReachabilityReport(
            MapReachabilityVerdict.NO_VERIFIED_ROUTE_MAP_INCOMPLETE,
            reasons=("no_route_in_materialized_verified_subcomplex", "unknown_or_candidate_map_content_prevents_registered-map-closure_claim"),
        )
    return MapReachabilityReport(
        MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE,
        reasons=(
            "no_verified_route_in_certified_registered_map",
            "verdict_is_only_about_bound_problem_operator_basis_chart_and_closure_subject",
            "no_mathematical_impossibility_or_unprovability_authority",
        ),
    )
