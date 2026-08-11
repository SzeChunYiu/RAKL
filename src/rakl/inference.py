"""Stdlib-only statistical inference helpers for RAKL empirical gates.

This module provides paired bootstrap confidence intervals and sign-flip
permutation tests using only the Python standard library (no numpy/scipy).
All resampling methods are deterministic given a seed.

Entry points:
    - paired_bootstrap_ci: confidence interval for paired differences
    - paired_permutation_p_value: two-sided p-value via sign-flip
    - paired_lift_verdict: combined verdict with interval and p-value
    - interval_excludes_zero: check if CI excludes the null

Example:
    >>> from rakl.inference import paired_lift_verdict
    >>> diffs = [0.05, -0.02, 0.08, 0.03, -0.01]
    >>> result = paired_lift_verdict(diffs, alpha=0.05, n_boot=10000, seed=42)
    >>> assert result["point_estimate"] > 0
    >>> assert result["excludes_null"] == result["ci_lo"] > 0
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class InferenceStatus(str, Enum):
    """Outcome of an inference computation.

    distinct from gate verdicts — this is about whether the computation
    itself could complete, not whether a gate passes.
    """

    MEASURED_AND_DISTINGUISHABLE = "MEASURED_AND_DISTINGUISHABLE"
    MEASURED_BUT_INDISTINGUISHABLE = "MEASURED_BUT_INDISTINGUISHABLE"
    INSUFFICIENT_N = "INSUFFICIENT_N"
    ALL_ZERO = "ALL_ZERO"
    EMPTY = "EMPTY"


@dataclass(frozen=True)
class PairedLiftVerdict:
    """Result of a paired-difference inference test.

    Attributes:
        point_estimate: mean of the paired differences
        ci_lo: lower bound of the bootstrap confidence interval
        ci_hi: upper bound of the bootstrap confidence interval
        p_value: two-sided p-value from sign-flip permutation
        excludes_null: whether the confidence interval excludes zero
        status: enum describing the inference outcome
        n: number of paired differences
        alpha: nominal Type I error rate used
    """

    point_estimate: float
    ci_lo: float
    ci_hi: float
    p_value: float
    excludes_null: bool
    status: InferenceStatus
    n: int
    alpha: float


def _require_non_empty(iterable: Iterable, label: str) -> list:
    """Validate and convert an iterable to a list."""
    items = list(iterable)
    if not items:
        raise ValueError(f"{label} cannot be empty")
    return items


def paired_bootstrap_ci(
    diffs: Iterable[float],
    *,
    alpha: float = 0.05,
    n_boot: int = 10000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Percentile confidence interval via paired bootstrap.

    Args:
        diffs: paired differences (treatment - control) for each item/task
        alpha: Type I error rate (default 0.05 for 95% CI)
        n_boot: number of bootstrap iterations
        seed: random seed for reproducibility

    Returns:
        (point_estimate, ci_lo, ci_hi) where ci_lo/ci_hi are the alpha/2
        and 1-alpha/2 percentiles of the bootstrap distribution.

    Raises:
        ValueError: if diffs is empty
    """
    diffs = _require_non_empty(diffs, "diffs")
    rng = random.Random(seed)

    point_estimate = sum(diffs) / len(diffs)
    n = len(diffs)

    # bootstrap resample with replacement
    boot_means: list[float] = []
    for _ in range(n_boot):
        sample = [rng.choice(diffs) for _ in range(n)]
        boot_means.append(sum(sample) / n)

    boot_means.sort()
    k_lo = int(alpha / 2 * n_boot)
    k_hi = int((1 - alpha / 2) * n_boot)

    ci_lo = boot_means[max(0, k_lo)]
    ci_hi = boot_means[min(n_boot - 1, k_hi)]

    return point_estimate, ci_lo, ci_hi


def paired_permutation_p_value(
    diffs: Iterable[float],
    *,
    n_perm: int = 10000,
    seed: int = 0,
) -> float:
    """Two-sided p-value via paired sign-flip permutation test.

    Under the null hypothesis (no systematic difference), each difference
    is equally likely to be positive or negative. We randomly flip signs
    to build the null distribution of the mean.

    Args:
        diffs: paired differences (treatment - control)
        n_perm: number of permutation iterations
        seed: random seed for reproducibility

    Returns:
        Two-sided p-value: proportion of null means with absolute value
        >= the absolute observed mean.

    Raises:
        ValueError: if diffs is empty
    """
    diffs = _require_non_empty(diffs, "diffs")
    rng = random.Random(seed)

    observed_mean = sum(diffs) / len(diffs)
    abs_observed = abs(observed_mean)
    n = len(diffs)

    extreme_count = 0
    for _ in range(n_perm):
        # flip each sign independently with probability 0.5
        flipped = [d if rng.random() < 0.5 else -d for d in diffs]
        perm_mean = sum(flipped) / n
        if abs(perm_mean) >= abs_observed:
            extreme_count += 1

    return extreme_count / n_perm


def interval_excludes_zero(ci_lo: float, ci_hi: float, alpha: float) -> bool:
    """Check whether a confidence interval excludes the null value (zero).

    This is the key decision rule for interval-based gate verdicts:
    a gate passes only when the entire CI lies on one side of zero.

    Args:
        ci_lo: lower bound of the confidence interval
        ci_hi: upper bound of the confidence interval
        alpha: nominal Type I error rate (for documentation)

    Returns:
        True if the interval excludes zero (both bounds have same sign),
        False otherwise.
    """
    return ci_lo > 0 or ci_hi < 0


def paired_lift_verdict(
    diffs: Iterable[float],
    *,
    alpha: float = 0.05,
    n_boot: int = 10000,
    n_perm: int = 10000,
    seed: int = 0,
) -> PairedLiftVerdict:
    """Combined inference verdict for a paired-difference lift test.

    This is the primary entry point for gates that need to distinguish
    signal from noise. It returns a structured verdict containing both
    frequentist inference artifacts (CI, p-value) and a decision helper
    (excludes_null, status).

    Edge cases:
        - Empty diffs: status=EMPTY, excludes_null=False
        - All diffs zero: status=ALL_ZERO, excludes_null=False
        - n < 3: status=INSUFFICIENT_N, excludes_null=False
          (bootstrap is unstable with tiny samples)

    Args:
        diffs: paired differences (treatment - control)
        alpha: Type I error rate for CI and p-value threshold
        n_boot: bootstrap iterations for CI
        n_perm: permutation iterations for p-value
        seed: random seed for reproducibility

    Returns:
        PairedLiftVerdict with all inference outputs.

    Example:
        >>> diffs = [0.05, -0.02, 0.08, 0.03]
        >>> verdict = paired_lift_verdict(diffs, alpha=0.05, seed=42)
        >>> if verdict.excludes_null:
        ...     print(f"lift is distinguishable: {verdict.point_estimate:.3f}")
    """
    diffs_list = list(diffs)

    # edge cases
    if not diffs_list:
        return PairedLiftVerdict(
            point_estimate=0.0,
            ci_lo=0.0,
            ci_hi=0.0,
            p_value=1.0,
            excludes_null=False,
            status=InferenceStatus.EMPTY,
            n=0,
            alpha=alpha,
        )

    n = len(diffs_list)
    if n < 3:
        point_estimate = sum(diffs_list) / n
        return PairedLiftVerdict(
            point_estimate=point_estimate,
            ci_lo=point_estimate,
            ci_hi=point_estimate,
            p_value=1.0,
            excludes_null=False,
            status=InferenceStatus.INSUFFICIENT_N,
            n=n,
            alpha=alpha,
        )

    if all(d == 0 for d in diffs_list):
        return PairedLiftVerdict(
            point_estimate=0.0,
            ci_lo=0.0,
            ci_hi=0.0,
            p_value=1.0,
            excludes_null=False,
            status=InferenceStatus.ALL_ZERO,
            n=n,
            alpha=alpha,
        )

    # full inference
    point_estimate, ci_lo, ci_hi = paired_bootstrap_ci(
        diffs_list, alpha=alpha, n_boot=n_boot, seed=seed
    )
    p_value = paired_permutation_p_value(diffs_list, n_perm=n_perm, seed=seed)

    excludes_null = interval_excludes_zero(ci_lo, ci_hi, alpha)

    status = (
        InferenceStatus.MEASURED_AND_DISTINGUISHABLE
        if excludes_null
        else InferenceStatus.MEASURED_BUT_INDISTINGUISHABLE
    )

    return PairedLiftVerdict(
        point_estimate=point_estimate,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        p_value=p_value,
        excludes_null=excludes_null,
        status=status,
        n=n,
        alpha=alpha,
    )
