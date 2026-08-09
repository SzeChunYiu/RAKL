from dataclasses import FrozenInstanceError

import pytest

from rakl.similarity import (
    AnalogyDiscoveryObservation,
    AnalogyDiscoveryVerdict,
    MappingAdmissibility,
    MotifVerdict,
    ProbeFamily,
    SimilarityRelation,
    SimilarityWitness,
    WitnessVerdict,
    corroborate_structural_motif,
    diagnose_analogy_discovery,
    validate_similarity_witness,
)


def _witness(
    *,
    source_id: str = "source-A",
    target_id: str = "target",
    source_domain: str = "domain-A",
    relation: SimilarityRelation = SimilarityRelation.RELATIONALLY_ANALOGOUS,
    preserved: tuple[str, ...] = ("feedback_loop", "role_order"),
    not_preserved: tuple[str, ...] = ("substrate",),
    declared_before_fit: bool | None = True,
    null_calibration_passed: bool | None = True,
    constraint_violations: tuple[str, ...] = (),
    constraints: tuple[str, ...] = ("typed_roles", "causal_direction"),
) -> SimilarityWitness:
    return SimilarityWitness(
        relation=relation,
        source_id=source_id,
        target_id=target_id,
        source_domain=source_domain,
        target_domain="target-domain",
        question_or_qoi="does the feedback structure transfer?",
        mapping_pairs=(("driver", "driver"), ("response", "response")),
        preserved=preserved,
        not_preserved=not_preserved,
        regime=("bounded-input",),
        evidence_ids=("evidence-1",),
        mapping_admissibility=MappingAdmissibility(
            family_id="typed-role-map-v1",
            declared_before_fit=declared_before_fit,
            constraints=constraints,
            constraint_violations=constraint_violations,
            null_calibration_passed=null_calibration_passed,
        ),
        probe_family=ProbeFamily(
            family_id="probe-family-v1",
            probe_ids=("direction-probe", "regime-probe"),
        ),
    )


def _observation(**overrides) -> AnalogyDiscoveryObservation:
    values = dict(
        target_id="target",
        designated_source_id="source-A",
        corpus_candidate_ids=("surface-neighbor", "source-A", "source-B"),
        retrieved_candidate_ids=("surface-neighbor", "source-A"),
        retrieval_route="domain_stripped_relational",
        witness=_witness(),
        target_transfer_tested=False,
        target_transfer_passed=None,
        hidden_label_exposed=False,
        query_frozen_before_labels=True,
    )
    values.update(overrides)
    return AnalogyDiscoveryObservation(**values)


def test_valid_witness_is_scoped_and_fail_closed():
    report = validate_similarity_witness(_witness())
    assert report.verdict is WitnessVerdict.VALID


def test_posthoc_mapping_family_is_rejected():
    report = validate_similarity_witness(_witness(declared_before_fit=False))
    assert report.verdict is WitnessVerdict.REJECT
    assert "posthoc_mapping_family_expansion" in report.reasons


def test_mapping_constraint_violation_is_rejected():
    report = validate_similarity_witness(
        _witness(constraint_violations=("unit_mismatch",))
    )
    assert report.verdict is WitnessVerdict.REJECT
    assert any(reason.endswith("unit_mismatch") for reason in report.reasons)


def test_mathematical_isomorphism_requires_type_or_unit_constraint():
    report = validate_similarity_witness(
        _witness(
            relation=SimilarityRelation.MATHEMATICALLY_ISOMORPHIC,
            constraints=("bijective",),
        )
    )
    assert report.verdict is WitnessVerdict.CANNOT_CHECK
    assert "type_or_unit_compatibility_constraint_missing" in report.reasons


def test_corpus_absence_is_not_mislabeled_as_retrieval_failure():
    report = diagnose_analogy_discovery(
        _observation(corpus_candidate_ids=("surface-neighbor",))
    )
    assert report.verdict is AnalogyDiscoveryVerdict.CORPUS_COVERAGE_FAILURE


def test_present_but_not_retrieved_is_retrieval_failure():
    report = diagnose_analogy_discovery(
        _observation(retrieved_candidate_ids=("surface-neighbor",))
    )
    assert report.verdict is AnalogyDiscoveryVerdict.RETRIEVAL_FAILURE


def test_retrieved_but_unmapped_is_recognition_failure():
    report = diagnose_analogy_discovery(_observation(witness=None))
    assert report.verdict is AnalogyDiscoveryVerdict.RECOGNITION_FAILURE


def test_valid_witness_without_target_test_remains_proposal_only():
    report = diagnose_analogy_discovery(_observation())
    assert report.verdict is AnalogyDiscoveryVerdict.WITNESSED_ANALOGY
    assert report.activates_authority is False


def test_target_refutation_preserves_structural_witness():
    report = diagnose_analogy_discovery(
        _observation(target_transfer_tested=True, target_transfer_passed=False)
    )
    assert report.verdict is AnalogyDiscoveryVerdict.TARGET_TRANSFER_REFUTED
    assert report.witness_report is not None
    assert report.witness_report.verdict is WitnessVerdict.VALID


def test_hidden_answer_exposure_invalidates_trial():
    report = diagnose_analogy_discovery(_observation(hidden_label_exposed=True))
    assert report.verdict is AnalogyDiscoveryVerdict.TRIAL_INVALID


def test_posthoc_query_edit_invalidates_trial():
    report = diagnose_analogy_discovery(
        _observation(query_frozen_before_labels=False)
    )
    assert report.verdict is AnalogyDiscoveryVerdict.TRIAL_INVALID


def test_cross_domain_witnesses_can_corroborate_only_a_proposal_motif():
    first = _witness(source_id="source-A", source_domain="biology")
    second = _witness(
        source_id="source-B",
        source_domain="control-theory",
        preserved=("feedback_loop", "stability_boundary"),
        not_preserved=("substrate", "state_dimension"),
    )
    report = corroborate_structural_motif((first, second))
    assert report.verdict is MotifVerdict.CORROBORATED_PROPOSAL_ONLY
    assert report.common_preserved == ("feedback_loop",)
    assert report.target_validated is False


def test_same_domain_repetition_is_not_cross_domain_confirmation():
    first = _witness(source_id="source-A", source_domain="biology")
    second = _witness(source_id="source-B", source_domain="biology")
    report = corroborate_structural_motif((first, second))
    assert report.verdict is MotifVerdict.CANNOT_CHECK


def test_witness_contract_is_immutable():
    witness = _witness()
    with pytest.raises(FrozenInstanceError):
        witness.source_id = "changed"  # type: ignore[misc]
