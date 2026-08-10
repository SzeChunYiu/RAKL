"""Executable witness for the C010 block-sum cover ceiling.

The source model is Cavalar--Oliveira graph cover complexity with row/column
generators.  A disjoint pair (E,H) that contains the complement row and
column fibres of a graph edge on opposite sides covers *every* semi-filter
above that edge, because E,H then belong to the semi-filter while
E intersection H = empty does not.

This module constructs such pairs for block-diagonal complement sums.  It is
an executable proof witness and counterexample-to-composition oracle, not a
proof of an asymptotic circuit lower bound or a novelty certificate.
"""

from __future__ import annotations

from math import ceil, log2
from typing import Iterable


Edge = tuple[int, int]
Pair = tuple[frozenset[Edge], frozenset[Edge]]


def _fibres(n_vertices_per_side: int, complement: set[Edge]) -> tuple[dict[int, set[Edge]], dict[int, set[Edge]]]:
    rows = {
        u: {edge for edge in complement if edge[0] == u}
        for u in range(n_vertices_per_side)
    }
    columns = {
        v: {edge for edge in complement if edge[1] == v}
        for v in range(n_vertices_per_side)
    }
    return rows, columns


def generator_separating_pairs_cover_all_relevant_edges(
    n_vertices_per_side: int,
    complement: set[Edge],
    pairs: Iterable[Pair],
) -> bool:
    """Check the sufficient disjoint generator-separation condition for full cover.

    Graph edges with an empty complement row or column fibre have no
    semi-filter above them under Definition 19, because the empty set would
    be required to belong to the semi-filter.  They are therefore skipped.
    """
    materialized = tuple(pairs)
    for e_set, h_set in materialized:
        if e_set & h_set:
            raise ValueError("generator-separating pairs must be disjoint")
        if not (e_set | h_set) <= complement:
            raise ValueError("pair contains an edge outside the complement ground set")

    rows, columns = _fibres(n_vertices_per_side, complement)
    for u in range(n_vertices_per_side):
        for v in range(n_vertices_per_side):
            if (u, v) in complement:
                continue
            row = rows[u]
            column = columns[v]
            if not row or not column:
                continue
            if not any(
                (row <= e_set and column <= h_set)
                or (row <= h_set and column <= e_set)
                for e_set, h_set in materialized
            ):
                return False
    return True


def block_diagonal_complement(
    base_n: int,
    base_complement: set[Edge],
    copies: int,
) -> tuple[int, set[Edge]]:
    """Return t disjoint complement blocks on a square (t*base_n)-vertex side."""
    if base_n < 1 or copies < 1:
        raise ValueError("base_n and copies must be positive")
    for u, v in base_complement:
        if not (0 <= u < base_n and 0 <= v < base_n):
            raise ValueError("base complement edge is outside its block")
    combined: set[Edge] = set()
    for block in range(copies):
        offset = block * base_n
        combined.update((offset + u, offset + v) for u, v in base_complement)
    return base_n * copies, combined


def block_sum_generator_separating_pairs(
    base_n: int,
    base_complement: set[Edge],
    base_pairs: Iterable[Pair],
    copies: int,
) -> tuple[int, set[Edge], list[Pair]]:
    """Multiplex a local disjoint cover and add binary block-separation pairs.

    Preconditions are checked executably.  The returned family has
    ``len(base_pairs) + ceil(log2(copies))`` pairs and generator-separates
    every relevant edge of the block-sum graph.
    """
    local_pairs = tuple(base_pairs)
    if not generator_separating_pairs_cover_all_relevant_edges(
        base_n, base_complement, local_pairs
    ):
        raise ValueError("base pairs do not generator-separate every relevant base edge")

    total_n, complement = block_diagonal_complement(base_n, base_complement, copies)
    global_pairs: list[Pair] = []

    # Multiplex the j-th local pair over every block.  Disjointness survives
    # because block ground sets are disjoint and each local pair is disjoint.
    for local_e, local_h in local_pairs:
        global_e: set[Edge] = set()
        global_h: set[Edge] = set()
        for block in range(copies):
            offset = block * base_n
            global_e.update((offset + u, offset + v) for u, v in local_e)
            global_h.update((offset + u, offset + v) for u, v in local_h)
        global_pairs.append((frozenset(global_e), frozenset(global_h)))

    # Cross-block graph edges are handled by binary block codes.  Each pair
    # partitions entire complement blocks, so the endpoint fibres of two
    # differently coded blocks are placed on opposite sides.
    bit_count = ceil(log2(copies)) if copies > 1 else 0
    for bit in range(bit_count):
        global_e: set[Edge] = set()
        global_h: set[Edge] = set()
        for block in range(copies):
            offset = block * base_n
            target = global_h if ((block >> bit) & 1) else global_e
            target.update((offset + u, offset + v) for u, v in base_complement)
        global_pairs.append((frozenset(global_e), frozenset(global_h)))

    if not generator_separating_pairs_cover_all_relevant_edges(
        total_n, complement, global_pairs
    ):
        raise RuntimeError("C010 construction failed its generator-separation invariant")
    return total_n, complement, global_pairs


def c008_base_complement() -> set[Edge]:
    return {(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)}


def c008_disjoint_generator_cover() -> tuple[Pair, Pair]:
    """A two-pair disjoint full-cover witness for the merged C008 gadget."""
    a = (0, 0)
    b = (0, 1)
    c = (1, 0)
    d = (1, 2)
    e = (2, 1)
    return (
        (frozenset({a, b}), frozenset({d})),
        (frozenset({a, c, d}), frozenset({b, e})),
    )


def c008_block_sum_witness(copies: int) -> tuple[int, set[Edge], list[Pair]]:
    return block_sum_generator_separating_pairs(
        3, c008_base_complement(), c008_disjoint_generator_cover(), copies
    )


def c010_bound(copies: int) -> int:
    if copies < 1:
        raise ValueError("copies must be positive")
    return 2 + (ceil(log2(copies)) if copies > 1 else 0)
