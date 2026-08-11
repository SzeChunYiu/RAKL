from __future__ import annotations

import importlib.util
from math import ceil, comb
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
    / "finite_state_cover_ceiling.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


finite_state = _load("finite_state_cover_ceiling", PATH)


def test_hamming_mod3_dfa_matches_direct_predicate() -> None:
    for t in range(1, 6):
        witness = finite_state.hamming_mod3_witness(t)
        assert witness.accepted == witness.direct_accepted
        assert witness.counted_intersections <= 8 * t
        assert witness.upper_bound_intersections == 8 * t


def test_hamming_parity_uses_generic_propagation() -> None:
    for t in range(1, 5):
        witness = finite_state.hamming_parity_witness(t)
        assert witness.accepted == witness.direct_accepted
        assert witness.counted_intersections <= 6 * t
        assert witness.upper_bound_intersections == 6 * t


def test_mod3_row_degree_matches_binomial_residue_count() -> None:
    for t in range(1, 9):
        expected = sum(comb(t, j) for j in range(t + 1) if j % 3 == 0)
        assert finite_state.hamming_mod3_row_degree(t) == expected


def test_mod3_graph_has_growing_forest_count_lower_bound() -> None:
    # Each forest on the 2N bipartite vertices has at most 2N-1 edges.
    # The bound is already double-digit by t=6 and grows rapidly thereafter.
    assert finite_state.hamming_mod3_arboricity_lower_bound(6) == 12
    assert finite_state.hamming_mod3_arboricity_lower_bound(7) == 22
    assert finite_state.hamming_mod3_arboricity_lower_bound(8) > 40


def test_symbol_sets_form_exact_partition() -> None:
    ambient, partitions = finite_state.xor_symbol_sets(4)
    for partition in partitions:
        assert partition[0].isdisjoint(partition[1])
        assert partition[0] | partition[1] == ambient


def test_malformed_dfa_fails_closed() -> None:
    ambient, partitions = finite_state.xor_symbol_sets(2)
    bad = finite_state.DFA(
        states=(0, 1),
        alphabet=(0, 1),
        start=0,
        accepting=frozenset({1}),
        transition={(0, 0): 0},
    )
    with pytest.raises(ValueError, match="transition map must be total"):
        finite_state.finite_state_witness(
            ambient=ambient,
            symbol_sets=partitions,
            dfa=bad,
            local_intersection_costs=[2, 2],
            direct_accepted=frozenset(),
        )


def test_overlapping_symbol_partition_fails_closed() -> None:
    ambient, partitions = finite_state.xor_symbol_sets(2)
    broken = [dict(partition) for partition in partitions]
    broken[0][1] = ambient
    with pytest.raises(ValueError, match="symbol sets overlap"):
        finite_state.finite_state_witness(
            ambient=ambient,
            symbol_sets=broken,
            dfa=finite_state.parity_dfa(),
            local_intersection_costs=[2, 2],
            direct_accepted=frozenset(),
        )


def test_finite_calibration_guard() -> None:
    with pytest.raises(ValueError, match="t <= 8"):
        finite_state.hamming_mod3_witness(9)
