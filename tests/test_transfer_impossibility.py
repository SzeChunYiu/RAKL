"""Hostile tests for the typed-refusal transfer (#609 follow-on).

The load-bearing property is G1: a CERTIFIABLY_IMPOSSIBLE verdict must never be
emitted on a refusal that some other admissible witness could repair, nor on an
open-world target, nor on an incomplete exhaustion. A wrong impossibility
certificate is worse than a plain refusal, so every test below is written to
try to provoke one.
"""

from __future__ import annotations

import pytest

from rakl.structural_transfer import assess_transfer
from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    StructuralWitness,
    TransferDecision,
)
from rakl.transfer_impossibility import (
    RefusalKind,
    TargetDeclaration,
    classify_refusal,
    classify_refusal_faithful_import,
    exists_licensing_role_mapping,
    structural_obstructions,
)


def _object(structure_id, *, qoi="Q", roles=("a",), relations=(), invariants=frozenset(), boundaries=()):
    return StructuralObject(
        structure_id=structure_id,
        domain="test",
        qoi=qoi,
        context_id=f"ctx-{structure_id}",
        roles=tuple(StructuralRole(role_id=r, kind="generic") for r in roles),
        relations=tuple(
            StructuralRelation(source_role=a, relation_type=t, target_role=b)
            for a, t, b in relations
        ),
        invariants=invariants,
        boundaries=tuple(BoundaryCondition(key=k, value=v) for k, v in boundaries),
        evidence_ids=(f"ev-{structure_id}",),
    )


def _witness(source, target, mapping, *, preserved=None, boundaries=()):
    return StructuralWitness(
        witness_id="w",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        role_mapping=mapping,
        preserved_invariants=source.invariants if preserved is None else preserved,
        non_preserved_properties=frozenset(),
        required_target_boundaries=tuple(
            BoundaryCondition(key=k, value=v) for k, v in boundaries
        ),
        evidence_ids=("ev-w",),
    )


def _closed(target):
    return TargetDeclaration(
        target_structure_id=target.structure_id, closed_world=True, declared_by="test"
    )


def _open(target):
    return TargetDeclaration(target_structure_id=target.structure_id, closed_world=False)


# --------------------------------------------------------------------------
# G1: no false impossibility certificates
# --------------------------------------------------------------------------


def test_repairable_role_mapping_is_only_merely_unlicensed():
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),))
    target = _object("t", roles=("x", "y"), relations=(("x", "causes", "y"),))
    bad = _witness(source, target, (("a", "y"), ("b", "x")))

    assert assess_transfer(source, target, bad).decision is TransferDecision.REJECTED
    refusal = classify_refusal(source, target, bad, target_declaration=_closed(target))
    assert refusal.kind is RefusalKind.MERELY_UNLICENSED
    assert refusal.certificate is None

    good = _witness(source, target, (("a", "x"), ("b", "y")))
    assert assess_transfer(source, target, good).decision is TransferDecision.LICENSED


def test_repairable_boundary_declaration_is_only_merely_unlicensed():
    source = _object("s")
    target = _object("t", roles=("x",), boundaries=(("regime", "low"),))
    bad = _witness(source, target, (("a", "x"),), boundaries=(("regime", "high"),))

    refusal = classify_refusal(source, target, bad, target_declaration=_closed(target))
    assert refusal.kind is RefusalKind.MERELY_UNLICENSED

    good = _witness(source, target, (("a", "x"),))
    assert assess_transfer(source, target, good).decision is TransferDecision.LICENSED


def test_open_world_target_never_certifies_even_with_real_structural_gap():
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),))
    target = _object("t", roles=("x", "y"), relations=(("x", "correlates", "y"),))
    witness = _witness(source, target, (("a", "x"), ("b", "y")))

    # the gap is real under a closed world ...
    assert (
        classify_refusal(source, target, witness, target_declaration=_closed(target)).kind
        is RefusalKind.CERTIFIABLY_IMPOSSIBLE
    )
    # ... but absence of evidence is not evidence of absence
    refusal = classify_refusal(source, target, witness, target_declaration=_open(target))
    assert refusal.kind is RefusalKind.MERELY_UNLICENSED
    assert refusal.reasons == ("target_not_declared_closed_world",)


def test_budget_exhaustion_never_certifies():
    roles = tuple(f"a{i}" for i in range(6))
    troles = tuple(f"x{i}" for i in range(7))
    source = _object(
        "s",
        roles=roles,
        relations=tuple((roles[i], "causes", roles[i + 1]) for i in range(5))
        + (("a0", "absent_type", "a5"),),
    )
    target = _object(
        "t",
        roles=troles,
        relations=tuple(
            (troles[i], "causes", troles[j])
            for i in range(len(troles))
            for j in range(len(troles))
            if i != j
        ),
    )
    witness = _witness(source, target, tuple((roles[i], troles[i]) for i in range(6)))

    refusal = classify_refusal(
        source, target, witness, target_declaration=_closed(target), max_search_nodes=5
    )
    assert refusal.kind is RefusalKind.MERELY_UNLICENSED
    assert refusal.search_completed is False
    assert refusal.reasons == ("presentation_space_exhaustion_incomplete",)


def test_declaration_identity_mismatch_never_certifies():
    source = _object("s", qoi="Q")
    target = _object("t", qoi="OTHER", roles=("x",))
    witness = _witness(source, target, (("a", "x"),))
    wrong = TargetDeclaration(
        target_structure_id="somewhere-else", closed_world=True, declared_by="test"
    )
    refusal = classify_refusal(source, target, witness, target_declaration=wrong)
    assert refusal.kind is RefusalKind.MERELY_UNLICENSED
    assert refusal.reasons == ("target_declaration_identity_mismatch",)


# --------------------------------------------------------------------------
# G2: the strong verdict actually fires
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source_kwargs,target_kwargs,expected_criterion",
    [
        (
            {"roles": ("a", "b"), "relations": (("a", "causes", "b"),)},
            {"roles": ("x", "y"), "relations": (("x", "correlates", "y"),)},
            "S3_RELATIONS",
        ),
        ({"qoi": "Q"}, {"qoi": "OTHER", "roles": ("x",)}, "S1_QOI"),
        (
            {"invariants": frozenset({"energy"})},
            {"roles": ("x",), "invariants": frozenset()},
            "S2_INVARIANTS",
        ),
    ],
)
def test_genuine_structural_gaps_certify(source_kwargs, target_kwargs, expected_criterion):
    source = _object("s", **source_kwargs)
    target = _object("t", **target_kwargs)
    mapping = tuple(zip(sorted(source.role_ids), sorted(target.role_ids)))
    witness = _witness(source, target, mapping)

    refusal = classify_refusal(source, target, witness, target_declaration=_closed(target))
    assert refusal.kind is RefusalKind.CERTIFIABLY_IMPOSSIBLE
    assert refusal.certificate is not None
    assert expected_criterion in refusal.certificate.failed_criteria


def test_certificate_carries_structural_content():
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),), invariants=frozenset({"energy"}))
    target = _object("t", roles=("x", "y"), relations=(("x", "correlates", "y"),))
    witness = _witness(source, target, (("a", "x"), ("b", "y")))
    refusal = classify_refusal(source, target, witness, target_declaration=_closed(target))
    cert = refusal.certificate
    assert cert is not None
    assert cert.missing_invariants == ("energy",)
    assert cert.unmatchable_relation_types == ("causes:1",)


# --------------------------------------------------------------------------
# G3: the control arm behaves as the control arm
# --------------------------------------------------------------------------


def test_faithful_import_emits_false_certificate_on_repairable_witness():
    """The control arm is SUPPOSED to fail here. This documents the cost of
    importing the verdict form without the source's preconditions."""
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),))
    target = _object("t", roles=("x", "y"), relations=(("x", "causes", "y"),))
    bad = _witness(source, target, (("a", "y"), ("b", "x")))

    assert (
        classify_refusal_faithful_import(source, target, bad).kind
        is RefusalKind.CERTIFIABLY_IMPOSSIBLE
    )
    assert (
        classify_refusal(source, target, bad, target_declaration=_closed(target)).kind
        is RefusalKind.MERELY_UNLICENSED
    )


# --------------------------------------------------------------------------
# search primitive
# --------------------------------------------------------------------------


def test_role_mapping_search_respects_injectivity_and_cardinality():
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),))
    target = _object("t", roles=("x",), relations=())
    result, nodes = exists_licensing_role_mapping(source, target)
    assert result is False
    assert nodes == 0

    certificate, completed = structural_obstructions(source, target)
    assert completed is True
    assert certificate.role_cardinality_obstruction is True


def test_search_finds_non_identity_mapping():
    source = _object("s", roles=("a", "b"), relations=(("a", "causes", "b"),))
    target = _object("t", roles=("x", "y"), relations=(("y", "causes", "x"),))
    result, _ = exists_licensing_role_mapping(source, target)
    assert result is True


def test_budget_exhaustion_returns_none_not_false():
    roles = tuple(f"a{i}" for i in range(5))
    troles = tuple(f"x{i}" for i in range(6))
    source = _object("s", roles=roles, relations=(("a0", "absent", "a4"),))
    target = _object(
        "t",
        roles=troles,
        relations=tuple(
            (troles[i], "causes", troles[j])
            for i in range(len(troles))
            for j in range(len(troles))
            if i != j
        ),
    )
    result, _ = exists_licensing_role_mapping(source, target, max_search_nodes=3)
    assert result is None


# --------------------------------------------------------------------------
# authority + non-interference
# --------------------------------------------------------------------------


def test_typed_refusal_grants_no_authority():
    source = _object("s", qoi="Q")
    target = _object("t", qoi="OTHER", roles=("x",))
    witness = _witness(source, target, (("a", "x"),))
    refusal = classify_refusal(source, target, witness, target_declaration=_closed(target))
    assert refusal.grants_scientific_authority is False


def test_licensed_and_cannot_check_are_not_typed_as_refusals():
    source = _object("s")
    target = _object("t", roles=("x",))
    good = _witness(source, target, (("a", "x"),))
    assert (
        classify_refusal(source, target, good, target_declaration=_closed(target)).kind
        is RefusalKind.NOT_A_REFUSAL
    )

    mismatched = StructuralWitness(
        witness_id="w",
        source_structure_id="wrong",
        target_structure_id=target.structure_id,
        role_mapping=(("a", "x"),),
        preserved_invariants=frozenset(),
        non_preserved_properties=frozenset(),
        required_target_boundaries=(),
        evidence_ids=("ev-w",),
    )
    refusal = classify_refusal(source, target, mismatched, target_declaration=_closed(target))
    assert refusal.kind is RefusalKind.NOT_A_REFUSAL
    assert refusal.base_decision is TransferDecision.CANNOT_CHECK


def test_closed_world_declaration_requires_a_declarer():
    with pytest.raises(ValueError):
        TargetDeclaration(target_structure_id="t", closed_world=True, declared_by="")
