from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class MethodChangeClass(str, Enum):
    IMPLEMENTATION = "CLASS_A_IMPLEMENTATION"
    WORKFLOW = "CLASS_B_WORKFLOW"
    CONSTITUTION = "CLASS_C_CONSTITUTION"


@dataclass(frozen=True)
class MetaEvaluation:
    tests_passed: bool
    receipt_present: bool
    benchmark_frozen_before_result: bool
    history_preserved: bool
    blocking_failures: tuple[str, ...] = ()
    improvements: Mapping[str, float] | None = None
    regressions: Mapping[str, float] | None = None
    independent_review_passed: bool = False

    @property
    def blocking_clean(self) -> bool:
        return not self.blocking_failures

    @property
    def has_positive_improvement(self) -> bool:
        if not self.improvements:
            return False
        return any(value > 0 for value in self.improvements.values())


class ConstitutionGuard:
    """Fail-closed promotion gate for recursive self-modification."""

    @staticmethod
    def can_auto_promote(
        change_class: MethodChangeClass,
        evaluation: MetaEvaluation,
    ) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []

        if change_class == MethodChangeClass.CONSTITUTION:
            reasons.append("constitutional changes require human-visible amendment review")

        if not evaluation.tests_passed:
            reasons.append("tests did not pass")
        if not evaluation.receipt_present:
            reasons.append("machine-readable change/research receipt missing")
        if not evaluation.benchmark_frozen_before_result:
            reasons.append("benchmark/evaluation was not frozen before observing result")
        if not evaluation.history_preserved:
            reasons.append("historical evidence/supersession lineage not preserved")
        if evaluation.blocking_failures:
            reasons.extend(
                f"blocking meta-QoI failure: {failure}"
                for failure in evaluation.blocking_failures
            )
        if change_class == MethodChangeClass.WORKFLOW and not evaluation.has_positive_improvement:
            reasons.append("workflow challenger has no registered positive meta-QoI improvement")

        return (not reasons, tuple(reasons))


@dataclass(frozen=True)
class ResearchBudget:
    exploit: float = 0.55
    diversify: float = 0.25
    moonshot: float = 0.10
    meta_rakl: float = 0.10

    def __post_init__(self) -> None:
        values = (self.exploit, self.diversify, self.moonshot, self.meta_rakl)
        if any(value < 0 for value in values):
            raise ValueError("research budget fractions must be non-negative")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("research budget fractions must sum to 1")

    def as_dict(self) -> dict[str, float]:
        return {
            "exploit": self.exploit,
            "diversify": self.diversify,
            "moonshot": self.moonshot,
            "meta_rakl": self.meta_rakl,
        }


class ResearchPortfolioScheduler:
    """Non-greedy portfolio policy for long-horizon research exploration."""

    def __init__(self, baseline: ResearchBudget | None = None) -> None:
        self.baseline = baseline or ResearchBudget()

    def allocate(
        self,
        *,
        saturation_wall: bool = False,
        high_value_residual: bool = False,
        constitutional_uncertainty: bool = False,
    ) -> ResearchBudget:
        if high_value_residual:
            # Focus on the implicated fiber but retain diversity and meta-checks.
            return ResearchBudget(
                exploit=0.70,
                diversify=0.15,
                moonshot=0.05,
                meta_rakl=0.10,
            )

        if saturation_wall:
            # Broaden the action surface instead of repeating local hill-climbing.
            return ResearchBudget(
                exploit=0.35,
                diversify=0.30,
                moonshot=0.20,
                meta_rakl=0.15,
            )

        if constitutional_uncertainty:
            # Do not let the method rewrite its axioms while mostly exploiting them.
            return ResearchBudget(
                exploit=0.35,
                diversify=0.25,
                moonshot=0.10,
                meta_rakl=0.30,
            )

        return self.baseline
