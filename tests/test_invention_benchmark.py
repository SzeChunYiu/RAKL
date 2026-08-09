from rakl.invention_benchmark import (
    InventionAttempt,
    InventionBenchmarkCase,
    InventionBenchmarkVerdict,
    InventionWorldKind,
    evaluate_invention_attempt,
)


def _case(kind=InventionWorldKind.RECONSTRUCTION):
    return InventionBenchmarkCase(
        benchmark_id="b1",
        world_kind=kind,
        frozen_evidence_ids=("e1", "e2"),
        target_signature=("latent_state", "feedback", "regime_switch"),
        minimum_signature_recall=2 / 3,
        minimum_signature_precision=0.5,
        hidden_target_id="hidden-law",
        target_hidden_from_proposer=True,
        thresholds_frozen_before_attempt=True,
        evaluator_separate=True,
        required_novel_combinations=("latent+feedback",) if kind is InventionWorldKind.NOVEL_COMPOSITION else (),
    )


def test_hidden_target_exposure_invalidates_trial():
    attempt = InventionAttempt(
        benchmark_id="b1",
        candidate_id="c",
        recovered_signature=("latent_state",),
        candidate_frozen_before_target_exposure=True,
        hidden_target_exposed=True,
        target_validation_passed=True,
        formal_verification_passed=True,
    )
    report = evaluate_invention_attempt(_case(), attempt)
    assert report.verdict is InventionBenchmarkVerdict.TRIAL_INVALID


def test_hidden_world_recovery_can_pass():
    attempt = InventionAttempt(
        benchmark_id="b1",
        candidate_id="c",
        recovered_signature=("latent_state", "feedback", "regime_switch"),
        candidate_frozen_before_target_exposure=True,
        hidden_target_exposed=False,
        target_validation_passed=True,
        formal_verification_passed=True,
    )
    report = evaluate_invention_attempt(_case(), attempt)
    assert report.verdict is InventionBenchmarkVerdict.INVENTION_RECOVERED


def test_novel_composition_requires_generated_combination():
    case = _case(InventionWorldKind.NOVEL_COMPOSITION)
    attempt = InventionAttempt(
        benchmark_id="b1",
        candidate_id="c",
        recovered_signature=("latent_state", "feedback", "regime_switch"),
        candidate_frozen_before_target_exposure=True,
        hidden_target_exposed=False,
        target_validation_passed=True,
        formal_verification_passed=True,
        generated_combination_ids=(),
    )
    report = evaluate_invention_attempt(case, attempt)
    assert report.verdict is InventionBenchmarkVerdict.PARTIAL_RECOVERY
