"""Executable witness for the C011 coordinate-product cover ceiling.

The construction uses the Cavalar--Oliveira graph-cover model with row/column
generators.  For a fixed bipartite base graph G0, define a coupled product by
making a product edge absent exactly when *every* coordinate is absent in G0.
Equivalently, the complement relation is the Cartesian product U0^t.

A local disjoint generator-separating pair can then be lifted to a cylinder in
one coordinate.  One lifted copy per local pair per coordinate separates every
relevant graph edge, giving a cover of size at most t*sigma(G0).

This module checks the sufficient generator-separation witness.  It is proof
regression and route falsification only, not an asymptotic circuit lower bound
or a novelty certificate.
"""

from __future__ import annotations

from itertools import product
from typing import Iterable


Edge = tuple[int, int]
Pair = tuple[frozenset[Edge], frozenset[Edge]]


def _validate_base(base_n: int, base_complement: set[Edge]) -> None:
    if base_n < 2:
        raise ValueError("base_n must be at least 2")
    if not base_complement:
        raise ValueError("base complement must be nonempty")
    for u, v in base_complement:
        if not (0 <= u < base_n and 0 <= v < base_n):
            raise ValueError("base complement edge lies outside the base graph")


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
    """Check the disjoint generator-separation sufficient condition."""
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


def coordinate_product_complement(
    base_n: int,
    base_complement: set[Edge],
    copies: int,
) -> tuple[int, set[Edge], tuple[tuple[int, ...], ...]]:
    """Return the complement relation U0^copies on n^copies vertices per side."""
    _validate_base(base_n, base_complement)
    if copies < 1:
        raise ValueError("copies must be positive")

    vertices = tuple(product(range(base_n), repeat=copies))
    complement: set[Edge] = set()
    for left_index, left in enumerate(vertices):
        for right_index, right in enumerate(vertices):
            if all(
                (left[coordinate], right[coordinate]) in base_complement
                for coordinate in range(copies)
            ):
                complement.add((left_index, right_index))
    return len(vertices), complement, vertices


def coordinate_product_generator_separating_pairs(
    base_n: int,
    base_complement: set[Edge],
    base_pairs: Iterable[Pair],
    copies: int,
) -> tuple[int, set[Edge], list[Pair]]:
    """Lift a local disjoint cover to coordinate cylinders.

    If the base family has k pairs, the returned family has k*copies pairs.
    Preconditions and the global generator-separation invariant are checked.
    """
    local_pairs = tuple(base_pairs)
    if not generator_separating_pairs_cover_all_relevant_edges(
        base_n, base_complement, local_pairs
    ):
        raise ValueError("base pairs do not generator-separate every relevant base edge")

    total_n, complement, vertices = coordinate_product_complement(
        base_n, base_complement, copies
    )
    lifted: list[Pair] = []

    for coordinate in range(copies):
        for local_e, local_h in local_pairs:
            global_e = frozenset(
                edge
                for edge in complement
                if (vertices[edge[0]][coordinate], vertices[edge[1]][coordinate])
                in local_e
            )
            global_h = frozenset(
                edge
                for edge in complement
                if (vertices[edge[0]][coordinate], vertices[edge[1]][coordinate])
                in local_h
            )
            if global_e & global_h:
                raise RuntimeError("coordinate-cylinder lift lost disjointness")
            lifted.append((global_e, global_h))

    if not generator_separating_pairs_cover_all_relevant_edges(
        total_n, complement, lifted
    ):
        raise RuntimeError("C011 coordinate-product witness failed its invariant")
    return total_n, complement, lifted


def c008_base_complement() -> set[Edge]:
    return {(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)}


def c008_disjoint_generator_cover() -> tuple[Pair, Pair]:
    a = (0, 0)
    b = (0, 1)
    c = (1, 0)
    d = (1, 2)
    e = (2, 1)
    return (
        (frozenset({a, b}), frozenset({d})),
        (frozenset({a, c, d}), frozenset({b, e})),
    )


def c008_coordinate_product_witness(copies: int) -> tuple[int, set[Edge], list[Pair]]:
    return coordinate_product_generator_separating_pairs(
        3,
        c008_base_complement(),
        c008_disjoint_generator_cover(),
        copies,
    )


def c011_bound(copies: int) -> int:
    if copies < 1:
        raise ValueError("copies must be positive")
    return 2 * copies
