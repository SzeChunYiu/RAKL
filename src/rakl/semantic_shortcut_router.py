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
    audit_obstruction_transformation_review,
    discover_shortcut_candidates,
    validate_transformation_memory,
)


@dataclass(frozen=True)
class ShortcutResolution:
    """Pure, non-authoritative resolution of the invention-last route ladder.

    The resolver does not make a transported transformation true.  It only chooses
    the first route whose already-supplied witnesses survive the canonical
    ``audit_obstruction_transformation_review`` gate.  Ambiguous or unresolved
    earlier lanes stop at ``CANNOT_CHECK`` rather than being bypassed.
    """

    review: ObstructionTransformationReview
    report: ShortcutReviewReport
    considered_modes: Tuple[ShortcutMode, ...]

    @property
    def selected_mode(self) -> ShortcutMode:
        return self.review.selected_mode

    @property
    def candidate_route_ready(self) -> bool:
        return self.report.candidate_route_ready



def _artifact_hash(
    *,
    review_id: str,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    memory_snapshot_hash: str,
    obstruction_id: str,
    mode: ShortcutMode,
    selected_episode_ids: Tuple[str, ...],
    direct_candidate_episode_ids: Tuple[str, ...],
    direct_mapping_witnesses: Tuple[StructuralMappingWitness, ...],
    jump_mapping_witnesses: Tuple[StructuralMappingWitness, ...],
    glue_witness: TransformationCompositionWitness | None,
    exhaustion_witness: ExhaustionWitness | None,
    missing_transformation_specification: MissingTransformationSpecification | None,
) -> str:
    payload = {
        "review_id": review_id,
        "atom_id": atom_id,
        "context_hash": context_hash,
        "research_memory_review_hash": research_memory_review_hash,
        "memory_snapshot_hash": memory_snapshot_hash,
        "obstruction_id": obstruction_id,
        "mode": mode.value,
        "selected_episode_ids": list(selected_episode_ids),
        "direct_candidate_episode_ids": list(direct_candidate_episode_ids),
        "direct_mapping_artifact_hashes": [
            witness.artifact_hash for witness in direct_mapping_witnesses
        ],
        "jump_mapping_artifact_hashes": [
            witness.artifact_hash for witness in jump_mapping_witnesses
        ],
        "glue_artifact_hash": glue_witness.artifact_hash if glue_witness else "",
        "exhaustion_artifact_hash": (
            exhaustion_witness.artifact_hash if exhaustion_witness else ""
        ),
        "lift_spec_artifact_hash": (
            missing_transformation_specification.artifact_hash
            if missing_transformation_specification
            else ""
        ),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()



def _review(
    *,
    review_id: str,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    transformation_memory: ObstructionTransformationMemory,
    obstruction: ObstructionFingerprint,
    mode: ShortcutMode,
    direct_search_status: RouteSearchStatus,
    jump_search_status: RouteSearchStatus,
    glue_search_status: RouteSearchStatus,
    evidence_pointers: Tuple[str, ...],
    direct_candidate_episode_ids: Tuple[str, ...] = (),
    direct_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = (),
    jump_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = (),
    glue_witness: TransformationCompositionWitness | None = None,
    selected_episode_ids: Tuple[str, ...] = (),
    exhaustion_witness: ExhaustionWitness | None = None,
    missing_transformation_specification: MissingTransformationSpecification | None = None,
) -> ObstructionTransformationReview:
    return ObstructionTransformationReview(
        review_id=review_id,
        target_atom_id=atom_id,
        target_context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        episode_memory_snapshot_hash=transformation_memory.snapshot_hash,
        obstruction=obstruction,
        direct_search_status=direct_search_status,
        jump_search_status=jump_search_status,
        glue_search_status=glue_search_status,
        selected_mode=mode,
        direct_candidate_episode_ids=direct_candidate_episode_ids,
        direct_mapping_witnesses=direct_mapping_witnesses,
        jump_mapping_witnesses=jump_mapping_witnesses,
        glue_witness=glue_witness,
        selected_episode_ids=selected_episode_ids,
        exhaustion_witness=exhaustion_witness,
        missing_transformation_specification=missing_transformation_specification,
        evidence_pointers=evidence_pointers,
        artifact_hash=_artifact_hash(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            memory_snapshot_hash=transformation_memory.snapshot_hash,
            obstruction_id=obstruction.obstruction_id,
            mode=mode,
            selected_episode_ids=selected_episode_ids,
            direct_candidate_episode_ids=direct_candidate_episode_ids,
            direct_mapping_witnesses=direct_mapping_witnesses,
            jump_mapping_witnesses=jump_mapping_witnesses,
            glue_witness=glue_witness,
            exhaustion_witness=exhaustion_witness,
            missing_transformation_specification=missing_transformation_specification,
        ),
    )



def _audit(
    review: ObstructionTransformationReview,
    *,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    transformation_memory: ObstructionTransformationMemory,
) -> ShortcutReviewReport:
    return audit_obstruction_transformation_review(
        review,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=transformation_memory,
    )



def resolve_obstruction_transformation_route(
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
) -> ShortcutResolution:
    """Resolve SEARCH -> JUMP -> GLUE -> LIFT without bypassing uncertainty.

    This is deliberately conservative.  A structurally available earlier route
    whose applicability witness is missing or invalid blocks fallback to a later
    route and returns ``CANNOT_CHECK``.  That keeps the selector aligned with the
    existing canonical audit rather than weakening it to manufacture route recall.

    LIFT is attempted only when SEARCH/JUMP/GLUE have no structural candidates in
    the bound memory.  More permissive "candidate was found but conclusively
    rejected" fall-through needs a future typed rejection witness; the current
    review schema does not carry one outside the LIFT exhaustion artifact.
    """

    if not review_id or not atom_id or not context_hash or not research_memory_review_hash:
        raise ValueError("resolver identity/context hashes must be nonempty")
    if not evidence_pointers or any(not value for value in evidence_pointers):
        raise ValueError("resolver requires nonempty evidence pointers")

    memory_reasons = validate_transformation_memory(transformation_memory)
    if memory_reasons:
        unresolved = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
            obstruction=obstruction,
            mode=ShortcutMode.CANNOT_CHECK,
            direct_search_status=RouteSearchStatus.NOT_RUN,
            jump_search_status=RouteSearchStatus.NOT_RUN,
            glue_search_status=RouteSearchStatus.NOT_RUN,
            evidence_pointers=evidence_pointers,
        )
        report = _audit(
            unresolved,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
        )
        return ShortcutResolution(unresolved, report, (ShortcutMode.CANNOT_CHECK,))

    candidates = discover_shortcut_candidates(obstruction, transformation_memory)
    direct_ids = tuple(match.episode_id for match in candidates.direct_matches)
    jump_ids = tuple(match.episode_id for match in candidates.jump_matches)
    glue_sets = tuple(candidates.glue_episode_sets)
    considered: list[ShortcutMode] = []

    if direct_ids:
        considered.append(ShortcutMode.SEARCH)
        direct_by_episode = {
            witness.episode_id: witness for witness in direct_mapping_witnesses
        }
        for episode_id in direct_ids:
            witness = direct_by_episode.get(episode_id)
            if witness is None:
                continue
            candidate = _review(
                review_id=review_id,
                atom_id=atom_id,
                context_hash=context_hash,
                research_memory_review_hash=research_memory_review_hash,
                transformation_memory=transformation_memory,
                obstruction=obstruction,
                mode=ShortcutMode.SEARCH,
                direct_search_status=RouteSearchStatus.MATCHES_FOUND,
                jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                evidence_pointers=evidence_pointers,
                direct_candidate_episode_ids=direct_ids,
                direct_mapping_witnesses=(witness,),
                selected_episode_ids=(episode_id,),
            )
            report = _audit(
                candidate,
                atom_id=atom_id,
                context_hash=context_hash,
                research_memory_review_hash=research_memory_review_hash,
                transformation_memory=transformation_memory,
            )
            if report.verdict is ShortcutReviewVerdict.PASS:
                return ShortcutResolution(candidate, report, tuple(considered))

        unresolved = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
            obstruction=obstruction,
            mode=ShortcutMode.CANNOT_CHECK,
            direct_search_status=RouteSearchStatus.MATCHES_FOUND,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
        )
        report = _audit(
            unresolved,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
        )
        return ShortcutResolution(
            unresolved, report, tuple(considered + [ShortcutMode.CANNOT_CHECK])
        )

    if jump_ids:
        considered.append(ShortcutMode.JUMP)
        jump_by_episode = {
            witness.episode_id: witness for witness in jump_mapping_witnesses
        }
        for episode_id in jump_ids:
            witness = jump_by_episode.get(episode_id)
            if witness is None:
                continue
            candidate = _review(
                review_id=review_id,
                atom_id=atom_id,
                context_hash=context_hash,
                research_memory_review_hash=research_memory_review_hash,
                transformation_memory=transformation_memory,
                obstruction=obstruction,
                mode=ShortcutMode.JUMP,
                direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                jump_search_status=RouteSearchStatus.MATCHES_FOUND,
                glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                evidence_pointers=evidence_pointers,
                jump_mapping_witnesses=(witness,),
                selected_episode_ids=(episode_id,),
            )
            report = _audit(
                candidate,
                atom_id=atom_id,
                context_hash=context_hash,
                research_memory_review_hash=research_memory_review_hash,
                transformation_memory=transformation_memory,
            )
            if report.verdict is ShortcutReviewVerdict.PASS:
                return ShortcutResolution(candidate, report, tuple(considered))

        unresolved = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
            obstruction=obstruction,
            mode=ShortcutMode.CANNOT_CHECK,
            direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
        )
        report = _audit(
            unresolved,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
        )
        return ShortcutResolution(
            unresolved, report, tuple(considered + [ShortcutMode.CANNOT_CHECK])
        )

    if glue_sets:
        considered.append(ShortcutMode.GLUE)
        if glue_witness is not None:
            selected = tuple(glue_witness.episode_ids)
            if tuple(sorted(selected)) in set(glue_sets):
                jump_by_episode = {
                    witness.episode_id: witness for witness in jump_mapping_witnesses
                }
                mappings = tuple(
                    jump_by_episode[item]
                    for item in selected
                    if item in jump_by_episode
                )
                if len(mappings) == len(selected):
                    candidate = _review(
                        review_id=review_id,
                        atom_id=atom_id,
                        context_hash=context_hash,
                        research_memory_review_hash=research_memory_review_hash,
                        transformation_memory=transformation_memory,
                        obstruction=obstruction,
                        mode=ShortcutMode.GLUE,
                        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
                        glue_search_status=RouteSearchStatus.MATCHES_FOUND,
                        evidence_pointers=evidence_pointers,
                        jump_mapping_witnesses=mappings,
                        glue_witness=glue_witness,
                        selected_episode_ids=selected,
                    )
                    report = _audit(
                        candidate,
                        atom_id=atom_id,
                        context_hash=context_hash,
                        research_memory_review_hash=research_memory_review_hash,
                        transformation_memory=transformation_memory,
                    )
                    if report.verdict is ShortcutReviewVerdict.PASS:
                        return ShortcutResolution(candidate, report, tuple(considered))

        unresolved = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
            obstruction=obstruction,
            mode=ShortcutMode.CANNOT_CHECK,
            direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
        )
        report = _audit(
            unresolved,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
        )
        return ShortcutResolution(
            unresolved, report, tuple(considered + [ShortcutMode.CANNOT_CHECK])
        )

    if exhaustion_witness is not None and missing_transformation_specification is not None:
        considered.append(ShortcutMode.LIFT)
        candidate = _review(
            review_id=review_id,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
            obstruction=obstruction,
            mode=ShortcutMode.LIFT,
            direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
            evidence_pointers=evidence_pointers,
            exhaustion_witness=exhaustion_witness,
            missing_transformation_specification=missing_transformation_specification,
        )
        report = _audit(
            candidate,
            atom_id=atom_id,
            context_hash=context_hash,
            research_memory_review_hash=research_memory_review_hash,
            transformation_memory=transformation_memory,
        )
        if report.verdict is ShortcutReviewVerdict.PASS:
            return ShortcutResolution(candidate, report, tuple(considered))

    considered.append(ShortcutMode.CANNOT_CHECK)
    unresolved = _review(
        review_id=review_id,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=transformation_memory,
        obstruction=obstruction,
        mode=ShortcutMode.CANNOT_CHECK,
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        evidence_pointers=evidence_pointers,
    )
    report = _audit(
        unresolved,
        atom_id=atom_id,
        context_hash=context_hash,
        research_memory_review_hash=research_memory_review_hash,
        transformation_memory=transformation_memory,
    )
    return ShortcutResolution(unresolved, report, tuple(considered))
