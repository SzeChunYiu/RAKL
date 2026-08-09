from rakl.formalism import (
    EquationKind,
    ExprOp,
    FormalEquation,
    FormalExpression,
    FormalSymbol,
    Formalism,
    FormalismStructureVerdict,
    MechanismGraph,
    MechanismNode,
    MechanismNodeKind,
    SymbolRole,
    VerificationPacket,
    VerificationVerdict,
    validate_formalism_structure,
    verify_formalism,
)


def _base_formalism() -> Formalism:
    x = FormalSymbol("x", SymbolRole.STATE, domain="real", units="price")
    y = FormalSymbol("y", SymbolRole.OBSERVABLE, domain="real", units="price")
    equation = FormalEquation(
        "eq_y",
        FormalExpression.sym("y"),
        FormalExpression.sym("x"),
        EquationKind.OBSERVATION,
        unit_balance_passed=True,
    )
    mechanism = MechanismGraph(
        "m0",
        nodes=(
            MechanismNode("n_x", MechanismNodeKind.STATE, "state", symbol="x"),
            MechanismNode("n_y", MechanismNodeKind.OBSERVABLE, "observed", symbol="y"),
        ),
        edges=(),
    )
    return Formalism("f0", "spot", (x, y), (equation,), mechanism)


def test_typed_formalism_structure_validates_symbol_references():
    report = validate_formalism_structure(_base_formalism())
    assert report.verdict is FormalismStructureVerdict.VALID


def test_unknown_symbol_fails_closed():
    formalism = _base_formalism()
    bad = FormalEquation(
        "eq_bad",
        FormalExpression.sym("y"),
        FormalExpression(ExprOp.ADD, args=(FormalExpression.sym("x"), FormalExpression.sym("z"))),
        EquationKind.ALGEBRAIC,
    )
    formalism = Formalism(
        "f_bad",
        formalism.object_id,
        formalism.symbols,
        formalism.equations + (bad,),
        formalism.mechanism,
    )
    report = validate_formalism_structure(formalism)
    assert report.verdict is FormalismStructureVerdict.REJECT
    assert "z" in report.unknown_symbols


def test_verification_packet_is_bound_to_exact_candidate():
    formalism = _base_formalism()
    packet = VerificationPacket(
        formalism_id="other",
        dimensional_analysis_passed=True,
        limiting_cases_passed=True,
        invariants_passed=True,
        stability_passed=True,
        identifiability_passed=True,
        simulation_sanity_passed=True,
        leakage_checks_passed=True,
        falsifier_execution_passed=True,
        evidence_lineage_ids=("receipt:1",),
    )
    report = verify_formalism(formalism, packet)
    assert report.verdict is VerificationVerdict.FAIL


def test_all_required_oracles_can_pass():
    formalism = _base_formalism()
    packet = VerificationPacket(
        formalism_id="f0",
        dimensional_analysis_passed=True,
        limiting_cases_passed=True,
        invariants_passed=True,
        stability_passed=True,
        identifiability_passed=True,
        simulation_sanity_passed=True,
        leakage_checks_passed=True,
        falsifier_execution_passed=True,
        evidence_lineage_ids=("receipt:1", "receipt:2"),
    )
    report = verify_formalism(formalism, packet)
    assert report.verdict is VerificationVerdict.PASS
