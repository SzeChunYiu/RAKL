from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Sequence, Tuple


Matrix = Tuple[Tuple[float, ...], ...]
Vector = Tuple[float, ...]


class MetrologyVerdict(str, Enum):
    EXECUTED = "EXECUTED"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class AffineTransform:
    transform_id: str
    matrix: Matrix
    offset: Vector
    declared_before_results: bool | None
    invertibility_required: bool = False

    @property
    def source_dim(self) -> int:
        return len(self.matrix[0]) if self.matrix else 0

    @property
    def target_dim(self) -> int:
        return len(self.matrix)


@dataclass(frozen=True)
class MetrologyReport:
    verdict: MetrologyVerdict
    reasons: Tuple[str, ...]
    mean: Vector = ()
    covariance: Matrix = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_mechanism_authority(self) -> bool:
        return False


def _rectangular(matrix: Matrix) -> bool:
    return bool(matrix) and bool(matrix[0]) and all(len(row) == len(matrix[0]) for row in matrix)


def _symmetric(matrix: Matrix, tol: float = 1e-12) -> bool:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        return False
    return all(abs(matrix[i][j] - matrix[j][i]) <= tol for i in range(len(matrix)) for j in range(len(matrix)))


def _positive_semidefinite(matrix: Matrix, tol: float = 1e-12) -> bool:
    """Pure-Python semidefinite Cholesky check for a symmetric matrix.

    The algorithm accepts zero pivots only when the corresponding unresolved
    cross terms are also zero within tolerance. It is a validation routine, not
    a numerical linear-algebra replacement for large ill-conditioned systems.
    """
    if not _symmetric(matrix, tol):
        return False
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            residual = matrix[i][j] - sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if residual < -tol:
                    return False
                lower[i][j] = sqrt(max(0.0, residual))
            else:
                pivot = lower[j][j]
                if pivot > tol:
                    lower[i][j] = residual / pivot
                elif abs(residual) > tol:
                    return False
                else:
                    lower[i][j] = 0.0
    return True


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    return tuple(sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix)


def _matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right:
        return ()
    return tuple(
        tuple(sum(left[i][k] * right[k][j] for k in range(len(right))) for j in range(len(right[0])))
        for i in range(len(left))
    )


def _transpose(matrix: Matrix) -> Matrix:
    return tuple(tuple(matrix[i][j] for i in range(len(matrix))) for j in range(len(matrix[0])))


def _rank(matrix: Matrix, tol: float = 1e-12) -> int:
    work = [list(row) for row in matrix]
    rows = len(work)
    cols = len(work[0]) if rows else 0
    rank = 0
    col = 0
    while rank < rows and col < cols:
        pivot = max(range(rank, rows), key=lambda r: abs(work[r][col]))
        if abs(work[pivot][col]) <= tol:
            col += 1
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][col]
        work[rank] = [value / pivot_value for value in work[rank]]
        for r in range(rows):
            if r == rank:
                continue
            factor = work[r][col]
            if abs(factor) <= tol:
                continue
            work[r] = [work[r][c] - factor * work[rank][c] for c in range(cols)]
        rank += 1
        col += 1
    return rank


def validate_affine_transform(transform: AffineTransform) -> Tuple[str, ...]:
    problems: list[str] = []
    if not transform.transform_id.strip():
        problems.append("transform_id_missing")
    if transform.declared_before_results is None:
        problems.append("transform_chronology_unknown")
    elif transform.declared_before_results is False:
        problems.append("transform_declared_posthoc")
    if not _rectangular(transform.matrix):
        problems.append("matrix_not_rectangular_or_empty")
        return tuple(problems)
    if len(transform.offset) != transform.target_dim:
        problems.append("offset_dimension_mismatch")
    if transform.invertibility_required:
        if transform.source_dim != transform.target_dim:
            problems.append("invertible_transform_must_be_square")
        elif _rank(transform.matrix) != transform.source_dim:
            problems.append("transform_not_invertible")
    return tuple(problems)


def propagate_affine(
    mean: Sequence[float],
    covariance: Sequence[Sequence[float]],
    transform: AffineTransform,
) -> MetrologyReport:
    """Execute y = A x + b and Sigma_y = A Sigma_x A^T.

    The covariance law is exact for an affine map. No independence assumption is
    needed because the full covariance matrix is transported.
    """
    problems = list(validate_affine_transform(transform))
    mean_v: Vector = tuple(float(x) for x in mean)
    cov: Matrix = tuple(tuple(float(x) for x in row) for row in covariance)

    if len(mean_v) != transform.source_dim:
        problems.append("mean_dimension_mismatch")
    if len(cov) != transform.source_dim or any(len(row) != transform.source_dim for row in cov):
        problems.append("covariance_dimension_mismatch")
    elif not _symmetric(cov):
        problems.append("covariance_not_symmetric")
    elif not _positive_semidefinite(cov):
        problems.append("covariance_not_positive_semidefinite")

    if problems:
        verdict = MetrologyVerdict.CANNOT_CHECK if "transform_chronology_unknown" in problems else MetrologyVerdict.REJECT
        return MetrologyReport(verdict, tuple(problems))

    transformed_mean = tuple(
        value + transform.offset[i]
        for i, value in enumerate(_matvec(transform.matrix, mean_v))
    )
    transformed_covariance = _matmul(_matmul(transform.matrix, cov), _transpose(transform.matrix))
    return MetrologyReport(
        MetrologyVerdict.EXECUTED,
        (
            "affine_mean_transform_executed",
            "full_covariance_transport_executed",
            "no_independence_assumption_required",
            "metrology_execution_does_not_mint_scientific_or_mechanism_authority",
        ),
        transformed_mean,
        transformed_covariance,
    )


@dataclass(frozen=True)
class FirstOrderTransform:
    transform_id: str
    jacobian: Matrix
    declared_before_results: bool | None
    differentiability_witness: bool | None


def propagate_first_order_covariance(
    covariance: Sequence[Sequence[float]],
    transform: FirstOrderTransform,
) -> MetrologyReport:
    """Execute the first-order delta-method covariance J Sigma J^T.

    This is a local linearization, not an exact nonlinear uncertainty law.
    Differentiability and predeclaration are therefore blocking assumptions.
    """
    cov: Matrix = tuple(tuple(float(x) for x in row) for row in covariance)
    jac = transform.jacobian
    reasons: list[str] = []
    if not transform.transform_id.strip():
        reasons.append("transform_id_missing")
    if transform.declared_before_results is None:
        reasons.append("transform_chronology_unknown")
    elif transform.declared_before_results is False:
        reasons.append("transform_declared_posthoc")
    if transform.differentiability_witness is None:
        reasons.append("differentiability_unknown")
    elif transform.differentiability_witness is False:
        reasons.append("differentiability_not_established")
    if not _rectangular(jac):
        reasons.append("jacobian_not_rectangular_or_empty")
    else:
        source_dim = len(jac[0])
        if len(cov) != source_dim or any(len(row) != source_dim for row in cov):
            reasons.append("covariance_dimension_mismatch")
        elif not _symmetric(cov):
            reasons.append("covariance_not_symmetric")
        elif not _positive_semidefinite(cov):
            reasons.append("covariance_not_positive_semidefinite")
    if reasons:
        cannot = any(reason.endswith("_unknown") for reason in reasons)
        return MetrologyReport(MetrologyVerdict.CANNOT_CHECK if cannot else MetrologyVerdict.REJECT, tuple(reasons))
    result = _matmul(_matmul(jac, cov), _transpose(jac))
    return MetrologyReport(
        MetrologyVerdict.EXECUTED,
        (
            "first_order_covariance_propagation_executed",
            "result_is_local_linearization_not_exact_nonlinear_law",
            "metrology_execution_does_not_mint_scientific_or_mechanism_authority",
        ),
        covariance=result,
    )


def combine_independent_standard_uncertainties(
    standard_uncertainties: Sequence[float],
    *,
    independence_witness: bool | None,
) -> tuple[MetrologyVerdict, float | None, Tuple[str, ...]]:
    """Combine standard uncertainties only under an explicit independence witness.

    u_c = sqrt(sum_i u_i^2) is licensed here only for an uncorrelated linear
    combination with unit coefficients. Correlated cases must provide a full
    covariance model and use the covariance propagation path instead.
    """
    values = tuple(float(value) for value in standard_uncertainties)
    if not values:
        return MetrologyVerdict.CANNOT_CHECK, None, ("standard_uncertainties_missing",)
    if any(value < 0 for value in values):
        return MetrologyVerdict.REJECT, None, ("negative_standard_uncertainty",)
    if independence_witness is None:
        return MetrologyVerdict.CANNOT_CHECK, None, ("independence_status_unknown",)
    if independence_witness is False:
        return MetrologyVerdict.REJECT, None, ("root_sum_square_not_licensed_for_correlated_inputs",)
    return (
        MetrologyVerdict.EXECUTED,
        sqrt(sum(value * value for value in values)),
        ("root_sum_square_licensed_by_explicit_independence_witness",),
    )
