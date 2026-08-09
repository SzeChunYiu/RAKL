from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Sequence, Tuple


class OracleVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MatrixOracleReport:
    verdict: OracleVerdict
    reasons: Tuple[str, ...]
    rank: int | None = None
    dimension: int | None = None


def _validate_rectangular(matrix: Sequence[Sequence[float]]) -> tuple[int, int] | None:
    if not matrix or not matrix[0]:
        return None
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        return None
    return len(matrix), width


def matrix_rank(matrix: Sequence[Sequence[float]], *, tolerance: float = 1e-10) -> int:
    shape = _validate_rectangular(matrix)
    if shape is None:
        raise ValueError("matrix must be nonempty and rectangular")
    rows, cols = shape
    work = [list(map(float, row)) for row in matrix]
    rank = 0
    pivot_col = 0
    while rank < rows and pivot_col < cols:
        pivot = max(range(rank, rows), key=lambda row: abs(work[row][pivot_col]))
        if abs(work[pivot][pivot_col]) <= tolerance:
            pivot_col += 1
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][pivot_col]
        work[rank] = [value / pivot_value for value in work[rank]]
        for row in range(rows):
            if row == rank:
                continue
            factor = work[row][pivot_col]
            if abs(factor) <= tolerance:
                continue
            work[row] = [
                value - factor * pivot_entry
                for value, pivot_entry in zip(work[row], work[rank])
            ]
        rank += 1
        pivot_col += 1
    return rank


def check_local_identifiability(
    sensitivity_jacobian: Sequence[Sequence[float]],
    *,
    parameter_count: int,
    tolerance: float = 1e-10,
) -> MatrixOracleReport:
    """Local rank-condition oracle for a registered parameterization."""

    shape = _validate_rectangular(sensitivity_jacobian)
    if shape is None or parameter_count < 1:
        return MatrixOracleReport(
            OracleVerdict.CANNOT_CHECK,
            ("sensitivity_jacobian_or_parameter_count_invalid",),
        )
    _, cols = shape
    if cols != parameter_count:
        return MatrixOracleReport(
            OracleVerdict.FAIL,
            ("sensitivity_jacobian_column_count_mismatch",),
            dimension=parameter_count,
        )
    rank = matrix_rank(sensitivity_jacobian, tolerance=tolerance)
    if rank < parameter_count:
        return MatrixOracleReport(
            OracleVerdict.FAIL,
            ("local_sensitivity_rank_deficient",),
            rank,
            parameter_count,
        )
    return MatrixOracleReport(
        OracleVerdict.PASS,
        ("local_sensitivity_full_column_rank",),
        rank,
        parameter_count,
    )


class DynamicsClock(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    DISCRETE = "DISCRETE"


@dataclass(frozen=True)
class StabilityReport:
    verdict: OracleVerdict
    reasons: Tuple[str, ...]
    trace: float | None = None
    determinant: float | None = None


def check_local_linear_stability(
    jacobian: Sequence[Sequence[float]],
    *,
    clock: DynamicsClock,
    tolerance: float = 1e-10,
) -> StabilityReport:
    """Exact local asymptotic stability oracle for 1D/2D linearizations.

    Higher-dimensional systems deliberately return CANNOT_CHECK so a numerical or
    symbolic eigenvalue backend can be used without pretending this small oracle is
    universal.
    """

    shape = _validate_rectangular(jacobian)
    if shape is None or shape[0] != shape[1]:
        return StabilityReport(OracleVerdict.CANNOT_CHECK, ("jacobian_not_square",))
    n = shape[0]
    if n == 1:
        value = float(jacobian[0][0])
        stable = value < -tolerance if clock is DynamicsClock.CONTINUOUS else abs(value) < 1.0 - tolerance
        return StabilityReport(
            OracleVerdict.PASS if stable else OracleVerdict.FAIL,
            ("one_dimensional_stability_condition_passed" if stable else "one_dimensional_stability_condition_failed",),
            trace=value,
            determinant=value,
        )
    if n != 2:
        return StabilityReport(
            OracleVerdict.CANNOT_CHECK,
            ("builtin_exact_stability_oracle_supports_only_1d_2d",),
        )

    a, b = map(float, jacobian[0])
    c, d = map(float, jacobian[1])
    trace = a + d
    determinant = a * d - b * c
    if clock is DynamicsClock.CONTINUOUS:
        stable = trace < -tolerance and determinant > tolerance
        reasons = (
            "two_dimensional_hurwitz_conditions_passed"
            if stable
            else "two_dimensional_hurwitz_conditions_failed",
        )
    else:
        # Jury/Schur conditions for lambda^2 - trace lambda + determinant.
        c1 = 1.0 - trace + determinant
        c2 = 1.0 + trace + determinant
        c3 = 1.0 - determinant
        stable = c1 > tolerance and c2 > tolerance and c3 > tolerance
        reasons = (
            "two_dimensional_jury_conditions_passed"
            if stable
            else "two_dimensional_jury_conditions_failed",
        )
    return StabilityReport(
        OracleVerdict.PASS if stable else OracleVerdict.FAIL,
        reasons,
        trace,
        determinant,
    )


def _determinant(matrix: Sequence[Sequence[float]], *, tolerance: float = 1e-12) -> float:
    shape = _validate_rectangular(matrix)
    if shape is None or shape[0] != shape[1]:
        raise ValueError("determinant requires square matrix")
    n = shape[0]
    work = [list(map(float, row)) for row in matrix]
    determinant = 1.0
    sign = 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(work[row][col]))
        if abs(work[pivot][col]) <= tolerance:
            return 0.0
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
            sign *= -1.0
        pivot_value = work[col][col]
        determinant *= pivot_value
        for row in range(col + 1, n):
            factor = work[row][col] / pivot_value
            for j in range(col + 1, n):
                work[row][j] -= factor * work[col][j]
    return sign * determinant


def check_covariance_psd(
    covariance: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-10,
    max_exact_dimension: int = 7,
) -> MatrixOracleReport:
    """Check symmetry and all principal minors for small covariance matrices."""

    shape = _validate_rectangular(covariance)
    if shape is None or shape[0] != shape[1]:
        return MatrixOracleReport(OracleVerdict.CANNOT_CHECK, ("covariance_not_square",))
    n = shape[0]
    if n > max_exact_dimension:
        return MatrixOracleReport(
            OracleVerdict.CANNOT_CHECK,
            ("covariance_dimension_exceeds_builtin_exact_psd_oracle",),
            dimension=n,
        )
    for i in range(n):
        for j in range(n):
            if abs(float(covariance[i][j]) - float(covariance[j][i])) > tolerance:
                return MatrixOracleReport(
                    OracleVerdict.FAIL,
                    ("covariance_not_symmetric",),
                    dimension=n,
                )

    indices = range(n)
    for size in range(1, n + 1):
        for subset in combinations(indices, size):
            principal = [
                [float(covariance[i][j]) for j in subset]
                for i in subset
            ]
            if _determinant(principal) < -tolerance:
                return MatrixOracleReport(
                    OracleVerdict.FAIL,
                    (f"negative_principal_minor:{subset}",),
                    dimension=n,
                )
    return MatrixOracleReport(
        OracleVerdict.PASS,
        ("covariance_symmetric_positive_semidefinite",),
        dimension=n,
    )


def check_transition_matrix(
    transition: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-10,
) -> MatrixOracleReport:
    shape = _validate_rectangular(transition)
    if shape is None or shape[0] != shape[1]:
        return MatrixOracleReport(OracleVerdict.CANNOT_CHECK, ("transition_matrix_not_square",))
    n = shape[0]
    for row_index, row in enumerate(transition):
        if any(float(value) < -tolerance or float(value) > 1.0 + tolerance for value in row):
            return MatrixOracleReport(
                OracleVerdict.FAIL,
                (f"transition_probability_out_of_range:row{row_index}",),
                dimension=n,
            )
        if abs(sum(map(float, row)) - 1.0) > tolerance:
            return MatrixOracleReport(
                OracleVerdict.FAIL,
                (f"transition_row_not_normalized:row{row_index}",),
                dimension=n,
            )
    return MatrixOracleReport(
        OracleVerdict.PASS,
        ("transition_matrix_is_row_stochastic",),
        dimension=n,
    )
