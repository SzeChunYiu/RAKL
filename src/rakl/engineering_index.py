"""Rebuildable target/query projection over canonical semantic state.

The index is disposable.  It never mints semantic identity or authority; deletion
must be recoverable by rebuilding from the canonical semantic store.

Fail-closed rules (HOSTILE_TEST_MATRIX H13/H14):

* ``SemanticIndexSnapshot`` is content-identified like every other identity-
  bearing object in this layer: its ``index_id`` is recomputed in
  ``__post_init__`` and a mismatch raises. A snapshot carrying atoms it did not
  hash cannot be constructed.
* ``RebuildableSemanticIndex.verify(store)`` checks every atom the index would
  serve against the canonical store: the atom must exist. Any ghost is
  reported. A verification is bound to the ``index_id`` it verified; a
  projection swapped in afterwards is unverified again.
* ``exact_filter`` / ``lexical`` refuse to serve an unverified or failed
  projection: they raise ``IndexIntegrityError`` (the CANNOT_CHECK terminal of
  this layer) rather than filtering ghosts out silently -- filtering would hide
  the corruption the operator needs to see. Rebuilding is the repair.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple

from .engineering_semantic_store import SqliteSemanticStateStore
from .engineering_state import canonical_sha256


class IndexIntegrityError(RuntimeError):
    """The index projection is unverified or referentially broken; it will not be served."""


class IndexVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    GHOST_ATOMS = "GHOST_ATOMS"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    NOT_BUILT = "NOT_BUILT"


@dataclass(frozen=True)
class IndexedAtom:
    atom_id: str
    version_id: str
    fiber_id: str
    kind: str
    label: str


def _index_identity(semantic_revision: str, atoms: Tuple[IndexedAtom, ...]) -> str:
    return "semantic-index:" + canonical_sha256(
        {
            "semantic_revision": semantic_revision,
            "atoms": [item.__dict__ for item in atoms],
        }
    )


@dataclass(frozen=True)
class SemanticIndexSnapshot:
    semantic_revision: str
    indexed_atoms: Tuple[IndexedAtom, ...]
    index_id: str = ""

    def __post_init__(self) -> None:
        if not self.semantic_revision.strip():
            raise ValueError("index snapshot requires a semantic revision")
        ids = [item.atom_id for item in self.indexed_atoms]
        if len(ids) != len(set(ids)):
            raise ValueError("index snapshot cannot carry one atom twice")
        expected = _index_identity(self.semantic_revision, tuple(self.indexed_atoms))
        if self.index_id and self.index_id != expected:
            raise ValueError("index_id does not match indexed content")
        if not self.index_id:
            object.__setattr__(self, "index_id", expected)

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class IndexVerification:
    verdict: IndexVerdict
    ghost_atom_ids: Tuple[str, ...] = ()
    detail: str = ""
    index_id: str = ""      # the projection this verdict is about

    @property
    def ok(self) -> bool:
        return self.verdict is IndexVerdict.VERIFIED


class RebuildableSemanticIndex:
    def __init__(self) -> None:
        self._snapshot: SemanticIndexSnapshot | None = None
        self._verification: IndexVerification | None = None

    def rebuild(self, store: SqliteSemanticStateStore, *, sequence: int) -> SemanticIndexSnapshot:
        atoms = tuple(
            IndexedAtom(item.atom_id, item.version_id, item.fiber_id, item.kind, item.label)
            for item in store.atom_versions_at(sequence)
        )
        revision = store.semantic_revision(sequence)
        self._snapshot = SemanticIndexSnapshot(revision, atoms)
        # a projection built from the canonical store IS verified against it, by construction
        self._verification = IndexVerification(IndexVerdict.VERIFIED, detail=f"rebuilt at sequence {sequence}",
                                               index_id=self._snapshot.index_id)
        return self._snapshot

    def clear(self) -> None:
        self._snapshot = None
        self._verification = None

    @property
    def snapshot(self) -> SemanticIndexSnapshot | None:
        return self._snapshot

    @property
    def verification(self) -> IndexVerification | None:
        return self._verification

    def verify(self, store: SqliteSemanticStateStore) -> IndexVerification:
        """Referential check of the served projection against the canonical store.

        Every indexed atom must exist canonically. The snapshot's own identity is
        re-derived too, so a swapped-in projection whose ``index_id`` was forged is
        caught even if its atoms happen to be real. An indexed atom at an older
        version than the store's latest is lag (reported in detail), not a ghost.
        """

        snap = self._snapshot
        if snap is None:
            self._verification = IndexVerification(IndexVerdict.NOT_BUILT, detail="index has never been built")
            return self._verification
        if snap.index_id != _index_identity(snap.semantic_revision, tuple(snap.indexed_atoms)):
            self._verification = IndexVerification(IndexVerdict.IDENTITY_MISMATCH, detail="index_id does not bind atoms",
                                                   index_id=snap.index_id)
            return self._verification
        ghosts: list[str] = []
        stale: list[str] = []
        for item in snap.indexed_atoms:
            canonical = store.latest_atom_version(item.atom_id)
            if canonical is None:
                ghosts.append(item.atom_id)
            elif canonical.version_id != item.version_id:
                stale.append(item.atom_id)     # real atom, older version: lag, not a ghost (probe_index reports lag)
        if ghosts:
            self._verification = IndexVerification(
                IndexVerdict.GHOST_ATOMS, tuple(ghosts),
                f"{len(ghosts)} indexed atom(s) have no canonical counterpart; rebuild the index",
                index_id=snap.index_id,
            )
        else:
            self._verification = IndexVerification(
                IndexVerdict.VERIFIED,
                detail=f"{len(snap.indexed_atoms)} atoms resolve" + (f"; {len(stale)} at an older version" if stale else ""),
                index_id=snap.index_id,
            )
        return self._verification

    def _served(self) -> SemanticIndexSnapshot:
        """The projection, only if it is verified. Otherwise CANNOT_CHECK, never a guess."""

        if self._snapshot is None:
            raise IndexIntegrityError("index has not been built; rebuild from the canonical store")
        v = self._verification
        if v is None or not v.ok or v.index_id != self._snapshot.index_id:
            raise IndexIntegrityError(
                "index projection is not verified against the canonical store"
                + (f" ({v.verdict.value}: {v.detail})" if v is not None and not v.ok else "")
                + ("; the projection changed since it was verified" if v is not None and v.ok else "")
                + "; call verify(store) or rebuild(store)"
            )
        # self-identity check every time it is served: a projection whose atoms were
        # mutated behind its id is caught here
        if self._snapshot.index_id != _index_identity(self._snapshot.semantic_revision, tuple(self._snapshot.indexed_atoms)):
            self._verification = IndexVerification(IndexVerdict.IDENTITY_MISMATCH, detail="index_id does not bind atoms",
                                                   index_id=self._snapshot.index_id)
            raise IndexIntegrityError("index projection identity mismatch; rebuild from the canonical store")
        return self._snapshot

    def exact_filter(
        self, *, fiber_ids: Iterable[str] = (), kinds: Iterable[str] = ()
    ) -> Tuple[IndexedAtom, ...]:
        if self._snapshot is None:
            return ()   # H13: a cleared index is degraded, not broken -- empty, honestly
        snap = self._served()
        fibers = set(fiber_ids)
        kinds_set = set(kinds)
        return tuple(
            item
            for item in snap.indexed_atoms
            if (not fibers or item.fiber_id in fibers)
            and (not kinds_set or item.kind in kinds_set)
        )

    def lexical(self, query: str, *, limit: int = 20) -> Tuple[IndexedAtom, ...]:
        if self._snapshot is None or not query.strip() or limit < 1:
            return ()
        snap = self._served()
        terms = tuple(term.casefold() for term in query.split() if term)
        scored: list[tuple[int, str, IndexedAtom]] = []
        for item in snap.indexed_atoms:
            haystack = item.label.casefold()
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((-score, item.atom_id, item))
        scored.sort(key=lambda row: (row[0], row[1]))
        return tuple(row[2] for row in scored[:limit])


__all__ = [
    "IndexIntegrityError", "IndexVerdict", "IndexVerification", "IndexedAtom",
    "RebuildableSemanticIndex", "SemanticIndexSnapshot",
]
