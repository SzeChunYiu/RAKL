from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class InventionWorldKind(str, Enum):
    RECONSTRUCTION = "RECONSTRUCTION"
    NOVEL_COMPOSITION = "NOVEL_COMPOSITION"
    CROSS_DOMAIN_TRANSFER = "CROSS_DOMAIN_TRANSFER"
    ADVERSARIAL_RESIDUAL = "ADVERSARIAL_RESIDUAL"


@dataclass(frozen=True)
class InventionBenchmarkCase:
    benchmark_id: str
    world_kind: InventionWorldKind
    frozen_evidence_ids: Tuple[str, ...]
    target_signature: Tuple[str, ...]
    minimum_signature_recall: float
    minimum_signature_precision: float
    hidden_target_id: str
    target_hidden_from_proposer: Optional[bool]
    thresholds_frozen_before_attempt: Optional[bool]
    evaluator_separate: Optional[bool]
    source_components: Tuple[str, ...] = ()
    required_novel_combinations: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.benchmark_id or not self.hidden_target_id:
            raise ValueError("benchmark and hidden target identities are required")
        if not self.frozen_evidence_ids:
            raise ValueError("frozen evidence packet is required")
        if not self.target_signature:
            raise ValueError("evaluator target signature is required")
        for value in (self.minimum_signature_recall, self.minimum_signature_precision):
            if value < 0 or value > 1:
                raise ValueError("signature thresholds must lie in [0, 1]")


@dataclass(frozen=True)
class InventionAttempt:
    benchmark_id: str
    candidate_id: str
    recovered_signature: Tuple[str, ...]
    candidate_frozen_before_target_exposure: Optional[bool]
    hidden_target_exposed: Optional[bool]
    target_validation_passed: Optional[bool]
    formal_verification_passed: Optional[bool]
    source_component_ids_used: Tuple[str, ...] = ()
    generated_combination_ids: Tuple[str, ...] = ()


class InventionBenchmarkVerdict(str, Enum):
    INVENTION_RECOVERED = "INVENTION_RECOVERED"
    PARTIAL_RECOVERY = "PARTIAL_RECOVERY"
    NO_RECOVERY = "NO_RECOVERY"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class InventionBenchmarkReport:
    verdict: InventionBenchmarkVerdict
    recall: Optional[float]
    precision: Optional[float]
    novel_combination_recall: Optional[float]
    reasons: Tuple[str, ...]

    @property
    def supports_invention_capability(self) -> bool:
        return self.verdict is InventionBenchmarkVerdict.INVENTION_RECOVERED


def _safe_recall(required: set[str], observed: set[str]) -> float:
    return len(required & observed) / len(required) if required else 1.0


def _safe_precision(required: set[str], observed: set[str]) -> float:
    return len(required & observed) / len(observed) if observed else 0.0


def evaluate_invention_attempt(
    case: InventionBenchmarkCase,
    attempt: InventionAttempt,
) -> InventionBenchmarkReport:
    if attempt.benchmark_id != case.benchmark_id:
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            ("attempt_bound_to_wrong_benchmark",),
        )

    chronology_unknown = []
    if case.target_hidden_from_proposer is None:
        chronology_unknown.append("target_hidden_status_unknown")
    if case.thresholds_frozen_before_attempt is None:
        chronology_unknown.append("benchmark_threshold_chronology_unknown")
    if case.evaluator_separate is None:
        chronology_unknown.append("evaluator_separation_unknown")
    if attempt.candidate_frozen_before_target_exposure is None:
        chronology_unknown.append("candidate_freeze_chronology_unknown")
    if attempt.hidden_target_exposed is None:
        chronology_unknown.append("attempt_target_exposure_unknown")
    if chronology_unknown:
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            tuple(chronology_unknown),
        )

    if (
        case.target_hidden_from_proposer is not True
        or case.thresholds_frozen_before_attempt is not True
        or case.evaluator_separate is not True
        or attempt.candidate_frozen_before_target_exposure is not True
        or attempt.hidden_target_exposed is True
    ):
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            ("hidden_world_or_chronology_integrity_failed",),
        )

    if attempt.formal_verification_passed is None or attempt.target_validation_passed is None:
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            ("formal_or_target_validation_outcome_missing",),
        )

    target = set(case.target_signature)
    recovered = set(attempt.recovered_signature)
    recall = _safe_recall(target, recovered)
    precision = _safe_precision(target, recovered)

    novel_recall: Optional[float] = None
    if case.world_kind is InventionWorldKind.NOVEL_COMPOSITION:
        required_novel = set(case.required_novel_combinations)
        generated = set(attempt.generated_combination_ids)
        novel_recall = _safe_recall(required_novel, generated)

    threshold_pass = (
        recall >= case.minimum_signature_recall
        and precision >= case.minimum_signature_precision
    )
    if novel_recall is not None:
        threshold_pass = threshold_pass and novel_recall == 1.0

    if (
        threshold_pass
        and attempt.formal_verification_passed is True
        and attempt.target_validation_passed is True
    ):
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.INVENTION_RECOVERED,
            recall,
            precision,
            novel_recall,
            (
                "hidden_target_signature_recovered",
                "candidate_formally_verified",
                "target_validation_passed",
                "benchmark_chronology_and_evaluator_separation_clean",
            ),
        )

    if recall > 0 or precision > 0:
        return InventionBenchmarkReport(
            InventionBenchmarkVerdict.PARTIAL_RECOVERY,
            recall,
            precision,
            novel_recall,
            (
                "some_hidden_structure_recovered_but_certifying_threshold_not_met",
                "failed_or_partial attempts remain training/evolution evidence only",
            ),
        )

    return InventionBenchmarkReport(
        InventionBenchmarkVerdict.NO_RECOVERY,
        recall,
        precision,
        novel_recall,
        ("no_registered_hidden_target_structure_recovered",),
    )


@dataclass(frozen=True)
class InventionBenchmarkSuiteReport:
    reports: Tuple[InventionBenchmarkReport, ...]
    success_rate: float
    all_world_kinds_represented: bool
    supports_scoped_invention_claim: bool


def summarize_invention_suite(
    cases: Tuple[InventionBenchmarkCase, ...],
    reports: Tuple[InventionBenchmarkReport, ...],
) -> InventionBenchmarkSuiteReport:
    if len(cases) != len(reports):
        raise ValueError("case/report count mismatch")
    if not reports:
        return InventionBenchmarkSuiteReport((), 0.0, False, False)
    successes = sum(report.supports_invention_capability for report in reports)
    success_rate = successes / len(reports)
    required_worlds = {
        InventionWorldKind.RECONSTRUCTION,
        InventionWorldKind.NOVEL_COMPOSITION,
        InventionWorldKind.ADVERSARIAL_RESIDUAL,
    }
    represented = {case.world_kind for case in cases}
    all_worlds = required_worlds.issubset(represented)
    valid_reports = all(
        report.verdict
        not in {InventionBenchmarkVerdict.TRIAL_INVALID, InventionBenchmarkVerdict.CANNOT_CHECK}
        for report in reports
    )
    return InventionBenchmarkSuiteReport(
        reports,
        success_rate,
        all_worlds,
        bool(all_worlds and valid_reports and success_rate > 0),
    )
