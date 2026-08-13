import pytest
from rakl.structural_types import (
    BoundaryCondition,
    ChartTransitionWitness,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    StructuralWitness,
)


def base_object(**overrides):
    values = dict(
        structure_id="s", domain="d", qoi="q", context_id="c",
        roles=(StructuralRole("x", "node"),), relations=(), invariants=frozenset(),
        boundaries=(), evidence_ids=("e",),
    )
    values.update(overrides)
    return StructuralObject(**values)


def test_duplicate_boundary_keys_rejected_before_boundary_map_can_collapse_them():
    with pytest.raises(ValueError):
        base_object(boundaries=(BoundaryCondition("b", "1"), BoundaryCondition("b", "2")))


def test_duplicate_relation_signatures_rejected():
    r = StructuralRelation("x", "rel", "x")
    with pytest.raises(ValueError):
        base_object(relations=(r, r))


def test_duplicate_or_blank_structural_evidence_rejected():
    with pytest.raises(ValueError):
        base_object(evidence_ids=("e", "e"))
    with pytest.raises(ValueError):
        base_object(evidence_ids=("",))


def test_witness_boundary_and_evidence_contract_is_unambiguous():
    with pytest.raises(ValueError):
        StructuralWitness(
            "w", "s", "t", (("x", "y"),), frozenset(), frozenset(),
            (BoundaryCondition("b", "1"), BoundaryCondition("b", "2")), ("e",),
        )
    with pytest.raises(ValueError):
        StructuralWitness("w", "s", "t", (("x", "y"),), frozenset(), frozenset(), (), ("",))


def test_chart_transition_rejects_blank_mapping_and_duplicate_evidence():
    with pytest.raises(ValueError):
        ChartTransitionWitness("w", "a", "b", (("", "y"),), ("e",))
    with pytest.raises(ValueError):
        ChartTransitionWitness("w", "a", "b", (("x", "y"),), ("e", "e"))
