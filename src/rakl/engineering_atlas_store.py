"""Atomic persistence for the Atlas chart/transition/obstruction plane.

Closes engineering fiber E3, whose residual read:

    local_reference_does_not_yet_persist_full_Atlas_chart_transition_obstruction_plane_atomically

The three objects are one plane, not three tables that happen to be related. A
chart whose overlap transitions are missing describes a cover that was never
checked; an obstruction certificate without the transition it refutes is
unattributable. Persisting any one without the others leaves the store
describing an atlas that never existed, so the batch commits whole or not at
all.

Mirrors `engineering_semantic_store` deliberately: same batch/commit shape, same
`BEGIN IMMEDIATE` transaction discipline, same idempotent-replay contract, and —
since the cross-plane campaign (CROSS_PLANE_ATTACKS_V1 X11/X12) showed it was
missing — the same compare-and-swap on the base revision plus a monotonic
sequence check. A second store that invents its own transactional semantics is
a second thing to get wrong.

Plane position and revision are stored per commit. A batch is admitted only if

    batch.sequence            == stored max sequence + 1   (1 on an empty plane)
    batch.base_atlas_revision == stored revision at that max (ATLAS_GENESIS_REVISION
                                                            on an empty plane)

``expected_atlas_revision`` remains a self-consistency check on the batch the
caller thinks it is committing; it is recomputed from the batch and therefore
cannot detect a stale base by itself.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping, Sequence

from .engineering_schema_guard import guard_and_initialize_schema
from .engineering_state import canonical_sha256
from .engineering_store import EngineeringIntegrityError


@dataclass(frozen=True)
class AtlasChartRecord:
    """One chart of the atlas: a locally valid region with its own coordinates."""

    chart_id: str
    layer: str
    coordinates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "chart_id": self.chart_id,
            "layer": self.layer,
            "coordinates": list(self.coordinates),
        }


@dataclass(frozen=True)
class AtlasTransitionRecord:
    """An overlap transition between two charts."""

    transition_id: str
    source_chart_id: str
    target_chart_id: str
    verdict: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "transition_id": self.transition_id,
            "source_chart_id": self.source_chart_id,
            "target_chart_id": self.target_chart_id,
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class AtlasObstructionRecord:
    """A certificate that some transition cannot be glued."""

    obstruction_id: str
    transition_id: str
    obstruction_type: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "obstruction_id": self.obstruction_id,
            "transition_id": self.transition_id,
            "obstruction_type": self.obstruction_type,
        }


@dataclass(frozen=True)
class AtlasPlaneBatch:
    """One all-or-nothing mutation of the atlas plane."""

    sequence: int
    base_atlas_revision: str
    batch_id: str
    charts: tuple[AtlasChartRecord, ...] = ()
    transitions: tuple[AtlasTransitionRecord, ...] = ()
    obstructions: tuple[AtlasObstructionRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.batch_id:
            raise ValueError("atlas batch requires an id")
        if self.sequence < 1:
            # Sequence 0 is the empty plane (ATLAS_GENESIS_REVISION); the first
            # mutation is sequence 1, as in the evidence store.
            raise ValueError("atlas batch sequence must be >= 1")

        chart_ids = {c.chart_id for c in self.charts}
        if len(chart_ids) != len(self.charts):
            raise ValueError("chart ids must be unique within a batch")

        transition_ids = {t.transition_id for t in self.transitions}
        if len(transition_ids) != len(self.transitions):
            raise ValueError("transition ids must be unique within a batch")

        obstruction_ids = {o.obstruction_id for o in self.obstructions}
        if len(obstruction_ids) != len(self.obstructions):
            raise ValueError("obstruction ids must be unique within a batch")

        # Referential integrity is checked here, before any write, because the
        # whole point of this fiber is that the plane is never half-written.
        for t in self.transitions:
            for end in (t.source_chart_id, t.target_chart_id):
                if end not in chart_ids:
                    raise EngineeringIntegrityError(
                        f"transition {t.transition_id!r} references chart {end!r} "
                        "that the batch does not carry"
                    )
        for o in self.obstructions:
            if o.transition_id not in transition_ids:
                raise EngineeringIntegrityError(
                    f"obstruction {o.obstruction_id!r} references transition "
                    f"{o.transition_id!r} that the batch does not carry"
                )

    def payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "base_atlas_revision": self.base_atlas_revision,
            "batch_id": self.batch_id,
            "charts": [c.to_dict() for c in self.charts],
            "transitions": [t.to_dict() for t in self.transitions],
            "obstructions": [o.to_dict() for o in self.obstructions],
        }

    @property
    def is_empty(self) -> bool:
        return not (self.charts or self.transitions or self.obstructions)


@dataclass(frozen=True)
class AtlasPlaneCommit:
    """Receipt of one committed plane mutation."""

    batch_id: str
    committed_snapshot_id: str
    atlas_revision: str
    chart_count: int
    transition_count: int
    obstruction_count: int


def atlas_revision_for(sequence: int, batch: AtlasPlaneBatch) -> str:
    """Revision identity of the plane after applying ``batch``."""

    return canonical_sha256({"sequence": sequence, "plane": batch.payload()})


#: Revision of the empty plane, i.e. the base every first batch must declare.
#: Mirrors ``SqliteSemanticStateStore.semantic_revision(0)``: the identity of
#: "sequence 0, nothing applied", derived by the same function that names every
#: later revision, so a genesis marker cannot collide with a real revision.
ATLAS_GENESIS_REVISION: str = canonical_sha256({"sequence": 0, "plane": None})



_SCHEMA_SQL = """
                CREATE TABLE IF NOT EXISTS atlas_plane_commits (
                    batch_id TEXT PRIMARY KEY,
                    sequence INTEGER NOT NULL,
                    committed_snapshot_id TEXT NOT NULL,
                    atlas_revision TEXT NOT NULL,
                    chart_count INTEGER NOT NULL,
                    transition_count INTEGER NOT NULL,
                    obstruction_count INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS atlas_charts (
                    chart_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL REFERENCES atlas_plane_commits(batch_id),
                    layer TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS atlas_transitions (
                    transition_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL REFERENCES atlas_plane_commits(batch_id),
                    source_chart_id TEXT NOT NULL REFERENCES atlas_charts(chart_id),
                    target_chart_id TEXT NOT NULL REFERENCES atlas_charts(chart_id),
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS atlas_obstructions (
                    obstruction_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL REFERENCES atlas_plane_commits(batch_id),
                    transition_id TEXT NOT NULL REFERENCES atlas_transitions(transition_id),
                    payload_json TEXT NOT NULL
                );
                """

class SqliteAtlasPlaneStore:
    """Reference store persisting the atlas plane as one transactional unit."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.execute("COMMIT")
        except Exception:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            db.close()

    def _init_schema(self) -> None:
        db = self._connect()
        try:
            # H21: verify-or-create. A populated database is checked, never repaired (see engineering_schema_guard).
            guard_and_initialize_schema(
                db, component="engineering_atlas_store", schema_version="orion-engineering-atlas-store-v2",
                tables=("atlas_plane_commits", "atlas_charts", "atlas_transitions", "atlas_obstructions"),
                create_script=_SCHEMA_SQL,
            )
            # a typed, backfilling column migration -- explicit, not a silent CREATE-over-populated
            self._migrate_sequence_column(db)
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS atlas_plane_commits_sequence "
                "ON atlas_plane_commits(sequence)"
            )
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _migrate_sequence_column(db: sqlite3.Connection) -> None:
        """Bring a pre-CAS database forward: the sequence used to live only in payload_json.

        Backfilled from the committed payload, which is authoritative for the batch
        that was committed. A pre-CAS database that already contains a sequence
        rewind cannot satisfy the unique index; that failure is surfaced, not
        papered over, because such a plane genuinely holds two states at one position.
        """

        columns = {row["name"] for row in db.execute("PRAGMA table_info(atlas_plane_commits)")}
        if "sequence" in columns:
            return
        db.execute("ALTER TABLE atlas_plane_commits ADD COLUMN sequence INTEGER NOT NULL DEFAULT -1")
        rows = db.execute("SELECT batch_id, payload_json FROM atlas_plane_commits").fetchall()
        for row in rows:
            db.execute(
                "UPDATE atlas_plane_commits SET sequence=? WHERE batch_id=?",
                (int(json.loads(row["payload_json"])["sequence"]), row["batch_id"]),
            )

    @staticmethod
    def _dump(value: Mapping[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def commit_batch(
        self,
        batch: AtlasPlaneBatch,
        *,
        committed_snapshot_id: str,
        expected_atlas_revision: str,
    ) -> AtlasPlaneCommit:
        """Commit the whole plane, or none of it.

        Replaying the same ``batch_id`` returns the existing commit; replaying a
        different batch under the same id is an idempotency conflict, matching
        the semantic store's contract.

        A NEW batch is admitted only against the plane's stored position: its
        sequence must advance the plane exactly once and its
        ``base_atlas_revision`` must equal the stored revision at that position
        (``ATLAS_GENESIS_REVISION`` for an empty plane). Both checks read stored
        state inside the ``BEGIN IMMEDIATE`` transaction, so two writers planning
        against the same base cannot both commit.
        """

        revision = atlas_revision_for(batch.sequence, batch)
        if expected_atlas_revision and expected_atlas_revision != revision:
            raise EngineeringIntegrityError(
                "expected atlas revision does not match the batch's computed revision"
            )

        with self._tx() as db:
            existing = db.execute(
                "SELECT committed_snapshot_id,atlas_revision,chart_count,transition_count,"
                "obstruction_count,payload_json FROM atlas_plane_commits WHERE batch_id=?",
                (batch.batch_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_json"] != self._dump(batch.payload()):
                    raise EngineeringIntegrityError(
                        "batch id already bound to a different atlas plane payload"
                    )
                return AtlasPlaneCommit(
                    batch_id=batch.batch_id,
                    committed_snapshot_id=existing["committed_snapshot_id"],
                    atlas_revision=existing["atlas_revision"],
                    chart_count=existing["chart_count"],
                    transition_count=existing["transition_count"],
                    obstruction_count=existing["obstruction_count"],
                )

            current_sequence, current_revision = self._current_position_db(db)
            if batch.sequence != current_sequence + 1:
                raise EngineeringIntegrityError(
                    "atlas batch sequence must advance the plane exactly once "
                    f"(stored position {current_sequence}, batch declares {batch.sequence})"
                )
            if batch.base_atlas_revision != current_revision:
                raise EngineeringIntegrityError("atlas batch base revision is stale")

            db.execute(
                "INSERT INTO atlas_plane_commits (batch_id,sequence,committed_snapshot_id,"
                "atlas_revision,chart_count,transition_count,obstruction_count,payload_json) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    batch.batch_id,
                    batch.sequence,
                    committed_snapshot_id,
                    revision,
                    len(batch.charts),
                    len(batch.transitions),
                    len(batch.obstructions),
                    self._dump(batch.payload()),
                ),
            )
            for chart in batch.charts:
                db.execute(
                    "INSERT INTO atlas_charts (chart_id,batch_id,layer,payload_json) VALUES (?,?,?,?)",
                    (chart.chart_id, batch.batch_id, chart.layer, self._dump(chart.to_dict())),
                )
            for transition in batch.transitions:
                db.execute(
                    "INSERT INTO atlas_transitions (transition_id,batch_id,source_chart_id,"
                    "target_chart_id,payload_json) VALUES (?,?,?,?,?)",
                    (
                        transition.transition_id,
                        batch.batch_id,
                        transition.source_chart_id,
                        transition.target_chart_id,
                        self._dump(transition.to_dict()),
                    ),
                )
            for obstruction in batch.obstructions:
                db.execute(
                    "INSERT INTO atlas_obstructions (obstruction_id,batch_id,transition_id,"
                    "payload_json) VALUES (?,?,?,?)",
                    (
                        obstruction.obstruction_id,
                        batch.batch_id,
                        obstruction.transition_id,
                        self._dump(obstruction.to_dict()),
                    ),
                )

        return AtlasPlaneCommit(
            batch_id=batch.batch_id,
            committed_snapshot_id=committed_snapshot_id,
            atlas_revision=revision,
            chart_count=len(batch.charts),
            transition_count=len(batch.transitions),
            obstruction_count=len(batch.obstructions),
        )

    @staticmethod
    def _current_position_db(db: sqlite3.Connection) -> tuple[int, str]:
        """(stored max sequence, revision at it); (0, ATLAS_GENESIS_REVISION) when empty."""

        row = db.execute(
            "SELECT sequence, atlas_revision FROM atlas_plane_commits ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return 0, ATLAS_GENESIS_REVISION
        return int(row["sequence"]), str(row["atlas_revision"])

    def current_atlas_revision(self) -> str:
        """The base revision the NEXT batch must declare."""

        db = self._connect()
        try:
            return self._current_position_db(db)[1]
        finally:
            db.close()

    def current_sequence(self) -> int:
        """The plane's stored position; the next batch must declare this + 1."""

        db = self._connect()
        try:
            return self._current_position_db(db)[0]
        finally:
            db.close()

    def plane_counts(self) -> dict[str, int]:
        """Row counts per plane table — used to assert nothing was half-written."""

        db = self._connect()
        try:
            return {
                table: db.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for table in ("atlas_plane_commits", "atlas_charts", "atlas_transitions", "atlas_obstructions")
            }
        finally:
            db.close()

    def batch_commit(self, batch_id: str) -> AtlasPlaneCommit | None:
        db = self._connect()
        try:
            row = db.execute(
                "SELECT committed_snapshot_id,atlas_revision,chart_count,transition_count,"
                "obstruction_count FROM atlas_plane_commits WHERE batch_id=?",
                (batch_id,),
            ).fetchone()
        finally:
            db.close()
        if row is None:
            return None
        return AtlasPlaneCommit(
            batch_id=batch_id,
            committed_snapshot_id=row["committed_snapshot_id"],
            atlas_revision=row["atlas_revision"],
            chart_count=row["chart_count"],
            transition_count=row["transition_count"],
            obstruction_count=row["obstruction_count"],
        )


def atlas_action_payload_hash(batch: AtlasPlaneBatch) -> str:
    """Bind a transition request to an atlas batch, as the semantic path does."""

    return canonical_sha256({"atlas_batch_id": batch.batch_id})


__all__ = [
    "ATLAS_GENESIS_REVISION",
    "AtlasChartRecord",
    "AtlasObstructionRecord",
    "AtlasPlaneBatch",
    "AtlasPlaneCommit",
    "AtlasTransitionRecord",
    "SqliteAtlasPlaneStore",
    "atlas_action_payload_hash",
    "atlas_revision_for",
]
