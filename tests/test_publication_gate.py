from __future__ import annotations

from pathlib import Path

from rakl.publication_gate import (
    PublicationGatePacket,
    PublicationGateVerdict,
    evaluate_publication_gate,
)


REQUIRED = (
    "E1_KNOWN_ANSWER",
    "E3_MATCHED_WORKFLOW",
    "E4_SELF_EVOLUTION",
    "E2_SPOT_PREDICTIVE",
)


def packet(**overrides):
    base = dict(
        manuscript_text="Complete manuscript without unresolved slots.",
        required_result_ids=REQUIRED,
        receipted_result_ids=REQUIRED,
        quant_real_result_receipted=True,
        self_evolution_fresh_assurance_receipted=True,
        matched_workflow_receipted=True,
        independent_method_review=True,
        independent_quant_review=True,
        independent_artifact_reproduction=True,
        figures_tables_from_receipts=True,
        release_manifest_verified=True,
        code_data_availability_ready=True,
        ai_use_disclosure_ready=True,
    )
    base.update(overrides)
    return PublicationGatePacket(**base)


def test_complete_packet_is_scoped_submission_ready():
    report = evaluate_publication_gate(packet())
    assert report.verdict == PublicationGateVerdict.SCOPED_SUBMISSION_READY
    assert report.submission_ready
    assert report.scientific_truth_authority is False


def test_current_manuscript_result_slots_block_submission():
    manuscript = (
        Path(__file__).resolve().parents[1] / "paper" / "RAKL_MANUSCRIPT.md"
    ).read_text(encoding="utf-8")
    report = evaluate_publication_gate(
        packet(
            manuscript_text=manuscript,
            receipted_result_ids=(),
            quant_real_result_receipted=False,
            self_evolution_fresh_assurance_receipted=False,
            matched_workflow_receipted=False,
            independent_method_review=False,
            independent_quant_review=False,
            independent_artifact_reproduction=False,
            figures_tables_from_receipts=False,
            release_manifest_verified=False,
            code_data_availability_ready=False,
            ai_use_disclosure_ready=False,
        )
    )
    assert report.verdict == PublicationGateVerdict.NOT_SUBMISSION_READY
    assert set(report.unresolved_result_ids) == set(REQUIRED)
    assert set(report.unresolved_manuscript_slots) == set(REQUIRED)


def test_development_only_self_evolution_cannot_close_submission():
    report = evaluate_publication_gate(
        packet(self_evolution_fresh_assurance_receipted=False)
    )
    assert report.verdict == PublicationGateVerdict.NOT_SUBMISSION_READY
    assert any("fresh-assurance" in reason for reason in report.reasons)


def test_green_driver_without_real_quant_result_cannot_close_submission():
    report = evaluate_publication_gate(packet(quant_real_result_receipted=False))
    assert report.verdict == PublicationGateVerdict.NOT_SUBMISSION_READY
    assert any("quant-science" in reason for reason in report.reasons)


def test_hand_entered_headline_result_is_rejected():
    report = evaluate_publication_gate(
        packet(hand_entered_headline_numbers_detected=True)
    )
    assert report.verdict == PublicationGateVerdict.REJECT


def test_blocking_failure_cannot_be_compensated():
    report = evaluate_publication_gate(
        packet(blocking_failures=("authority leakage",))
    )
    assert report.verdict == PublicationGateVerdict.REJECT
    assert not report.submission_ready


def test_independent_review_is_mandatory():
    report = evaluate_publication_gate(packet(independent_method_review=False))
    assert report.verdict == PublicationGateVerdict.NOT_SUBMISSION_READY
    assert any("method/novelty" in reason for reason in report.reasons)
