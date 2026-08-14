from rakl.external_analogy_grounding import (
    AnalogyDecision,
    ExternalAnalogyCase,
    GroundedMapping,
    GroundedWitness,
    evaluate_grounded_witness,
)


POS = ExternalAnalogyCase(
    case_id="pos",
    source_text="Evaporation converts liquid water into water vapor before clouds form.",
    target_text="Fixation converts atmospheric nitrogen into a usable form before deposition.",
    gold_decision=AnalogyDecision.LICENSED,
    gold_mappings=(("Evaporation", "Fixation"),),
)
NEG = ExternalAnalogyCase(
    case_id="neg",
    source_text="Evaporation converts liquid water into water vapor.",
    target_text="A seismograph records waves after an earthquake.",
    gold_decision=AnalogyDecision.REJECTED,
)
UNK = ExternalAnalogyCase(
    case_id="unk",
    source_text="Evaporation converts liquid water into water vapor.",
    target_text="The corresponding target mechanism is omitted from this excerpt.",
    gold_decision=AnalogyDecision.CANNOT_CHECK,
)


def good_positive():
    return GroundedWitness(
        AnalogyDecision.LICENSED,
        (
            GroundedMapping(
                "Evaporation",
                "Fixation",
                "Evaporation converts liquid water into water vapor",
                "Fixation converts atmospheric nitrogen into a usable form",
            ),
        ),
        "process-step role under the presented conversion QoI",
    )


def test_valid_grounded_positive_passes():
    result = evaluate_grounded_witness(POS, good_positive())
    assert result.structured_valid
    assert result.decision_correct
    assert result.mapping_f1 == 1.0
    assert result.grounded_mapping_rate == 1.0
    assert not result.unsafe_false_accept
    assert not result.grants_scientific_authority


def test_always_licensed_fails_challenging_negative():
    attack = GroundedWitness(
        AnalogyDecision.LICENSED,
        (GroundedMapping("Evaporation", "seismograph", "Evaporation", "seismograph"),),
        "generic process",
    )
    result = evaluate_grounded_witness(NEG, attack)
    assert result.unsafe_false_accept
    assert not result.decision_correct


def test_always_rejected_fails_true_analogy():
    result = evaluate_grounded_witness(POS, GroundedWitness(AnalogyDecision.REJECTED))
    assert result.structured_valid
    assert not result.decision_correct
    assert result.mapping_f1 == 0.0


def test_always_cannot_check_fails_true_analogy():
    result = evaluate_grounded_witness(POS, GroundedWitness(AnalogyDecision.CANNOT_CHECK))
    assert result.structured_valid
    assert not result.decision_correct


def test_missing_evidence_control_accepts_cannot_check():
    result = evaluate_grounded_witness(UNK, GroundedWitness(AnalogyDecision.CANNOT_CHECK))
    assert result.structured_valid
    assert result.decision_correct


def test_fabricated_span_fails_closed():
    bad = GroundedWitness(
        AnalogyDecision.LICENSED,
        (GroundedMapping("Evaporation", "Fixation", "not present", "Fixation"),),
        "process-step role",
    )
    result = evaluate_grounded_witness(POS, bad)
    assert not result.structured_valid
    assert not result.decision_correct
    assert "mapping_not_exactly_source_span_grounded" in result.reasons


def test_reversed_mapping_is_scored_wrong_even_when_spans_exist():
    bad = GroundedWitness(
        AnalogyDecision.LICENSED,
        (
            GroundedMapping(
                "liquid water",
                "atmospheric nitrogen",
                "Evaporation converts liquid water into water vapor",
                "Fixation converts atmospheric nitrogen into a usable form",
            ),
        ),
        "process-step role",
    )
    result = evaluate_grounded_witness(POS, bad)
    assert result.structured_valid
    assert result.mapping_f1 == 0.0


def test_nonlicensed_output_cannot_smuggle_positive_mapping():
    bad = GroundedWitness(
        AnalogyDecision.CANNOT_CHECK,
        (GroundedMapping("Evaporation", "Fixation", "Evaporation", "Fixation"),),
    )
    result = evaluate_grounded_witness(POS, bad)
    assert not result.structured_valid
    assert "nonlicensed_output_carries_positive_mapping" in result.reasons


def test_duplicate_mapping_is_invalid():
    item = GroundedMapping("Evaporation", "Fixation", "Evaporation", "Fixation")
    result = evaluate_grounded_witness(
        POS,
        GroundedWitness(AnalogyDecision.LICENSED, (item, item), "process-step role"),
    )
    assert not result.structured_valid
    assert "duplicate_mapping" in result.reasons
