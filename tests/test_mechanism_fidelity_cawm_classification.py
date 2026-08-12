from rakl.mechanism_fidelity import (
    MechanismAgentOutput,
    MechanismFidelityVerdict,
    MechanismPrediction,
    MechanismWorld,
    RegimeObservation,
    evaluate_mechanism_fidelity,
)


def test_unique_survivor_without_point_identification_is_not_cawm():
    world = MechanismWorld(
        world_id="unique-survivor",
        candidate_mechanism_ids=("m1", "m2"),
        predictions=(
            MechanismPrediction("m1", "r0", "A"),
            MechanismPrediction("m2", "r0", "B"),
        ),
        observations=(RegimeObservation("r0", "A"),),
        target_regime_id="r0",
        target_outcome="A",
        available_discriminator_regimes=(),
        registered_valid_scope_regimes=("r0",),
        known_answer_validated=True,
        frozen_before_output=True,
    )
    output = MechanismAgentOutput(
        predicted_target_outcome="A",
        survivor_mechanism_ids=("m1",),
        mechanism_supported_ids=("m1",),
        identified_mechanism_id=None,
        proposed_discriminator_regime=None,
        claimed_scope_regimes=("r0",),
    )

    report = evaluate_mechanism_fidelity(world, output)

    assert report.prediction_correct is True
    assert report.survivor_set_correct is True
    assert report.mechanism_support_valid is True
    assert report.identification_correct is False
    assert report.correct_answer_wrong_mechanism is False
    assert report.verdict is MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE
