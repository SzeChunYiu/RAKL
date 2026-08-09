from rakl.formalism import (
    EquationKind,
    ExprOp,
    FormalExpression,
    FormalSymbol,
    Formalism,
    MechanismEdge,
    MechanismGraph,
    MechanismNode,
    MechanismNodeKind,
    MechanismRelation,
    SymbolRole,
)
from rakl.mechanism_compiler import (
    InteractionLaw,
    MechanismCompileVerdict,
    StateEvolutionSpec,
    compile_mechanism_equations,
)


def _formalism():
    return Formalism(
        "f",
        "spot",
        symbols=(
            FormalSymbol("x", SymbolRole.STATE, "real", units="return"),
            FormalSymbol("q", SymbolRole.OBSERVABLE, "real", units="flow"),
            FormalSymbol("t", SymbolRole.CLOCK, "positive", units="time"),
            FormalSymbol("beta", SymbolRole.PARAMETER, "real", units="return/flow/time"),
        ),
        equations=(),
        mechanism=MechanismGraph(
            "m",
            nodes=(
                MechanismNode("nx", MechanismNodeKind.STATE, "return state", symbol="x"),
                MechanismNode("nq", MechanismNodeKind.OBSERVABLE, "flow", symbol="q"),
            ),
            edges=(
                MechanismEdge("e", "nq", "nx", MechanismRelation.CAUSES, sign=1),
            ),
        ),
    )


def test_compiler_materializes_mechanism_dynamics():
    contribution = FormalExpression(
        ExprOp.MUL,
        args=(FormalExpression.sym("beta"), FormalExpression.sym("q")),
    )
    report = compile_mechanism_equations(
        _formalism(),
        laws=(
            InteractionLaw(
                "law",
                "e",
                contribution,
                "x",
                declared_before_evaluation=True,
            ),
        ),
        specs=(StateEvolutionSpec("x", "t", EquationKind.DIFFERENTIAL),),
    )
    assert report.verdict is MechanismCompileVerdict.COMPILED
    assert report.equations[0].lhs.op is ExprOp.DERIVATIVE
    assert report.equations[0].derivation_ids == ("law",)


def test_compiler_surfaces_unformalized_influential_edge():
    report = compile_mechanism_equations(
        _formalism(),
        laws=(),
        specs=(StateEvolutionSpec("x", "t", EquationKind.DIFFERENTIAL),),
    )
    assert report.verdict is MechanismCompileVerdict.CANNOT_CHECK
    assert report.missing_edge_ids == ("e",)


def test_post_result_interaction_law_is_rejected():
    report = compile_mechanism_equations(
        _formalism(),
        laws=(
            InteractionLaw(
                "law",
                "e",
                FormalExpression.sym("q"),
                "x",
                declared_before_evaluation=False,
            ),
        ),
        specs=(StateEvolutionSpec("x", "t"),),
    )
    assert report.verdict is MechanismCompileVerdict.REJECT
