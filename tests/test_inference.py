"""Tests for stdlib-only statistical inference helpers."""

from __future__ import annotations

import pytest

from rakl.inference import (
    InferenceStatus,
    interval_excludes_zero,
    paired_bootstrap_ci,
    paired_lift_verdict,
    paired_permutation_p_value,
)


def test_paired_bootstrap_ci_returns_interval_containing_point_estimate() -> None:
    """Bootstrap CI should bracket the point estimate on known data."""
    # Fixed seed ensures reproducibility
    diffs = [0.05, -0.02, 0.08, 0.03, -0.01, 0.04]
    point, lo, hi = paired_bootstrap_ci(diffs, alpha=0.05, n_boot=5000, seed=42)

    # point estimate should be mean of diffs
    expected_point = sum(diffs) / len(diffs)
    assert abs(point - expected_point) < 1e-10

    # CI should contain the point estimate
    assert lo <= point <= hi

    # CI should be symmetric-ish around point
    assert (point - lo) > 0
    assert (hi - point) > 0


def test_paired_bootstrap_ci_strong_signal_excludes_zero() -> None:
    """A strong positive signal should produce a CI entirely above zero."""
    # All positive differences, decent n
    diffs = [0.15, 0.12, 0.18, 0.10, 0.14, 0.16, 0.13, 0.11]
    point, lo, hi = paired_bootstrap_ci(diffs, alpha=0.05, n_boot=5000, seed=42)

    assert point > 0
    assert lo > 0  # entire CI is positive
    assert hi > lo


def test_paired_bootstrap_ci_weak_signal_includes_zero() -> None:
    """A weak noisy signal should produce a CI that includes zero."""
    # Mixed small differences near zero
    diffs = [0.02, -0.01, 0.03, -0.02, 0.01, -0.03, 0.00, 0.02]
    point, lo, hi = paired_bootstrap_ci(diffs, alpha=0.05, n_boot=5000, seed=42)

    # CI should span zero
    assert lo < 0 < hi


def test_paired_bootstrap_ci_raises_on_empty_input() -> None:
    """Empty diffs should raise ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        paired_bootstrap_ci([])


def test_paired_bootstrap_ci_deterministic_with_seed() -> None:
    """Same seed must produce identical output."""
    diffs = [0.05, -0.02, 0.08, 0.03]
    result1 = paired_bootstrap_ci(diffs, alpha=0.05, n_boot=1000, seed=12345)
    result2 = paired_bootstrap_ci(diffs, alpha=0.05, n_boot=1000, seed=12345)

    assert result1 == result2


def test_paired_permutation_p_value_all_positive_gives_small_p() -> None:
    """All-positive diffs should yield a small two-sided p-value."""
    # Consistently positive signal
    diffs = [0.15, 0.12, 0.18, 0.10, 0.14, 0.16]
    p = paired_permutation_p_value(diffs, n_perm=5000, seed=42)

    # p-value should be very small (signal is strong)
    assert p < 0.05
    assert p > 0


def test_paired_permutation_p_value_all_negative_gives_small_p() -> None:
    """All-negative diffs should also yield a small p-value (symmetric)."""
    diffs = [-0.15, -0.12, -0.18, -0.10, -0.14, -0.16]
    p = paired_permutation_p_value(diffs, n_perm=5000, seed=42)

    assert p < 0.05
    assert p > 0


def test_paired_permutation_p_value_mixed_gives_large_p() -> None:
    """Mixed-sign diffs centered near zero should yield a large p-value."""
    # Roughly centered at zero
    diffs = [0.05, -0.05, 0.03, -0.03, 0.02, -0.02, 0.04, -0.04]
    p = paired_permutation_p_value(diffs, n_perm=5000, seed=42)

    # p-value should be large (null plausible)
    assert p > 0.3


def test_paired_permutation_p_value_raises_on_empty_input() -> None:
    """Empty diffs should raise ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        paired_permutation_p_value([])


def test_paired_permutation_p_value_deterministic_with_seed() -> None:
    """Same seed must produce identical p-value."""
    diffs = [0.05, -0.02, 0.08, 0.03]
    p1 = paired_permutation_p_value(diffs, n_perm=1000, seed=9876)
    p2 = paired_permutation_p_value(diffs, n_perm=1000, seed=9876)

    assert p1 == p2


def test_interval_excludes_zero_positive_interval() -> None:
    """A CI entirely above zero excludes the null."""
    assert interval_excludes_zero(0.02, 0.08, alpha=0.05)


def test_interval_excludes_zero_negative_interval() -> None:
    """A CI entirely below zero excludes the null."""
    assert interval_excludes_zero(-0.08, -0.02, alpha=0.05)


def test_interval_excludes_zero_interval_spanning_zero() -> None:
    """A CI that spans zero does NOT exclude the null."""
    assert not interval_excludes_zero(-0.03, 0.02, alpha=0.05)


def test_interval_excludes_zero_edge_cases() -> None:
    """Edge cases: zero bounds."""
    assert not interval_excludes_zero(0.0, 0.05, alpha=0.05)
    assert not interval_excludes_zero(-0.05, 0.0, alpha=0.05)


def test_paired_lift_verdict_strong_positive_signal() -> None:
    """Strong positive signal should yield MEASURED_AND_DISTINGUISHABLE."""
    diffs = [0.15, 0.12, 0.18, 0.10, 0.14, 0.16, 0.13, 0.11]
    verdict = paired_lift_verdict(diffs, alpha=0.05, n_boot=5000, n_perm=5000, seed=42)

    assert verdict.point_estimate > 0
    assert verdict.excludes_null
    assert verdict.status == InferenceStatus.MEASURED_AND_DISTINGUISHABLE
    assert verdict.p_value < 0.05
    assert verdict.ci_lo > 0
    assert verdict.n == len(diffs)
    assert verdict.alpha == 0.05


def test_paired_lift_verdict_weak_signal_indistinguishable() -> None:
    """Weak noisy signal should yield MEASURED_BUT_INDISTINGUISHABLE."""
    diffs = [0.02, -0.01, 0.03, -0.02, 0.01, -0.03, 0.00, 0.02]
    verdict = paired_lift_verdict(diffs, alpha=0.05, n_boot=5000, n_perm=5000, seed=42)

    assert not verdict.excludes_null
    assert verdict.status == InferenceStatus.MEASURED_BUT_INDISTINGUISHABLE
    assert verdict.p_value > 0.3  # null is plausible


def test_paired_lift_verdict_empty_returns_cannot_check() -> None:
    """Empty diffs should yield EMPTY status."""
    verdict = paired_lift_verdict([], alpha=0.05)

    assert verdict.status == InferenceStatus.EMPTY
    assert not verdict.excludes_null
    assert verdict.n == 0
    assert verdict.point_estimate == 0.0


def test_paired_lift_verdict_all_zero_returns_all_zero_status() -> None:
    """All-zero diffs should yield ALL_ZERO status."""
    diffs = [0.0, 0.0, 0.0, 0.0, 0.0]
    verdict = paired_lift_verdict(diffs, alpha=0.05)

    assert verdict.status == InferenceStatus.ALL_ZERO
    assert not verdict.excludes_null
    assert verdict.point_estimate == 0.0


def test_paired_lift_verdict_tiny_n_returns_insufficient_n() -> None:
    """n < 3 should yield INSUFFICIENT_N (bootstrap unstable)."""
    diffs = [0.05, 0.03]
    verdict = paired_lift_verdict(diffs, alpha=0.05)

    assert verdict.status == InferenceStatus.INSUFFICIENT_N
    assert not verdict.excludes_null
    assert verdict.n == 2
    # Should still compute point estimate
    assert verdict.point_estimate == sum(diffs) / 2


def test_paired_lift_verdict_single_item_insufficient_n() -> None:
    """Single-item diffs should yield INSUFFICIENT_N."""
    diffs = [0.05]
    verdict = paired_lift_verdict(diffs, alpha=0.05)

    assert verdict.status == InferenceStatus.INSUFFICIENT_N
    assert verdict.n == 1
    assert not verdict.excludes_null


def test_paired_lift_verdict_deterministic_with_seed() -> None:
    """Same seed must produce identical verdict."""
    diffs = [0.05, -0.02, 0.08, 0.03, 0.01]
    v1 = paired_lift_verdict(diffs, alpha=0.05, n_boot=1000, n_perm=1000, seed=555)
    v2 = paired_lift_verdict(diffs, alpha=0.05, n_boot=1000, n_perm=1000, seed=555)

    assert v1 == v2
