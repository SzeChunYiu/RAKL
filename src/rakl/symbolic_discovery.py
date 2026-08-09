from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, isfinite, log, sqrt
from typing import Mapping, Optional, Sequence, Tuple

from .formalism import EquationKind, ExprOp, FormalEquation, FormalExpression


class SymbolicSearchVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    CANNOT_CHECK = "CANNOT_CHECK"
    REJECT = "REJECT"


@dataclass(frozen=True)
class SymbolicDiscoverySpec:
    target_symbol: str
    feature_symbols: Tuple[str, ...]
    constants: Tuple[float, ...] = (1.0,)
    max_depth: int = 2
    beam_width: int = 40
    max_generated: int = 4000
    allow_add_sub: bool = True
    allow_mul: bool = True
    allow_div: bool = True
    allow_square: bool = True
    unary_functions: Tuple[str, ...] = ()
    fit_affine_wrapper: bool = True
    fit_two_basis_linear_model: bool = True
    rows_are_training_partition: Optional[bool] = None
    operator_set_frozen_before_scoring: Optional[bool] = None

    def __post_init__(self) -> None:
        if not self.target_symbol:
            raise ValueError("target_symbol is required")
        if not self.feature_symbols:
            raise ValueError("at least one feature symbol is required")
        if self.target_symbol in self.feature_symbols:
            raise ValueError("target cannot be used as a feature")
        if self.max_depth < 0 or self.max_depth > 4:
            raise ValueError("max_depth must lie in [0, 4]")
        if self.beam_width < 1 or self.max_generated < 1:
            raise ValueError("search budgets must be positive")


@dataclass(frozen=True)
class SymbolicLawCandidate:
    candidate_id: str
    expression: FormalExpression
    equation: FormalEquation
    mse: float
    normalized_mse: float
    complexity: int
    finite_fraction: float
    basis_ids: Tuple[str, ...] = ()
    fitted_coefficients: Tuple[float, ...] = ()


@dataclass(frozen=True)
class SymbolicDiscoveryReport:
    verdict: SymbolicSearchVerdict
    reasons: Tuple[str, ...]
    candidates: Tuple[SymbolicLawCandidate, ...] = ()
    generated_expression_count: int = 0
    valid_row_count: int = 0


def expression_complexity(expression: FormalExpression) -> int:
    return 1 + sum(expression_complexity(arg) for arg in expression.args)


def evaluate_expression(expression: FormalExpression, row: Mapping[str, float]) -> float:
    if expression.op is ExprOp.SYMBOL:
        if expression.symbol is None or expression.symbol not in row:
            raise KeyError(expression.symbol)
        return float(row[expression.symbol])
    if expression.op is ExprOp.CONSTANT:
        if expression.value is None:
            raise ValueError("constant value missing")
        return float(expression.value)

    values = [evaluate_expression(arg, row) for arg in expression.args]
    if expression.op is ExprOp.ADD:
        return sum(values)
    if expression.op is ExprOp.SUB:
        if len(values) != 2:
            raise ValueError("SUB requires two arguments")
        return values[0] - values[1]
    if expression.op is ExprOp.MUL:
        result = 1.0
        for value in values:
            result *= value
        return result
    if expression.op is ExprOp.DIV:
        if len(values) != 2 or abs(values[1]) < 1e-12:
            raise ValueError("unsafe division")
        return values[0] / values[1]
    if expression.op is ExprOp.POW:
        if len(values) != 2:
            raise ValueError("POW requires two arguments")
        return values[0] ** values[1]
    if expression.op is ExprOp.NEG:
        if len(values) != 1:
            raise ValueError("NEG requires one argument")
        return -values[0]
    if expression.op is ExprOp.FUNCTION:
        if len(values) != 1:
            raise ValueError("registered symbolic unary functions require one argument")
        name = (expression.function_name or "").lower()
        value = values[0]
        if name == "abs":
            return abs(value)
        if name == "sqrt":
            if value < 0:
                raise ValueError("sqrt domain")
            return sqrt(value)
        if name == "log":
            if value <= 0:
                raise ValueError("log domain")
            return log(value)
        if name == "exp":
            if value > 700:
                raise ValueError("exp overflow")
            return exp(value)
        if name == "signed_log1p":
            return (1.0 if value >= 0 else -1.0) * log(1.0 + abs(value))
        raise ValueError(f"unsupported symbolic function: {name}")
    raise ValueError(f"unsupported discovery expression operator: {expression.op.value}")


def _prediction_vector(
    expression: FormalExpression,
    rows: Sequence[Mapping[str, float]],
) -> Tuple[Optional[float], ...]:
    output: list[Optional[float]] = []
    for row in rows:
        try:
            value = evaluate_expression(expression, row)
            output.append(value if isfinite(value) else None)
        except (ArithmeticError, KeyError, ValueError, OverflowError):
            output.append(None)
    return tuple(output)


def _signature(values: Tuple[Optional[float], ...]) -> Tuple[Optional[float], ...]:
    finite = [abs(value) for value in values if value is not None]
    scale = max(finite, default=1.0)
    if scale == 0:
        scale = 1.0
    return tuple(None if value is None else round(value / scale, 8) for value in values)


def _target_values(
    rows: Sequence[Mapping[str, float]],
    target_symbol: str,
) -> Optional[Tuple[float, ...]]:
    values = []
    for row in rows:
        if target_symbol not in row:
            return None
        value = float(row[target_symbol])
        if not isfinite(value):
            return None
        values.append(value)
    return tuple(values)


def _mse(y: Sequence[float], prediction: Sequence[Optional[float]]) -> Tuple[float, float]:
    pairs = [(target, pred) for target, pred in zip(y, prediction) if pred is not None]
    if not pairs:
        return float("inf"), 0.0
    error = sum((target - pred) ** 2 for target, pred in pairs) / len(pairs)
    return error, len(pairs) / len(y)


def _target_variance(y: Sequence[float]) -> float:
    mean = sum(y) / len(y)
    return sum((value - mean) ** 2 for value in y) / len(y)


def _fit_affine(
    x: Sequence[Optional[float]],
    y: Sequence[float],
) -> Optional[Tuple[float, float]]:
    pairs = [(float(value), float(target)) for value, target in zip(x, y) if value is not None]
    if len(pairs) < 3:
        return None
    mean_x = sum(value for value, _ in pairs) / len(pairs)
    mean_y = sum(target for _, target in pairs) / len(pairs)
    denominator = sum((value - mean_x) ** 2 for value, _ in pairs)
    if denominator < 1e-15:
        return None
    slope = sum((value - mean_x) * (target - mean_y) for value, target in pairs) / denominator
    intercept = mean_y - slope * mean_x
    return intercept, slope


def _solve_3x3(matrix: list[list[float]], vector: list[float]) -> Optional[Tuple[float, float, float]]:
    augmented = [row[:] + [rhs] for row, rhs in zip(matrix, vector)]
    n = 3
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            return None
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [value / scale for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[col])
            ]
    return tuple(augmented[row][-1] for row in range(n))  # type: ignore[return-value]


def _fit_two_basis(
    x1: Sequence[Optional[float]],
    x2: Sequence[Optional[float]],
    y: Sequence[float],
) -> Optional[Tuple[float, float, float]]:
    rows = [
        (1.0, float(a), float(b), float(target))
        for a, b, target in zip(x1, x2, y)
        if a is not None and b is not None
    ]
    if len(rows) < 5:
        return None
    matrix = [[0.0] * 3 for _ in range(3)]
    vector = [0.0] * 3
    for c0, c1, c2, target in rows:
        cols = (c0, c1, c2)
        for i in range(3):
            vector[i] += cols[i] * target
            for j in range(3):
                matrix[i][j] += cols[i] * cols[j]
    return _solve_3x3(matrix, vector)


def _scale_term(coefficient: float, expression: FormalExpression) -> FormalExpression:
    if abs(coefficient - 1.0) < 1e-12:
        return expression
    return FormalExpression(
        ExprOp.MUL,
        args=(FormalExpression.const(coefficient), expression),
    )


def _affine_expression(intercept: float, slope: float, expression: FormalExpression) -> FormalExpression:
    term = _scale_term(slope, expression)
    if abs(intercept) < 1e-12:
        return term
    return FormalExpression(ExprOp.ADD, args=(FormalExpression.const(intercept), term))


def _two_basis_expression(
    intercept: float,
    left_coef: float,
    left: FormalExpression,
    right_coef: float,
    right: FormalExpression,
) -> FormalExpression:
    terms = [_scale_term(left_coef, left), _scale_term(right_coef, right)]
    if abs(intercept) >= 1e-12:
        terms.insert(0, FormalExpression.const(intercept))
    return FormalExpression(ExprOp.ADD, args=tuple(terms)) if len(terms) > 1 else terms[0]


def _make_candidate(
    candidate_id: str,
    expression: FormalExpression,
    y: Tuple[float, ...],
    rows: Sequence[Mapping[str, float]],
    target_symbol: str,
    *,
    basis_ids: Tuple[str, ...] = (),
    coefficients: Tuple[float, ...] = (),
) -> SymbolicLawCandidate:
    predictions = _prediction_vector(expression, rows)
    error, finite_fraction = _mse(y, predictions)
    variance = _target_variance(y)
    normalized = error / variance if variance > 1e-15 else error
    equation = FormalEquation(
        equation_id=f"symbolic:{candidate_id}",
        lhs=FormalExpression.sym(target_symbol),
        rhs=expression,
        kind=EquationKind.STRUCTURAL,
        derivation_ids=(f"symbolic-search:{candidate_id}",),
    )
    return SymbolicLawCandidate(
        candidate_id,
        expression,
        equation,
        error,
        normalized,
        expression_complexity(expression),
        finite_fraction,
        basis_ids,
        coefficients,
    )


def _primitive_pool(spec: SymbolicDiscoverySpec) -> list[FormalExpression]:
    pool = [FormalExpression.sym(name) for name in spec.feature_symbols]
    pool.extend(FormalExpression.const(value) for value in spec.constants)
    return pool


def discover_symbolic_laws(
    rows: Sequence[Mapping[str, float]],
    spec: SymbolicDiscoverySpec,
    *,
    top_k: int = 20,
) -> SymbolicDiscoveryReport:
    """Bounded grammar/beam search for mathematical law candidates.

    This is a discovery operator, not a certifier. It searches only the supplied
    training partition and emits frozen typed equations that must subsequently face
    untouched/forward validation under the normal RAKL authority rules.
    """

    if spec.rows_are_training_partition is not True:
        return SymbolicDiscoveryReport(
            SymbolicSearchVerdict.CANNOT_CHECK,
            ("symbolic_search_rows_not_verified_as_training_partition",),
        )
    if spec.operator_set_frozen_before_scoring is not True:
        return SymbolicDiscoveryReport(
            SymbolicSearchVerdict.CANNOT_CHECK,
            ("symbolic_operator_set_not_frozen_before_scoring",),
        )
    if len(rows) < 5:
        return SymbolicDiscoveryReport(
            SymbolicSearchVerdict.CANNOT_CHECK,
            ("insufficient_training_rows",),
            valid_row_count=len(rows),
        )
    y = _target_values(rows, spec.target_symbol)
    if y is None:
        return SymbolicDiscoveryReport(
            SymbolicSearchVerdict.REJECT,
            ("target_missing_or_nonfinite",),
        )
    for feature in spec.feature_symbols:
        if any(feature not in row for row in rows):
            return SymbolicDiscoveryReport(
                SymbolicSearchVerdict.REJECT,
                (f"feature_missing:{feature}",),
            )

    generated = 0
    all_expressions: list[FormalExpression] = []
    by_signature: dict[Tuple[Optional[float], ...], FormalExpression] = {}

    def retain(expression: FormalExpression) -> None:
        nonlocal generated
        if generated >= spec.max_generated:
            return
        generated += 1
        predictions = _prediction_vector(expression, rows)
        if sum(value is not None for value in predictions) / len(rows) < 0.8:
            return
        signature = _signature(predictions)
        incumbent = by_signature.get(signature)
        if incumbent is None or expression_complexity(expression) < expression_complexity(incumbent):
            by_signature[signature] = expression

    for expression in _primitive_pool(spec):
        retain(expression)

    frontier = list(by_signature.values())
    for _depth in range(1, spec.max_depth + 1):
        scored_frontier = sorted(
            frontier,
            key=lambda expr: _make_candidate("tmp", expr, y, rows, spec.target_symbol).normalized_mse,
        )[: spec.beam_width]
        base = list(by_signature.values())[: max(spec.beam_width * 2, len(spec.feature_symbols))]
        for left in scored_frontier:
            if spec.allow_square:
                retain(
                    FormalExpression(
                        ExprOp.POW,
                        args=(left, FormalExpression.const(2.0)),
                    )
                )
            for function_name in spec.unary_functions:
                retain(
                    FormalExpression(
                        ExprOp.FUNCTION,
                        args=(left,),
                        function_name=function_name,
                    )
                )
            for right in base:
                if spec.allow_add_sub:
                    retain(FormalExpression(ExprOp.ADD, args=(left, right)))
                    retain(FormalExpression(ExprOp.SUB, args=(left, right)))
                if spec.allow_mul:
                    retain(FormalExpression(ExprOp.MUL, args=(left, right)))
                if spec.allow_div:
                    retain(FormalExpression(ExprOp.DIV, args=(left, right)))
                if generated >= spec.max_generated:
                    break
            if generated >= spec.max_generated:
                break
        frontier = list(by_signature.values())
        if generated >= spec.max_generated:
            break

    all_expressions = list(by_signature.values())
    raw_candidates = [
        _make_candidate(f"raw:{index}", expression, y, rows, spec.target_symbol)
        for index, expression in enumerate(all_expressions)
    ]
    raw_candidates.sort(key=lambda candidate: (candidate.normalized_mse, candidate.complexity))

    candidates = list(raw_candidates[: max(top_k, spec.beam_width)])
    basis = raw_candidates[: min(spec.beam_width, len(raw_candidates))]

    if spec.fit_affine_wrapper:
        for index, candidate in enumerate(basis):
            predictions = _prediction_vector(candidate.expression, rows)
            fit = _fit_affine(predictions, y)
            if fit is None:
                continue
            intercept, slope = fit
            expression = _affine_expression(intercept, slope, candidate.expression)
            candidates.append(
                _make_candidate(
                    f"affine:{index}",
                    expression,
                    y,
                    rows,
                    spec.target_symbol,
                    basis_ids=(candidate.candidate_id,),
                    coefficients=(intercept, slope),
                )
            )

    if spec.fit_two_basis_linear_model:
        pair_basis = basis[: min(12, len(basis))]
        for i, left in enumerate(pair_basis):
            left_predictions = _prediction_vector(left.expression, rows)
            for j, right in enumerate(pair_basis[i + 1 :], start=i + 1):
                right_predictions = _prediction_vector(right.expression, rows)
                fit = _fit_two_basis(left_predictions, right_predictions, y)
                if fit is None:
                    continue
                intercept, left_coef, right_coef = fit
                expression = _two_basis_expression(
                    intercept,
                    left_coef,
                    left.expression,
                    right_coef,
                    right.expression,
                )
                candidates.append(
                    _make_candidate(
                        f"two:{i}:{j}",
                        expression,
                        y,
                        rows,
                        spec.target_symbol,
                        basis_ids=(left.candidate_id, right.candidate_id),
                        coefficients=(intercept, left_coef, right_coef),
                    )
                )

    # Deduplicate final predictive forms by normalized predictions and retain the
    # simplest candidate at equivalent training behavior.
    final_by_signature: dict[Tuple[Optional[float], ...], SymbolicLawCandidate] = {}
    for candidate in candidates:
        signature = _signature(_prediction_vector(candidate.expression, rows))
        incumbent = final_by_signature.get(signature)
        if incumbent is None or (
            candidate.normalized_mse,
            candidate.complexity,
        ) < (
            incumbent.normalized_mse,
            incumbent.complexity,
        ):
            final_by_signature[signature] = candidate

    final = sorted(
        final_by_signature.values(),
        key=lambda candidate: (candidate.normalized_mse, candidate.complexity),
    )[:top_k]
    return SymbolicDiscoveryReport(
        SymbolicSearchVerdict.COMPLETE,
        (
            "bounded_symbolic_grammar_search_completed",
            "training_only_fit_candidate_equations_emitted",
            "untouched_validation_still_required",
        ),
        tuple(final),
        generated,
        len(rows),
    )
