#!/usr/bin/env python3
"""Validate a Paper 1 outbound external-review solicitation request.

The request receipt proves only that a coordinator froze and sent an exact packet
request. It cannot prove reviewer identity, independence, response receipt, peer
review, acceptance, or publication.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


FROZEN_STATUS = "frozen-outbound-solicitation-receipt"
TEMPLATE_STATUS = "template-example-not-sent"
ZERO_SHA256 = "0" * 64


def _utc(value: Any, *, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        errors.append(f"{field} must be a UTC date-time ending in Z")
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        errors.append(f"{field} must be a valid UTC date-time")
        return None


def _contains_template_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return value == ZERO_SHA256 or value.startswith("EXAMPLE ONLY:") or "-EXAMPLE-" in value
    if isinstance(value, dict):
        return any(_contains_template_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_template_placeholder(item) for item in value)
    return False


def _default_packet_manifest_path() -> Path:
    return Path(__file__).parents[1] / "external_solicitation" / "PACKET_MANIFEST.json"


def validate_request_contract(
    request: dict[str, Any],
    *,
    require_frozen: bool = True,
    manifest_path: str | Path | None = None,
) -> list[str]:
    """Return fail-closed relational errors without minting review authority."""

    errors: list[str] = []
    status = request.get("request_status")
    if require_frozen and status != FROZEN_STATUS:
        errors.append(
            "request_status must be frozen-outbound-solicitation-receipt for ingestion"
        )
    if status == FROZEN_STATUS and _contains_template_placeholder(request):
        errors.append("frozen request contains a zero hash or EXAMPLE ONLY template placeholder")
    if status == TEMPLATE_STATUS and not require_frozen:
        return errors

    packet_manifest_path = (
        Path(manifest_path) if manifest_path is not None else _default_packet_manifest_path()
    )
    try:
        manifest_bytes = packet_manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"packet manifest binding cannot be loaded: {exc}")
        manifest = {}
        manifest_bytes = b""

    if manifest_bytes:
        expected_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        if request.get("packet_manifest_sha256") != expected_manifest_sha:
            errors.append("packet manifest binding hash does not match PACKET_MANIFEST.json")
    if request.get("packet_id") != manifest.get("packet_id"):
        errors.append("packet_id binding does not match PACKET_MANIFEST.json")

    observation_path = Path(__file__).with_name("PUBLIC_SOLICITATION_OBSERVATION.json")
    try:
        observation_bytes = observation_path.read_bytes()
        observation = json.loads(observation_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"public solicitation observation binding cannot be loaded: {exc}")
        observation = {}
        observation_bytes = b""
    expected_public_context = {
        "issue_number": observation.get("issue", {}).get("number"),
        "issue_url": observation.get("issue", {}).get("url"),
        "observation_receipt_path": (
            "review/paper1/external_outreach/PUBLIC_SOLICITATION_OBSERVATION.json"
        ),
        "observation_receipt_sha256": (
            hashlib.sha256(observation_bytes).hexdigest() if observation_bytes else None
        ),
        "public_issue_is_private_delivery_receipt": False,
        "public_comment_is_qualified_review": False,
    }
    if request.get("public_solicitation_context") != expected_public_context:
        errors.append("public solicitation context does not bind the issue observation receipt")
    if observation.get("packet_binding", {}).get("packet_manifest_sha256") != (
        hashlib.sha256(manifest_bytes).hexdigest() if manifest_bytes else None
    ):
        errors.append("public issue observation does not bind the exact packet manifest")

    subject = manifest.get("subject", {})
    expected_artifact_binding = {
        "manuscript_subject_sha": subject.get("git_sha"),
        "modular_source_sha256": subject.get("source", {}).get("sha256"),
        "builder_sha256": subject.get("builder", {}).get("sha256"),
        "staged_source_sha256": subject.get("staged_source", {}).get("sha256"),
        "pdf_sha256": subject.get("pdf", {}).get("sha256"),
        "pdf_pages": subject.get("pdf", {}).get("pages"),
    }
    if request.get("artifact_binding") != expected_artifact_binding:
        errors.append("artifact binding does not exactly match the packet subject")

    requested_track = request.get("requested_track", {})
    lens = requested_track.get("lens")
    tracks = {
        track.get("lens"): track
        for track in manifest.get("requested_review_tracks", [])
        if isinstance(track, dict)
    }
    track = tracks.get(lens)
    expected_track = {
        "lens": lens,
        "reviewer_role": track.get("reviewer_role") if track else None,
        "form_path": track.get("form_path") if track else None,
        "concern_namespace": track.get("concern_namespace") if track else None,
        "external_gate": track.get("external_gate") if track else None,
    }
    if not track or requested_track != expected_track:
        errors.append("requested track does not exactly bind a packet review track")

    reviewer = request.get("reviewer_candidate", {})
    if track and reviewer.get("role") != track.get("reviewer_role"):
        errors.append("reviewer candidate role does not bind the requested lens")
    code = reviewer.get("concern_code")
    round_number = request.get("review_round")
    if not isinstance(code, str) or not re.fullmatch(r"[A-Z0-9]{4}", code):
        errors.append("reviewer_candidate.concern_code must contain four uppercase letters/digits")
    elif reviewer.get("pseudonymous_id") != f"P1-REVIEWER-{code}":
        errors.append("reviewer candidate pseudonymous_id must bind the concern code")
    if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
        errors.append("review_round must be a positive integer")
    if isinstance(code, str) and isinstance(round_number, int):
        expected_request_id = f"P1-EXT-REQ-{code}-R{round_number:02d}"
        if request.get("request_id") != expected_request_id:
            errors.append(f"request_id must bind reviewer code and round as {expected_request_id}")

    return_contract = request.get("return_contract", {})
    expected_response_schema_path = Path(__file__).parents[3] / "schemas" / (
        "paper1-external-review-response.schema.json"
    )
    try:
        expected_response_schema_sha = hashlib.sha256(
            expected_response_schema_path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        errors.append(f"response schema binding cannot be loaded: {exc}")
        expected_response_schema_sha = None
    expected_return_contract = {
        "response_template_path": "review/paper1/external_solicitation/RESPONSE_TEMPLATE.json",
        "response_schema_path": "schemas/paper1-external-review-response.schema.json",
        "response_schema_sha256": expected_response_schema_sha,
        "response_validator_path": "review/paper1/external_solicitation/validate_response.py",
        "secure_return_channel_supplied_privately": True,
    }
    if return_contract != expected_return_contract:
        errors.append("return contract does not bind the bundled response schema and validator")

    chronology = request.get("chronology", {})
    timestamps = [
        _utc(chronology.get(key), field=f"chronology.{key}", errors=errors)
        for key in (
            "concern_code_assigned_at_utc",
            "request_payload_frozen_at_utc",
            "request_sent_at_utc",
            "private_delivery_receipt_recorded_at_utc",
            "response_due_at_utc",
        )
    ]
    if all(value is not None for value in timestamps):
        assigned, payload_frozen, sent, receipt_recorded, due = timestamps
        if not (assigned <= payload_frozen <= sent <= receipt_recorded < due):
            errors.append(
                "request chronology must satisfy assigned <= payload frozen <= sent "
                "<= receipt recorded < due"
            )

    delivery = request.get("delivery", {})
    if delivery.get("private_contact_details_in_repository") is not False:
        errors.append("public request receipt must not contain private contact details")

    if status == FROZEN_STATUS:
        attestations = request.get("attestations", {})
        false_attestations = [key for key, value in attestations.items() if value is not True]
        if false_attestations:
            errors.append(
                "frozen request requires all request attestations true: "
                + ", ".join(sorted(false_attestations))
            )
        declaration = request.get("declaration", {})
        if declaration.get("solicitation_sent") is not True:
            errors.append("frozen request must declare solicitation_sent=true")
        if any(
            declaration.get(field) is not False
            for field in (
                "response_received",
                "independent_review_completed",
                "peer_review_completed",
                "accepted_or_published",
            )
        ):
            errors.append("a solicitation request cannot declare a response or completed review")

    return errors


def _schema_errors(request: dict[str, Any]) -> Iterable[str]:
    try:
        import jsonschema
    except ImportError:
        yield "jsonschema is required for schema validation; install jsonschema>=4"
        return
    schema = json.loads(Path(__file__).with_name("SCHEMA.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    for error in sorted(validator.iter_errors(request), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        yield f"schema:{location}: {error.message}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an outbound Paper 1 review request without conferring review authority."
    )
    parser.add_argument("request", type=Path)
    parser.add_argument("--allow-template", action="store_true")
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    errors = list(_schema_errors(request))
    errors.extend(validate_request_contract(request, require_frozen=not args.allow_template))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("VALID solicitation request structure; no review or independence authority conferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
