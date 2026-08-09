from rakl.formalism import (
    EquationKind,
    FormalEquation,
    FormalExpression,
    FormalSymbol,
    Formalism,
    MechanismGraph,
    MechanismNode,
    MechanismNodeKind,
    SymbolRole,
    VerificationReport,
    VerificationVerdict,
)
from rakl.invention import (
    CandidateMutationVerdict,
    CandidateScore,
    CandidateTheory,
    GoalAssessmentVerdict,
    InventionMove,
    InventionOperator,
    PositiveGoalContract,
    ResidualKind,
    ResidualSignature,
    apply_invention_move,
    continuation_required,
    evaluate_positive_goal,
    invention_tasks_for_residual,
    pareto_frontier,
    recombine_candidates,
    residual_from_goal_assessment,
)


def _candidate() -> CandidateTheory:
    x = FormalSymbol("x", SymbolRole.STATE, domain="real", units="return")
    equation = FormalEquation(
        "eq_x",
        FormalExpression.sym("x"),
        FormalExpression.sym("x"),
        EquationKind.DEFINITION,
        unit_balance_passed=True,
    )
    mechanism = MechanismGraph(
        "m0",
        (MechanismNode("n_x", MechanismNodeKind.STATE, "spot state", symbol="x"),),
        (),
        source_fiber_ids=("fiber:spot",),
    )
    return CandidateTheory(
        "c0",
        Formalism("f0", "spot", (x,), (equation,), mechanism),
    )


def test_residual_routes_to_constructive_operators():
    residual = ResidualSignature(
        "r1",
        (ResidualKind.REGIME, ResidualKind.VOLATILITY),
        "variance and sign persistence change sharply across hidden states",
        implicated_fiber_ids=("fiber:regime",),
        evidence_ids=("receipt:r1",),
    )
    tasks = invention_tasks_for_residual(residual)
    operators = {task.operator for task in tasks}
    assert InventionOperator.SPLIT_REGIME in operators
    assert InventionOperator.ADD_LATENT_STATE in operators
    assert InventionOperator.ADD_FEEDBACK in operators


def test_typed_invention_move_preserves_lineage():
    parent = _candidate()
    latent = FormalSymbol("z", SymbolRole.LATENT_STATE, domain="real", units="state")
    move = InventionMove(
        move_id="move:add-z",
        operator=InventionOperator.ADD_LATENT_STATE,
        rationale="hidden state explains the registered regime residual",
        residual_ids=("r1",),
        source_fiber_ids=("fiber:regime",),
        add_symbols=(latent,),
        add_mechanism_nodes=(
            MechanismNode("n_z", MechanismNodeKind.LATENT_STATE, "latent regime", symbol="z"),
        ),
        declared_before_evaluation=True,
    )
    report = apply_invention_move(
        parent,
        move,
        candidate_id="c1",
        formalism_id="f1",
    )
    assert report.candidate is not None
    assert report.candidate.parent_candidate_ids == ("c0",)
    assert report.candidate.move_history == ("move:add-z",)
    assert "z" in report.candidate.formalism.symbol_map()


def test_recombination_allows_identical_shared_ancestry():
    root = _candidate()
    left_move = InventionMove(
        move_id="left",
        operator=InventionOperator.ADD_LATENT_STATE,
        rationale="left branch",
        residual_ids=("r1",),
        add_symbols=(FormalSymbol("z", SymbolRole.LATENT_STATE, "real", units="state"),),
        add_mechanism_nodes=(
            MechanismNode("n_z", MechanismNodeKind.LATENT_STATE, "z", symbol="z"),
        ),
        declared_before_evaluation=True,
    )
    right_move = InventionMove(
        move_id="right",
        operator=InventionOperator.ADD_LATENT_STATE,
        rationale="right branch",
        residual_ids=("r1",),
        add_symbols=(FormalSymbol("w", SymbolRole.LATENT_STATE, "real", units="state"),),
        add_mechanism_nodes=(
            MechanismNode("n_w", MechanismNodeKind.LATENT_STATE, "w", symbol="w"),
        ),
        declared_before_evaluation=True,
    )
    left = apply_invention_move(root, left_move, candidate_id="left", formalism_id="fl").candidate
    right = apply_invention_move(root, right_move, candidate_id="right", formalism_id="fr").candidate
    assert left is not None and right is not None
    merge = InventionMove(
        move_id="merge",
        operator=InventionOperator.RECOMBINE,
        rationale="combine non-equivalent latent coordinates",
        residual_ids=("r1",),
        declared_before_evaluation=True,
    )
    report = recombine_candidates(
        left,
        right,
        merge,
        candidate_id="merged",
        formalism_id="fm",
    )
    assert report.verdict is CandidateMutationVerdict.CREATED
    assert report.candidate is not None
    assert set(report.candidate.formalism.symbol_map()) == {"x", "z", "w"}
    assert report.candidate.parent_candidate_ids == ("left", "right")


def test_pareto_frontier_keeps_non_dominated_theories():
    strong = CandidateScore("strong", 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.6, 2.0)
    weak = CandidateScore("weak", 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 3.0)
    novel = CandidateScore("novel", 0.8, 0.8, 0.7, 0.7, 0.8, 0.7, 0.95, 2.5)
    frontier = {score.candidate_id for score in pareto_frontier((strong, weak, novel))}
    assert "weak" not in frontier
    assert frontier == {"strong", "novel"}


def _contract() -> PositiveGoalContract:
    return PositiveGoalContract(
        contract_id="spot-positive-v1",
        min_descriptive_coverage=0.8,
        min_residual_closure=0.8,
        min_predictive_value=0.7,
        min_identification=0.6,
        min_falsifiability=0.8,
        min_robustness=0.7,
        thresholds_frozen_before_results=True,
    )


def test_failed_candidate_is_nonterminal_and_requires_continuation():
    score = CandidateScore("c1", 0.9, 0.4, 0.2, 0.8, 0.9, 0.8, 0.7, 2.0)
    verification = VerificationReport(VerificationVerdict.PASS, ("ok",))
    assessment = evaluate_positive_goal(_contract(), score, verification)
    assert assessment.verdict is GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE
    assert continuation_required(assessment)


def test_failed_goal_becomes_typed_residual_for_next_round():
    score = CandidateScore("c1", 0.9, 0.4, 0.2, 0.8, 0.9, 0.6, 0.7, 2.0)
    assessment = evaluate_positive_goal(
        _contract(),
        score,
        VerificationReport(VerificationVerdict.PASS, ("ok",)),
    )
    residual = residual_from_goal_assessment(
        assessment,
        candidate_id="c1",
        residual_id="goal-r1",
        implicated_fiber_ids=("fiber:spot",),
        evidence_ids=("receipt:goal",),
    )
    assert residual is not None
    assert residual.failed_candidate_ids == ("c1",)
    assert ResidualKind.PREDICTIVE in residual.kinds
    assert ResidualKind.TRANSPORT in residual.kinds


def test_goal_only_closes_on_positive_locked_success():
    score = CandidateScore("c2", 0.95, 0.9, 0.8, 0.75, 0.9, 0.85, 0.8, 2.0)
    verification = VerificationReport(VerificationVerdict.PASS, ("all checks passed",))
    assessment = evaluate_positive_goal(_contract(), score, verification)
    assert assessment.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
    assert not continuation_required(assessment)
    assert residual_from_goal_assessment(
        assessment,
        candidate_id="c2",
        residual_id="unused",
    ) is None


def test_post_result_threshold_rescue_is_blocked():
    contract = PositiveGoalContract(
        contract_id="invalid-posthoc",
        min_descriptive_coverage=0.5,
        min_residual_closure=0.5,
        min_predictive_value=0.5,
        min_identification=0.5,
        min_falsifiability=0.5,
        min_robustness=0.5,
        thresholds_frozen_before_results=False,
    )
    score = CandidateScore("c", 1, 1, 1, 1, 1, 1, 1, 1)
    assessment = evaluate_positive_goal(
        contract,
        score,
        VerificationReport(VerificationVerdict.PASS, ("ok",)),
    )
    assert assessment.verdict is GoalAssessmentVerdict.BLOCKED_INTEGRITY
