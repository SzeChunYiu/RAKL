import pytest

from rakl.engineering_index import RebuildableSemanticIndex
from rakl.engineering_semantic_store import (
    RelationWitnessVersion,
    SemanticAtomVersion,
    SemanticFiber,
    SemanticMutationBatch,
    SqliteSemanticStateStore,
)
from rakl.engineering_store import EngineeringIntegrityError


def atom(atom_id, seq, *, supersedes=None, label=None, fiber="fiber:root", kind="MECHANISM_NODE"):
    return SemanticAtomVersion(
        atom_id=atom_id, fiber_id=fiber, kind=kind, label=label or f"label {atom_id} v{seq}",
        evidence_ids=(f"evidence:{atom_id}:{seq}",), payload={"value": seq},
        valid_from_sequence=seq, supersedes_version_id=supersedes,
    )


def test_semantic_versions_are_append_only_and_revision_is_deterministic(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root"), valid_from_snapshot_id="snapshot:0")
    a0 = store.add_atom_version(atom("a", 0), valid_from_snapshot_id="snapshot:0")
    b0 = store.add_atom_version(atom("b", 0), valid_from_snapshot_id="snapshot:0")
    rev0 = store.semantic_revision(0)
    a1 = store.add_atom_version(atom("a", 1, supersedes=a0.version_id, label="updated mechanism a"), valid_from_snapshot_id="snapshot:1")
    rev1 = store.semantic_revision(1)
    assert rev0 != rev1
    assert [item.version_id for item in store.atom_versions_at(0)] == [a0.version_id, b0.version_id]
    assert [item.version_id for item in store.atom_versions_at(1)] == [a1.version_id, b0.version_id]


def test_atom_identity_cannot_move_fiber_or_skip_supersession_head(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root"), valid_from_snapshot_id="snapshot:0")
    store.add_fiber(SemanticFiber("fiber:other"), valid_from_snapshot_id="snapshot:0")
    a0 = store.add_atom_version(atom("a", 0), valid_from_snapshot_id="snapshot:0")
    with pytest.raises(EngineeringIntegrityError, match="fiber or kind"):
        store.add_atom_version(atom("a", 1, supersedes=a0.version_id, fiber="fiber:other"), valid_from_snapshot_id="snapshot:1")
    with pytest.raises(EngineeringIntegrityError, match="supersede current head"):
        store.add_atom_version(atom("a", 1, supersedes="wrong"), valid_from_snapshot_id="snapshot:1")


def test_relation_witness_requires_existing_atoms_and_version_head(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root"), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(atom("a", 0), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(atom("b", 0), valid_from_snapshot_id="snapshot:0")
    w0 = RelationWitnessVersion(
        witness_id="w:a:b", left_atom_id="a", right_atom_id="b", relation_type="COMPATIBLE",
        reason="known world", condition=None, evidence_ids=("e:w0",), payload={}, valid_from_sequence=0,
    )
    store.add_witness_version(w0, valid_from_snapshot_id="snapshot:0")
    w1 = RelationWitnessVersion(
        witness_id="w:a:b", left_atom_id="a", right_atom_id="b", relation_type="CONDITIONAL",
        reason="new boundary", condition="regime:x", evidence_ids=("e:w1",), payload={},
        valid_from_sequence=1, supersedes_version_id=w0.version_id,
    )
    store.add_witness_version(w1, valid_from_snapshot_id="snapshot:1")
    assert store.witness_versions_at(0)[0].relation_type == "COMPATIBLE"
    assert store.witness_versions_at(1)[0].relation_type == "CONDITIONAL"


def test_rebuildable_index_can_be_deleted_and_recreated_without_semantic_change(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root"), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(atom("a", 0, label="memory kernel mechanism"), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(atom("b", 0, label="observation model"), valid_from_snapshot_id="snapshot:0")
    revision = store.semantic_revision(0)
    index = RebuildableSemanticIndex(); first = index.rebuild(store, sequence=0)
    assert first.semantic_revision == revision
    assert index.lexical("memory mechanism")[0].atom_id == "a"
    index.clear(); assert index.lexical("memory") == ()
    second = index.rebuild(store, sequence=0)
    assert second.index_id == first.index_id
    assert store.semantic_revision(0) == revision


def test_historical_revision_ignores_fibers_created_in_future_snapshots(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root", created_from_sequence=0), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(atom("a", 0), valid_from_snapshot_id="snapshot:0")
    before = store.semantic_revision(0)
    store.add_fiber(SemanticFiber("fiber:future", parent_fiber_id="fiber:root", created_from_sequence=1), valid_from_snapshot_id="snapshot:1")
    assert store.semantic_revision(0) == before
    assert store.semantic_revision(1) != before


def test_child_fiber_cannot_predate_parent(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:parent", created_from_sequence=2), valid_from_snapshot_id="snapshot:2")
    with pytest.raises(EngineeringIntegrityError, match="predate"):
        store.add_fiber(SemanticFiber("fiber:child", parent_fiber_id="fiber:parent", created_from_sequence=1), valid_from_snapshot_id="snapshot:1")


def test_mutation_batch_preview_breaks_snapshot_identity_cycle(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    base = store.semantic_revision(-1)
    batch = SemanticMutationBatch(
        sequence=0,
        base_semantic_revision=base,
        new_fibers=(SemanticFiber("fiber:root", created_from_sequence=0),),
        atom_versions=(atom("a", 0),),
    )
    preview = store.preview_batch_revision(batch)
    assert preview.startswith("semantic-revision:")
    # The after snapshot can now hash `preview`; only after it exists is the batch
    # bound to that snapshot. No semantic version hash depends on snapshot id.
    commit = store.commit_batch(batch, committed_snapshot_id="snapshot:" + "a" * 64, expected_semantic_revision=preview)
    assert commit.semantic_revision == preview
    assert store.semantic_revision(0) == preview


def test_batch_commit_refuses_stale_base_revision(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    with pytest.raises(EngineeringIntegrityError, match="base revision is stale"):
        store.preview_batch_revision(
            SemanticMutationBatch(
                sequence=0, base_semantic_revision="semantic-revision:stale",
                new_fibers=(SemanticFiber("fiber:root"),), atom_versions=(atom("a", 0),),
            )
        )


def test_new_fiber_parent_order_is_canonical_not_caller_order(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    base = store.semantic_revision(0)
    # Child deliberately appears before its new parent.
    batch = SemanticMutationBatch(
        sequence=1,
        base_semantic_revision=base,
        new_fibers=(
            SemanticFiber("fiber:child", "fiber:parent", 1),
            SemanticFiber("fiber:parent", None, 1),
        ),
    )
    preview = store.preview_batch_revision(batch)
    store.commit_batch(
        batch,
        committed_snapshot_id="snapshot:" + "d" * 64,
        expected_semantic_revision=preview,
    )
    assert [f.fiber_id for f in store.fibers_at(1)] == ["fiber:child", "fiber:parent"]
    assert store.semantic_revision(1) == preview


def test_new_fiber_parent_cycle_fails_at_preview_not_database_commit(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    batch = SemanticMutationBatch(
        sequence=1,
        base_semantic_revision=store.semantic_revision(0),
        new_fibers=(
            SemanticFiber("fiber:a", "fiber:b", 1),
            SemanticFiber("fiber:b", "fiber:a", 1),
        ),
    )
    with pytest.raises(EngineeringIntegrityError, match="parent cycle"):
        store.preview_batch_revision(batch)
