from __future__ import annotations

from rakl.self_bootstrap import BootstrapTrial, BootstrapVerdict, evaluate_bootstrap_trial


ROUTES = (
    "scientific_method",
    "metacognition",
    "experiment_design",
    "formal_methods",
    "local_global",
    "causal_identification",
    "retrieval_memory",
    "software_reliability",
    "self_improving_agents",
    "scientific_visualization",
    "cross_domain_workflows",
)


def trial(**overrides):
    base = dict(
        benchmark_frozen_before_candidate=True,
        hidden_weakness_label_exposed=False,
        route_families_required=ROUTES,
        route_families_covered=ROUTES,
        route_semantically_flat_or_blocked=True,
        weakness_detected=True,
        weakness_correct=True,
        weakness_type="METHOD_BASIS_GAP",
        epistemic_cut_localized=True,
        candidate_operator_family="new-operator",
        candidate_frozen_before_outcomes=True,
        candidate_semantically_equivalent_to_incumbent=False,
        alternatives_remain_compatible=False,
        development_delta=0.2,
        development_material_threshold=0.05,
        fresh_assurance_delta=0.15,
        assurance_material_threshold=0.05,
        fresh_assurance_executed=True,
        assurance_exposed_to_optimizer=False,
        assurance_evidence_lineage_independent=True,
        blocking_failures=(),
        negative_history_preserved=True,
        evaluator_separated_from_challenger=True,
        matched_resource_accounting=True,
        matched_baseline_complete=True,
    )
    base.update(overrides)
    return BootstrapTrial(**base)


def test_strong_positive_requires_fresh_assurance_and_clean_governance():
    report = evaluate_bootstrap_trial(trial())
    assert report.verdict is BootstrapVerdict.SCOPED_BOOTSTRAP_EVOLUTION_EVIDENCE
    assert report.grants_method_promotion is False
    assert report.grants_independent_review_credit is False
    assert report.grants_global_framework_saturation is False


def test_development_only_gain_is_local_improvement():
    report = evaluate_bootstrap_trial(
        trial(fresh_assurance_executed=False, fresh_assurance_delta=None)
    )
    assert report.verdict is BootstrapVerdict.LOCAL_IMPROVEMENT_ONLY


def test_development_gain_with_assurance_regression_is_meta_overfit():
    report = evaluate_bootstrap_trial(trial(fresh_assurance_delta=-0.1))
    assert report.verdict is BootstrapVerdict.META_OVERFIT


def test_hidden_label_exposure_invalidates_trial():
    report = evaluate_bootstrap_trial(trial(hidden_weakness_label_exposed=True))
    assert report.verdict is BootstrapVerdict.TRIAL_INVALID


def test_assurance_exposure_to_optimizer_invalidates_trial():
    report = evaluate_bootstrap_trial(trial(assurance_exposed_to_optimizer=True))
    assert report.verdict is BootstrapVerdict.TRIAL_INVALID


def test_missing_route_coverage_invalidates_saturation_based_bootstrap():
    report = evaluate_bootstrap_trial(trial(route_families_covered=ROUTES[:-1]))
    assert report.verdict is BootstrapVerdict.TRIAL_INVALID
    assert any(reason.startswith("route_not_covered") for reason in report.reasons)


def test_semantically_equivalent_challenger_is_not_improvement():
    report = evaluate_bootstrap_trial(
        trial(candidate_semantically_equivalent_to_incumbent=True)
    )
    assert report.verdict is BootstrapVerdict.NO_IMPROVEMENT


def test_missing_data_does_not_become_missing_method_operator():
    report = evaluate_bootstrap_trial(
        trial(
            weakness_type="MISSING_EVIDENCE",
            candidate_operator_family=None,
            development_delta=None,
            fresh_assurance_delta=None,
            fresh_assurance_executed=False,
        )
    )
    assert report.verdict is BootstrapVerdict.LOCAL_IMPROVEMENT_ONLY


def test_implementation_bug_does_not_become_method_basis_gap():
    report = evaluate_bootstrap_trial(
        trial(
            weakness_type="IMPLEMENTATION_DEFECT",
            candidate_operator_family=None,
            development_delta=None,
            fresh_assurance_delta=None,
            fresh_assurance_executed=False,
        )
    )
    assert report.verdict is BootstrapVerdict.LOCAL_IMPROVEMENT_ONLY


def test_multiple_compatible_operator_families_remain_partially_identified():
    report = evaluate_bootstrap_trial(trial(alternatives_remain_compatible=True))
    assert report.verdict is BootstrapVerdict.PARTIALLY_IDENTIFIED


def test_no_surviving_weakness_does_not_force_change():
    report = evaluate_bootstrap_trial(
        trial(
            weakness_detected=False,
            weakness_correct=False,
            epistemic_cut_localized=False,
            candidate_operator_family=None,
            development_delta=None,
            fresh_assurance_delta=None,
            fresh_assurance_executed=False,
        )
    )
    assert report.verdict is BootstrapVerdict.NO_IMPROVEMENT


def test_blocking_failure_invalidates_positive_score():
    report = evaluate_bootstrap_trial(trial(blocking_failures=("negative_history_loss",)))
    assert report.verdict is BootstrapVerdict.TRIAL_INVALID
