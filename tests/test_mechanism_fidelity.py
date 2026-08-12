from rakl.mechanism_fidelity import (
    MechanismAgentOutput,
    MechanismFidelityVerdict,
    MechanismPrediction,
    MechanismWorld,
    RegimeObservation,
    evaluate_mechanism_fidelity,
)


def _equivalence_world(**overrides):
    values = dict(
        world_id="equivalence",
        candidate_mechanism_ids=("m1", "m2"),
        predictions=(
            MechanismPrediction("m1", "r0", "A"),
            MechanismPrediction("m2", "r0", "A"),
            MechanismPrediction("m1", "r1", "B"),
            MechanismPrediction("m2", "r1", "C"),
        ),
        observations=(RegimeObservation("r0", "A"),),
        target_regime_id="r0",
        target_outcome="A",
        available_discriminator_regimes=("r1",),
        registered_valid_scope_regimes=("r0",),
        known_answer_validated=True,
        frozen_before_output=True,
    )
    values.update(overrides)
    return MechanismWorld(**values)


def _correct_equivalence_output(**overrides):
    values = dict(
        predicted_target_outcome="A",
        survivor_mechanism_ids=("m1", "m2"),
        mechanism_supported_ids=("m1", "m2"),
        identified_mechanism_id=None,
        proposed_discriminator_regime="r1",
        claimed_scope_regimes=("r0",),
    )
    values.update(overrides)
    return MechanismAgentOutput(**values)


def _shift_world():
    return MechanismWorld(
        world_id="shift",
        candidate_mechanism_ids=("m1", "m2"),
        predictions=(
            MechanismPrediction("m1", "r0", "A"),
            MechanismPrediction("m2", "r0", "A"),
            MechanismPrediction("m1", "r1", "B"),
            MechanismPrediction("m2", "r1", "C"),
        ),
        observations=(
            RegimeObservation("r0", "A"),
            RegimeObservation("r1", "B"),
        ),
        target_regime_id="r1",
        target_outcome="B",
        available_discriminator_regimes=(),
        registered_valid_scope_regimes=("r0", "r1"),
        known_answer_validated=True,
        frozen_before_output=True,
    )


def test_observational_equivalence_preserves_survivor_set_and_forbids_point_identification():
    report = evaluate_mechanism_fidelity(
        _equivalence_world(),
        _correct_equivalence_output(),
    )
    assert report.verdict is MechanismFidelityVerdict.PASS
    assert report.prediction_correct is True
    assert report.gold_survivor_mechanism_ids == ("m1", "m2")
    assert report.identification_correct is True
    assert report.gold_discriminator_regimes == ("r1",)
    assert report.grants_scientific_authority is False


def test_correct_prediction_with_premature_identification_is_cawm():
    output = _correct_equivalence_output(
        survivor_mechanism_ids=("m1",),
        mechanism_supported_ids=("m1",),
        identified_mechanism_id="m1",
    )
    report = evaluate_mechanism_fidelity(_equivalence_world(), output)
    assert report.verdict is MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE
    assert report.correct_answer_wrong_mechanism is True
    assert report.mechanism_to_identification_leak is True


def test_regime_shift_eliminates_wrong_mechanism_and_licenses_identification():
    output = MechanismAgentOutput(
        predicted_target_outcome="B",
        survivor_mechanism_ids=("m1",),
        mechanism_supported_ids=("m1",),
        identified_mechanism_id="m1",
        proposed_discriminator_regime=None,
        claimed_scope_regimes=("r0", "r1"),
    )
    report = evaluate_mechanism_fidelity(_shift_world(), output)
    assert report.verdict is MechanismFidelityVerdict.PASS
    assert report.gold_survivor_mechanism_ids == ("m1",)
    assert report.identification_correct is True


def test_correct_prediction_cannot_rescue_mechanism_contradicted_by_shift():
    output = MechanismAgentOutput(
        predicted_target_outcome="B",
        survivor_mechanism_ids=("m1",),
        mechanism_supported_ids=("m2",),
        identified_mechanism_id="m2",
        proposed_discriminator_regime=None,
        claimed_scope_regimes=("r0", "r1"),
    )
    report = evaluate_mechanism_fidelity(_shift_world(), output)
    assert report.prediction_correct is True
    assert report.mechanism_support_valid is False
    assert report.correct_answer_wrong_mechanism is True
    assert report.prediction_to_mechanism_leak is True
    assert report.verdict is MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE


def test_wrong_discriminator_is_separate_from_prediction_accuracy():
    report = evaluate_mechanism_fidelity(
        _equivalence_world(),
        _correct_equivalence_output(proposed_discriminator_regime="r2"),
    )
    assert report.prediction_correct is True
    assert report.discriminator_correct is False
    assert report.verdict is MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE


def test_scope_generalization_after_local_success_is_detected():
    report = evaluate_mechanism_fidelity(
        _equivalence_world(),
        _correct_equivalence_output(claimed_scope_regimes=("r0", "r1")),
    )
    assert report.scope_correct is False
    assert report.verdict is MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE
    assert "mechanism_scope_incorrect" in report.reasons


def test_mechanism_can_be_right_while_target_prediction_is_wrong():
    output = MechanismAgentOutput(
        predicted_target_outcome="wrong",
        survivor_mechanism_ids=("m1",),
        mechanism_supported_ids=("m1",),
        identified_mechanism_id="m1",
        proposed_discriminator_regime=None,
        claimed_scope_regimes=("r0", "r1"),
    )
    report = evaluate_mechanism_fidelity(_shift_world(), output)
    assert report.prediction_correct is False
    assert report.identification_correct is True
    assert report.verdict is MechanismFidelityVerdict.MECHANISM_OR_IDENTIFICATION_FAILURE


def test_unvalidated_or_posthoc_world_fails_closed():
    unknown = evaluate_mechanism_fidelity(
        _equivalence_world(known_answer_validated=None),
        _correct_equivalence_output(),
    )
    assert unknown.verdict is MechanismFidelityVerdict.CANNOT_CHECK

    posthoc = evaluate_mechanism_fidelity(
        _equivalence_world(frozen_before_output=False),
        _correct_equivalence_output(),
    )
    assert posthoc.verdict is MechanismFidelityVerdict.INVALID


def test_missing_prediction_in_known_world_invalidates_evaluator_contract():
    world = _equivalence_world(
        predictions=(
            MechanismPrediction("m1", "r0", "A"),
            MechanismPrediction("m1", "r1", "B"),
            MechanismPrediction("m2", "r1", "C"),
        )
    )
    report = evaluate_mechanism_fidelity(world, _correct_equivalence_output())
    assert report.verdict is MechanismFidelityVerdict.INVALID
    assert any(reason.startswith("missing_prediction:m2:r0") for reason in report.reasons)


def test_unknown_mechanism_reference_is_invalid_not_scored_as_reasoning_error():
    output = _correct_equivalence_output(mechanism_supported_ids=("m3",))
    report = evaluate_mechanism_fidelity(_equivalence_world(), output)
    assert report.verdict is MechanismFidelityVerdict.INVALID
    assert any(reason.startswith("unknown_mechanism_reference:") for reason in report.reasons)
