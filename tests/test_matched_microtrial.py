from __future__ import annotations

from dataclasses import replace

from rakl.matched_microtrial import (
    EvidenceCorpusFingerprint,
    MatchedModelConfig,
    MatchedTrialArm,
    PendulumStructuredAnswer,
    TrialCondition,
    canonical_protocol_hash,
    score_pendulum_answer,
    validate_matched_arms,
)


def _model() -> MatchedModelConfig:
    return MatchedModelConfig(
        model_id="provider/model",
        model_revision="exact-revision",
        temperature=0.0,
        max_output_tokens=512,
        seed=17,
        system_prompt="Answer the registered scientific question using only supplied evidence.",
    )


def _evidence() -> EvidenceCorpusFingerprint:
    return EvidenceCorpusFingerprint.from_payloads(
        {
            "S1": b"small-angle pendulum law",
            "S2": b"finite-amplitude correction",
        }
    )


def _arms() -> tuple[MatchedTrialArm, MatchedTrialArm]:
    common = dict(
        model=_model(),
        evidence=_evidence(),
        tool_policy_id="NO_EXTERNAL_TOOLS_AFTER_PROMPT_BUILD_V1",
        output_schema_id="PENDULUM_STRUCTURED_ANSWER_V1",
        question_set_hash=canonical_protocol_hash(["Q1", "Q2"]),
        evaluator_protocol_hash=canonical_protocol_hash({"evaluator": "sealed-known-answer-v1"}),
    )
    return (
        MatchedTrialArm(condition=TrialCondition.DIRECT_CORPUS, **common),
        MatchedTrialArm(condition=TrialCondition.RAKL_CONTEXT, **common),
    )


def test_matched_arms_require_same_model_corpus_tools_questions_and_evaluator():
    direct, rakl = _arms()
    result = validate_matched_arms(direct, rakl)
    assert result.matched
    assert result.problems == ()


def test_model_or_corpus_drift_is_detected_before_trial_execution():
    direct, rakl = _arms()
    drifted_model = replace(rakl.model, temperature=0.2)
    drifted_evidence = EvidenceCorpusFingerprint.from_payloads({"S1": b"different"})

    model_result = validate_matched_arms(direct, replace(rakl, model=drifted_model))
    corpus_result = validate_matched_arms(direct, replace(rakl, evidence=drifted_evidence))
    assert "model_configuration_mismatch" in model_result.problems
    assert "evidence_corpus_mismatch" in corpus_result.problems


def test_evidence_fingerprint_is_order_invariant_but_byte_sensitive():
    left = EvidenceCorpusFingerprint.from_payloads((("S2", b"b"), ("S1", b"a")))
    right = EvidenceCorpusFingerprint.from_payloads((("S1", b"a"), ("S2", b"b")))
    changed = EvidenceCorpusFingerprint.from_payloads((("S1", b"a"), ("S2", b"B")))
    assert left == right
    assert left != changed


def test_sealed_pendulum_score_rewards_context_alignment_and_source_grounding():
    answer = PendulumStructuredAnswer(
        small_angle_is_asymptotic=True,
        finite_amplitude_increases_period=True,
        period_differs_from_time_to_angle=True,
        context_alignment_required_before_contradiction=True,
        supporting_source_ids=("S2", "S3", "S7"),
        rejected_as_misaligned_source_ids=("S4", "S5"),
    )
    score = score_pendulum_answer(answer)
    assert score.conceptual_correct == 4
    assert score.conceptual_total == 4
    assert score.required_support_recall == 1.0
    assert score.support_precision == 1.0
    assert score.misalignment_recall == 1.0
    assert score.unsupported_source_count == 0
    assert score.exact_conceptual_pass


def test_sealed_score_does_not_turn_unknown_source_ids_into_credit():
    answer = PendulumStructuredAnswer(
        small_angle_is_asymptotic=False,
        finite_amplitude_increases_period=False,
        period_differs_from_time_to_angle=False,
        context_alignment_required_before_contradiction=False,
        supporting_source_ids=("S999",),
        rejected_as_misaligned_source_ids=(),
    )
    score = score_pendulum_answer(answer)
    assert score.conceptual_correct == 0
    assert score.required_support_recall == 0.0
    assert score.support_precision == 0.0
    assert score.unsupported_source_count == 1
    assert not score.exact_conceptual_pass
