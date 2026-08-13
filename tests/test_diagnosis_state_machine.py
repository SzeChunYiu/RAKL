import pytest
from rakl.diagnosis_state_machine import *


def test_competing_causes_need_discriminator_or_remain_partial():
    s = competing_state("d", ("METRIC_FALSEHOOD", "LOCAL_MINIMUM"), discriminator_ids=("x",))
    assert s.verdict is DiagnosisVerdict.DISCRIMINATOR_REQUIRED
    resolved = resolve_discriminator(s, discriminator_id="x", surviving_causes=("METRIC_FALSEHOOD",), evidence_receipt_id="ev")
    assert resolved.verdict is DiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
    assert resolved.candidate_causes == ("METRIC_FALSEHOOD",)


def test_unique_concrete_cause_cannot_hide_in_cannot_check():
    with pytest.raises(ValueError):
        DiagnosisState("d", ("METRIC_FALSEHOOD",), (), (), None, DiagnosisVerdict.CANNOT_CHECK)


def test_no_gap_needs_evidence():
    with pytest.raises(ValueError):
        DiagnosisState("d", (), (), (), None, DiagnosisVerdict.NO_GAP)
    s = unresolved_state("d")
    done = establish_no_gap(s, evidence_receipt_id="disc-negative")
    assert done.verdict is DiagnosisVerdict.NO_GAP
    assert not done.grants_scientific_authority


def test_discriminator_transition_receipt_binds_before_after_and_choice():
    s = competing_state("d", ("A", "B"), discriminator_ids=("disc",))
    after, receipt = resolve_discriminator_with_receipt(
        s, transition_id="tr", discriminator_id="disc", surviving_causes=("A",), evidence_receipt_id="ev"
    )
    assert receipt.before_state_digest == s.digest
    assert receipt.after_state_digest == after.digest
    assert receipt.discriminator_id == "disc"
    assert not receipt.grants_method_promotion_authority
