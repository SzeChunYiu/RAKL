"""Tests for Wave-1 Lane C Paper III powered non-circular BLOCKED_HUMAN freeze."""

from __future__ import annotations

import json
from pathlib import Path

from rakl.paper3_power_design import (
    verify_issue_217_zero_public_responses,
    verify_public_annotation_directory,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research/paper3_powered_noncircular_human_packet_v1"


def _load(name: str) -> dict:
    return json.loads((PACKET_DIR / name).read_text(encoding="utf-8"))


def test_packet_dir_complete() -> None:
    required = [
        "README.md",
        "ZERO_LABELS_CHRONOLOGY_RECEIPT.json",
        "BLOCKED_HUMAN_RECEIPT.json",
        "AI_OPERATOR_DEMOTION_BINDING.json",
        "POWERED_NONCIRCULAR_PACKET_FREEZE.json",
        "WAVE2_BLOCKERS.json",
        "PACKET_FREEZE_RECEIPT.json",
    ]
    for name in required:
        assert (PACKET_DIR / name).is_file(), name


def test_zero_labels_chronology_before_independent_humans() -> None:
    chrono = _load("ZERO_LABELS_CHRONOLOGY_RECEIPT.json")
    assert chrono["state"] == "ZERO_LABELS_OBSERVED"
    assert chrono["observation"] == "ZERO_INDEPENDENT_EXTERNAL_HUMAN_LABELS"
    assert chrono["label_payload_accessed"] is False
    assert chrono["evaluated_results_accessed"] is False
    assert chrono["first_independent_external_label_at_utc"] is None
    assert chrono["chronology_attestation"]["freeze_before_independent_labels"] is True
    assert chrono["counts"]["independent_external_annotations"] == 0
    assert (
        chrono["demoted_ai_operator_inventory"]["counts_as_independent_human_evidence"]
        is False
    )
    assert chrono["grants_scientific_authority"] is False

    live_ann = verify_public_annotation_directory(ROOT)
    live_issue = verify_issue_217_zero_public_responses(ROOT)
    assert live_ann["verdict"] == "ZERO_PUBLIC_ANNOTATION_PAYLOADS"
    assert live_issue["verdict"] == "ZERO_IMPORTED_EXTERNAL_PAYLOADS"


def test_blocked_human_does_not_invent_or_promote_ai_operator() -> None:
    blocked = _load("BLOCKED_HUMAN_RECEIPT.json")
    assert blocked["status"] == "BLOCKED_HUMAN"
    assert blocked["acceptance_assessment"]["independent_annotator_a_present"] is False
    assert blocked["acceptance_assessment"]["independent_annotator_b_present"] is False
    assert (
        blocked["acceptance_assessment"]["distinct_external_adjudicator_present"]
        is False
    )
    assert (
        blocked["acceptance_assessment"][
            "distinct_external_provenance_auditor_present"
        ]
        is False
    )
    assert "AI_OPERATOR_AS_INDEPENDENT_HUMAN" in blocked["forbidden_substitutions"]
    assert blocked["ai_operator_status"]["may_satisfy_blocked_human"] is False
    assert blocked["ai_operator_status"]["preserved_as"] == "demoted-only"
    assert blocked["grants_scientific_authority"] is False


def test_ai_operator_demotion_binding() -> None:
    binding = _load("AI_OPERATOR_DEMOTION_BINDING.json")
    honesty = json.loads(
        (
            ROOT / "research/paper3/ai_operator_v2_1/HONESTY_STAMP_AI_OPERATOR.json"
        ).read_text(encoding="utf-8")
    )
    assert binding["authority_class"] == "DEMOTED_AI_OPERATOR"
    assert binding["independent_external_human"] is False
    assert binding["promotion_to_independent_forbidden"] is True
    assert honesty["independent_external_human"] is False
    assert honesty["authority_class"] == "DEMOTED_AI_OPERATOR"


def test_powered_design_bound_without_fabricating_n48() -> None:
    packet = _load("POWERED_NONCIRCULAR_PACKET_FREEZE.json")
    assert packet["design_class"] == "POWERED_NONCIRCULAR_EXTERNAL_VALIDATION"
    assert packet["status"] == "FROZEN_DESIGN_BLOCKED_HUMAN"
    assert packet["power_binding"]["adequate_n_all_sigmas"] == 48
    assert packet["power_binding"]["prior_confirmatory_n"] == 16
    assert packet["powered_expansion_status"]["successor_source_set_created"] is False
    assert packet["powered_expansion_status"]["successor_public_packet_created"] is False
    assert packet["human_recruitment_status"] == "BLOCKED_HUMAN"
    assert packet["noncircular_binding"]["human_labels_may_enter_extractor"] is False
    assert packet["grants_scientific_authority"] is False


def test_freeze_receipt_wave1_claim_boundary() -> None:
    receipt = _load("PACKET_FREEZE_RECEIPT.json")
    assert receipt["terminal_status"] == "BLOCKED_HUMAN"
    assert receipt["freeze_before_labels_attested"] is True
    assert receipt["acceptance_assessment"]["independent_humans_fabricated"] is False
    assert receipt["acceptance_assessment"]["n48_source_set_fabricated"] is False
    assert receipt["acceptance_assessment"]["ai_operator_kept_demoted_only"] is True
    assert receipt["grants_scientific_authority"] is False
    assert receipt["promotional_lift_claim_allowed"] is False
    wave2 = _load("WAVE2_BLOCKERS.json")
    blocker_ids = {b["id"] for b in wave2["blockers"]}
    assert "W2-P3-HUMAN-ROLES" in blocker_ids
    assert "W2-P3-N48-SOURCE-EXPANSION" in blocker_ids
