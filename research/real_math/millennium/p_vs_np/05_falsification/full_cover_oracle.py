"""Exact tiny oracle for full graph cover complexity.

This implements Definitions 18--21 of Cavalar--Oliveira, ECCC TR25-033,
for bipartite graph complexity.  It enumerates every semi-filter over the
complement ground set, every candidate pair (E,H), and solves the resulting
finite set-cover instance exactly.

The implementation is deliberately guarded at |U| <= 5.  Its outputs are
finite computational evidence and regression witnesses only; they do not
prove asymptotic circuit lower bounds or novelty.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


Edge = tuple[int, int]
Pair = tuple[frozenset[int], frozenset[int]]


@dataclass(frozen=True)
class FullCoverResult:
    n_vertices_per_side: int
    complement_edges: int
    relevant_semifilters: int
    distinct_maximal_pair_masks: int
    minimum_pairs: int


def _validate_graph(n_vertices_per_side: int, complement: set[Edge]) -> None:
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    limit = n_vertices_per_side * n_vertices_per_side
    for u, v in complement:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("complement edge lies outside the requested bipartite ground set")
    if len(complement) == 0 or len(complement) == limit:
        raise ValueError("use a nontrivial graph with a nonempty complement")


def _is_comparable(a: int, b: int) -> bool:
    return (a & b) == a or (a & b) == b


@lru_cache(maxsize=None)
def _nonempty_antichains(universe_size: int) -> tuple[tuple[int, ...], ...]:
    """Enumerate all nonempty antichains of nonempty subsets of [universe_size]."""
    subsets = tuple(range(1, 1 << universe_size))
    answer: list[tuple[int, ...]] = []

    def visit(start: int, chosen: list[int]) -> None:
        if chosen:
            answer.append(tuple(chosen))
        for index in range(start, len(subsets)):
            candidate = subsets[index]
            if all(not _is_comparable(candidate, existing) for existing in chosen):
                chosen.append(candidate)
                visit(index + 1, chosen)
                chosen.pop()

    visit(0, [])
    return tuple(answer)


def _filter_contains(minimals: tuple[int, ...], subset: int) -> bool:
    return any((minimal & subset) == minimal for minimal in minimals)


def _graph_masks(
    n_vertices_per_side: int, complement: set[Edge]
) -> tuple[list[Edge], list[int], list[int], list[Edge]]:
    ordered_u = sorted(complement)
    index = {edge: i for i, edge in enumerate(ordered_u)}
    row_masks = [0] * n_vertices_per_side
    column_masks = [0] * n_vertices_per_side
    for (u, v), bit in index.items():
        row_masks[u] |= 1 << bit
        column_masks[v] |= 1 << bit
    graph_edges = [
        (u, v)
        for u in range(n_vertices_per_side)
        for v in range(n_vertices_per_side)
        if (u, v) not in complement
    ]
    return ordered_u, row_masks, column_masks, graph_edges


def _relevant_semifilters(
    n_vertices_per_side: int, complement: set[Edge]
) -> tuple[tuple[int, ...], ...]:
    ordered_u, row_masks, column_masks, graph_edges = _graph_masks(
        n_vertices_per_side, complement
    )
    filters: list[tuple[int, ...]] = []
    for minimals in _nonempty_antichains(len(ordered_u)):
        for u, v in graph_edges:
            row = row_masks[u]
            column = column_masks[v]
            # Requiring an empty generator would require the empty set to
            # belong to the semi-filter, which Definition 18 forbids.
            if not row or not column:
                continue
            if _filter_contains(minimals, row) and _filter_contains(minimals, column):
                filters.append(minimals)
                break
    return tuple(filters)


def pair_covers_semifilter(
    minimals: tuple[int, ...], e_set: int, h_set: int
) -> bool:
    """Definition 20: F fails to preserve (E,H)."""
    return (
        _filter_contains(minimals, e_set)
        and _filter_contains(minimals, h_set)
        and not _filter_contains(minimals, e_set & h_set)
    )


def _maximal_masks(masks: Iterable[int]) -> list[int]:
    maximal: list[int] = []
    for mask in sorted(set(masks), key=int.bit_count, reverse=True):
        if not any(mask | other == other for other in maximal):
            maximal.append(mask)
    return maximal


def exact_full_cover_number(
    n_vertices_per_side: int,
    complement: set[Edge],
    *,
    max_complement_edges: int = 5,
) -> FullCoverResult:
    """Return the exact full semi-filter cover number for a tiny graph."""
    _validate_graph(n_vertices_per_side, complement)
    if len(complement) > max_complement_edges:
        raise ValueError(
            f"strict exhaustive-search guard: |U|={len(complement)} exceeds "
            f"max_complement_edges={max_complement_edges}"
        )

    filters = _relevant_semifilters(n_vertices_per_side, complement)
    if not filters:
        return FullCoverResult(
            n_vertices_per_side, len(complement), 0, 0, 0
        )

    universe_size = len(complement)
    masks: set[int] = set()
    for e_set in range(1 << universe_size):
        for h_set in range(1 << universe_size):
            mask = 0
            for bit, minimals in enumerate(filters):
                if pair_covers_semifilter(minimals, e_set, h_set):
                    mask |= 1 << bit
            if mask:
                masks.add(mask)

    maximal = _maximal_masks(masks)
    full = (1 << len(filters)) - 1
    queue = deque([0])
    depth = {0: 0}
    while queue:
        current = queue.popleft()
        next_depth = depth[current] + 1
        for pair_mask in maximal:
            nxt = current | pair_mask
            if nxt == full:
                return FullCoverResult(
                    n_vertices_per_side,
                    len(complement),
                    len(filters),
                    len(maximal),
                    next_depth,
                )
            if nxt != current and nxt not in depth:
                depth[nxt] = next_depth
                queue.append(nxt)
    raise RuntimeError("semi-filter universe was not coverable; implementation invariant failed")


def pair_family_covers_all_relevant_semifilters(
    n_vertices_per_side: int,
    complement: set[Edge],
    pairs: Iterable[Pair],
) -> bool:
    """Check an explicit pair family against every relevant semi-filter."""
    ordered_u = sorted(complement)
    index = {edge: i for i, edge in enumerate(ordered_u)}
    encoded_pairs = tuple(
        (
            sum(1 << index[edge] for edge in e_set),
            sum(1 << index[edge] for edge in h_set),
        )
        for e_set, h_set in pairs
    )
    return all(
        any(pair_covers_semifilter(minimals, e_set, h_set) for e_set, h_set in encoded_pairs)
        for minimals in _relevant_semifilters(n_vertices_per_side, complement)
    )


def c008_gadget_complement() -> set[Edge]:
    """The 3x3 complement used by candidate C008."""
    return {(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)}


def c008_two_pair_witness() -> tuple[Pair, Pair]:
    a = (0, 0)
    b = (0, 1)
    c = (1, 0)
    d = (1, 2)
    e = (2, 1)
    return (
        (frozenset({a}), frozenset({b, d, e})),
        (frozenset({a, c, d}), frozenset({a, b, e})),
    )
