from __future__ import annotations

import importlib.util
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
    / "coordinate_combiner_cover.py"
)

spec = importlib.util.spec_from_file_location("coordinate_combiner_cover", MODULE_PATH)
assert spec is not None and spec.loader is not None
combiner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = combiner
spec.loader.exec_module(combiner)


BASE_GRAPH = {(0, 0), (0, 1), (1, 0)}  # nontrivial 2x2 local predicate


def test_dual_rail_exact_for_or_and_combiners() -> None:
    for arity in range(1, 5):
        assert combiner.verify_dual_rail_simulation(
            2, BASE_GRAPH, arity, combiner.fold_or(arity)
        )
        assert combiner.verify_dual_rail_simulation(
            2, BASE_GRAPH, arity, combiner.fold_and(arity)
        )


def test_dual_rail_exact_for_one_shared_logic_gadget_as_formula() -> None:
    formula = combiner.xor2(combiner.input_bit(0), combiner.input_bit(1))
    assert combiner.verify_dual_rail_simulation(2, BASE_GRAPH, 2, formula)
    assert combiner.counted_binary_gates(formula) == 3


def test_constructive_bound_for_linear_or_and_formulas() -> None:
    for arity in range(1, 9):
        expected = arity * 4 + max(0, arity - 1)
        assert combiner.constructive_intersection_bound(
            2, arity, combiner.fold_or(arity)
        ) == expected
        assert combiner.constructive_intersection_bound(
            2, arity, combiner.fold_and(arity)
        ) == expected


def test_formula_index_guard_fails_closed() -> None:
    with pytest.raises(ValueError, match="outside the declared arity"):
        combiner.constructive_intersection_bound(2, 2, combiner.input_bit(2))


def test_base_graph_ground_guard_fails_closed() -> None:
    with pytest.raises(ValueError, match="outside the local ground set"):
        combiner.verify_dual_rail_simulation(2, {(2, 0)}, 1, combiner.input_bit(0))
