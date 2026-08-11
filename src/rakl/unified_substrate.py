from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Tuple

from .core import KnowledgeFiber
from .experience_substrate import (
    ExperienceLedger,
    SubstrateEdge,
    SubstrateKind,
    SubstrateNode,
    SubstrateRelation,
)
from .failure_lattice import FailureExperienceLattice
from .research_tool_inventory import ResearchToolInventory


@dataclass(frozen=True)
class UnifiedSubstrateSnapshot:
    """Read-only overlay across RAKL's specialized canonical/working stores."""

    nodes: Tuple[SubstrateNode, ...]
    edges: Tuple[SubstrateEdge, ...]
    unresolved_links: Tuple[str, ...]
    snapshot_hash: str

    def nodes_of_kind(self, kind: SubstrateKind) -> Tuple[SubstrateNode, ...]:
        return tuple(node for node in self.nodes if node.kind is kind)


def _knowledge_node_id(fiber_id: str, projection_id: str) -> str:
    return f"knowledge:{fiber_id}:{projection_id}"


def _tool_node_id(tool_id: str) -> str:
    return f"tool:{tool_id}"


def _failure_node_id(failure_id: str) -> str:
    return f"failure:{failure_id}"


def materialize_unified_substrate(
    *,
    experience: ExperienceLedger,
    tools: ResearchToolInventory,
    failures: FailureExperienceLattice,
    legacy_knowledge_fibers: Iterable[KnowledgeFiber] = (),
) -> UnifiedSubstrateSnapshot:
    """Build one typed relational overlay without changing specialized authority.

    The overlay gives RAKL one queryable identity space for epistemic objects,
    operators, episodes, obstructions, strategies, and meta-method lessons while
    preserving the specialized stores as the owners of their own semantics.
    """

    nodes: list[SubstrateNode] = list(experience.nodes)
    edges: list[SubstrateEdge] = list(experience.edges)
    unresolved: list[str] = []
    node_ids = {node.node_id for node in nodes}

    def add_node(node: SubstrateNode) -> None:
        if node.node_id in node_ids:
            raise ValueError(f"unified substrate node collision: {node.node_id}")
        node_ids.add(node.node_id)
        nodes.append(node)

    for fiber in legacy_knowledge_fibers:
        for projection_id in sorted(fiber.projections):
            projection = fiber.projections[projection_id]
            add_node(
                SubstrateNode(
                    node_id=_knowledge_node_id(fiber.fiber_id, projection.projection_id),
                    kind=SubstrateKind.EPISTEMIC,
                    label=f"projection:{fiber.fiber_id}:{projection.projection_id}",
                    payload_hash=sha256(repr(projection).encode("utf-8")).hexdigest(),
                    metadata=(
                        ("authority", projection.authority.value),
                        ("object_id", projection.object_id),
                        ("fiber_id", fiber.fiber_id),
                    ),
                )
            )

    for failure in failures.experiences:
        node_id = _failure_node_id(failure.failure_id)
        add_node(
            SubstrateNode(
                node_id=node_id,
                kind=SubstrateKind.OBSTRUCTION,
                label=f"failure:{failure.failure_mode}",
                payload_hash=failure.artifact_hash,
                source_ids=(failure.research_trace_event_id,),
                metadata=(
                    ("diagnosis_status", failure.diagnosis_status.value),
                    ("method_family", failure.method_family),
                    ("context_hash", failure.context_packet_hash),
                ),
            )
        )
        if failure.research_trace_event_id in node_ids:
            edges.append(
                SubstrateEdge(
                    source_id=failure.research_trace_event_id,
                    target_id=node_id,
                    relation=SubstrateRelation.FAILED_WITH,
                    rationale="observed task episode produced this registered failure experience",
                    evidence_pointers=failure.evidence_pointers,
                )
            )
        else:
            unresolved.append(f"failure_episode_link_missing:{failure.failure_id}:{failure.research_trace_event_id}")

    lesson_ids = {lesson.lesson_id for lesson in experience.lessons}
    failure_ids = {failure.failure_id for failure in failures.experiences}
    episode_ids = {episode.episode_id for episode in experience.episodes}
    for tool in tools.tools:
        node_id = _tool_node_id(tool.tool_id)
        add_node(
            SubstrateNode(
                node_id=node_id,
                kind=SubstrateKind.OPERATOR,
                label=f"tool:{tool.name}",
                payload_hash=tool.artifact_hash,
                metadata=(
                    ("authority", tool.authority.value),
                    ("kind", tool.kind),
                    ("source_context_hash", tool.source_context_hash),
                ),
            )
        )
        if tool.source_candidate_id in lesson_ids:
            edges.append(
                SubstrateEdge(
                    source_id=tool.source_candidate_id,
                    target_id=node_id,
                    relation=SubstrateRelation.DERIVED_FROM,
                    rationale="validated operational lesson was projected into the research tool inventory",
                    evidence_pointers=tool.evidence_pointers,
                )
            )
        else:
            unresolved.append(f"tool_lesson_link_missing:{tool.tool_id}:{tool.source_candidate_id}")

        for failure_id in tool.known_failure_ids:
            if failure_id in failure_ids:
                edges.append(
                    SubstrateEdge(
                        source_id=_failure_node_id(failure_id),
                        target_id=node_id,
                        relation=SubstrateRelation.CONTRADICTS,
                        rationale="registered failure bounds or contradicts unqualified use of this tool",
                        evidence_pointers=tool.evidence_pointers,
                    )
                )
            else:
                unresolved.append(f"tool_known_failure_link_missing:{tool.tool_id}:{failure_id}")

        for reuse_id in tool.successful_reuse_ids:
            if reuse_id in episode_ids:
                edges.append(
                    SubstrateEdge(
                        source_id=reuse_id,
                        target_id=node_id,
                        relation=SubstrateRelation.SUCCEEDED_WITH,
                        rationale="registered successful reuse episode supports this tool's transfer history",
                        evidence_pointers=tool.evidence_pointers,
                    )
                )

    if len({node.node_id for node in nodes}) != len(nodes):
        raise ValueError("unified substrate node identities are not unique")

    edge_keys = {
        (edge.source_id, edge.target_id, edge.relation.value, edge.rationale)
        for edge in edges
    }
    if len(edge_keys) != len(edges):
        deduped: list[SubstrateEdge] = []
        seen: set[tuple[str, str, str, str]] = set()
        for edge in edges:
            key = (edge.source_id, edge.target_id, edge.relation.value, edge.rationale)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(edge)
        edges = deduped

    payload = repr(
        (
            tuple((node.node_id, node.kind.value, node.payload_hash) for node in nodes),
            tuple((edge.source_id, edge.target_id, edge.relation.value) for edge in edges),
            tuple(sorted(unresolved)),
        )
    ).encode("utf-8")
    return UnifiedSubstrateSnapshot(
        nodes=tuple(nodes),
        edges=tuple(edges),
        unresolved_links=tuple(sorted(set(unresolved))),
        snapshot_hash=sha256(payload).hexdigest(),
    )
