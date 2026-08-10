from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import comb

from .typed_lattice import TypedKnowledgeLattice


class LatticeGrowthClass(str, Enum):
    """Observed change between two canonical/active lattice snapshots.

    The labels are descriptive metrology, not scientific-authority certificates.
    In particular, ``volume`` is a discrete occupancy proxy over registered
    (fiber, atom-kind) cells; it is not a Euclidean or latent-vector volume.
    """

    EXPANSION = "EXPANSION"
    SEMANTIC_DENSIFICATION = "SEMANTIC_DENSIFICATION"
    RELATIONAL_DENSIFICATION = "RELATIONAL_DENSIFICATION"
    EVIDENCE_DENSIFICATION = "EVIDENCE_DENSIFICATION"
    MIXED_DENSIFICATION = "MIXED_DENSIFICATION"
    FLAT = "FLAT"
    CONTRACTION_OR_VIEW_CHANGE = "CONTRACTION_OR_VIEW_CHANGE"


@dataclass(frozen=True)
class LatticeSnapshotMetrics:
    atom_count: int
    fiber_count: int
    kind_count: int
    occupied_volume_cells: int
    type_span_cells: int
    occupancy_ratio: float
    atom_cell_density: float
    witness_count: int
    relation_density: float
    atom_evidence_bindings: int
    witness_evidence_bindings: int
    evidence_binding_count: int
    distinct_evidence_sources: int


@dataclass(frozen=True)
class LatticeTransitionMetrics:
    growth_class: LatticeGrowthClass
    volume_delta_cells: int
    atom_delta: int
    witness_delta: int
    evidence_binding_delta: int
    distinct_evidence_source_delta: int
    atom_cell_density_delta: float
    relation_density_delta: float

    @property
    def flat(self) -> bool:
        return self.growth_class is LatticeGrowthClass.FLAT

    @property
    def adds_semantic_volume(self) -> bool:
        return self.volume_delta_cells > 0


class ActiveCapacityAction(str, Enum):
    KEEP_ACTIVE = "KEEP_ACTIVE"
    REJECT_REDUNDANT_ACTIVE_UPDATE = "REJECT_REDUNDANT_ACTIVE_UPDATE"
    COMPACT_OR_DEMOTE_ACTIVE_VIEW = "COMPACT_OR_DEMOTE_ACTIVE_VIEW"


@dataclass(frozen=True)
class ActiveLatticeCapacityPolicy:
    """Capacity guard for the *active* lattice/materialized view.

    Canonical evidence remains append-only and content-addressable elsewhere.  This
    policy prevents active-state/prompt growth from being mistaken for permission to
    delete evidence.  Thresholds are deployment parameters, not epistemic constants.
    """

    max_active_atoms: int
    max_active_witnesses: int
    max_active_fibers: int
    max_type_span_cells: int

    def __post_init__(self) -> None:
        if min(
            self.max_active_atoms,
            self.max_active_witnesses,
            self.max_active_fibers,
            self.max_type_span_cells,
        ) < 1:
            raise ValueError("active lattice capacity coordinates must be positive")


@dataclass(frozen=True)
class ActiveCapacityDecision:
    action: ActiveCapacityAction
    reasons: tuple[str, ...]
    canonical_archive_must_be_preserved: bool = True


def measure_lattice(lattice: TypedKnowledgeLattice) -> LatticeSnapshotMetrics:
    atoms = tuple(lattice.atoms.values())
    witnesses = tuple(lattice.witnesses.values())
    fibers = {atom.fiber_id for atom in atoms}
    kinds = {atom.kind for atom in atoms}
    occupied_cells = {(atom.fiber_id, atom.kind) for atom in atoms}

    atom_count = len(atoms)
    witness_count = len(witnesses)
    type_span_cells = len(fibers) * len(kinds)
    possible_pairs = comb(atom_count, 2) if atom_count >= 2 else 0

    atom_evidence_bindings = sum(len(set(atom.evidence_ids)) for atom in atoms)
    witness_evidence_bindings = sum(len(set(witness.evidence_ids)) for witness in witnesses)
    evidence_sources = {
        evidence_id
        for atom in atoms
        for evidence_id in atom.evidence_ids
    } | {
        evidence_id
        for witness in witnesses
        for evidence_id in witness.evidence_ids
    }

    return LatticeSnapshotMetrics(
        atom_count=atom_count,
        fiber_count=len(fibers),
        kind_count=len(kinds),
        occupied_volume_cells=len(occupied_cells),
        type_span_cells=type_span_cells,
        occupancy_ratio=(len(occupied_cells) / type_span_cells if type_span_cells else 0.0),
        atom_cell_density=(atom_count / len(occupied_cells) if occupied_cells else 0.0),
        witness_count=witness_count,
        relation_density=(witness_count / possible_pairs if possible_pairs else 0.0),
        atom_evidence_bindings=atom_evidence_bindings,
        witness_evidence_bindings=witness_evidence_bindings,
        evidence_binding_count=atom_evidence_bindings + witness_evidence_bindings,
        distinct_evidence_sources=len(evidence_sources),
    )


def compare_lattices(
    before: TypedKnowledgeLattice,
    after: TypedKnowledgeLattice,
) -> LatticeTransitionMetrics:
    left = measure_lattice(before)
    right = measure_lattice(after)

    volume_delta = right.occupied_volume_cells - left.occupied_volume_cells
    atom_delta = right.atom_count - left.atom_count
    witness_delta = right.witness_count - left.witness_count
    evidence_delta = right.evidence_binding_count - left.evidence_binding_count
    source_delta = right.distinct_evidence_sources - left.distinct_evidence_sources

    primitive_deltas = (volume_delta, atom_delta, witness_delta, evidence_delta, source_delta)
    if any(delta < 0 for delta in primitive_deltas):
        growth = LatticeGrowthClass.CONTRACTION_OR_VIEW_CHANGE
    elif all(delta == 0 for delta in primitive_deltas):
        growth = LatticeGrowthClass.FLAT
    elif volume_delta > 0:
        growth = LatticeGrowthClass.EXPANSION
    else:
        semantic = atom_delta > 0
        relational = witness_delta > 0
        evidential = evidence_delta > 0 or source_delta > 0
        active = sum((semantic, relational, evidential))
        if active > 1:
            growth = LatticeGrowthClass.MIXED_DENSIFICATION
        elif semantic:
            growth = LatticeGrowthClass.SEMANTIC_DENSIFICATION
        elif relational:
            growth = LatticeGrowthClass.RELATIONAL_DENSIFICATION
        else:
            growth = LatticeGrowthClass.EVIDENCE_DENSIFICATION

    return LatticeTransitionMetrics(
        growth_class=growth,
        volume_delta_cells=volume_delta,
        atom_delta=atom_delta,
        witness_delta=witness_delta,
        evidence_binding_delta=evidence_delta,
        distinct_evidence_source_delta=source_delta,
        atom_cell_density_delta=right.atom_cell_density - left.atom_cell_density,
        relation_density_delta=right.relation_density - left.relation_density,
    )


def evaluate_active_capacity(
    snapshot: LatticeSnapshotMetrics,
    transition: LatticeTransitionMetrics,
    policy: ActiveLatticeCapacityPolicy,
) -> ActiveCapacityDecision:
    if transition.flat:
        return ActiveCapacityDecision(
            ActiveCapacityAction.REJECT_REDUNDANT_ACTIVE_UPDATE,
            ("no_registered_lattice_coordinate_changed",),
        )

    exceeded: list[str] = []
    if snapshot.atom_count > policy.max_active_atoms:
        exceeded.append("active_atom_cap_exceeded")
    if snapshot.witness_count > policy.max_active_witnesses:
        exceeded.append("active_witness_cap_exceeded")
    if snapshot.fiber_count > policy.max_active_fibers:
        exceeded.append("active_fiber_cap_exceeded")
    if snapshot.type_span_cells > policy.max_type_span_cells:
        exceeded.append("active_type_span_cap_exceeded")

    if exceeded:
        return ActiveCapacityDecision(
            ActiveCapacityAction.COMPACT_OR_DEMOTE_ACTIVE_VIEW,
            tuple(exceeded) + (
                "preserve_canonical_archive_and_rebuild_a_bounded_active_view",
            ),
        )

    return ActiveCapacityDecision(
        ActiveCapacityAction.KEEP_ACTIVE,
        ("active_lattice_within_registered_capacity",),
    )
