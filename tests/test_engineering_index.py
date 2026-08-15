"""H13/H14: the rebuildable index is disposable AND fails closed on referential corruption.

Both directions: ghost atoms are refused (construction, swap-in, mutation, failed verify) and an
honest rebuilt index is served.
"""

from __future__ import annotations

import pytest

from rakl.engineering_index import (
    IndexedAtom, IndexIntegrityError, IndexVerdict, RebuildableSemanticIndex, SemanticIndexSnapshot,
)
from rakl.engineering_semantic_store import (
    SemanticAtomVersion, SemanticFiber, SemanticMutationBatch, SqliteSemanticStateStore,
)


def _store(tmp_path) -> SqliteSemanticStateStore:
    store = SqliteSemanticStateStore(tmp_path / "sem.db")
    batch = SemanticMutationBatch(
        sequence=1, base_semantic_revision=store.semantic_revision(0),
        new_fibers=(SemanticFiber("fiber:a", created_from_sequence=1),),
        atom_versions=(
            SemanticAtomVersion(atom_id="atom:a", fiber_id="fiber:a", kind="MECHANISM_NODE", label="alpha",
                                evidence_ids=("e:a",), payload={}, valid_from_sequence=1),
            SemanticAtomVersion(atom_id="atom:b", fiber_id="fiber:a", kind="MECHANISM_NODE", label="beta",
                                evidence_ids=("e:b",), payload={}, valid_from_sequence=1),
        ),
    )
    store.commit_batch(batch, committed_snapshot_id="snapshot:" + "1" * 64,
                       expected_semantic_revision=store.preview_batch_revision(batch))
    return store


GHOST = IndexedAtom("atom:ghost", "ver:ghost", "fiber:a", "MECHANISM_NODE", "alpha ghost")


# --- identity ------------------------------------------------------------------


def test_snapshot_id_is_content_derived_and_verified() -> None:
    a = SemanticIndexSnapshot("rev", (GHOST,))
    assert a.index_id.startswith("semantic-index:")
    assert SemanticIndexSnapshot("rev", (GHOST,), a.index_id) == a
    with pytest.raises(ValueError, match="index_id does not match"):
        SemanticIndexSnapshot("rev", (), a.index_id)


def test_forged_snapshot_under_real_id_is_refused(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    real = idx.rebuild(store, sequence=1)
    with pytest.raises(ValueError):
        SemanticIndexSnapshot(real.semantic_revision, real.indexed_atoms + (GHOST,), real.index_id)


def test_snapshot_refuses_duplicate_atoms() -> None:
    with pytest.raises(ValueError, match="twice"):
        SemanticIndexSnapshot("rev", (GHOST, GHOST))


# --- H13: disposable ---------------------------------------------------------


def test_cleared_index_is_empty_and_rebuild_is_identity_stable(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    first = idx.rebuild(store, sequence=1)
    idx.clear()
    assert idx.snapshot is None
    assert idx.exact_filter(fiber_ids=("fiber:a",)) == ()
    assert idx.lexical("alpha") == ()
    assert store.latest_atom_version("atom:a") is not None
    assert idx.rebuild(store, sequence=1).index_id == first.index_id


# --- H14: referential integrity ---------------------------------------------


def test_swapped_in_ghost_projection_is_refused_until_verified_and_verify_names_it(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    real = idx.rebuild(store, sequence=1)
    idx._snapshot = SemanticIndexSnapshot(real.semantic_revision, real.indexed_atoms + (GHOST,))
    with pytest.raises(IndexIntegrityError, match="changed since it was verified"):
        idx.exact_filter(fiber_ids=("fiber:a",))
    v = idx.verify(store)
    assert v.verdict is IndexVerdict.GHOST_ATOMS
    assert v.ghost_atom_ids == ("atom:ghost",)
    with pytest.raises(IndexIntegrityError, match="GHOST_ATOMS"):
        idx.exact_filter(fiber_ids=("fiber:a",))
    with pytest.raises(IndexIntegrityError, match="GHOST_ATOMS"):
        idx.lexical("ghost")


def test_atoms_mutated_behind_a_verified_id_are_refused(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    idx.rebuild(store, sequence=1)
    object.__setattr__(idx._snapshot, "indexed_atoms", idx._snapshot.indexed_atoms + (GHOST,))
    with pytest.raises(IndexIntegrityError, match="identity mismatch"):
        idx.lexical("ghost")
    assert idx.verification is not None and idx.verification.verdict is IndexVerdict.IDENTITY_MISMATCH


def test_verify_on_unbuilt_index_is_not_built_not_ok(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    assert idx.verify(store).verdict is IndexVerdict.NOT_BUILT


# --- no-alarm ------------------------------------------------------------------


def test_rebuilt_index_is_verified_and_served(tmp_path) -> None:
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    idx.rebuild(store, sequence=1)
    assert idx.verification is not None and idx.verification.ok
    assert idx.verify(store).ok
    assert {a.atom_id for a in idx.exact_filter(fiber_ids=("fiber:a",))} == {"atom:a", "atom:b"}
    assert [a.atom_id for a in idx.lexical("alpha")] == ["atom:a"]
    assert idx.exact_filter(kinds=("NOPE",)) == ()


def test_index_at_an_older_version_is_lag_not_ghost(tmp_path) -> None:
    """A real atom indexed at an earlier version is stale (probe_index's DEGRADED), not a ghost."""
    store = _store(tmp_path)
    idx = RebuildableSemanticIndex()
    idx.rebuild(store, sequence=1)
    b2 = SemanticMutationBatch(
        sequence=2, base_semantic_revision=store.semantic_revision(1), new_fibers=(),
        atom_versions=(SemanticAtomVersion(
            atom_id="atom:a", fiber_id="fiber:a", kind="MECHANISM_NODE", label="alpha v2", evidence_ids=("e:a2",),
            payload={}, valid_from_sequence=2, supersedes_version_id=store.latest_atom_version("atom:a").version_id),),
    )
    store.commit_batch(b2, committed_snapshot_id="snapshot:" + "2" * 64,
                       expected_semantic_revision=store.preview_batch_revision(b2))
    v = idx.verify(store)
    assert v.ok and "older version" in v.detail
    assert [a.atom_id for a in idx.lexical("alpha")] == ["atom:a"]
