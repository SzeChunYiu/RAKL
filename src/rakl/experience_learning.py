from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Tuple

from .experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    lesson_content_bytes,
)
from .failure_lattice import FailureDiagnosisStatus, FailureExperience
from .research_tool_inventory import ResearchTool, ResearchToolAuthority
from .v3_authority import (
    AttestationPurpose,
    ProtectedAuthorityContext,
    resolve_protected_attestation,
    canonical_json_bytes,
)


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
    verification_attestation_id: str | None = None
    transfer_attestation_id: str | None = None
    proof_attestation_id: str | None = None
    authority_context: ProtectedAuthorityContext | None = None


@dataclass(frozen=True)
class LessonConsolidationReport:
    verdict: ConsolidationVerdict
    target_authority: LessonAuthority
    reasons: Tuple[str, ...]
    supporting_episode_ids: Tuple[str, ...]
    contradicting_episode_ids: Tuple[str, ...]
    authority_attestation_id: str | None = None
    authority_subject_hash: str | None = None
    evidence_packet_hash: str | None = None

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


def consolidation_evidence_packet_hash(
    candidate: Lesson,
    evidence: LessonConsolidationEvidence,
) -> str:
    context = evidence.authority_context
    artifact_bindings = () if context is None else tuple(
        sorted((item.artifact_id, item.payload_sha256, item.frozen_at, item.producer_id) for item in context.artifacts)
    )
    attestation_bindings = () if context is None else tuple(
        sorted((item.attestation_id, item.signature, item.subject_hash, item.issued_at) for item in context.attestations)
    )
    return sha256(canonical_json_bytes({
        "candidate_hash": candidate.artifact_hash,
        "supporting_episode_ids": list(evidence.supporting_episode_ids),
        "contradicting_episode_ids": list(evidence.contradicting_episode_ids),
        "diagnostic_episode_ids": list(evidence.diagnostic_episode_ids),
        "replay_episode_ids": list(evidence.replay_episode_ids),
        "fresh_transfer_episode_ids": list(evidence.fresh_transfer_episode_ids),
        "verification_attestation_id": evidence.verification_attestation_id,
        "transfer_attestation_id": evidence.transfer_attestation_id,
        "proof_attestation_id": evidence.proof_attestation_id,
        "artifact_bindings": artifact_bindings,
        "attestation_bindings": attestation_bindings,
    })).hexdigest()


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
    packet_hash = consolidation_evidence_packet_hash(candidate, evidence)
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
            LessonAuthority.CANDIDATE,
            tuple(f"fresh_transfer_failed:{item}" for item in failed_transfer),
            positive_ids,
            tuple(dict.fromkeys(evidence.contradicting_episode_ids + failed_transfer)),
        )

    support_hashes = tuple(episodes[item].artifact_hash for item in evidence.supporting_episode_ids + evidence.replay_episode_ids)
    verification = resolve_protected_attestation(
        evidence.authority_context,
        evidence.verification_attestation_id,
        purpose=AttestationPurpose.LESSON_VERIFICATION,
        subject_hash=candidate.artifact_hash,
        required_artifact_hashes=support_hashes,
    )

    if evidence.proof_attestation_id:
        if not verification.valid:
            return LessonConsolidationReport(
                ConsolidationVerdict.CANNOT_CHECK,
                LessonAuthority.CANDIDATE,
                ("proof_backing_without_resolved_verification",) + verification.reasons,
                positive_ids,
                evidence.contradicting_episode_ids,
            )
        proof = resolve_protected_attestation(
            evidence.authority_context,
            evidence.proof_attestation_id,
            purpose=AttestationPurpose.LESSON_PROOF,
            subject_hash=candidate.artifact_hash,
            required_artifact_hashes=support_hashes,
        )
        if not proof.valid:
            return LessonConsolidationReport(
                ConsolidationVerdict.CANNOT_CHECK,
                LessonAuthority.CANDIDATE,
                proof.reasons,
                positive_ids,
                evidence.contradicting_episode_ids,
            )
        return LessonConsolidationReport(
            ConsolidationVerdict.PROOF_BACKED,
            LessonAuthority.PROOF_BACKED,
            ("protected proof and verification attestations resolve exact scoped content",),
            positive_ids,
            evidence.contradicting_episode_ids,
            evidence.proof_attestation_id,
            candidate.artifact_hash,
            packet_hash,
        )

    if not evidence.verification_attestation_id:
        if evidence.verification_artifact_ids or evidence.proof_certificate_ids or evidence.evaluator_separated is not None or evidence.evidence_lineage_independent is not None:
            return LessonConsolidationReport(
                ConsolidationVerdict.CANNOT_CHECK,
                LessonAuthority.CANDIDATE,
                ("caller_ids_or_boole_cannot_substitute_for_protected_attestation",),
                positive_ids,
                evidence.contradicting_episode_ids,
            )
        return LessonConsolidationReport(
            ConsolidationVerdict.CANDIDATE_ONLY,
            LessonAuthority.CANDIDATE,
            ("reflection_or_outcome_pattern_observed_without_external_verification",),
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    if not verification.valid:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.CANDIDATE,
            verification.reasons,
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
            evidence.verification_attestation_id,
            candidate.artifact_hash,
            packet_hash,
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
    transfer = resolve_protected_attestation(
        evidence.authority_context,
        evidence.transfer_attestation_id,
        purpose=AttestationPurpose.LESSON_TRANSFER,
        subject_hash=candidate.artifact_hash,
        required_artifact_hashes=tuple(episodes[item].artifact_hash for item in evidence.fresh_transfer_episode_ids),
    )
    if not transfer.valid:
        return LessonConsolidationReport(
            ConsolidationVerdict.CANNOT_CHECK,
            LessonAuthority.VERIFIED_LOCAL,
            transfer.reasons,
            positive_ids,
            evidence.contradicting_episode_ids,
        )
    return LessonConsolidationReport(
        ConsolidationVerdict.CONDITIONALLY_REUSABLE,
        LessonAuthority.CONDITIONALLY_REUSABLE,
        ("verified source lesson transferred successfully to fresh independent evidence",),
        positive_ids,
        evidence.contradicting_episode_ids,
        evidence.transfer_attestation_id,
        candidate.artifact_hash,
        packet_hash,
    )


def promoted_lesson_version(
    candidate: Lesson,
    *,
    new_lesson_id: str,
    artifact_hash: str,
    report: LessonConsolidationReport,
    evidence: LessonConsolidationEvidence,
) -> Lesson:
    if not new_lesson_id:
        raise ValueError("promoted lesson version requires new id")
    if report.verdict is ConsolidationVerdict.CANNOT_CHECK:
        raise ValueError("cannot promote lesson from CANNOT_CHECK evidence")
    if report.authority_subject_hash != candidate.artifact_hash:
        raise ValueError("consolidation report subject does not match exact candidate content")
    if report.evidence_packet_hash != consolidation_evidence_packet_hash(candidate, evidence):
        raise ValueError("consolidation report does not bind the exact evidence packet")
    if report.supporting_episode_ids != _positive_evidence_ids(evidence):
        raise ValueError("consolidation report support does not match exact evidence set")
    if report.target_authority is not LessonAuthority.CANDIDATE and not report.authority_attestation_id:
        raise ValueError("promoted lesson requires resolved protected authority attestation")
    draft = replace(
        candidate,
        lesson_id=new_lesson_id,
        authority=report.target_authority,
        supporting_episode_ids=report.supporting_episode_ids,
        contradicting_episode_ids=tuple(dict.fromkeys(report.contradicting_episode_ids)),
        evidence_pointers=tuple(
            dict.fromkeys(
                candidate.evidence_pointers
                + tuple(item for item in (evidence.verification_attestation_id, evidence.transfer_attestation_id, evidence.proof_attestation_id) if item)
            )
        ),
        artifact_hash="",
        parent_lesson_id=candidate.lesson_id,
        authority_attestation_id=report.authority_attestation_id,
        authority_subject_hash=report.authority_subject_hash,
        authority_evidence_packet_hash=report.evidence_packet_hash,
    )
    # The caller-provided artifact_hash is retained only as a backwards API
    # parameter; authority identity is always recomputed from exact content.
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


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


def research_tool_projection_preview(
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
    if authority is not ResearchToolAuthority.HEURISTIC:
        if not lesson.authority_attestation_id or not lesson.authority_subject_hash:
            raise ValueError("research tool preview requires lesson authority lineage")
    draft = ResearchTool(
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
        # The projected tool content carries the exact promoted lesson identity,
        # rather than only its human-readable id and operation.  This prevents a
        # projection attestation from being replayed across a same-id lesson
        # whose support or other reviewed content has changed.
        evidence_pointers=tuple(
            dict.fromkeys(
                lesson.evidence_pointers
                + (f"source_lesson_sha256:{lesson.artifact_hash}",)
            )
        ),
        known_failure_ids=known_failure_ids,
        proof_backing=lesson.evidence_pointers if authority is ResearchToolAuthority.PROOF_BACKED else (),
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(research_tool_content_bytes(draft)).hexdigest())


def lesson_to_research_tool(
    lesson: Lesson,
    ledger: ExperienceLedger,
    *,
    tool_id: str,
    name: str,
    kind: str,
    known_failure_ids: Tuple[str, ...] = (),
    authority_context: ProtectedAuthorityContext | None = None,
    projection_attestation_id: str | None = None,
    projection_artifact_id: str | None = None,
) -> ResearchTool:
    recorded_lessons = tuple(
        item for item in ledger.lessons if item.lesson_id == lesson.lesson_id
    )
    if (
        len(recorded_lessons) != 1
        or recorded_lessons[0] != lesson
        or sha256(lesson_content_bytes(lesson)).hexdigest() != lesson.artifact_hash
    ):
        raise ValueError(
            "research tool projection requires the exact recorded lesson version"
        )
    episodes = _episode_map(ledger)
    tool = research_tool_projection_preview(
        lesson,
        ledger,
        tool_id=tool_id,
        name=name,
        kind=kind,
        known_failure_ids=known_failure_ids,
    )
    if tool.authority is not ResearchToolAuthority.HEURISTIC:
        purpose = {
            LessonAuthority.VERIFIED_LOCAL: AttestationPurpose.LESSON_VERIFICATION,
            LessonAuthority.CONDITIONALLY_REUSABLE: AttestationPurpose.LESSON_TRANSFER,
            LessonAuthority.PROOF_BACKED: AttestationPurpose.LESSON_PROOF,
            LessonAuthority.SUPERSEDED: AttestationPurpose.LESSON_VERIFICATION,
        }[lesson.authority]
        resolution = resolve_protected_attestation(
            authority_context,
            lesson.authority_attestation_id,
            purpose=purpose,
            subject_hash=lesson.authority_subject_hash or "",
            required_artifact_hashes=tuple(
                episodes[item].artifact_hash
                for item in lesson.supporting_episode_ids
                if item in episodes
            ),
        )
        if not resolution.valid:
            raise ValueError(
                "research tool authority requires resolved protected lesson attestation: "
                + ", ".join(resolution.reasons)
            )
        attestation = next(
            item
            for item in authority_context.attestations
            if item.attestation_id == lesson.authority_attestation_id
        )
        episode_id_by_hash = {
            item.artifact_hash: item.episode_id for item in ledger.episodes
        }
        attested_episode_ids = {
            episode_id_by_hash[digest]
            for _, digest in attestation.evidence_bindings
            if digest in episode_id_by_hash
        }
        if attested_episode_ids != set(lesson.supporting_episode_ids):
            raise ValueError(
                "research tool lesson support does not equal attested episode lineage"
            )
    projection = resolve_protected_attestation(
        authority_context,
        projection_attestation_id,
        purpose=AttestationPurpose.TOOL_PROJECTION,
        subject_hash=tool.artifact_hash,
        required_artifact_ids=(projection_artifact_id,) if projection_artifact_id else (),
        required_artifact_hashes=(
            tool.artifact_hash,
            lesson.artifact_hash,
            lesson.authority_subject_hash or "",
        ) + tuple(
            episodes[item].artifact_hash for item in lesson.supporting_episode_ids
        ),
    )
    if not projection.valid:
        raise ValueError(
            "research tool projection requires exact content attestation: "
            + ", ".join(projection.reasons)
        )
    return tool


def research_tool_content_bytes(tool: ResearchTool) -> bytes:
    return canonical_json_bytes({
        "tool_id": tool.tool_id,
        "name": tool.name,
        "kind": tool.kind,
        "abstraction": tool.abstraction,
        "source_atom_id": tool.source_atom_id,
        "source_candidate_id": tool.source_candidate_id,
        "source_result_ids": list(tool.source_result_ids),
        "source_context_hash": tool.source_context_hash,
        "authority": tool.authority.value,
        "preconditions": list(tool.preconditions),
        "structural_signature": list(tool.structural_signature),
        "operation": tool.operation,
        "guaranteed_effects": list(tool.guaranteed_effects),
        "non_guarantees": list(tool.non_guarantees),
        "validation_obligations": list(tool.validation_obligations),
        "evidence_pointers": list(tool.evidence_pointers),
        "known_failure_ids": list(tool.known_failure_ids),
        "successful_reuse_ids": list(tool.successful_reuse_ids),
        "proof_backing": list(tool.proof_backing),
    })
