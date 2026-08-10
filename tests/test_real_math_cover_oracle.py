from __future__ import annotations

import importlib.util
from itertools import combinations
from pathlib import Path
import sys

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "canonical_cover_oracle.py"
)

spec = importlib.util.spec_from_file_location("canonical_cover_oracle", MODULE_PATH)
assert spec is not None and spec.loader is not None
oracle = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = oracle
spec.loader.exec_module(oracle)


def _subsets(universe: frozenset[int]) -> list[frozenset[int]]:
    items = tuple(sorted(universe))
    return [
        frozenset(choice)
        for size in range(len(items) + 1)
        for choice in combinations(items, size)
    ]


def test_c005_pair_coverage_orientations() -> None:
    row = frozenset({0})
    column = frozenset({1})

    assert oracle.pair_covers_canonical_edge(
        row, column, frozenset({0}), frozenset({1})
    )
    assert oracle.pair_covers_canonical_edge(
        row, column, frozenset({1}), frozenset({0})
    )
    assert not oracle.pair_covers_canonical_edge(
        row, column, frozenset({0, 1}), frozenset({1})
    )
    assert not oracle.pair_covers_canonical_edge(
        row, column, frozenset({0}), frozenset({0})
    )


def test_overlap_deletion_can_destroy_canonical_coverage() -> None:
    # C007 exact counterexample. A non-singleton row fibre can straddle
    # E-only and E∩H. The original pair covers, but deleting E∩H destroys
    # full containment of that generator.
    row = frozenset({0, 1})
    column = frozenset({2})
    e_set = frozenset({0, 1})
    h_set = frozenset({1, 2})

    assert oracle.pair_covers_canonical_edge(row, column, e_set, h_set)
    assert not oracle.pair_covers_canonical_edge(
        row,
        column,
        e_set - h_set,
        h_set - e_set,
    )


def test_union_normalization_preserves_all_tiny_covered_fibres() -> None:
    # Exhaustively regression-test C008-L1 on every nonempty row/column fibre
    # and every pair (E,H) over a four-element universe.
    universe = frozenset(range(4))
    subsets = _subsets(universe)
    nonempty = [subset for subset in subsets if subset]

    for row in nonempty:
        for column in nonempty:
            for e_set in subsets:
                for h_set in subsets:
                    if not oracle.pair_covers_canonical_edge(
                        row, column, e_set, h_set
                    ):
                        continue
                    e_norm, h_norm = oracle.union_normalize_pair(
                        universe, e_set, h_set
                    )
                    assert e_norm | h_norm == universe
                    assert oracle.pair_covers_canonical_edge(
                        row, column, e_norm, h_norm
                    )


def test_perfect_matching_ceiling_construction_for_all_n3_supersets() -> None:
    # C009 construction. Exhaust every 3x3 complement graph containing the
    # diagonal perfect matching. Two code coordinates must cover every
    # canonical G-edge, regardless of which extra complement edges are added.
    n_vertices = 3
    matching = {(i, i) for i in range(n_vertices)}
    off_diagonal = [
        (u, v)
        for u in range(n_vertices)
        for v in range(n_vertices)
        if u != v
    ]

    for extra_size in range(len(off_diagonal) + 1):
        for extra in combinations(off_diagonal, extra_size):
            complement = matching | set(extra)
            ordered_u, row_fibers, column_fibers, canonical_edges = (
                oracle._canonical_edge_data(n_vertices, complement)
            )
            index = {edge: i for i, edge in enumerate(ordered_u)}
            matching_indices = {row: index[(row, row)] for row in range(n_vertices)}
            nonmatching_indices = frozenset(
                i for i, edge in enumerate(ordered_u) if edge not in matching
            )

            pairs: list[tuple[frozenset[int], frozenset[int]]] = []
            for bit in range(2):
                p_set = frozenset(
                    matching_indices[row]
                    for row in range(n_vertices)
                    if ((row >> bit) & 1) == 0
                )
                m_set = frozenset(
                    matching_indices[row]
                    for row in range(n_vertices)
                    if ((row >> bit) & 1) == 1
                )
                pairs.append(
                    (p_set | nonmatching_indices, m_set | nonmatching_indices)
                )

            for u, v in canonical_edges:
                assert any(
                    oracle.pair_covers_canonical_edge(
                        row_fibers[u], column_fibers[v], e_set, h_set
                    )
                    for e_set, h_set in pairs
                )


def test_hall_deficient_complement_can_have_smaller_canonical_cover() -> None:
    # C010 star-biclique partition example. The 3x3 complement has maximum
    # matching size 2 and no perfect matching:
    # L0={0,1}, R0={0}; L1={2}, R1={1,2}.
    complement = {(0, 0), (1, 0), (2, 1), (2, 2)}
    result = oracle.exact_canonical_cover_number(3, complement)
    assert result.canonical_edges > 0
    assert result.minimum_pairs == 1


def test_neq_source_calibration_on_powers_of_two() -> None:
    assert oracle.neq_calibration(2).minimum_pairs == 1
    assert oracle.neq_calibration(4).minimum_pairs == 2


def test_neq_finite_coding_sanity() -> None:
    assert oracle.neq_calibration(3).minimum_pairs == 2
    assert oracle.neq_calibration(5).minimum_pairs == 3


def test_exhaustive_guard_is_fail_closed() -> None:
    complement = {(u, v) for u in range(4) for v in range(4) if u != v}
    with pytest.raises(ValueError, match="strict exhaustive-search guard"):
        oracle.exact_canonical_cover_number(
            4,
            complement,
            max_complement_edges=4,
        )
