"""Finite certificates for C018 GF(2)-rank pullback pruning.

The script factors a binary adjacency matrix M=UV over GF(2) and exposes each
row of U and each column of V as feature labels.  Their mod-2 inner product
must reconstruct every adjacency bit.  This is an executable calibration of
the pullback representation, not a proof certificate for the asymptotic claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


BinaryMatrix = Sequence[Sequence[int]]


@dataclass(frozen=True)
class RankPullbackCertificate:
    size: int
    rank: int
    left_labels: tuple[int, ...]
    right_labels: tuple[int, ...]
    reconstructed_rows: tuple[int, ...]
    cover_upper_bound: int


def _validate_square_binary(matrix: BinaryMatrix) -> tuple[int, tuple[int, ...]]:
    n = len(matrix)
    if n < 1:
        raise ValueError("matrix must be nonempty")
    if any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")
    rows: list[int] = []
    for row in matrix:
        if any(bit not in (0, 1) for bit in row):
            raise ValueError("matrix entries must be binary")
        rows.append(sum(bit << column for column, bit in enumerate(row)))
    return n, tuple(rows)


def _chosen_row_basis(rows: tuple[int, ...]) -> tuple[int, ...]:
    pivots: dict[int, int] = {}
    chosen: list[int] = []
    for row in rows:
        reduced = row
        for pivot in sorted(pivots, reverse=True):
            if (reduced >> pivot) & 1:
                reduced ^= pivots[pivot]
        if reduced:
            pivots[reduced.bit_length() - 1] = reduced
            chosen.append(row)
    return tuple(chosen)


def _coordinate_solver(basis_rows: tuple[int, ...]):
    pivots: dict[int, tuple[int, int]] = {}
    for index, row in enumerate(basis_rows):
        reduced = row
        coefficients = 1 << index
        for pivot in sorted(pivots, reverse=True):
            if (reduced >> pivot) & 1:
                pivot_row, pivot_coefficients = pivots[pivot]
                reduced ^= pivot_row
                coefficients ^= pivot_coefficients
        if not reduced:
            raise AssertionError("chosen basis rows are dependent")
        pivots[reduced.bit_length() - 1] = (reduced, coefficients)

    def solve(row: int) -> int:
        reduced = row
        coefficients = 0
        for pivot in sorted(pivots, reverse=True):
            if (reduced >> pivot) & 1:
                pivot_row, pivot_coefficients = pivots[pivot]
                reduced ^= pivot_row
                coefficients ^= pivot_coefficients
        if reduced:
            raise AssertionError("row is outside the selected row span")
        return coefficients

    return solve


def rank_pullback_certificate(matrix: BinaryMatrix) -> RankPullbackCertificate:
    n, rows = _validate_square_binary(matrix)
    basis_rows = _chosen_row_basis(rows)
    rank = len(basis_rows)

    if rank == 0:
        return RankPullbackCertificate(
            size=n,
            rank=0,
            left_labels=tuple(0 for _ in range(n)),
            right_labels=tuple(0 for _ in range(n)),
            reconstructed_rows=tuple(0 for _ in range(n)),
            cover_upper_bound=0,
        )

    solve = _coordinate_solver(basis_rows)
    left_labels = tuple(solve(row) for row in rows)
    right_labels = tuple(
        sum(((basis_rows[feature] >> column) & 1) << feature for feature in range(rank))
        for column in range(n)
    )

    reconstructed_rows: list[int] = []
    for left_label in left_labels:
        reconstructed = 0
        for column, right_label in enumerate(right_labels):
            bit = (left_label & right_label).bit_count() & 1
            reconstructed |= bit << column
        reconstructed_rows.append(reconstructed)

    if tuple(reconstructed_rows) != rows:
        raise AssertionError("GF(2) rank pullback failed to reconstruct adjacency matrix")

    return RankPullbackCertificate(
        size=n,
        rank=rank,
        left_labels=left_labels,
        right_labels=right_labels,
        reconstructed_rows=tuple(reconstructed_rows),
        cover_upper_bound=3 * rank - 2,
    )


def bilinear_adjacency(matrix_a: BinaryMatrix) -> list[list[int]]:
    t, rows_a = _validate_square_binary(matrix_a)
    if t > 5:
        raise ValueError("finite bilinear calibration guard: use t <= 5")

    n = 1 << t
    adjacency: list[list[int]] = []
    for x in range(n):
        row: list[int] = []
        for y in range(n):
            value = 0
            for bit in range(t):
                if (x >> bit) & 1:
                    value ^= (rows_a[bit] & y).bit_count() & 1
            row.append(value)
        adjacency.append(row)
    return adjacency


if __name__ == "__main__":
    example = [
        [1, 1, 1],
        [0, 1, 1],
        [0, 0, 1],
    ]
    adjacency = bilinear_adjacency(example)
    print(rank_pullback_certificate(adjacency))
