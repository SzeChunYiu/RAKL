from rakl.availability_oracle import (
    AvailabilityVerdict,
    SymbolAvailability,
    check_predictive_availability,
)
from rakl.formalism import (
    EquationKind,
    ExprOp,
    FormalEquation,
    FormalExpression,
    FormalSymbol,
    Formalism,
    MechanismGraph,
    SymbolRole,
)


def _formalism():
    return Formalism(
        "f",
        "spot",
        symbols=(
            FormalSymbol("future_return", SymbolRole.OBSERVABLE, "real"),
            FormalSymbol("flow", SymbolRole.OBSERVABLE, "real"),
            FormalSymbol("regime", SymbolRole.REGIME, "categorical"),
            FormalSymbol("beta", SymbolRole.PARAMETER, "real"),
        ),
        equations=(
            FormalEquation(
                "predict",
                FormalExpression.sym("future_return"),
                FormalExpression(
                    ExprOp.ADD,
                    args=(
                        FormalExpression(
                            ExprOp.MUL,
                            args=(FormalExpression.sym("beta"), FormalExpression.sym("flow")),
                        ),
                        FormalExpression.sym("regime"),
                    ),
                ),
                EquationKind.STRUCTURAL,
            ),
        ),
        mechanism=MechanismGraph("m", (), ()),
    )


def test_strict_availability_passes_causal_historical_inputs():
    report = check_predictive_availability(
        _formalism(),
        predictive_equation_ids=("predict",),
        availability=(
            SymbolAvailability("flow", -5.0, 1.0, True, evidence_ids=("clock:flow",)),
            SymbolAvailability(
                "regime",
                -1.0,
                0.0,
                True,
                causal_estimator=True,
                estimator_frozen_before_evaluation=True,
                evidence_ids=("clock:regime",),
            ),
        ),
    )
    assert report.verdict is AvailabilityVerdict.PASS


def test_future_arriving_feature_fails():
    report = check_predictive_availability(
        _formalism(),
        predictive_equation_ids=("predict",),
        availability=(
            SymbolAvailability("flow", -0.1, 1.0, True, evidence_ids=("clock:flow",)),
            SymbolAvailability(
                "regime",
                -1.0,
                0.0,
                True,
                causal_estimator=True,
                estimator_frozen_before_evaluation=True,
                evidence_ids=("clock:regime",),
            ),
        ),
    )
    assert report.verdict is AvailabilityVerdict.FAIL
    assert "flow" in report.failed_symbols


def test_latent_regime_requires_frozen_causal_estimator():
    report = check_predictive_availability(
        _formalism(),
        predictive_equation_ids=("predict",),
        availability=(
            SymbolAvailability("flow", -5.0, 1.0, True, evidence_ids=("clock:flow",)),
            SymbolAvailability("regime", -1.0, 0.0, True, causal_estimator=False, evidence_ids=("clock:regime",)),
        ),
    )
    assert report.verdict is AvailabilityVerdict.FAIL
    assert "regime" in report.failed_symbols
