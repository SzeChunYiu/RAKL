import pytest

from rakl.engineering_api import EngineeringServiceFacade
from rakl.engineering_capacity import (
    CapacityVerdict,
    EngineeringCapacityObservation,
    EngineeringCapacityPolicy,
    assess_engineering_capacity,
)
from rakl.engineering_state import (
    EpistemicAxisStatus, EpistemicStatus, NextActionClass, ProjectSnapshot,
    StateTransitionRequest, TransitionStatus,
)
from rakl.engineering_store import SqliteEngineeringStateStore

T0="2026-08-15T17:00:00+00:00"; T1="2026-08-15T17:01:00+00:00"


def snap(seq=0, prev=None):
    return ProjectSnapshot(
        project_id="p", sequence=seq, previous_snapshot_id=prev,
        evidence_cutoff=f"e:{seq}", semantic_state_revision=f"s:{seq}",
        metric_ledger_head=f"m:{seq}", episode_store_head=f"ep:{seq}",
        saturation_basis_ids=("b",), authority_projection_revision=f"a:{seq}",
        controller_epoch_id="epoch", created_at_utc=T0 if seq == 0 else T1,
    )


def status(s):
    return EpistemicStatus(
        project_snapshot_id=s.snapshot_id, target_id="t", fiber_id="f",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("r1",)),),
        required_routes=("r1",), covered_routes=("r1",), missing_routes=(),
        active_residual_ids=(), freshness_stale=False, required_authority=0,
        available_support_paths=1, blocking_cut_ids=(), hard_gate_ids=("sat",),
        next_action=NextActionClass.COMPILE_SOLVER_VIEW, reasons=("ready",),
        metric_receipt_ids=("metric",), basis_fingerprints=("basis",),
    )


def test_service_plan_is_projection_of_canonical_status(tmp_path):
    store=SqliteEngineeringStateStore(tmp_path/"s.sqlite3")
    s0=store.initialize_project(snap()); st=store.record_epistemic_status(status(s0))
    api=EngineeringServiceFacade(store)
    plan=api.plan_action(project_id="p",target_id="t",fiber_id="f")
    assert plan.project_snapshot_id == s0.snapshot_id
    assert plan.status_id == st.status_id
    assert plan.next_action == st.next_action.value


def test_service_mutation_preserves_snapshot_cas_and_idempotency(tmp_path):
    store=SqliteEngineeringStateStore(tmp_path/"s.sqlite3"); s0=store.initialize_project(snap())
    s1=snap(1,s0.snapshot_id)
    req=StateTransitionRequest(
        project_id="p", before_snapshot_id=s0.snapshot_id, action="ADVANCE",
        action_payload_hash="c"*64, idempotency_key="k", process_identity="w",
        read_set=("head",), write_set=("head",), created_at_utc=T1,
    )
    api=EngineeringServiceFacade(store)
    first=api.commit_metadata_transition(request=req,after_snapshot=s1,created_at_utc=T1)
    second=api.commit_metadata_transition(request=req,after_snapshot=s1,created_at_utc=T1)
    assert first == second
    assert first.status is TransitionStatus.COMMITTED


def test_capacity_is_noncompensatory_and_missing_measurement_fails_closed():
    policy=EngineeringCapacityPolicy("p",1000,1000,2,1,100)
    missing=EngineeringCapacityObservation("snapshot:x",1,None,0,0,10)
    assert assess_engineering_capacity(missing,policy).verdict is CapacityVerdict.CANNOT_CHECK

    context_over=EngineeringCapacityObservation("snapshot:x",1,1,0,0,101)
    assert assess_engineering_capacity(context_over,policy).verdict is CapacityVerdict.BLOCK_NEW_WORK

    index_over=EngineeringCapacityObservation("snapshot:x",1,1001,0,2,10)
    result=assess_engineering_capacity(index_over,policy)
    assert result.verdict is CapacityVerdict.COMPACT_REBUILDABLE_VIEWS
    assert result.preserve_canonical_history
