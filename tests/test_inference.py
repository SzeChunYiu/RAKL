"""Known-answer validation for the RAKL inference helper.

This module is the instrument that judges every other empirical result in the
framework, so it is validated against worlds whose answer is known in advance
rather than against fixtures that merely exercise the code paths.  The
calibration test is the load-bearing one: it asserts that the false-positive
rate of the rule is at or below its own nominal alpha.  A checker that only
ever tests the alarm case is not evidence of calibration.
"""

from __future__ import annotations

import math
import random

import pytest

from rakl.inference import (
    DEFAULT_ALPHA,
    DistinguishabilityVerdict,
    assess_paired_distinguishability,
    case_resampled_difference_ci,
    holm_bonferroni,
    minimum_detectable_effect,
    paired_bootstrap_ci,
    sign_flip_permutation_p,
)


def _noisy_effect(effect: float, count: int, *, seed: int, spread: float = 0.1) -> list[float]:
    rng = random.Random(seed)
    return [effect + rng.gauss(0.0, spread) for _ in range(count)]


# --------------------------------------------------------------------------
# Known-answer world 1: a large clean effect must be found
# --------------------------------------------------------------------------


def test_large_clean_effect_is_distinguishable_with_interval_excluding_zero() -> None:
    deltas = _noisy_effect(0.40, 16, seed=11)
    assessment = assess_paired_distinguishability(
        deltas, seed=7, resamples=2000, minimum_effect_of_interest=0.10
    )
    assert assessment.verdict is DistinguishabilityVerdict.DISTINGUISHABLE
    assert assessment.interval is not None
    assert assessment.interval.ci_lower > 0.0
    assert assessment.interval.excludes_null
    assert assessment.permutation is not None
    assert assessment.permutation.p_value <= DEFAULT_ALPHA


def test_large_negative_effect_is_distinguishable_and_interval_is_below_zero() -> None:
    deltas = _noisy_effect(-0.40, 16, seed=12)
    assessment = assess_paired_distinguishability(
        deltas, seed=7, resamples=2000, minimum_effect_of_interest=0.10
    )
    assert assessment.verdict is DistinguishabilityVerdict.DISTINGUISHABLE
    assert assessment.interval is not None
    assert assessment.interval.ci_upper < 0.0


# --------------------------------------------------------------------------
# Known-answer world 2: pure noise must not be called an effect
# --------------------------------------------------------------------------


def test_pure_noise_is_not_distinguishable() -> None:
    rng = random.Random(4242)
    deltas = [rng.gauss(0.0, 1.0) for _ in range(16)]
    assessment = assess_paired_distinguishability(
        deltas, seed=3, resamples=2000, minimum_effect_of_interest=2.0
    )
    assert assessment.verdict is not DistinguishabilityVerdict.DISTINGUISHABLE
    assert assessment.interval is not None
    assert not assessment.interval.excludes_null


def test_registered_effect_of_interest_separates_indistinguishable_from_underpowered() -> None:
    """The same null data yields different, and both honest, verdicts.

    With a large registered effect the design could have seen it and did not,
    which is ``INDISTINGUISHABLE``.  With no registered effect at all there is
    no basis for that claim, so the verdict falls back to ``UNDERPOWERED``.
    """

    rng = random.Random(99)
    deltas = [rng.gauss(0.0, 1.0) for _ in range(16)]

    with_registration = assess_paired_distinguishability(
        deltas, seed=5, resamples=1000, minimum_effect_of_interest=5.0
    )
    assert with_registration.verdict is DistinguishabilityVerdict.INDISTINGUISHABLE

    without_registration = assess_paired_distinguishability(deltas, seed=5, resamples=1000)
    assert without_registration.verdict is DistinguishabilityVerdict.UNDERPOWERED
    assert "no_registered_minimum_effect_of_interest" in without_registration.reasons


def test_effect_below_minimum_detectable_effect_is_reported_underpowered() -> None:
    rng = random.Random(2026)
    deltas = [rng.gauss(0.0, 1.0) for _ in range(6)]
    assessment = assess_paired_distinguishability(
        deltas, seed=5, resamples=1000, minimum_effect_of_interest=0.01
    )
    assert assessment.verdict is DistinguishabilityVerdict.UNDERPOWERED
    assert assessment.minimum_detectable_effect is not None
    assert assessment.minimum_detectable_effect > 0.01


# --------------------------------------------------------------------------
# Known-answer world 3: degenerate inputs fail closed
# --------------------------------------------------------------------------


def test_all_zero_deltas_do_not_crash_and_do_not_report_significance() -> None:
    deltas = [0.0] * 8
    permutation = sign_flip_permutation_p(deltas, seed=1, resamples=100)
    assert permutation.p_value == 1.0

    interval = paired_bootstrap_ci(deltas, seed=1, resamples=200)
    assert interval.point_estimate == 0.0
    assert not interval.excludes_null

    assessment = assess_paired_distinguishability(
        deltas, seed=1, resamples=200, minimum_effect_of_interest=0.1
    )
    assert assessment.verdict is not DistinguishabilityVerdict.DISTINGUISHABLE


@pytest.mark.parametrize("deltas", [[], [0.42]])
def test_fewer_than_two_units_fails_closed_as_insufficient_data(deltas: list[float]) -> None:
    assessment = assess_paired_distinguishability(
        deltas, seed=1, resamples=100, minimum_effect_of_interest=0.1
    )
    assert assessment.verdict is DistinguishabilityVerdict.INSUFFICIENT_DATA
    assert assessment.interval is None
    assert assessment.permutation is None
    assert assessment.minimum_detectable_effect == math.inf


def test_empty_delta_vector_raises_rather_than_returning_a_wide_interval() -> None:
    with pytest.raises(ValueError):
        paired_bootstrap_ci([], seed=1, resamples=10)
    with pytest.raises(ValueError):
        sign_flip_permutation_p([], seed=1, resamples=10)


def test_minimum_detectable_effect_is_infinite_below_two_units() -> None:
    assert minimum_detectable_effect(0, 1.0) == math.inf
    assert minimum_detectable_effect(1, 1.0) == math.inf


def test_minimum_detectable_effect_shrinks_as_the_design_grows() -> None:
    small = minimum_detectable_effect(8, 1.0)
    large = minimum_detectable_effect(64, 1.0)
    assert large < small
    # The Student-t correction must make the small design look *less* powerful
    # than a bare normal approximation would, never more.
    normal_only = (1.959963984540054 + 0.8416212335729143) / math.sqrt(8)
    assert small > normal_only


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------


def test_same_seed_reproduces_identical_intervals() -> None:
    deltas = _noisy_effect(0.2, 12, seed=31)
    first = paired_bootstrap_ci(deltas, seed=20260811, resamples=500)
    second = paired_bootstrap_ci(deltas, seed=20260811, resamples=500)
    assert first == second
    assert repr(first) == repr(second)


def test_different_seeds_are_recorded_on_the_interval() -> None:
    deltas = _noisy_effect(0.2, 12, seed=31)
    first = paired_bootstrap_ci(deltas, seed=1, resamples=500)
    second = paired_bootstrap_ci(deltas, seed=2, resamples=500)
    assert first.seed == 1
    assert second.seed == 2
    assert first.point_estimate == second.point_estimate


def test_receipt_block_carries_everything_needed_to_recompute_the_interval() -> None:
    deltas = _noisy_effect(0.2, 12, seed=31)
    block = paired_bootstrap_ci(deltas, seed=77, resamples=300).as_receipt_block()
    for key in ("seed", "resamples", "alpha", "method", "n", "ci_lower", "ci_upper"):
        assert key in block
    replayed = paired_bootstrap_ci(
        deltas, seed=block["seed"], resamples=block["resamples"], alpha=block["alpha"]
    )
    assert replayed.ci_lower == block["ci_lower"]
    assert replayed.ci_upper == block["ci_upper"]


# --------------------------------------------------------------------------
# Exact and sampled permutation paths agree
# --------------------------------------------------------------------------


def test_exact_path_is_taken_below_the_threshold_and_sampled_above_it() -> None:
    deltas = _noisy_effect(0.3, 10, seed=5)
    exact = sign_flip_permutation_p(deltas, seed=1, resamples=1000, exact_max_n=20)
    sampled = sign_flip_permutation_p(deltas, seed=1, resamples=1000, exact_max_n=1)
    assert exact.exact is True
    assert exact.method == "exact_sign_flip_enumeration"
    assert exact.seed is None
    assert exact.resamples == 2**10
    assert sampled.exact is False
    assert sampled.method == "sampled_sign_flip"
    assert sampled.seed == 1


def test_exact_and_sampled_permutation_agree_where_both_are_computable() -> None:
    rng = random.Random(808)
    deltas = [rng.gauss(0.15, 0.5) for _ in range(12)]
    exact = sign_flip_permutation_p(deltas, seed=1, resamples=1, exact_max_n=20)
    sampled = sign_flip_permutation_p(deltas, seed=1, resamples=20000, exact_max_n=1)
    assert exact.p_value == pytest.approx(sampled.p_value, abs=0.02)


def test_sampled_permutation_never_reports_exactly_zero() -> None:
    deltas = [5.0] * 30
    sampled = sign_flip_permutation_p(deltas, seed=1, resamples=200, exact_max_n=1)
    assert sampled.p_value > 0.0


# --------------------------------------------------------------------------
# Calibration: the false-positive rate of this rule must not exceed alpha
# --------------------------------------------------------------------------


def test_false_positive_rate_under_the_null_is_at_or_below_alpha() -> None:
    """Simulate many null worlds and measure how often the rule cries wolf.

    Trial count is fixed against binomial noise rather than chosen loosely:
    at 400 trials and alpha=0.05 the binomial SE is about 0.011, so a
    tolerance of 0.04 leaves roughly 3.7 SE of headroom and the test is not
    flaky by construction.  The assertion is one-sided (``<= alpha + tol``)
    because the rule requires *both* an interval excluding zero and a
    permutation p-value at or below alpha, which is deliberately conservative
    -- an observed rate well under alpha is the expected, correct behaviour,
    not a defect.
    """

    trials = 400
    alpha = 0.05
    tolerance = 0.04
    data_rng = random.Random(20260811)
    false_positives = 0
    for trial in range(trials):
        deltas = [data_rng.gauss(0.0, 1.0) for _ in range(10)]
        assessment = assess_paired_distinguishability(
            deltas,
            seed=trial,
            resamples=400,
            alpha=alpha,
            minimum_effect_of_interest=5.0,
        )
        if assessment.verdict is DistinguishabilityVerdict.DISTINGUISHABLE:
            false_positives += 1
    observed_rate = false_positives / trials
    assert observed_rate <= alpha + tolerance, (
        f"false-positive rate {observed_rate:.4f} exceeds alpha {alpha} + {tolerance}"
    )


def test_the_rule_still_detects_a_real_effect_at_the_same_settings() -> None:
    """Calibration without sensitivity would be satisfied by never firing."""

    trials = 60
    data_rng = random.Random(5150)
    detections = 0
    for trial in range(trials):
        deltas = [data_rng.gauss(1.2, 1.0) for _ in range(10)]
        assessment = assess_paired_distinguishability(
            deltas,
            seed=trial,
            resamples=400,
            alpha=0.05,
            minimum_effect_of_interest=0.5,
        )
        if assessment.verdict is DistinguishabilityVerdict.DISTINGUISHABLE:
            detections += 1
    assert detections / trials >= 0.6


# --------------------------------------------------------------------------
# Case-index resampling for set-level functionals
# --------------------------------------------------------------------------


def _mean_gap(values_a: list[float], values_b: list[float]):
    def difference(indices):
        if len(set(indices)) < 2:
            return None
        return sum(values_a[i] for i in indices) / len(indices) - sum(
            values_b[i] for i in indices
        ) / len(indices)

    return difference


def test_case_resampling_finds_a_real_set_level_difference() -> None:
    values_a = [0.9, 0.85, 0.95, 0.88, 0.92, 0.91, 0.87, 0.93]
    values_b = [0.30, 0.35, 0.28, 0.33, 0.31, 0.29, 0.34, 0.32]
    interval = case_resampled_difference_ci(
        len(values_a), _mean_gap(values_a, values_b), seed=3, resamples=800
    )
    assert interval.excludes_null
    assert interval.ci_lower > 0.0
    assert interval.n == 8


def test_case_resampling_counts_and_reports_degenerate_resamples() -> None:
    values_a = [0.5, 0.6]
    values_b = [0.4, 0.4]
    interval = case_resampled_difference_ci(
        2, _mean_gap(values_a, values_b), seed=3, resamples=500
    )
    # With two units, half of all resamples draw the same index twice and the
    # functional is undefined; those must be counted, not silently dropped.
    assert interval.skipped_resamples > 0
    assert interval.effective_resamples == 500 - interval.skipped_resamples
    assert interval.effective_resamples > 0


def test_case_resampling_fails_closed_when_the_functional_is_undefined() -> None:
    with pytest.raises(ValueError):
        case_resampled_difference_ci(4, lambda indices: None, seed=1, resamples=10)


def test_case_resampling_is_reproducible_from_its_seed() -> None:
    values_a = [0.9, 0.85, 0.95, 0.88, 0.92, 0.91]
    values_b = [0.30, 0.35, 0.28, 0.33, 0.31, 0.29]
    first = case_resampled_difference_ci(6, _mean_gap(values_a, values_b), seed=9, resamples=400)
    second = case_resampled_difference_ci(6, _mean_gap(values_a, values_b), seed=9, resamples=400)
    assert first == second


# --------------------------------------------------------------------------
# Multiplicity control
# --------------------------------------------------------------------------


def test_holm_bonferroni_rejects_only_what_survives_the_step_down() -> None:
    decisions = holm_bonferroni({"a": 0.001, "b": 0.04, "c": 0.5}, alpha=0.05)
    by_label = {decision.label: decision for decision in decisions}
    assert by_label["a"].rejected is True
    assert by_label["b"].rejected is False
    assert by_label["c"].rejected is False


def test_holm_bonferroni_is_never_more_permissive_than_an_uncorrected_or() -> None:
    """Two marginal p-values that an ``or`` would pass must not both pass here."""

    p_values = {"success": 0.03, "score": 0.04}
    decisions = holm_bonferroni(p_values, alpha=0.05)
    assert all(not decision.rejected for decision in decisions)
    assert any(p <= 0.05 for p in p_values.values())


def test_holm_bonferroni_adjusted_p_values_are_monotone() -> None:
    decisions = holm_bonferroni({"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.9}, alpha=0.05)
    adjusted = [decision.adjusted_p_value for decision in decisions]
    assert adjusted == sorted(adjusted)


def test_holm_bonferroni_ordering_is_deterministic_under_ties() -> None:
    first = holm_bonferroni({"z": 0.02, "a": 0.02}, alpha=0.05)
    second = holm_bonferroni({"a": 0.02, "z": 0.02}, alpha=0.05)
    assert [decision.label for decision in first] == [decision.label for decision in second]
