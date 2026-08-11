from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Tuple

from .experience_substrate import Lesson, LessonAuthority, LessonKind
from .failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    FailureLink,
    FailureRelation,
    add_failure_experience,
    add_failure_link,
)


@dataclass(frozen=True)
class FailureDiagnosisRevisionSpec:
    new_failure_id: str
    selected_diagnosis: str
    diagnosis_status: FailureDiagnosisStatus
    new_evidence_pointers: Tuple[str, ...]
    artifact_hash: str
    timestamp: str
    broken_assumptions: Tuple[str, ...] | None = None
    scope_conditions: Tuple[str, ...] | None = None
    competing_diagnoses: Tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.new_failure_id or not self.selected_diagnosis or not self.artifact_hash or not self.timestamp:
            raise ValueError("diagnosis revision requires new identity, selected diagnosis, artifact hash, and timestamp")
        if self.diagnosis_status in {
            FailureDiagnosisStatus.OBSERVED_ONLY,
            FailureDiagnosisStatus.SUPERSEDED,
        }:
            raise ValueError("diagnosis revision must represent an active evidential diagnosis state")
        if not self.new_evidence_pointers:
            raise ValueError("diagnosis revision requires new evidence")


@dataclass(frozen=True)
class BoundaryLessonSpec:
    lesson_id: str
    trigger_signature: Tuple[str, ...]
    context_scope: Tuple[str, ...]
    action: str
    expected_effects: Tuple[str, ...]
    boundary_conditions: Tuple[str, ...]
    falsifier: str
    validation_obligations: Tuple[str, ...]
    artifact_hash: str

    def __post_init__(self) -> None:
        if not self.lesson_id or not self.action or not self.falsifier or not self.artifact_hash:
            raise ValueError("boundary lesson spec requires id, action, falsifier, and artifact hash")
        if not self.trigger_signature or not self.context_scope or not self.expected_effects:
            raise ValueError("boundary lesson spec requires trigger, context, and expected effects")
        if not self.boundary_conditions or not self.validation_obligations:
            raise ValueError("boundary lesson spec requires boundary conditions and validation obligations")


def revise_failure_diagnosis(
    lattice: FailureExperienceLattice,
    *,
    prior_failure_id: str,
    spec: FailureDiagnosisRevisionSpec,
) -> FailureExperienceLattice:
    """Append an evidence-backed diagnosis version; never rewrite the original failure."""

    by_id = {failure.failure_id: failure for failure in lattice.experiences}
    prior = by_id.get(prior_failure_id)
    if prior is None:
        raise ValueError("prior failure does not exist")
    if spec.new_failure_id in by_id:
        raise ValueError("diagnosis revision id already exists")

    evidence = tuple(dict.fromkeys(prior.evidence_pointers + spec.new_evidence_pointers))
    revised = replace(
        prior,
        failure_id=spec.new_failure_id,
        selected_diagnosis=spec.selected_diagnosis,
        diagnosis_status=spec.diagnosis_status,
        evidence_pointers=evidence,
        artifact_hash=spec.artifact_hash,
        timestamp=spec.timestamp,
        broken_assumptions=(
            spec.broken_assumptions
            if spec.broken_assumptions is not None
            else prior.broken_assumptions
        ),
        scope_conditions=(
            spec.scope_conditions
            if spec.scope_conditions is not None
            else prior.scope_conditions
        ),
        competing_diagnoses=(
            spec.competing_diagnoses
            if spec.competing_diagnoses is not None
            else prior.competing_diagnoses
        ),
    )
    updated = add_failure_experience(lattice, revised)
    return add_failure_link(
        updated,
        FailureLink(
            source_id=revised.failure_id,
            target_id=prior.failure_id,
            relation=FailureRelation.SUPERSEDES_DIAGNOSIS,
            rationale="new evidence supports a revised diagnosis while preserving the original observed failure record",
            evidence_pointers=spec.new_evidence_pointers,
        ),
    )


def boundary_lesson_from_supported_failure(
    failure: FailureExperience,
    spec: BoundaryLessonSpec,
) -> Lesson:
    """Convert supported failure knowledge into a candidate obstruction lesson.

    The output remains CANDIDATE authority.  Cross-context replay/transfer must use
    normal lesson consolidation before the boundary becomes reusable.
    """

    if failure.diagnosis_status not in {
        FailureDiagnosisStatus.SUPPORTED,
        FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY,
    }:
        raise ValueError("boundary lesson requires a supported or verified-impossibility diagnosis")
    if not failure.selected_diagnosis:
        raise ValueError("boundary lesson requires an explicit selected diagnosis")
    boundary_conditions = tuple(
        dict.fromkeys(
            spec.boundary_conditions
            + failure.scope_conditions
            + failure.broken_assumptions
        )
    )
    return Lesson(
        lesson_id=spec.lesson_id,
        kind=LessonKind.BOUNDARY,
        trigger_signature=spec.trigger_signature,
        context_scope=spec.context_scope,
        action=spec.action,
        expected_effects=spec.expected_effects,
        boundaries=boundary_conditions,
        supporting_episode_ids=(failure.research_trace_event_id,),
        contradicting_episode_ids=(),
        falsifier=spec.falsifier,
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=spec.validation_obligations,
        evidence_pointers=failure.evidence_pointers,
        artifact_hash=spec.artifact_hash,
    )
