from __future__ import annotations

from rakl.lattice_metrology import (
    ActiveCapacityAction,
    ActiveLatticeCapacityPolicy,
    EpistemicStateSummary,
    LatticeGrowthClass,
    LatticeMeasurementBasis,
    compare_epistemic_state,
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


def _basis(basis_id: str = "demo-v1") -> LatticeMeasurementBasis:
    return LatticeMeasurementBasis(
        basis_id=basis_id,
        fiber_partition_semantics="registered research-fiber ids are stable semantic partitions",
        kind_schema_version="KnowledgeAtomKind:v1",
        identity_policy_id="exact-identity-plus-context:v1",
        context_schema_id="context:v1",
    )


def test_new_cell_is_discrete_volume_expansion():
    before = _base()
    after = _base()
    after.add_atom(KnowledgeAtom("a3", "f3", KnowledgeAtomKind.QOI, "target", ("s3",)))
    change = compare_lattices(before, after)
    assert change.growth_class is LatticeGrowthClass.EXPANSION
    assert change.volume_delta_cells == 1
    assert change.atom_delta == 1
    assert change.adds_semantic_volume


def test_new_atom_in_existing_cell_can_be_pure_semantic_densification():
    before = _base()
    after = _base()
    after.add_atom(KnowledgeAtom("a3", "f1", KnowledgeAtomKind.REPRESENTATION, "candidate representation"))
    change = compare_lattices(before, after)
    assert change.volume_delta_cells == 0
    assert change.atom_delta == 1
    assert change.evidence_binding_delta == 0
    assert change.growth_class is LatticeGrowthClass.SEMANTIC_DENSIFICATION
    assert change.atom_cell_density_delta > 0


def test_existing_relation_can_gain_evidence_without_fake_volume():
    before = _base()
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


def test_frozen_measurement_basis_allows_longitudinal_comparison():
    basis = _basis()
    change = compare_lattices(_base(), _base(), before_basis=basis, after_basis=basis)
    assert change.basis_comparable
    assert change.basis_fingerprint == basis.fingerprint
    assert change.growth_class is LatticeGrowthClass.FLAT


def test_fiber_partition_or_schema_change_invalidates_volume_comparison():
    before_basis = _basis("demo-v1")
    after_basis = LatticeMeasurementBasis(
        basis_id="demo-v2",
        fiber_partition_semantics="fibers were split into finer partitions",
        kind_schema_version="KnowledgeAtomKind:v1",
        identity_policy_id="exact-identity-plus-context:v1",
        context_schema_id="context:v1",
    )
    change = compare_lattices(
        _base(),
        _base(),
        before_basis=before_basis,
        after_basis=after_basis,
    )
    assert not change.basis_comparable
    assert change.growth_class is LatticeGrowthClass.COMPARISON_INVALID_BASIS
    assert change.volume_delta_cells == 0
    assert change.comparison_issues == ("measurement_basis_fingerprint_changed",)


def test_missing_basis_on_one_side_fails_closed():
    change = compare_lattices(_base(), _base(), before_basis=_basis())
    assert not change.basis_comparable
    assert change.growth_class is LatticeGrowthClass.COMPARISON_INVALID_BASIS


def test_epistemic_value_is_separate_from_lattice_geometry():
    before = EpistemicStateSummary(
        blocking_epistemic_cuts=1,
        target_support_paths=0,
        distinct_independent_evidence_roots=6,
        negative_history_objects=1,
    )
    after = EpistemicStateSummary(
        blocking_epistemic_cuts=0,
        target_support_paths=1,
        distinct_independent_evidence_roots=7,
        negative_history_objects=1,
    )
    gain = compare_epistemic_state(before, after)
    assert gain.blocking_cuts_closed == 1
    assert gain.support_paths_opened == 1
    assert gain.independent_evidence_roots_added == 1
    assert gain.target_access_improved
    assert gain.evidential_robustness_improved
    assert not gain.completely_flat


def test_identical_epistemic_state_is_flat_even_if_graph_layout_or_prose_changes():
    state = EpistemicStateSummary(1, 0, 6, 1)
    gain = compare_epistemic_state(state, state)
    assert gain.completely_flat
    assert not gain.target_access_improved


def test_identical_snapshot_is_flat_and_rejected_from_active_growth():
    lattice = _base()
    snapshot = measure_lattice(lattice)
    change = compare_lattices(lattice, lattice)
    policy = ActiveLatticeCapacityPolicy(10, 10, 10, 100)
    assert change.growth_class is LatticeGrowthClass.FLAT
    decision = evaluate_active_capacity(snapshot, change, policy)
    assert decision.action is ActiveCapacityAction.REJECT_REDUNDANT_ACTIVE_UPDATE
    assert decision.canonical_archive_must_be_preserved


def test_invalid_basis_cannot_drive_a_normal_active_capacity_decision():
    lattice = _base()
    snapshot = measure_lattice(lattice)
    change = compare_lattices(
        lattice,
        lattice,
        before_basis=_basis("v1"),
        after_basis=_basis("v2"),
    )
    decision = evaluate_active_capacity(snapshot, change, ActiveLatticeCapacityPolicy(10, 10, 10, 100))
    assert decision.action is ActiveCapacityAction.COMPACT_OR_DEMOTE_ACTIVE_VIEW
    assert "basis_invalid" in decision.reasons[0]


def test_capacity_overflow_demotes_active_view_without_deleting_archive():
    before = TypedKnowledgeLattice.empty()
    after = _base()
    snapshot = measure_lattice(after)
    change = compare_lattices(before, after)
    policy = ActiveLatticeCapacityPolicy(1, 1, 1, 1)
    decision = evaluate_active_capacity(snapshot, change, policy)
    assert decision.action is ActiveCapacityAction.COMPACT_OR_DEMOTE_ACTIVE_VIEW
    assert "active_atom_cap_exceeded" in decision.reasons
    assert decision.canonical_archive_must_be_preserved
