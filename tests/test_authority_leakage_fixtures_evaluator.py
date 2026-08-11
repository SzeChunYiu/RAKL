"""Fail-closed evaluator + frozen fixture slice for ALR V1 (refs #154).

Continues after protocol/schema/stub freeze (#198): lands three known-answer
fixtures on disk and an evaluator that shape-checks before scoring and never
grants scientific authority.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from rakl.authority_leakage_benchmark import (
    LABEL_FIELD_NAMES,
    AuthorityAxis,
    EvaluationStatus,
    FIXTURE_MANIFEST_PATH,
    RationaleReceipts,
    TransitionDecision,
    TransitionResponse,
    always_blocked_responder,
    always_escalate_responder,
    build_freeze_receipt,
    build_proposal_context,
    evaluate_authority_leakage,
    frozen_case_panel,
    frozen_fixture_panel,
    load_fixture,
    response_to_dict,
    run_responder,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "benchmarks" / "scientific_transition_authority" / "fixtures"
FIXTURE_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-fixture-v1.schema.json"
CASE_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-case-v1.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "scientific-transition-result-v1.schema.json"

EXPECTED_CASE_IDS = (
    "ALR-01-prediction-not-mechanism",
    "ALR-06-missing-evidence-integrity-trap",
    "ALR-07-legitimate-mechanism-upgrade",
)


@pytest.fixture(scope="module")
def fixture_panel():
    return frozen_fixture_panel()


def test_manifest_names_three_known_answer_cases() -> None:
    manifest = json.loads(FIXTURE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["grants_authority"] is False
    assert manifest["case_ids"] == list(EXPECTED_CASE_IDS)
    assert manifest["protocol_id"] == "scientific-transition-authority-v1"


def test_fixtures_load_and_match_in_code_panel_labels(fixture_panel) -> None:
    by_id = {case.case_id: case for case in frozen_case_panel()}
    assert [case.case_id for case in fixture_panel] == list(EXPECTED_CASE_IDS)
    for case in fixture_panel:
        reference = by_id[case.case_id]
        assert case.labels.required_terminal_status is reference.labels.required_terminal_status
        assert case.labels.allowed_authority_effects == reference.labels.allowed_authority_effects
        assert dict(case.labels.disallowed_authority_effects) == dict(
            reference.labels.disallowed_authority_effects
        )
        assert case.stratum is reference.stratum


def test_fixture_visible_halves_validate_and_exclude_labels(fixture_panel) -> None:
    case_validator = Draft7Validator(json.loads(CASE_SCHEMA_PATH.read_text(encoding="utf-8")))
    fixture_validator = Draft7Validator(
        json.loads(FIXTURE_SCHEMA_PATH.read_text(encoding="utf-8"))
    )
    for case_id in EXPECTED_CASE_IDS:
        raw = json.loads((FIXTURES_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        assert list(fixture_validator.iter_errors(raw)) == []
        assert list(case_validator.iter_errors(raw["visible"])) == []
        rendered = json.dumps(build_proposal_context(load_fixture(FIXTURES_DIR / f"{case_id}.json").visible))
        for name in LABEL_FIELD_NAMES:
            assert name not in rendered
        # Proposal context must not carry terminal-status vocabulary.
        for decision in TransitionDecision:
            assert decision.value not in rendered


def test_fixture_slice_has_hostile_and_legitimate_controls(fixture_panel) -> None:
    terminals = {case.labels.required_terminal_status for case in fixture_panel}
    assert TransitionDecision.CANNOT_CHECK in terminals
    assert TransitionDecision.SUPPORTED in terminals
    assert any(case.labels.allowed_authority_effects for case in fixture_panel)
    assert any(case.labels.disallowed_authority_effects for case in fixture_panel)


def test_evaluator_scores_oracle_responses_without_granting_authority(fixture_panel) -> None:
    """Oracle: raise only allowed axes / emit required terminal + blockers."""

    payloads = []
    for case in fixture_panel:
        delta = {axis: 1 for axis in case.labels.allowed_authority_effects}
        payloads.append(
            response_to_dict(
                TransitionResponse(
                    case_id=case.case_id,
                    transition_decision=case.labels.required_terminal_status,
                    authority_delta=delta,
                    state_edits=case.labels.required_state_edits,
                    rationale_receipts=RationaleReceipts(
                        dependency_ids=case.labels.required_blockers
                    ),
                )
            )
        )
    report = evaluate_authority_leakage(fixture_panel, payloads, responder_id="oracle")
    assert report.status is EvaluationStatus.SCORED
    assert report.ok is True
    assert report.grants_authority is False
    assert report.score is not None
    assert report.score.alr == 0.0
    assert report.score.valid_upgrade_recall == 1.0
    assert report.result is not None
    assert report.result["grants_authority"] is False
    validator = Draft7Validator(json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8")))
    assert list(validator.iter_errors(report.result)) == []


def test_evaluator_detects_prediction_to_mechanism_leak_on_fixture(fixture_panel) -> None:
    case = next(c for c in fixture_panel if c.case_id == "ALR-01-prediction-not-mechanism")
    others = [c for c in fixture_panel if c.case_id != case.case_id]
    payloads = [
        response_to_dict(
            TransitionResponse(
                case_id=case.case_id,
                transition_decision=TransitionDecision.SUPPORTED,
                authority_delta={
                    AuthorityAxis.REPRESENTATION: 1,
                    AuthorityAxis.MECHANISM: 1,
                },
            )
        )
    ]
    for other in others:
        payloads.append(
            response_to_dict(
                TransitionResponse(
                    case_id=other.case_id,
                    transition_decision=other.labels.required_terminal_status,
                    authority_delta={axis: 1 for axis in other.labels.allowed_authority_effects},
                    state_edits=other.labels.required_state_edits,
                    rationale_receipts=RationaleReceipts(
                        dependency_ids=other.labels.required_blockers
                    ),
                )
            )
        )
    report = evaluate_authority_leakage(fixture_panel, payloads)
    assert report.status is EvaluationStatus.SCORED
    assert report.score is not None
    assert report.score.alr > 0.0
    leaked = next(o for o in report.score.outcomes if o.case_id == case.case_id)
    assert leaked.leaked is True


def test_evaluator_fail_closed_on_missing_response(fixture_panel) -> None:
    payloads = [
        response_to_dict(response)
        for response in run_responder(fixture_panel[:1], always_blocked_responder)
    ]
    report = evaluate_authority_leakage(fixture_panel, payloads)
    assert report.status is EvaluationStatus.BLOCKED
    assert report.score is None
    assert report.result is None
    assert report.grants_authority is False
    assert any(block.startswith("missing_response:") for block in report.blockers)


def test_evaluator_fail_closed_on_label_smuggling(fixture_panel) -> None:
    payloads = [
        response_to_dict(response)
        for response in run_responder(fixture_panel, always_blocked_responder)
    ]
    payloads[0] = dict(payloads[0])
    payloads[0]["required_terminal_status"] = "BLOCKED"
    report = evaluate_authority_leakage(fixture_panel, payloads)
    assert report.status is EvaluationStatus.BLOCKED
    assert report.score is None
    assert any(block.startswith("shape_invalid:") for block in report.blockers)


def test_evaluator_fail_closed_on_malformed_enum(fixture_panel) -> None:
    payloads = [
        response_to_dict(response)
        for response in run_responder(fixture_panel, always_escalate_responder)
    ]
    payloads[0] = dict(payloads[0])
    payloads[0]["transition_decision"] = "MAYBE"
    report = evaluate_authority_leakage(fixture_panel, payloads)
    assert report.status is EvaluationStatus.BLOCKED
    assert report.score is None


def test_evaluator_never_emits_authority_grant_even_for_escalate(fixture_panel) -> None:
    payloads = [
        response_to_dict(response)
        for response in run_responder(fixture_panel, always_escalate_responder)
    ]
    report = evaluate_authority_leakage(fixture_panel, payloads, responder_id="always_escalate")
    assert report.status is EvaluationStatus.SCORED
    assert report.grants_authority is False
    assert report.result is not None
    assert report.result["grants_authority"] is False
    assert report.score is not None
    assert report.score.alr == 1.0


def test_load_fixture_rejects_case_id_mismatch(tmp_path: Path) -> None:
    raw = json.loads(
        (FIXTURES_DIR / "ALR-01-prediction-not-mechanism.json").read_text(encoding="utf-8")
    )
    raw["case_id"] = "ALR-01-prediction-not-mechanism"
    raw["visible"] = dict(raw["visible"])
    raw["visible"]["case_id"] = "other-id"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="case_id"):
        load_fixture(path)


def test_freeze_receipt_still_matches_after_scorer_extension() -> None:
    """Adding fixtures/evaluator must keep the committed 8-case freeze coherent."""

    path = ROOT / "benchmarks" / "scientific_transition_authority" / "FREEZE_RECEIPT_V1.json"
    committed = json.loads(path.read_text(encoding="utf-8"))
    live = build_freeze_receipt(frozen_case_panel())
    assert committed["scorer_source_sha256"] == live.scorer_source_sha256
    assert committed["artifact_hash"] == live.artifact_hash
    assert committed["grants_authority"] is False
