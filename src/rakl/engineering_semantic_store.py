"""Transactional reference persistence for the typed semantic knowledge plane.

Semantic content identity is intentionally independent of the *after snapshot id*.
Otherwise a circular identity appears: the snapshot hashes the semantic revision while
semantic versions hash the snapshot that is supposed to contain them.  ORION therefore
uses a previewable content-identified ``SemanticMutationBatch``:

    current semantic revision
      -> plan mutation batch
      -> preview next semantic revision
      -> construct after ProjectSnapshot
      -> commit batch bound to that after snapshot

The snapshot binding is durable metadata/provenance.  It is not part of the semantic
version content hash.  Historical semantic state remains append-only and queryable.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator, Mapping, Tuple

from .engineering_state import canonical_sha256
from .engineering_store import EngineeringIntegrityError


@dataclass(frozen=True)
class SemanticFiber:
    fiber_id: str
    parent_fiber_id: str | None = None
    created_from_sequence: int = 0

    def __post_init__(self) -> None:
        if not self.fiber_id.strip():
            raise ValueError("fiber_id is required")
        if self.parent_fiber_id == self.fiber_id:
            raise ValueError("fiber cannot parent itself")
        if self.created_from_sequence < 0:
            raise ValueError("created_from_sequence cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "fiber_id": self.fiber_id,
            "parent_fiber_id": self.parent_fiber_id,
            "created_from_sequence": self.created_from_sequence,
        }


@dataclass(frozen=True)
class SemanticAtomVersion:
    atom_id: str
    fiber_id: str
    kind: str
    label: str
    evidence_ids: Tuple[str, ...]
    payload: Mapping[str, object]
    valid_from_sequence: int
    supersedes_version_id: str | None = None
    version_id: str = ""

    def __post_init__(self) -> None:
        for name in ("atom_id", "fiber_id", "kind", "label"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.valid_from_sequence < 0:
            raise ValueError("valid_from_sequence cannot be negative")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence ids must be unique")
        expected = "atom-version:" + canonical_sha256(self.identity_payload)
        if self.version_id and self.version_id != expected:
            raise ValueError("atom version id does not match content")
        if not self.version_id:
            object.__setattr__(self, "version_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "atom_id": self.atom_id,
            "fiber_id": self.fiber_id,
            "kind": self.kind,
            "label": self.label,
            "evidence_ids": list(self.evidence_ids),
            "payload": dict(self.payload),
            "valid_from_sequence": self.valid_from_sequence,
            "supersedes_version_id": self.supersedes_version_id,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "version_id": self.version_id}


@dataclass(frozen=True)
class RelationWitnessVersion:
    witness_id: str
    left_atom_id: str
    right_atom_id: str
    relation_type: str
    reason: str
    condition: str | None
    evidence_ids: Tuple[str, ...]
    payload: Mapping[str, object]
    valid_from_sequence: int
    supersedes_version_id: str | None = None
    version_id: str = ""

    def __post_init__(self) -> None:
        for name in ("witness_id", "left_atom_id", "right_atom_id", "relation_type", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.left_atom_id == self.right_atom_id:
            raise ValueError("relation witness requires distinct atoms")
        if self.valid_from_sequence < 0:
            raise ValueError("valid_from_sequence cannot be negative")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence ids must be unique")
        expected = "relation-version:" + canonical_sha256(self.identity_payload)
        if self.version_id and self.version_id != expected:
            raise ValueError("relation version id does not match content")
        if not self.version_id:
            object.__setattr__(self, "version_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "witness_id": self.witness_id,
            "left_atom_id": self.left_atom_id,
            "right_atom_id": self.right_atom_id,
            "relation_type": self.relation_type,
            "reason": self.reason,
            "condition": self.condition,
            "evidence_ids": list(self.evidence_ids),
            "payload": dict(self.payload),
            "valid_from_sequence": self.valid_from_sequence,
            "supersedes_version_id": self.supersedes_version_id,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "version_id": self.version_id}


@dataclass(frozen=True)
class SemanticMutationBatch:
    sequence: int
    base_semantic_revision: str
    new_fibers: Tuple[SemanticFiber, ...] = ()
    atom_versions: Tuple[SemanticAtomVersion, ...] = ()
    witness_versions: Tuple[RelationWitnessVersion, ...] = ()
    batch_id: str = ""

    def __post_init__(self) -> None:
        if self.sequence < 0 or not self.base_semantic_revision.strip():
            raise ValueError("batch requires sequence and base semantic revision")
        if any(item.created_from_sequence != self.sequence for item in self.new_fibers):
            raise ValueError("new fibers must be created at batch sequence")
        if any(item.valid_from_sequence != self.sequence for item in self.atom_versions):
            raise ValueError("atom versions must start at batch sequence")
        if any(item.valid_from_sequence != self.sequence for item in self.witness_versions):
            raise ValueError("witness versions must start at batch sequence")
        for items, label, identity in (
            (self.new_fibers, "fibers", lambda x: x.fiber_id),
            (self.atom_versions, "atoms", lambda x: x.atom_id),
            (self.witness_versions, "witnesses", lambda x: x.witness_id),
        ):
            values = [identity(item) for item in items]
            if len(values) != len(set(values)):
                raise ValueError(f"batch {label} must have unique semantic identities")
        expected = "semantic-batch:" + canonical_sha256(self.identity_payload)
        if self.batch_id and self.batch_id != expected:
            raise ValueError("semantic batch id does not match content")
        if not self.batch_id:
            object.__setattr__(self, "batch_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "sequence": self.sequence,
            "base_semantic_revision": self.base_semantic_revision,
            "new_fibers": [item.to_dict() for item in self.new_fibers],
            "atom_versions": [item.to_dict() for item in self.atom_versions],
            "witness_versions": [item.to_dict() for item in self.witness_versions],
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "batch_id": self.batch_id}


@dataclass(frozen=True)
class SemanticBatchCommit:
    batch_id: str
    committed_snapshot_id: str
    semantic_revision: str


class SqliteSemanticStateStore:
    """Reference append-only semantic store with preview/commit semantics."""

    @staticmethod
    def _ordered_new_fibers(
        new_fibers: Iterable[SemanticFiber],
        *,
        existing_fiber_ids: Iterable[str] = (),
    ) -> Tuple[SemanticFiber, ...]:
        """Return deterministic parent-before-child order and reject cycles.

        Preview and commit must agree independently of caller tuple order. A parent
        may already exist or be created in the same batch; a missing parent or a
        cycle is an integrity defect in the batch, not a database-order concern.
        """
        batch_items = tuple(new_fibers)
        items = {item.fiber_id: item for item in batch_items}
        existing = set(existing_fiber_ids)
        if len(items) != len(batch_items):
            # SemanticMutationBatch already rejects this, but keep helper safe for
            # direct internal use.
            raise EngineeringIntegrityError("new fiber identities must be unique")
        ordered: list[SemanticFiber] = []
        state: dict[str, int] = {}  # 1 visiting, 2 done

        def visit(fiber_id: str) -> None:
            mark = state.get(fiber_id, 0)
            if mark == 2:
                return
            if mark == 1:
                raise EngineeringIntegrityError("semantic batch fiber parent cycle")
            state[fiber_id] = 1
            item = items[fiber_id]
            parent = item.parent_fiber_id
            if parent is not None and parent not in existing:
                if parent not in items:
                    raise EngineeringIntegrityError("semantic batch fiber parent unavailable")
                visit(parent)
            state[fiber_id] = 2
            ordered.append(item)

        for fiber_id in sorted(items):
            visit(fiber_id)
        return tuple(ordered)

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS semantic_fibers(
                    fiber_id TEXT PRIMARY KEY,
                    parent_fiber_id TEXT,
                    created_from_snapshot_id TEXT NOT NULL,
                    created_from_sequence INTEGER NOT NULL CHECK(created_from_sequence >= 0),
                    FOREIGN KEY(parent_fiber_id) REFERENCES semantic_fibers(fiber_id)
                );
                CREATE TABLE IF NOT EXISTS semantic_atoms(
                    atom_id TEXT PRIMARY KEY,
                    fiber_id TEXT NOT NULL REFERENCES semantic_fibers(fiber_id),
                    kind TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS semantic_atom_versions(
                    version_id TEXT PRIMARY KEY,
                    atom_id TEXT NOT NULL REFERENCES semantic_atoms(atom_id),
                    valid_from_snapshot_id TEXT NOT NULL,
                    valid_from_sequence INTEGER NOT NULL CHECK(valid_from_sequence >= 0),
                    supersedes_version_id TEXT REFERENCES semantic_atom_versions(version_id),
                    payload_json TEXT NOT NULL,
                    UNIQUE(atom_id, valid_from_sequence)
                );
                CREATE INDEX IF NOT EXISTS semantic_atom_versions_lookup
                    ON semantic_atom_versions(atom_id, valid_from_sequence DESC);
                CREATE TABLE IF NOT EXISTS semantic_witnesses(
                    witness_id TEXT PRIMARY KEY,
                    left_atom_id TEXT NOT NULL REFERENCES semantic_atoms(atom_id),
                    right_atom_id TEXT NOT NULL REFERENCES semantic_atoms(atom_id)
                );
                CREATE TABLE IF NOT EXISTS semantic_witness_versions(
                    version_id TEXT PRIMARY KEY,
                    witness_id TEXT NOT NULL REFERENCES semantic_witnesses(witness_id),
                    valid_from_snapshot_id TEXT NOT NULL,
                    valid_from_sequence INTEGER NOT NULL CHECK(valid_from_sequence >= 0),
                    supersedes_version_id TEXT REFERENCES semantic_witness_versions(version_id),
                    payload_json TEXT NOT NULL,
                    UNIQUE(witness_id, valid_from_sequence)
                );
                CREATE INDEX IF NOT EXISTS semantic_witness_versions_lookup
                    ON semantic_witness_versions(witness_id, valid_from_sequence DESC);
                CREATE TABLE IF NOT EXISTS semantic_batch_commits(
                    batch_id TEXT PRIMARY KEY,
                    sequence INTEGER NOT NULL,
                    committed_snapshot_id TEXT NOT NULL,
                    semantic_revision TEXT NOT NULL,
                    batch_json TEXT NOT NULL,
                    UNIQUE(sequence)
                );
                """
            )

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

    @staticmethod
    def _dump(value: Mapping[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def add_fiber(self, fiber: SemanticFiber, *, valid_from_snapshot_id: str) -> SemanticFiber:
        if not valid_from_snapshot_id:
            raise ValueError("valid_from_snapshot_id is required")
        with self._tx() as db:
            return self._add_fiber(db, fiber, valid_from_snapshot_id=valid_from_snapshot_id)

    def _add_fiber(
        self, db: sqlite3.Connection, fiber: SemanticFiber, *, valid_from_snapshot_id: str
    ) -> SemanticFiber:
        existing = db.execute(
            """SELECT parent_fiber_id,created_from_sequence FROM semantic_fibers
               WHERE fiber_id=?""",
            (fiber.fiber_id,),
        ).fetchone()
        if existing is not None:
            if (
                existing["parent_fiber_id"] != fiber.parent_fiber_id
                or int(existing["created_from_sequence"]) != fiber.created_from_sequence
            ):
                raise EngineeringIntegrityError("semantic fiber identity cannot be rebound")
            return fiber
        if fiber.parent_fiber_id is not None:
            parent = db.execute(
                "SELECT created_from_sequence FROM semantic_fibers WHERE fiber_id=?",
                (fiber.parent_fiber_id,),
            ).fetchone()
            if parent is None:
                raise KeyError(fiber.parent_fiber_id)
            if int(parent["created_from_sequence"]) > fiber.created_from_sequence:
                raise EngineeringIntegrityError("child fiber cannot predate its parent fiber")
        db.execute(
            "INSERT INTO semantic_fibers VALUES(?,?,?,?)",
            (
                fiber.fiber_id,
                fiber.parent_fiber_id,
                valid_from_snapshot_id,
                fiber.created_from_sequence,
            ),
        )
        return fiber

    def get_fiber(self, fiber_id: str) -> SemanticFiber | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT fiber_id,parent_fiber_id,created_from_sequence FROM semantic_fibers WHERE fiber_id=?",
                (fiber_id,),
            ).fetchone()
        if row is None:
            return None
        return SemanticFiber(row["fiber_id"], row["parent_fiber_id"], int(row["created_from_sequence"]))

    def fibers_at(self, sequence: int) -> Tuple[SemanticFiber, ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT fiber_id,parent_fiber_id,created_from_sequence FROM semantic_fibers
                   WHERE created_from_sequence <= ? ORDER BY fiber_id""",
                (sequence,),
            ).fetchall()
        return tuple(
            SemanticFiber(row["fiber_id"], row["parent_fiber_id"], int(row["created_from_sequence"]))
            for row in rows
        )

    def _latest_atom_row(self, db: sqlite3.Connection, atom_id: str) -> sqlite3.Row | None:
        return db.execute(
            """SELECT * FROM semantic_atom_versions WHERE atom_id=?
               ORDER BY valid_from_sequence DESC LIMIT 1""",
            (atom_id,),
        ).fetchone()

    def latest_atom_version(self, atom_id: str) -> SemanticAtomVersion | None:
        with self._connect() as db:
            row = self._latest_atom_row(db, atom_id)
        return None if row is None else self._atom_from_dict(json.loads(row["payload_json"]))

    def add_atom_version(
        self, version: SemanticAtomVersion, *, valid_from_snapshot_id: str
    ) -> SemanticAtomVersion:
        if not valid_from_snapshot_id:
            raise ValueError("valid_from_snapshot_id is required")
        with self._tx() as db:
            return self._add_atom_version(db, version, valid_from_snapshot_id=valid_from_snapshot_id)

    def _add_atom_version(
        self, db: sqlite3.Connection, version: SemanticAtomVersion, *, valid_from_snapshot_id: str
    ) -> SemanticAtomVersion:
        if db.execute("SELECT 1 FROM semantic_fibers WHERE fiber_id=?", (version.fiber_id,)).fetchone() is None:
            raise KeyError(version.fiber_id)
        identity = db.execute(
            "SELECT fiber_id,kind FROM semantic_atoms WHERE atom_id=?", (version.atom_id,)
        ).fetchone()
        if identity is None:
            if version.supersedes_version_id is not None:
                raise EngineeringIntegrityError("first atom version cannot supersede")
            db.execute("INSERT INTO semantic_atoms VALUES(?,?,?)", (version.atom_id, version.fiber_id, version.kind))
        elif identity["fiber_id"] != version.fiber_id or identity["kind"] != version.kind:
            raise EngineeringIntegrityError("atom identity cannot change fiber or kind")

        same = db.execute("SELECT payload_json FROM semantic_atom_versions WHERE version_id=?", (version.version_id,)).fetchone()
        if same is not None:
            if json.loads(same["payload_json"]) != version.to_dict():
                raise EngineeringIntegrityError("atom version id collision")
            return version
        latest = self._latest_atom_row(db, version.atom_id)
        if latest is not None:
            if version.supersedes_version_id != latest["version_id"]:
                raise EngineeringIntegrityError("new atom version must supersede current head")
            if version.valid_from_sequence <= int(latest["valid_from_sequence"]):
                raise EngineeringIntegrityError("atom version sequence must increase")
        db.execute(
            "INSERT INTO semantic_atom_versions VALUES(?,?,?,?,?,?)",
            (
                version.version_id,
                version.atom_id,
                valid_from_snapshot_id,
                version.valid_from_sequence,
                version.supersedes_version_id,
                self._dump(version.to_dict()),
            ),
        )
        return version

    def latest_witness_version(self, witness_id: str) -> RelationWitnessVersion | None:
        with self._connect() as db:
            row = db.execute(
                """SELECT payload_json FROM semantic_witness_versions WHERE witness_id=?
                   ORDER BY valid_from_sequence DESC LIMIT 1""",
                (witness_id,),
            ).fetchone()
        return None if row is None else self._witness_from_dict(json.loads(row["payload_json"]))

    def add_witness_version(
        self, version: RelationWitnessVersion, *, valid_from_snapshot_id: str
    ) -> RelationWitnessVersion:
        if not valid_from_snapshot_id:
            raise ValueError("valid_from_snapshot_id is required")
        with self._tx() as db:
            return self._add_witness_version(db, version, valid_from_snapshot_id=valid_from_snapshot_id)

    def _add_witness_version(
        self, db: sqlite3.Connection, version: RelationWitnessVersion, *, valid_from_snapshot_id: str
    ) -> RelationWitnessVersion:
        for atom_id in (version.left_atom_id, version.right_atom_id):
            if db.execute("SELECT 1 FROM semantic_atoms WHERE atom_id=?", (atom_id,)).fetchone() is None:
                raise KeyError(atom_id)
        identity = db.execute(
            "SELECT left_atom_id,right_atom_id FROM semantic_witnesses WHERE witness_id=?",
            (version.witness_id,),
        ).fetchone()
        if identity is None:
            if version.supersedes_version_id is not None:
                raise EngineeringIntegrityError("first witness version cannot supersede")
            db.execute(
                "INSERT INTO semantic_witnesses VALUES(?,?,?)",
                (version.witness_id, version.left_atom_id, version.right_atom_id),
            )
        elif {identity["left_atom_id"], identity["right_atom_id"]} != {
            version.left_atom_id,
            version.right_atom_id,
        }:
            raise EngineeringIntegrityError("witness identity cannot change endpoints")

        same = db.execute("SELECT payload_json FROM semantic_witness_versions WHERE version_id=?", (version.version_id,)).fetchone()
        if same is not None:
            if json.loads(same["payload_json"]) != version.to_dict():
                raise EngineeringIntegrityError("witness version id collision")
            return version
        latest = db.execute(
            """SELECT * FROM semantic_witness_versions WHERE witness_id=?
               ORDER BY valid_from_sequence DESC LIMIT 1""",
            (version.witness_id,),
        ).fetchone()
        if latest is not None:
            if version.supersedes_version_id != latest["version_id"]:
                raise EngineeringIntegrityError("new witness version must supersede current head")
            if version.valid_from_sequence <= int(latest["valid_from_sequence"]):
                raise EngineeringIntegrityError("witness version sequence must increase")
        db.execute(
            "INSERT INTO semantic_witness_versions VALUES(?,?,?,?,?,?)",
            (
                version.version_id,
                version.witness_id,
                valid_from_snapshot_id,
                version.valid_from_sequence,
                version.supersedes_version_id,
                self._dump(version.to_dict()),
            ),
        )
        return version

    def atom_versions_at(self, sequence: int) -> Tuple[SemanticAtomVersion, ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT v.payload_json FROM semantic_atom_versions v
                   JOIN (
                     SELECT atom_id, MAX(valid_from_sequence) AS seq
                     FROM semantic_atom_versions WHERE valid_from_sequence <= ? GROUP BY atom_id
                   ) h ON h.atom_id=v.atom_id AND h.seq=v.valid_from_sequence
                   ORDER BY v.atom_id""",
                (sequence,),
            ).fetchall()
        return tuple(self._atom_from_dict(json.loads(row["payload_json"])) for row in rows)

    def witness_versions_at(self, sequence: int) -> Tuple[RelationWitnessVersion, ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT v.payload_json FROM semantic_witness_versions v
                   JOIN (
                     SELECT witness_id, MAX(valid_from_sequence) AS seq
                     FROM semantic_witness_versions WHERE valid_from_sequence <= ? GROUP BY witness_id
                   ) h ON h.witness_id=v.witness_id AND h.seq=v.valid_from_sequence
                   ORDER BY v.witness_id""",
                (sequence,),
            ).fetchall()
        return tuple(self._witness_from_dict(json.loads(row["payload_json"])) for row in rows)

    @staticmethod
    def _revision_for(
        sequence: int,
        fibers: Iterable[SemanticFiber],
        atoms: Iterable[SemanticAtomVersion],
        witnesses: Iterable[RelationWitnessVersion],
    ) -> str:
        return "semantic-revision:" + canonical_sha256(
            {
                "fibers": [item.to_dict() for item in sorted(fibers, key=lambda item: item.fiber_id)],
                "atom_version_ids": [item.version_id for item in sorted(atoms, key=lambda item: item.atom_id)],
                "witness_version_ids": [item.version_id for item in sorted(witnesses, key=lambda item: item.witness_id)],
            }
        )

    def semantic_revision(self, sequence: int) -> str:
        return self._revision_for(
            sequence,
            self.fibers_at(sequence),
            self.atom_versions_at(sequence),
            self.witness_versions_at(sequence),
        )

    def _preview_batch_revision_db(
        self, db: sqlite3.Connection, batch: SemanticMutationBatch
    ) -> str:
        base_sequence = batch.sequence - 1
        current_base = self._revision_for(
            base_sequence,
            self._fibers_at_db(db, base_sequence),
            self._atom_versions_at_db(db, base_sequence),
            self._witness_versions_at_db(db, base_sequence),
        )
        if batch.base_semantic_revision != current_base:
            raise EngineeringIntegrityError("semantic batch base revision is stale")
        fibers = {item.fiber_id: item for item in self._fibers_at_db(db, base_sequence)}
        atoms = {item.atom_id: item for item in self._atom_versions_at_db(db, base_sequence)}
        witnesses = {item.witness_id: item for item in self._witness_versions_at_db(db, base_sequence)}
        for item in batch.new_fibers:
            existing = fibers.get(item.fiber_id)
            if existing is not None and existing != item:
                raise EngineeringIntegrityError("semantic batch rebinds fiber identity")
        ordered_new_fibers = self._ordered_new_fibers(
            batch.new_fibers, existing_fiber_ids=fibers
        )
        for item in ordered_new_fibers:
            fibers[item.fiber_id] = item
        for item in batch.atom_versions:
            previous = atoms.get(item.atom_id)
            if previous is None and item.supersedes_version_id is not None:
                raise EngineeringIntegrityError("new batch atom cannot supersede absent atom")
            if previous is not None:
                if previous.fiber_id != item.fiber_id or previous.kind != item.kind:
                    raise EngineeringIntegrityError("batch atom changes fiber or kind")
                if item.supersedes_version_id != previous.version_id:
                    raise EngineeringIntegrityError("batch atom must supersede current head")
            if item.fiber_id not in fibers:
                raise EngineeringIntegrityError("batch atom references unavailable fiber")
            atoms[item.atom_id] = item
        for item in batch.witness_versions:
            previous = witnesses.get(item.witness_id)
            if previous is None and item.supersedes_version_id is not None:
                raise EngineeringIntegrityError("new batch witness cannot supersede absent witness")
            if previous is not None:
                if {previous.left_atom_id, previous.right_atom_id} != {item.left_atom_id, item.right_atom_id}:
                    raise EngineeringIntegrityError("batch witness changes endpoints")
                if item.supersedes_version_id != previous.version_id:
                    raise EngineeringIntegrityError("batch witness must supersede current head")
            if item.left_atom_id not in atoms or item.right_atom_id not in atoms:
                raise EngineeringIntegrityError("batch witness references unavailable atom")
            witnesses[item.witness_id] = item
        return self._revision_for(batch.sequence, fibers.values(), atoms.values(), witnesses.values())

    def preview_batch_revision(self, batch: SemanticMutationBatch) -> str:
        with self._connect() as db:
            return self._preview_batch_revision_db(db, batch)

    def _commit_batch_db(
        self,
        db: sqlite3.Connection,
        batch: SemanticMutationBatch,
        *,
        committed_snapshot_id: str,
        expected_semantic_revision: str,
    ) -> SemanticBatchCommit:
        if not committed_snapshot_id:
            raise ValueError("committed_snapshot_id is required")
        preview = self._preview_batch_revision_db(db, batch)
        if preview != expected_semantic_revision:
            raise EngineeringIntegrityError("semantic batch preview does not match after snapshot revision")
        existing = db.execute(
            "SELECT committed_snapshot_id,semantic_revision,batch_json FROM semantic_batch_commits WHERE batch_id=?",
            (batch.batch_id,),
        ).fetchone()
        if existing is not None:
            if (
                existing["committed_snapshot_id"] != committed_snapshot_id
                or existing["semantic_revision"] != expected_semantic_revision
                or json.loads(existing["batch_json"]) != batch.to_dict()
            ):
                raise EngineeringIntegrityError("semantic batch id already committed differently")
            return SemanticBatchCommit(batch.batch_id, committed_snapshot_id, expected_semantic_revision)
        existing_fiber_ids = {item.fiber_id for item in self._fibers_at_db(db, batch.sequence - 1)}
        for fiber in self._ordered_new_fibers(
            batch.new_fibers, existing_fiber_ids=existing_fiber_ids
        ):
            self._add_fiber(db, fiber, valid_from_snapshot_id=committed_snapshot_id)
        for version in batch.atom_versions:
            self._add_atom_version(db, version, valid_from_snapshot_id=committed_snapshot_id)
        for version in batch.witness_versions:
            self._add_witness_version(db, version, valid_from_snapshot_id=committed_snapshot_id)
        actual = self._revision_for(
            batch.sequence,
            self._fibers_at_db(db, batch.sequence),
            self._atom_versions_at_db(db, batch.sequence),
            self._witness_versions_at_db(db, batch.sequence),
        )
        if actual != expected_semantic_revision:
            raise EngineeringIntegrityError("committed semantic revision diverged from preview")
        db.execute(
            "INSERT INTO semantic_batch_commits VALUES(?,?,?,?,?)",
            (batch.batch_id, batch.sequence, committed_snapshot_id, actual, self._dump(batch.to_dict())),
        )
        return SemanticBatchCommit(batch.batch_id, committed_snapshot_id, expected_semantic_revision)

    def commit_batch(
        self,
        batch: SemanticMutationBatch,
        *,
        committed_snapshot_id: str,
        expected_semantic_revision: str,
    ) -> SemanticBatchCommit:
        with self._tx() as db:
            return self._commit_batch_db(
                db, batch, committed_snapshot_id=committed_snapshot_id,
                expected_semantic_revision=expected_semantic_revision,
            )

    def batch_commit(self, batch_id: str) -> SemanticBatchCommit | None:
        """Return the durable commit binding for one semantic mutation batch.

        This query is intentionally separate from the semantic content itself: a
        batch may be valid to preview but it becomes part of canonical project
        history only when a snapshot-bound commit record exists.
        """
        if not batch_id or not batch_id.strip():
            raise ValueError("batch_id is required")
        with self._connect() as db:
            row = db.execute(
                "SELECT committed_snapshot_id,semantic_revision FROM semantic_batch_commits WHERE batch_id=?",
                (batch_id,),
            ).fetchone()
        if row is None:
            return None
        return SemanticBatchCommit(batch_id, row["committed_snapshot_id"], row["semantic_revision"])

    def _fibers_at_db(self, db: sqlite3.Connection, sequence: int) -> Tuple[SemanticFiber, ...]:
        rows = db.execute(
            "SELECT fiber_id,parent_fiber_id,created_from_sequence FROM semantic_fibers WHERE created_from_sequence <= ? ORDER BY fiber_id",
            (sequence,),
        ).fetchall()
        return tuple(SemanticFiber(row["fiber_id"], row["parent_fiber_id"], int(row["created_from_sequence"])) for row in rows)

    def _atom_versions_at_db(self, db: sqlite3.Connection, sequence: int) -> Tuple[SemanticAtomVersion, ...]:
        rows = db.execute(
            """SELECT v.payload_json FROM semantic_atom_versions v JOIN (
                 SELECT atom_id, MAX(valid_from_sequence) seq FROM semantic_atom_versions
                 WHERE valid_from_sequence <= ? GROUP BY atom_id
               ) h ON h.atom_id=v.atom_id AND h.seq=v.valid_from_sequence ORDER BY v.atom_id""",
            (sequence,),
        ).fetchall()
        return tuple(self._atom_from_dict(json.loads(row["payload_json"])) for row in rows)

    def _witness_versions_at_db(self, db: sqlite3.Connection, sequence: int) -> Tuple[RelationWitnessVersion, ...]:
        rows = db.execute(
            """SELECT v.payload_json FROM semantic_witness_versions v JOIN (
                 SELECT witness_id, MAX(valid_from_sequence) seq FROM semantic_witness_versions
                 WHERE valid_from_sequence <= ? GROUP BY witness_id
               ) h ON h.witness_id=v.witness_id AND h.seq=v.valid_from_sequence ORDER BY v.witness_id""",
            (sequence,),
        ).fetchall()
        return tuple(self._witness_from_dict(json.loads(row["payload_json"])) for row in rows)

    @staticmethod
    def _atom_from_dict(value: Mapping[str, object]) -> SemanticAtomVersion:
        return SemanticAtomVersion(
            atom_id=str(value["atom_id"]),
            fiber_id=str(value["fiber_id"]),
            kind=str(value["kind"]),
            label=str(value["label"]),
            evidence_ids=tuple(str(item) for item in value.get("evidence_ids", ())),
            payload=dict(value.get("payload", {})),
            valid_from_sequence=int(value["valid_from_sequence"]),
            supersedes_version_id=(None if value.get("supersedes_version_id") is None else str(value["supersedes_version_id"])),
            version_id=str(value.get("version_id", "")),
        )

    @staticmethod
    def _witness_from_dict(value: Mapping[str, object]) -> RelationWitnessVersion:
        return RelationWitnessVersion(
            witness_id=str(value["witness_id"]),
            left_atom_id=str(value["left_atom_id"]),
            right_atom_id=str(value["right_atom_id"]),
            relation_type=str(value["relation_type"]),
            reason=str(value["reason"]),
            condition=(None if value.get("condition") is None else str(value["condition"])),
            evidence_ids=tuple(str(item) for item in value.get("evidence_ids", ())),
            payload=dict(value.get("payload", {})),
            valid_from_sequence=int(value["valid_from_sequence"]),
            supersedes_version_id=(None if value.get("supersedes_version_id") is None else str(value["supersedes_version_id"])),
            version_id=str(value.get("version_id", "")),
        )
