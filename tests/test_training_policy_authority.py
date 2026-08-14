from rakl.training_policy_authority import (
    AdaptivePolicyAuthorization,
    TrainingPolicyMode,
    choose_active_training_policy,
)


def _auth(**overrides):
    values = dict(
        receipt_id="p4-phase2-confirmatory-v1",
        terminal="ADAPTIVE_RESIDUAL_SUPPORTED",
        evaluated_subject_hash="a" * 64,
        evidence_ids=("fresh-assurance", "paired-inference", "cost"),
        fresh_assurance=True,
        strongest_parent_residual=True,
        hard_harms_pass=True,
        full_overhead_accounted=True,
    )
    values.update(overrides)
    return AdaptivePolicyAuthorization(**values)


def test_static_structural_is_active_default_without_positive_adaptive_receipt():
    decision = choose_active_training_policy()
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL
    assert decision.grants_scientific_authority is False


def test_resource_blocked_never_makes_adaptive_active():
    assert choose_active_training_policy(_auth(terminal="RESOURCE_BLOCKED")).mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_null_harm_or_parent_win_never_makes_adaptive_active():
    for terminal in (
        "STATIC_EQUALS_ADAPTIVE",
        "PARENT_MATCHES_OR_BEATS",
        "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
    ):
        assert choose_active_training_policy(_auth(terminal=terminal)).mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_adaptive_requires_every_registered_promotion_gate():
    for field in ("fresh_assurance", "strongest_parent_residual", "hard_harms_pass", "full_overhead_accounted"):
        assert choose_active_training_policy(_auth(**{field: False})).mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_valid_external_adaptive_residual_receipt_can_switch_active_policy():
    decision = choose_active_training_policy(_auth())
    assert decision.mode is TrainingPolicyMode.ADAPTIVE_STRUCTURAL
    assert decision.authorization_receipt_id == "p4-phase2-confirmatory-v1"
    assert decision.grants_scientific_authority is False


def test_scheduler_cannot_self_authorize_by_omitting_evidence():
    assert choose_active_training_policy(_auth(evidence_ids=())).mode is TrainingPolicyMode.STATIC_STRUCTURAL
