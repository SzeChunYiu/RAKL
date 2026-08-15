from dataclasses import dataclass
from enum import Enum

from rakl.engineering_semantic_adapters import import_typed_knowledge_lattice
from rakl.engineering_semantic_store import SqliteSemanticStateStore


class Kind(str, Enum):
    MECHANISM_NODE = "MECHANISM_NODE"


class Relation(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    CONDITIONAL = "CONDITIONAL"


@dataclass(frozen=True)
class Atom:
    atom_id: str
    fiber_id: str
    kind: Kind
    label: str
    evidence_ids: tuple[str, ...]
    equation: object | None = None
    expression: object | None = None
    mechanism_node: object | None = None
    mechanism_edge: object | None = None
    payload: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Witness:
    left_atom_id: str
    right_atom_id: str
    relation: Relation
    reason: str
    condition: str | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass
class Lattice:
    atoms: dict[str, Atom]
    witnesses: dict[frozenset[str], Witness]


def lattice(*, rel=Relation.COMPATIBLE, label="mechanism a"):
    a = Atom("a", "fiber:root", Kind.MECHANISM_NODE, label, ("e:a",), payload=(("x", "1"),))
    b = Atom("b", "fiber:root", Kind.MECHANISM_NODE, "mechanism b", ("e:b",))
    w = Witness("a", "b", rel, "known world", evidence_ids=("e:w",))
    return Lattice({"a": a, "b": b}, {frozenset(("a", "b")): w})


def test_typed_lattice_import_is_idempotent_and_does_not_invent_novelty(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    first = import_typed_knowledge_lattice(store, lattice(), snapshot_id="snapshot:0", sequence=0)
    second = import_typed_knowledge_lattice(store, lattice(), snapshot_id="snapshot:1", sequence=1)
    assert first.retained_semantic_novelty == 3
    assert second.retained_semantic_novelty == 0
    assert second.unchanged_atom_ids == ("a", "b")
    assert len(second.unchanged_witness_ids) == 1


def test_material_lattice_change_appends_new_version(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    first = import_typed_knowledge_lattice(store, lattice(), snapshot_id="snapshot:0", sequence=0)
    changed = import_typed_knowledge_lattice(
        store, lattice(rel=Relation.CONDITIONAL, label="updated mechanism a"),
        snapshot_id="snapshot:1", sequence=1,
    )
    assert changed.retained_semantic_novelty == 2
    assert store.semantic_revision(0) == first.semantic_revision
    assert store.semantic_revision(1) == changed.semantic_revision
    assert first.semantic_revision != changed.semantic_revision
