from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class EvolutionVerdict(str, Enum):
    """Evidence level for a proposed self-improvement step.

    The enum deliberately avoids a global ``EVOLVED`` state.  The strongest
    verdict is scoped to the frozen development/assurance packets and the
    declared resource/evaluator boundary.
    """

    SCOPED_EVOLUTION_EVIDENCE = "SCOPED_EVOLUTION_EVIDENCE"
    TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED = (
        "TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED"
    )
    LOCAL_IMPROVEMENT_ONLY = "LOCAL_IMPROVEMENT_ONLY"
    META_OVERFIT = "META_OVERFIT"
    NO_IMPROVEMENT = "NO_IMPROVEMENT"
    BLOCKED = "BLOCKED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class AssuranceReserve:
    """A bounded blind holdout used to support self-evolution claims.

    Repeated optimizer-visible evaluation leaks information about a holdout.
    RAKL therefore treats assurance capacity as consumable rather than assuming
    that the same revealed benchmark remains independent forever.
    """

    benchmark_id: str
    exposure_limit: int = 1
    optimizer_visible_exposures: int = 0

    def __post_init__(self) -> None:
        if not self.benchmark_id:
            raise ValueError("benchmark_id cannot be empty")
        if self.exposure_limit < 1:
            raise ValueError("exposure_limit must be at least 1")
        if self.optimizer_visible_exposures < 0:
            raise ValueError("optimizer_visible_exposures cannot be negative")

    @property
    def available(self) -> bool:
        return self.optimizer_visible_exposures < self.exposure_limit

    @property
    def remaining_exposures(self) -> int:
        return max(0, self.exposure_limit - self.optimizer_visible_exposures)

    def consume(self) -> "AssuranceReserve":
        """Return the post-evaluation reserve state.

        Consumption is explicit even when the reserve is already exhausted so
        that callers cannot silently reset exposure history.
        """

        return AssuranceReserve(
            benchmark_id=self.benchmark_id,
            exposure_limit=self.exposure_limit,
            optimizer_visible_exposures=self.optimizer_visible_exposures + 1,
        )


@dataclass(frozen=True)
class EvolutionTrial:
    """Frozen evidence packet for one parent -> child method update.

    Improvement mappings use signed deltas normalized so positive values mean
    improvement.  Blocking validity failures are represented separately and can
    never be compensated by a positive optimization metric.
    """

    parent_version: str
    child_version: str
    development_benchmark_id: str
    development_improvements: Mapping[str, float]
    assurance_benchmark_id: str | None = None
    transfer_improvements: Mapping[str, float] | None = None
    transfer_regressions: Mapping[str, float] | None = None

    tests_passed: bool = True
    receipt_present: bool = True
    development_benchmark_frozen_before_result: bool = True
    assurance_benchmark_frozen_before_mutation: bool | None = None
    assurance_hidden_from_proposer: bool | None = None
    assurance_evaluator_separate: bool | None = None
    candidate_identity_verified: bool | None = None
    resource_comparability_verified: bool | None = None
    history_preserved: bool = True
    blocking_failures: tuple[str, ...] = ()

    assurance_exposure_limit: int = 1
    assurance_exposures_before_trial: int = 0

    def __post_init__(self) -> None:
        if not self.parent_version:
            raise ValueError("parent_version cannot be empty")
        if not self.child_version:
            raise ValueError("child_version cannot be empty")
        if not self.development_benchmark_id:
            raise ValueError("development_benchmark_id cannot be empty")
        if self.assurance_exposure_limit < 1:
            raise ValueError("assurance_exposure_limit must be at least 1")
        if self.assurance_exposures_before_trial < 0:
            raise ValueError("assurance_exposures_before_trial cannot be negative")

    @property
    def development_gain_qois(self) -> tuple[str, ...]:
        return tuple(
            sorted(name for name, delta in self.development_improvements.items() if delta > 0)
        )

    @property
    def transfer_gain_qois(self) -> tuple[str, ...]:
        if not self.transfer_improvements:
            return ()
        return tuple(
            sorted(name for name, delta in self.transfer_improvements.items() if delta > 0)
        )

    @property
    def transfer_regression_qois(self) -> tuple[str, ...]:
        if not self.transfer_regressions:
            return ()
        return tuple(
            sorted(name for name, magnitude in self.transfer_regressions.items() if magnitude > 0)
        )

    @property
    def assurance_fresh(self) -> bool:
        return self.assurance_exposures_before_trial < self.assurance_exposure_limit


@dataclass(frozen=True)
class EvolutionAssessment:
    verdict: EvolutionVerdict
    reasons: tuple[str, ...]
    development_gain_qois: tuple[str, ...]
    transfer_gain_qois: tuple[str, ...]
    transfer_regression_qois: tuple[str, ...]
    assurance_fresh: bool | None

    @property
    def supports_scoped_evolution(self) -> bool:
        return self.verdict == EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE


class SelfEvolutionAssessor:
    """Fail-closed classifier for evidence of RAKL self-evolution.

    This is a support/evaluation layer.  It does not mutate RAKL, promote a
    challenger, change the Constitution, or replace ``ConstitutionGuard``.
    """

    @staticmethod
    def assess(trial: EvolutionTrial) -> EvolutionAssessment:
        development_gain = trial.development_gain_qois
        transfer_gain = trial.transfer_gain_qois
        transfer_regression = trial.transfer_regression_qois

        def result(
            verdict: EvolutionVerdict,
            reasons: list[str] | tuple[str, ...],
            *,
            assurance_fresh: bool | None = None,
        ) -> EvolutionAssessment:
            return EvolutionAssessment(
                verdict=verdict,
                reasons=tuple(reasons),
                development_gain_qois=development_gain,
                transfer_gain_qois=transfer_gain,
                transfer_regression_qois=transfer_regression,
                assurance_fresh=assurance_fresh,
            )

        blocking_reasons: list[str] = []
        if not trial.tests_passed:
            blocking_reasons.append("candidate tests did not pass")
        if not trial.receipt_present:
            blocking_reasons.append("machine-readable evolution receipt missing")
        if not trial.history_preserved:
            blocking_reasons.append("negative/supersession history not preserved")
        blocking_reasons.extend(
            f"blocking invariant failure: {failure}" for failure in trial.blocking_failures
        )
        if blocking_reasons:
            return result(EvolutionVerdict.BLOCKED, blocking_reasons)

        chronology_or_identity_unknown: list[str] = []
        if not trial.development_benchmark_frozen_before_result:
            chronology_or_identity_unknown.append(
                "development benchmark was not frozen before observing result"
            )
        if trial.candidate_identity_verified is not True:
            chronology_or_identity_unknown.append("exact candidate identity is not verified")
        if chronology_or_identity_unknown:
            return result(EvolutionVerdict.CANNOT_CHECK, chronology_or_identity_unknown)

        if not development_gain:
            return result(
                EvolutionVerdict.NO_IMPROVEMENT,
                ("no registered positive development meta-QoI improvement",),
            )

        if trial.assurance_benchmark_id is None or trial.transfer_improvements is None:
            return result(
                EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY,
                ("development improvement observed but no transfer packet was evaluated",),
            )

        if transfer_regression:
            return result(
                EvolutionVerdict.META_OVERFIT,
                tuple(
                    f"registered transfer regression: {name}"
                    for name in transfer_regression
                ),
                assurance_fresh=trial.assurance_fresh,
            )

        if not transfer_gain:
            return result(
                EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY,
                ("development improvement did not produce a positive transfer gain",),
                assurance_fresh=trial.assurance_fresh,
            )

        # Transfer has been observed.  The next checks determine whether that
        # transfer is strong enough to support a fresh, blind assurance claim.
        cannot_check: list[str] = []
        if trial.assurance_benchmark_frozen_before_mutation is not True:
            cannot_check.append(
                "assurance benchmark was not demonstrably frozen before method mutation"
            )
        if trial.resource_comparability_verified is not True:
            cannot_check.append(
                "development/assurance model-tool-budget comparability is not verified"
            )
        if cannot_check:
            return result(
                EvolutionVerdict.CANNOT_CHECK,
                cannot_check,
                assurance_fresh=trial.assurance_fresh,
            )

        assurance_limits: list[str] = []
        if trial.assurance_hidden_from_proposer is not True:
            assurance_limits.append("assurance packet was not blind to the proposer")
        if trial.assurance_evaluator_separate is not True:
            assurance_limits.append("assurance evaluator is not separate/protected")
        if not trial.assurance_fresh:
            assurance_limits.append("assurance exposure budget was already exhausted")
        if assurance_limits:
            return result(
                EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED,
                assurance_limits,
                assurance_fresh=trial.assurance_fresh,
            )

        return result(
            EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE,
            (
                "positive development gain transferred to a fresh blind assurance packet",
                "blocking invariants, identity, history, evaluator separation and resource comparability are clean",
            ),
            assurance_fresh=True,
        )
