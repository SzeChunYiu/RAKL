from dataclasses import dataclass
from enum import Enum

import pytest

from rakl.engineering_state import (
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    StateTransitionReceipt,
    StateTransitionRequest,
    TransitionStatus,
    status_from_saturation_vector,
)


T0 = "2026-08-15T14:00:00+00:00"


def snapshot(sequence=0, previous=None, semantic="semantic:0"):
    return ProjectSnapshot(
        project_id="project:demo",
        sequence=sequence,
        previous_snapshot_id=previous,
        evidence_cutoff="evidence:cutoff:0",
        semantic_state_revision=semantic,
        metric_ledger_head="metric:head:0",
        episode_store_head="episode:head:0",
        saturation_basis_ids=("basis:knowledge:v1",),
        authority_projection_revision="authority:0",
        controller_epoch_id="epoch:0",
        created_at_utc=T0,
    )


def test_snapshot_identity_roundtrip_and_tamper_rejection():
    s = snapshot()
    assert s.snapshot_id.startswith("snapshot:")
    assert ProjectSnapshot.from_dict(s.to_dict()) == s
    broken = s.to_dict()
    broken["semantic_state_revision"] = "semantic:tampered"
    with pytest.raises(ValueError, match="snapshot_id"):
        ProjectSnapshot.from_dict(broken)


def test_epistemic_status_keeps_axis_vector_and_never_grants_completeness():
    s = snapshot()
    status = EpistemicStatus(
        project_snapshot_id=s.snapshot_id,
        target_id="target:qoi",
        fiber_id="fiber:mechanism",
        axis_statuses=(
            EpistemicAxisStatus("KNOWLEDGE", True, 0, ("FOUNDATIONAL", "ALIEN")),
            EpistemicAxisStatus("PATH", False, 2, ("BACKWARD",)),
        ),
        required_routes=("FOUNDATIONAL", "ALIEN"),
        covered_routes=("FOUNDATIONAL", "ALIEN"),
        missing_routes=(),
        active_residual_ids=("residual:path",),
        freshness_stale=False,
        required_authority=2,
        available_support_paths=0,
        blocking_cut_ids=("cut:1",),
        hard_gate_ids=("bounded_saturation_gate",),
        next_action=NextActionClass.REPAIR_EPISTEMIC_CUT,
        reasons=("knowledge_flat_but_target_path_blocked",),
        metric_receipt_ids=("metric:saturation:1",),
        basis_fingerprints=("sha256:basis",),
    )
    assert not status.bounded_saturated
    assert not status.grants_absolute_completeness
    assert not status.grants_scientific_authority
    assert EpistemicStatus.from_dict(status.to_dict()) == status


def test_status_route_complement_is_enforced():
    with pytest.raises(ValueError, match="missing_routes"):
        EpistemicStatus(
            project_snapshot_id="snapshot:x",
            target_id="target:x",
            fiber_id="fiber:x",
            axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", False, 1),),
            required_routes=("A", "B"),
            covered_routes=("A",),
            missing_routes=(),
            active_residual_ids=(),
            freshness_stale=False,
            required_authority=0,
            available_support_paths=0,
            blocking_cut_ids=(),
            hard_gate_ids=(),
            next_action=NextActionClass.CONTINUE_SEARCH,
            reasons=("route_missing",),
            metric_receipt_ids=(),
            basis_fingerprints=(),
        )


def test_committed_receipt_requires_after_snapshot_and_noncommitted_forbids_it():
    with pytest.raises(ValueError, match="after_snapshot_id"):
        StateTransitionReceipt(
            project_id="p",
            before_snapshot_id="s0",
            after_snapshot_id=None,
            action="update",
            action_payload_hash="b" * 64,
            idempotency_key="k",
            request_hash="a" * 64,
            process_identity="worker",
            read_set=("semantic",),
            write_set=("semantic",),
            produced_artifact_ids=(),
            metric_receipt_ids=(),
            residual_ids=(),
            status=TransitionStatus.COMMITTED,
            reasons=("bad",),
            created_at_utc=T0,
        )


class Axis(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"


@dataclass(frozen=True)
class AxisReport:
    axis: Axis
    flat: bool
    independent_flat_route_families: tuple[str, ...]
    recent_retained_novelty: int
    reopen_residuals: tuple[str, ...]


@dataclass(frozen=True)
class VectorReport:
    axis_reports: tuple[AxisReport, ...]


def test_saturation_projection_is_structural_and_explicit_about_next_action():
    report = VectorReport((AxisReport(Axis.KNOWLEDGE, True, ("R1", "R2"), 0, ()),))
    result = status_from_saturation_vector(
        project_snapshot_id="snapshot:1",
        target_id="target:1",
        fiber_id="fiber:1",
        saturation_report=report,
        required_routes=("R1", "R2"),
        covered_routes=("R1", "R2"),
        next_action=NextActionClass.PROCEED_OBJECT_WORK,
        reasons=("bounded_knowledge_saturation_established",),
    )
    assert result.bounded_saturated
    assert result.next_action is NextActionClass.PROCEED_OBJECT_WORK
    assert result.missing_routes == ()
