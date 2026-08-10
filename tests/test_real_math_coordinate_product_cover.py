from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "coordinate_product_cover.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


product_cover = _load("coordinate_product_cover", PRODUCT_PATH)


def test_c008_coordinate_product_pair_count_and_separation() -> None:
    for copies in range(1, 5):
        n_vertices, complement, pairs = product_cover.c008_coordinate_product_witness(
            copies
        )
        assert n_vertices == 3**copies
        assert len(complement) == 5**copies
        assert len(pairs) == 2 * copies
        assert len(pairs) == product_cover.c011_bound(copies)
        assert all(not (e_set & h_set) for e_set, h_set in pairs)
        assert product_cover.generator_separating_pairs_cover_all_relevant_edges(
            n_vertices, complement, pairs
        )


def test_coordinate_product_is_genuinely_cross_coordinate_coupled() -> None:
    n_vertices, complement, vertices = product_cover.coordinate_product_complement(
        3, product_cover.c008_base_complement(), 2
    )
    index = {vertex: i for i, vertex in enumerate(vertices)}

    left = index[(0, 1)]
    right = index[(0, 2)]
    assert (0, 0) in product_cover.c008_base_complement()
    assert (1, 2) in product_cover.c008_base_complement()
    assert (left, right) in complement
    assert n_vertices == 9


def test_coordinate_product_constructor_rejects_nonseparating_base_family() -> None:
    complement = product_cover.c008_base_complement()
    bad_pairs = [(frozenset({(0, 0)}), frozenset({(0, 1)}))]
    with pytest.raises(ValueError, match="do not generator-separate"):
        product_cover.coordinate_product_generator_separating_pairs(
            3, complement, bad_pairs, 2
        )


def test_coordinate_product_requires_positive_copy_count() -> None:
    with pytest.raises(ValueError, match="copies must be positive"):
        product_cover.coordinate_product_complement(
            3, product_cover.c008_base_complement(), 0
        )
