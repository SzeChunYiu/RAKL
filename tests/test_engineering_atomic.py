import sqlite3

import pytest

from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator
from rakl.engineering_semantic_store import SemanticAtomVersion, SemanticFiber, SemanticMutationBatch
from rakl.engineering_state import ProjectSnapshot, StateTransitionRequest, TransitionStatus
from rakl.engineering_store import EngineeringIntegrityError

T0="2026-08-15T15:00:00+00:00"; T1="2026-08-15T15:01:00+00:00"


def initial(coordinator):
    revision = coordinator.semantic.semantic_revision(0)
    return ProjectSnapshot(
        project_id="p", sequence=0, previous_snapshot_id=None,
        evidence_cutoff=coordinator.evidence.evidence_revision("p", 0), semantic_state_revision=revision,
        metric_ledger_head="m0", episode_store_head="ep0", saturation_basis_ids=("b0",),
        authority_projection_revision="a0", controller_epoch_id="epoch0", created_at_utc=T0,
    )


def batch(coordinator):
    return SemanticMutationBatch(
        sequence=1,
        base_semantic_revision=coordinator.semantic.semantic_revision(0),
        new_fibers=(SemanticFiber("fiber:root", created_from_sequence=1),),
        atom_versions=(SemanticAtomVersion(
            atom_id="a", fiber_id="fiber:root", kind="MECHANISM_NODE", label="a",
            evidence_ids=("e:a",), payload={}, valid_from_sequence=1,
        ),),
    )


def after_from_batch(coordinator, s0, b):
    revision = coordinator.semantic.preview_batch_revision(b)
    return ProjectSnapshot(
        project_id="p", sequence=1, previous_snapshot_id=s0.snapshot_id,
        evidence_cutoff=s0.evidence_cutoff, semantic_state_revision=revision,
        metric_ledger_head=s0.metric_ledger_head, episode_store_head=s0.episode_store_head, saturation_basis_ids=s0.saturation_basis_ids,
        authority_projection_revision=s0.authority_projection_revision, controller_epoch_id=s0.controller_epoch_id, created_at_utc=T1,
    )


def request(coordinator, s0, b, key="k"):
    return StateTransitionRequest(
        project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
        action_payload_hash=coordinator.semantic_action_payload_hash(b), idempotency_key=key,
        process_identity="worker:1", read_set=("semantic",), write_set=("semantic",),
        created_at_utc=T1,
    )


def test_semantic_batch_snapshot_and_receipt_commit_atomically(tmp_path):
    c=SqliteAtomicEngineeringCoordinator(tmp_path/"unified.sqlite3")
    s0=c.initialize_empty_project(initial(c)); b=batch(c); s1=after_from_batch(c,s0,b); r=request(c,s0,b)
    result=c.commit_semantic_transition(r,b,s1,created_at_utc=T1)
    assert result.transition_receipt.status is TransitionStatus.COMMITTED
    assert c.state.head("p") == s1
    assert c.semantic.semantic_revision(1) == s1.semantic_state_revision
    assert result.semantic_commit.committed_snapshot_id == s1.snapshot_id
    replay=c.commit_semantic_transition(r,b,s1,created_at_utc=T1)
    assert replay == result


def test_atomic_transition_rolls_back_semantic_batch_when_after_snapshot_invalid(tmp_path):
    path=tmp_path/"unified.sqlite3"; c=SqliteAtomicEngineeringCoordinator(path)
    s0=c.initialize_empty_project(initial(c)); b=batch(c); good=after_from_batch(c,s0,b)
    bad=ProjectSnapshot(
        project_id=good.project_id, sequence=good.sequence, previous_snapshot_id=good.previous_snapshot_id,
        evidence_cutoff=good.evidence_cutoff, semantic_state_revision="semantic:wrong",
        metric_ledger_head=good.metric_ledger_head, episode_store_head=good.episode_store_head,
        saturation_basis_ids=good.saturation_basis_ids, authority_projection_revision=good.authority_projection_revision,
        controller_epoch_id=good.controller_epoch_id, created_at_utc=good.created_at_utc,
    )
    with pytest.raises(EngineeringIntegrityError, match="batch preview"):
        c.commit_semantic_transition(request(c,s0,b),b,bad,created_at_utc=T1)
    assert c.state.head("p") == s0
    assert c.semantic.atom_versions_at(1) == ()
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM semantic_batch_commits").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] == 0


def test_action_payload_hash_must_bind_exact_semantic_batch(tmp_path):
    c=SqliteAtomicEngineeringCoordinator(tmp_path/"unified.sqlite3")
    s0=c.initialize_empty_project(initial(c)); b=batch(c); s1=after_from_batch(c,s0,b)
    wrong=StateTransitionRequest(
        project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
        action_payload_hash="f"*64, idempotency_key="k", process_identity="worker:1",
        read_set=("semantic",), write_set=("semantic",), created_at_utc=T1,
    )
    with pytest.raises(EngineeringIntegrityError, match="does not bind"):
        c.commit_semantic_transition(wrong,b,s1,created_at_utc=T1)


def test_concurrent_atomic_semantic_writers_commit_once_and_retry_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path = tmp_path / "unified.sqlite3"
    c0 = SqliteAtomicEngineeringCoordinator(path)
    s0 = c0.initialize_empty_project(initial(c0))

    def make_batch(name):
        c = SqliteAtomicEngineeringCoordinator(path)
        b = SemanticMutationBatch(
            sequence=1,
            base_semantic_revision=c.semantic.semantic_revision(0),
            new_fibers=(SemanticFiber(f"fiber:{name}", created_from_sequence=1),),
            atom_versions=(SemanticAtomVersion(
                atom_id=f"atom:{name}", fiber_id=f"fiber:{name}", kind="MECHANISM_NODE",
                label=name, evidence_ids=(f"e:{name}",), payload={}, valid_from_sequence=1,
            ),),
        )
        revision = c.semantic.preview_batch_revision(b)
        after = ProjectSnapshot(
            project_id="p", sequence=1, previous_snapshot_id=s0.snapshot_id,
            evidence_cutoff=s0.evidence_cutoff, semantic_state_revision=revision,
            metric_ledger_head=s0.metric_ledger_head, episode_store_head=s0.episode_store_head, saturation_basis_ids=s0.saturation_basis_ids,
            authority_projection_revision=s0.authority_projection_revision, controller_epoch_id=s0.controller_epoch_id, created_at_utc=T1,
        )
        req = StateTransitionRequest(
            project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
            action_payload_hash=c.semantic_action_payload_hash(b), idempotency_key=f"k:{name}",
            process_identity=f"worker:{name}", read_set=("semantic",), write_set=("semantic",),
            created_at_utc=T1,
        )
        return c, b, after, req

    work = {name: make_batch(name) for name in ("left", "right")}

    def run(name):
        c, b, after, req = work[name]
        return name, c.commit_semantic_transition(req, b, after, created_at_utc=T1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = dict(pool.map(run, ("left", "right")))

    statuses = sorted(result.transition_receipt.status.value for result in results.values())
    assert statuses == ["COMMITTED", "RETRY_REQUIRED"]

    winner = next(name for name, result in results.items() if result.transition_receipt.status is TransitionStatus.COMMITTED)
    loser = "right" if winner == "left" else "left"
    current = SqliteAtomicEngineeringCoordinator(path)
    assert current.state.head("p").snapshot_id == work[winner][2].snapshot_id
    assert current.semantic.semantic_revision(1) == work[winner][2].semantic_state_revision
    assert current.semantic.batch_commit(work[winner][1].batch_id) is not None
    assert current.semantic.batch_commit(work[loser][1].batch_id) is None


def test_pure_semantic_transition_cannot_smuggle_other_head_changes(tmp_path):
    c=SqliteAtomicEngineeringCoordinator(tmp_path/"unified.sqlite3")
    s0=c.initialize_empty_project(initial(c)); b=batch(c); good=after_from_batch(c,s0,b)
    bad=ProjectSnapshot(
        project_id=good.project_id, sequence=good.sequence, previous_snapshot_id=good.previous_snapshot_id,
        evidence_cutoff="evidence-revision:smuggled", semantic_state_revision=good.semantic_state_revision,
        metric_ledger_head=good.metric_ledger_head, episode_store_head=good.episode_store_head,
        saturation_basis_ids=good.saturation_basis_ids, authority_projection_revision=good.authority_projection_revision,
        controller_epoch_id=good.controller_epoch_id, created_at_utc=good.created_at_utc,
    )
    with pytest.raises(EngineeringIntegrityError,match="unexpectedly changes evidence_cutoff"):
        c.commit_semantic_transition(request(c,s0,b),b,bad,created_at_utc=T1)
    assert c.state.head("p") == s0
    assert c.semantic.batch_commit(b.batch_id) is None
