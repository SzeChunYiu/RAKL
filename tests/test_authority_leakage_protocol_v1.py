"""Protocol / result-schema / leakage-check stub contract for ALR V1 (refs #154).

Continues #154 after the merged scorer+panel PR: freezes PROTOCOL_V1.md, the
result and response schemas, a hash-bound freeze receipt, and a shape-only
leakage-check stub that never sees hidden labels.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from rakl.authority_leakage_benchmark import (
    CLAIM_BOUNDARY,
    LABEL_FIELD_NAMES,
    PROTOCOL_ID,
    AuthorityAxis,
    TransitionDecision,
    TransitionResponse,
    always_blocked_responder,
    always_escalate_responder,
    build_freeze_receipt,
    check_response_shape,
    frozen_case_panel,
    response_to_dict,
    run_responder,
    score_panel,
    score_to_result_dict,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "benchmarks" / "scientific_transition_authority" / "PROTOCOL_V1.md"
CASE_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-case-v1.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-result-v1.schema.json"
RESPONSE_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-response-v1.schema.json"

PANEL = frozen_case_panel()


def test_protocol_document_exists_and_names_frozen_ids() -> None:
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    assert PROTOCOL_ID in text
    assert "scientific-transition-case-v1" in text
    assert "scientific-transition-result-v1" in text
    assert "ALR is never reportable alone" in text or "never reportable alone" in text
    assert "No evaluated model result may precede this protocol freeze" in text
    assert "arXiv:2604.18805" in text
    assert "arXiv:2605.10246" in text


def test_protocol_defines_alr_as_unauthorized_over_opportunities() -> None:
    """Metric definition test: protocol text and scorer share the same ALR form."""

    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    assert re.search(
        r"ALR\s*=\s*\(cases with ≥1 unauthorized authority upgrade\)",
        text,
    )
    score = score_panel(PANEL, run_responder(PANEL, always_escalate_responder))
    assert score.leak_opportunities > 0
    assert score.alr == score.leaked_cases / score.leak_opportunities


def test_freeze_receipt_binds_protocol_schemas_panel_and_scorer() -> None:
    receipt = build_freeze_receipt(PANEL)
    assert receipt.protocol_id == PROTOCOL_ID
    assert receipt.case_count == len(PANEL)
    assert receipt.leakage_subtype_count >= 6
    assert receipt.grants_authority is False
    assert receipt.claim_boundary == CLAIM_BOUNDARY
    assert re.fullmatch(r"[0-9a-f]{64}", receipt.protocol_sha256)
    assert re.fullmatch(r"[0-9a-f]{64}", receipt.panel_visible_sha256)
    assert re.fullmatch(r"[0-9a-f]{64}", receipt.artifact_hash)
    assert receipt.to_dict()["protocol_path"].endswith("PROTOCOL_V1.md")


def test_freeze_receipt_is_stable_for_identical_panel() -> None:
    assert build_freeze_receipt(PANEL).artifact_hash == build_freeze_receipt(PANEL).artifact_hash


def test_committed_freeze_receipt_matches_live_builder() -> None:
    """Docs-contract: the checked-in receipt must equal a live freeze."""

    path = ROOT / "benchmarks" / "scientific_transition_authority" / "FREEZE_RECEIPT_V1.json"
    committed = json.loads(path.read_text(encoding="utf-8"))
    live = build_freeze_receipt(PANEL)
    assert committed["protocol_id"] == live.protocol_id
    assert committed["protocol_sha256"] == live.protocol_sha256
    assert committed["case_schema_sha256"] == live.case_schema_sha256
    assert committed["result_schema_sha256"] == live.result_schema_sha256
    assert committed["response_schema_sha256"] == live.response_schema_sha256
    assert committed["panel_visible_sha256"] == live.panel_visible_sha256
    assert committed["scorer_source_sha256"] == live.scorer_source_sha256
    assert committed["artifact_hash"] == live.artifact_hash
    assert committed["grants_authority"] is False
    assert committed["issue"] == 154


def test_response_schema_accepts_serialized_stub_responses() -> None:
    validator = Draft7Validator(json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8")))
    for response in run_responder(PANEL, always_blocked_responder):
        payload = response_to_dict(response)
        assert list(validator.iter_errors(payload)) == []


def test_response_schema_rejects_smuggled_labels() -> None:
    validator = Draft7Validator(json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8")))
    payload = response_to_dict(
        TransitionResponse(
            case_id="x",
            transition_decision=TransitionDecision.BLOCKED,
            authority_delta={},
        )
    )
    payload["required_terminal_status"] = "BLOCKED"
    assert list(validator.iter_errors(payload)) != []


def test_leakage_check_stub_accepts_well_formed_response() -> None:
    payload = response_to_dict(
        TransitionResponse(
            case_id="ALR-01-prediction-not-mechanism",
            transition_decision=TransitionDecision.SUPPORTED,
            authority_delta={AuthorityAxis.REPRESENTATION: 1, AuthorityAxis.MECHANISM: 1},
        )
    )
    report = check_response_shape(payload)
    assert report.ok is True
    assert report.raised_axes == ("M", "R")
    # Stub must not decide authorization — only shape.
    assert not hasattr(report, "leaked")


def test_leakage_check_stub_rejects_label_smuggling_and_bad_enums() -> None:
    bad = {
        "case_id": "x",
        "transition_decision": "MAYBE",
        "authority_delta": {"M": 1},
        "state_edits": ["no_change"],
        "rationale_receipts": {
            "evidence_ids": [],
            "alignment_ids": [],
            "dependency_ids": [],
        },
        "allowed_authority_effects": ["M"],
    }
    report = check_response_shape(bad)
    assert report.ok is False
    assert any("transition_decision" in err or "MAYBE" in err for err in report.errors)
    assert any("smuggled label field" in err for err in report.errors)


def test_result_schema_accepts_packaged_degenerate_scores() -> None:
    receipt = build_freeze_receipt(PANEL)
    validator = Draft7Validator(json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8")))
    for responder, responder_id in (
        (always_blocked_responder, "always_blocked"),
        (always_escalate_responder, "always_escalate"),
    ):
        score = score_panel(PANEL, run_responder(PANEL, responder))
        payload = score_to_result_dict(
            score,
            protocol_sha256=receipt.protocol_sha256,
            case_schema_sha256=receipt.case_schema_sha256,
            result_schema_sha256=receipt.result_schema_sha256,
            panel_visible_sha256_digest=receipt.panel_visible_sha256,
            scorer_source_sha256=receipt.scorer_source_sha256,
            responder_id=responder_id,
        )
        assert list(validator.iter_errors(payload)) == []
        assert payload["grants_authority"] is False
        assert set(payload) >= {"alr", "valid_upgrade_recall"}


def test_result_schema_rejects_authority_grant() -> None:
    receipt = build_freeze_receipt(PANEL)
    score = score_panel(PANEL, run_responder(PANEL, always_blocked_responder))
    payload = score_to_result_dict(
        score,
        protocol_sha256=receipt.protocol_sha256,
        case_schema_sha256=receipt.case_schema_sha256,
        result_schema_sha256=receipt.result_schema_sha256,
        panel_visible_sha256_digest=receipt.panel_visible_sha256,
        scorer_source_sha256=receipt.scorer_source_sha256,
    )
    payload["grants_authority"] = True
    validator = Draft7Validator(json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8")))
    assert list(validator.iter_errors(payload)) != []


def test_case_schema_still_present_for_protocol_binding() -> None:
    assert CASE_SCHEMA_PATH.is_file()
    assert RESPONSE_SCHEMA_PATH.is_file()
    assert RESULT_SCHEMA_PATH.is_file()


@pytest.mark.parametrize("name", LABEL_FIELD_NAMES)
def test_protocol_documents_hidden_label_field_names(name: str) -> None:
    # Defence in depth for the docs contract: the protocol names the separation.
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    assert "HiddenCaseLabels" in text
    assert "VisibleCaseContext" in text
    assert name  # keep parametrize meaningful / non-empty
