from rakl.structural_benchmark import SimilarityQuadrant, make_quadrant_cases
from rakl.structural_transfer import assess_transfer, structural_overlap_score
from rakl.structural_types import BoundaryCondition, StructuralWitness, TransferDecision


def cases_by_quadrant():
    return {case.quadrant: case for case in make_quadrant_cases()}


def test_q2_cross_domain_structure_is_licensed_despite_low_semantic_label() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT]
    assessment = assess_transfer(case.source, case.target, case.witness)
    assert case.semantic_similarity_label == "low"
    assert assessment.decision is TransferDecision.LICENSED
    assert assessment.structurally_complete


def test_q3_semantic_decoy_is_rejected() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT]
    assessment = assess_transfer(case.source, case.target, case.witness)
    assert case.semantic_similarity_label == "high"
    assert assessment.decision is TransferDecision.REJECTED
    assert not assessment.structurally_complete
    assert any("relation_not_preserved" in reason for reason in assessment.reasons)
    assert any("boundary_mismatch" in reason for reason in assessment.reasons)


def test_q4_unrelated_structure_is_rejected() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q4_LOW_SEM_LOW_STRUCT]
    assessment = assess_transfer(case.source, case.target, case.witness)
    assert assessment.decision is TransferDecision.REJECTED


def test_structural_overlap_score_ignores_domain_nouns() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT]
    assert structural_overlap_score(case.source, case.target) == 1.0


def test_boundary_violation_rejects_otherwise_matching_witness() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT]
    bad = StructuralWitness(
        witness_id="boundary-bad",
        source_structure_id=case.source.structure_id,
        target_structure_id=case.target.structure_id,
        role_mapping=case.witness.role_mapping,
        preserved_invariants=case.witness.preserved_invariants,
        non_preserved_properties=case.witness.non_preserved_properties,
        required_target_boundaries=(BoundaryCondition("flow_regime", "finite_batch"),),
        evidence_ids=("evidence:boundary-bad",),
    )
    assessment = assess_transfer(case.source, case.target, bad)
    assert assessment.decision is TransferDecision.REJECTED
    assert "boundary_mismatch:flow_regime" in assessment.reasons


def test_witness_explicitly_retains_non_preserved_properties() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT]
    assert "entity_semantics" in case.witness.non_preserved_properties
    assert "domain_specific_priority_rules" in case.witness.non_preserved_properties


def test_endpoint_identity_mismatch_fails_as_cannot_check_not_transfer() -> None:
    case = cases_by_quadrant()[SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT]
    wrong = StructuralWitness(
        witness_id="wrong-endpoint",
        source_structure_id="not-the-source",
        target_structure_id=case.target.structure_id,
        role_mapping=case.witness.role_mapping,
        preserved_invariants=case.witness.preserved_invariants,
        non_preserved_properties=frozenset(),
        required_target_boundaries=case.witness.required_target_boundaries,
        evidence_ids=("evidence:wrong",),
    )
    assert assess_transfer(case.source, case.target, wrong).decision is TransferDecision.CANNOT_CHECK
