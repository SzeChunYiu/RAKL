from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class CostBreakdown:
    """Non-hidden cost coordinates for learning/reasoning amortization studies."""

    induction: float = 0.0
    training: float = 0.0
    retrieval: float = 0.0
    adaptation_or_reasoning: float = 0.0
    tools: float = 0.0
    verification: float = 0.0

    def __post_init__(self) -> None:
        values = (
            self.induction,
            self.training,
            self.retrieval,
            self.adaptation_or_reasoning,
            self.tools,
            self.verification,
        )
        if min(values) < 0:
            raise ValueError("cost coordinates cannot be negative")

    @property
    def total(self) -> float:
        return sum(
            (
                self.induction,
                self.training,
                self.retrieval,
                self.adaptation_or_reasoning,
                self.tools,
                self.verification,
            )
        )


@dataclass(frozen=True)
class ReuseEconomics:
    induction_cost: float
    baseline_per_task_cost: float
    reuse_per_task_cost: float

    def __post_init__(self) -> None:
        if min(self.induction_cost, self.baseline_per_task_cost, self.reuse_per_task_cost) < 0:
            raise ValueError("costs cannot be negative")

    @property
    def marginal_saving(self) -> float:
        return self.baseline_per_task_cost - self.reuse_per_task_cost

    @property
    def break_even_reuse_count(self) -> int | None:
        """Smallest integer task count for which reuse is strictly cheaper.

        Returns None when the reuse path is not cheaper per task, so no amount of reuse
        can amortize a positive induction cost under this stationary cost model.
        """

        saving = self.marginal_saving
        if saving <= 0:
            return 0 if self.induction_cost == 0 and saving == 0 else None
        return max(1, int(self.induction_cost // saving) + 1)

    def baseline_total(self, n_tasks: int) -> float:
        if n_tasks < 0:
            raise ValueError("n_tasks cannot be negative")
        return n_tasks * self.baseline_per_task_cost

    def reuse_total(self, n_tasks: int) -> float:
        if n_tasks < 0:
            raise ValueError("n_tasks cannot be negative")
        return self.induction_cost + n_tasks * self.reuse_per_task_cost

    def saving_at(self, n_tasks: int) -> float:
        return self.baseline_total(n_tasks) - self.reuse_total(n_tasks)


@dataclass(frozen=True)
class CapabilityPoint:
    capability: float
    cost: CostBreakdown
    validity_failures: int = 0

    def __post_init__(self) -> None:
        if self.validity_failures < 0:
            raise ValueError("validity_failures cannot be negative")


def cost_to_capability(
    points: tuple[CapabilityPoint, ...],
    *,
    target_capability: float,
    max_validity_failures: int = 0,
) -> CapabilityPoint | None:
    """Return the minimum-total-cost point satisfying a frozen capability target."""

    eligible = [
        point
        for point in points
        if point.capability >= target_capability
        and point.validity_failures <= max_validity_failures
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda point: point.cost.total)
