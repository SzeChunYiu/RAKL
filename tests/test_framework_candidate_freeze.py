"""Frozen worlds for authoritative framework-SHA revalidation at candidate freeze (#385)."""

from __future__ import annotations

import pytest

from rakl.framework_candidate_freeze import (
    CandidateFreezeRevalidationVerdict,
    DiffPathClassification,
    DiffSurfaceClass,
    FrameworkSubjectFreezeBinding,
    FrameworkSubjectRevalidationObservation,
    audit_candidate_freeze_framework_subject,
    gate_candidate_materialization_framework_subject,
)
from rakl.math_research_assurance import MathResearchRecord
from rakl.math_research_runtime import plan_math_research
from rakl.problem_solving_algebra import ProblemSignature


FREEZE_SHA = "a" * 40
CURRENT_SHA = "b" * 40
PACKET_HASH = "c" * 64


def _binding() -> FrameworkSubjectFreezeBinding:
    return FrameworkSubjectFreezeBinding(
        binding_id="FSB-1",
        authoritative_framework_sha=FREEZE_SHA,
        pre_candidate_packet_hash=PACKET_HASH,
        frozen_at_utc="2026-08-12T04:00:00Z",
        evidence_pointers=("evidence:pre-candidate-freeze",),
    )


def test_inactive_gate_licenses_without_binding() -> None:
    report = audit_candidate_freeze_framework_subject(None, None, required=False)
    assert report.licenses_candidate_materialization is True
    assert report.verdict is CandidateFreezeRevalidationVerdict.CURRENT_UNCHANGED


def test_unchanged_main_licenses_candidate_materialization() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=FREEZE_SHA,
        intervening_diff=(),
        observation_evidence_pointers=("evidence:observed-main",),
    )
    report = gate_candidate_materialization_framework_subject(_binding(), observation)
    assert report.verdict is CandidateFreezeRevalidationVerdict.CURRENT_UNCHANGED
    assert report.licenses_candidate_materialization is True
    assert report.grants_scientific_authority is False


def test_non_method_publication_drift_acknowledged_without_invalidation() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=CURRENT_SHA,
        intervening_diff=(
            DiffPathClassification(
                path="research/PAPER_NOTE.md",
                surface_class=DiffSurfaceClass.NON_METHOD_PUBLICATION_OR_RESEARCH,
            ),
        ),
        observation_evidence_pointers=("evidence:diff-class",),
    )
    report = audit_candidate_freeze_framework_subject(_binding(), observation)
    assert report.verdict is CandidateFreezeRevalidationVerdict.ACKNOWLEDGED_NON_METHOD_DRIFT
    assert report.licenses_candidate_materialization is True
    assert report.non_method_paths_changed == ("research/PAPER_NOTE.md",)


def test_protected_surface_change_fails_closed() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=CURRENT_SHA,
        intervening_diff=(
            DiffPathClassification(
                path="src/rakl/math_research_runtime.py",
                surface_class=DiffSurfaceClass.PROTECTED_METHOD_GATE_SCHEMA_RUNTIME,
            ),
            DiffPathClassification(
                path="research/PAPER_NOTE.md",
                surface_class=DiffSurfaceClass.NON_METHOD_PUBLICATION_OR_RESEARCH,
            ),
        ),
        observation_evidence_pointers=("evidence:diff-class",),
    )
    report = audit_candidate_freeze_framework_subject(_binding(), observation)
    assert report.verdict is CandidateFreezeRevalidationVerdict.STALE_PROTECTED_SURFACE_CHANGED
    assert report.licenses_candidate_materialization is False
    assert report.protected_paths_changed == ("src/rakl/math_research_runtime.py",)


def test_unclassified_diff_fails_closed() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=CURRENT_SHA,
        intervening_diff=(
            DiffPathClassification(
                path="mystery.txt",
                surface_class=DiffSurfaceClass.UNCLASSIFIED,
            ),
        ),
        observation_evidence_pointers=("evidence:diff-class",),
    )
    report = audit_candidate_freeze_framework_subject(_binding(), observation)
    assert report.verdict is CandidateFreezeRevalidationVerdict.UNCLASSIFIED_DIFF_FAIL_CLOSED
    assert report.licenses_candidate_materialization is False


def test_sha_changed_without_diff_cannot_check() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=CURRENT_SHA,
        intervening_diff=(),
        observation_evidence_pointers=("evidence:observed-main",),
    )
    report = audit_candidate_freeze_framework_subject(_binding(), observation)
    assert report.verdict is CandidateFreezeRevalidationVerdict.CANNOT_CHECK
    assert report.licenses_candidate_materialization is False


def test_binding_rejects_scientific_authority_flag() -> None:
    report = audit_candidate_freeze_framework_subject(_binding(), None, required=True)
    assert report.licenses_candidate_materialization is False
    with pytest.raises(ValueError, match="scientific authority"):
        type(report)(
            binding_id="x",
            verdict=CandidateFreezeRevalidationVerdict.CURRENT_UNCHANGED,
            reasons=("x",),
            freeze_sha=FREEZE_SHA,
            observed_current_main_sha=FREEZE_SHA,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=True,
            grants_scientific_authority=True,
        )


def test_plan_math_research_framework_subject_gate_blocks_candidates() -> None:
    observation = FrameworkSubjectRevalidationObservation(
        observed_current_main_sha=CURRENT_SHA,
        intervening_diff=(
            DiffPathClassification(
                path="schemas/math-research-trace.schema.json",
                surface_class=DiffSurfaceClass.PROTECTED_METHOD_GATE_SCHEMA_RUNTIME,
            ),
        ),
        observation_evidence_pointers=("evidence:diff-class",),
    )
    plan = plan_math_research(
        signature=ProblemSignature(
            objects=("claim",),
            domain="mathematics",
            goal_type="prove theorem",
        ),
        record=MathResearchRecord(claim_id="C-freeze"),
        framework_subject_binding=_binding(),
        framework_subject_observation=observation,
    )
    assert plan.candidate_generation_allowed is False
    assert plan.framework_subject_gate is not None
    assert (
        plan.framework_subject_gate.verdict
        is CandidateFreezeRevalidationVerdict.STALE_PROTECTED_SURFACE_CHANGED
    )
    assert plan.framework_subject_gate.licenses_candidate_materialization is False
