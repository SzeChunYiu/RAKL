"""Rebuildable target/query projection over canonical semantic state.

The index is disposable.  It never mints semantic identity or authority; deletion
must be recoverable by rebuilding from the canonical semantic store.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .engineering_semantic_store import SemanticAtomVersion, SqliteSemanticStateStore
from .engineering_state import canonical_sha256


@dataclass(frozen=True)
class IndexedAtom:
    atom_id: str
    version_id: str
    fiber_id: str
    kind: str
    label: str


@dataclass(frozen=True)
class SemanticIndexSnapshot:
    semantic_revision: str
    indexed_atoms: Tuple[IndexedAtom, ...]
    index_id: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


class RebuildableSemanticIndex:
    def __init__(self) -> None:
        self._snapshot: SemanticIndexSnapshot | None = None

    def rebuild(self, store: SqliteSemanticStateStore, *, sequence: int) -> SemanticIndexSnapshot:
        atoms = tuple(
            IndexedAtom(item.atom_id, item.version_id, item.fiber_id, item.kind, item.label)
            for item in store.atom_versions_at(sequence)
        )
        revision = store.semantic_revision(sequence)
        index_id = "semantic-index:" + canonical_sha256(
            {
                "semantic_revision": revision,
                "atoms": [item.__dict__ for item in atoms],
            }
        )
        self._snapshot = SemanticIndexSnapshot(revision, atoms, index_id)
        return self._snapshot

    def clear(self) -> None:
        self._snapshot = None

    @property
    def snapshot(self) -> SemanticIndexSnapshot | None:
        return self._snapshot

    def exact_filter(
        self, *, fiber_ids: Iterable[str] = (), kinds: Iterable[str] = ()
    ) -> Tuple[IndexedAtom, ...]:
        if self._snapshot is None:
            return ()
        fibers = set(fiber_ids)
        kinds_set = set(kinds)
        return tuple(
            item
            for item in self._snapshot.indexed_atoms
            if (not fibers or item.fiber_id in fibers)
            and (not kinds_set or item.kind in kinds_set)
        )

    def lexical(self, query: str, *, limit: int = 20) -> Tuple[IndexedAtom, ...]:
        if self._snapshot is None or not query.strip() or limit < 1:
            return ()
        terms = tuple(term.casefold() for term in query.split() if term)
        scored: list[tuple[int, str, IndexedAtom]] = []
        for item in self._snapshot.indexed_atoms:
            haystack = item.label.casefold()
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((-score, item.atom_id, item))
        scored.sort(key=lambda row: (row[0], row[1]))
        return tuple(row[2] for row in scored[:limit])
