"""Exact tiny oracle for canonical graph cover complexity.

This implements the C005 pair-coverage criterion for the canonical
semi-filters used in the R004 two-dimensional cover-complexity route.

The oracle is deliberately tiny and exhaustive. It is a conjecture and
counterexample generator only. It does not prove asymptotic cover or
Boolean-circuit lower bounds.

C007 supplies an explicit logarithmic canonical cover when the complement
contains a perfect matching. C009 generalizes this to every complement by
coding biclique classes induced by a maximum matching. These constructors
are executable proof witnesses for finite combinatorial lemmas, not
substitutes for theorem-prover formalization or novelty review.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from math import ceil, log2
from typing import Iterable


Edge = tuple[int, int]
Pair = tuple[frozenset[int], frozenset[int]]


@dataclass(frozen=True)
class CanonicalCoverResult:
    n_vertices_per_side: int
    complement_edges: int
    canonical_edges: int
    distinct_maximal_pair_masks: int
    minimum_pairs: int


def neq_complement(n_vertices_per_side: int) -> set[Edge]:
    return {(i, i) for i in range(n_vertices_per_side)}


def _canonical_edge_data(
    n_vertices_per_side: int, complement: set[Edge]
) -> tuple[list[Edge], dict[int, frozenset[int]], dict[int, frozenset[int]], list[Edge]]:
    ordered_u = sorted(complement)
    index = {edge: i for i, edge in enumerate(ordered_u)}
    row_fibers = {
        u: frozenset(index[(u, v)] for v in range(n_vertices_per_side) if (u, v) in index)
        for u in range(n_vertices_per_side)
    }
    column_fibers = {
        v: frozenset(index[(u, v)] for u in range(n_vertices_per_side) if (u, v) in index)
        for v in range(n_vertices_per_side)
    }
    graph_edges = [
        (u, v)
        for u in range(n_vertices_per_side)
        for v in range(n_vertices_per_side)
        if (u, v) not in index
    ]
    canonical_edges = [
        (u, v)
        for (u, v) in graph_edges
        if row_fibers[u] and column_fibers[v]
    ]
    return ordered_u, row_fibers, column_fibers, canonical_edges


def pair_covers_canonical_edge(
    row_fiber: frozenset[int],
    column_fiber: frozenset[int],
    e_set: frozenset[int],
    h_set: frozenset[int],
) -> bool:
    orientation_1 = (
        row_fiber <= e_set
        and column_fiber <= h_set
        and not row_fiber <= h_set
        and not column_fiber <= e_set
    )
    orientation_2 = (
        row_fiber <= h_set
        and column_fiber <= e_set
        and not row_fiber <= e_set
        and not column_fiber <= h_set
    )
    return orientation_1 or orientation_2


def _validate_perfect_matching(
    n_vertices_per_side: int, complement: set[Edge], matching: set[Edge]
) -> dict[int, int]:
    if len(matching) != n_vertices_per_side:
        raise ValueError("matching must contain exactly one edge per row and column")
    if not matching <= complement:
        raise ValueError("matching must be a subset of the complement graph")
    row_to_column: dict[int, int] = {}
    columns: set[int] = set()
    for u, v in matching:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("matching edge lies outside the requested bipartite ground set")
        if u in row_to_column or v in columns:
            raise ValueError("matching must contain exactly one edge per row and column")
        row_to_column[u] = v
        columns.add(v)
    if set(row_to_column) != set(range(n_vertices_per_side)) or columns != set(range(n_vertices_per_side)):
        raise ValueError("matching must contain exactly one edge per row and column")
    return row_to_column


def perfect_matching_canonical_cover_pairs(
    n_vertices_per_side: int, complement: set[Edge], matching: set[Edge]
) -> list[Pair]:
    """Construct the C007 logarithmic canonical cover from a perfect matching."""
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    row_to_column = _validate_perfect_matching(n_vertices_per_side, complement, matching)
    ordered_u = sorted(complement)
    index = {edge: i for i, edge in enumerate(ordered_u)}
    matching_indices = {index[edge] for edge in matching}
    nonmatching_indices = set(range(len(ordered_u))) - matching_indices
    pairs: list[Pair] = []
    for bit in range(expected_neq_cover(n_vertices_per_side)):
        e_set = set(nonmatching_indices)
        h_set = set(nonmatching_indices)
        for u in range(n_vertices_per_side):
            edge_index = index[(u, row_to_column[u])]
            if (u >> bit) & 1:
                e_set.add(edge_index)
            else:
                h_set.add(edge_index)
        pairs.append((frozenset(e_set), frozenset(h_set)))
    return pairs


def _maximum_bipartite_matching(
    n_vertices_per_side: int, complement: set[Edge]
) -> set[Edge]:
    """Return a deterministic maximum-cardinality matching of the complement."""
    neighbors = {
        u: tuple(sorted(v for x, v in complement if x == u))
        for u in range(n_vertices_per_side)
    }
    matched_right: dict[int, int] = {}

    def augment(u: int, seen_right: set[int]) -> bool:
        for v in neighbors[u]:
            if v in seen_right:
                continue
            seen_right.add(v)
            if v not in matched_right or augment(matched_right[v], seen_right):
                matched_right[v] = u
                return True
        return False

    for u in range(n_vertices_per_side):
        augment(u, set())
    return {(u, v) for v, u in matched_right.items()}


def matching_number_canonical_cover_pairs(
    n_vertices_per_side: int, complement: set[Edge]
) -> list[Pair]:
    """Construct the C009 canonical cover from a maximum matching.

    The proof partitions active vertices into star-biclique classes indexed by
    the matching edges. Internal class complement edges carry one exclusive
    bit value; cross-class complement edges are placed in both sides.
    """
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    for u, v in complement:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("complement edge lies outside the requested bipartite ground set")
    if not complement:
        return []

    matching = sorted(_maximum_bipartite_matching(n_vertices_per_side, complement))
    matching_size = len(matching)
    if matching_size <= 1:
        return []

    row_class: dict[int, int] = {}
    column_class: dict[int, int] = {}
    for class_id, (u, v) in enumerate(matching):
        row_class[u] = class_id
        column_class[v] = class_id

    active_rows = {u for u, _ in complement}
    active_columns = {v for _, v in complement}

    for u in sorted(active_rows - row_class.keys()):
        candidates = sorted(
            (column_class[v], v)
            for x, v in complement
            if x == u and v in column_class
        )
        if not candidates:
            raise RuntimeError("maximum matching invariant failed for unmatched active row")
        row_class[u] = candidates[0][0]

    for v in sorted(active_columns - column_class.keys()):
        candidates = sorted(
            (row_class[u], u)
            for u, y in complement
            if y == v and u in row_class
        )
        if not candidates:
            raise RuntimeError("maximum matching invariant failed for unmatched active column")
        column_class[v] = candidates[0][0]

    # Executable assertion for the C009-L1 star-biclique invariant.
    for u in active_rows:
        for v in active_columns:
            if row_class[u] == column_class[v] and (u, v) not in complement:
                raise RuntimeError("maximum-matching class is not a complement biclique")

    ordered_u = sorted(complement)
    pairs: list[Pair] = []
    bit_count = ceil(log2(matching_size))
    for bit in range(bit_count):
        e_set: set[int] = set()
        h_set: set[int] = set()
        for edge_index, (u, v) in enumerate(ordered_u):
            if row_class[u] == column_class[v]:
                if (row_class[u] >> bit) & 1:
                    e_set.add(edge_index)
                else:
                    h_set.add(edge_index)
            else:
                e_set.add(edge_index)
                h_set.add(edge_index)
        pairs.append((frozenset(e_set), frozenset(h_set)))
    return pairs


def canonical_pairs_cover_all_edges(
    n_vertices_per_side: int, complement: set[Edge], pairs: Iterable[Pair]
) -> bool:
    _, row_fibers, column_fibers, canonical_edges = _canonical_edge_data(n_vertices_per_side, complement)
    materialized = tuple(pairs)
    return all(
        any(
            pair_covers_canonical_edge(row_fibers[u], column_fibers[v], e_set, h_set)
            for e_set, h_set in materialized
        )
        for u, v in canonical_edges
    )


def _maximal_masks(masks: Iterable[int]) -> list[int]:
    maximal: list[int] = []
    for mask in sorted(set(masks), key=int.bit_count, reverse=True):
        if not any(mask | other == other for other in maximal):
            maximal.append(mask)
    return maximal


def exact_canonical_cover_number(
    n_vertices_per_side: int,
    complement: set[Edge],
    *,
    max_complement_edges: int = 10,
) -> CanonicalCoverResult:
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    limit = n_vertices_per_side * n_vertices_per_side
    for u, v in complement:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("complement edge lies outside the requested bipartite ground set")
    if len(complement) == 0 or len(complement) == limit:
        raise ValueError("use a nontrivial graph with a nonempty complement")
    if len(complement) > max_complement_edges:
        raise ValueError(
            f"strict exhaustive-search guard: |U|={len(complement)} exceeds max_complement_edges={max_complement_edges}"
        )
    ordered_u, row_fibers, column_fibers, canonical_edges = _canonical_edge_data(n_vertices_per_side, complement)
    if not canonical_edges:
        return CanonicalCoverResult(n_vertices_per_side, len(ordered_u), 0, 0, 0)
    masks: set[int] = set()
    for states in product(range(4), repeat=len(ordered_u)):
        e_set = frozenset(i for i, state in enumerate(states) if state & 1)
        h_set = frozenset(i for i, state in enumerate(states) if state & 2)
        mask = 0
        for bit, (u, v) in enumerate(canonical_edges):
            if pair_covers_canonical_edge(row_fibers[u], column_fibers[v], e_set, h_set):
                mask |= 1 << bit
        if mask:
            masks.add(mask)
    maximal = _maximal_masks(masks)
    full = (1 << len(canonical_edges)) - 1
    queue = deque([0])
    depth = {0: 0}
    while queue:
        current = queue.popleft()
        next_depth = depth[current] + 1
        for pair_mask in maximal:
            nxt = current | pair_mask
            if nxt == full:
                return CanonicalCoverResult(
                    n_vertices_per_side,
                    len(ordered_u),
                    len(canonical_edges),
                    len(maximal),
                    next_depth,
                )
            if nxt != current and nxt not in depth:
                depth[nxt] = next_depth
                queue.append(nxt)
    raise RuntimeError("canonical edge universe was not coverable; implementation invariant failed")


def neq_calibration(n_vertices_per_side: int) -> CanonicalCoverResult:
    return exact_canonical_cover_number(n_vertices_per_side, neq_complement(n_vertices_per_side))


def expected_neq_cover(n_vertices_per_side: int) -> int:
    return ceil(log2(n_vertices_per_side))


if __name__ == "__main__":
    for n_vertices in range(2, 6):
        result = neq_calibration(n_vertices)
        print(n_vertices, result.minimum_pairs, expected_neq_cover(n_vertices), result)
