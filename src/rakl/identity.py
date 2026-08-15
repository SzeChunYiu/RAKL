from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class EvidenceIdentityRelation(str, Enum):
    """Typed relations between evidence entities.

    Only ``IDENTICAL_TO`` is exact identity and therefore collapses identifiers.
    ``VERSION_OF`` and ``DERIVED_FROM`` preserve distinct entity identity while
    contributing shared ancestry for independence checks. ``POSSIBLE_ALIAS`` is an
    unresolved identity claim and therefore blocks a full identity certificate for
    any lineage it touches.
    """

    IDENTICAL_TO = "IDENTICAL_TO"
    VERSION_OF = "VERSION_OF"
    DERIVED_FROM = "DERIVED_FROM"
    POSSIBLE_ALIAS = "POSSIBLE_ALIAS"


@dataclass(frozen=True, order=True)
class EvidenceIdentityEdge:
    left: str
    right: str
    relation: EvidenceIdentityRelation

    def __post_init__(self) -> None:
        if not self.left.strip() or not self.right.strip():
            raise ValueError("evidence identity endpoints cannot be empty")
        if self.left == self.right:
            raise ValueError("evidence identity relation must connect distinct identifiers")


@dataclass(frozen=True)
class LineageResolution:
    raw_entities: frozenset[str]
    canonical_entities: frozenset[str]
    ancestry_tokens: frozenset[str]
    unresolved_identity_pairs: tuple[tuple[str, str], ...]

    @property
    def identity_resolved(self) -> bool:
        return not self.unresolved_identity_pairs


@dataclass(frozen=True)
class EvidenceIdentityLedger:
    """Conservative identity/ancestry normalization for evidence lineages.

    The ledger deliberately separates exact aliasing from versioning and derivation.
    Exact aliases form deterministic equivalence classes. Version/derivation edges are
    directed child -> ancestor relationships and are transitively expanded for overlap
    detection without collapsing the child into the ancestor. Possible aliases remain
    unresolved and prevent a full independence certificate when they touch a lineage.
    """

    edges: tuple[EvidenceIdentityEdge, ...] = ()

    @classmethod
    def from_relations(
        cls,
        relations: Iterable[
            tuple[str, str, EvidenceIdentityRelation | str]
            | EvidenceIdentityEdge
        ],
    ) -> "EvidenceIdentityLedger":
        edges: list[EvidenceIdentityEdge] = []
        for item in relations:
            if isinstance(item, EvidenceIdentityEdge):
                edge = item
            else:
                left, right, raw_relation = item
                relation = (
                    raw_relation
                    if isinstance(raw_relation, EvidenceIdentityRelation)
                    else EvidenceIdentityRelation(raw_relation)
                )
                edge = EvidenceIdentityEdge(left.strip(), right.strip(), relation)
            edges.append(edge)
        ledger = cls(tuple(sorted(set(edges))))
        ledger._assert_acyclic_ancestry()
        return ledger

    def _all_nodes(self, extra: Iterable[str] = ()) -> set[str]:
        nodes = {item.strip() for item in extra if item.strip()}
        for edge in self.edges:
            nodes.add(edge.left)
            nodes.add(edge.right)
        return nodes

    def _canonical_map(self, extra: Iterable[str] = ()) -> dict[str, str]:
        nodes = self._all_nodes(extra)
        parent = {node: node for node in nodes}

        def find(node: str) -> str:
            root = node
            while parent[root] != root:
                root = parent[root]
            while parent[node] != node:
                nxt = parent[node]
                parent[node] = root
                node = nxt
            return root

        def union(left: str, right: str) -> None:
            a = find(left)
            b = find(right)
            if a == b:
                return
            # Stable lexical representative makes receipts reproducible regardless
            # of relation insertion order.
            keep, other = sorted((a, b))
            parent[other] = keep

        for edge in self.edges:
            if edge.relation is EvidenceIdentityRelation.IDENTICAL_TO:
                union(edge.left, edge.right)

        return {node: find(node) for node in nodes}

    def canonical_id(self, entity_id: str) -> str:
        entity = entity_id.strip()
        if not entity:
            raise ValueError("evidence entity id cannot be empty")
        return self._canonical_map((entity,))[entity]

    def _ancestry_graph(self, canonical: dict[str, str]) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge.relation not in {
                EvidenceIdentityRelation.VERSION_OF,
                EvidenceIdentityRelation.DERIVED_FROM,
            }:
                continue
            child = canonical[edge.left]
            ancestor = canonical[edge.right]
            if child == ancestor:
                raise ValueError(
                    "version/derivation relation collapses into exact identity: "
                    f"{edge.left!r} -> {edge.right!r}"
                )
            graph.setdefault(child, set()).add(ancestor)
        return graph

    def _assert_acyclic_ancestry(self) -> None:
        canonical = self._canonical_map()
        graph = self._ancestry_graph(canonical)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError("evidence version/derivation ancestry must be acyclic")
            visiting.add(node)
            for ancestor in sorted(graph.get(node, ())):
                visit(ancestor)
            visiting.remove(node)
            visited.add(node)

        for node in sorted(graph):
            visit(node)

    def ancestry_roots(self, entity_ids: Iterable[str]) -> frozenset[str]:
        """Resolve entities to their maximal ancestors under version/derivation.

        A canonical entity with no outgoing version/derivation edge is its own
        root. Counting roots rather than canonical entities is what makes
        apparent independent support insensitive to citing several versions of
        one work; the ledger still keeps the versions as distinct entities.
        """

        resolution = self.normalize_lineage(entity_ids)
        canonical = self._canonical_map(resolution.raw_entities)
        graph = self._ancestry_graph(canonical)

        roots: set[str] = set()
        for entity in sorted(resolution.canonical_entities):
            seen: set[str] = set()
            stack = [entity]
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                ancestors = graph.get(node)
                if not ancestors:
                    roots.add(node)
                else:
                    stack.extend(sorted(ancestors))
        return frozenset(roots)

    def normalize_lineage(self, entity_ids: Iterable[str]) -> LineageResolution:
        raw = frozenset(item.strip() for item in entity_ids if item.strip())
        if not raw:
            raise ValueError("lineage normalization requires at least one evidence entity")

        canonical = self._canonical_map(raw)
        canonical_entities = frozenset(canonical[item] for item in raw)
        graph = self._ancestry_graph(canonical)

        closure = set(canonical_entities)
        stack = list(sorted(canonical_entities))
        while stack:
            node = stack.pop()
            for ancestor in sorted(graph.get(node, ())):
                if ancestor not in closure:
                    closure.add(ancestor)
                    stack.append(ancestor)

        unresolved: set[tuple[str, str]] = set()
        for edge in self.edges:
            if edge.relation is not EvidenceIdentityRelation.POSSIBLE_ALIAS:
                continue
            left = canonical[edge.left]
            right = canonical[edge.right]
            if left == right:
                continue
            if left in closure or right in closure:
                unresolved.add(tuple(sorted((left, right))))

        return LineageResolution(
            raw_entities=raw,
            canonical_entities=canonical_entities,
            ancestry_tokens=frozenset(closure),
            unresolved_identity_pairs=tuple(sorted(unresolved)),
        )
