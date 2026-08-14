from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from .semantic_shortcut import (
    ExhaustionWitness,
    MissingTransformationSpecification,
    ObstructionFingerprint,
    ObstructionTransformationMemory,
    ObstructionTransformationReview,
    RouteSearchStatus,
    ShortcutMode,
    ShortcutReviewReport,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationCompositionWitness,
    discover_shortcut_candidates,
    find_transformation_episode,
    validate_transformation_memory,
)
from .semantic_shortcut_router import ShortcutResolution, _audit, _review
from .semantic_shortcut_router_v2 import (
    CandidateRejectionCertificate,
    TypedShortcutResolution,
    _residual_memory,
    resolve_obstruction_transformation_route_with_rejections,
)


_CONCLUSIVE_COMPOSITION_REJECTION_REASONS = frozenset(
    {
        "mapping_has_unrepaired_source_preconditions",
    }
)


@dataclass(frozen=True)
class CompositionRejectionCertificate:
    """Content-bound evidence that one exact GLUE composition was rejected.

    A rejected composition does not delete its component episodes: those episodes
    may still participate in other compositions.  The certificate therefore binds
    the exact candidate set, order, component revisions, target, memory snapshot,
    failed review, canonical audit reasons, and semantic content of the supplied
    composition witness.
    """

    certificate_id: str
    candidate_key: str
    composition_id: str
    ordered_episode_ids: Tuple[str, ...]
    episode_revision_hashes: Tuple[Tuple[str, str], ...]
    operation_order: Tuple[str, ...]
    target_atom_id: str
    target_context_hash: str
    research_memory_review_hash: str
    target_obstruction_id: str
    input_memory_snapshot_hash: str
    composition_witness_artifact_hash: str
    composition_witness_content_hash: str
    candidate_review_hash: str
    audit_reasons: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class TypedShortcutResolutionV3:
    """Production route resolution with candidate and composition negative history."""

    resolution: ShortcutResolution
    parent_memory_snapshot_hash: str
    residual_memory_snapshot_hash: str
    candidate_rejection_certificates: Tuple[CandidateRejectionCertificate, ...] = ()
    composition_rejection_certificates: Tuple[CompositionRejectionCertificate, ...] = ()

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
    def candidate_route_ready(self) -> bool:
        return self.resolution.candidate_route_ready

    @property
    def rejection_certificates(self) -> Tuple[CandidateRejectionCertificate, ...]:
        """Compatibility alias for the v2 SEARCH/JUMP certificate sequence."""

        return self.candidate_rejection_certificates

    @property
    def considered_modes(self) -> Tuple[ShortcutMode, ...]:
        ordered: list[ShortcutMode] = []
        for certificate in self.candidate_rejection_certificates:
            if certificate.mode not in ordered:
                ordered.append(certificate.mode)
        if self.composition_rejection_certificates and ShortcutMode.GLUE not in ordered:
            ordered.append(ShortcutMode.GLUE)
        for mode in self.resolution.considered_modes:
            if mode not in ordered:
                ordered.append(mode)
        return tuple(ordered)


def _composition_candidate_key(episode_ids: Tuple[str, ...]) -> str:
    return "+".join(sorted(episode_ids))


def _composition_witness_content_hash(
    witness: TransformationCompositionWitness,
) -> str:
    payload = {
        "composition_id": witness.composition_id,
        "target_obstruction_id": witness.target_obstruction_id,
        "episode_ids": list(witness.episode_ids),
        "operation_order": list(witness.operation_order),
        "interface_obligations": list(witness.interface_obligations),
        "incompatibilities_checked": list(witness.incompatibilities_checked),
        "target_validation_obligations": list(witness.target_validation_obligations),
        "evidence_pointers": list(witness.evidence_pointers),
        "artifact_hash": witness.artifact_hash,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _composition_certificate_id(
    *,
    review: ObstructionTransformationReview,
    witness: TransformationCompositionWitness,
    candidate_key: str,
) -> str:
    payload = (
        f"{review.artifact_hash}|GLUE|{candidate_key}|"
        f"{witness.composition_id}|{witness.artifact_hash}"
    ).encode("utf-8")
    return "GRJ-" + hashlib.sha256(payload).hexdigest()[:20]


def _composition_certificate_hash(
    *,
    certificate_id: str,
    candidate_key: str,
    composition_id: str,
    ordered_episode_ids: Tuple[str, ...],
    episode_revision_hashes: Tuple[Tuple[str, str], ...],
    operation_order: Tuple[str, ...],
    target_atom_id: str,
    target_context_hash: str,
    research_memory_review_hash: str,
    target_obstruction_id: str,
    input_memory_snapshot_hash: str,
    composition_witness_artifact_hash: str,
    composition_witness_content_hash: str,
    candidate_review_hash: str,
    audit_reasons: Tuple[str, ...],
    evidence_pointers: Tuple[str, ...],
) -> str:
    payload = {
        "certificate_id": certificate_id,
        "candidate_key": candidate_key,
        "composition_id": composition_id,
        "ordered_episode_ids": list(ordered_episode_ids),
        "episode_revision_hashes": [list(item) for item in episode_revision_hashes],
        "operation_order": list(operation_order),
        "target_atom_id": target_atom_id,
        "target_context_hash": target_context_hash,
        "research_memory_review_hash": research_memory_review_hash,
        "target_obstruction_id": target_obstruction_id,
        "input_memory_snapshot_hash": input_memory_snapshot_hash,
        "composition_witness_artifact_hash": composition_witness_artifact_hash,
        "composition_witness_content_hash": composition_witness_content_hash,
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


def _conclusive_composition_rejection(report: ShortcutReviewReport) -> bool:
    reasons = tuple(sorted(set(report.reasons)))
    return bool(
        report.verdict is ShortcutReviewVerdict.FAIL
        and reasons
        and set(reasons).issubset(_CONCLUSIVE_COMPOSITION_REJECTION_REASONS)
    )


def _replay_candidate_residual(
    memory: ObstructionTransformationMemory,
    certificates: Tuple[CandidateRejectionCertificate, ...],
) -> ObstructionTransformationMemory:
    working = memory
    for certificate in certificates:
        working = _residual_memory(
            working,
            rejected_episode_id=certificate.candidate_episode_id,
            certificate_id=certificate.certificate_id,
        )
    return working


def _composition_review(
    *,
    review_id: str,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    obstruction: ObstructionFingerprint,
    memory: ObstructionTransformationMemory,
    evidence_pointers: Tuple[str, ...],
    witness: TransformationCompositionWitness,
    jump_mapping_witnesses: Tuple[StructuralMappingWitness, ...],
) -> tuple[ObstructionTransformationReview, ShortcutReviewReport]:
    mapping_by_episode = {
        mapping.episode_id: mapping for mapping in jump_mapping_witnesses
    }
    mappings = tuple(
        mapping_by_episode[episode_id]
        for episode_id in witness.episode_ids
        if episode_id in mapping_by_episode
    )
    review = _review(
        review_id=review_id,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=memory,
        obstruction=obstruction,
        mode=ShortcutMode.GLUE,
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        glue_search_status=RouteSearchStatus.MATCHES_FOUND,
        evidence_pointers=evidence_pointers,
        jump_mapping_witnesses=mappings,
        glue_witness=witness,
        selected_episode_ids=tuple(witness.episode_ids),
    )
    report = _audit(
        review,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=memory,
    )
    return review, report


def _issue_composition_rejection_certificate(
    *,
    review: ObstructionTransformationReview,
    report: ShortcutReviewReport,
    witness: TransformationCompositionWitness,
    memory: ObstructionTransformationMemory,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
) -> CompositionRejectionCertificate | None:
    if review.selected_mode is not ShortcutMode.GLUE:
        return None
    if not _conclusive_composition_rejection(report):
        return None
    if review.target_atom_id != atom_id or review.target_context_hash != context_hash:
        return None
    if review.research_memory_review_hash != research_memory_review_hash:
        return None
    if review.episode_memory_snapshot_hash != memory.snapshot_hash:
        return None
    if review.glue_witness != witness:
        return None
    if tuple(review.selected_episode_ids) != tuple(witness.episode_ids):
        return None

    revisions: list[tuple[str, str]] = []
    episode_evidence: list[str] = []
    for episode_id in witness.episode_ids:
        episode = find_transformation_episode(memory, episode_id)
        if episode is None:
            return None
        revisions.append((episode_id, episode.artifact_hash))
        episode_evidence.extend(episode.evidence_pointers)

    candidate_key = _composition_candidate_key(tuple(witness.episode_ids))
    candidate_keys = {
        _composition_candidate_key(tuple(items))
        for items in discover_shortcut_candidates(review.obstruction, memory).glue_episode_sets
    }
    if candidate_key not in candidate_keys:
        return None

    mapping_evidence = [
        pointer
        for mapping in review.jump_mapping_witnesses
        for pointer in mapping.evidence_pointers
    ]
    evidence = tuple(
        dict.fromkeys(
            review.evidence_pointers
            + witness.evidence_pointers
            + tuple(episode_evidence)
            + tuple(mapping_evidence)
        )
    )
    if not evidence:
        return None

    audit_reasons = tuple(sorted(set(report.reasons)))
    witness_content_hash = _composition_witness_content_hash(witness)
    certificate_id = _composition_certificate_id(
        review=review,
        witness=witness,
        candidate_key=candidate_key,
    )
    artifact_hash = _composition_certificate_hash(
        certificate_id=certificate_id,
        candidate_key=candidate_key,
        composition_id=witness.composition_id,
        ordered_episode_ids=tuple(witness.episode_ids),
        episode_revision_hashes=tuple(revisions),
        operation_order=tuple(witness.operation_order),
        target_atom_id=atom_id,
        target_context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        target_obstruction_id=review.obstruction.obstruction_id,
        input_memory_snapshot_hash=memory.snapshot_hash,
        composition_witness_artifact_hash=witness.artifact_hash,
        composition_witness_content_hash=witness_content_hash,
        candidate_review_hash=review.artifact_hash,
        audit_reasons=audit_reasons,
        evidence_pointers=evidence,
    )
    certificate = CompositionRejectionCertificate(
        certificate_id=certificate_id,
        candidate_key=candidate_key,
        composition_id=witness.composition_id,
        ordered_episode_ids=tuple(witness.episode_ids),
        episode_revision_hashes=tuple(revisions),
        operation_order=tuple(witness.operation_order),
        target_atom_id=atom_id,
        target_context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        target_obstruction_id=review.obstruction.obstruction_id,
        input_memory_snapshot_hash=memory.snapshot_hash,
        composition_witness_artifact_hash=witness.artifact_hash,
        composition_witness_content_hash=witness_content_hash,
        candidate_review_hash=review.artifact_hash,
        audit_reasons=audit_reasons,
        evidence_pointers=evidence,
        artifact_hash=artifact_hash,
    )
    if validate_composition_rejection_certificate(
        certificate,
        memory=memory,
        obstruction=review.obstruction,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        witness=witness,
    ):
        raise AssertionError("internally minted composition rejection certificate failed validation")
    return certificate


def validate_composition_rejection_certificate(
    certificate: CompositionRejectionCertificate,
    *,
    memory: ObstructionTransformationMemory,
    obstruction: ObstructionFingerprint,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    witness: TransformationCompositionWitness | None = None,
) -> Tuple[str, ...]:
    """Validate one GLUE rejection certificate against the current exact subject."""

    reasons: list[str] = []
    if validate_transformation_memory(memory):
        reasons.append("composition_rejection_input_memory_invalid")
    if certificate.input_memory_snapshot_hash != memory.snapshot_hash:
        reasons.append("composition_rejection_input_memory_snapshot_mismatch")
    if certificate.target_obstruction_id != obstruction.obstruction_id:
        reasons.append("composition_rejection_target_obstruction_mismatch")
    if certificate.target_atom_id != atom_id:
        reasons.append("composition_rejection_target_atom_mismatch")
    if certificate.target_context_hash != context_hash:
        reasons.append("composition_rejection_target_context_mismatch")
    if certificate.research_memory_review_hash != research_memory_review_hash:
        reasons.append("composition_rejection_research_memory_review_mismatch")
    if not certificate.composition_id:
        reasons.append("composition_rejection_composition_id_missing")
    if not certificate.candidate_review_hash:
        reasons.append("composition_rejection_candidate_review_hash_missing")
    if len(certificate.ordered_episode_ids) < 2 or len(
        set(certificate.ordered_episode_ids)
    ) != len(certificate.ordered_episode_ids):
        reasons.append("composition_rejection_requires_distinct_component_episodes")
    if certificate.operation_order != certificate.ordered_episode_ids:
        reasons.append("composition_rejection_operation_order_mismatch")
    expected_key = _composition_candidate_key(certificate.ordered_episode_ids)
    if certificate.candidate_key != expected_key:
        reasons.append("composition_rejection_candidate_key_mismatch")
    current_candidate_keys = {
        _composition_candidate_key(tuple(items))
        for items in discover_shortcut_candidates(obstruction, memory).glue_episode_sets
    }
    if certificate.candidate_key not in current_candidate_keys:
        reasons.append("composition_rejection_candidate_not_in_bound_memory_query")
    if not certificate.audit_reasons or not set(certificate.audit_reasons).issubset(
        _CONCLUSIVE_COMPOSITION_REJECTION_REASONS
    ):
        reasons.append("composition_rejection_reason_not_conclusive")
    if not certificate.evidence_pointers or any(
        not pointer for pointer in certificate.evidence_pointers
    ):
        reasons.append("composition_rejection_evidence_missing")

    expected_revisions: list[tuple[str, str]] = []
    for episode_id in certificate.ordered_episode_ids:
        episode = find_transformation_episode(memory, episode_id)
        if episode is None:
            reasons.append(
                f"composition_rejection_component_not_in_bound_memory:{episode_id}"
            )
            continue
        expected_revisions.append((episode_id, episode.artifact_hash))
    if tuple(expected_revisions) != certificate.episode_revision_hashes:
        reasons.append("composition_rejection_component_revision_mismatch")

    if witness is not None:
        if witness.composition_id != certificate.composition_id:
            reasons.append("composition_rejection_witness_composition_id_mismatch")
        if tuple(witness.episode_ids) != certificate.ordered_episode_ids:
            reasons.append("composition_rejection_witness_episode_order_mismatch")
        if tuple(witness.operation_order) != certificate.operation_order:
            reasons.append("composition_rejection_witness_operation_order_mismatch")
        if witness.target_obstruction_id != certificate.target_obstruction_id:
            reasons.append("composition_rejection_witness_target_mismatch")
        if witness.artifact_hash != certificate.composition_witness_artifact_hash:
            reasons.append("composition_rejection_witness_artifact_hash_mismatch")
        if (
            _composition_witness_content_hash(witness)
            != certificate.composition_witness_content_hash
        ):
            reasons.append("composition_rejection_witness_content_hash_mismatch")

    expected_hash = _composition_certificate_hash(
        certificate_id=certificate.certificate_id,
        candidate_key=certificate.candidate_key,
        composition_id=certificate.composition_id,
        ordered_episode_ids=certificate.ordered_episode_ids,
        episode_revision_hashes=certificate.episode_revision_hashes,
        operation_order=certificate.operation_order,
        target_atom_id=certificate.target_atom_id,
        target_context_hash=certificate.target_context_hash,
        research_memory_review_hash=certificate.research_memory_review_hash,
        target_obstruction_id=certificate.target_obstruction_id,
        input_memory_snapshot_hash=certificate.input_memory_snapshot_hash,
        composition_witness_artifact_hash=certificate.composition_witness_artifact_hash,
        composition_witness_content_hash=certificate.composition_witness_content_hash,
        candidate_review_hash=certificate.candidate_review_hash,
        audit_reasons=certificate.audit_reasons,
        evidence_pointers=certificate.evidence_pointers,
    )
    if certificate.artifact_hash != expected_hash:
        reasons.append("composition_rejection_artifact_hash_mismatch")
    return tuple(reasons)


def validate_composition_rejection_chain(
    certificates: Tuple[CompositionRejectionCertificate, ...],
    *,
    memory: ObstructionTransformationMemory,
    obstruction: ObstructionFingerprint,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    witnesses: Tuple[TransformationCompositionWitness, ...] = (),
) -> Tuple[str, ...]:
    """Validate all composition negatives against one immutable memory snapshot."""

    witness_by_key = {
        _composition_candidate_key(tuple(witness.episode_ids)): witness
        for witness in witnesses
    }
    reasons: list[str] = []
    seen: set[str] = set()
    for index, certificate in enumerate(certificates):
        if certificate.candidate_key in seen:
            reasons.append(
                f"composition_rejection_chain_{index}:duplicate_candidate_key"
            )
            continue
        seen.add(certificate.candidate_key)
        witness = witness_by_key.get(certificate.candidate_key)
        item_reasons = validate_composition_rejection_certificate(
            certificate,
            memory=memory,
            obstruction=obstruction,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            witness=witness,
        )
        reasons.extend(
            f"composition_rejection_chain_{index}:{reason}"
            for reason in item_reasons
        )
    return tuple(reasons)


def _wrap(
    base: TypedShortcutResolution,
    *,
    composition_certificates: Tuple[CompositionRejectionCertificate, ...] = (),
    resolution: ShortcutResolution | None = None,
) -> TypedShortcutResolutionV3:
    return TypedShortcutResolutionV3(
        resolution=resolution or base.resolution,
        parent_memory_snapshot_hash=base.parent_memory_snapshot_hash,
        residual_memory_snapshot_hash=base.residual_memory_snapshot_hash,
        candidate_rejection_certificates=base.rejection_certificates,
        composition_rejection_certificates=composition_certificates,
    )


def resolve_obstruction_transformation_route_with_composition_rejections(
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
    glue_witnesses: Tuple[TransformationCompositionWitness, ...] = (),
    exhaustion_witness: ExhaustionWitness | None = None,
    missing_transformation_specification: MissingTransformationSpecification | None = None,
) -> TypedShortcutResolutionV3:
    """Resolve SEARCH -> JUMP -> GLUE -> LIFT with typed GLUE rejection.

    SEARCH/JUMP handling is delegated unchanged to v2.  GLUE is evaluated only
    after v2 has either certified away or found no earlier candidates.  Every
    structural GLUE candidate must then PASS or receive an internally minted,
    content-bound conclusive rejection certificate before LIFT is even attempted.
    """

    base = resolve_obstruction_transformation_route_with_rejections(
        review_id=review_id,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        obstruction=obstruction,
        transformation_memory=transformation_memory,
        evidence_pointers=evidence_pointers,
        direct_mapping_witnesses=direct_mapping_witnesses,
        jump_mapping_witnesses=jump_mapping_witnesses,
        glue_witness=None,
        exhaustion_witness=exhaustion_witness,
        missing_transformation_specification=missing_transformation_specification,
    )
    if base.selected_mode is not ShortcutMode.CANNOT_CHECK:
        return _wrap(base)

    working = _replay_candidate_residual(
        transformation_memory,
        base.rejection_certificates,
    )
    candidates = discover_shortcut_candidates(obstruction, working)

    if candidates.direct_matches or candidates.jump_matches:
        return _wrap(base)

    glue_sets = tuple(candidates.glue_episode_sets)
    if not glue_sets:
        return _wrap(base)

    witness_by_key: dict[str, list[TransformationCompositionWitness]] = {}
    for witness in glue_witnesses:
        key = _composition_candidate_key(tuple(witness.episode_ids))
        witness_by_key.setdefault(key, []).append(witness)

    composition_certificates: list[CompositionRejectionCertificate] = []
    unresolved = False
    for glue_set in glue_sets:
        candidate_key = _composition_candidate_key(tuple(glue_set))
        matching = witness_by_key.get(candidate_key, [])
        if len(matching) != 1:
            unresolved = True
            continue
        witness = matching[0]
        review, report = _composition_review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            obstruction=obstruction,
            memory=working,
            evidence_pointers=evidence_pointers,
            witness=witness,
            jump_mapping_witnesses=jump_mapping_witnesses,
        )
        if report.verdict is ShortcutReviewVerdict.PASS:
            resolution = ShortcutResolution(
                review=review,
                report=report,
                considered_modes=(ShortcutMode.GLUE,),
            )
            return _wrap(
                base,
                composition_certificates=tuple(composition_certificates),
                resolution=resolution,
            )
        certificate = _issue_composition_rejection_certificate(
            review=review,
            report=report,
            witness=witness,
            memory=working,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
        )
        if certificate is None:
            unresolved = True
            continue
        composition_certificates.append(certificate)

    rejected_keys = {
        certificate.candidate_key for certificate in composition_certificates
    }
    expected_keys = {
        _composition_candidate_key(tuple(items)) for items in glue_sets
    }
    if unresolved or rejected_keys != expected_keys:
        return _wrap(
            base,
            composition_certificates=tuple(composition_certificates),
        )

    if (
        exhaustion_witness is not None
        and missing_transformation_specification is not None
    ):
        lift_review = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=working,
            obstruction=obstruction,
            mode=ShortcutMode.LIFT,
            direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
            exhaustion_witness=exhaustion_witness,
            missing_transformation_specification=missing_transformation_specification,
        )
        lift_report = _audit(
            lift_review,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=working,
        )
        if lift_report.verdict is ShortcutReviewVerdict.PASS:
            resolution = ShortcutResolution(
                review=lift_review,
                report=lift_report,
                considered_modes=(ShortcutMode.GLUE, ShortcutMode.LIFT),
            )
            return _wrap(
                base,
                composition_certificates=tuple(composition_certificates),
                resolution=resolution,
            )

    return _wrap(
        base,
        composition_certificates=tuple(composition_certificates),
    )
