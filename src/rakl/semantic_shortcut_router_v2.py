from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from .semantic_shortcut import (
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationMemory,
    ObstructionTransformationReview,
    RouteSearchStatus,
    ShortcutMode,
    ShortcutReviewReport,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationCompositionWitness,
    ExhaustionWitness,
    MissingTransformationSpecification,
    build_transformation_memory,
    discover_shortcut_candidates,
    find_transformation_episode,
    validate_transformation_memory,
)
from .semantic_shortcut_router import (
    ShortcutResolution,
    _audit,
    _review,
    resolve_obstruction_transformation_route,
)


_CONCLUSIVE_REJECTION_REASONS = frozenset(
    {
        "mapping_has_unrepaired_source_preconditions",
    }
)


@dataclass(frozen=True)
class CandidateRejectionCertificate:
    """Content-bound evidence that one candidate was conclusively rejected.

    This certificate is routing evidence only.  It is minted from the existing
    canonical shortcut audit, never from a caller-supplied rejection string.  The
    current v1 schema recognizes only a deliberately narrow conclusive class:
    explicit unrepaired source preconditions in an otherwise auditable mapping.
    """

    certificate_id: str
    mode: ShortcutMode
    candidate_episode_id: str
    candidate_revision_hash: str
    target_atom_id: str
    target_context_hash: str
    research_memory_review_hash: str
    target_obstruction_id: str
    input_memory_snapshot_hash: str
    output_memory_snapshot_hash: str
    candidate_review_hash: str
    audit_reasons: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class TypedShortcutResolution:
    """A shortcut resolution plus immutable negative-history certificates."""

    resolution: ShortcutResolution
    parent_memory_snapshot_hash: str
    residual_memory_snapshot_hash: str
    rejection_certificates: Tuple[CandidateRejectionCertificate, ...] = ()

    @property
    def selected_mode(self) -> ShortcutMode:
        return self.resolution.selected_mode

    @property
    def report(self) -> ShortcutReviewReport:
        return self.resolution.report

    @property
    def review(self) -> ObstructionTransformationReview:
        return self.resolution.review

    @property
    def considered_modes(self) -> Tuple[ShortcutMode, ...]:
        rejected = tuple(certificate.mode for certificate in self.rejection_certificates)
        return rejected + self.resolution.considered_modes

    @property
    def candidate_route_ready(self) -> bool:
        return self.resolution.candidate_route_ready



def _certificate_id(
    *,
    review: ObstructionTransformationReview,
    mode: ShortcutMode,
    episode_id: str,
) -> str:
    payload = f"{review.artifact_hash}|{mode.value}|{episode_id}".encode("utf-8")
    return "RJ-" + hashlib.sha256(payload).hexdigest()[:20]



def _certificate_hash(
    *,
    certificate_id: str,
    mode: ShortcutMode,
    candidate_episode_id: str,
    candidate_revision_hash: str,
    target_atom_id: str,
    target_context_hash: str,
    research_memory_review_hash: str,
    target_obstruction_id: str,
    input_memory_snapshot_hash: str,
    output_memory_snapshot_hash: str,
    candidate_review_hash: str,
    audit_reasons: Tuple[str, ...],
    evidence_pointers: Tuple[str, ...],
) -> str:
    payload = {
        "certificate_id": certificate_id,
        "mode": mode.value,
        "candidate_episode_id": candidate_episode_id,
        "candidate_revision_hash": candidate_revision_hash,
        "target_atom_id": target_atom_id,
        "target_context_hash": target_context_hash,
        "research_memory_review_hash": research_memory_review_hash,
        "target_obstruction_id": target_obstruction_id,
        "input_memory_snapshot_hash": input_memory_snapshot_hash,
        "output_memory_snapshot_hash": output_memory_snapshot_hash,
        "candidate_review_hash": candidate_review_hash,
        "audit_reasons": list(audit_reasons),
        "evidence_pointers": list(evidence_pointers),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()



def _residual_memory(
    memory: ObstructionTransformationMemory,
    *,
    rejected_episode_id: str,
    certificate_id: str,
) -> ObstructionTransformationMemory:
    remaining = tuple(
        episode
        for episode in memory.episodes
        if episode.episode_id != rejected_episode_id
    )
    if len(remaining) == len(memory.episodes):
        raise ValueError("rejected episode is not present in the input memory")
    return build_transformation_memory(
        memory_id=memory.memory_id,
        source_universe=memory.source_universe,
        episodes=remaining,
        evidence_pointers=memory.evidence_pointers + (f"rejection:{certificate_id}",),
    )



def _conclusive_rejection(report: ShortcutReviewReport) -> bool:
    reasons = tuple(sorted(set(report.reasons)))
    return bool(
        report.verdict is ShortcutReviewVerdict.FAIL
        and reasons
        and set(reasons).issubset(_CONCLUSIVE_REJECTION_REASONS)
    )



def _issue_candidate_rejection_certificate(
    *,
    mode: ShortcutMode,
    review: ObstructionTransformationReview,
    report: ShortcutReviewReport,
    episode: ObstructionTransformationEpisode,
    memory: ObstructionTransformationMemory,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
) -> tuple[CandidateRejectionCertificate, ObstructionTransformationMemory] | None:
    if mode not in {ShortcutMode.SEARCH, ShortcutMode.JUMP}:
        return None
    if not _conclusive_rejection(report):
        return None
    if review.selected_mode is not mode:
        return None
    if tuple(review.selected_episode_ids) != (episode.episode_id,):
        return None
    if review.target_atom_id != atom_id or review.target_context_hash != context_hash:
        return None
    if review.research_memory_review_hash != research_memory_review_hash:
        return None
    if review.episode_memory_snapshot_hash != memory.snapshot_hash:
        return None
    if review.obstruction.obstruction_id == "":
        return None
    current = find_transformation_episode(memory, episode.episode_id)
    if current is None or current.artifact_hash != episode.artifact_hash:
        return None

    certificate_id = _certificate_id(
        review=review,
        mode=mode,
        episode_id=episode.episode_id,
    )
    residual = _residual_memory(
        memory,
        rejected_episode_id=episode.episode_id,
        certificate_id=certificate_id,
    )
    witness_evidence = tuple(
        pointer
        for witness in review.direct_mapping_witnesses + review.jump_mapping_witnesses
        for pointer in witness.evidence_pointers
    )
    evidence = tuple(
        dict.fromkeys(
            review.evidence_pointers + episode.evidence_pointers + witness_evidence
        )
    )
    audit_reasons = tuple(sorted(set(report.reasons)))
    artifact_hash = _certificate_hash(
        certificate_id=certificate_id,
        mode=mode,
        candidate_episode_id=episode.episode_id,
        candidate_revision_hash=episode.artifact_hash,
        target_atom_id=atom_id,
        target_context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        target_obstruction_id=review.obstruction.obstruction_id,
        input_memory_snapshot_hash=memory.snapshot_hash,
        output_memory_snapshot_hash=residual.snapshot_hash,
        candidate_review_hash=review.artifact_hash,
        audit_reasons=audit_reasons,
        evidence_pointers=evidence,
    )
    certificate = CandidateRejectionCertificate(
        certificate_id=certificate_id,
        mode=mode,
        candidate_episode_id=episode.episode_id,
        candidate_revision_hash=episode.artifact_hash,
        target_atom_id=atom_id,
        target_context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        target_obstruction_id=review.obstruction.obstruction_id,
        input_memory_snapshot_hash=memory.snapshot_hash,
        output_memory_snapshot_hash=residual.snapshot_hash,
        candidate_review_hash=review.artifact_hash,
        audit_reasons=audit_reasons,
        evidence_pointers=evidence,
        artifact_hash=artifact_hash,
    )
    if validate_candidate_rejection_certificate(
        certificate,
        memory=memory,
        obstruction=review.obstruction,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
    ):
        raise AssertionError("internally minted rejection certificate failed validation")
    return certificate, residual



def validate_candidate_rejection_certificate(
    certificate: CandidateRejectionCertificate,
    *,
    memory: ObstructionTransformationMemory,
    obstruction: ObstructionFingerprint,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
) -> Tuple[str, ...]:
    """Validate a certificate against the exact current routing subject.

    Validation is intentionally reusable by tests, receipts, and future replay code.
    The production v2 resolver never trusts caller-supplied certificates; it mints
    them from current canonical audit failures and validates them immediately.
    """

    reasons: list[str] = []
    memory_reasons = validate_transformation_memory(memory)
    if memory_reasons:
        reasons.append("rejection_input_memory_invalid")
    if certificate.mode not in {ShortcutMode.SEARCH, ShortcutMode.JUMP}:
        reasons.append("rejection_mode_not_supported")
    if certificate.input_memory_snapshot_hash != memory.snapshot_hash:
        reasons.append("rejection_input_memory_snapshot_mismatch")
    if certificate.target_obstruction_id != obstruction.obstruction_id:
        reasons.append("rejection_target_obstruction_mismatch")
    if certificate.target_atom_id != atom_id:
        reasons.append("rejection_target_atom_mismatch")
    if certificate.target_context_hash != context_hash:
        reasons.append("rejection_target_context_mismatch")
    if certificate.research_memory_review_hash != research_memory_review_hash:
        reasons.append("rejection_research_memory_review_mismatch")
    if not certificate.candidate_review_hash:
        reasons.append("rejection_candidate_review_hash_missing")
    if not certificate.evidence_pointers or any(
        not pointer for pointer in certificate.evidence_pointers
    ):
        reasons.append("rejection_evidence_missing")
    if not certificate.audit_reasons or not set(certificate.audit_reasons).issubset(
        _CONCLUSIVE_REJECTION_REASONS
    ):
        reasons.append("rejection_reason_not_conclusive")

    episode = find_transformation_episode(memory, certificate.candidate_episode_id)
    if episode is None:
        reasons.append("rejection_candidate_not_in_bound_memory")
    elif episode.artifact_hash != certificate.candidate_revision_hash:
        reasons.append("rejection_candidate_revision_mismatch")

    try:
        residual = _residual_memory(
            memory,
            rejected_episode_id=certificate.candidate_episode_id,
            certificate_id=certificate.certificate_id,
        )
    except ValueError:
        residual = None
    if residual is None or residual.snapshot_hash != certificate.output_memory_snapshot_hash:
        reasons.append("rejection_output_memory_snapshot_mismatch")

    expected = _certificate_hash(
        certificate_id=certificate.certificate_id,
        mode=certificate.mode,
        candidate_episode_id=certificate.candidate_episode_id,
        candidate_revision_hash=certificate.candidate_revision_hash,
        target_atom_id=certificate.target_atom_id,
        target_context_hash=certificate.target_context_hash,
        research_memory_review_hash=certificate.research_memory_review_hash,
        target_obstruction_id=certificate.target_obstruction_id,
        input_memory_snapshot_hash=certificate.input_memory_snapshot_hash,
        output_memory_snapshot_hash=certificate.output_memory_snapshot_hash,
        candidate_review_hash=certificate.candidate_review_hash,
        audit_reasons=certificate.audit_reasons,
        evidence_pointers=certificate.evidence_pointers,
    )
    if certificate.artifact_hash != expected:
        reasons.append("rejection_artifact_hash_mismatch")
    return tuple(reasons)



def validate_candidate_rejection_chain(
    certificates: Tuple[CandidateRejectionCertificate, ...],
    *,
    memory: ObstructionTransformationMemory,
    obstruction: ObstructionFingerprint,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
) -> Tuple[str, ...]:
    """Replay a rejection chain from its original immutable memory snapshot."""

    working = memory
    reasons: list[str] = []
    for index, certificate in enumerate(certificates):
        certificate_reasons = validate_candidate_rejection_certificate(
            certificate,
            memory=working,
            obstruction=obstruction,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
        )
        reasons.extend(
            f"rejection_chain_{index}:{reason}" for reason in certificate_reasons
        )
        if certificate_reasons:
            break
        working = _residual_memory(
            working,
            rejected_episode_id=certificate.candidate_episode_id,
            certificate_id=certificate.certificate_id,
        )
    return tuple(reasons)



def _typed_result(
    resolution: ShortcutResolution,
    *,
    parent_memory_snapshot_hash: str,
    residual_memory_snapshot_hash: str,
    certificates: list[CandidateRejectionCertificate],
) -> TypedShortcutResolution:
    return TypedShortcutResolution(
        resolution=resolution,
        parent_memory_snapshot_hash=parent_memory_snapshot_hash,
        residual_memory_snapshot_hash=residual_memory_snapshot_hash,
        rejection_certificates=tuple(certificates),
    )



def _candidate_review(
    *,
    mode: ShortcutMode,
    review_id: str,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    obstruction: ObstructionFingerprint,
    memory: ObstructionTransformationMemory,
    evidence_pointers: Tuple[str, ...],
    candidate_ids: Tuple[str, ...],
    episode_id: str,
    witness: StructuralMappingWitness,
) -> tuple[ObstructionTransformationReview, ShortcutReviewReport]:
    if mode is ShortcutMode.SEARCH:
        review = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=memory,
            obstruction=obstruction,
            mode=mode,
            direct_search_status=RouteSearchStatus.MATCHES_FOUND,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
            direct_candidate_episode_ids=candidate_ids,
            direct_mapping_witnesses=(witness,),
            selected_episode_ids=(episode_id,),
        )
    elif mode is ShortcutMode.JUMP:
        review = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=memory,
            obstruction=obstruction,
            mode=mode,
            direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            jump_search_status=RouteSearchStatus.MATCHES_FOUND,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
            jump_mapping_witnesses=(witness,),
            selected_episode_ids=(episode_id,),
        )
    else:
        raise ValueError("candidate review supports SEARCH/JUMP only")
    report = _audit(
        review,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=memory,
    )
    return review, report



def resolve_obstruction_transformation_route_with_rejections(
    *,
    review_id: str,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    obstruction: ObstructionFingerprint,
    transformation_memory: ObstructionTransformationMemory,
    evidence_pointers: Tuple[str, ...],
    direct_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = (),
    jump_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = (),
    glue_witness: TransformationCompositionWitness | None = None,
    exhaustion_witness: ExhaustionWitness | None = None,
    missing_transformation_specification: MissingTransformationSpecification | None = None,
) -> TypedShortcutResolution:
    """Resolve with narrowly certified fallthrough after conclusive candidate failure.

    The original memory object is never mutated.  Each conclusive rejection creates
    a certificate and an ephemeral residual memory view; all later canonical audits
    run against that derived view.  A PASS always wins immediately.  Missing witness,
    CANNOT_CHECK, or any FAIL outside the conclusive allowlist remains fail-closed.
    """

    parent_snapshot = transformation_memory.snapshot_hash
    if validate_transformation_memory(transformation_memory):
        base = resolve_obstruction_transformation_route(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            obstruction=obstruction,
            transformation_memory=transformation_memory,
            evidence_pointers=evidence_pointers,
            direct_mapping_witnesses=direct_mapping_witnesses,
            jump_mapping_witnesses=jump_mapping_witnesses,
            glue_witness=glue_witness,
            exhaustion_witness=exhaustion_witness,
            missing_transformation_specification=missing_transformation_specification,
        )
        return _typed_result(
            base,
            parent_memory_snapshot_hash=parent_snapshot,
            residual_memory_snapshot_hash=transformation_memory.snapshot_hash,
            certificates=[],
        )

    working = transformation_memory
    certificates: list[CandidateRejectionCertificate] = []
    direct_by_episode = {witness.episode_id: witness for witness in direct_mapping_witnesses}
    jump_by_episode = {witness.episode_id: witness for witness in jump_mapping_witnesses}

    for mode in (ShortcutMode.SEARCH, ShortcutMode.JUMP):
        while True:
            candidates = discover_shortcut_candidates(obstruction, working)
            matches = candidates.direct_matches if mode is ShortcutMode.SEARCH else candidates.jump_matches
            ids = tuple(match.episode_id for match in matches)
            if not ids:
                break

            audits: list[
                tuple[
                    str,
                    ObstructionTransformationEpisode,
                    ObstructionTransformationReview,
                    ShortcutReviewReport,
                ]
            ] = []
            witness_map = direct_by_episode if mode is ShortcutMode.SEARCH else jump_by_episode
            for episode_id in ids:
                witness = witness_map.get(episode_id)
                if witness is None:
                    continue
                episode = find_transformation_episode(working, episode_id)
                if episode is None:
                    continue
                review, report = _candidate_review(
                    mode=mode,
                    review_id=review_id,
                    atom_id=atom_id,
                    context_hash=context_hash,
                    research_memory_review_hash=research_memory_review_hash,
                    obstruction=obstruction,
                    memory=working,
                    evidence_pointers=evidence_pointers,
                    candidate_ids=ids,
                    episode_id=episode_id,
                    witness=witness,
                )
                if report.verdict is ShortcutReviewVerdict.PASS:
                    resolution = ShortcutResolution(
                        review=review,
                        report=report,
                        considered_modes=(mode,),
                    )
                    return _typed_result(
                        resolution,
                        parent_memory_snapshot_hash=parent_snapshot,
                        residual_memory_snapshot_hash=working.snapshot_hash,
                        certificates=certificates,
                    )
                audits.append((episode_id, episode, review, report))

            conclusive = next(
                (row for row in audits if _conclusive_rejection(row[3])),
                None,
            )
            if conclusive is None:
                base = resolve_obstruction_transformation_route(
                    review_id=review_id,
                    atom_id=atom_id,
                    context_hash=context_hash,
                    research_memory_review_hash=research_memory_review_hash,
                    obstruction=obstruction,
                    transformation_memory=working,
                    evidence_pointers=evidence_pointers,
                    direct_mapping_witnesses=direct_mapping_witnesses,
                    jump_mapping_witnesses=jump_mapping_witnesses,
                    glue_witness=glue_witness,
                    exhaustion_witness=exhaustion_witness,
                    missing_transformation_specification=missing_transformation_specification,
                )
                return _typed_result(
                    base,
                    parent_memory_snapshot_hash=parent_snapshot,
                    residual_memory_snapshot_hash=working.snapshot_hash,
                    certificates=certificates,
                )

            _, episode, review, report = conclusive
            issued = _issue_candidate_rejection_certificate(
                mode=mode,
                review=review,
                report=report,
                episode=episode,
                memory=working,
                atom_id=atom_id,
                context_hash=context_hash,
                research_memory_review_hash=research_memory_review_hash,
            )
            if issued is None:
                base = resolve_obstruction_transformation_route(
                    review_id=review_id,
                    atom_id=atom_id,
                    context_hash=context_hash,
                    research_memory_review_hash=research_memory_review_hash,
                    obstruction=obstruction,
                    transformation_memory=working,
                    evidence_pointers=evidence_pointers,
                    direct_mapping_witnesses=direct_mapping_witnesses,
                    jump_mapping_witnesses=jump_mapping_witnesses,
                    glue_witness=glue_witness,
                    exhaustion_witness=exhaustion_witness,
                    missing_transformation_specification=missing_transformation_specification,
                )
                return _typed_result(
                    base,
                    parent_memory_snapshot_hash=parent_snapshot,
                    residual_memory_snapshot_hash=working.snapshot_hash,
                    certificates=certificates,
                )
            certificate, working = issued
            certificates.append(certificate)

    base = resolve_obstruction_transformation_route(
        review_id=review_id,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        obstruction=obstruction,
        transformation_memory=working,
        evidence_pointers=evidence_pointers,
        direct_mapping_witnesses=direct_mapping_witnesses,
        jump_mapping_witnesses=jump_mapping_witnesses,
        glue_witness=glue_witness,
        exhaustion_witness=exhaustion_witness,
        missing_transformation_specification=missing_transformation_specification,
    )
    return _typed_result(
        base,
        parent_memory_snapshot_hash=parent_snapshot,
        residual_memory_snapshot_hash=working.snapshot_hash,
        certificates=certificates,
    )
