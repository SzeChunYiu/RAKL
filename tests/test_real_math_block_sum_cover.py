from __future__ import annotations

import importlib.util
from math import ceil, log2
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BLOCK_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "block_sum_cover.py"
)
FULL_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "full_cover_oracle.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


block = _load("block_sum_cover", BLOCK_PATH)
full = _load("full_cover_oracle_for_block_sum", FULL_PATH)


def test_c008_disjoint_witness_covers_every_exact_relevant_semifilter() -> None:
    complement = block.c008_base_complement()
    pairs = block.c008_disjoint_generator_cover()
    assert all(not (e_set & h_set) for e_set, h_set in pairs)
    assert block.generator_separating_pairs_cover_all_relevant_edges(3, complement, pairs)
    assert full.pair_family_covers_all_relevant_semifilters(3, complement, pairs)
    assert full.exact_full_cover_number(3, complement).minimum_pairs == 2


def test_c010_block_sum_pair_count_and_generator_separation() -> None:
    for copies in range(1, 17):
        n_vertices, complement, pairs = block.c008_block_sum_witness(copies)
        assert n_vertices == 3 * copies
        assert len(complement) == 5 * copies
        assert len(pairs) == 2 + (ceil(log2(copies)) if copies > 1 else 0)
        assert len(pairs) == block.c010_bound(copies)
        assert all(not (e_set & h_set) for e_set, h_set in pairs)
        assert block.generator_separating_pairs_cover_all_relevant_edges(
            n_vertices, complement, pairs
        )


def test_block_sum_constructor_rejects_nonseparating_local_family() -> None:
    complement = block.c008_base_complement()
    bad_pairs = [(frozenset({(0, 0)}), frozenset({(0, 1)}))]
    with pytest.raises(ValueError, match="do not generator-separate"):
        block.block_sum_generator_separating_pairs(3, complement, bad_pairs, 2)


def test_generator_separating_checker_rejects_overlap() -> None:
    complement = block.c008_base_complement()
    bad_pairs = [(frozenset({(0, 0)}), frozenset({(0, 0)}))]
    with pytest.raises(ValueError, match="must be disjoint"):
        block.generator_separating_pairs_cover_all_relevant_edges(3, complement, bad_pairs)
