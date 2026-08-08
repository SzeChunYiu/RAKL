from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResearchNodeStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    SURVIVED = "SURVIVED"
    POWERED_NULL = "POWERED_NULL"
    REFUTED = "REFUTED"
    PARTIAL_ID = "PARTIAL_ID"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class BranchMetrics:
    expected_information_gain: float = 0.0
    decision_impact: float = 0.0
    semantic_novelty: float = 0.0
    cost: float = 1.0
    authority_risk: float = 0.0

    def __post_init__(self) -> None:
        if self.cost <= 0:
            raise ValueError("cost must be positive")
        if self.authority_risk < 0:
            raise ValueError("authority_risk must be non-negative")


@dataclass
class ResearchNode:
    node_id: str
    fiber_id: str
    hypothesis: str
    parent_id: str | None = None
    mechanism_family: str | None = None
    representation_family: str | None = None
    status: ResearchNodeStatus = ResearchNodeStatus.PROPOSED
    metrics: BranchMetrics = field(default_factory=BranchMetrics)
    evidence_ids: list[str] = field(default_factory=list)
    child_ids: list[str] = field(default_factory=list)


class ResearchTree:
    """Versioned hypothesis tree that preserves alternatives instead of greedy replacement."""

    def __init__(self) -> None:
        self.nodes: dict[str, ResearchNode] = {}
        self.events: list[dict] = []

    def add_node(self, node: ResearchNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node_id: {node.node_id}")
        if node.parent_id is not None and node.parent_id not in self.nodes:
            raise KeyError(f"missing parent_id: {node.parent_id}")

        self.nodes[node.node_id] = node
        if node.parent_id is not None:
            self.nodes[node.parent_id].child_ids.append(node.node_id)
        self.events.append(
            {
                "event": "ADD_NODE",
                "node_id": node.node_id,
                "parent_id": node.parent_id,
                "status": node.status.value,
            }
        )

    def set_status(
        self,
        node_id: str,
        status: ResearchNodeStatus,
        *,
        evidence_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        node = self.nodes[node_id]
        previous = node.status
        node.status = status
        if evidence_id is not None:
            node.evidence_ids.append(evidence_id)
        self.events.append(
            {
                "event": "SET_STATUS",
                "node_id": node_id,
                "from": previous.value,
                "to": status.value,
                "evidence_id": evidence_id,
                "reason": reason,
            }
        )

    def active_nodes(self) -> list[ResearchNode]:
        allowed = {
            ResearchNodeStatus.PROPOSED,
            ResearchNodeStatus.ACTIVE,
            ResearchNodeStatus.SURVIVED,
            ResearchNodeStatus.PARTIAL_ID,
        }
        return [node for node in self.nodes.values() if node.status in allowed]

    @staticmethod
    def dominates(left: ResearchNode, right: ResearchNode) -> bool:
        """Pareto dominance: maximize knowledge/value axes, minimize cost/risk."""
        a, b = left.metrics, right.metrics
        no_worse = (
            a.expected_information_gain >= b.expected_information_gain
            and a.decision_impact >= b.decision_impact
            and a.semantic_novelty >= b.semantic_novelty
            and a.cost <= b.cost
            and a.authority_risk <= b.authority_risk
        )
        strictly_better = (
            a.expected_information_gain > b.expected_information_gain
            or a.decision_impact > b.decision_impact
            or a.semantic_novelty > b.semantic_novelty
            or a.cost < b.cost
            or a.authority_risk < b.authority_risk
        )
        return no_worse and strictly_better

    def pareto_frontier(self) -> list[ResearchNode]:
        nodes = self.active_nodes()
        frontier: list[ResearchNode] = []
        for candidate in nodes:
            if any(
                other.node_id != candidate.node_id and self.dominates(other, candidate)
                for other in nodes
            ):
                continue
            frontier.append(candidate)
        return frontier

    def diverse_frontier(self) -> list[ResearchNode]:
        """Keep at least one non-dominated branch per distinct mechanism family.

        This is intentionally not a single-score ranker. It exposes epistemically distinct
        families so the portfolio scheduler can allocate diversification budget.
        """
        frontier = self.pareto_frontier()
        seen: set[str] = set()
        result: list[ResearchNode] = []
        for node in sorted(frontier, key=lambda n: n.node_id):
            family = node.mechanism_family or f"__unclassified__:{node.node_id}"
            if family in seen:
                continue
            seen.add(family)
            result.append(node)
        return result

    def unresolved_leaf_nodes(self) -> list[ResearchNode]:
        terminal = {
            ResearchNodeStatus.POWERED_NULL,
            ResearchNodeStatus.REFUTED,
            ResearchNodeStatus.RETIRED,
        }
        return [
            node
            for node in self.nodes.values()
            if not node.child_ids and node.status not in terminal
        ]
