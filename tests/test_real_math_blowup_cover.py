from __future__ import annotations

import importlib.util
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
BLOWUP_PATH = FALSIFICATION / "blowup_cover.py"
FULL_PATH = FALSIFICATION / "full_cover_oracle.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


blowup = _load("blowup_cover", BLOWUP_PATH)
full = _load("full_cover_oracle_for_blowup", FULL_PATH)


def test_neq_nonuniform_blowup_keeps_exact_one_pair_cover() -> None:
    labels = [0, 0, 1]
    complement = blowup.blowup_complement(
        2, blowup.neq_two_vertex_complement(), labels
    )
    pairs = blowup.lift_pair_family(
        blowup.neq_two_vertex_pair_witness(), labels
    )

    assert len(complement) == 5
    assert full.exact_full_cover_number(3, complement).minimum_pairs == 1
    assert full.pair_family_covers_all_relevant_semifilters(3, complement, pairs)


def test_eq_nonuniform_blowup_keeps_exact_one_pair_cover() -> None:
    labels = [0, 0, 1]
    complement = blowup.blowup_complement(
        2, blowup.eq_two_vertex_complement(), labels
    )
    pairs = blowup.lift_pair_family(
        blowup.eq_two_vertex_pair_witness(), labels
    )

    assert len(complement) == 4
    assert full.exact_full_cover_number(3, complement).minimum_pairs == 1
    assert full.pair_family_covers_all_relevant_semifilters(3, complement, pairs)


def test_blowup_accepts_distinct_surjective_left_and_right_maps() -> None:
    complement = blowup.blowup_complement(
        2,
        blowup.neq_two_vertex_complement(),
        [0, 0, 1],
        [0, 1, 1],
    )
    assert complement == {
        (0, 0),
        (1, 0),
        (2, 1),
        (2, 2),
    }


def test_blowup_rejects_non_surjective_labels() -> None:
    with pytest.raises(ValueError, match="surjective"):
        blowup.blowup_complement(
            2, blowup.neq_two_vertex_complement(), [0, 0, 0]
        )


def test_blowup_rejects_trivial_base_graphs() -> None:
    with pytest.raises(ValueError, match="nontrivial"):
        blowup.blowup_complement(2, set(), [0, 1])
    with pytest.raises(ValueError, match="nontrivial"):
        blowup.blowup_complement(
            2,
            {(0, 0), (0, 1), (1, 0), (1, 1)},
            [0, 1],
        )
