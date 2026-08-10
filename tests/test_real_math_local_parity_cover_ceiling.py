from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PARITY_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "local_parity_cover_ceiling.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


parity_cover = _load("local_parity_cover_ceiling", PARITY_PATH)


def test_xor_complement_pair_exhaustive_truth_table() -> None:
    for p, r in product((False, True), repeat=2):
        p_next, q_next = parity_cover.xor_complement_pair(
            p, not p, r, not r
        )
        assert p_next is (p ^ r)
        assert q_next is (not (p ^ r))


def test_xor_complement_pair_rejects_invalid_complements() -> None:
    with pytest.raises(ValueError, match="q must be"):
        parity_cover.xor_complement_pair(False, False, False, True)
    with pytest.raises(ValueError, match="s must be"):
        parity_cover.xor_complement_pair(False, True, False, False)


def test_parity_recurrence_matches_direct_parity() -> None:
    for width in range(1, 9):
        for bits in product((False, True), repeat=width):
            parity, complement = parity_cover.parity_with_complement(bits)
            expected = bool(sum(bits) & 1)
            assert parity is expected
            assert complement is (not expected)


def test_parity_recurrence_requires_nonempty_input() -> None:
    with pytest.raises(ValueError, match="bits must be non-empty"):
        parity_cover.parity_with_complement(())


def test_inner_product_corollary_bound_is_three_t_minus_two() -> None:
    for width in range(1, 17):
        assert parity_cover.c012_intersection_upper_bound(width, 1, 0) == 3 * width - 2


def test_inner_product_via_local_parity_matches_direct_definition() -> None:
    for width in range(1, 7):
        for x in range(1 << width):
            for y in range(1 << width):
                assert parity_cover.inner_product_via_local_parity(x, y, width) is (
                    parity_cover.inner_product_mod2(x, y, width)
                )


def test_c012_helpers_reject_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="t must be positive"):
        parity_cover.c012_intersection_upper_bound(0, 1, 0)
    with pytest.raises(ValueError, match="non-negative"):
        parity_cover.c012_intersection_upper_bound(1, -1, 0)
    with pytest.raises(ValueError, match="t must be positive"):
        parity_cover.inner_product_mod2(0, 0, 0)
    with pytest.raises(ValueError, match="fit in t bits"):
        parity_cover.inner_product_mod2(2, 0, 1)
