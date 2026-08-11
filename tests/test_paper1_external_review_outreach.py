from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path

import pytest


jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from review.paper1.external_outreach.validate_request import validate_request_contract


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "review" / "paper1" / "external_solicitation"
OUTREACH = ROOT / "review" / "paper1" / "external_outreach"
MANIFEST_PATH = PACKET / "PACKET_MANIFEST.json"
SCHEMA_PATH = ROOT / "schemas" / "paper1-external-review-request.schema.json"
OUTREACH_SCHEMA_PATH = OUTREACH / "SCHEMA.json"
TEMPLATE_PATH = OUTREACH / "REQUEST_TEMPLATE.json"
PUBLIC_OBSERVATION_PATH = OUTREACH / "PUBLIC_SOLICITATION_OBSERVATION.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _frozen_request() -> dict:
    request = deepcopy(_load(TEMPLATE_PATH))
    request["request_status"] = "frozen-outbound-solicitation-receipt"
    request["request_id"] = "P1-EXT-REQ-X001-R01"
    request["packet_manifest_sha256"] = _sha256(MANIFEST_PATH)
    request["reviewer_candidate"] = {
        "pseudonymous_id": "P1-REVIEWER-X001",
        "concern_code": "X001",
        "role": "formal_methods_reviewer",
        "expertise_requested": "Formal methods and scientific evidence governance",
        "human_expert_expected": True,
        "external_to_authoring_context_expected": True,
        "identity_and_coi_qualification_status": "pending-private-coordinator-audit",
    }
    request["coordinator"]["pseudonymous_id"] = "P1-COORDINATOR-C001"
    request["coordinator"]["private_identity_record_retained"] = True
    request["delivery"] = {
        "channel_class": "private_email",
        "private_contact_details_in_repository": False,
        "private_request_payload_sha256": "e" * 64,
        "private_delivery_receipt_sha256": "a" * 64,
    }
    request["chronology"] = {
        "concern_code_assigned_at_utc": "2026-08-11T08:00:00Z",
        "request_payload_frozen_at_utc": "2026-08-11T08:05:00Z",
        "request_sent_at_utc": "2026-08-11T08:10:00Z",
        "private_delivery_receipt_recorded_at_utc": "2026-08-11T08:11:00Z",
        "response_due_at_utc": "2026-08-25T08:10:00Z",
    }
    request["attestations"] = {key: True for key in request["attestations"]}
    request["declaration"]["solicitation_sent"] = True
    return request


def test_request_template_is_schema_valid_but_records_no_sent_review() -> None:
    request = _load(TEMPLATE_PATH)
    _validator().validate(request)

    assert request["request_status"] == "template-example-not-sent"
    assert request["packet_manifest_sha256"] == "0" * 64
    assert request["declaration"] == {
        "solicitation_sent": False,
        "response_received": False,
        "independent_review_completed": False,
        "peer_review_completed": False,
        "accepted_or_published": False,
    }
    assert request["delivery"]["private_contact_details_in_repository"] is False
    assert request["delivery"]["private_request_payload_sha256"] == "0" * 64
    assert OUTREACH_SCHEMA_PATH.read_bytes() == SCHEMA_PATH.read_bytes()


def test_public_issue_observation_records_only_public_state_and_no_review_authority() -> None:
    observation = _load(PUBLIC_OBSERVATION_PATH)
    request = _load(TEMPLATE_PATH)

    assert observation["issue"]["number"] == 41
    assert observation["issue"]["state"] == "OPEN"
    assert observation["issue"]["labels"] == ["help wanted", "question"]
    assert observation["issue"]["public_comment_count"] == 0
    assert observation["authority_boundary"] == {
        "public_issue_is_private_delivery_receipt": False,
        "public_issue_is_completed_review": False,
        "public_comment_is_qualified_independent_review": False,
        "zero_public_comments_implies_zero_private_responses": False,
        "private_delivery_status": "cannot-check-from-public-issue",
        "qualified_external_response_status": "cannot-check-from-public-issue-alone",
        "accepted_or_published": False,
    }
    assert request["public_solicitation_context"]["observation_receipt_sha256"] == _sha256(
        PUBLIC_OBSERVATION_PATH
    )


def test_frozen_request_binds_packet_track_artifact_and_return_contract() -> None:
    request = _frozen_request()
    _validator().validate(request)

    assert validate_request_contract(request, require_frozen=True) == []


@pytest.mark.parametrize(
    "mutation",
    [
        "manifest_hash",
        "artifact_hash",
        "lens_role",
        "reviewer_code",
        "return_schema_hash",
    ],
)
def test_runtime_rejects_broken_packet_track_reviewer_and_return_bindings(
    mutation: str,
) -> None:
    request = _frozen_request()
    if mutation == "manifest_hash":
        request["packet_manifest_sha256"] = "b" * 64
    elif mutation == "artifact_hash":
        request["artifact_binding"]["pdf_sha256"] = "c" * 64
    elif mutation == "lens_role":
        request["requested_track"]["reviewer_role"] = "novelty_prior_art_reviewer"
    elif mutation == "reviewer_code":
        request["reviewer_candidate"]["pseudonymous_id"] = "P1-REVIEWER-Z999"
    elif mutation == "return_schema_hash":
        request["return_contract"]["response_schema_sha256"] = "d" * 64
    else:  # pragma: no cover
        raise AssertionError(mutation)

    errors = validate_request_contract(request, require_frozen=True)
    assert errors
    assert any("bind" in error or "role" in error or "pseudonymous" in error for error in errors)


@pytest.mark.parametrize("mode", ["sent_before_freeze", "due_before_sent"])
def test_runtime_rejects_reversed_request_chronology(mode: str) -> None:
    request = _frozen_request()
    if mode == "sent_before_freeze":
        request["chronology"]["request_sent_at_utc"] = "2026-08-11T08:01:00Z"
    else:
        request["chronology"]["response_due_at_utc"] = "2026-08-11T08:09:00Z"

    errors = validate_request_contract(request, require_frozen=True)
    assert any("chronology" in error for error in errors)


def test_frozen_request_cannot_mint_external_review_authority() -> None:
    request = _frozen_request()
    request["declaration"]["independent_review_completed"] = True
    request["declaration"]["response_received"] = True

    errors = validate_request_contract(request, require_frozen=True)
    assert any("cannot declare a response or completed review" in error for error in errors)


def test_request_timestamps_are_explicit_utc_and_ordered() -> None:
    request = _frozen_request()
    chronology = request["chronology"]
    values = [
        datetime.fromisoformat(chronology[key].replace("Z", "+00:00"))
        for key in (
            "concern_code_assigned_at_utc",
            "request_payload_frozen_at_utc",
            "request_sent_at_utc",
            "private_delivery_receipt_recorded_at_utc",
            "response_due_at_utc",
        )
    ]

    assert values == sorted(values)
