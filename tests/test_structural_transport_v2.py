from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    TransferDecision,
)
from rakl.structural_transport_v2 import (
    ObligationKind,
    ObligationRequirement,
    ObligationStatus,
    StructuralWitnessV2,
    TransferObligation,
    assess_transfer_v2,
)


def _object(
    structure_id: str,
    context_id: str,
    *,
    qoi: str = "stability",
    boundary: str = "continual",
    matching_invariant: bool = True,
) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain="test-domain",
        qoi=qoi,
        context_id=context_id,
        roles=(StructuralRole("a", "input"), StructuralRole("b", "capacity")),
        relations=(StructuralRelation("a", "competes_with", "b"),),
        invariants=frozenset(
            {"arrival_gt_service_implies_growth"}
            if matching_invariant
            else {"different_invariant"}
        ),
        boundaries=(BoundaryCondition("flow_regime", boundary),),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _witness(
    source: StructuralObject,
    target: StructuralObject,
    obligations: list[TransferObligation],
    **kwargs: object,
) -> StructuralWitnessV2:
    return StructuralWitnessV2(
        witness_id="w",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        source_context_id=source.context_id,
        target_context_id=target.context_id,
        qoi="stability",
        role_mapping=(("a", "a"), ("b", "b")),
        obligations=tuple(obligations),
        **kwargs,
    )


def test_valid_distant_transfer_can_license_when_obligations_hold() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "qoi",
                ObligationKind.QOI,
                "stability",
                "stability",
                evidence_ids=("evidence:qoi",),
            ),
            TransferObligation(
                "invariant",
                ObligationKind.INVARIANT,
                "arrival_gt_service_implies_growth",
                "arrival_gt_service_implies_growth",
                evidence_ids=("evidence:invariant",),
            ),
            TransferObligation(
                "boundary",
                ObligationKind.BOUNDARY,
                "flow_regime",
                "continual",
                evidence_ids=("evidence:boundary",),
            ),
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.LICENSED


def test_missing_role_mapping_is_cannot_check_not_rejected() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = StructuralWitnessV2(
        witness_id="w",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        source_context_id=source.context_id,
        target_context_id=target.context_id,
        qoi="stability",
        role_mapping=(("a", "a"),),
        obligations=(
            TransferObligation(
                "role-b",
                ObligationKind.ROLE,
                "b",
                "b",
                evidence_ids=("evidence:role",),
            ),
        ),
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.CANNOT_CHECK


def test_boundary_mismatch_rejects() -> None:
    source = _object("source", "source-context")
    target = _object("target", "target-context", boundary="finite_batch")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "boundary",
                ObligationKind.BOUNDARY,
                "flow_regime",
                "continual",
                evidence_ids=("evidence:boundary",),
            )
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.REJECTED


def test_missing_required_evidence_is_cannot_check() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "invariant",
                ObligationKind.INVARIANT,
                "arrival_gt_service_implies_growth",
                "arrival_gt_service_implies_growth",
            )
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.CANNOT_CHECK


def test_explicit_precondition_violation_rejects() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "precondition",
                ObligationKind.PRECONDITION,
                "steady_state",
                "target",
                evidence_ids=("evidence:precondition",),
                status=ObligationStatus.VIOLATED,
                rationale_code="precondition_false",
            )
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.REJECTED


def test_permitted_non_loadbearing_loss_does_not_block() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "qoi",
                ObligationKind.QOI,
                "stability",
                "stability",
                evidence_ids=("evidence:qoi",),
            )
        ],
        permitted_losses=frozenset({"entity_semantics"}),
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.LICENSED


def test_forbidden_loss_without_preservation_proof_abstains() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "forbidden-loss",
                ObligationKind.FORBIDDEN_LOSS,
                "causal_direction",
                "",
                requirement=ObligationRequirement.FORBIDDEN,
                evidence_ids=("evidence:forbidden-loss",),
            )
        ],
        forbidden_losses=frozenset({"causal_direction"}),
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.CANNOT_CHECK


def test_direction_specific_violation_rejects() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "direction",
                ObligationKind.PRECONDITION,
                "source_to_target_direction",
                "target",
                evidence_ids=("evidence:direction",),
                status=ObligationStatus.VIOLATED,
                rationale_code="direction_invalid",
            )
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.REJECTED


def test_content_hash_is_deterministic() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "qoi",
                ObligationKind.QOI,
                "stability",
                "stability",
                evidence_ids=("evidence:qoi",),
            )
        ],
    )
    assert witness.content_hash == witness.content_hash
    assert len(witness.content_hash) == 64
