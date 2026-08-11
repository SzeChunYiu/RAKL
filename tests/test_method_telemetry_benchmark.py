"""Frozen tests for the proposal-only method-telemetry matched benchmark (#125)."""

from __future__ import annotations

from rakl.method_telemetry_benchmark import (
    BenchmarkArm,
    BenchmarkVerdict,
    GoldReconstructionLabels,
    ProseArmObservation,
    ReconstructionAttempt,
    TrialVerdict,
    TypedArmObservation,
    audit_prose_arm,
    audit_typed_arm,
    compare_matched_arms,
)


def _gold(**overrides: object) -> GoldReconstructionLabels:
    values: dict[str, object] = {
        "episode_id": "episode::atom-A7::0003",
        "routing_influence_ids": ("tool::prior-bridge", "failure::cong-audit"),
        "rejected_candidate_ids": ("cand::lambda-rule-table",),
        "failure_class": "REPRESENTATION",
        "gluing_status": "LOCAL_ONLY",
        "reopened_axis_ids": ("axis::representation-churn",),
        "next_action_id": "action::refine-projection::0004",
        "labels_frozen_before_arm_access": True,
    }
    values.update(overrides)
    return GoldReconstructionLabels(**values)  # type: ignore[arg-type]


def test_typed_arm_reconstructs_all_fields_when_honest() -> None:
    gold = _gold()
    obs = TypedArmObservation(
        trial_id="trial-typed-1",
        episode_id=gold.episode_id,
        telemetry_artifact_hash="a" * 64,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
        prose_exposed=False,
    )
    attempt = ReconstructionAttempt(
        trial_id="trial-typed-1",
        arm=BenchmarkArm.TYPED_METHOD_TELEMETRY,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
    )
    report = audit_typed_arm(gold, obs, attempt)
    assert report.verdict is TrialVerdict.VALID
    assert report.reconstruction_rate == 1.0
    assert report.grants_method_authority is False


def test_prose_arm_partial_reconstruction_is_scored() -> None:
    gold = _gold()
    obs = ProseArmObservation(
        trial_id="trial-prose-1",
        episode_id=gold.episode_id,
        action_trace_prose="tried representation change after prior failure",
        research_trace_prose="next: refine projection",
        typed_fields_exposed=False,
    )
    attempt = ReconstructionAttempt(
        trial_id="trial-prose-1",
        arm=BenchmarkArm.PROSE_ACTION_TRACE,
        routing_influence_ids=(),
        rejected_candidate_ids=(),
        failure_class="REPRESENTATION",
        gluing_status="GLUING_NOT_ASSESSED",
        reopened_axis_ids=(),
        next_action_id="action::refine-projection::0004",
    )
    report = audit_prose_arm(gold, obs, attempt)
    assert report.verdict is TrialVerdict.VALID
    assert report.reconstruction_rate is not None
    assert 0.0 < report.reconstruction_rate < 1.0


def test_blinding_failure_invalidates_trial() -> None:
    gold = _gold()
    obs = TypedArmObservation(
        trial_id="trial-typed-leak",
        episode_id=gold.episode_id,
        telemetry_artifact_hash="a" * 64,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
        prose_exposed=True,
    )
    attempt = ReconstructionAttempt(
        trial_id="trial-typed-leak",
        arm=BenchmarkArm.TYPED_METHOD_TELEMETRY,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
    )
    report = audit_typed_arm(gold, obs, attempt)
    assert report.verdict is TrialVerdict.TRIAL_INVALID
    assert "typed_arm_prose_not_blinded" in report.reasons


def test_matched_comparison_reports_typed_lift_without_promotion() -> None:
    gold = _gold()
    prose_obs = ProseArmObservation(
        trial_id="trial-prose-2",
        episode_id=gold.episode_id,
        action_trace_prose="unclear narrative",
        research_trace_prose="",
        typed_fields_exposed=False,
    )
    prose_attempt = ReconstructionAttempt(
        trial_id="trial-prose-2",
        arm=BenchmarkArm.PROSE_ACTION_TRACE,
        routing_influence_ids=(),
        rejected_candidate_ids=(),
        failure_class="UNCLASSIFIED_FAILURE",
        gluing_status="GLUING_NOT_ASSESSED",
        reopened_axis_ids=(),
        next_action_id="",
    )
    typed_obs = TypedArmObservation(
        trial_id="trial-typed-2",
        episode_id=gold.episode_id,
        telemetry_artifact_hash="b" * 64,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
        prose_exposed=False,
    )
    typed_attempt = ReconstructionAttempt(
        trial_id="trial-typed-2",
        arm=BenchmarkArm.TYPED_METHOD_TELEMETRY,
        routing_influence_ids=gold.routing_influence_ids,
        rejected_candidate_ids=gold.rejected_candidate_ids,
        failure_class=gold.failure_class,
        gluing_status=gold.gluing_status,
        reopened_axis_ids=gold.reopened_axis_ids,
        next_action_id=gold.next_action_id,
    )
    prose_report = audit_prose_arm(gold, prose_obs, prose_attempt)
    typed_report = audit_typed_arm(gold, typed_obs, typed_attempt)
    matched = compare_matched_arms(prose_report, typed_report)
    assert matched.verdict is BenchmarkVerdict.VALID
    assert matched.typed_lift is not None and matched.typed_lift > 0.0
    assert matched.grants_method_authority is False
    assert matched.promotes_framework_change is False
