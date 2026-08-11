#!/usr/bin/env python3
"""Relational checks for a Paper 1 external-review solicitation response.

Schema validation is necessary but cannot enforce timestamp ordering, cross-field
identity, or concern-set integrity. This module adds those fail-closed checks. It does
not decide whether a reviewer is genuinely independent; that requires a separate
coordinator provenance audit.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


LENS_TOKEN = {
    "formal_methods": "FORMAL",
    "novelty_prior_art": "NOVELTY",
    "editorial_significance": "EDITORIAL",
}
FROZEN_STATUS = "frozen-external-reviewer-response"
TEMPLATE_STATUS = "template-example-not-submitted"
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


def validate_response_contract(
    response: dict[str, Any],
    *,
    require_frozen: bool = True,
    manifest_path: str | Path | None = None,
) -> list[str]:
    """Return relational validation failures without conferring review authority."""

    errors: list[str] = []
    status = response.get("response_status")
    if require_frozen and status != FROZEN_STATUS:
        errors.append("response_status must be frozen-external-reviewer-response for ingestion")
    if status == FROZEN_STATUS and _contains_template_placeholder(response):
        errors.append("frozen response contains a zero hash or EXAMPLE ONLY template placeholder")
    if status == TEMPLATE_STATUS and not require_frozen:
        return errors

    packet_manifest_path = (
        Path(manifest_path)
        if manifest_path is not None
        else Path(__file__).with_name("PACKET_MANIFEST.json")
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
        if response.get("packet_manifest_sha256") != expected_manifest_sha:
            errors.append("packet manifest binding hash does not match bundled PACKET_MANIFEST.json")
    if response.get("packet_id") != manifest.get("packet_id"):
        errors.append("packet_id binding does not match bundled PACKET_MANIFEST.json")

    subject = manifest.get("subject", {})
    expected_artifact_binding = {
        "manuscript_subject_sha": subject.get("git_sha"),
        "modular_source_sha256": subject.get("source", {}).get("sha256"),
        "builder_sha256": subject.get("builder", {}).get("sha256"),
        "staged_source_sha256": subject.get("staged_source", {}).get("sha256"),
        "pdf_sha256": subject.get("pdf", {}).get("sha256"),
        "pdf_pages": subject.get("pdf", {}).get("pages"),
    }
    if response.get("artifact_binding") != expected_artifact_binding:
        errors.append("artifact binding does not exactly match the bundled packet subject")

    lens = response.get("review_lens")
    tracks = {
        track.get("lens"): track
        for track in manifest.get("requested_review_tracks", [])
        if isinstance(track, dict)
    }
    expected_role = tracks.get(lens, {}).get("reviewer_role")
    reviewer_for_binding = response.get("reviewer", {})
    if not expected_role or reviewer_for_binding.get("role") != expected_role:
        errors.append("review lens-to-role binding does not match packet manifest")

    chronology = response.get("chronology", {})
    accessed = _utc(
        chronology.get("artifact_accessed_at_utc"),
        field="chronology.artifact_accessed_at_utc",
        errors=errors,
    )
    frozen = _utc(
        chronology.get("response_frozen_at_utc"),
        field="chronology.response_frozen_at_utc",
        errors=errors,
    )
    signed = _utc(
        chronology.get("attestation_signed_at_utc"),
        field="chronology.attestation_signed_at_utc",
        errors=errors,
    )
    if accessed and frozen and signed and not (accessed <= frozen <= signed):
        errors.append("review chronology must satisfy accessed <= frozen <= signed")

    for field, label in (
        ("author_response_first_accessed_at_utc", "author response access"),
        ("other_reviewer_response_first_accessed_at_utc", "other reviewer response access"),
    ):
        value = chronology.get(field)
        if value is None:
            continue
        observed = _utc(value, field=f"chronology.{field}", errors=errors)
        if observed and frozen and observed < frozen:
            errors.append(f"{label} must be null or occur after the response freeze")

    reviewer = response.get("reviewer", {})
    eligible = reviewer.get("reviewer_asserts_independence_eligibility")
    if eligible is True:
        if reviewer.get("independent_of_authors_and_project") is not True:
            errors.append("reviewer independence eligibility contradicts non-independence attestation")
        if reviewer.get("conflicts"):
            errors.append("reviewer independence eligibility contradicts disclosed conflicts")

    code = reviewer.get("concern_code")
    round_number = response.get("review_round")
    if not isinstance(code, str) or not re.fullmatch(r"[A-Z0-9]{4}", code):
        errors.append("reviewer.concern_code must contain four uppercase letters/digits")
    elif reviewer.get("pseudonymous_id") != f"P1-REVIEWER-{code}":
        errors.append("reviewer pseudonymous_id binding must equal P1-REVIEWER-{concern_code}")
    if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
        errors.append("review_round must be a positive integer")
    if isinstance(code, str) and isinstance(round_number, int):
        expected_response_id = f"P1-EXT-RESP-{code}-R{round_number:02d}"
        if response.get("response_id") != expected_response_id:
            errors.append(f"response_id must equal {expected_response_id}")

    lens_token = LENS_TOKEN.get(lens)
    concerns = response.get("concerns", [])
    ids: list[str] = []
    if not isinstance(concerns, list):
        errors.append("concerns must be a list")
        concerns = []
    for concern in concerns:
        if not isinstance(concern, dict):
            errors.append("each concern must be an object")
            continue
        concern_id = concern.get("concern_id")
        if isinstance(concern_id, str):
            ids.append(concern_id)
            if lens_token and isinstance(code, str) and isinstance(round_number, int):
                pattern = rf"^P1-EXT-({lens_token}|ARTIFACT)-{re.escape(code)}-R{round_number:02d}-[0-9]{{3}}$"
                if not re.fullmatch(pattern, concern_id):
                    errors.append(
                        f"concern_id {concern_id!r} does not match lens, reviewer code, and round"
                    )
        else:
            errors.append("every concern requires a string concern_id")
    if len(ids) != len(set(ids)):
        errors.append("concern_id values must be unique within a response")

    open_blocking = {
        concern.get("concern_id")
        for concern in concerns
        if isinstance(concern, dict)
        and concern.get("severity") == "blocking"
        and concern.get("status") == "open"
        and isinstance(concern.get("concern_id"), str)
    }
    declared = response.get("overall_assessment", {}).get("blocking_concern_ids", [])
    if not isinstance(declared, list):
        errors.append("overall_assessment.blocking_concern_ids must be a list")
    elif set(declared) != open_blocking or len(declared) != len(set(declared)):
        errors.append(
            "blocking_concern_ids must equal the unique set of open concerns with blocking severity"
        )

    if status == FROZEN_STATUS:
        declaration = response.get("declaration", {})
        attestations = response.get("attestations", {})
        if declaration.get("external_reviewer_response") is not True:
            errors.append("frozen response must declare external_reviewer_response=true")
        if declaration.get("information_accurate_to_best_of_knowledge") is not True:
            errors.append("frozen response must attest information accuracy")
        false_attestations = [key for key, value in attestations.items() if value is not True]
        if false_attestations:
            errors.append(
                "frozen response requires all response attestations true: "
                + ", ".join(sorted(false_attestations))
            )

    return errors


def _schema_errors(response: dict[str, Any]) -> Iterable[str]:
    try:
        import jsonschema
    except ImportError:
        yield "jsonschema is required for schema validation; install jsonschema>=4"
        return
    schema = json.loads(Path(__file__).with_name("SCHEMA.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    for error in sorted(validator.iter_errors(response), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        yield f"schema:{location}: {error.message}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Paper 1 solicitation response without conferring review authority."
    )
    parser.add_argument("response", type=Path)
    parser.add_argument("--allow-template", action="store_true")
    args = parser.parse_args()
    response = json.loads(args.response.read_text(encoding="utf-8"))
    errors = list(_schema_errors(response))
    errors.extend(
        validate_response_contract(response, require_frozen=not args.allow_template)
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("VALID solicitation response structure; independence authority remains unaudited")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
