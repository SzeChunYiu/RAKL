from __future__ import annotations

import importlib.util
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
    / "symmetric_hamming_cover_ceiling.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


symmetric = _load("symmetric_hamming_cover_ceiling", PATH)


def test_arbitrary_weight_sets_reconstruct_exactly() -> None:
    cases = {
        1: {0},
        2: {1},
        3: {0, 2},
        4: {1, 3, 4},
        5: {0, 2, 5},
    }
    for t, weights in cases.items():
        witness = symmetric.symmetric_hamming_witness(t, weights)
        assert witness.accepted == witness.direct_accepted
        assert witness.intersection_count <= 80 * t


def test_growing_modulus_residue_predicates_are_exact() -> None:
    for t in range(2, 6):
        modulus = t
        weights = symmetric.residue_weights(t, modulus, {0, 1})
        witness = symmetric.symmetric_hamming_witness(t, weights)
        assert witness.accepted == witness.direct_accepted
        assert witness.intersection_count <= 80 * t


def test_exact_distance_and_threshold_predicates() -> None:
    exact = symmetric.symmetric_hamming_witness(5, {3})
    threshold = symmetric.symmetric_hamming_witness(
        5, symmetric.threshold_weights(5, 3)
    )

    assert all((x ^ y).bit_count() == 3 for x, y in exact.accepted)
    assert all((x ^ y).bit_count() >= 3 for x, y in threshold.accepted)


def test_population_count_bits_partition_ambient() -> None:
    for t in range(1, 6):
        witness = symmetric.symmetric_hamming_witness(t, range(t + 1))
        ambient = witness.accepted
        for pair in witness.weight_bits:
            assert pair.value.isdisjoint(pair.complement)
            assert pair.value | pair.complement == ambient


def test_empty_and_full_symmetric_predicates() -> None:
    empty = symmetric.symmetric_hamming_witness(4, set())
    full = symmetric.symmetric_hamming_witness(4, range(5))

    assert not empty.accepted
    assert len(full.accepted) == (1 << 4) ** 2


def test_invalid_weight_fails_closed() -> None:
    with pytest.raises(ValueError, match="accepted weights"):
        symmetric.symmetric_hamming_witness(4, {-1, 0})
    with pytest.raises(ValueError, match="accepted weights"):
        symmetric.symmetric_hamming_witness(4, {5})


def test_invalid_residue_and_threshold_parameters_fail_closed() -> None:
    with pytest.raises(ValueError, match="modulus"):
        symmetric.residue_weights(4, 0, {0})
    with pytest.raises(ValueError, match="threshold"):
        symmetric.threshold_weights(4, 6)


def test_finite_guard() -> None:
    with pytest.raises(ValueError, match="t <= 6"):
        symmetric.symmetric_hamming_witness(7, {0})
