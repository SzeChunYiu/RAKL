from rakl.compatibility_complex import TypedCompatibilityComplex
from rakl.typed_lattice import TypedKnowledgeLattice


def test_historical_lattice_name_is_explicitly_aliased_to_compatibility_complex():
    assert TypedCompatibilityComplex is TypedKnowledgeLattice
    structure = TypedCompatibilityComplex.empty()
    assert structure.atoms == {}
    assert structure.witnesses == {}


def test_compatibility_complex_does_not_claim_order_theoretic_operations():
    structure = TypedCompatibilityComplex.empty()
    assert not hasattr(structure, "meet")
    assert not hasattr(structure, "join")
    assert not hasattr(structure, "partial_order")
