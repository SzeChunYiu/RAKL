"""Proposal-only matched benchmark for typed method telemetry (issue #125).

Compares two arms against the same frozen gold reconstruction labels:

1. ``PROSE_ACTION_TRACE`` — free-text ``action_trace`` / research-trace prose only;
2. ``TYPED_METHOD_TELEMETRY`` — a content-bound :class:`~rakl.method_telemetry.MethodTelemetry`
   record for the same episode.

A blind downstream case-study evaluator is denied free prose when scoring the
typed arm, and denied the typed fields when scoring the prose arm.  The QoI is
whether the evaluator can reconstruct:

- which prior experience changed routing;
- which alternatives were rejected and why;
- failure category;
- gluing status;
- saturation axes reopened;
- next-action rationale / id.

This module mints no theorem, tool, gluing, review-independence, or framework
authority.  A positive reconstruction lift is not automatic Self-RAKL promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple


BENCHMARK_SCHEMA_VERSION = "method-telemetry-benchmark-v1"

RECONSTRUCTION_FIELDS: Tuple[str, ...] = (
    "routing_influence_ids",
    "rejected_candidate_ids",
    "failure_class",
    "gluing_status",
    "reopened_axis_ids",
    "next_action_id",
)


class BenchmarkArm(str, Enum):
    PROSE_ACTION_TRACE = "PROSE_ACTION_TRACE"
    TYPED_METHOD_TELEMETRY = "TYPED_METHOD_TELEMETRY"


class BenchmarkVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class TrialVerdict(str, Enum):
    VALID = "VALID"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class GoldReconstructionLabels:
    """Evaluator-side gold for one episode. Never visible to arm construction."""

    episode_id: str
    routing_influence_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    failure_class: str
    gluing_status: str
    reopened_axis_ids: Tuple[str, ...]
    next_action_id: str
    labels_frozen_before_arm_access: Optional[bool]


@dataclass(frozen=True)
class ProseArmObservation:
    """Free-text arm: only action_trace / research-trace prose is available."""

    trial_id: str
    episode_id: str
    action_trace_prose: str
    research_trace_prose: str
    typed_fields_exposed: Optional[bool]


@dataclass(frozen=True)
class TypedArmObservation:
    """Typed arm: only MethodTelemetry fields are available (prose blinded)."""

    trial_id: str
    episode_id: str
    telemetry_artifact_hash: str
    routing_influence_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    failure_class: str
    gluing_status: str
    reopened_axis_ids: Tuple[str, ...]
    next_action_id: str
    prose_exposed: Optional[bool]


@dataclass(frozen=True)
class ReconstructionAttempt:
    """What a blind evaluator claimed after seeing exactly one arm."""

    trial_id: str
    arm: BenchmarkArm
    routing_influence_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    failure_class: str
    gluing_status: str
    reopened_axis_ids: Tuple[str, ...]
    next_action_id: str


@dataclass(frozen=True)
class FieldScore:
    field_name: str
    matched: bool
    gold_repr: str
    attempt_repr: str


@dataclass(frozen=True)
class ArmTrialReport:
    verdict: TrialVerdict
    arm: BenchmarkArm
    field_scores: Tuple[FieldScore, ...]
    reconstruction_rate: Optional[float]
    reasons: Tuple[str, ...]

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def activates_workflow_change(self) -> bool:
        return False


@dataclass(frozen=True)
class MatchedBenchmarkReport:
    """Paired comparison of prose vs typed arms on one frozen gold packet."""

    verdict: BenchmarkVerdict
    prose_report: Optional[ArmTrialReport]
    typed_report: Optional[ArmTrialReport]
    typed_lift: Optional[float]
    reasons: Tuple[str, ...]
    schema_version: str = BENCHMARK_SCHEMA_VERSION

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def promotes_framework_change(self) -> bool:
        return False


def _normalize_ids(values: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple(sorted({v.strip() for v in values if v and v.strip()}))


def _field_repr(value: object) -> str:
    if isinstance(value, tuple):
        return ",".join(_normalize_ids(value))
    return str(value).strip()


def _score_fields(
    gold: GoldReconstructionLabels,
    attempt: ReconstructionAttempt,
) -> Tuple[FieldScore, ...]:
    pairs: Mapping[str, Tuple[object, object]] = {
        "routing_influence_ids": (
            _normalize_ids(gold.routing_influence_ids),
            _normalize_ids(attempt.routing_influence_ids),
        ),
        "rejected_candidate_ids": (
            _normalize_ids(gold.rejected_candidate_ids),
            _normalize_ids(attempt.rejected_candidate_ids),
        ),
        "failure_class": (gold.failure_class.strip(), attempt.failure_class.strip()),
        "gluing_status": (gold.gluing_status.strip(), attempt.gluing_status.strip()),
        "reopened_axis_ids": (
            _normalize_ids(gold.reopened_axis_ids),
            _normalize_ids(attempt.reopened_axis_ids),
        ),
        "next_action_id": (gold.next_action_id.strip(), attempt.next_action_id.strip()),
    }
    scores: list[FieldScore] = []
    for name in RECONSTRUCTION_FIELDS:
        gold_v, attempt_v = pairs[name]
        scores.append(
            FieldScore(
                field_name=name,
                matched=gold_v == attempt_v,
                gold_repr=_field_repr(gold_v),
                attempt_repr=_field_repr(attempt_v),
            )
        )
    return tuple(scores)


def audit_prose_arm(
    gold: GoldReconstructionLabels,
    observation: ProseArmObservation,
    attempt: ReconstructionAttempt,
) -> ArmTrialReport:
    reasons: list[str] = []
    if observation.episode_id != gold.episode_id:
        reasons.append("prose_arm_episode_mismatch")
    if attempt.arm is not BenchmarkArm.PROSE_ACTION_TRACE:
        reasons.append("prose_arm_attempt_arm_mismatch")
    if attempt.trial_id != observation.trial_id:
        reasons.append("prose_arm_trial_id_mismatch")
    if gold.labels_frozen_before_arm_access is not True:
        reasons.append("gold_labels_not_frozen_before_arm_access")
    if observation.typed_fields_exposed is not False:
        reasons.append("prose_arm_typed_fields_not_blinded")
    if not observation.action_trace_prose.strip() and not observation.research_trace_prose.strip():
        reasons.append("prose_arm_empty")
    if reasons:
        return ArmTrialReport(
            TrialVerdict.TRIAL_INVALID if any(
                r.endswith("_mismatch") or r.endswith("_not_blinded") or r.endswith("_empty")
                for r in reasons
            )
            else TrialVerdict.CANNOT_CHECK,
            BenchmarkArm.PROSE_ACTION_TRACE,
            (),
            None,
            tuple(reasons),
        )
    scores = _score_fields(gold, attempt)
    rate = sum(1 for s in scores if s.matched) / len(scores)
    return ArmTrialReport(
        TrialVerdict.VALID,
        BenchmarkArm.PROSE_ACTION_TRACE,
        scores,
        rate,
        ("prose_arm_scored_against_frozen_gold",),
    )


def audit_typed_arm(
    gold: GoldReconstructionLabels,
    observation: TypedArmObservation,
    attempt: ReconstructionAttempt,
) -> ArmTrialReport:
    reasons: list[str] = []
    if observation.episode_id != gold.episode_id:
        reasons.append("typed_arm_episode_mismatch")
    if attempt.arm is not BenchmarkArm.TYPED_METHOD_TELEMETRY:
        reasons.append("typed_arm_attempt_arm_mismatch")
    if attempt.trial_id != observation.trial_id:
        reasons.append("typed_arm_trial_id_mismatch")
    if gold.labels_frozen_before_arm_access is not True:
        reasons.append("gold_labels_not_frozen_before_arm_access")
    if observation.prose_exposed is not False:
        reasons.append("typed_arm_prose_not_blinded")
    if not observation.telemetry_artifact_hash.strip():
        reasons.append("typed_arm_telemetry_hash_missing")
    if reasons:
        return ArmTrialReport(
            TrialVerdict.TRIAL_INVALID if any(
                r.endswith("_mismatch") or r.endswith("_not_blinded") or r.endswith("_missing")
                for r in reasons
            )
            else TrialVerdict.CANNOT_CHECK,
            BenchmarkArm.TYPED_METHOD_TELEMETRY,
            (),
            None,
            tuple(reasons),
        )
    scores = _score_fields(gold, attempt)
    rate = sum(1 for s in scores if s.matched) / len(scores)
    return ArmTrialReport(
        TrialVerdict.VALID,
        BenchmarkArm.TYPED_METHOD_TELEMETRY,
        scores,
        rate,
        ("typed_arm_scored_against_frozen_gold",),
    )


def compare_matched_arms(
    prose_report: ArmTrialReport | None,
    typed_report: ArmTrialReport | None,
) -> MatchedBenchmarkReport:
    """Compute typed-vs-prose reconstruction lift. Proposal-only; never promotes."""

    if prose_report is None or typed_report is None:
        return MatchedBenchmarkReport(
            BenchmarkVerdict.CANNOT_CHECK,
            prose_report,
            typed_report,
            None,
            ("matched_arm_report_missing",),
        )
    if prose_report.verdict is not TrialVerdict.VALID or typed_report.verdict is not TrialVerdict.VALID:
        return MatchedBenchmarkReport(
            BenchmarkVerdict.REJECT,
            prose_report,
            typed_report,
            None,
            ("matched_arms_not_both_valid",) + prose_report.reasons + typed_report.reasons,
        )
    assert prose_report.reconstruction_rate is not None
    assert typed_report.reconstruction_rate is not None
    lift = typed_report.reconstruction_rate - prose_report.reconstruction_rate
    return MatchedBenchmarkReport(
        BenchmarkVerdict.VALID,
        prose_report,
        typed_report,
        lift,
        (
            "matched_prose_vs_typed_reconstruction_scored",
            "proposal_only_no_framework_promotion",
        ),
    )
