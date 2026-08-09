from rakl.symbolic_discovery import (
    SymbolicDiscoverySpec,
    SymbolicSearchVerdict,
    discover_symbolic_laws,
    evaluate_expression,
)


def test_symbolic_search_recovers_simple_nonlinear_law():
    rows = tuple(
        {"x": float(x), "y": 1.0 + 2.0 * float(x) ** 2}
        for x in range(-8, 9)
    )
    report = discover_symbolic_laws(
        rows,
        SymbolicDiscoverySpec(
            target_symbol="y",
            feature_symbols=("x",),
            constants=(1.0,),
            max_depth=1,
            beam_width=20,
            max_generated=200,
            rows_are_training_partition=True,
            operator_set_frozen_before_scoring=True,
        ),
        top_k=10,
    )
    assert report.verdict is SymbolicSearchVerdict.COMPLETE
    best = report.candidates[0]
    assert best.normalized_mse < 1e-20
    for row in rows:
        assert abs(evaluate_expression(best.expression, row) - row["y"]) < 1e-8


def test_symbolic_search_can_recover_interaction_term():
    rows = tuple(
        {"x": float(x), "z": float(z), "y": 3.0 * float(x) * float(z) - 0.5}
        for x, z in zip(range(1, 16), range(16, 1, -1))
    )
    report = discover_symbolic_laws(
        rows,
        SymbolicDiscoverySpec(
            target_symbol="y",
            feature_symbols=("x", "z"),
            max_depth=1,
            beam_width=30,
            max_generated=500,
            rows_are_training_partition=True,
            operator_set_frozen_before_scoring=True,
        ),
        top_k=10,
    )
    assert report.verdict is SymbolicSearchVerdict.COMPLETE
    assert report.candidates[0].normalized_mse < 1e-20


def test_symbolic_search_refuses_nontraining_rows():
    report = discover_symbolic_laws(
        ({"x": 1.0, "y": 2.0},) * 5,
        SymbolicDiscoverySpec(
            target_symbol="y",
            feature_symbols=("x",),
            rows_are_training_partition=False,
            operator_set_frozen_before_scoring=True,
        ),
    )
    assert report.verdict is SymbolicSearchVerdict.CANNOT_CHECK
