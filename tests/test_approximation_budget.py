from rakl.approximation_budget import *


def step(name, error, scope="s", metric="m"):
    return ApproximationStep(name, scope, metric, error, ("receipt",))


def test_additive_error_composition_can_exceed_local_tolerances():
    b = ApproximationBudget("b", "s", "m", .25, ErrorComposition.ADDITIVE)
    result = assess_composed_approximation(b, (step("a", .15), step("b", .15)))
    assert result.verdict is ApproximationVerdict.EXCEEDS_BUDGET


def test_max_composition_and_scope_binding():
    b = ApproximationBudget("b", "s", "m", .2, ErrorComposition.MAX)
    assert assess_composed_approximation(b, (step("a", .1), step("b", .2))).verdict is ApproximationVerdict.WITHIN_BUDGET
    assert assess_composed_approximation(b, (step("x", .1, scope="other"),)).verdict is ApproximationVerdict.CANNOT_CHECK


def test_custom_law_fails_closed_without_executed_evaluator():
    b = ApproximationBudget("b", "s", "m", 1, ErrorComposition.REGISTERED_CUSTOM, "law-receipt")
    assert assess_composed_approximation(b, (step("a", .1),)).verdict is ApproximationVerdict.CANNOT_CHECK
