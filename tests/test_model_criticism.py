from __future__ import annotations

from rakl.model_criticism import (
    CriticismProbe,
    ModelCriticismTrial,
    ModelCriticismVerdict,
    evaluate_model_criticism,
)


def _samples(center: float, n: int = 199):
    # Symmetric deterministic predictive sample grid with enough resolution for
    # alpha=0.05 two-sided empirical checks.
    return tuple(center + (i - (n - 1) / 2) / 20.0 for i in range(n))


def _trial(probes, **overrides):
    base = dict(
        model_id="M",
        observed_population_id="P",
        predictive_population_id="P",
        probes=tuple(probes),
        probe_family_frozen_before_results=True,
        hidden_confirmation_outcomes_exposed_before_freeze=False,
        family_alpha=0.05,
        multiplicity_policy="BONFERRONI" if len(probes) > 1 else "SINGLE",
        predictive_distribution_bound_to_model=True,
        residual_mapping_predeclared=True,
    )
    base.update(overrides)
    return ModelCriticismTrial(**base)


def test_well_calibrated_model_is_only_adequate_on_frozen_probes():
    probe = CriticismProbe(
        probe_id="mean",
        scientific_coordinate="return_center",
        context_scope=("spot", "5m"),
        observed_statistic=0.0,
        predictive_samples=_samples(0.0),
        materiality_tolerance=0.5,
        frozen_before_results=True,
    )
    report = evaluate_model_criticism(_trial((probe,)))
    assert report.verdict is ModelCriticismVerdict.ADEQUATE_ON_FROZEN_PROBES_PROPOSAL_ONLY
    assert report.grants_scientific_truth is False
    assert report.grants_mechanism_authority is False
    assert report.establishes_global_model_closure is False


def test_tail_or_other_frozen_statistic_can_create_structured_residual():
    probe = CriticismProbe(
        probe_id="tail-frequency",
        scientific_coordinate="tail_or_jump_coordinate",
        context_scope=("spot", "5m"),
        observed_statistic=20.0,
        predictive_samples=_samples(0.0),
        materiality_tolerance=5.0,
        frozen_before_results=True,
    )
    report = evaluate_model_criticism(_trial((probe,)))
    assert report.verdict is ModelCriticismVerdict.STRUCTURED_RESIDUAL_DETECTED
    assert report.residual_coordinates == ("tail_or_jump_coordinate",)


def test_memory_residual_is_localized_by_probe_coordinate_not_invented_mechanism():
    probe = CriticismProbe(
        probe_id="acf",
        scientific_coordinate="memory_or_dependence_coordinate",
        context_scope=("spot", "15m"),
        observed_statistic=20.0,
        predictive_samples=_samples(0.0),
        materiality_tolerance=3.0,
        frozen_before_results=True,
    )
    report = evaluate_model_criticism(_trial((probe,)))
    assert report.verdict is ModelCriticismVerdict.STRUCTURED_RESIDUAL_DETECTED
    assert "memory_or_dependence_coordinate" in report.residual_coordinates
    assert report.grants_mechanism_authority is False


def test_posthoc_probe_family_invalidates_trial():
    probe = CriticismProbe("p", "x", ("scope",), 0.0, _samples(0.0), 1.0, True)
    report = evaluate_model_criticism(_trial((probe,), probe_family_frozen_before_results=False))
    assert report.verdict is ModelCriticismVerdict.TRIAL_INVALID


def test_too_few_predictive_samples_cannot_resolve_declared_tail_threshold():
    probe = CriticismProbe("p", "x", ("scope",), 10.0, (0.0, 1.0, 2.0), 1.0, True)
    report = evaluate_model_criticism(_trial((probe,)))
    assert report.verdict is ModelCriticismVerdict.CANNOT_CHECK
    assert any("insufficient" in reason for reason in report.reasons)


def test_multiple_probe_family_requires_supported_frozen_multiplicity_policy():
    p1 = CriticismProbe("p1", "x", ("scope",), 0.0, _samples(0.0, 399), 1.0, True)
    p2 = CriticismProbe("p2", "y", ("scope",), 0.0, _samples(0.0, 399), 1.0, True)
    report = evaluate_model_criticism(_trial((p1, p2), multiplicity_policy="NONE"))
    assert report.verdict is ModelCriticismVerdict.CANNOT_CHECK


def test_population_mismatch_cannot_be_called_model_failure():
    probe = CriticismProbe("p", "x", ("scope",), 0.0, _samples(0.0), 1.0, True)
    report = evaluate_model_criticism(_trial((probe,), predictive_population_id="OTHER"))
    assert report.verdict is ModelCriticismVerdict.CANNOT_CHECK


def test_failed_probe_with_posthoc_residual_interpretation_is_partial_only():
    probe = CriticismProbe("p", "unknown_residual", ("scope",), 20.0, _samples(0.0), 1.0, True)
    report = evaluate_model_criticism(_trial((probe,), residual_mapping_predeclared=False))
    assert report.verdict is ModelCriticismVerdict.PARTIALLY_IDENTIFIED


def test_confirmation_outcomes_exposed_before_freeze_invalidates_trial():
    probe = CriticismProbe("p", "x", ("scope",), 0.0, _samples(0.0), 1.0, True)
    report = evaluate_model_criticism(
        _trial((probe,), hidden_confirmation_outcomes_exposed_before_freeze=True)
    )
    assert report.verdict is ModelCriticismVerdict.TRIAL_INVALID
