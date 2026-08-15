"""Atlas plane persistence — engineering fiber E3.

The residual was that the chart/transition/obstruction plane is not persisted
atomically. The load-bearing test is therefore the failure case: when a write
fails partway, nothing from that batch may survive.
"""

from __future__ import annotations

import sqlite3

import pytest

from rakl.engineering_atlas_store import (
    AtlasChartRecord,
    AtlasObstructionRecord,
    AtlasPlaneBatch,
    AtlasTransitionRecord,
    SqliteAtlasPlaneStore,
    atlas_action_payload_hash,
    atlas_revision_for,
)
from rakl.engineering_store import EngineeringIntegrityError


def plane(batch_id: str = "b1", *, sequence: int = 1) -> AtlasPlaneBatch:
    return AtlasPlaneBatch(
        sequence=sequence,
        base_atlas_revision="rev-0",
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

    store.commit_batch(plane("b1"), committed_snapshot_id="snap-1", expected_atlas_revision="")
    before = store.plane_counts()

    colliding = AtlasPlaneBatch(
        sequence=2,
        base_atlas_revision="rev-1",
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
        base_atlas_revision="rev-0",
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


def test_action_payload_hash_binds_the_batch() -> None:
    assert atlas_action_payload_hash(plane("b1")) != atlas_action_payload_hash(plane("b2"))


def test_batch_commit_lookup_round_trips(store) -> None:
    assert store.batch_commit("absent") is None
    store.commit_batch(plane(), committed_snapshot_id="snap-1", expected_atlas_revision="")
    found = store.batch_commit("b1")
    assert found is not None
    assert found.chart_count == 2
