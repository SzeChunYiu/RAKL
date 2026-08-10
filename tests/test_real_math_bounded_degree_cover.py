from __future__ import annotations

import importlib.util
from itertools import combinations
from math import ceil, log2
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
FALSIFICATION = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
)
PATH = FALSIFICATION / "bounded_degree_cover.py"
FULL_PATH = FALSIFICATION / "full_cover_oracle.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bounded = _load("bounded_degree_cover", PATH)
full = _load("full_cover_oracle_for_degree", FULL_PATH)


def test_permuted_perfect_matching_reconstructs_exactly() -> None:
    matching = {(0, 2), (1, 0), (2, 3), (3, 1)}
    witness = bounded.matching_intersection_witness(4, matching)

    assert witness.reconstructed == frozenset(matching)
    assert witness.perfect_extension == frozenset(matching)
    assert witness.code_bits == 2
    assert witness.counted_intersections == 3


def test_partial_non_power_of_two_matching_respects_c014_bound() -> None:
    matching = {(0, 4), (2, 1), (4, 3)}
    witness = bounded.matching_intersection_witness(5, matching)

    assert witness.reconstructed == frozenset(matching)
    assert witness.code_bits == 3
    assert witness.counted_intersections == 7
    assert witness.counted_intersections <= 2 * ceil(log2(5)) + 1


def test_two_matching_cycle_union_reconstructs_exactly() -> None:
    first = {(0, 0), (1, 1), (2, 2), (3, 3)}
    second = {(0, 1), (1, 2), (2, 3), (3, 0)}
    reconstructed, cost = bounded.reconstruct_matching_union(4, [first, second])

    assert reconstructed == frozenset(first | second)
    assert cost == 6
    assert cost <= 2 * (2 * ceil(log2(4)) + 1)


def test_exact_full_cover_respects_c014_on_every_nontrivial_2x2_graph() -> None:
    ambient = {(u, v) for u in range(2) for v in range(2)}
    ordered = sorted(ambient)
    for complement_size in range(1, 4):
        for complement_tuple in combinations(ordered, complement_size):
            complement = set(complement_tuple)
            graph = ambient - complement
            degree = max(
                max(sum((u, v) in graph for v in range(2)) for u in range(2)),
                max(sum((u, v) in graph for u in range(2)) for v in range(2)),
            )
            result = full.exact_full_cover_number(2, complement)
            assert result.minimum_pairs <= degree * (2 * ceil(log2(2)) + 1)


def test_duplicate_left_endpoint_fails_closed() -> None:
    with pytest.raises(ValueError, match="duplicate left"):
        bounded.matching_intersection_witness(4, {(0, 0), (0, 1)})


def test_duplicate_right_endpoint_fails_closed() -> None:
    with pytest.raises(ValueError, match="duplicate right"):
        bounded.matching_intersection_witness(4, {(0, 0), (1, 0)})


def test_union_decomposition_requires_edge_disjoint_matchings() -> None:
    with pytest.raises(ValueError, match="edge-disjoint"):
        bounded.reconstruct_matching_union(3, [{(0, 0)}, {(0, 0)}])


def test_matching_must_be_nonempty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        bounded.matching_intersection_witness(3, set())
