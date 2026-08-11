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


rank_ceiling = _load("gf2_rank_pullback_ceiling", FALSIFICATION / "gf2_rank_pullback_ceiling.py")
full_cover = _load("full_cover_oracle_for_c018", FALSIFICATION / "full_cover_oracle.py")


def _matrix_from_mask(n: int, mask: int) -> list[list[int]]:
    return [
        [((mask >> (row * n + column)) & 1) for column in range(n)]
        for row in range(n)
    ]


def _complement(matrix: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, column)
        for row in range(len(matrix))
        for column in range(len(matrix))
        if matrix[row][column] == 0
    }


def test_all_nontrivial_two_by_two_graphs_respect_rank_ceiling() -> None:
    n = 2
    for mask in range(1, (1 << (n * n)) - 1):
        matrix = _matrix_from_mask(n, mask)
        certificate = rank_ceiling.rank_pullback_certificate(matrix)
        assert certificate.rank >= 1
        result = full_cover.exact_full_cover_number(n, _complement(matrix))
        assert result.minimum_pairs <= certificate.cover_upper_bound


def test_selected_three_by_three_ranks_respect_exact_oracle() -> None:
    matrices = [
        [[1, 1, 1], [1, 1, 1], [0, 0, 0]],
        [[1, 1, 0], [1, 0, 1], [0, 1, 1]],
        [[1, 1, 1], [0, 1, 1], [0, 0, 1]],
    ]
    expected_ranks = [1, 2, 3]

    for matrix, expected_rank in zip(matrices, expected_ranks, strict=True):
        certificate = rank_ceiling.rank_pullback_certificate(matrix)
        assert certificate.rank == expected_rank
        result = full_cover.exact_full_cover_number(3, _complement(matrix))
        assert result.minimum_pairs <= certificate.cover_upper_bound


def test_dense_nonsymmetric_bilinear_form_has_low_rank_pullback() -> None:
    a = [
        [1, 1, 1],
        [0, 1, 1],
        [0, 0, 1],
    ]
    adjacency = rank_ceiling.bilinear_adjacency(a)
    certificate = rank_ceiling.rank_pullback_certificate(adjacency)

    assert certificate.rank == 3
    assert certificate.cover_upper_bound == 7
    assert certificate.reconstructed_rows == tuple(
        sum(bit << column for column, bit in enumerate(row))
        for row in adjacency
    )


def test_zero_matrix_is_trivial_rank_zero() -> None:
    certificate = rank_ceiling.rank_pullback_certificate([[0, 0], [0, 0]])
    assert certificate.rank == 0
    assert certificate.cover_upper_bound == 0


def test_malformed_matrices_fail_closed() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        rank_ceiling.rank_pullback_certificate([])
    with pytest.raises(ValueError, match="square"):
        rank_ceiling.rank_pullback_certificate([[1, 0, 1], [0, 1, 0]])
    with pytest.raises(ValueError, match="binary"):
        rank_ceiling.rank_pullback_certificate([[1, 2], [0, 1]])


def test_bilinear_guard() -> None:
    matrix = [[1 if i == j else 0 for j in range(6)] for i in range(6)]
    with pytest.raises(ValueError, match="t <= 5"):
        rank_ceiling.bilinear_adjacency(matrix)
