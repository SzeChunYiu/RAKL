"""Atlas plane persistence — engineering fiber E3.

The residual was that the chart/transition/obstruction plane is not persisted
atomically. The load-bearing test is therefore the failure case: when a write
fails partway, nothing from that batch may survive.
"""

from __future__ import annotations

import sqlite3

import pytest

from rakl.engineering_atlas_store import (
    ATLAS_GENESIS_REVISION,
    AtlasChartRecord,
    AtlasObstructionRecord,
    AtlasPlaneBatch,
    AtlasTransitionRecord,
    SqliteAtlasPlaneStore,
    atlas_action_payload_hash,
    atlas_revision_for,
)
from rakl.engineering_store import EngineeringIntegrityError


def plane(
    batch_id: str = "b1", *, sequence: int = 1, base: str = ATLAS_GENESIS_REVISION
) -> AtlasPlaneBatch:
    return AtlasPlaneBatch(
        sequence=sequence,
        base_atlas_revision=base,
        batch_id=batch_id,
        charts=(
            AtlasChartRecord("c1", "structural", ("x", "y")),
            AtlasChartRecord("c2", "structural", ("y", "z")),
        ),
        transitions=(AtlasTransitionRecord("t1", "c1", "c2", "CONSISTENT"),),
        obstructions=(AtlasObstructionRecord("o1", "t1", "CYCLE_INCONSISTENCY"),),
    )


@pytest.fixture()
def store(tmp_path) -> SqliteAtlasPlaneStore:
    return SqliteAtlasPlaneStore(tmp_path / "atlas.db")


# --- the residual itself ----------------------------------------------------


def test_the_whole_plane_commits_together(store) -> None:
    commit = store.commit_batch(plane(), committed_snapshot_id="snap-1", expected_atlas_revision="")
    assert (commit.chart_count, commit.transition_count, commit.obstruction_count) == (2, 1, 1)
    counts = store.plane_counts()
    assert counts["atlas_charts"] == 2
    assert counts["atlas_transitions"] == 1
    assert counts["atlas_obstructions"] == 1


def test_a_failure_partway_leaves_nothing_behind(store) -> None:
    """The load-bearing case: a half-written plane describes an atlas that never existed.

    The failure is induced through a real constraint rather than a patched
    driver: a second batch reuses an obstruction id that is already committed,
    so its INSERT fails *after* its own charts and transitions have been written
    inside the same transaction. If those survive, the plane is not atomic.
    """

    first = store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    before = store.plane_counts()

    colliding = AtlasPlaneBatch(
        sequence=2,
        base_atlas_revision=first.atlas_revision,  # honest base: only the collision can fail it
        batch_id="b2",
        charts=(AtlasChartRecord("c9", "structural"), AtlasChartRecord("c8", "structural")),
        transitions=(AtlasTransitionRecord("t9", "c9", "c8"),),
        # o1 is already committed by b1: this insert must fail.
        obstructions=(AtlasObstructionRecord("o1", "t9"),),
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.commit_batch(colliding, committed_snapshot_id="snap-2", expected_atlas_revision="")

    after = store.plane_counts()
    assert after == before, "the failed batch left rows behind"
    assert store.batch_commit("b2") is None


# --- referential integrity, checked before any write ------------------------


def test_a_transition_must_reference_charts_the_batch_carries() -> None:
    with pytest.raises(EngineeringIntegrityError, match="does not carry"):
        AtlasPlaneBatch(
            sequence=1,
            base_atlas_revision="rev-0",
            batch_id="bad",
            charts=(AtlasChartRecord("c1", "structural"),),
            transitions=(AtlasTransitionRecord("t1", "c1", "c-missing"),),
        )


def test_an_obstruction_must_reference_a_transition_the_batch_carries() -> None:
    with pytest.raises(EngineeringIntegrityError, match="does not carry"):
        AtlasPlaneBatch(
            sequence=1,
            base_atlas_revision="rev-0",
            batch_id="bad",
            charts=(AtlasChartRecord("c1", "structural"), AtlasChartRecord("c2", "structural")),
            transitions=(AtlasTransitionRecord("t1", "c1", "c2"),),
            obstructions=(AtlasObstructionRecord("o1", "t-missing"),),
        )


def test_ids_are_unique_within_a_batch() -> None:
    for kwargs, match in (
        ({"charts": (AtlasChartRecord("c1", "s"), AtlasChartRecord("c1", "s"))}, "chart ids"),
        (
            {
                "charts": (AtlasChartRecord("c1", "s"), AtlasChartRecord("c2", "s")),
                "transitions": (
                    AtlasTransitionRecord("t1", "c1", "c2"),
                    AtlasTransitionRecord("t1", "c2", "c1"),
                ),
            },
            "transition ids",
        ),
    ):
        with pytest.raises(ValueError, match=match):
            AtlasPlaneBatch(sequence=1, base_atlas_revision="r", batch_id="b", **kwargs)


# --- idempotency, mirroring the semantic store -----------------------------


def test_replaying_the_same_batch_returns_the_existing_commit(store) -> None:
    first = store.commit_batch(plane(), committed_snapshot_id="snap-1", expected_atlas_revision="")
    second = store.commit_batch(plane(), committed_snapshot_id="snap-2", expected_atlas_revision="")
    assert second.committed_snapshot_id == first.committed_snapshot_id == "snap-1"
    assert store.plane_counts()["atlas_charts"] == 2  # not doubled


def test_a_different_payload_under_the_same_batch_id_is_a_conflict(store) -> None:
    store.commit_batch(plane(), committed_snapshot_id="snap-1", expected_atlas_revision="")
    other = AtlasPlaneBatch(
        sequence=1,
        base_atlas_revision=ATLAS_GENESIS_REVISION,
        batch_id="b1",
        charts=(AtlasChartRecord("cX", "structural"),),
    )
    with pytest.raises(EngineeringIntegrityError, match="different atlas plane payload"):
        store.commit_batch(other, committed_snapshot_id="snap-2", expected_atlas_revision="")


def test_a_wrong_expected_revision_is_refused(store) -> None:
    with pytest.raises(EngineeringIntegrityError, match="expected atlas revision"):
        store.commit_batch(
            plane(), committed_snapshot_id="snap-1", expected_atlas_revision="not-the-revision"
        )
    assert store.plane_counts()["atlas_plane_commits"] == 0


# --- identity ---------------------------------------------------------------


def test_revision_is_deterministic_and_content_sensitive() -> None:
    a = atlas_revision_for(1, plane())
    assert a == atlas_revision_for(1, plane())
    assert a != atlas_revision_for(2, plane(sequence=2))
    assert a != atlas_revision_for(1, plane("b2"))
    assert a != ATLAS_GENESIS_REVISION


def test_action_payload_hash_binds_the_batch() -> None:
    assert atlas_action_payload_hash(plane("b1")) != atlas_action_payload_hash(plane("b2"))


def test_batch_commit_lookup_round_trips(store) -> None:
    assert store.batch_commit("absent") is None
    store.commit_batch(plane(), committed_snapshot_id="snap-1", expected_atlas_revision="")
    found = store.batch_commit("b1")
    assert found is not None
    assert found.chart_count == 2


# --- compare-and-swap on the base revision (CROSS_PLANE_ATTACKS_V1 X11) ------


def test_a_stale_base_revision_is_refused_and_writes_nothing(store) -> None:
    """Before the fix a batch declaring the pre-b1 base committed after b1."""

    store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    before = store.plane_counts()
    stale = AtlasPlaneBatch(
        sequence=2,
        base_atlas_revision=ATLAS_GENESIS_REVISION,  # planned against a plane that no longer exists
        batch_id="b2",
        charts=(AtlasChartRecord("c3", "structural"),),
    )
    with pytest.raises(EngineeringIntegrityError, match="atlas batch base revision is stale"):
        store.commit_batch(stale, committed_snapshot_id="snap-2", expected_atlas_revision="")
    assert store.plane_counts() == before
    assert store.batch_commit("b2") is None


def test_first_batch_must_declare_the_genesis_revision(store) -> None:
    with pytest.raises(EngineeringIntegrityError, match="atlas batch base revision is stale"):
        store.commit_batch(plane(base="rev-0"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    assert store.plane_counts()["atlas_plane_commits"] == 0
    assert store.current_atlas_revision() == ATLAS_GENESIS_REVISION
    assert store.current_sequence() == 0


def test_expected_atlas_revision_alone_cannot_stand_in_for_the_base_cas(store) -> None:
    """expected_atlas_revision is recomputed from the batch, so it agrees with any base."""

    store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    stale = AtlasPlaneBatch(
        sequence=2, base_atlas_revision=ATLAS_GENESIS_REVISION, batch_id="b2",
        charts=(AtlasChartRecord("c3", "structural"),),
    )
    self_consistent = atlas_revision_for(2, stale)
    with pytest.raises(EngineeringIntegrityError, match="base revision is stale"):
        store.commit_batch(stale, committed_snapshot_id="snap-2", expected_atlas_revision=self_consistent)


def test_two_writers_planning_against_the_same_base_cannot_both_commit(store) -> None:
    first = store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    writer_a = AtlasPlaneBatch(2, first.atlas_revision, "b-a", charts=(AtlasChartRecord("ca", "s"),))
    writer_b = AtlasPlaneBatch(2, first.atlas_revision, "b-b", charts=(AtlasChartRecord("cb", "s"),))
    store.commit_batch(writer_a, committed_snapshot_id="snap-2", expected_atlas_revision="")
    with pytest.raises(EngineeringIntegrityError):
        store.commit_batch(writer_b, committed_snapshot_id="snap-2", expected_atlas_revision="")
    assert store.batch_commit("b-b") is None
    assert store.current_sequence() == 2


# --- monotonic sequence (CROSS_PLANE_ATTACKS_V1 X12) ---------------------------


def test_sequence_rewind_from_an_established_position_is_refused(store) -> None:
    """Before the fix a batch at sequence 1 committed after sequences 1 and 2."""

    c1 = store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    c2 = store.commit_batch(
        AtlasPlaneBatch(2, c1.atlas_revision, "b2", charts=(AtlasChartRecord("c3", "s"),)),
        committed_snapshot_id="snap-2", expected_atlas_revision="",
    )
    before = store.plane_counts()
    rewind = AtlasPlaneBatch(1, c2.atlas_revision, "b3", charts=(AtlasChartRecord("c4", "s"),))
    with pytest.raises(EngineeringIntegrityError, match="advance the plane exactly once"):
        store.commit_batch(rewind, committed_snapshot_id="snap-3", expected_atlas_revision="")
    assert store.plane_counts() == before
    assert store.current_sequence() == 2


def test_sequence_skip_is_refused(store) -> None:
    c1 = store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    skip = AtlasPlaneBatch(3, c1.atlas_revision, "b3", charts=(AtlasChartRecord("c4", "s"),))
    with pytest.raises(EngineeringIntegrityError, match="advance the plane exactly once"):
        store.commit_batch(skip, committed_snapshot_id="snap-3", expected_atlas_revision="")
    assert store.current_sequence() == 1


def test_batch_sequence_zero_is_not_a_mutation() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        AtlasPlaneBatch(0, ATLAS_GENESIS_REVISION, "b0", charts=(AtlasChartRecord("c", "s"),))


# --- no-alarm: the honest chain still commits and replays ---------------------


def test_an_honest_chain_of_batches_commits_and_replays_idempotently(store) -> None:
    c1 = store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    assert store.current_atlas_revision() == c1.atlas_revision
    b2 = AtlasPlaneBatch(2, store.current_atlas_revision(), "b2", charts=(AtlasChartRecord("c3", "s"),))
    c2 = store.commit_batch(b2, committed_snapshot_id="snap-2", expected_atlas_revision=atlas_revision_for(2, b2))
    assert store.current_sequence() == 2 and store.current_atlas_revision() == c2.atlas_revision
    # replaying an already-committed batch (now behind the head) is idempotent, not stale
    assert store.commit_batch(plane("b1"), committed_snapshot_id="ignored", expected_atlas_revision="") == c1
    assert store.plane_counts()["atlas_plane_commits"] == 2


def test_pre_cas_database_is_migrated_and_position_recovered(tmp_path) -> None:
    """A database created by the previous schema (no sequence column) must open and CAS."""

    path = tmp_path / "old-atlas.db"
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE atlas_plane_commits (
            batch_id TEXT PRIMARY KEY, committed_snapshot_id TEXT NOT NULL,
            atlas_revision TEXT NOT NULL, chart_count INTEGER NOT NULL,
            transition_count INTEGER NOT NULL, obstruction_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL);
        CREATE TABLE atlas_charts (chart_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL,
            layer TEXT NOT NULL, payload_json TEXT NOT NULL);
        CREATE TABLE atlas_transitions (transition_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL,
            source_chart_id TEXT NOT NULL, target_chart_id TEXT NOT NULL, payload_json TEXT NOT NULL);
        CREATE TABLE atlas_obstructions (obstruction_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL,
            transition_id TEXT NOT NULL, payload_json TEXT NOT NULL);
        """
    )
    old = AtlasPlaneBatch(1, ATLAS_GENESIS_REVISION, "legacy", charts=(AtlasChartRecord("c1", "s"),))
    import json as _json
    db.execute(
        "INSERT INTO atlas_plane_commits VALUES (?,?,?,?,?,?,?)",
        ("legacy", "snap-legacy", atlas_revision_for(1, old), 1, 0, 0,
         _json.dumps(old.payload(), sort_keys=True, separators=(",", ":"))),
    )
    db.commit(); db.close()

    store = SqliteAtlasPlaneStore(path)
    assert store.current_sequence() == 1
    assert store.current_atlas_revision() == atlas_revision_for(1, old)
    nxt = AtlasPlaneBatch(2, store.current_atlas_revision(), "b2", charts=(AtlasChartRecord("c2", "s"),))
    store.commit_batch(nxt, committed_snapshot_id="snap-2", expected_atlas_revision="")
    assert store.current_sequence() == 2
