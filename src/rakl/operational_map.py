from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Tuple


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


VERIFIED_TRAVERSABLE = frozenset({
    MapEdgeStatus.VERIFIED_APPLICABLE,
    MapEdgeStatus.VERIFIED_TRANSITION,
})


class MapReachabilityVerdict(str, Enum):
    VERIFIED_ROUTE_FOUND = "VERIFIED_ROUTE_FOUND"
    NO_VERIFIED_ROUTE_MAP_INCOMPLETE = "NO_VERIFIED_ROUTE_MAP_INCOMPLETE"
    NO_VERIFIED_ROUTE_COVERAGE_COMPLETE = "NO_VERIFIED_ROUTE_COVERAGE_COMPLETE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class OperationalEdge:
    edge_id: str
    source_state_id: str
    target_state_id: str
    status: MapEdgeStatus
    scope: str
    verification_id: str | None = None
    failure_id: str | None = None
    representation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.edge_id or not self.source_state_id or not self.target_state_id or not self.scope:
            raise ValueError("operational edge requires id, endpoints, and scope")
        if self.status in VERIFIED_TRAVERSABLE and not self.verification_id:
            raise ValueError("verified traversable edge requires verification_id")
        if self.status is MapEdgeStatus.REFUTED_IN_SCOPE and not self.failure_id:
            raise ValueError("refuted edge requires failure/evidence identity")


@dataclass(frozen=True)
class OperationalMapReceipt:
    map_id: str
    problem_state_hash: str
    operator_basis_version: str
    chart_id: str
    edges: Tuple[OperationalEdge, ...] = ()
    coverage_coordinates: Tuple[str, ...] = ()
    unknown_coordinates: Tuple[str, ...] = ()
    coverage_complete: bool = False

    def __post_init__(self) -> None:
        if not self.map_id or not self.problem_state_hash or not self.operator_basis_version or not self.chart_id:
            raise ValueError("operational map requires map/problem/operator-basis/chart identity")
        ids = [edge.edge_id for edge in self.edges]
        if len(ids) != len(set(ids)):
            raise ValueError("operational edge ids must be unique")
        if len(set(self.coverage_coordinates)) != len(self.coverage_coordinates):
            raise ValueError("coverage coordinates must be unique")
        if len(set(self.unknown_coordinates)) != len(self.unknown_coordinates):
            raise ValueError("unknown coordinates must be unique")
        if self.coverage_complete and self.unknown_coordinates:
            raise ValueError("coverage_complete is incompatible with declared unknown coordinates")

    @property
    def content_hash(self) -> str:
        return _hash({
            "schema": "orion.operational_map.v1",
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
                }
                for e in self.edges
            ],
            "coverage_coordinates": list(self.coverage_coordinates),
            "unknown_coordinates": list(self.unknown_coordinates),
            "coverage_complete": self.coverage_complete,
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
        return self.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE


def add_edge(receipt: OperationalMapReceipt, edge: OperationalEdge) -> OperationalMapReceipt:
    if edge.edge_id in {item.edge_id for item in receipt.edges}:
        raise ValueError(f"duplicate operational edge id: {edge.edge_id}")
    return replace(receipt, edges=receipt.edges + (edge,))


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

    adjacency: dict[str, list[OperationalEdge]] = {}
    for edge in receipt.edges:
        if edge.status in VERIFIED_TRAVERSABLE:
            adjacency.setdefault(edge.source_state_id, []).append(edge)

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

    if found:
        route: list[str] = []
        node = target_state_id
        while node != start_state_id:
            prev, edge_id = parent[node]
            route.append(edge_id)
            node = prev
        route.reverse()
        return MapReachabilityReport(MapReachabilityVerdict.VERIFIED_ROUTE_FOUND, tuple(route), ("route_uses_verified_traversable_edges_only",))

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
            reasons=("no_route_in_materialized_verified_subcomplex", "unknown_or_candidate_map_content_prevents_impossibility_claim"),
        )
    return MapReachabilityReport(
        MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE,
        reasons=("no_verified_route_in_declared_complete_map", "verdict_is_scoped_to_registered_operator_basis_chart_and_coverage_contract"),
    )
