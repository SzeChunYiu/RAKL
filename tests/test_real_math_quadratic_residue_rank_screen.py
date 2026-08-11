from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
FALSIFICATION = ROOT / "research" / "real_math" / "millennium" / "p_vs_np" / "05_falsification"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


qr = _load("quadratic_residue_rank_screen", FALSIFICATION / "quadratic_residue_rank_screen.py")


def test_admissible_primes_have_full_gf2_rank_and_no_translation_compression() -> None:
    for prime in (3, 11, 19, 43, 59):
        result = qr.screen_quadratic_residue_graph(prime)
        assert result.gf2_rank == prime
        assert result.distinct_rows == prime
        assert result.distinct_columns == prime
        assert result.translation_stabilizer == (0,)


def test_density_screen_matches_exact_counts() -> None:
    for prime in (11, 19, 43):
        result = qr.screen_quadratic_residue_graph(prime)
        assert result.degree == (prime - 1) // 2
        assert result.edge_count == prime * (prime - 1) // 2
        assert result.forest_partition_density_lower_bound == qr.math.ceil(
            result.edge_count / (2 * prime - 1)
        )
        assert result.c018_rank_ceiling == 3 * prime - 2


def test_rows_are_cyclic_shifts_of_the_quadratic_residue_indicator() -> None:
    prime = 11
    rows = qr.adjacency_row_masks(prime)
    residues = qr.quadratic_residues(prime)
    expected_zero_row = sum(1 << value for value in residues)
    assert rows[0] == expected_zero_row

    for x, row in enumerate(rows):
        expected = sum(1 << ((value + x) % prime) for value in residues)
        assert row == expected


def test_non_admissible_inputs_fail_closed() -> None:
    for value in (0, 1, 2, 5, 7, 9, 15, 17, 23):
        with pytest.raises(ValueError):
            qr.screen_quadratic_residue_graph(value)


def test_quadratic_residue_helper_rejects_nonprime_or_even_modulus() -> None:
    with pytest.raises(ValueError, match="odd prime"):
        qr.quadratic_residues(2)
    with pytest.raises(ValueError, match="odd prime"):
        qr.quadratic_residues(21)
