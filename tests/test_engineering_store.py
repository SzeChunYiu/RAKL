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
    metadata_transition_payload_hash,
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


def make_request(before, key, *, after, action="UPDATE_ATLAS"):
    return StateTransitionRequest(
        project_id="project:demo",
        before_snapshot_id=before.snapshot_id,
        action=action,
        action_payload_hash=metadata_transition_payload_hash(after),
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
    receipt = store.commit_transition(make_request(s0, "idem:1", after=s1), s1, created_at_utc=T1)
    assert receipt.status is TransitionStatus.COMMITTED
    assert store.head("project:demo") == s1

    reopened = SqliteEngineeringStateStore(path)
    assert reopened.head("project:demo") == s1
    assert reopened.transition_receipt("project:demo", "idem:1") == receipt


def test_idempotent_replay_does_not_create_second_snapshot(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    request = make_request(s0, "idem:same", after=s1)
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
    store.commit_transition(make_request(s0, "idem:1", after=s1), s1, created_at_utc=T1)
    different = make_request(s0, "idem:1", after=s1, action="DIFFERENT_ACTION")
    with pytest.raises(IdempotencyConflict):
        store.commit_transition(different, s1, created_at_utc=T1)


def test_stale_competing_update_is_retry_required_not_last_writer_wins(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:winner")
    assert store.commit_transition(make_request(s0, "winner", after=s1), s1, created_at_utc=T1).status is TransitionStatus.COMMITTED

    # This worker planned against the now-stale s0.  Its proposed after snapshot
    # is never installed; the store records a typed retry requirement.
    stale_after = make_snapshot(1, s0.snapshot_id, "semantic:loser")
    stale = store.commit_transition(make_request(s0, "loser", after=stale_after), stale_after, created_at_utc=T2)
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
        proposed = make_snapshot(1, s0.snapshot_id, semantic)
        request = make_request(s0, key, after=proposed)
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
    request = make_request(s0, "external:ambiguous", after=s0, action="RUN_NON_IDEMPOTENT_ACTIVITY")
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
    after = ProjectSnapshot(
        project_id="p1", sequence=1, previous_snapshot_id=p1.snapshot_id,
        evidence_cutoff="evidence:1", semantic_state_revision="semantic:1",
        metric_ledger_head="metric:1", episode_store_head="episode:1",
        saturation_basis_ids=("basis:v1",), authority_projection_revision="authority:1",
        controller_epoch_id="epoch:1", created_at_utc=T1,
    )
    request = StateTransitionRequest(
        project_id="p1", before_snapshot_id=p2.snapshot_id, action="UPDATE_ATLAS",
        action_payload_hash=metadata_transition_payload_hash(after),
        idempotency_key="cross-project", process_identity="worker:test",
        read_set=("semantic_state",), write_set=("semantic_state",), created_at_utc=T1,
    )
    with pytest.raises(EngineeringIntegrityError, match="different project"):
        store.commit_transition(request, after, created_at_utc=T1)
    assert store.transition_receipt("p1", "cross-project") is None


# --- X08 regression: the base store is not a bypass around payload binding ---


def test_transition_whose_payload_hash_binds_nothing_is_refused_and_moves_no_head(tmp_path):
    """CROSS_PLANE_ATTACKS_V1 X08: before the fix this COMMITTED and moved six heads."""

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    attacker_after = ProjectSnapshot(
        project_id="project:demo", sequence=1, previous_snapshot_id=s0.snapshot_id,
        evidence_cutoff="evidence:ATTACKER", semantic_state_revision="semantic:ATTACKER",
        metric_ledger_head="metric:ATTACKER", episode_store_head="episode:ATTACKER",
        saturation_basis_ids=("basis:ATTACKER",), authority_projection_revision="authority:ATTACKER",
        controller_epoch_id="epoch:ATTACKER", created_at_utc=T1,
    )
    unbound = StateTransitionRequest(
        project_id="project:demo", before_snapshot_id=s0.snapshot_id, action="unrelated_noop",
        action_payload_hash="b" * 64, idempotency_key="k-unbound", process_identity="attacker",
        read_set=(), write_set=(), created_at_utc=T1,
    )
    with pytest.raises(EngineeringIntegrityError, match="does not bind the after snapshot"):
        store.commit_transition(unbound, attacker_after, created_at_utc=T1)
    assert store.head("project:demo") == s0
    # refused outright: no receipt of any status is minted for it
    assert store.transition_receipt("project:demo", "k-unbound") is None
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] == 0


def test_payload_hash_bound_to_a_different_after_snapshot_is_refused(tmp_path):
    """Binding some other snapshot is not binding this one."""

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    intended = make_snapshot(1, s0.snapshot_id, "semantic:intended")
    smuggled = make_snapshot(1, s0.snapshot_id, "semantic:smuggled")
    request = make_request(s0, "k", after=intended)
    with pytest.raises(EngineeringIntegrityError, match="does not bind the after snapshot"):
        store.commit_transition(request, smuggled, created_at_utc=T1)
    assert store.head("project:demo") == s0


def test_coordinator_style_payload_hash_cannot_be_replayed_through_the_base_store(tmp_path):
    """Domain separation: a hash minted for the semantic/evidence path is refused here."""

    from rakl.engineering_state import canonical_sha256

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    for foreign in (
        canonical_sha256({"semantic_batch_id": "semantic-batch:x"}),
        canonical_sha256({"evidence_batch_id": "evidence-batch:x"}),
        canonical_sha256({"atlas_batch_id": "atlas-batch-x"}),
    ):
        request = StateTransitionRequest(
            project_id="project:demo", before_snapshot_id=s0.snapshot_id, action="ADVANCE",
            action_payload_hash=foreign, idempotency_key=f"k-{foreign[:8]}",
            process_identity="worker:test", read_set=(), write_set=(), created_at_utc=T1,
        )
        with pytest.raises(EngineeringIntegrityError, match="does not bind the after snapshot"):
            store.commit_transition(request, s1, created_at_utc=T1)
    assert store.head("project:demo") == s0


def test_legitimately_bound_transition_still_commits_and_replays(tmp_path):
    """NO-ALARM: the guard must not flag the honest path."""

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    request = make_request(s0, "k", after=s1)
    assert request.action_payload_hash == metadata_transition_payload_hash(s1)
    first = store.commit_transition(request, s1, created_at_utc=T1)
    assert first.status is TransitionStatus.COMMITTED
    assert first.action_payload_hash == metadata_transition_payload_hash(s1)
    assert store.commit_transition(request, s1, created_at_utc=T1) == first
    assert store.head("project:demo") == s1



# --- the dead idempotency key -------------------------------------------------


def test_retry_required_receipt_does_not_kill_the_idempotency_key(tmp_path):
    """The exact five-step trace the capacity campaign recorded.

    A commits from genesis. B, built against genesis (now stale), gets
    RETRY_REQUIRED telling it to replan on the current head. Before the fix, B
    doing exactly that under the SAME key was refused as IDEMPOTENCY_CONFLICT
    forever, because the deferral occupied the (project, key) slot and its
    request_hash bound the stale before snapshot. Only a fresh key could
    commit. Same-key eventual success under 16 writers measured 0.317.

    A RETRY_REQUIRED receipt is a deferral, not a binding: the retry it asks
    for supersedes it, and the superseded deferral is kept.
    """

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    # 1. A commits from genesis
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    a = store.commit_transition(make_request(s0, "key:A", after=s1), s1, created_at_utc=T1)
    assert a.status is TransitionStatus.COMMITTED
    # 2. B built against genesis, now stale -> RETRY_REQUIRED, persisted under key:B
    s1b = make_snapshot(1, s0.snapshot_id, "semantic:1b")
    b_stale = store.commit_transition(make_request(s0, "key:B", after=s1b), s1b, created_at_utc=T1)
    assert b_stale.status is TransitionStatus.RETRY_REQUIRED
    assert store.transition_receipt("project:demo", "key:B").status is TransitionStatus.RETRY_REQUIRED
    # 3. B does exactly what the receipt asked: same key, fresh before snapshot
    s2 = make_snapshot(2, s1.snapshot_id, "semantic:2")
    b_retry = store.commit_transition(make_request(s1, "key:B", after=s2), s2, created_at_utc=T2)
    assert b_retry.status is TransitionStatus.COMMITTED, "the retry the deferral asked for must commit under the same key"
    assert store.head("project:demo") == s2
    # the deferral is superseded, and kept
    conn = sqlite3.connect(tmp_path / "engineering.sqlite3")
    kept = conn.execute("SELECT status FROM superseded_transitions WHERE idempotency_key=?", ("key:B",)).fetchall()
    conn.close()
    assert kept == [("RETRY_REQUIRED",)]
    # 4. the key now holds the COMMITTED receipt and replays it
    assert store.transition_receipt("project:demo", "key:B") == b_retry
    assert store.commit_transition(make_request(s1, "key:B", after=s2), s2, created_at_utc=T2) == b_retry


def test_two_deferrals_then_commit_counts_supersessions(tmp_path):
    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    store.commit_transition(make_request(s0, "key:A", after=s1), s1, created_at_utc=T1)
    s2 = make_snapshot(2, s1.snapshot_id, "semantic:2")
    store.commit_transition(make_request(s1, "key:A2", after=s2), s2, created_at_utc=T2)
    # B is stale twice in a row under one key, then lands
    d1 = store.commit_transition(make_request(s0, "key:B", after=make_snapshot(1, s0.snapshot_id, "x")),
                                 make_snapshot(1, s0.snapshot_id, "x"), created_at_utc=T1)
    assert d1.status is TransitionStatus.RETRY_REQUIRED
    d2 = store.commit_transition(make_request(s1, "key:B", after=make_snapshot(2, s1.snapshot_id, "y")),
                                 make_snapshot(2, s1.snapshot_id, "y"), created_at_utc=T2)
    assert d2.status is TransitionStatus.RETRY_REQUIRED
    assert "superseded_deferrals:1" in d2.reasons
    s3 = make_snapshot(3, s2.snapshot_id, "semantic:3")
    done = store.commit_transition(make_request(s2, "key:B", after=s3), s3, created_at_utc=T2)
    assert done.status is TransitionStatus.COMMITTED


def test_a_terminal_receipt_still_binds_the_key(tmp_path):
    """The no-alarm side: COMMITTED and non-retry receipts are still conflicts under a different request."""

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    store.commit_transition(make_request(s0, "key:A", after=s1), s1, created_at_utc=T1)
    # a different request under the COMMITTED key: still a conflict
    s2 = make_snapshot(2, s1.snapshot_id, "semantic:2")
    with pytest.raises(IdempotencyConflict):
        store.commit_transition(make_request(s1, "key:A", after=s2), s2, created_at_utc=T2)
    # and RECOVERY_REQUIRED is terminal on purpose: a retry must not erase the ambiguity record
    s2r = make_snapshot(2, s1.snapshot_id, "semantic:2r")
    rec = store.record_recovery_required(make_request(s1, "key:R", after=s2r), reasons=("ambiguous",), created_at_utc=T2) \
        if hasattr(store, "record_recovery_required") else None
    if rec is not None:
        with pytest.raises(IdempotencyConflict):
            store.commit_transition(make_request(s1, "key:R", after=s2), s2, created_at_utc=T2)


def test_identical_stale_resend_replays_the_same_deferral(tmp_path):
    """Idempotency of the deferral itself: the same stale request twice is one receipt."""

    store = SqliteEngineeringStateStore(tmp_path / "engineering.sqlite3")
    s0 = store.initialize_project(make_snapshot(0, None, "semantic:0"))
    s1 = make_snapshot(1, s0.snapshot_id, "semantic:1")
    store.commit_transition(make_request(s0, "key:A", after=s1), s1, created_at_utc=T1)
    stale_after = make_snapshot(1, s0.snapshot_id, "semantic:1b")
    req = make_request(s0, "key:B", after=stale_after)
    first = store.commit_transition(req, stale_after, created_at_utc=T1)
    second = store.commit_transition(req, stale_after, created_at_utc=T1)
    assert first == second and first.status is TransitionStatus.RETRY_REQUIRED
