from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
FULL_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "full_cover_oracle.py"
)
CANONICAL_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "canonical_cover_oracle.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


full = _load("full_cover_oracle", FULL_PATH)
canonical = _load("canonical_cover_oracle_for_full_tests", CANONICAL_PATH)


def test_full_cover_neq_source_calibration() -> None:
    assert full.exact_full_cover_number(2, {(0, 0), (1, 1)}).minimum_pairs == 1
    assert full.exact_full_cover_number(
        4, {(i, i) for i in range(4)}
    ).minimum_pairs == 2


def test_c008_strict_canonical_full_separation() -> None:
    complement = full.c008_gadget_complement()
    canonical_result = canonical.exact_canonical_cover_number(3, complement)
    full_result = full.exact_full_cover_number(3, complement)

    assert canonical_result.minimum_pairs == 1
    assert full_result.minimum_pairs == 2


def test_c008_two_pair_witness_covers_every_relevant_semifilter() -> None:
    complement = full.c008_gadget_complement()
    assert full.pair_family_covers_all_relevant_semifilters(
        3, complement, full.c008_two_pair_witness()
    )


def test_full_cover_guard_is_fail_closed() -> None:
    complement = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)}
    with pytest.raises(ValueError, match="strict exhaustive-search guard"):
        full.exact_full_cover_number(3, complement, max_complement_edges=5)
