from __future__ import annotations

import pytest

from rakl.failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    FailureRelation,
    add_failure_experience,
)
from rakl.failure_learning import (
    BoundaryLessonSpec,
    FailureDiagnosisRevisionSpec,
    boundary_lesson_from_supported_failure,
    revise_failure_diagnosis,
)
from rakl.experience_substrate import LessonAuthority, LessonKind


def _observed_failure() -> FailureExperience:
    return FailureExperience(
        failure_id="F-observed",
        atom_id="A1",
        candidate_id="candidate",
        context_packet_hash="ctx",
        research_trace_event_id="E1",
        method_family="bridge-method",
        failure_mode="interface mismatch",
        residual_signature=("interface_mismatch",),
        broken_assumptions=(),
        scope_conditions=("ctx",),
        competing_diagnoses=("bad bridge", "scope mismatch"),
        selected_diagnosis="",
        diagnosis_status=FailureDiagnosisStatus.OBSERVED_ONLY,
        evidence_pointers=("artifact:E1",),
        falsifier_or_attempt="interface test",
        observed_result="FAILURE",
        artifact_hash="sha256:F-observed",
        timestamp="2026-08-11T09:10:00+00:00",
    )


def test_failure_diagnosis_revisions_preserve_original_observation() -> None:
    lattice = add_failure_experience(FailureExperienceLattice(), _observed_failure())
    updated = revise_failure_diagnosis(
        lattice,
        prior_failure_id="F-observed",
        spec=FailureDiagnosisRevisionSpec(
            new_failure_id="F-supported",
            selected_diagnosis="scope mismatch",
            diagnosis_status=FailureDiagnosisStatus.SUPPORTED,
            new_evidence_pointers=("challenge:scope-discriminator",),
            artifact_hash="sha256:F-supported",
            timestamp="2026-08-11T09:11:00+00:00",
            broken_assumptions=("shared interface scope",),
        ),
    )
    assert tuple(item.failure_id for item in updated.experiences) == ("F-observed", "F-supported")
    assert updated.experiences[0].diagnosis_status is FailureDiagnosisStatus.OBSERVED_ONLY
    assert updated.experiences[1].diagnosis_status is FailureDiagnosisStatus.SUPPORTED
    assert updated.experiences[1].selected_diagnosis == "scope mismatch"
    assert updated.links[0].relation is FailureRelation.SUPERSEDES_DIAGNOSIS
    assert updated.links[0].source_id == "F-supported"
    assert updated.links[0].target_id == "F-observed"


def test_only_supported_failure_can_seed_candidate_boundary_lesson() -> None:
    observed = _observed_failure()
    spec = BoundaryLessonSpec(
        lesson_id="B1",
        trigger_signature=("bridge", "interface"),
        context_scope=("typed interface",),
        action="require explicit scope alignment before bridge reuse",
        expected_effects=("avoid interface mismatch",),
        boundary_conditions=("cross-scope composition",),
        falsifier="bridge succeeds under deliberately misaligned scope",
        validation_obligations=("fresh cross-scope replay",),
        artifact_hash="sha256:B1",
    )
    with pytest.raises(ValueError, match="supported or verified-impossibility"):
        boundary_lesson_from_supported_failure(observed, spec)

    supported = FailureExperience(
        **{
            **observed.__dict__,
            "failure_id": "F-supported",
            "selected_diagnosis": "scope mismatch",
            "diagnosis_status": FailureDiagnosisStatus.SUPPORTED,
            "broken_assumptions": ("shared interface scope",),
            "artifact_hash": "sha256:F-supported",
        }
    )
    lesson = boundary_lesson_from_supported_failure(supported, spec)
    assert lesson.kind is LessonKind.BOUNDARY
    assert lesson.authority is LessonAuthority.CANDIDATE
    assert lesson.supporting_episode_ids == ("E1",)
    assert "shared interface scope" in lesson.boundaries
