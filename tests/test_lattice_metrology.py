from __future__ import annotations

from rakl.lattice_metrology import (
    ActiveCapacityAction,
    ActiveLatticeCapacityPolicy,
    LatticeGrowthClass,
    compare_lattices,
    evaluate_active_capacity,
    measure_lattice,
)
from rakl.typed_lattice import (
    CompatibilityWitness,
    KnowledgeAtom,
    KnowledgeAtomKind,
    LatticeCompatibility,
    TypedKnowledgeLattice,
)


def _base() -> TypedKnowledgeLattice:
    lattice = TypedKnowledgeLattice.empty()
    lattice.add_atom(KnowledgeAtom("a1", "f1", KnowledgeAtomKind.REPRESENTATION, "law", ("s1",)))
    lattice.add_atom(KnowledgeAtom("a2", "f2", KnowledgeAtomKind.REGIME, "earth", ("s2",)))
    lattice.add_witness(
        CompatibilityWitness("a1", "a2", LatticeCompatibility.COMPATIBLE, "same scope", evidence_ids=("s1", "s2"))
    )
    return lattice


def test_new_cell_is_discrete_volume_expansion():
    before = _base()
    after = _base()
    after.add_atom(KnowledgeAtom("a3", "f3", KnowledgeAtomKind.QOI, "target", ("s3",)))

    change = compare_lattices(before, after)
    assert change.growth_class is LatticeGrowthClass.EXPANSION
    assert change.volume_delta_cells == 1
    assert change.atom_delta == 1
    assert change.adds_semantic_volume


def test_new_atom_in_existing_cell_is_semantic_densification():
    before = _base()
    after = _base()
    after.add_atom(KnowledgeAtom("a3", "f1", KnowledgeAtomKind.REPRESENTATION, "finite correction", ("s3",)))

    change = compare_lattices(before, after)
    assert change.volume_delta_cells == 0
    assert change.atom_delta == 1
    assert change.growth_class is LatticeGrowthClass.SEMANTIC_DENSIFICATION
    assert change.atom_cell_density_delta > 0


def test_existing_relation_can_gain_evidence_without_fake_volume():
    before = _base()

    # Typed witness identities are immutable within one snapshot. Build the later
    # snapshot explicitly with the same relation semantics plus a new source pin.
    after = TypedKnowledgeLattice.empty()
    for atom in before.atoms.values():
        after.add_atom(atom)
    after.add_witness(
        CompatibilityWitness("a1", "a2", LatticeCompatibility.COMPATIBLE, "same scope", evidence_ids=("s1", "s2", "s3"))
    )

    change = compare_lattices(before, after)
    assert change.volume_delta_cells == 0
    assert change.atom_delta == 0
    assert change.witness_delta == 0
    assert change.evidence_binding_delta == 1
    assert change.growth_class is LatticeGrowthClass.EVIDENCE_DENSIFICATION


def test_identical_snapshot_is_flat_and_rejected_from_active_growth():
    lattice = _base()
    snapshot = measure_lattice(lattice)
    change = compare_lattices(lattice, lattice)
    policy = ActiveLatticeCapacityPolicy(10, 10, 10, 100)

    assert change.growth_class is LatticeGrowthClass.FLAT
    decision = evaluate_active_capacity(snapshot, change, policy)
    assert decision.action is ActiveCapacityAction.REJECT_REDUNDANT_ACTIVE_UPDATE
    assert decision.canonical_archive_must_be_preserved


def test_capacity_overflow_demotes_active_view_without_deleting_archive():
    before = TypedKnowledgeLattice.empty()
    after = _base()
    snapshot = measure_lattice(after)
    change = compare_lattices(before, after)
    policy = ActiveLatticeCapacityPolicy(
        max_active_atoms=1,
        max_active_witnesses=1,
        max_active_fibers=1,
        max_type_span_cells=1,
    )

    decision = evaluate_active_capacity(snapshot, change, policy)
    assert decision.action is ActiveCapacityAction.COMPACT_OR_DEMOTE_ACTIVE_VIEW
    assert "active_atom_cap_exceeded" in decision.reasons
    assert decision.canonical_archive_must_be_preserved
