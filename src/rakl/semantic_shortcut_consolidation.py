from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from enum import Enum
from typing import Tuple

from .experience_substrate import (
    EpisodeAdmissionReceipt,
    EpisodeOutcome,
    InventoryAdmissionVerdict,
    TaskEpisode,
    resolve_inventory_admission,
)
from .semantic_shortcut import (
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationMemory,
    ObstructionTransformationReview,
    ShortcutMode,
    ShortcutReviewReport,
    ShortcutReviewVerdict,
    TransformationEpisodeAuthority,
    add_transformation_episode,
    audit_obstruction_transformation_review,
    validate_transformation_episode,
    validate_transformation_memory,
)
from .v3_authority import canonical_json_bytes


class StructuralConsolidationVerdict(str, Enum):
    VALIDATED_TARGET_CONSOLIDATED = "VALIDATED_TARGET_CONSOLIDATED"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class StructuralConsolidationReport:
    verdict: StructuralConsolidationVerdict
    reasons: Tuple[str, ...]
    candidate_episode_id: str
    target_task_episode_id: str
    route_review_id: str
    input_memory_snapshot_hash: str
    candidate_content_hash: str
    promoted_episode_id: str | None = None
    promoted_artifact_hash: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_research_tool_promotion(self) -> bool:
        return False


@dataclass(frozen=True)
class StructuralConsolidationOutcome:
    memory: ObstructionTransformationMemory
    report: StructuralConsolidationReport
    promoted_episode: ObstructionTransformationEpisode | None = None


def _fingerprint_payload(fingerprint: ObstructionFingerprint) -> dict[str, object]:
    return {
        "obstruction_id": fingerprint.obstruction_id,
        "domain": fingerprint.domain,
        "roles": list(fingerprint.roles),
        "relations": list(fingerprint.relations),
        "constraints": list(fingerprint.constraints),
        "failure_mechanisms": list(fingerprint.failure_mechanisms),
        "invariants_to_preserve": list(fingerprint.invariants_to_preserve),
        "desired_transition": list(fingerprint.desired_transition),
        "forbidden_losses": list(fingerprint.forbidden_losses),
    }


def transformation_episode_content_hash(
    episode: ObstructionTransformationEpisode,
) -> str:
    """Canonical content identity for post-success structural consolidation.

    Historical semantic-shortcut episode hashes are deliberately not re-keyed.
    This stronger v1 consolidation path requires its own newly proposed and
    promoted episodes to use an exact hash over every semantic field except the
    hash field itself.
    """

    payload = {
        "episode_id": episode.episode_id,
        "source_domain": episode.source_domain,
        "source_context": episode.source_context,
        "source_obstruction": _fingerprint_payload(episode.source_obstruction),
        "transformation_name": episode.transformation_name,
        "operation": episode.operation,
        "preconditions": list(episode.preconditions),
        "resulting_relations": list(episode.resulting_relations),
        "preserved_invariants": list(episode.preserved_invariants),
        "relaxed_or_broken_constraints": list(episode.relaxed_or_broken_constraints),
        "known_breakpoints": list(episode.known_breakpoints),
        "evidence_pointers": list(episode.evidence_pointers),
        "authority": episode.authority.value,
        "lineage_ids": list(episode.lineage_ids),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _report(
    *,
    verdict: StructuralConsolidationVerdict,
    reasons: Tuple[str, ...],
    memory: ObstructionTransformationMemory,
    candidate: ObstructionTransformationEpisode,
    target_episode: TaskEpisode,
    review: ObstructionTransformationReview,
    promoted_episode: ObstructionTransformationEpisode | None = None,
) -> StructuralConsolidationReport:
    return StructuralConsolidationReport(
        verdict=verdict,
        reasons=reasons,
        candidate_episode_id=candidate.episode_id,
        target_task_episode_id=target_episode.episode_id,
        route_review_id=review.review_id,
        input_memory_snapshot_hash=memory.snapshot_hash,
        candidate_content_hash=transformation_episode_content_hash(candidate),
        promoted_episode_id=(
            promoted_episode.episode_id if promoted_episode is not None else None
        ),
        promoted_artifact_hash=(
            promoted_episode.artifact_hash if promoted_episode is not None else None
        ),
    )


def _required_lineage(review: ObstructionTransformationReview, target_episode: TaskEpisode) -> Tuple[str, ...]:
    required = [target_episode.episode_id, review.review_id]
    required.extend(review.selected_episode_ids)
    if (
        review.selected_mode is ShortcutMode.LIFT
        and review.missing_transformation_specification is not None
    ):
        required.append(review.missing_transformation_specification.spec_id)
    return tuple(dict.fromkeys(required))


def assess_validated_target_transformation(
    *,
    memory: ObstructionTransformationMemory,
    candidate: ObstructionTransformationEpisode,
    review: ObstructionTransformationReview,
    supplied_route_report: ShortcutReviewReport,
    target_episode: TaskEpisode,
    target_admission_receipt: EpisodeAdmissionReceipt | None,
) -> StructuralConsolidationReport:
    """Assess whether one proposal-only target transformation may enter memory.

    The function deliberately re-audits the route rather than trusting a caller-
    supplied PASS report.  The target execution must also be a canonically
    admitted successful TaskEpisode.  Passing this gate only earns local
    structural-memory authority; it never promotes a scientific claim or a
    ResearchTool.
    """

    memory_reasons = validate_transformation_memory(memory)
    if memory_reasons:
        return _report(
            verdict=StructuralConsolidationVerdict.CANNOT_CHECK,
            reasons=tuple(f"memory:{reason}" for reason in memory_reasons),
            memory=memory,
            candidate=candidate,
            target_episode=target_episode,
            review=review,
        )

    candidate_reasons = validate_transformation_episode(candidate)
    if candidate_reasons:
        return _report(
            verdict=StructuralConsolidationVerdict.REJECT,
            reasons=tuple(f"candidate:{reason}" for reason in candidate_reasons),
            memory=memory,
            candidate=candidate,
            target_episode=target_episode,
            review=review,
        )

    reasons: list[str] = []
    if candidate.authority is not TransformationEpisodeAuthority.PROPOSAL_ONLY:
        reasons.append("candidate_authority_must_be_proposal_only")
    expected_candidate_hash = transformation_episode_content_hash(candidate)
    if candidate.artifact_hash != expected_candidate_hash:
        reasons.append("candidate_content_hash_mismatch")

    exact_route_report = audit_obstruction_transformation_review(
        review,
        atom_id=review.target_atom_id,
        context_hash=review.target_context_hash,
        research_memory_review_hash=review.research_memory_review_hash,
        transformation_memory=memory,
    )
    if supplied_route_report != exact_route_report:
        reasons.append("supplied_route_report_does_not_match_exact_reaudit")
    if exact_route_report.verdict is not ShortcutReviewVerdict.PASS:
        reasons.append("route_review_not_pass_after_exact_reaudit")
    if not exact_route_report.candidate_route_ready:
        reasons.append("route_review_not_candidate_ready")
    if exact_route_report.selected_mode is not review.selected_mode:
        reasons.append("route_report_mode_mismatch")

    admission = resolve_inventory_admission(
        target_episode,
        target_admission_receipt,
        treat_as_canonical=True,
    )
    if admission.verdict is not InventoryAdmissionVerdict.CANONICAL_INVENTORY_ADMITTED:
        reasons.append("target_episode_not_canonically_admitted")
        reasons.extend(f"target_admission:{item}" for item in admission.reasons)
    if target_episode.outcome is not EpisodeOutcome.SUCCESS:
        reasons.append(f"target_episode_not_success:{target_episode.outcome.value}")
    if target_episode.atom_id != review.target_atom_id:
        reasons.append("target_episode_atom_mismatch")
    if target_episode.context_hash != review.target_context_hash:
        reasons.append("target_episode_context_mismatch")

    if candidate.source_obstruction != review.obstruction:
        reasons.append("candidate_obstruction_does_not_equal_review_target")
    if candidate.source_domain != review.obstruction.domain:
        reasons.append("candidate_source_domain_does_not_equal_target_domain")
    if candidate.source_domain not in set(memory.source_universe):
        reasons.append("candidate_source_domain_outside_bound_memory_universe")

    desired = set(review.obstruction.desired_transition)
    if not desired.issubset(set(candidate.resulting_relations)):
        reasons.append("candidate_does_not_record_full_target_transition")
    invariants = set(review.obstruction.invariants_to_preserve)
    if not invariants.issubset(set(candidate.preserved_invariants)):
        reasons.append("candidate_does_not_record_required_invariants")
    forbidden = set(review.obstruction.forbidden_losses)
    if forbidden & set(candidate.relaxed_or_broken_constraints):
        reasons.append("candidate_records_forbidden_target_loss")

    required_lineage = set(_required_lineage(review, target_episode))
    if not required_lineage.issubset(set(candidate.lineage_ids)):
        reasons.append("candidate_lineage_missing_target_or_route_sources")
    if review.selected_mode is ShortcutMode.LIFT:
        if review.missing_transformation_specification is None:
            reasons.append("lift_candidate_missing_bound_specification")
        elif review.missing_transformation_specification.spec_id not in set(candidate.lineage_ids):
            reasons.append("lift_candidate_missing_specification_lineage")

    if reasons:
        return _report(
            verdict=StructuralConsolidationVerdict.REJECT,
            reasons=tuple(dict.fromkeys(reasons)),
            memory=memory,
            candidate=candidate,
            target_episode=target_episode,
            review=review,
        )

    return _report(
        verdict=StructuralConsolidationVerdict.VALIDATED_TARGET_CONSOLIDATED,
        reasons=(
            "exact_semantic_shortcut_route_reaudited",
            "canonically_admitted_target_episode_succeeded",
            "proposal_candidate_matches_target_structure_and_lineage",
            "eligible_for_verified_local_structural_memory_only",
        ),
        memory=memory,
        candidate=candidate,
        target_episode=target_episode,
        review=review,
    )


def consolidate_validated_target_transformation(
    *,
    memory: ObstructionTransformationMemory,
    candidate: ObstructionTransformationEpisode,
    review: ObstructionTransformationReview,
    supplied_route_report: ShortcutReviewReport,
    target_episode: TaskEpisode,
    target_admission_receipt: EpisodeAdmissionReceipt | None,
    promoted_episode_id: str,
) -> StructuralConsolidationOutcome:
    """Append one target-validated transformation as VERIFIED_LOCAL experience."""

    report = assess_validated_target_transformation(
        memory=memory,
        candidate=candidate,
        review=review,
        supplied_route_report=supplied_route_report,
        target_episode=target_episode,
        target_admission_receipt=target_admission_receipt,
    )
    if report.verdict is not StructuralConsolidationVerdict.VALIDATED_TARGET_CONSOLIDATED:
        return StructuralConsolidationOutcome(memory=memory, report=report)

    if not promoted_episode_id:
        rejected = replace(
            report,
            verdict=StructuralConsolidationVerdict.REJECT,
            reasons=("promoted_episode_id_missing",),
        )
        return StructuralConsolidationOutcome(memory=memory, report=rejected)
    if promoted_episode_id == candidate.episode_id:
        rejected = replace(
            report,
            verdict=StructuralConsolidationVerdict.REJECT,
            reasons=("promotion_must_create_new_episode_version",),
        )
        return StructuralConsolidationOutcome(memory=memory, report=rejected)

    lineage = tuple(
        dict.fromkeys(
            candidate.lineage_ids
            + (candidate.episode_id, target_episode.episode_id, review.review_id)
        )
    )
    evidence = tuple(
        dict.fromkeys(
            candidate.evidence_pointers
            + target_episode.evidence_pointers
            + review.evidence_pointers
            + (
                f"target_episode:{target_episode.episode_id}",
                f"route_review:{review.review_id}",
                f"admission_receipt:{target_admission_receipt.receipt_id}",
            )
        )
    )
    draft = replace(
        candidate,
        episode_id=promoted_episode_id,
        authority=TransformationEpisodeAuthority.VERIFIED_LOCAL,
        lineage_ids=lineage,
        evidence_pointers=evidence,
        artifact_hash="",
    )
    promoted = replace(draft, artifact_hash=transformation_episode_content_hash(draft))
    promoted_reasons = validate_transformation_episode(promoted)
    if promoted_reasons:
        rejected = replace(
            report,
            verdict=StructuralConsolidationVerdict.CANNOT_CHECK,
            reasons=tuple(f"promoted:{item}" for item in promoted_reasons),
        )
        return StructuralConsolidationOutcome(memory=memory, report=rejected)

    updated = add_transformation_episode(memory, promoted)
    final_report = replace(
        report,
        promoted_episode_id=promoted.episode_id,
        promoted_artifact_hash=promoted.artifact_hash,
    )
    return StructuralConsolidationOutcome(
        memory=updated,
        report=final_report,
        promoted_episode=promoted,
    )
