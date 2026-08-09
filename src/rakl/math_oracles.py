from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from .formalism import ExprOp, FormalEquation, FormalExpression, Formalism


@dataclass(frozen=True)
class Dimension:
    """Symbolic physical/semantic dimension represented by base exponents."""

    exponents: Tuple[Tuple[str, float], ...] = ()

    @staticmethod
    def from_mapping(values: Mapping[str, float]) -> "Dimension":
        normalized = tuple(
            sorted((name, float(power)) for name, power in values.items() if power != 0)
        )
        return Dimension(normalized)

    @staticmethod
    def dimensionless() -> "Dimension":
        return Dimension(())

    def as_dict(self) -> dict[str, float]:
        return dict(self.exponents)

    def multiply(self, other: "Dimension") -> "Dimension":
        values = self.as_dict()
        for name, power in other.exponents:
            values[name] = values.get(name, 0.0) + power
        return Dimension.from_mapping(values)

    def divide(self, other: "Dimension") -> "Dimension":
        values = self.as_dict()
        for name, power in other.exponents:
            values[name] = values.get(name, 0.0) - power
        return Dimension.from_mapping(values)

    def power(self, exponent: float) -> "Dimension":
        return Dimension.from_mapping(
            {name: power * exponent for name, power in self.exponents}
        )


class DimensionVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class DimensionInference:
    verdict: DimensionVerdict
    dimension: Optional[Dimension]
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class EquationDimensionReport:
    equation_id: str
    verdict: DimensionVerdict
    lhs_dimension: Optional[Dimension]
    rhs_dimension: Optional[Dimension]
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class FormalismDimensionReport:
    formalism_id: str
    verdict: DimensionVerdict
    equation_reports: Tuple[EquationDimensionReport, ...]
    reasons: Tuple[str, ...]


def _merge_same(inferences: Tuple[DimensionInference, ...]) -> DimensionInference:
    if any(item.verdict is DimensionVerdict.FAIL for item in inferences):
        return DimensionInference(
            DimensionVerdict.FAIL,
            None,
            tuple(reason for item in inferences for reason in item.reasons),
        )
    if any(item.verdict is DimensionVerdict.CANNOT_CHECK for item in inferences):
        return DimensionInference(
            DimensionVerdict.CANNOT_CHECK,
            None,
            tuple(reason for item in inferences for reason in item.reasons),
        )
    dimensions = {item.dimension for item in inferences}
    if len(dimensions) != 1:
        return DimensionInference(
            DimensionVerdict.FAIL,
            None,
            ("additive_terms_have_different_dimensions",),
        )
    return DimensionInference(DimensionVerdict.PASS, inferences[0].dimension)


def infer_expression_dimension(
    expression: FormalExpression,
    symbol_dimensions: Mapping[str, Dimension],
) -> DimensionInference:
    if expression.op is ExprOp.SYMBOL:
        if not expression.symbol or expression.symbol not in symbol_dimensions:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                (f"dimension_missing_for_symbol:{expression.symbol}",),
            )
        return DimensionInference(
            DimensionVerdict.PASS,
            symbol_dimensions[expression.symbol],
        )

    if expression.op is ExprOp.CONSTANT:
        return DimensionInference(DimensionVerdict.PASS, Dimension.dimensionless())

    if expression.op in {ExprOp.ADD, ExprOp.SUB, ExprOp.PIECEWISE}:
        if not expression.args:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                ("additive_expression_has_no_args",),
            )
        return _merge_same(
            tuple(infer_expression_dimension(arg, symbol_dimensions) for arg in expression.args)
        )

    if expression.op is ExprOp.NEG:
        if len(expression.args) != 1:
            return DimensionInference(DimensionVerdict.FAIL, None, ("neg_requires_one_arg",))
        return infer_expression_dimension(expression.args[0], symbol_dimensions)

    if expression.op in {ExprOp.MUL, ExprOp.DIV}:
        if not expression.args:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                ("multiplicative_expression_has_no_args",),
            )
        parts = tuple(infer_expression_dimension(arg, symbol_dimensions) for arg in expression.args)
        if any(item.verdict is not DimensionVerdict.PASS for item in parts):
            verdict = (
                DimensionVerdict.FAIL
                if any(item.verdict is DimensionVerdict.FAIL for item in parts)
                else DimensionVerdict.CANNOT_CHECK
            )
            return DimensionInference(
                verdict,
                None,
                tuple(reason for item in parts for reason in item.reasons),
            )
        dimension = parts[0].dimension or Dimension.dimensionless()
        for part in parts[1:]:
            assert part.dimension is not None
            if expression.op is ExprOp.MUL:
                dimension = dimension.multiply(part.dimension)
            else:
                dimension = dimension.divide(part.dimension)
        return DimensionInference(DimensionVerdict.PASS, dimension)

    if expression.op is ExprOp.POW:
        if len(expression.args) != 2:
            return DimensionInference(DimensionVerdict.FAIL, None, ("pow_requires_two_args",))
        base, exponent = expression.args
        base_report = infer_expression_dimension(base, symbol_dimensions)
        if base_report.verdict is not DimensionVerdict.PASS:
            return base_report
        if exponent.op is not ExprOp.CONSTANT or exponent.value is None:
            if base_report.dimension != Dimension.dimensionless():
                return DimensionInference(
                    DimensionVerdict.CANNOT_CHECK,
                    None,
                    ("dimensionful_base_with_nonconstant_exponent",),
                )
            return DimensionInference(DimensionVerdict.PASS, Dimension.dimensionless())
        assert base_report.dimension is not None
        return DimensionInference(
            DimensionVerdict.PASS,
            base_report.dimension.power(exponent.value),
        )

    if expression.op is ExprOp.DERIVATIVE:
        if len(expression.args) != 1 or not expression.variable:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                ("derivative_requires_argument_and_variable",),
            )
        numerator = infer_expression_dimension(expression.args[0], symbol_dimensions)
        denominator = symbol_dimensions.get(expression.variable)
        if numerator.verdict is not DimensionVerdict.PASS or denominator is None:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                numerator.reasons + (f"derivative_variable_dimension_missing:{expression.variable}",),
            )
        assert numerator.dimension is not None
        return DimensionInference(
            DimensionVerdict.PASS,
            numerator.dimension.divide(denominator.power(expression.order)),
        )

    if expression.op is ExprOp.INTEGRAL:
        if len(expression.args) != 1 or not expression.variable:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                ("integral_requires_argument_and_variable",),
            )
        integrand = infer_expression_dimension(expression.args[0], symbol_dimensions)
        variable_dimension = symbol_dimensions.get(expression.variable)
        if integrand.verdict is not DimensionVerdict.PASS or variable_dimension is None:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                integrand.reasons + (f"integral_variable_dimension_missing:{expression.variable}",),
            )
        assert integrand.dimension is not None
        return DimensionInference(
            DimensionVerdict.PASS,
            integrand.dimension.multiply(variable_dimension),
        )

    if expression.op in {ExprOp.EXPECTATION, ExprOp.SUM}:
        if len(expression.args) != 1:
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                (f"{expression.op.value.lower()}_requires_one_arg",),
            )
        return infer_expression_dimension(expression.args[0], symbol_dimensions)

    if expression.op is ExprOp.FUNCTION:
        inputs = tuple(infer_expression_dimension(arg, symbol_dimensions) for arg in expression.args)
        if any(item.verdict is not DimensionVerdict.PASS for item in inputs):
            return DimensionInference(
                DimensionVerdict.CANNOT_CHECK,
                None,
                tuple(reason for item in inputs for reason in item.reasons),
            )
        dimensionless_functions = {"exp", "log", "sin", "cos", "tan", "sigmoid", "softplus"}
        if (expression.function_name or "").lower() in dimensionless_functions:
            if any(item.dimension != Dimension.dimensionless() for item in inputs):
                return DimensionInference(
                    DimensionVerdict.FAIL,
                    None,
                    ("dimensionful_argument_to_dimensionless_function",),
                )
            return DimensionInference(DimensionVerdict.PASS, Dimension.dimensionless())
        return DimensionInference(
            DimensionVerdict.CANNOT_CHECK,
            None,
            (f"function_dimension_rule_unknown:{expression.function_name}",),
        )

    return DimensionInference(
        DimensionVerdict.CANNOT_CHECK,
        None,
        (f"unsupported_expression_operator:{expression.op.value}",),
    )


def check_equation_dimensions(
    equation: FormalEquation,
    symbol_dimensions: Mapping[str, Dimension],
) -> EquationDimensionReport:
    lhs = infer_expression_dimension(equation.lhs, symbol_dimensions)
    rhs = infer_expression_dimension(equation.rhs, symbol_dimensions)
    if lhs.verdict is DimensionVerdict.FAIL or rhs.verdict is DimensionVerdict.FAIL:
        return EquationDimensionReport(
            equation.equation_id,
            DimensionVerdict.FAIL,
            lhs.dimension,
            rhs.dimension,
            lhs.reasons + rhs.reasons,
        )
    if lhs.verdict is DimensionVerdict.CANNOT_CHECK or rhs.verdict is DimensionVerdict.CANNOT_CHECK:
        return EquationDimensionReport(
            equation.equation_id,
            DimensionVerdict.CANNOT_CHECK,
            lhs.dimension,
            rhs.dimension,
            lhs.reasons + rhs.reasons,
        )
    if lhs.dimension != rhs.dimension:
        return EquationDimensionReport(
            equation.equation_id,
            DimensionVerdict.FAIL,
            lhs.dimension,
            rhs.dimension,
            ("lhs_rhs_dimension_mismatch",),
        )
    return EquationDimensionReport(
        equation.equation_id,
        DimensionVerdict.PASS,
        lhs.dimension,
        rhs.dimension,
        ("lhs_rhs_dimensions_match",),
    )


def check_formalism_dimensions(
    formalism: Formalism,
    symbol_dimensions: Mapping[str, Dimension],
) -> FormalismDimensionReport:
    reports = tuple(
        check_equation_dimensions(equation, symbol_dimensions)
        for equation in formalism.equations
    )
    if any(report.verdict is DimensionVerdict.FAIL for report in reports):
        return FormalismDimensionReport(
            formalism.formalism_id,
            DimensionVerdict.FAIL,
            reports,
            ("one_or_more_equations_dimensionally_invalid",),
        )
    if any(report.verdict is DimensionVerdict.CANNOT_CHECK for report in reports):
        return FormalismDimensionReport(
            formalism.formalism_id,
            DimensionVerdict.CANNOT_CHECK,
            reports,
            ("one_or_more_equations_dimensionally_unresolved",),
        )
    return FormalismDimensionReport(
        formalism.formalism_id,
        DimensionVerdict.PASS,
        reports,
        ("all_equations_dimensionally_consistent",),
    )
