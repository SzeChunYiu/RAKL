from __future__ import annotations

from rakl.assumption_sensitivity import (
    AssumptionScenario,
    AssumptionSensitivityTrial,
    AssumptionSensitivityVerdict,
    ConclusionClass,
    evaluate_assumption_sensitivity,
)


BASE_SCOPE = ("asset:btc", "venue:spot", "horizon:5m")


def _scenario(sid: str, estimate, *, scope=BASE_SCOPE, qoi="return_effect", frozen=True):
    return AssumptionScenario(
        scenario_id=sid,
        assumption_id=f"assumption:{sid}",
        context_scope=scope,
        target_qoi=qoi,
        estimate=estimate,
        frozen_before_results=frozen,
        evidence_id=f"evidence:{sid}",
    )


def _trial(scenarios, **overrides):
    base = dict(
        baseline_id="baseline",
        baseline_estimate=0.30,
        material_delta=0.10,
        baseline_context_scope=BASE_SCOPE,
        baseline_target_qoi="return_effect",
        scenarios=tuple(scenarios),
        scenario_family_frozen_before_results=True,
        hidden_confirmation_outcomes_exposed_before_freeze=False,
        envelope_complete_for_registered_question=True,
        negative_history_preserved=True,
    )
    base.update(overrides)
    return AssumptionSensitivityTrial(**base)


def test_all_predeclared_scenarios_preserve_positive_conclusion():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25), _scenario("b", 0.18)))
    )
    assert report.verdict is AssumptionSensitivityVerdict.ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY
    assert report.baseline_conclusion is ConclusionClass.POSITIVE
    assert report.sensitive_scenario_ids == ()
    assert report.grants_assumption_truth is False
    assert report.grants_mechanism_authority is False
    assert report.grants_scientific_promotion is False


def test_one_scenario_flips_positive_to_negative():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25), _scenario("b", -0.30)))
    )
    assert report.verdict is AssumptionSensitivityVerdict.ASSUMPTION_SENSITIVE
    assert report.sensitive_scenario_ids == ("b",)


def test_one_scenario_falls_inside_materiality_band_without_sign_flip():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25), _scenario("b", 0.05)))
    )
    assert report.verdict is AssumptionSensitivityVerdict.ASSUMPTION_SENSITIVE
    assert report.scenario_assessments[1].conclusion is ConclusionClass.INDETERMINATE


def test_posthoc_family_selection_invalidates_trial():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25),), scenario_family_frozen_before_results=False)
    )
    assert report.verdict is AssumptionSensitivityVerdict.TRIAL_INVALID


def test_posthoc_individual_scenario_invalidates_trial():
    report = evaluate_assumption_sensitivity(_trial((_scenario("a", 0.25, frozen=False),)))
    assert report.verdict is AssumptionSensitivityVerdict.TRIAL_INVALID


def test_missing_registered_scenario_partially_identifies_robustness():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25), _scenario("b", None)))
    )
    assert report.verdict is AssumptionSensitivityVerdict.PARTIALLY_IDENTIFIED
    assert any("unavailable:b" in reason for reason in report.reasons)


def test_robustness_never_grants_assumption_truth():
    report = evaluate_assumption_sensitivity(_trial((_scenario("a", 0.25),)))
    assert report.verdict is AssumptionSensitivityVerdict.ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY
    assert not report.grants_assumption_truth
    assert not report.grants_mechanism_authority


def test_different_population_or_context_is_not_same_assumption_trial():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25, scope=("asset:eth", "venue:spot", "horizon:5m")),))
    )
    assert report.verdict is AssumptionSensitivityVerdict.CANNOT_COMPARE


def test_changed_target_or_qoi_is_not_same_assumption_trial():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25, qoi="volatility_effect"),))
    )
    assert report.verdict is AssumptionSensitivityVerdict.CANNOT_COMPARE


def test_no_registered_scenarios_cannot_establish_robustness():
    report = evaluate_assumption_sensitivity(_trial(()))
    assert report.verdict is AssumptionSensitivityVerdict.CANNOT_CHECK


def test_confirmation_outcomes_exposed_before_freeze_invalidates_trial():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25),), hidden_confirmation_outcomes_exposed_before_freeze=True)
    )
    assert report.verdict is AssumptionSensitivityVerdict.TRIAL_INVALID


def test_negative_history_must_be_preserved():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25),), negative_history_preserved=False)
    )
    assert report.verdict is AssumptionSensitivityVerdict.TRIAL_INVALID


def test_unknown_envelope_completeness_fails_closed():
    report = evaluate_assumption_sensitivity(
        _trial((_scenario("a", 0.25),), envelope_complete_for_registered_question=None)
    )
    assert report.verdict is AssumptionSensitivityVerdict.CANNOT_CHECK
