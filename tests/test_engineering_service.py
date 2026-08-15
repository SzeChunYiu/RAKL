import pytest

from rakl.engineering_service import EngineeringReadService, EpistemicStatusUnavailable
from rakl.engineering_state import (
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    StateTransitionRequest,
)
from rakl.engineering_store import SqliteEngineeringStateStore

T0 = "2026-08-15T16:30:00+00:00"
T1 = "2026-08-15T16:31:00+00:00"


def snapshot(sequence=0, previous=None, semantic="semantic:0"):
    return ProjectSnapshot(
        project_id="p", sequence=sequence, previous_snapshot_id=previous,
        evidence_cutoff=f"e:{sequence}", semantic_state_revision=semantic,
        metric_ledger_head=f"m:{sequence}", episode_store_head=f"ep:{sequence}",
        saturation_basis_ids=("basis:v1",), authority_projection_revision=f"a:{sequence}",
        controller_epoch_id="epoch:0", created_at_utc=T0 if sequence == 0 else T1,
    )


def status(bound_snapshot):
    return EpistemicStatus(
        project_snapshot_id=bound_snapshot.snapshot_id,
        target_id="target", fiber_id="fiber",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("r1", "r2")),),
        required_routes=("r1", "r2"), covered_routes=("r1", "r2"), missing_routes=(),
        active_residual_ids=(), freshness_stale=False, required_authority=0,
        available_support_paths=1, blocking_cut_ids=(), hard_gate_ids=("sat",),
        next_action=NextActionClass.COMPILE_SOLVER_VIEW,
        reasons=("bounded_current_snapshot",), metric_receipt_ids=("metric:1",),
        basis_fingerprints=("basis:fingerprint",),
    )


def test_controller_and_observatory_share_exact_canonical_status(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "state.sqlite3")
    s0 = store.initialize_project(snapshot())
    canonical = store.record_epistemic_status(status(s0))
    read = EngineeringReadService(store).shared_status(project_id="p", target_id="target", fiber_id="fiber")
    assert read.status == canonical
    assert read.controller.status_id == canonical.status_id == read.observatory.status_id
    assert read.controller.project_snapshot_id == read.observatory.project_snapshot_id == s0.snapshot_id
    assert read.controller.next_action is read.observatory.next_action


def test_service_never_reuses_status_from_stale_snapshot(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "state.sqlite3")
    s0 = store.initialize_project(snapshot())
    store.record_epistemic_status(status(s0))
    s1 = snapshot(1, s0.snapshot_id, semantic="semantic:1")
    req = StateTransitionRequest(
        project_id="p", before_snapshot_id=s0.snapshot_id, action="ADVANCE",
        action_payload_hash="a" * 64, idempotency_key="advance", process_identity="worker",
        read_set=("head",), write_set=("head",), created_at_utc=T1,
    )
    store.commit_transition(req, s1, created_at_utc=T1)
    with pytest.raises(EpistemicStatusUnavailable):
        EngineeringReadService(store).current_status(project_id="p", target_id="target", fiber_id="fiber")
