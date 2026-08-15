"""Projection adapters from incumbent ``TypedKnowledgeLattice`` shapes.

The primary API is plan -> preview -> commit.  This avoids a content-identity cycle
between semantic versions and the ProjectSnapshot that records their revision.
Deletion/retirement is never inferred from absence in a partial lattice view.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Mapping, Tuple

from .engineering_semantic_store import (
    RelationWitnessVersion,
    SemanticAtomVersion,
    SemanticFiber,
    SemanticMutationBatch,
    SqliteSemanticStateStore,
)
from .engineering_state import canonical_sha256


class SemanticProjectionError(ValueError):
    pass


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_canonical_value(item) for item in value]
        return sorted(converted, key=lambda item: repr(item))
    raise SemanticProjectionError(f"unsupported incumbent semantic payload type:{type(value).__name__}")


def _enum_text(value: object) -> str:
    return str(getattr(value, "value", value))


def _atom_payload(atom: object) -> dict[str, object]:
    primary = {}
    for field in ("equation", "expression", "mechanism_node", "mechanism_edge"):
        value = getattr(atom, field, None)
        if value is not None:
            primary[field] = _canonical_value(value)
    return {
        "typed_primary": primary,
        "generic_payload": _canonical_value(getattr(atom, "payload", ())),
    }


def _atom_semantics(version: SemanticAtomVersion) -> object:
    return {
        "fiber_id": version.fiber_id,
        "kind": version.kind,
        "label": version.label,
        "evidence_ids": list(version.evidence_ids),
        "payload": dict(version.payload),
    }


def _witness_semantics(version: RelationWitnessVersion) -> object:
    return {
        "left_atom_id": version.left_atom_id,
        "right_atom_id": version.right_atom_id,
        "relation_type": version.relation_type,
        "reason": version.reason,
        "condition": version.condition,
        "evidence_ids": list(version.evidence_ids),
        "payload": dict(version.payload),
    }


@dataclass(frozen=True)
class LatticeImportPlan:
    batch: SemanticMutationBatch
    atom_ids_seen: Tuple[str, ...]
    witness_ids_seen: Tuple[str, ...]
    unchanged_atom_ids: Tuple[str, ...]
    unchanged_witness_ids: Tuple[str, ...]
    preview_semantic_revision: str

    @property
    def retained_semantic_novelty(self) -> int:
        return len(self.batch.new_fibers) + len(self.batch.atom_versions) + len(self.batch.witness_versions)


@dataclass(frozen=True)
class LatticeImportReport:
    snapshot_id: str
    sequence: int
    batch_id: str
    atom_ids_seen: Tuple[str, ...]
    witness_ids_seen: Tuple[str, ...]
    atom_versions_added: Tuple[str, ...]
    witness_versions_added: Tuple[str, ...]
    unchanged_atom_ids: Tuple[str, ...]
    unchanged_witness_ids: Tuple[str, ...]
    semantic_revision: str

    @property
    def retained_semantic_novelty(self) -> int:
        return len(self.atom_versions_added) + len(self.witness_versions_added)

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def plan_typed_knowledge_lattice_import(
    store: SqliteSemanticStateStore,
    lattice: object,
    *,
    sequence: int,
) -> LatticeImportPlan:
    if sequence < 0:
        raise ValueError("sequence must be non-negative")
    atoms_mapping = getattr(lattice, "atoms", None)
    witnesses_mapping = getattr(lattice, "witnesses", None)
    if not isinstance(atoms_mapping, Mapping) or not isinstance(witnesses_mapping, Mapping):
        raise SemanticProjectionError("lattice must expose mapping atoms and witnesses")

    atoms = tuple(sorted(atoms_mapping.values(), key=lambda item: str(getattr(item, "atom_id", ""))))
    fiber_ids = tuple(sorted({str(getattr(atom, "fiber_id", "")) for atom in atoms}))
    if any(not fiber_id for fiber_id in fiber_ids):
        raise SemanticProjectionError("all incumbent atoms require fiber_id")
    new_fibers = tuple(
        SemanticFiber(fiber_id, created_from_sequence=sequence)
        for fiber_id in fiber_ids
        if store.get_fiber(fiber_id) is None
    )

    added_atoms: list[SemanticAtomVersion] = []
    unchanged_atoms: list[str] = []
    seen_atoms: list[str] = []
    for atom in atoms:
        atom_id = str(getattr(atom, "atom_id", ""))
        fiber_id = str(getattr(atom, "fiber_id", ""))
        label = str(getattr(atom, "label", ""))
        kind = _enum_text(getattr(atom, "kind", ""))
        if not atom_id or not fiber_id or not label or not kind:
            raise SemanticProjectionError("incumbent atom identity/kind/label incomplete")
        latest = store.latest_atom_version(atom_id)
        candidate = SemanticAtomVersion(
            atom_id=atom_id,
            fiber_id=fiber_id,
            kind=kind,
            label=label,
            evidence_ids=tuple(str(item) for item in getattr(atom, "evidence_ids", ())),
            payload=_atom_payload(atom),
            valid_from_sequence=sequence,
            supersedes_version_id=None if latest is None else latest.version_id,
        )
        seen_atoms.append(atom_id)
        if latest is not None and _atom_semantics(latest) == _atom_semantics(candidate):
            unchanged_atoms.append(atom_id)
        else:
            added_atoms.append(candidate)

    added_witnesses: list[RelationWitnessVersion] = []
    unchanged_witnesses: list[str] = []
    seen_witnesses: list[str] = []
    witnesses = tuple(
        sorted(
            witnesses_mapping.values(),
            key=lambda item: tuple(sorted((str(getattr(item, "left_atom_id", "")), str(getattr(item, "right_atom_id", ""))))),
        )
    )
    for witness in witnesses:
        left = str(getattr(witness, "left_atom_id", "")); right = str(getattr(witness, "right_atom_id", ""))
        if not left or not right:
            raise SemanticProjectionError("compatibility witness endpoints required")
        witness_id = "compatibility:" + canonical_sha256({"endpoints": list(sorted((left, right)))})
        latest = store.latest_witness_version(witness_id)
        candidate = RelationWitnessVersion(
            witness_id=witness_id,
            left_atom_id=left,
            right_atom_id=right,
            relation_type=_enum_text(getattr(witness, "relation", "UNKNOWN")),
            reason=str(getattr(witness, "reason", "")),
            condition=(None if getattr(witness, "condition", None) is None else str(getattr(witness, "condition"))),
            evidence_ids=tuple(str(item) for item in getattr(witness, "evidence_ids", ())),
            payload={"source_projection": "TypedKnowledgeLattice.CompatibilityWitness"},
            valid_from_sequence=sequence,
            supersedes_version_id=None if latest is None else latest.version_id,
        )
        seen_witnesses.append(witness_id)
        if latest is not None and _witness_semantics(latest) == _witness_semantics(candidate):
            unchanged_witnesses.append(witness_id)
        else:
            added_witnesses.append(candidate)

    batch = SemanticMutationBatch(
        sequence=sequence,
        base_semantic_revision=store.semantic_revision(sequence - 1),
        new_fibers=new_fibers,
        atom_versions=tuple(added_atoms),
        witness_versions=tuple(added_witnesses),
    )
    preview = store.preview_batch_revision(batch)
    return LatticeImportPlan(
        batch=batch,
        atom_ids_seen=tuple(seen_atoms),
        witness_ids_seen=tuple(seen_witnesses),
        unchanged_atom_ids=tuple(unchanged_atoms),
        unchanged_witness_ids=tuple(unchanged_witnesses),
        preview_semantic_revision=preview,
    )


def commit_typed_knowledge_lattice_import(
    store: SqliteSemanticStateStore,
    plan: LatticeImportPlan,
    *,
    snapshot_id: str,
) -> LatticeImportReport:
    store.commit_batch(
        plan.batch,
        committed_snapshot_id=snapshot_id,
        expected_semantic_revision=plan.preview_semantic_revision,
    )
    return LatticeImportReport(
        snapshot_id=snapshot_id,
        sequence=plan.batch.sequence,
        batch_id=plan.batch.batch_id,
        atom_ids_seen=plan.atom_ids_seen,
        witness_ids_seen=plan.witness_ids_seen,
        atom_versions_added=tuple(item.version_id for item in plan.batch.atom_versions),
        witness_versions_added=tuple(item.version_id for item in plan.batch.witness_versions),
        unchanged_atom_ids=plan.unchanged_atom_ids,
        unchanged_witness_ids=plan.unchanged_witness_ids,
        semantic_revision=plan.preview_semantic_revision,
    )


def import_typed_knowledge_lattice(
    store: SqliteSemanticStateStore,
    lattice: object,
    *,
    snapshot_id: str,
    sequence: int,
) -> LatticeImportReport:
    """Convenience wrapper when the caller already constructed the after snapshot."""
    plan = plan_typed_knowledge_lattice_import(store, lattice, sequence=sequence)
    return commit_typed_knowledge_lattice_import(store, plan, snapshot_id=snapshot_id)
