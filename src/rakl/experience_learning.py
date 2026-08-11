from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Tuple

from .experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
)
from .failure_lattice import FailureDiagnosisStatus, FailureExperience
from .research_tool_inventory import ResearchTool, ResearchToolAuthority


class ConsolidationVerdict(str, Enum):
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    VERIFIED_LOCAL = "VERIFIED_LOCAL"
    CONDITIONALLY_REUSABLE = "CONDITIONALLY_REUSABLE"
    PROOF_BACKED = "PROOF_BACKED"
    CONTRADICTED = "CONTRADICTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class LessonConsolidationEvidence:
    """Evidence packet for promoting a lesson without rewriting its episodes."""

    supporting_episode_ids: Tuple[str, ...]
    contradicting_episode_ids: Tuple[str, ...] = ()
    diagnostic_episode_ids: Tuple[str, ...] = ()
    replay_episode_ids: Tuple[str, ...] = ()
    fresh_transfer_episode_ids: Tuple[str, ...] = ()
    verification_artifact_ids: Tuple[str, ...] = ()
    proof_certificate_ids: Tuple[str, ...] = ()
    evaluator_separated: bool | None = None
    evidence_lineage_independent: bool | None = None


@dataclass(frozen=True)
class LessonConsolidationReport:
    verdict: ConsolidationVerdict
    target_authority: LessonAuthority
    reasons: Tuple[str, ...]
    supporting_episode_ids: Tuple[str, ...]
    contradicting_episode_ids: Tuple[str, ...]

    @property
    def reusable(self) -> bool:
        return self.verdict in {
            ConsolidationVerdict.CONDITIONALLY_REUSABLE,
            ConsolidationVerdict.PROOF_BACKED,
        }


def _episode_map(ledger: ExperienceLedger) -> dict[str, TaskEpisode]:
    return {episode.episode_id: episode for episode in ledger.episodes}


def _positive_evidence_ids(evidence: LessonConsolidationEvidence) -> Tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            evidence.supporting_episode_ids
            + evidence.diagnostic_episode_ids
            + evidence.replay_episode_ids
            + evidence.fresh_transfer_episode_ids
        )
    )


def assess_lesson_consolidation(
    ledger: ExperienceLedger,
    candidate: Lesson,
    evidence: LessonConsolidationEvidence,
) -> LessonConsolidationReport:
    """Promote only what outcome-linked evidence supports.

    Same-context reflection can create a candidate lesson, but reusable authority
    requires verification plus fresh transfer or proof.  A failed fresh transfer
    bounds the lesson instead of being averaged away.
    """

    episodes = _episode_map(ledger)
    referenced = set(evidence.supporting_episode_ids)
    referenced |= set(evidence.contradicting_episode_ids)
    referenced |= set(evidence.diagnostic_episode_ids)
    referenced |= set(evidence.replay_episode_ids)
    referenced |= set(evidence.fresh_transfer_episode_ids)
    missing = referenced - set(episodes)
    positive_ids = _positive_evidence_ids(evidence)
    if missing:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.CANDIDATE,
            tuple(f"unknown_episode:{item}" for item in sorted(missing)),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    if set(candidate.supporting_episode_ids) - set(evidence.supporting_episode_ids):
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.CANDIDATE,
            ("candidate_support_not_covered_by_consolidation_packet",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    if not evidence.supporting_episode_ids:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.CANDIDATE,
            ("supporting_experience_missing",),
            (),
            evidence.contradicting_episode_ids,
        )

    failed_transfer = tuple(
        episode_id
        for episode_id in evidence.fresh_transfer_episode_ids
        if episodes[episode_id].outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.BLOCKED}
    )
    if failed_transfer:
        return LessonConsolidationReport(
            ConsolidationVerdict.CONTRADICTED,
            LessonAuthority.VERIFIED_LOCAL if evidence.verification_artifact_ids else LessonAuthority.CANDIDATE,
            tuple(f"fresh_transfer_failed:{item}" for item in failed_transfer),
            positive_ids,
            tuple(dict.fromkeys(evidence.contradicting_episode_ids + failed_transfer)),
        )

    if evidence.proof_certificate_ids:
        if not evidence.verification_artifact_ids:
            return LessonConsolidationReport(
                ConsolidationVerdict.CANNOT_CHECK,
                LessonAuthority.CANDIDATE,
                ("proof_backing_without_registered_verification_artifact",),
                positive_ids,
                evidence.contradicting_episode_ids,
            )
        return LessonConsolidationReport(
            ConsolidationVerdict.PROOF_BACKED,
            LessonAuthority.PROOF_BACKED,
            ("registered proof backing and verification support the scoped lesson",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )

    if not evidence.verification_artifact_ids:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANDIDATE_ONLY,
            LessonAuthority.CANDIDATE,
            ("reflection_or_outcome_pattern_observed_without_external_verification",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )

    if not evidence.fresh_transfer_episode_ids:
        return LessonConsolidationReport(
            ConsolidationVerdict.VERIFIED_LOCAL,
            LessonAuthority.VERIFIED_LOCAL,
            ("lesson verified in source/replay scope but fresh transfer is absent",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )

    transfer_successes = tuple(
        episode_id
        for episode_id in evidence.fresh_transfer_episode_ids
        if episodes[episode_id].outcome is EpisodeOutcome.SUCCESS
    )
    if len(transfer_successes) != len(evidence.fresh_transfer_episode_ids):
        return LessonConsolidationReport(
            ConsolidationVerdict.VERIFIED_LOCAL,
            LessonAuthority.VERIFIED_LOCAL,
            ("fresh transfer is not uniformly successful; retain local authority and refine boundary",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    if evidence.evaluator_separated is not True:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.VERIFIED_LOCAL,
            ("fresh_transfer_evaluator_not_separated",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    if evidence.evidence_lineage_independent is not True:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.VERIFIED_LOCAL,
            ("fresh_transfer_evidence_lineage_not_independent",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    return LessonConsolidationReport(
        ConsolidationVerdict.CONDITIONALLY_REUSABLE,
        LessonAuthority.CONDITIONALLY_REUSABLE,
        ("verified source lesson transferred successfully to fresh independent evidence",),
        positive_ids,
        evidence.contradicting_episode_ids,
    )


def promoted_lesson_version(
    candidate: Lesson,
    *,
    new_lesson_id: str,
    artifact_hash: str,
    report: LessonConsolidationReport,
    evidence: LessonConsolidationEvidence,
) -> Lesson:
    if not new_lesson_id or not artifact_hash:
        raise ValueError("promoted lesson version requires new id and artifact hash")
    if report.verdict is ConsolidationVerdict.CANNOT_CHECK:
        raise ValueError("cannot promote lesson from CANNOT_CHECK evidence")
    return replace(
        candidate,
        lesson_id=new_lesson_id,
        authority=report.target_authority,
        supporting_episode_ids=report.supporting_episode_ids,
        contradicting_episode_ids=tuple(dict.fromkeys(report.contradicting_episode_ids)),
        evidence_pointers=tuple(dict.fromkeys(candidate.evidence_pointers + evidence.verification_artifact_ids + evidence.proof_certificate_ids)),
        artifact_hash=artifact_hash,
        parent_lesson_id=candidate.lesson_id,
    )


def episode_to_failure_experience(
    episode: TaskEpisode,
    *,
    failure_id: str,
    candidate_id: str,
    method_family: str,
    failure_mode: str,
    competing_diagnoses: Tuple[str, ...],
    selected_diagnosis: str = "",
    diagnosis_status: FailureDiagnosisStatus = FailureDiagnosisStatus.OBSERVED_ONLY,
    broken_assumptions: Tuple[str, ...] = (),
    scope_conditions: Tuple[str, ...] = (),
    falsifier_or_attempt: str = "episode outcome",
    local_repair_attempts: Tuple[str, ...] = (),
) -> FailureExperience:
    if episode.outcome not in {EpisodeOutcome.FAILURE, EpisodeOutcome.PARTIAL_SUCCESS, EpisodeOutcome.BLOCKED}:
        raise ValueError("only non-success episodes can project into failure experience")
    return FailureExperience(
        failure_id=failure_id,
        atom_id=episode.atom_id,
        candidate_id=candidate_id,
        context_packet_hash=episode.context_hash,
        research_trace_event_id=episode.episode_id,
        method_family=method_family,
        failure_mode=failure_mode,
        residual_signature=episode.residual_signature,
        broken_assumptions=broken_assumptions,
        scope_conditions=scope_conditions or (f"context_hash:{episode.context_hash}",),
        competing_diagnoses=competing_diagnoses,
        selected_diagnosis=selected_diagnosis,
        diagnosis_status=diagnosis_status,
        evidence_pointers=episode.evidence_pointers,
        falsifier_or_attempt=falsifier_or_attempt,
        observed_result=episode.outcome.value,
        artifact_hash=episode.artifact_hash,
        timestamp=episode.timestamp,
        local_repair_attempts=local_repair_attempts,
    )


def lesson_to_research_tool(
    lesson: Lesson,
    ledger: ExperienceLedger,
    *,
    tool_id: str,
    name: str,
    kind: str,
    known_failure_ids: Tuple[str, ...] = (),
) -> ResearchTool:
    if lesson.kind not in {LessonKind.OPERATOR, LessonKind.STRATEGY, LessonKind.REPRESENTATION}:
        raise ValueError("only operational lessons can project into research tools")
    episodes = _episode_map(ledger)
    if not lesson.supporting_episode_ids:
        raise ValueError("tool lesson requires at least one supporting episode")
    source = episodes.get(lesson.supporting_episode_ids[0])
    if source is None:
        raise ValueError("tool lesson supporting episode is missing from ledger")
    authority = {
        LessonAuthority.CANDIDATE: ResearchToolAuthority.HEURISTIC,
        LessonAuthority.VERIFIED_LOCAL: ResearchToolAuthority.VERIFIED_LOCAL,
        LessonAuthority.CONDITIONALLY_REUSABLE: ResearchToolAuthority.CONDITIONALLY_REUSABLE,
        LessonAuthority.PROOF_BACKED: ResearchToolAuthority.PROOF_BACKED,
        LessonAuthority.SUPERSEDED: ResearchToolAuthority.SUPERSEDED,
    }[lesson.authority]
    return ResearchTool(
        tool_id=tool_id,
        name=name,
        kind=kind,
        abstraction=lesson.kind.value,
        source_atom_id=source.atom_id,
        source_candidate_id=lesson.lesson_id,
        source_result_ids=source.verification_ids or source.observation_ids or (source.episode_id,),
        source_context_hash=source.context_hash,
        authority=authority,
        preconditions=lesson.context_scope,
        structural_signature=lesson.trigger_signature,
        operation=lesson.action,
        guaranteed_effects=lesson.expected_effects,
        non_guarantees=lesson.boundaries,
        validation_obligations=lesson.validation_obligations,
        evidence_pointers=lesson.evidence_pointers,
        known_failure_ids=known_failure_ids,
        proof_backing=lesson.evidence_pointers if authority is ResearchToolAuthority.PROOF_BACKED else (),
        artifact_hash=lesson.artifact_hash,
    )
