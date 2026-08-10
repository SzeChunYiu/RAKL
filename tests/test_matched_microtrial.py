from __future__ import annotations

from dataclasses import replace

from rakl.matched_microtrial import (
    EvidenceCorpusFingerprint,
    MatchedModelConfig,
    MatchedTrialArm,
    PendulumStructuredAnswer,
    TrialCondition,
    TrialResourceCeiling,
    TrialResourceUsage,
    canonical_protocol_hash,
    score_pendulum_answer,
    validate_matched_arms,
    validate_pendulum_evaluator_sources,
    validate_resource_usage,
)
from rakl.mini_research_demo import _sources


def _model() -> MatchedModelConfig:
    return MatchedModelConfig(
        model_id="provider/model",
        model_revision="exact-revision",
        temperature=0.0,
        max_output_tokens=512,
        seed=17,
        system_prompt="Answer the registered scientific question using only supplied evidence.",
    )


def _ceiling() -> TrialResourceCeiling:
    return TrialResourceCeiling(
        max_model_input_tokens=4096,
        max_model_output_tokens=512,
        max_preprocessing_model_tokens=4096,
        max_preprocessing_tool_calls=32,
        max_external_retrieval_calls=0,
        max_wall_time_ms=60_000,
    )


def _evidence() -> EvidenceCorpusFingerprint:
    return EvidenceCorpusFingerprint.from_payloads(
        {
            source.source_id: source.text.encode("utf-8")
            for source in _sources()
        }
    )


def _arms() -> tuple[MatchedTrialArm, MatchedTrialArm]:
    common = dict(
        model=_model(),
        evidence=_evidence(),
        resource_ceiling=_ceiling(),
        tool_policy_id="NO_EXTERNAL_TOOLS_AFTER_PROMPT_BUILD_V1",
        output_schema_id="PENDULUM_STRUCTURED_ANSWER_V2",
        question_set_hash=canonical_protocol_hash(["Q1", "Q2", "Q3", "Q4"]),
        evaluator_protocol_hash=canonical_protocol_hash({"evaluator": "sealed-known-answer-v2"}),
    )
    return (
        MatchedTrialArm(condition=TrialCondition.DIRECT_CORPUS, **common),
        MatchedTrialArm(condition=TrialCondition.RAKL_CONTEXT, **common),
    )


def test_matched_arms_require_same_model_corpus_resources_tools_questions_and_evaluator():
    direct, rakl = _arms()
    result = validate_matched_arms(direct, rakl)
    assert result.matched
    assert result.problems == ()


def test_model_corpus_or_resource_drift_is_detected_before_trial_execution():
    direct, rakl = _arms()
    drifted_model = replace(rakl.model, temperature=0.2)
    drifted_evidence = EvidenceCorpusFingerprint.from_payloads({"S1": b"different"})
    drifted_ceiling = replace(rakl.resource_ceiling, max_preprocessing_tool_calls=64)

    model_result = validate_matched_arms(direct, replace(rakl, model=drifted_model))
    corpus_result = validate_matched_arms(direct, replace(rakl, evidence=drifted_evidence))
    resource_result = validate_matched_arms(direct, replace(rakl, resource_ceiling=drifted_ceiling))
    assert "model_configuration_mismatch" in model_result.problems
    assert "evidence_corpus_mismatch" in corpus_result.problems
    assert "resource_ceiling_mismatch" in resource_result.problems


def test_preprocessing_usage_may_differ_but_each_arm_must_stay_within_same_ceiling():
    ceiling = _ceiling()
    direct_usage = TrialResourceUsage(1500, 200, 0, 0, 0, 700)
    rakl_usage = TrialResourceUsage(700, 220, 1800, 12, 0, 3200)
    assert validate_resource_usage(direct_usage, ceiling).within_ceiling
    assert validate_resource_usage(rakl_usage, ceiling).within_ceiling


def test_resource_ceiling_violation_invalidates_that_execution_receipt():
    usage = TrialResourceUsage(700, 220, 5000, 12, 0, 3200)
    report = validate_resource_usage(usage, _ceiling())
    assert not report.within_ceiling
    assert any("preprocessing_model_tokens" in problem for problem in report.problems)


def test_evidence_fingerprint_is_order_invariant_but_byte_sensitive():
    left = EvidenceCorpusFingerprint.from_payloads((("S2", b"b"), ("S1", b"a")))
    right = EvidenceCorpusFingerprint.from_payloads((("S1", b"a"), ("S2", b"b")))
    changed = EvidenceCorpusFingerprint.from_payloads((("S1", b"a"), ("S2", b"B")))
    assert left == right
    assert left != changed


def test_sealed_pendulum_evaluator_is_defined_only_on_frozen_corpus_source_ids():
    report = validate_pendulum_evaluator_sources(_evidence())
    assert report.valid
    assert report.problems == ()


def test_evaluator_source_validation_fails_if_required_frozen_source_is_missing():
    corpus = EvidenceCorpusFingerprint.from_payloads(
        {
            source.source_id: source.text.encode("utf-8")
            for source in _sources()
            if source.source_id != "S6"
        }
    )
    report = validate_pendulum_evaluator_sources(corpus)
    assert not report.valid
    assert "evaluator_required_refuted_source_missing:S6" in report.problems


def test_frozen_pendulum_corpus_contains_every_registered_conceptual_distinction():
    texts = {source.source_id: source.text.lower() for source in _sources()}
    assert "small angle" in texts["S1"]
    assert "finite-amplitude correction" in texts["S3"]
    assert "small-angle approximation" in texts["S4"]
    assert "moon" in texts["S5"] and "lunar" in texts["S5"]
    assert "increasing the bob mass increases" in texts["S6"]
    assert "does not materially change" in texts["S7"]
    assert "independent derivation" in texts["S8"]


def test_sealed_pendulum_score_rewards_context_alignment_grounding_and_refutation():
    answer = PendulumStructuredAnswer(
        small_angle_is_asymptotic=True,
        finite_amplitude_increases_period=True,
        context_distinct_claims_not_direct_contradictions=True,
        ideal_period_is_mass_invariant=True,
        context_alignment_required_before_contradiction=True,
        supporting_source_ids=("S1", "S2", "S3", "S4", "S5", "S7", "S8"),
        rejected_as_misaligned_source_ids=("S4", "S5"),
        refuted_source_ids=("S6",),
    )
    score = score_pendulum_answer(answer)
    assert score.conceptual_correct == 5
    assert score.conceptual_total == 5
    assert score.required_support_recall == 1.0
    assert score.support_precision == 1.0
    assert score.misalignment_recall == 1.0
    assert score.refutation_recall == 1.0
    assert score.refutation_precision == 1.0
    assert score.unsupported_source_count == 0
    assert score.exact_conceptual_pass


def test_same_source_may_support_one_claim_and_be_misaligned_for_another_comparison():
    answer = PendulumStructuredAnswer(
        small_angle_is_asymptotic=True,
        finite_amplitude_increases_period=True,
        context_distinct_claims_not_direct_contradictions=True,
        ideal_period_is_mass_invariant=True,
        context_alignment_required_before_contradiction=True,
        supporting_source_ids=("S4", "S5"),
        rejected_as_misaligned_source_ids=("S4", "S5"),
        refuted_source_ids=("S6",),
    )
    score = score_pendulum_answer(answer)
    assert score.support_precision == 1.0
    assert score.misalignment_recall == 1.0
    assert score.refutation_recall == 1.0
    assert score.required_support_recall < 1.0


def test_sealed_score_does_not_turn_unknown_or_false_support_ids_into_credit():
    answer = PendulumStructuredAnswer(
        small_angle_is_asymptotic=False,
        finite_amplitude_increases_period=False,
        context_distinct_claims_not_direct_contradictions=False,
        ideal_period_is_mass_invariant=False,
        context_alignment_required_before_contradiction=False,
        supporting_source_ids=("S6", "S999"),
        rejected_as_misaligned_source_ids=(),
        refuted_source_ids=("S999",),
    )
    score = score_pendulum_answer(answer)
    assert score.conceptual_correct == 0
    assert score.required_support_recall == 0.0
    assert score.support_precision == 0.0
    assert score.misalignment_recall == 0.0
    assert score.refutation_recall == 0.0
    assert score.refutation_precision == 0.0
    assert score.unsupported_source_count == 2
    assert not score.exact_conceptual_pass
