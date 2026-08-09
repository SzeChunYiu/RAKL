from dataclasses import FrozenInstanceError

import pytest

from rakl.generator_transport import (
    AbstractionLevel,
    EvidenceScope,
    GeneratorFamilyCandidate,
    GeneratorFamilyVerdict,
    GeneratorLift,
    GeneratorRelation,
    GeneratorRelationVerdict,
    GeneratorRelationWitness,
    GeneratorTransportTrial,
    GeneratorTransportVerdict,
    assess_generator_family,
    evaluate_generator_relation,
    project_through_generator,
    validate_generator_lift,
)


def _lift(
    *,
    instance_id: str = "apple",
    instance_domain: str = "pomology",
    generator_id: str = "ripening-generator",
    question_or_qoi: str = "what controls the state transition?",
    abstraction_level: AbstractionLevel = AbstractionLevel.L3,
    evidence_scope: EvidenceScope = EvidenceScope.GENERATOR,
    preserved: tuple[str, ...] = ("state_transition", "feedback", "causal_direction"),
    not_preserved: tuple[str, ...] = ("species_specific_substrate",),
    erased: tuple[str, ...] = ("species_name",),
    instance_specific: tuple[str, ...] = ("cultivar",),
    regime: tuple[str, ...] = ("climacteric",),
    evidence_ids: tuple[str, ...] = ("paper-1",),
    evidence_lineage_ids: tuple[str, ...] = ("lineage-A",),
    environment_id: str = "environment-A",
    intervention_or_query_ids: tuple[str, ...] = ("intervention-ethylene",),
    commutation_passed: bool | None = True,
    declared_before_outcomes: bool | None = True,
) -> GeneratorLift:
    return GeneratorLift(
        instance_id=instance_id,
        instance_domain=instance_domain,
        generator_id=generator_id,
        question_or_qoi=question_or_qoi,
        abstraction_level=abstraction_level,
        evidence_scope=evidence_scope,
        mapping_pairs=(("driver", "generator_driver"), ("response", "generator_response")),
        preserved=preserved,
        not_preserved=not_preserved,
        erased=erased,
        instance_specific=instance_specific,
        regime=regime,
        evidence_ids=evidence_ids,
        evidence_lineage_ids=evidence_lineage_ids,
        environment_id=environment_id,
        intervention_or_query_ids=intervention_or_query_ids,
        commutation_passed=commutation_passed,
        declared_before_outcomes=declared_before_outcomes,
    )


def _witness(
    *,
    relation: GeneratorRelation = GeneratorRelation.SHARES_GENERATOR_WITH,
    source_lift: GeneratorLift | None = None,
    target_lift: GeneratorLift | None = None,
    required_core_features: tuple[str, ...] = ("state_transition", "feedback"),
    level_transition_map_id: str | None = None,
    hidden_labels_exposed: bool | None = False,
    relation_declared_before_outcomes: bool | None = True,
) -> GeneratorRelationWitness:
    return GeneratorRelationWitness(
        relation=relation,
        source_lift=source_lift or _lift(instance_id="banana", instance_domain="banana-science"),
        target_lift=target_lift or _lift(),
        required_core_features=required_core_features,
        level_transition_map_id=level_transition_map_id,
        hidden_labels_exposed=hidden_labels_exposed,
        relation_declared_before_outcomes=relation_declared_before_outcomes,
    )


def _trial(**overrides) -> GeneratorTransportTrial:
    values = dict(
        trial_id="transport-1",
        relation_witness=_witness(),
        source_claim_id="banana-claim",
        generator_claim_id="generator-claim",
        target_hypothesis_id="apple-hypothesis",
        target_tested=False,
        target_passed=None,
    )
    values.update(overrides)
    return GeneratorTransportTrial(**values)


def test_valid_lift_is_contextual_and_immutable():
    lift = _lift()
    assert validate_generator_lift(lift).verdict.value == "VALID"
    with pytest.raises(FrozenInstanceError):
        lift.instance_id = "changed"  # type: ignore[misc]


def test_category_only_relation_is_discovery_hint_not_transfer():
    source = _lift(evidence_scope=EvidenceScope.CATEGORY_ONLY)
    target = _lift(instance_id="banana", evidence_scope=EvidenceScope.CATEGORY_ONLY)
    report = evaluate_generator_relation(
        _witness(
            relation=GeneratorRelation.SHARES_CATEGORY_WITH,
            source_lift=source,
            target_lift=target,
        )
    )
    assert report.verdict is GeneratorRelationVerdict.DISCOVERY_HINT_ONLY
    assert report.grants_target_authority is False


def test_shared_parent_is_retrieval_hint_only():
    source = _lift(evidence_scope=EvidenceScope.PARENT)
    target = _lift(instance_id="banana", evidence_scope=EvidenceScope.PARENT)
    report = evaluate_generator_relation(
        _witness(
            relation=GeneratorRelation.SHARES_PARENT_WITH,
            source_lift=source,
            target_lift=target,
        )
    )
    assert report.verdict is GeneratorRelationVerdict.RETRIEVAL_HINT_ONLY


def test_abstract_schema_is_analogy_proposal_only():
    source = _lift(evidence_scope=EvidenceScope.ABSTRACT_SCHEMA)
    target = _lift(instance_id="control-loop", evidence_scope=EvidenceScope.ABSTRACT_SCHEMA)
    report = evaluate_generator_relation(
        _witness(
            relation=GeneratorRelation.SHARES_ABSTRACT_SCHEMA_WITH,
            source_lift=source,
            target_lift=target,
        )
    )
    assert report.verdict is GeneratorRelationVerdict.ANALOGY_PROPOSAL_ONLY


def test_mechanism_family_can_create_transfer_hypothesis_but_not_authority():
    source = _lift(evidence_scope=EvidenceScope.MECHANISM_FAMILY)
    target = _lift(instance_id="banana", evidence_scope=EvidenceScope.MECHANISM_FAMILY)
    report = evaluate_generator_relation(
        _witness(
            relation=GeneratorRelation.SHARES_MECHANISM_FAMILY_WITH,
            source_lift=source,
            target_lift=target,
        )
    )
    assert report.verdict is GeneratorRelationVerdict.TRANSFER_HYPOTHESIS_ONLY
    assert report.grants_target_authority is False


def test_shared_generator_requires_commuting_intervention_or_query():
    source = _lift(commutation_passed=None)
    report = evaluate_generator_relation(_witness(source_lift=source))
    assert report.verdict is GeneratorRelationVerdict.CANNOT_CHECK
    assert "intervention_or_query_commutation_unknown" in report.reasons


def test_failed_intervention_commutation_rejects_generator_transfer():
    source = _lift(commutation_passed=False)
    report = evaluate_generator_relation(_witness(source_lift=source))
    assert report.verdict is GeneratorRelationVerdict.REJECT
    assert "intervention_or_query_commutation_failed" in report.reasons


def test_disjoint_regime_rejects_transport():
    target = _lift(instance_id="banana", regime=("non-climacteric",))
    report = evaluate_generator_relation(_witness(target_lift=target))
    assert report.verdict is GeneratorRelationVerdict.REJECT
    assert "no_overlapping_validity_regime" in report.reasons


def test_level_mismatch_without_transition_map_is_cannot_check():
    target = _lift(instance_id="banana", abstraction_level=AbstractionLevel.L4)
    report = evaluate_generator_relation(_witness(target_lift=target))
    assert report.verdict is GeneratorRelationVerdict.CANNOT_CHECK
    assert "abstraction_level_mismatch_without_transition_map" in report.reasons


def test_required_core_feature_contradiction_rejects_relation():
    target = _lift(
        instance_id="banana",
        preserved=("state_transition", "causal_direction"),
        not_preserved=("feedback",),
    )
    report = evaluate_generator_relation(_witness(target_lift=target))
    assert report.verdict is GeneratorRelationVerdict.REJECT
    assert any("required_core_feature_explicitly_not_preserved:feedback" == x for x in report.reasons)


def test_category_evidence_cannot_escalate_to_generator_claim():
    source = _lift(evidence_scope=EvidenceScope.CATEGORY_ONLY)
    target = _lift(instance_id="banana", evidence_scope=EvidenceScope.CATEGORY_ONLY)
    report = evaluate_generator_relation(
        _witness(
            relation=GeneratorRelation.SHARES_GENERATOR_WITH,
            source_lift=source,
            target_lift=target,
        )
    )
    assert report.verdict is GeneratorRelationVerdict.REJECT
    assert "source_evidence_scope_cannot_support_claimed_relation" in report.reasons


def test_hidden_label_exposure_invalidates_relation_trial():
    report = evaluate_generator_relation(_witness(hidden_labels_exposed=True))
    assert report.verdict is GeneratorRelationVerdict.TRIAL_INVALID


def test_posthoc_relation_expansion_invalidates_trial():
    report = evaluate_generator_relation(
        _witness(relation_declared_before_outcomes=False)
    )
    assert report.verdict is GeneratorRelationVerdict.TRIAL_INVALID


def test_same_lineage_support_is_not_independent_corroboration():
    lifts = (
        _lift(instance_id="apple", environment_id="env-A"),
        _lift(instance_id="banana", environment_id="env-B", evidence_ids=("paper-2",)),
        _lift(instance_id="pear", environment_id="env-C", evidence_ids=("paper-3",)),
    )
    report = assess_generator_family(
        GeneratorFamilyCandidate(
            candidate_id="candidate-1",
            generator_id="ripening-generator",
            question_or_qoi="what controls the state transition?",
            abstraction_level=AbstractionLevel.L3,
            required_core_features=("state_transition", "feedback"),
            lifts=lifts,
            declared_before_outcomes=True,
            hidden_labels_exposed=False,
        )
    )
    assert report.verdict is GeneratorFamilyVerdict.CORRELATED_SUPPORT_ONLY


def test_multi_lineage_multi_environment_support_is_proposal_only():
    lifts = (
        _lift(instance_id="apple", evidence_lineage_ids=("lineage-A",), environment_id="env-A"),
        _lift(
            instance_id="banana",
            evidence_ids=("paper-2",),
            evidence_lineage_ids=("lineage-B",),
            environment_id="env-B",
        ),
    )
    report = assess_generator_family(
        GeneratorFamilyCandidate(
            candidate_id="candidate-2",
            generator_id="ripening-generator",
            question_or_qoi="what controls the state transition?",
            abstraction_level=AbstractionLevel.L3,
            required_core_features=("state_transition", "feedback"),
            lifts=lifts,
            declared_before_outcomes=True,
            hidden_labels_exposed=False,
        )
    )
    assert report.verdict is GeneratorFamilyVerdict.CORROBORATED_GENERATOR_PROPOSAL_ONLY
    assert report.validates_generator_as_truth is False


def test_outlier_sibling_is_preserved_not_forced_into_family():
    lifts = (
        _lift(instance_id="apple", evidence_lineage_ids=("lineage-A",), environment_id="env-A"),
        _lift(
            instance_id="banana",
            evidence_ids=("paper-2",),
            evidence_lineage_ids=("lineage-B",),
            environment_id="env-B",
        ),
        _lift(
            instance_id="stone",
            instance_domain="materials",
            generator_id="ripening-generator",
            evidence_scope=EvidenceScope.ABSTRACT_SCHEMA,
            preserved=("state_transition",),
            not_preserved=("feedback",),
            evidence_ids=("paper-3",),
            evidence_lineage_ids=("lineage-C",),
            environment_id="env-C",
        ),
    )
    report = assess_generator_family(
        GeneratorFamilyCandidate(
            candidate_id="candidate-3",
            generator_id="ripening-generator",
            question_or_qoi="what controls the state transition?",
            abstraction_level=AbstractionLevel.L3,
            required_core_features=("state_transition", "feedback"),
            lifts=lifts,
            declared_before_outcomes=True,
            hidden_labels_exposed=False,
        )
    )
    assert report.verdict is GeneratorFamilyVerdict.CORROBORATED_WITH_OUTLIER_PRESERVED
    assert "stone" in report.outlier_instance_ids


def test_unknown_sibling_is_preserved_as_unknown():
    lifts = (
        _lift(instance_id="apple", evidence_lineage_ids=("lineage-A",), environment_id="env-A"),
        _lift(
            instance_id="banana",
            evidence_ids=("paper-2",),
            evidence_lineage_ids=("lineage-B",),
            environment_id="env-B",
        ),
        _lift(
            instance_id="pear",
            preserved=("state_transition",),
            not_preserved=("species_specific_substrate",),
            evidence_ids=("paper-3",),
            evidence_lineage_ids=("lineage-C",),
            environment_id="env-C",
        ),
    )
    report = assess_generator_family(
        GeneratorFamilyCandidate(
            candidate_id="candidate-4",
            generator_id="ripening-generator",
            question_or_qoi="what controls the state transition?",
            abstraction_level=AbstractionLevel.L3,
            required_core_features=("state_transition", "feedback"),
            lifts=lifts,
            declared_before_outcomes=True,
            hidden_labels_exposed=False,
        )
    )
    assert report.verdict is GeneratorFamilyVerdict.CORROBORATED_WITH_UNKNOWN_PRESERVED
    assert "pear" in report.unknown_instance_ids


def test_generator_projection_without_target_test_remains_hypothesis():
    report = project_through_generator(_trial())
    assert report.verdict is GeneratorTransportVerdict.TRANSFER_HYPOTHESIS_ONLY
    assert report.activates_canonical_knowledge is False


def test_target_refutation_preserves_generator_witness():
    report = project_through_generator(
        _trial(target_tested=True, target_passed=False)
    )
    assert (
        report.verdict
        is GeneratorTransportVerdict.TARGET_REFUTED_GENERATOR_WITNESS_PRESERVED
    )
    assert report.relation_report is not None
    assert (
        report.relation_report.verdict
        is GeneratorRelationVerdict.TRANSFER_HYPOTHESIS_ONLY
    )


def test_target_pass_still_requires_separate_promotion():
    report = project_through_generator(
        _trial(target_tested=True, target_passed=True)
    )
    assert (
        report.verdict
        is GeneratorTransportVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED
    )
    assert report.activates_canonical_knowledge is False
