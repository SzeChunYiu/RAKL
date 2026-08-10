"""Exact tiny oracle for canonical graph cover complexity.

This implements the C005 pair-coverage criterion for the canonical
semi-filters used in the R004 two-dimensional cover-complexity route.

The oracle is deliberately tiny and exhaustive. It is a conjecture and
counterexample generator only. It does not prove asymptotic cover or
Boolean-circuit lower bounds.

C007 additionally supplies an explicit logarithmic canonical cover whenever
the complement graph contains a perfect matching. That constructor is an
executable proof witness for the finite combinatorial lemma, not a substitute
for theorem-prover formalization or novelty review.
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
    """Complement of G_NEQ, namely the diagonal perfect matching."""
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
    """C005 exactly: whether (E,H) covers one canonical semi-filter."""
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
    n_vertices_per_side: int,
    complement: set[Edge],
    matching: set[Edge],
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

    if set(row_to_column) != set(range(n_vertices_per_side)) or columns != set(
        range(n_vertices_per_side)
    ):
        raise ValueError("matching must contain exactly one edge per row and column")
    return row_to_column


def perfect_matching_canonical_cover_pairs(
    n_vertices_per_side: int,
    complement: set[Edge],
    matching: set[Edge],
) -> list[Pair]:
    """Construct the C007 logarithmic canonical cover from a perfect matching.

    Every nonmatching complement edge is placed in both members of each pair.
    A matching edge is placed exclusively in E or H according to one bit of a
    distinct binary row code. This realizes the row code on each row and the
    same code on its matched column.
    """
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    row_to_column = _validate_perfect_matching(
        n_vertices_per_side, complement, matching
    )

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


def canonical_pairs_cover_all_edges(
    n_vertices_per_side: int,
    complement: set[Edge],
    pairs: Iterable[Pair],
) -> bool:
    """Check directly whether the supplied pairs cover every canonical edge."""
    _, row_fibers, column_fibers, canonical_edges = _canonical_edge_data(
        n_vertices_per_side, complement
    )
    materialized = tuple(pairs)
    return all(
        any(
            pair_covers_canonical_edge(
                row_fibers[u], column_fibers[v], e_set, h_set
            )
            for e_set, h_set in materialized
        )
        for u, v in canonical_edges
    )


def _maximal_masks(masks: Iterable[int]) -> list[int]:
    """Discard pair masks contained in another pair mask."""
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
    """Return the exact canonical cover number for a tiny bipartite graph.

    Each complement element has four membership states with respect to a pair
    (E,H): neither, E only, H only, or both. We enumerate all 4^|U| states,
    deduplicate the induced canonical-edge coverage masks, remove dominated
    masks, then solve the remaining set-cover instance exactly by BFS.
    """
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
            f"strict exhaustive-search guard: |U|={len(complement)} exceeds "
            f"max_complement_edges={max_complement_edges}"
        )

    ordered_u, row_fibers, column_fibers, canonical_edges = _canonical_edge_data(
        n_vertices_per_side, complement
    )

    if not canonical_edges:
        return CanonicalCoverResult(
            n_vertices_per_side,
            len(ordered_u),
            0,
            0,
            0,
        )

    masks: set[int] = set()
    # state 0: neither, 1: E, 2: H, 3: both
    for states in product(range(4), repeat=len(ordered_u)):
        e_set = frozenset(i for i, state in enumerate(states) if state & 1)
        h_set = frozenset(i for i, state in enumerate(states) if state & 2)
        mask = 0
        for bit, (u, v) in enumerate(canonical_edges):
            if pair_covers_canonical_edge(
                row_fibers[u], column_fibers[v], e_set, h_set
            ):
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
    return exact_canonical_cover_number(
        n_vertices_per_side,
        neq_complement(n_vertices_per_side),
    )


def expected_neq_cover(n_vertices_per_side: int) -> int:
    """Finite coding baseline; equals log2(N) on source-supported N=2^n."""
    return ceil(log2(n_vertices_per_side))


if __name__ == "__main__":
    for n_vertices in range(2, 6):
        result = neq_calibration(n_vertices)
        print(
            n_vertices,
            result.minimum_pairs,
            expected_neq_cover(n_vertices),
            result,
        )
