from __future__ import annotations

from dataclasses import dataclass
from math import inf, log
from statistics import mean
from typing import Iterable, Sequence

from .evolution_trace import MetricDefinition, MetricDirection


@dataclass(frozen=True)
class PairedEffect:
    n: int
    mean_delta: float
    win_rate: float
    losses: int
    ties: int


def paired_effect(parent: Sequence[float], child: Sequence[float]) -> PairedEffect:
    if len(parent) != len(child) or not parent:
        raise ValueError("paired samples must be non-empty and equal length")
    deltas = [c - p for p, c in zip(parent, child)]
    wins = sum(d > 0 for d in deltas)
    losses = sum(d < 0 for d in deltas)
    ties = len(deltas) - wins - losses
    return PairedEffect(len(deltas), mean(deltas), wins / len(deltas), losses, ties)


def normalize_for_control(value: float, definition: MetricDefinition) -> float:
    """Map a raw metric to frozen [0,1] desirability using predeclared bounds.

    Bounds belong to the versioned MetricDefinition; they are not inferred from
    the candidate set, which would leak post-hoc information into the controller.
    """
    if definition.control_min is None or definition.control_max is None:
        raise ValueError("metric has no frozen control normalization")
    lo, hi = definition.control_min, definition.control_max
    clipped = min(max(value, lo), hi)
    z = (clipped - lo) / (hi - lo)
    if definition.direction is MetricDirection.MAXIMIZE:
        return z
    if definition.direction is MetricDirection.MINIMIZE:
        return 1.0 - z
    raise ValueError("constraint metrics are hard gates, not scalar utility inputs")


def brier_score(probabilities: Sequence[float], outcomes: Sequence[int]) -> float:
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("probabilities/outcomes must be non-empty and equal length")
    if any(p < 0 or p > 1 for p in probabilities) or any(o not in (0, 1) for o in outcomes):
        raise ValueError("probabilities must be [0,1] and outcomes binary")
    return mean((p - o) ** 2 for p, o in zip(probabilities, outcomes))


def expected_calibration_error(probabilities: Sequence[float], outcomes: Sequence[int], bins: int = 10) -> float:
    if bins < 1:
        raise ValueError("bins must be positive")
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("probabilities/outcomes must be non-empty and equal length")
    total = len(probabilities)
    error = 0.0
    for idx in range(bins):
        lo, hi = idx / bins, (idx + 1) / bins
        members = [(p, o) for p, o in zip(probabilities, outcomes) if (lo <= p < hi) or (idx == bins - 1 and p == 1.0)]
        if not members:
            continue
        conf = mean(p for p, _ in members)
        acc = mean(o for _, o in members)
        error += len(members) / total * abs(conf - acc)
    return error


def categorical_information_gain(
    prior: Sequence[float],
    posterior: Sequence[float],
    *,
    smoothing_epsilon: float | None = None,
) -> float:
    """KL(posterior || prior) with no hidden smoothing.

    If posterior places mass where an unsmoothed prior has zero mass, the KL is
    infinite. Callers that want smoothing must explicitly provide epsilon; both
    vectors are then additively smoothed and renormalized.
    """
    if len(prior) != len(posterior) or not prior:
        raise ValueError("prior/posterior must be non-empty and equal length")
    if any(x < 0 for x in prior) or any(x < 0 for x in posterior):
        raise ValueError("probabilities cannot be negative")
    if abs(sum(prior) - 1.0) > 1e-8 or abs(sum(posterior) - 1.0) > 1e-8:
        raise ValueError("probability vectors must sum to 1")
    if smoothing_epsilon is not None:
        if smoothing_epsilon <= 0:
            raise ValueError("smoothing epsilon must be positive")
        n = len(prior)
        den = 1.0 + n * smoothing_epsilon
        prior = tuple((p + smoothing_epsilon) / den for p in prior)
        posterior = tuple((q + smoothing_epsilon) / den for q in posterior)
    terms = []
    for p, q in zip(prior, posterior):
        if q == 0:
            continue
        if p == 0:
            return inf
        terms.append(q * log(q / p))
    return sum(terms)


def learning_progress(previous_error: float, current_error: float) -> float:
    return previous_error - current_error


def gain_per_cost(gain: float, cost: float) -> float:
    if cost <= 0:
        raise ValueError("cost must be positive")
    return gain / cost


def mutation_success_rate(verdicts: Iterable[str], success_states: frozenset[str] = frozenset({"ASSURED", "INCUMBENT"})) -> float:
    values = tuple(verdicts)
    if not values:
        raise ValueError("at least one mutation verdict required")
    return sum(v in success_states for v in values) / len(values)


def alpha_per_look(family_alpha: float, planned_looks: int) -> float:
    """Conservative preregistered Bonferroni alpha for repeated peeking."""
    if not 0 < family_alpha < 1 or planned_looks < 1:
        raise ValueError("invalid family alpha or planned look count")
    return family_alpha / planned_looks
