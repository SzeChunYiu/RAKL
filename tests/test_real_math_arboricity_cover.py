from __future__ import annotations

import importlib.util
from math import ceil, log2
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "arboricity_cover.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


arboricity = _load("arboricity_cover", PATH)


def test_partial_map_right_to_left_reconstructs_non_power_of_two() -> None:
    edges = {(4, 0), (1, 2), (3, 4)}
    witness = arboricity.right_to_left_partial_function_witness(5, edges)

    assert witness.reconstructed == frozenset(edges)
    assert witness.direction == "R->L"
    assert witness.counted_intersections == 2 * ceil(log2(5))


def test_partial_map_left_to_right_reconstructs() -> None:
    edges = {(0, 3), (2, 1), (4, 0)}
    witness = arboricity.left_to_right_partial_function_witness(5, edges)

    assert witness.reconstructed == frozenset(edges)
    assert witness.direction == "L->R"
    assert witness.counted_intersections == 2 * ceil(log2(5))


def test_high_degree_star_is_cheap_despite_large_maximum_degree() -> None:
    n = 8
    star = {(0, v) for v in range(n)}
    witness = arboricity.forest_intersection_witness(n, star)

    assert witness.reconstructed == frozenset(star)
    assert witness.counted_intersections <= 4 * ceil(log2(n))
    assert witness.counted_intersections == 2 * ceil(log2(n))


def test_path_uses_both_parent_side_partial_functions() -> None:
    path = {(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)}
    witness = arboricity.forest_intersection_witness(4, path)

    assert witness.reconstructed == frozenset(path)
    assert witness.left_parent_edges
    assert witness.right_parent_edges
    assert witness.counted_intersections <= 4 * ceil(log2(4))


def test_disconnected_forest_reconstructs_exactly() -> None:
    forest = {(0, 0), (1, 0), (3, 3), (3, 4), (4, 4)}
    witness = arboricity.forest_intersection_witness(5, forest)

    assert witness.reconstructed == frozenset(forest)
    assert witness.counted_intersections <= 4 * ceil(log2(5))


def test_explicit_two_forest_partition_has_additive_bound() -> None:
    first = {(0, 0), (1, 0), (1, 1), (2, 1)}
    second = {(0, 2), (2, 2), (3, 2), (3, 3)}
    reconstructed, cost = arboricity.reconstruct_forest_union(4, [first, second])

    assert reconstructed == frozenset(first | second)
    assert cost <= 2 * 4 * ceil(log2(4))


def test_cycle_fails_closed_as_nonforest() -> None:
    cycle = {(0, 0), (1, 0), (1, 1), (0, 1)}
    with pytest.raises(ValueError, match="not a forest"):
        arboricity.forest_intersection_witness(3, cycle)


def test_non_function_on_unique_side_fails_closed() -> None:
    with pytest.raises(ValueError, match="right endpoint"):
        arboricity.right_to_left_partial_function_witness(4, {(0, 0), (1, 0)})

    with pytest.raises(ValueError, match="left endpoint"):
        arboricity.left_to_right_partial_function_witness(4, {(0, 0), (0, 1)})


def test_forest_partition_requires_edge_disjointness() -> None:
    with pytest.raises(ValueError, match="edge-disjoint"):
        arboricity.reconstruct_forest_union(4, [{(0, 0)}, {(0, 0)}])
