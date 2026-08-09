from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .meta import MethodChangeClass


class CheckConclusion(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    NEUTRAL = "NEUTRAL"


class PromotionDecision(str, Enum):
    PROMOTE = "PROMOTE"
    BLOCK = "BLOCK"
    CANNOT_CHECK = "CANNOT_CHECK"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    PROCESS_VIOLATION = "PROCESS_VIOLATION"


@dataclass(frozen=True)
class RequiredCheck:
    """Observed evidence for one required candidate validation check.

    ``exact_candidate_sha`` prevents a green check from another revision being
    reused. ``trusted_source`` records whether the check came from the frozen
    expected integration rather than an arbitrary status writer.
    """

    name: str
    conclusion: CheckConclusion
    source: str
    exact_candidate_sha: bool = True
    trusted_source: bool = True


@dataclass(frozen=True)
class PromotionPacket:
    """Evidence packet evaluated before the active main ref may move."""

    incumbent_sha: str
    candidate_sha: str
    observed_main_sha: str
    benchmark_frozen_before_candidate: bool
    receipt_present: bool
    history_preserved: bool
    required_checks: tuple[RequiredCheck, ...] = ()
    expected_required_checks: tuple[str, ...] = ()
    validator_fingerprints_unchanged: bool = True
    changed_protected_paths: tuple[str, ...] = ()
    fast_forward_compatible: bool = True
    blocking_failures: tuple[str, ...] = ()
    improvements: Mapping[str, float] | None = None
    regressions: Mapping[str, float] | None = None

    @property
    def has_positive_improvement(self) -> bool:
        if not self.improvements:
            return False
        return any(value > 0 for value in self.improvements.values())


@dataclass(frozen=True)
class PromotionVerdict:
    decision: PromotionDecision
    reasons: tuple[str, ...]

    @property
    def may_move_main(self) -> bool:
        return self.decision == PromotionDecision.PROMOTE


class PromotionGate:
    """Transactional, fail-closed gate for recursive self-modification.

    The gate is intentionally stricter than merely observing a green CI badge.
    It binds validation to the exact candidate revision, checks that the active
    main ref has not moved prematurely, and prevents the candidate from silently
    changing the evaluator that judges it.
    """

    @staticmethod
    def evaluate(
        change_class: MethodChangeClass,
        packet: PromotionPacket,
    ) -> PromotionVerdict:
        if packet.observed_main_sha != packet.incumbent_sha:
            return PromotionVerdict(
                PromotionDecision.PROCESS_VIOLATION,
                (
                    "active main moved before promotion verdict",
                    f"expected incumbent {packet.incumbent_sha}",
                    f"observed main {packet.observed_main_sha}",
                ),
            )

        if change_class == MethodChangeClass.CONSTITUTION:
            return PromotionVerdict(
                PromotionDecision.PROPOSAL_ONLY,
                ("constitutional changes cannot be auto-promoted by this gate",),
            )

        reasons: list[str] = []
        cannot_check: list[str] = []

        if packet.candidate_sha == packet.incumbent_sha:
            reasons.append("candidate SHA does not differ from incumbent")
        if not packet.fast_forward_compatible:
            reasons.append("candidate is not a verified fast-forward from incumbent")
        if not packet.benchmark_frozen_before_candidate:
            reasons.append("benchmark/evaluation was not frozen before candidate creation")
        if not packet.receipt_present:
            reasons.append("machine-readable research/change receipt missing")
        if not packet.history_preserved:
            reasons.append("historical evidence/supersession lineage not preserved")
        if not packet.validator_fingerprints_unchanged:
            reasons.append("protected validator/evaluator fingerprint changed")
        if packet.changed_protected_paths:
            reasons.extend(
                f"candidate changed protected evaluator path: {path}"
                for path in packet.changed_protected_paths
            )
        if packet.blocking_failures:
            reasons.extend(
                f"blocking meta-QoI failure: {failure}"
                for failure in packet.blocking_failures
            )

        observed_by_name = {check.name: check for check in packet.required_checks}
        expected_names = set(packet.expected_required_checks)
        if expected_names:
            missing = sorted(expected_names - observed_by_name.keys())
            if missing:
                cannot_check.extend(
                    f"required check not observed: {name}" for name in missing
                )
        elif not packet.required_checks:
            cannot_check.append("no required candidate checks were observed")

        for check in packet.required_checks:
            if not check.exact_candidate_sha:
                reasons.append(
                    f"check {check.name!r} does not belong to the exact candidate SHA"
                )
            if not check.trusted_source:
                reasons.append(
                    f"check {check.name!r} came from an untrusted status source"
                )
            if check.conclusion == CheckConclusion.PENDING:
                cannot_check.append(f"required check {check.name!r} is still pending")
            elif check.conclusion != CheckConclusion.SUCCESS:
                reasons.append(
                    f"required check {check.name!r} concluded {check.conclusion.value}"
                )

        if change_class == MethodChangeClass.WORKFLOW and not packet.has_positive_improvement:
            reasons.append("workflow challenger has no registered positive meta-QoI improvement")

        if reasons:
            return PromotionVerdict(PromotionDecision.BLOCK, tuple(reasons))
        if cannot_check:
            return PromotionVerdict(
                PromotionDecision.CANNOT_CHECK,
                tuple(cannot_check),
            )
        return PromotionVerdict(PromotionDecision.PROMOTE, ())
