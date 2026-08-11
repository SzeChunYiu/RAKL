"""Executable witness construction for C015 arboricity/forest cover pruning.

The helper realizes one-sided partial-function graphs and bipartite forests from
row/column generators using only the pairwise intersections counted by
Cavalar--Oliveira intersection complexity.  It checks finite set equalities and
operation counts.  It is calibration evidence, not an asymptotic proof
certificate and not a circuit lower bound.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable, Literal


Edge = tuple[int, int]
Side = Literal["left", "right"]


@dataclass(frozen=True)
class PartialFunctionWitness:
    n_vertices_per_side: int
    direction: str
    target: frozenset[Edge]
    reconstructed: frozenset[Edge]
    code_bits: int
    counted_intersections: int


@dataclass(frozen=True)
class ForestWitness:
    n_vertices_per_side: int
    target: frozenset[Edge]
    left_parent_edges: frozenset[Edge]
    right_parent_edges: frozenset[Edge]
    reconstructed: frozenset[Edge]
    code_bits: int
    counted_intersections: int


def _validate_n(n_vertices_per_side: int) -> None:
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")


def _normalize_edges(n: int, edges: Iterable[Edge]) -> tuple[Edge, ...]:
    _validate_n(n)
    normalized = tuple(sorted(set(edges)))
    for u, v in normalized:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge lies outside the requested bipartite graph")
    return normalized


def _row(n: int, u: int) -> set[Edge]:
    return {(u, v) for v in range(n)}


def _column(n: int, v: int) -> set[Edge]:
    return {(u, v) for u in range(n)}


def _partial_function_witness(
    n_vertices_per_side: int,
    edges: Iterable[Edge],
    *,
    unique_side: Side,
) -> PartialFunctionWitness:
    """Reconstruct a bipartite partial function with at most 2 ceil(log2 N) intersections.

    ``unique_side="right"`` means each right vertex has at most one left
    neighbour (a partial map R -> L).  ``unique_side="left"`` is symmetric.
    """

    n = n_vertices_per_side
    target = frozenset(_normalize_edges(n, edges))
    if not target:
        raise ValueError("partial-function edge set must be non-empty")

    if unique_side == "right":
        endpoints = [v for _, v in target]
        if len(set(endpoints)) != len(endpoints):
            raise ValueError("right endpoint has more than one image")
        image_for_active = {v: u for u, v in target}
    elif unique_side == "left":
        endpoints = [u for u, _ in target]
        if len(set(endpoints)) != len(endpoints):
            raise ValueError("left endpoint has more than one image")
        image_for_active = {u: v for u, v in target}
    else:
        raise ValueError("unique_side must be 'left' or 'right'")

    k = ceil(log2(n))
    codes = {vertex: vertex for vertex in range(n)}
    equality_bits: list[set[Edge]] = []
    counted = 0

    for bit in range(k):
        rows_one: set[Edge] = set()
        rows_zero: set[Edge] = set()
        columns_one: set[Edge] = set()
        columns_zero: set[Edge] = set()

        for u in range(n):
            if unique_side == "right":
                code = codes[u]
            else:
                code = codes[image_for_active[u]] if u in image_for_active else 0
            (rows_one if (code >> bit) & 1 else rows_zero).update(_row(n, u))

        for v in range(n):
            if unique_side == "right":
                code = codes[image_for_active[v]] if v in image_for_active else 0
            else:
                code = codes[v]
            (columns_one if (code >> bit) & 1 else columns_zero).update(_column(n, v))

        a_bit = rows_one | columns_zero
        b_bit = rows_zero | columns_one
        equality_bits.append(a_bit & b_bit)
        counted += 1

    reconstructed = set(equality_bits[0])
    for equality_bit in equality_bits[1:]:
        reconstructed &= equality_bit
        counted += 1

    # Equality coding gives exactly one candidate cell on every vertex of the
    # unique side, including inactive vertices whose temporary code is zero.
    # One free union of active generators followed by one intersection removes
    # all inactive cells.
    active_generators: set[Edge] = set()
    if unique_side == "right":
        for v in image_for_active:
            active_generators.update(_column(n, v))
    else:
        for u in image_for_active:
            active_generators.update(_row(n, u))
    reconstructed &= active_generators
    counted += 1

    if frozenset(reconstructed) != target:
        raise AssertionError("partial-function coding failed to reconstruct target")

    return PartialFunctionWitness(
        n_vertices_per_side=n,
        direction="R->L" if unique_side == "right" else "L->R",
        target=target,
        reconstructed=frozenset(reconstructed),
        code_bits=k,
        counted_intersections=counted,
    )


def right_to_left_partial_function_witness(
    n_vertices_per_side: int, edges: Iterable[Edge]
) -> PartialFunctionWitness:
    return _partial_function_witness(
        n_vertices_per_side, edges, unique_side="right"
    )


def left_to_right_partial_function_witness(
    n_vertices_per_side: int, edges: Iterable[Edge]
) -> PartialFunctionWitness:
    return _partial_function_witness(
        n_vertices_per_side, edges, unique_side="left"
    )


def _forest_parent_partition(n: int, edges: tuple[Edge, ...]) -> tuple[set[Edge], set[Edge]]:
    """Orient each forest component away from a root and split by parent side."""

    adjacency: dict[tuple[Side, int], list[tuple[Side, int]]] = {
        (side, vertex): []
        for side in ("left", "right")
        for vertex in range(n)
    }
    for u, v in edges:
        adjacency[("left", u)].append(("right", v))
        adjacency[("right", v)].append(("left", u))

    left_parent_edges: set[Edge] = set()
    right_parent_edges: set[Edge] = set()
    visited: set[tuple[Side, int]] = set()

    for root in adjacency:
        if root in visited or not adjacency[root]:
            continue
        visited.add(root)
        queue: deque[tuple[Side, int]] = deque([root])
        while queue:
            parent = queue.popleft()
            for child in adjacency[parent]:
                if child in visited:
                    continue
                visited.add(child)
                queue.append(child)
                if parent[0] == "left":
                    edge = (parent[1], child[1])
                    left_parent_edges.add(edge)
                else:
                    edge = (child[1], parent[1])
                    right_parent_edges.add(edge)

    oriented = left_parent_edges | right_parent_edges
    if oriented != set(edges):
        raise ValueError("edge set is not a forest: a cycle or duplicate connectivity remains")
    return left_parent_edges, right_parent_edges


def forest_intersection_witness(
    n_vertices_per_side: int, edges: Iterable[Edge]
) -> ForestWitness:
    """Reconstruct a nonempty bipartite forest with <=4 ceil(log2 N) intersections."""

    n = n_vertices_per_side
    normalized = _normalize_edges(n, edges)
    if not normalized:
        raise ValueError("forest must be non-empty")
    left_parent, right_parent = _forest_parent_partition(n, normalized)

    reconstructed: set[Edge] = set()
    counted = 0
    if left_parent:
        witness = right_to_left_partial_function_witness(n, left_parent)
        reconstructed.update(witness.reconstructed)
        counted += witness.counted_intersections
    if right_parent:
        witness = left_to_right_partial_function_witness(n, right_parent)
        reconstructed.update(witness.reconstructed)
        counted += witness.counted_intersections

    target = frozenset(normalized)
    if frozenset(reconstructed) != target:
        raise AssertionError("forest orientation decomposition failed")

    return ForestWitness(
        n_vertices_per_side=n,
        target=target,
        left_parent_edges=frozenset(left_parent),
        right_parent_edges=frozenset(right_parent),
        reconstructed=frozenset(reconstructed),
        code_bits=ceil(log2(n)),
        counted_intersections=counted,
    )


def reconstruct_forest_union(
    n_vertices_per_side: int, forests: Iterable[Iterable[Edge]]
) -> tuple[frozenset[Edge], int]:
    """Construct the union of an explicitly supplied edge-disjoint forest partition."""

    union: set[Edge] = set()
    cost = 0
    seen_any = False
    for forest in forests:
        forest_edges = set(forest)
        if not forest_edges:
            continue
        seen_any = True
        witness = forest_intersection_witness(n_vertices_per_side, forest_edges)
        if union.intersection(witness.target):
            raise ValueError("forest partition must be edge-disjoint")
        union.update(witness.reconstructed)
        cost += witness.counted_intersections
    if not seen_any:
        raise ValueError("at least one non-empty forest is required")
    return frozenset(union), cost
