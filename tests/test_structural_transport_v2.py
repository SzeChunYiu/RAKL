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


def _covering_obligations() -> list[TransferObligation]:
    """Obligations that cover every load-bearing part of `_object`'s source content."""
    return [
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
            "relation",
            ObligationKind.RELATION,
            "a|competes_with|b|1",
            "a|competes_with|b|1",
            evidence_ids=("evidence:relation",),
        ),
    ]


def test_valid_distant_transfer_can_license_when_obligations_hold() -> None:
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        _covering_obligations()
        + [
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
        _covering_obligations(),
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


def _zero_obligation_witness(
    source: StructuralObject, target: StructuralObject
) -> StructuralWitnessV2:
    return StructuralWitnessV2(
        witness_id="w",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        source_context_id=source.context_id,
        target_context_id=target.context_id,
        qoi="stability",
        role_mapping=(),
        obligations=(),
    )


def test_zero_obligation_witness_cannot_license_identical_objects() -> None:
    """An empty obligation list asks nothing, so nothing can fail: it must not license."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    assessment = assess_transfer_v2(source, target, _zero_obligation_witness(source, target))
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "uncovered_qoi" in assessment.reasons


def test_zero_obligation_witness_cannot_license_unrelated_target() -> None:
    source = _object("source", "source-context")
    target = StructuralObject(
        structure_id="target",
        domain="test-domain",
        qoi="stability",
        context_id="target-context",
        roles=(StructuralRole("z", "other"),),
        relations=(),
        invariants=frozenset(),
        boundaries=(),
        evidence_ids=("evidence:target",),
    )
    assessment = assess_transfer_v2(source, target, _zero_obligation_witness(source, target))
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "uncovered_source_relation:a|competes_with|b|1" in assessment.reasons
    assert "uncovered_source_invariant:arrival_gt_service_implies_growth" in assessment.reasons


def test_uncovered_source_relation_blocks_license() -> None:
    """Thinning one obligation out of an otherwise complete witness must abstain."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    obligations = [
        obligation
        for obligation in _covering_obligations()
        if obligation.obligation_id != "relation"
    ]
    witness = _witness(source, target, obligations)
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "uncovered_source_relation:a|competes_with|b|1" in assessment.reasons


def test_optional_obligations_cannot_discharge_coverage() -> None:
    """An OPTIONAL obligation can never block, so it must not count as coverage."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                obligation.obligation_id,
                obligation.kind,
                obligation.source_ref,
                obligation.target_ref,
                requirement=ObligationRequirement.OPTIONAL,
                evidence_ids=obligation.evidence_ids,
            )
            for obligation in _covering_obligations()
        ],
    )
    assert assess_transfer_v2(source, target, witness).decision is TransferDecision.CANNOT_CHECK


def test_witness_cannot_self_certify_a_structurally_decidable_obligation() -> None:
    """A SATISFIED claim about a checkable fact is derived, not taken on the witness's word."""
    source = _object("source", "source-context")
    target = _object("target", "target-context", matching_invariant=False)
    witness = _witness(
        source,
        target,
        [
            obligation
            if obligation.obligation_id != "invariant"
            else TransferObligation(
                "invariant",
                ObligationKind.INVARIANT,
                "arrival_gt_service_implies_growth",
                "arrival_gt_service_implies_growth",
                evidence_ids=("evidence:invariant",),
                status=ObligationStatus.SATISFIED,
                rationale_code="witness_says_so",
            )
            for obligation in _covering_obligations()
        ],
    )
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is TransferDecision.REJECTED
    assert "invariant_missing" in assessment.reasons


def test_relation_obligation_must_check_the_role_mapping_image() -> None:
    """The witness may not redirect a source relation onto some other target relation."""
    source = _object("source", "source-context")
    target = StructuralObject(
        structure_id="target",
        domain="test-domain",
        qoi="stability",
        context_id="target-context",
        roles=(StructuralRole("a", "input"), StructuralRole("b", "capacity")),
        # The image of the source relation is absent; only its reverse is present.
        relations=(StructuralRelation("b", "competes_with", "a"),),
        invariants=frozenset({"arrival_gt_service_implies_growth"}),
        boundaries=(BoundaryCondition("flow_regime", "continual"),),
        evidence_ids=("evidence:target",),
    )
    witness = _witness(
        source,
        target,
        [
            obligation
            if obligation.obligation_id != "relation"
            else TransferObligation(
                "relation",
                ObligationKind.RELATION,
                "a|competes_with|b|1",
                "b|competes_with|a|1",
                evidence_ids=("evidence:relation",),
            )
            for obligation in _covering_obligations()
        ],
    )
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "relation_target_ref_not_role_mapping_image" in assessment.reasons


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


def _disjoint_target(structure_id: str, context_id: str) -> StructuralObject:
    """A structure sharing no roles, relations, invariants, or QoI with _object()."""
    return StructuralObject(
        structure_id=structure_id,
        domain="unrelated-domain",
        qoi="throughput",
        context_id=context_id,
        roles=(StructuralRole("x", "field"), StructuralRole("y", "operator")),
        relations=(StructuralRelation("x", "commutes_with", "y"),),
        invariants=frozenset({"totally_unrelated_invariant"}),
        boundaries=(BoundaryCondition("regime", "adiabatic"),),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def test_empty_obligation_set_fails_closed_on_disjoint_structures() -> None:
    """The 2026-08-14 fail-open defect: wholly disjoint structures with an empty
    obligation set were LICENSED with zero reasons. They must not be."""
    source = _object("source", "source-context")
    target = _disjoint_target("target", "target-context")
    witness = StructuralWitnessV2(
        witness_id="w",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        source_context_id=source.context_id,
        target_context_id=target.context_id,
        qoi="stability",
        role_mapping=(),
        obligations=(),
    )
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is not TransferDecision.LICENSED
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "empty_load_bearing_obligation_set" in assessment.reasons


def test_optional_only_obligations_fail_closed() -> None:
    """OPTIONAL-only obligations leave the load-bearing set empty: still not licensable."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(
        source,
        target,
        [
            TransferObligation(
                "qoi-optional",
                ObligationKind.QOI,
                "stability",
                "stability",
                requirement=ObligationRequirement.OPTIONAL,
                evidence_ids=("evidence:qoi",),
            )
        ],
    )
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is TransferDecision.CANNOT_CHECK
    assert "empty_load_bearing_obligation_set" in assessment.reasons


def test_licensed_always_carries_a_satisfied_load_bearing_obligation() -> None:
    """The LICENSED-with-zero-reasons path is dead: any LICENSED assessment must
    trace at least one satisfied load-bearing obligation. Witness upgraded to the
    covering set under the source-derived coverage regime (#633)."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    licensed_witness = _witness(source, target, _covering_obligations())
    empty_witness = _witness(source, target, [])
    for witness in (licensed_witness, empty_witness):
        assessment = assess_transfer_v2(source, target, witness)
        load_bearing_ids = {
            obligation.obligation_id
            for obligation in witness.obligations
            if obligation.requirement
            in {ObligationRequirement.REQUIRED, ObligationRequirement.FORBIDDEN}
        }
        satisfied_load_bearing = [
            trace
            for trace in assessment.traces
            if trace.obligation_id in load_bearing_ids
            and trace.status is ObligationStatus.SATISFIED
        ]
        if assessment.decision is TransferDecision.LICENSED:
            assert len(satisfied_load_bearing) >= 1
    assert assess_transfer_v2(source, target, licensed_witness).decision is TransferDecision.LICENSED
    assert assess_transfer_v2(source, target, empty_witness).decision is TransferDecision.CANNOT_CHECK


def test_no_alarm_legitimate_licensing_unchanged() -> None:
    """No-alarm control: a fully covering satisfied case still returns LICENSED
    with satisfied traces and no reasons, exactly as before both repairs.
    Witness upgraded to the covering set under #633."""
    source, target = _object("source", "source-context"), _object("target", "target-context")
    witness = _witness(source, target, _covering_obligations())
    assessment = assess_transfer_v2(source, target, witness)
    assert assessment.decision is TransferDecision.LICENSED
    assert assessment.reasons == ()
    assert all(trace.status is ObligationStatus.SATISFIED for trace in assessment.traces)
    assert len(assessment.traces) == len(_covering_obligations())
