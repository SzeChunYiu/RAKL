"""Executable witness construction for C014 bounded-degree cover pruning.

This module checks the matching construction behind the intersection-complexity
upper bound.  It constructs actual subsets of [N] x [N] using the same unions
and intersections as the proof and reports only the number of intersections.
It is finite regression evidence, not an asymptotic proof certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable


Edge = tuple[int, int]


@dataclass(frozen=True)
class MatchingWitness:
    n_vertices_per_side: int
    matching: frozenset[Edge]
    perfect_extension: frozenset[Edge]
    reconstructed: frozenset[Edge]
    code_bits: int
    counted_intersections: int


def _validate_n(n_vertices_per_side: int) -> None:
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")


def _validate_matching(n_vertices_per_side: int, matching: Iterable[Edge]) -> tuple[Edge, ...]:
    _validate_n(n_vertices_per_side)
    edges = tuple(matching)
    if not edges:
        raise ValueError("matching must be non-empty")
    for u, v in edges:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("matching edge lies outside the requested bipartite graph")
    left = [u for u, _ in edges]
    right = [v for _, v in edges]
    if len(set(left)) != len(left):
        raise ValueError("matching contains a duplicate left endpoint")
    if len(set(right)) != len(right):
        raise ValueError("matching contains a duplicate right endpoint")
    return edges


def extend_to_perfect_matching(
    n_vertices_per_side: int, matching: Iterable[Edge]
) -> tuple[Edge, ...]:
    """Deterministically extend a partial matching inside K_{N,N}."""

    edges = _validate_matching(n_vertices_per_side, matching)
    used_left = {u for u, _ in edges}
    used_right = {v for _, v in edges}
    missing_left = [u for u in range(n_vertices_per_side) if u not in used_left]
    missing_right = [v for v in range(n_vertices_per_side) if v not in used_right]
    assert len(missing_left) == len(missing_right)
    return tuple(edges) + tuple(zip(missing_left, missing_right, strict=True))


def _row(n: int, u: int) -> set[Edge]:
    return {(u, v) for v in range(n)}


def _column(n: int, v: int) -> set[Edge]:
    return {(u, v) for u in range(n)}


def matching_intersection_witness(
    n_vertices_per_side: int, matching: Iterable[Edge]
) -> MatchingWitness:
    """Reconstruct a matching using <= 2 ceil(log2 N)+1 intersections."""

    target = frozenset(_validate_matching(n_vertices_per_side, matching))
    perfect = tuple(extend_to_perfect_matching(n_vertices_per_side, target))
    n = n_vertices_per_side
    k = ceil(log2(n))

    # Give each matched pair one distinct code.  The code attached to a left
    # endpoint equals the code attached to its perfect-matching partner.
    left_code: dict[int, int] = {}
    right_code: dict[int, int] = {}
    for code, (u, v) in enumerate(perfect):
        left_code[u] = code
        right_code[v] = code

    equality_bits: list[set[Edge]] = []
    counted = 0
    for bit in range(k):
        rows_one: set[Edge] = set()
        rows_zero: set[Edge] = set()
        columns_one: set[Edge] = set()
        columns_zero: set[Edge] = set()
        for u in range(n):
            (rows_one if (left_code[u] >> bit) & 1 else rows_zero).update(_row(n, u))
        for v in range(n):
            (columns_one if (right_code[v] >> bit) & 1 else columns_zero).update(_column(n, v))

        a_bit = rows_one | columns_zero
        b_bit = rows_zero | columns_one
        equality_bits.append(a_bit & b_bit)
        counted += 1

    reconstructed_perfect = set(equality_bits[0])
    for equality_bit in equality_bits[1:]:
        reconstructed_perfect &= equality_bit
        counted += 1

    if frozenset(reconstructed_perfect) != frozenset(perfect):
        raise AssertionError("binary-code construction failed to recover the perfect matching")

    if len(target) == n:
        reconstructed = reconstructed_perfect
    else:
        active_rows: set[Edge] = set()
        active_columns: set[Edge] = set()
        for u, v in target:
            active_rows.update(_row(n, u))
            active_columns.update(_column(n, v))
        active_rectangle = active_rows & active_columns
        counted += 1
        reconstructed = reconstructed_perfect & active_rectangle
        counted += 1

    if frozenset(reconstructed) != target:
        raise AssertionError("partial-matching mask failed to recover the target matching")

    return MatchingWitness(
        n_vertices_per_side=n,
        matching=target,
        perfect_extension=frozenset(perfect),
        reconstructed=frozenset(reconstructed),
        code_bits=k,
        counted_intersections=counted,
    )


def reconstruct_matching_union(
    n_vertices_per_side: int, matchings: Iterable[Iterable[Edge]]
) -> tuple[frozenset[Edge], int]:
    """Construct a union of supplied matchings and add their intersection costs."""

    union: set[Edge] = set()
    cost = 0
    for matching in matchings:
        witness = matching_intersection_witness(n_vertices_per_side, matching)
        if union.intersection(witness.matching):
            raise ValueError("matching decomposition must be edge-disjoint")
        union.update(witness.reconstructed)
        cost += witness.counted_intersections
    if not union:
        raise ValueError("at least one non-empty matching is required")
    return frozenset(union), cost
