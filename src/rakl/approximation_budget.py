"""Composable approximation/error budgets for derived quotient/portal results.

A local VALID_APPROXIMATE receipt is not by itself a license for arbitrary
composition.  This module binds errors to metric, scope, and composition law,
and requires the final accumulated bound to fit the registered decision budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class ErrorComposition(str, Enum):
    ADDITIVE = "ADDITIVE"
    MAX = "MAX"
    REGISTERED_CUSTOM = "REGISTERED_CUSTOM"


class ApproximationVerdict(str, Enum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    EXCEEDS_BUDGET = "EXCEEDS_BUDGET"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ApproximationBudget:
    budget_id: str
    scope_hash: str
    metric_id: str
    max_error: float
    composition: ErrorComposition
    custom_composition_receipt_id: str | None = None

    def __post_init__(self) -> None:
        if not self.budget_id or not self.scope_hash or not self.metric_id:
            raise ValueError("approximation budget identity/scope/metric required")
        if not isfinite(self.max_error) or self.max_error < 0:
            raise ValueError("max_error must be finite and nonnegative")
        if self.composition is ErrorComposition.REGISTERED_CUSTOM and not self.custom_composition_receipt_id:
            raise ValueError("custom composition requires a registered receipt")


@dataclass(frozen=True)
class ApproximationStep:
    step_id: str
    scope_hash: str
    metric_id: str
    certified_error_bound: float
    evidence_receipt_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.step_id or not self.scope_hash or not self.metric_id or not self.evidence_receipt_ids:
            raise ValueError("approximation step requires bound identity and evidence")
        if not isfinite(self.certified_error_bound) or self.certified_error_bound < 0:
            raise ValueError("certified error must be finite and nonnegative")


@dataclass(frozen=True)
class ApproximationAssessment:
    verdict: ApproximationVerdict
    accumulated_error_bound: float | None
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_composed_approximation(
    budget: ApproximationBudget,
    steps: tuple[ApproximationStep, ...],
) -> ApproximationAssessment:
    if not steps:
        return ApproximationAssessment(ApproximationVerdict.CANNOT_CHECK, None, ("no_approximation_steps",))
    reasons: list[str] = []
    for step in steps:
        if step.scope_hash != budget.scope_hash:
            reasons.append(f"scope_mismatch:{step.step_id}")
        if step.metric_id != budget.metric_id:
            reasons.append(f"metric_mismatch:{step.step_id}")
    if reasons:
        return ApproximationAssessment(ApproximationVerdict.CANNOT_CHECK, None, tuple(reasons))
    values = [step.certified_error_bound for step in steps]
    if budget.composition is ErrorComposition.ADDITIVE:
        total = sum(values)
    elif budget.composition is ErrorComposition.MAX:
        total = max(values)
    else:
        # A receipt saying a custom law exists is not an executable law.  The
        # caller must provide a separately verified composition evaluator.
        return ApproximationAssessment(
            ApproximationVerdict.CANNOT_CHECK,
            None,
            ("custom_error_composition_not_executed",),
        )
    if total <= budget.max_error:
        return ApproximationAssessment(ApproximationVerdict.WITHIN_BUDGET, total, ())
    return ApproximationAssessment(
        ApproximationVerdict.EXCEEDS_BUDGET,
        total,
        (f"accumulated_error:{total}>budget:{budget.max_error}",),
    )
