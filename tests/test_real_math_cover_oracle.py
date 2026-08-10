from __future__ import annotations

import importlib.util
from itertools import product
from math import ceil, log2
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


def test_c005_pair_coverage_orientations() -> None:
    row = frozenset({0})
    column = frozenset({1})
    assert oracle.pair_covers_canonical_edge(row, column, frozenset({0}), frozenset({1}))
    assert oracle.pair_covers_canonical_edge(row, column, frozenset({1}), frozenset({0}))
    assert not oracle.pair_covers_canonical_edge(row, column, frozenset({0, 1}), frozenset({1}))
    assert not oracle.pair_covers_canonical_edge(row, column, frozenset({0}), frozenset({0}))


def test_neq_source_calibration_on_powers_of_two() -> None:
    assert oracle.neq_calibration(2).minimum_pairs == 1
    assert oracle.neq_calibration(4).minimum_pairs == 2


def test_neq_finite_coding_sanity() -> None:
    assert oracle.neq_calibration(3).minimum_pairs == 2
    assert oracle.neq_calibration(5).minimum_pairs == 3


def test_c007_matching_witness_covers_neq() -> None:
    for n_vertices in range(2, 6):
        complement = oracle.neq_complement(n_vertices)
        pairs = oracle.perfect_matching_canonical_cover_pairs(n_vertices, complement, complement)
        assert len(pairs) == oracle.expected_neq_cover(n_vertices)
        assert oracle.canonical_pairs_cover_all_edges(n_vertices, complement, pairs)


def test_c007_matching_witness_survives_extra_complement_edges() -> None:
    n_vertices = 4
    matching = {(u, u) for u in range(n_vertices)}
    complement = matching | {(u, (u + 1) % n_vertices) for u in range(n_vertices)}
    pairs = oracle.perfect_matching_canonical_cover_pairs(n_vertices, complement, matching)
    assert len(pairs) == 2
    assert oracle.canonical_pairs_cover_all_edges(n_vertices, complement, pairs)
    assert oracle.exact_canonical_cover_number(n_vertices, complement).minimum_pairs == 2


def test_c007_rejects_nonperfect_matching() -> None:
    complement = {(0, 0), (1, 1), (2, 2)}
    with pytest.raises(ValueError, match="exactly one edge per row and column"):
        oracle.perfect_matching_canonical_cover_pairs(3, complement, {(0, 0), (1, 1)})


def test_c009_matching_number_witness_covers_neq() -> None:
    for n_vertices in range(2, 7):
        complement = oracle.neq_complement(n_vertices)
        pairs = oracle.matching_number_canonical_cover_pairs(n_vertices, complement)
        assert len(pairs) == ceil(log2(n_vertices))
        assert oracle.canonical_pairs_cover_all_edges(n_vertices, complement, pairs)


def test_c009_hall_deficient_star_has_empty_canonical_family() -> None:
    complement = {(0, 0), (0, 1), (0, 2), (0, 3)}
    pairs = oracle.matching_number_canonical_cover_pairs(4, complement)
    assert pairs == []
    assert oracle.canonical_pairs_cover_all_edges(4, complement, pairs)
    assert oracle.exact_canonical_cover_number(4, complement).minimum_pairs == 0


def test_c009_witness_exhaustive_on_every_three_by_three_complement() -> None:
    n_vertices = 3
    edges = [(u, v) for u, v in product(range(n_vertices), repeat=2)]
    for mask in range(1, (1 << len(edges)) - 1):
        complement = {edge for bit, edge in enumerate(edges) if (mask >> bit) & 1}
        matching_size = len(oracle._maximum_bipartite_matching(n_vertices, complement))
        pairs = oracle.matching_number_canonical_cover_pairs(n_vertices, complement)
        expected = 0 if matching_size <= 1 else ceil(log2(matching_size))
        assert len(pairs) == expected
        assert oracle.canonical_pairs_cover_all_edges(n_vertices, complement, pairs)


def test_c009_witness_covers_c008_full_cover_separator_canonical_subfamily() -> None:
    complement = {(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)}
    pairs = oracle.matching_number_canonical_cover_pairs(3, complement)
    assert oracle.canonical_pairs_cover_all_edges(3, complement, pairs)
    assert len(pairs) <= ceil(log2(3))


def test_exhaustive_guard_is_fail_closed() -> None:
    complement = {(u, v) for u in range(4) for v in range(4) if u != v}
    with pytest.raises(ValueError, match="strict exhaustive-search guard"):
        oracle.exact_canonical_cover_number(4, complement, max_complement_edges=4)
