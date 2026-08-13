from rakl.structural_transfer_use import *
from rakl.structural_types import BoundaryCondition, StructuralObject, StructuralRelation, StructuralRole, StructuralWitness


def objects():
    s = StructuralObject("s", "a", "q", "c", (StructuralRole("x", "node"),), (), frozenset(), (), ("e",))
    t = StructuralObject("t", "b", "q", "c", (StructuralRole("y", "node"),), (), frozenset(), (), ("e",))
    w = StructuralWitness("w", "s", "t", (("x", "y"),), frozenset(), frozenset({"entity_semantics"}), (), ("we",))
    return s, t, w


def test_non_preserved_property_must_be_acknowledged():
    s, t, w = objects()
    u = StructuralTransferUseContract("u", "q", frozenset(), frozenset())
    assert assess_transfer_for_use(s, t, w, u).verdict is TransferUseVerdict.CANNOT_CHECK


def test_required_non_preserved_property_rejects():
    s, t, w = objects()
    u = StructuralTransferUseContract(
        "u", "q", frozenset({"entity_semantics"}), frozenset(), (("entity_semantics", "receipt"),)
    )
    assert assess_transfer_for_use(s, t, w, u).verdict is TransferUseVerdict.REJECTED


def test_acknowledged_irrelevant_loss_allows_base_transfer():
    s, t, w = objects()
    u = StructuralTransferUseContract("u", "q", frozenset(), frozenset({"entity_semantics"}))
    assert assess_transfer_for_use(
        s, t, w, u, resolved_witness_evidence_ids=frozenset({"we"})
    ).verdict is TransferUseVerdict.LICENSED_FOR_USE


def test_named_property_receipt_must_be_resolved_by_assurance_layer():
    s, t, w = objects()
    u = StructuralTransferUseContract(
        "u", "q", frozenset({"formal_property"}), frozenset({"entity_semantics"}),
        (("formal_property", "receipt:formal"),)
    )
    assert assess_transfer_for_use(s, t, w, u).verdict is TransferUseVerdict.CANNOT_CHECK
    assert assess_transfer_for_use(
        s, t, w, u, resolved_witness_evidence_ids=frozenset({"we"}),
        resolved_preservation_receipt_ids=frozenset({"receipt:formal"})
    ).verdict is TransferUseVerdict.LICENSED_FOR_USE


def test_witness_named_evidence_is_not_self_resolving():
    s, t, w = objects()
    u = StructuralTransferUseContract("u", "q", frozenset(), frozenset({"entity_semantics"}))
    result = assess_transfer_for_use(s, t, w, u)
    assert result.verdict is TransferUseVerdict.CANNOT_CHECK
    assert "witness_evidence_unresolved:we" in result.reasons
