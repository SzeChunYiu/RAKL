from rakl.formalism import EquationKind, ExprOp, FormalEquation, FormalExpression
from rakl.math_oracles import (
    Dimension,
    DimensionVerdict,
    check_equation_dimensions,
)


def test_multiplicative_dimension_composition_passes():
    velocity = Dimension.from_mapping({"length": 1, "time": -1})
    time = Dimension.from_mapping({"time": 1})
    length = Dimension.from_mapping({"length": 1})
    equation = FormalEquation(
        "distance",
        FormalExpression.sym("x"),
        FormalExpression(
            ExprOp.MUL,
            args=(FormalExpression.sym("v"), FormalExpression.sym("t")),
        ),
        EquationKind.ALGEBRAIC,
    )
    report = check_equation_dimensions(
        equation,
        {"x": length, "v": velocity, "t": time},
    )
    assert report.verdict is DimensionVerdict.PASS


def test_addition_of_incompatible_dimensions_fails():
    equation = FormalEquation(
        "bad",
        FormalExpression.sym("x"),
        FormalExpression(
            ExprOp.ADD,
            args=(FormalExpression.sym("x"), FormalExpression.sym("t")),
        ),
        EquationKind.ALGEBRAIC,
    )
    report = check_equation_dimensions(
        equation,
        {
            "x": Dimension.from_mapping({"length": 1}),
            "t": Dimension.from_mapping({"time": 1}),
        },
    )
    assert report.verdict is DimensionVerdict.FAIL


def test_derivative_dimension_is_inferred():
    equation = FormalEquation(
        "velocity",
        FormalExpression.sym("v"),
        FormalExpression(
            ExprOp.DERIVATIVE,
            args=(FormalExpression.sym("x"),),
            variable="t",
        ),
        EquationKind.DIFFERENTIAL,
    )
    report = check_equation_dimensions(
        equation,
        {
            "v": Dimension.from_mapping({"length": 1, "time": -1}),
            "x": Dimension.from_mapping({"length": 1}),
            "t": Dimension.from_mapping({"time": 1}),
        },
    )
    assert report.verdict is DimensionVerdict.PASS
