"""Dependency-free statistical inference for RAKL empirical gates.

RAKL is rigorous about chronology, provenance and authority and has, until now,
been silent about inference: every empirical verdict the runtime could emit was
a comparison of point estimates.  This module supplies the missing instrument.

Design constraints
------------------

* **Stdlib only.**  The runtime dependency set is ``["jsonschema"]``.  Paired
  bootstrap and sign-flip permutation need nothing else, so keeping the
  dependency set minimal is not an obstacle to doing inference properly.
* **Exactly reproducible.**  Every resampling entry point takes an explicit
  ``seed`` and records it, the resample count and the method label on the
  result, so any interval in a receipt can be recomputed byte-identically.
  A local :class:`random.Random` is always used; the global RNG is never
  touched and never read.
* **Fails closed.**  Too little data yields
  :attr:`DistinguishabilityVerdict.INSUFFICIENT_DATA`, never a default pass.
  A design that cannot see the effect it was built to look for yields
  :attr:`DistinguishabilityVerdict.UNDERPOWERED`, not a refutation.

Two resampling entry points, and why both are needed
----------------------------------------------------

The distinction is load-bearing and is the most common way to compute a number
that looks like an interval but is not one:

* :func:`paired_bootstrap_ci` applies to statistics that are a **mean of
  per-unit differences** -- Paper II per-task success/score deltas, or a Brier
  reduction (whose per-item contribution ``(p - y)**2`` makes the per-item
  delta average exactly to the set-level reduction).
* :func:`case_resampled_difference_ci` applies to statistics that are
  **set-level functionals** and have no per-unit decomposition -- ROC AUC and
  average precision.  There is no such thing as "the AUC delta for item i", so
  these must be obtained by resampling case indices and recomputing the whole
  functional on each resample.

``INDISTINGUISHABLE`` is a first-class scientific outcome.  It reports that a
measurement was made and could not be separated from chance.  It is never
collapsed into failure, and it is not the same as ``UNDERPOWERED``, which
reports that the design could not have seen the effect either way.

Measured calibration
--------------------

The decision rule requires **both** an interval excluding zero and a
permutation p-value at or below ``alpha``.  That conjunction is not belt-and-
braces caution; it is what makes the rule calibrated.  Measured over 2000
simulated null worlds per cell (``tests/test_inference.py`` asserts the
bound, these are the point estimates):

===========================================  ==============
rule at ``alpha = 0.05``, ``n = 16``          false-positive
===========================================  ==============
bias-corrected bootstrap interval alone       0.072
sign-flip permutation alone                   0.0385
both, i.e. the rule shipped here              0.0385
===========================================  ==============

The bootstrap interval **alone is anti-conservative at these sample sizes**,
rejecting at 7.2% against a nominal 5%: a small-sample property of the
percentile family, and precisely the sort of thing that would have gone
unnoticed had the helper only ever been tested on an obvious effect.  The
exact permutation is the binding constraint and pulls the combined rate back
under ``alpha``.  Across ``n`` in 6, 10, 16, 24 the combined rate measured
0.032, 0.046, 0.041 and 0.040 respectively.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from statistics import NormalDist, fmean, stdev
from typing import Any, Callable, Mapping, Sequence

__all__ = [
    "DistinguishabilityVerdict",
    "IntervalEstimate",
    "PermutationResult",
    "DistinguishabilityAssessment",
    "HolmDecision",
    "paired_bootstrap_ci",
    "case_resampled_difference_ci",
    "sign_flip_permutation_p",
    "minimum_detectable_effect",
    "assess_paired_distinguishability",
    "holm_bonferroni",
    "DEFAULT_ALPHA",
    "DEFAULT_RESAMPLES",
    "DEFAULT_POWER",
    "EXACT_PERMUTATION_MAX_N",
]


DEFAULT_ALPHA = 0.05
DEFAULT_RESAMPLES = 10_000
DEFAULT_POWER = 0.8

#: Above this many paired units, exhaustive sign-flip enumeration (``2**n``
#: assignments) stops being affordable and the sampled path is used instead.
EXACT_PERMUTATION_MAX_N = 20

#: Absolute tolerance used when comparing a permuted statistic against the
#: observed one.  Without it, floating-point noise on values that are
#: mathematically equal would silently drop legitimate ties out of the tail and
#: understate the p-value.
_TIE_TOLERANCE = 1e-12


class DistinguishabilityVerdict(str, Enum):
    """Outcome of asking whether an observed effect is separable from chance.

    ``INDISTINGUISHABLE`` and ``UNDERPOWERED`` are both legitimate scientific
    results and neither is a failure.  They differ in what they license:
    ``INDISTINGUISHABLE`` means the design could have seen the registered
    effect of interest and did not; ``UNDERPOWERED`` means it could not have
    seen it either way, so no conclusion about the effect is available.
    """

    DISTINGUISHABLE = "DISTINGUISHABLE"
    INDISTINGUISHABLE = "INDISTINGUISHABLE"
    UNDERPOWERED = "UNDERPOWERED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class IntervalEstimate:
    """A resampled interval, carrying everything needed to reproduce it."""

    point_estimate: float
    ci_lower: float
    ci_upper: float
    alpha: float
    method: str
    seed: int
    resamples: int
    effective_resamples: int
    skipped_resamples: int
    n: int

    @property
    def excludes_null(self) -> bool:
        """True when the whole interval lies strictly on one side of zero."""

        return self.ci_lower > 0.0 or self.ci_upper < 0.0

    def as_receipt_block(self) -> dict[str, Any]:
        return {
            "point_estimate": self.point_estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "alpha": self.alpha,
            "method": self.method,
            "seed": self.seed,
            "resamples": self.resamples,
            "effective_resamples": self.effective_resamples,
            "skipped_resamples": self.skipped_resamples,
            "n": self.n,
            "excludes_null": self.excludes_null,
        }


@dataclass(frozen=True)
class PermutationResult:
    """A sign-flip permutation p-value and the path used to obtain it."""

    p_value: float
    method: str
    resamples: int
    seed: int | None
    n: int
    observed_statistic: float
    exact: bool

    def as_receipt_block(self) -> dict[str, Any]:
        return {
            "p_value": self.p_value,
            "method": self.method,
            "resamples": self.resamples,
            "seed": self.seed,
            "n": self.n,
            "observed_statistic": self.observed_statistic,
            "exact": self.exact,
        }


@dataclass(frozen=True)
class DistinguishabilityAssessment:
    """Verdict plus the full evidence that produced it."""

    verdict: DistinguishabilityVerdict
    interval: IntervalEstimate | None
    permutation: PermutationResult | None
    minimum_detectable_effect: float | None
    minimum_effect_of_interest: float | None
    power: float
    n: int
    reasons: tuple[str, ...]

    @property
    def distinguishable(self) -> bool:
        return self.verdict is DistinguishabilityVerdict.DISTINGUISHABLE

    def as_receipt_block(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "interval": self.interval.as_receipt_block() if self.interval else None,
            "permutation": self.permutation.as_receipt_block() if self.permutation else None,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "minimum_effect_of_interest": self.minimum_effect_of_interest,
            "power": self.power,
            "n": self.n,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class HolmDecision:
    """One family member's Holm-Bonferroni outcome."""

    label: str
    p_value: float
    adjusted_p_value: float
    rejected: bool

    def as_receipt_block(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "p_value": self.p_value,
            "adjusted_p_value": self.adjusted_p_value,
            "rejected": self.rejected,
        }


def _empirical_quantile(sorted_values: Sequence[float], probability: float) -> float:
    """Linearly interpolated empirical quantile of an already-sorted sample."""

    if not sorted_values:
        raise ValueError("cannot take a quantile of an empty sample")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    probability = min(max(probability, 0.0), 1.0)
    position = probability * (len(sorted_values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return float(sorted_values[lower_index])
    weight = position - lower_index
    return float(
        sorted_values[lower_index] * (1.0 - weight) + sorted_values[upper_index] * weight
    )


def _bias_corrected_bounds(
    replicates: Sequence[float], observed: float, alpha: float
) -> tuple[float, float, str]:
    """Bias-corrected percentile bounds, falling back to plain percentile.

    The bias correction (Efron's BC) shifts the percentile levels by the
    median bias of the bootstrap distribution, ``z0``, estimated from the
    fraction of replicates below the observed statistic.  It costs one
    ``NormalDist`` inverse CDF, needs no derivative or jackknife, and removes
    the percentile interval's systematic miscoverage when the resampling
    distribution is skewed -- which is the normal case for a bounded
    statistic such as a success-rate delta or an AUC gain near the edge of
    its range.

    When every replicate falls on one side of the observed value ``z0`` is
    infinite and the correction is undefined; in that case the plain
    percentile interval is returned and the degenerate path is recorded in
    the method label rather than being silently applied.
    """

    ordered = sorted(replicates)
    below = sum(1 for value in ordered if value < observed)
    proportion_below = below / len(ordered)
    if proportion_below <= 0.0 or proportion_below >= 1.0:
        return (
            _empirical_quantile(ordered, alpha / 2.0),
            _empirical_quantile(ordered, 1.0 - alpha / 2.0),
            "percentile_bias_correction_degenerate",
        )
    normal = NormalDist()
    z0 = normal.inv_cdf(proportion_below)
    z_low = normal.inv_cdf(alpha / 2.0)
    z_high = normal.inv_cdf(1.0 - alpha / 2.0)
    lower_level = normal.cdf(2.0 * z0 + z_low)
    upper_level = normal.cdf(2.0 * z0 + z_high)
    return (
        _empirical_quantile(ordered, lower_level),
        _empirical_quantile(ordered, upper_level),
        "bias_corrected_percentile",
    )


def _validate_resampling_arguments(alpha: float, resamples: int) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between 0 and 1")
    if resamples < 1:
        raise ValueError("resamples must be a positive integer")


def paired_bootstrap_ci(
    paired_deltas: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
) -> IntervalEstimate:
    """Bias-corrected percentile bootstrap CI for the mean paired difference.

    ``paired_deltas`` must be one difference per independent unit -- per task,
    per item -- already paired, so that resampling the vector resamples whole
    units.  This is the correct entry point only for statistics that *are* a
    mean of per-unit differences.  For set-level functionals such as ROC AUC
    or average precision use :func:`case_resampled_difference_ci`.

    Raises ``ValueError`` on an empty vector: an interval over no data is not
    a wide interval, it is not an interval, and returning one would let a
    caller treat absent evidence as weak evidence.
    """

    _validate_resampling_arguments(alpha, resamples)
    deltas = [float(value) for value in paired_deltas]
    if not deltas:
        raise ValueError("paired_bootstrap_ci requires at least one paired delta")
    observed = fmean(deltas)
    rng = random.Random(seed)
    count = len(deltas)
    replicates: list[float] = []
    for _ in range(resamples):
        total = 0.0
        for _ in range(count):
            total += deltas[rng.randrange(count)]
        replicates.append(total / count)
    lower, upper, method = _bias_corrected_bounds(replicates, observed, alpha)
    return IntervalEstimate(
        point_estimate=observed,
        ci_lower=lower,
        ci_upper=upper,
        alpha=alpha,
        method=method,
        seed=seed,
        resamples=resamples,
        effective_resamples=len(replicates),
        skipped_resamples=0,
        n=count,
    )


def case_resampled_difference_ci(
    unit_count: int,
    difference: Callable[[Sequence[int]], float | None],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
) -> IntervalEstimate:
    """Bootstrap CI for a set-level functional difference, by case resampling.

    ``difference`` receives a sequence of case indices drawn with replacement
    and returns the arm-to-arm difference of the functional recomputed on
    exactly those cases, or ``None`` when the resample makes the functional
    undefined.  A resample containing a single outcome class leaves ROC AUC
    and average precision undefined, so this is a real and frequent case at
    small ``n``.

    Skipped resamples are counted and reported rather than silently dropped:
    they change the effective resample count and therefore the interval, and
    a receipt that hid them would not be reproducible from its own numbers.

    Raises ``ValueError`` if the functional is undefined on the observed data,
    or if every resample was degenerate -- both fail closed rather than
    returning an interval with no support.
    """

    _validate_resampling_arguments(alpha, resamples)
    if unit_count < 1:
        raise ValueError("case_resampled_difference_ci requires at least one unit")
    observed = difference(tuple(range(unit_count)))
    if observed is None:
        raise ValueError("difference functional is undefined on the observed cases")
    observed = float(observed)
    rng = random.Random(seed)
    replicates: list[float] = []
    skipped = 0
    for _ in range(resamples):
        indices = tuple(rng.randrange(unit_count) for _ in range(unit_count))
        value = difference(indices)
        if value is None:
            skipped += 1
            continue
        replicates.append(float(value))
    if not replicates:
        raise ValueError("every bootstrap resample left the functional undefined")
    lower, upper, method = _bias_corrected_bounds(replicates, observed, alpha)
    return IntervalEstimate(
        point_estimate=observed,
        ci_lower=lower,
        ci_upper=upper,
        alpha=alpha,
        method=f"case_resampled_{method}",
        seed=seed,
        resamples=resamples,
        effective_resamples=len(replicates),
        skipped_resamples=skipped,
        n=unit_count,
    )


def _exact_sign_flip_tail(deltas: Sequence[float], observed_sum: float) -> tuple[int, int]:
    """Count sign-flip assignments at least as extreme as the observed sum.

    Flipping a subset ``S`` to negative gives ``total - 2 * sum(S)``, so the
    whole ``2**n`` enumeration is obtained by building the subset-sum multiset
    by repeated doubling: ``O(2**n)`` total work rather than ``O(n * 2**n)``.
    """

    total = math.fsum(deltas)
    subset_sums = [0.0]
    for delta in deltas:
        subset_sums.extend([value + delta for value in subset_sums])
    threshold = abs(observed_sum) - _TIE_TOLERANCE
    extreme = sum(1 for value in subset_sums if abs(total - 2.0 * value) >= threshold)
    return extreme, len(subset_sums)


def sign_flip_permutation_p(
    paired_deltas: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    exact_max_n: int = EXACT_PERMUTATION_MAX_N,
) -> PermutationResult:
    """Two-sided sign-flip permutation p-value for the mean paired difference.

    Under the null the deltas are symmetric about zero, so every assignment of
    signs is equally likely.  All ``2**n`` assignments are enumerated exactly
    when ``n <= exact_max_n``; above that a seeded sample is drawn and the path
    taken is recorded on the result.

    The exact path needs no seed and none is recorded, because its answer is
    a deterministic property of the data.  The sampled path uses the
    ``(count + 1) / (resamples + 1)`` estimator so that a p-value is never
    reported as exactly zero -- a sampled tail of zero means "smaller than the
    resolution of this many resamples", not "impossible".

    An all-zero delta vector yields ``p = 1.0``: every permutation reproduces
    the observed statistic, which is the correct answer and not a crash.
    """

    if resamples < 1:
        raise ValueError("resamples must be a positive integer")
    deltas = [float(value) for value in paired_deltas]
    count = len(deltas)
    if count < 1:
        raise ValueError("sign_flip_permutation_p requires at least one paired delta")
    observed_mean = fmean(deltas)
    observed_sum = math.fsum(deltas)
    if count <= exact_max_n:
        extreme, total = _exact_sign_flip_tail(deltas, observed_sum)
        return PermutationResult(
            p_value=extreme / total,
            method="exact_sign_flip_enumeration",
            resamples=total,
            seed=None,
            n=count,
            observed_statistic=observed_mean,
            exact=True,
        )
    rng = random.Random(seed)
    threshold = abs(observed_sum) - _TIE_TOLERANCE
    extreme = 0
    for _ in range(resamples):
        total_sum = 0.0
        for delta in deltas:
            total_sum += delta if rng.getrandbits(1) else -delta
        if abs(total_sum) >= threshold:
            extreme += 1
    return PermutationResult(
        p_value=(extreme + 1) / (resamples + 1),
        method="sampled_sign_flip",
        resamples=resamples,
        seed=seed,
        n=count,
        observed_statistic=observed_mean,
        exact=False,
    )


def _student_t_quantile(probability: float, degrees_of_freedom: int) -> float:
    """Cornish-Fisher approximation to a Student-t quantile.

    Used so that :func:`minimum_detectable_effect` does not understate what a
    small design can detect.  A plain normal quantile would make a 16-item
    design look more powerful than it is; the ``t`` correction moves the
    estimate in the conservative direction, which is the direction that fails
    closed.
    """

    z = NormalDist().inv_cdf(probability)
    if degrees_of_freedom <= 0:
        return math.inf
    nu = float(degrees_of_freedom)
    return (
        z
        + (z**3 + z) / (4.0 * nu)
        + (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * nu**2)
        + (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z) / (384.0 * nu**3)
    )


def minimum_detectable_effect(
    n: int,
    per_unit_standard_deviation: float,
    *,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
) -> float:
    """Smallest true mean difference detectable at ``n`` with the given power.

    ``MDE = (t_{1-alpha/2, n-1} + z_power) * sd / sqrt(n)``.

    Registering this alongside a protocol is what makes a null interpretable:
    it converts "we saw no effect" into "we saw no effect, and an effect below
    this size would have been invisible to us anyway".  Returns ``math.inf``
    for ``n < 2``, where no effect is detectable at any size.
    """

    if n < 2:
        return math.inf
    if per_unit_standard_deviation < 0.0:
        raise ValueError("standard deviation cannot be negative")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between 0 and 1")
    if not 0.0 < power < 1.0:
        raise ValueError("power must lie strictly between 0 and 1")
    t_alpha = _student_t_quantile(1.0 - alpha / 2.0, n - 1)
    z_power = NormalDist().inv_cdf(power)
    return (t_alpha + z_power) * per_unit_standard_deviation / math.sqrt(n)


def assess_paired_distinguishability(
    paired_deltas: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    minimum_effect_of_interest: float | None = None,
) -> DistinguishabilityAssessment:
    """Full paired assessment: interval, permutation p-value and verdict.

    An effect is reported ``DISTINGUISHABLE`` only when **both** the interval
    excludes zero **and** the permutation p-value clears ``alpha``.  Requiring
    both is strictly more conservative than requiring either, so this rule can
    only ever be harder to satisfy than a bare sign or threshold check.

    Without a registered ``minimum_effect_of_interest`` a non-significant
    result is reported ``UNDERPOWERED`` rather than ``INDISTINGUISHABLE``:
    with no registered effect there is no basis for the claim "we would have
    seen it", and asserting absence of evidence as evidence of absence is
    exactly the error this module exists to prevent.  Registering the effect
    is what unlocks the stronger, and more useful, ``INDISTINGUISHABLE``.
    """

    deltas = [float(value) for value in paired_deltas]
    count = len(deltas)
    if count < 2:
        return DistinguishabilityAssessment(
            verdict=DistinguishabilityVerdict.INSUFFICIENT_DATA,
            interval=None,
            permutation=None,
            minimum_detectable_effect=math.inf,
            minimum_effect_of_interest=minimum_effect_of_interest,
            power=power,
            n=count,
            reasons=(f"paired_unit_count_below_two:{count}",),
        )

    interval = paired_bootstrap_ci(deltas, seed=seed, resamples=resamples, alpha=alpha)
    permutation = sign_flip_permutation_p(deltas, seed=seed, resamples=resamples)
    spread = stdev(deltas) if count > 1 else 0.0
    mde = minimum_detectable_effect(count, spread, alpha=alpha, power=power)

    reasons: list[str] = []
    if interval.excludes_null and permutation.p_value <= alpha:
        reasons.append("interval_excludes_null_and_permutation_p_at_or_below_alpha")
        return DistinguishabilityAssessment(
            verdict=DistinguishabilityVerdict.DISTINGUISHABLE,
            interval=interval,
            permutation=permutation,
            minimum_detectable_effect=mde,
            minimum_effect_of_interest=minimum_effect_of_interest,
            power=power,
            n=count,
            reasons=tuple(reasons),
        )

    if not interval.excludes_null:
        reasons.append("interval_contains_null")
    if permutation.p_value > alpha:
        reasons.append(f"permutation_p_above_alpha:{permutation.p_value:.6f}")

    if minimum_effect_of_interest is None:
        reasons.append("no_registered_minimum_effect_of_interest")
        verdict = DistinguishabilityVerdict.UNDERPOWERED
    elif mde >= abs(minimum_effect_of_interest):
        reasons.append("minimum_detectable_effect_exceeds_registered_effect_of_interest")
        verdict = DistinguishabilityVerdict.UNDERPOWERED
    else:
        reasons.append("design_powered_for_registered_effect_and_null_not_excluded")
        verdict = DistinguishabilityVerdict.INDISTINGUISHABLE

    return DistinguishabilityAssessment(
        verdict=verdict,
        interval=interval,
        permutation=permutation,
        minimum_detectable_effect=mde,
        minimum_effect_of_interest=minimum_effect_of_interest,
        power=power,
        n=count,
        reasons=tuple(reasons),
    )


def holm_bonferroni(
    p_values: Mapping[str, float], *, alpha: float = DEFAULT_ALPHA
) -> tuple[HolmDecision, ...]:
    """Holm-Bonferroni step-down correction over a family of tests.

    Controls the family-wise error rate at ``alpha`` while being uniformly
    more powerful than plain Bonferroni.  This is the correction #138 section
    C4 already specifies for Paper V, applied here so that combining several
    metrics cannot inflate the false-positive rate above ``alpha`` -- which is
    precisely what an ``or`` across two correlated metrics does.

    Returned in ascending p-value order with monotone adjusted p-values; ties
    are broken by label so the ordering is deterministic.
    """

    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between 0 and 1")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    total = len(ordered)
    decisions: list[HolmDecision] = []
    running_max = 0.0
    still_rejecting = True
    for index, (label, p_value) in enumerate(ordered):
        adjusted = min(1.0, (total - index) * p_value)
        running_max = max(running_max, adjusted)
        if still_rejecting and running_max > alpha:
            still_rejecting = False
        decisions.append(
            HolmDecision(
                label=label,
                p_value=p_value,
                adjusted_p_value=running_max,
                rejected=still_rejecting,
            )
        )
    return tuple(decisions)
