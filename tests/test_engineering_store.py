import sqlite3

import pytest

from rakl.engineering_state import (
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    StateTransitionRequest,
    TransitionStatus,
)
from rakl.engineering_store import (
    EngineeringIntegrityError,
    IdempotencyConflict,
    SqliteEngineeringStateStore,
)


T0 = "2026-08-15T14:00:00+00:00"
T1 = "2026-08-15T14:01:00+00:00"
T2 = "2026-08-15T14:02:00+00:00"


def make_snapshot(sequence, previous, semantic):
    return ProjectSnapshot(
        project_id="project:demo",
        sequence=sequence,
        previous_snapshot_id=previous,
        evidence_cutoff=f"evidence:{sequence}",
        semantic_state_revision=semantic,
        metric_ledger_head=f"metric:{sequence}",
        episode_store_head=f"episode:{sequence}",
        saturation_basis_ids=("basis:v1",),
        authority_projection_revision=f"authority:{sequence}",
        controller_epoch_id="epoch:1",
        created_at_utc=T0 if sequence == 0 else (T1 if sequence == 1 else T2),
    )


def make_request(before, key, *, action="UPDATE_ATLAS"):
    return StateTransitionRequest(
        project_id="project:demo",
        before_snapshot_id=before.snapshot_id,
        action=action,
        action_payload_hash="b" * 64,
        idempotency_key=key,
        process_identity="worker:test",
        read_set=("semantic_state", "saturation"),
        write_set=("semantic_state", "saturation"),
        created_at_utc=T1,
    )


def test_reference_store_commits_snapshot_and_reopens(tmp_path):
    path = tmp_path / "engineering.sqlite3"
    store = SqliteEngineeringStateStore(path)
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    receipt = store.commit_transition(make_request(s0, "idem:1"), s1, created_at_utc=T1)
    assert receipt.status is TransitionStatus.COMMITTED
    assert store.head("project:demo") == s1

    reopened = SqliteEngineeringStateStore(path)
    assert reopened.head("project:demo") == s1
    assert reopened.transition_receipt("project:demo", "idem:1") == receipt


def test_idempotent_replay_does_not_create_second_snapshot(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    request = make_request(s0, "idem:same")
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    first = store.commit_transition(request, s1, created_at_utc=T1)
    second = store.commit_transition(request, s1, created_at_utc=T1)
    assert first == second
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 2


def test_idempotency_key_reuse_for_different_request_fails_closed(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    store.commit_transition(make_request(s0, "idem:1"), s1, created_at_utc=T1)
    different = make_request(s0, "idem:1", action="DIFFERENT_ACTION")
    with pytest.raises(IdempotencyConflict):
        store.commit_transition(different, s1, created_at_utc=T1)


def test_stale_competing_update_is_retry_required_not_last_writer_wins(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:winner")
    assert store.commit_transition(make_request(s0, "winner"), s1, created_at_utc=T1).status is TransitionStatus.COMMITTED

    # This worker planned against the now-stale s0.  Its proposed after snapshot
    # is never installed; the store records a typed retry requirement.
    stale_after = make_snapshot(1, s0.snapshot_id, "semantic:loser")
    stale = store.commit_transition(make_request(s0, "loser"), stale_after, created_at_utc=T2)
    assert stale.status is TransitionStatus.RETRY_REQUIRED
    assert stale.after_snapshot_id is None
    assert store.head("project:demo") == s1


def test_status_is_bound_to_existing_snapshot_and_roundtrips(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    status = EpistemicStatus(
        project_snapshot_id=s0.snapshot_id,
        target_id="target:qoi",
        fiber_id="fiber:knowledge",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("R1", "R2")),),
        required_routes=("R1", "R2"),
        covered_routes=("R1", "R2"),
        missing_routes=(),
        active_residual_ids=(),
        freshness_stale=False,
        required_authority=1,
        available_support_paths=2,
        blocking_cut_ids=(),
        hard_gate_ids=("bounded_saturation_gate",),
        next_action=NextActionClass.PROCEED_OBJECT_WORK,
        reasons=("bounded_knowledge_saturation_established",),
        metric_receipt_ids=("metric:1",),
        basis_fingerprints=("basis-fingerprint:1",),
    )
    store.record_epistemic_status(status)
    assert store.latest_epistemic_status(
        project_snapshot_id=s0.snapshot_id,
        target_id="target:qoi",
        fiber_id="fiber:knowledge",
    ) == status


def test_snapshot_payload_tampering_is_detected_on_read(tmp_path):
    path = tmp_path / "engineering.sqlite3"
    store = SqliteEngineeringStateStore(path)
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    with sqlite3.connect(path) as db:
        payload = db.execute("SELECT payload_json FROM snapshots WHERE snapshot_id=?", (s0.snapshot_id,)).fetchone()[0]
        db.execute(
            "UPDATE snapshots SET payload_json=? WHERE snapshot_id=?",
            (payload.replace("semantic:0", "semantic:tampered"), s0.snapshot_id),
        )
    with pytest.raises(ValueError, match="snapshot_id"):
        store.get_snapshot(s0.snapshot_id)


def test_actual_concurrent_writers_produce_one_commit_and_one_retry(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    barrier = threading.Barrier(2)

    def run(key, semantic):
        local_store = SqliteEngineeringStateStore(store.path)
        request = make_request(s0, key)
        proposed = make_snapshot(1, s0.snapshot_id, semantic)
        barrier.wait()
        return local_store.commit_transition(request, proposed, created_at_utc=T1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda args: run(*args), (("k:a", "semantic:a"), ("k:b", "semantic:b"))))

    statuses = sorted(item.status.value for item in results)
    assert statuses == [TransitionStatus.COMMITTED.value, TransitionStatus.RETRY_REQUIRED.value]
    committed = next(item for item in results if item.status is TransitionStatus.COMMITTED)
    assert store.head("project:demo").snapshot_id == committed.after_snapshot_id


def test_recovery_required_outcome_is_idempotently_persisted(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    request = make_request(s0, "external:ambiguous", action="RUN_NON_IDEMPOTENT_ACTIVITY")
    first = store.record_noncommitted_transition(
        request,
        status=TransitionStatus.RECOVERY_REQUIRED,
        reasons=("worker_died_after_possible_external_effect",),
        created_at_utc=T1,
    )
    second = store.record_noncommitted_transition(
        request,
        status=TransitionStatus.RECOVERY_REQUIRED,
        reasons=("worker_died_after_possible_external_effect",),
        created_at_utc=T1,
    )
    assert first == second
    assert first.status is TransitionStatus.RECOVERY_REQUIRED
    assert store.head("project:demo") == s0


def test_same_snapshot_target_fiber_cannot_have_two_epistemic_truths(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    base = dict(
        project_snapshot_id=s0.snapshot_id,
        target_id="target:qoi",
        fiber_id="fiber:knowledge",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("R1", "R2")),),
        required_routes=("R1", "R2"),
        covered_routes=("R1", "R2"),
        missing_routes=(),
        active_residual_ids=(),
        freshness_stale=False,
        required_authority=1,
        available_support_paths=1,
        blocking_cut_ids=(),
        hard_gate_ids=("bounded_saturation_gate",),
        reasons=("bounded_knowledge_saturation_established",),
        metric_receipt_ids=("metric:1",),
        basis_fingerprints=("basis:1",),
    )
    first = EpistemicStatus(next_action=NextActionClass.PROCEED_OBJECT_WORK, **base)
    store.record_epistemic_status(first)
    conflicting = EpistemicStatus(next_action=NextActionClass.CONTINUE_SEARCH, **base)
    with pytest.raises(EngineeringIntegrityError, match="different EpistemicStatus"):
        store.record_epistemic_status(conflicting)


def test_transition_rejects_snapshot_from_different_project(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "state.sqlite3")
    def initial(project_id):
        return ProjectSnapshot(
            project_id=project_id, sequence=0, previous_snapshot_id=None,
            evidence_cutoff="evidence:0", semantic_state_revision="semantic:0",
            metric_ledger_head="metric:0", episode_store_head="episode:0",
            saturation_basis_ids=("basis:v1",), authority_projection_revision="authority:0",
            controller_epoch_id="epoch:1", created_at_utc=T0,
        )
    p1, p2 = initial("p1"), initial("p2")
    store.initialize_project(p1)
    store.initialize_project(p2)
    request = StateTransitionRequest(
        project_id="p1", before_snapshot_id=p2.snapshot_id, action="UPDATE_ATLAS",
        action_payload_hash="b" * 64,
        idempotency_key="cross-project", process_identity="worker:test",
        read_set=("semantic_state",), write_set=("semantic_state",), created_at_utc=T1,
    )
    after = ProjectSnapshot(
        project_id="p1", sequence=1, previous_snapshot_id=p1.snapshot_id,
        evidence_cutoff="evidence:1", semantic_state_revision="semantic:1",
        metric_ledger_head="metric:1", episode_store_head="episode:1",
        saturation_basis_ids=("basis:v1",), authority_projection_revision="authority:1",
        controller_epoch_id="epoch:1", created_at_utc=T1,
    )
    with pytest.raises(EngineeringIntegrityError, match="different project"):
        store.commit_transition(request, after, created_at_utc=T1)
    assert store.transition_receipt("p1", "cross-project") is None
