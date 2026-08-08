from rakl.meta import (
    ConstitutionGuard,
    MetaEvaluation,
    MethodChangeClass,
    ResearchBudget,
    ResearchPortfolioScheduler,
)


def clean_eval(**overrides):
    values = dict(
        tests_passed=True,
        receipt_present=True,
        benchmark_frozen_before_result=True,
        history_preserved=True,
        blocking_failures=(),
        improvements={"semantic_recall": 0.1},
        regressions={},
        independent_review_passed=False,
    )
    values.update(overrides)
    return MetaEvaluation(**values)


def test_implementation_change_can_auto_promote_when_clean():
    ok, reasons = ConstitutionGuard.can_auto_promote(
        MethodChangeClass.IMPLEMENTATION,
        clean_eval(),
    )
    assert ok is True
    assert reasons == ()


def test_workflow_change_requires_positive_registered_improvement():
    ok, reasons = ConstitutionGuard.can_auto_promote(
        MethodChangeClass.WORKFLOW,
        clean_eval(improvements={"semantic_recall": 0.0}),
    )
    assert ok is False
    assert any("no registered positive" in reason for reason in reasons)


def test_constitution_change_never_self_promotes():
    ok, reasons = ConstitutionGuard.can_auto_promote(
        MethodChangeClass.CONSTITUTION,
        clean_eval(independent_review_passed=True),
    )
    assert ok is False
    assert any("constitutional" in reason for reason in reasons)


def test_blocking_failure_beats_efficiency_gain():
    ok, reasons = ConstitutionGuard.can_auto_promote(
        MethodChangeClass.WORKFLOW,
        clean_eval(
            blocking_failures=("fabricated citation",),
            improvements={"token_cost": 0.9},
        ),
    )
    assert ok is False
    assert any("fabricated citation" in reason for reason in reasons)


def test_default_research_budget_is_non_greedy():
    budget = ResearchBudget()
    assert budget.exploit < 1.0
    assert budget.diversify > 0
    assert budget.moonshot > 0
    assert budget.meta_rakl > 0


def test_saturation_wall_expands_action_surface():
    scheduler = ResearchPortfolioScheduler()
    baseline = scheduler.allocate()
    wall = scheduler.allocate(saturation_wall=True)
    assert wall.exploit < baseline.exploit
    assert wall.diversify > baseline.diversify
    assert wall.moonshot > baseline.moonshot
    assert wall.meta_rakl > baseline.meta_rakl


def test_high_value_residual_focuses_without_zeroing_diversity():
    scheduler = ResearchPortfolioScheduler()
    budget = scheduler.allocate(high_value_residual=True)
    assert budget.exploit == 0.70
    assert budget.diversify > 0
    assert budget.moonshot > 0
    assert budget.meta_rakl > 0
