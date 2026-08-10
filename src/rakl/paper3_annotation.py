from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANNOTATION_FIELDS = (
    "semantic_similarity_high",
    "structural_match",
    "roles_preserved",
    "typed_relations_preserved",
    "invariant_preserved",
    "boundary_matched",
    "qoi_matched",
    "directional_mapping_complete",
    "transfer_valid",
)
REQUIRED_V1_BENCHMARK_CANONICAL_SHA256 = "831fa5804efca457f0c9763ec6efd4913c569068aa5ba3ae0b9b4f1f982e9db4"

_PACKET_FIELDS = (
    "family",
    "source_domain",
    "target_domain",
    "source_surface_terms",
    "target_surface_terms",
    "source_skill_tags",
    "target_skill_tags",
    "source_dependencies",
    "target_dependencies",
    "candidate_load_bearing_invariant",
    "candidate_load_bearing_boundary",
    "qoi",
    "source_evidence",
    "target_evidence",
)

_FORBIDDEN_SOURCE_FRAGMENTS = (
    "proposal",
    "quadrant",
    "transfer_valid",
    "structural_match",
    "semantic_similarity_high",
    "annotation",
    "adjudication",
    "prediction",
    "result",
    "gold",
    "label",
    "outcome",
    "decision",
)
_SOURCE_ITEM_FIELDS = {"source_item_id", *_PACKET_FIELDS}
_SOURCE_SET_FIELDS = {
    "schema_version",
    "source_set_id",
    "authority_status",
    "frozen_at_utc",
    "protocol_id",
    "protocol_sha256",
    "rubric_id",
    "rubric_sha256",
    "label_blind_attestation",
    "items",
}
_LABEL_BLIND_ATTESTATION_FIELDS = {
    "curator_id",
    "benchmark_author_ids",
    "no_v1_item_copying",
    "no_outcome_or_diagnostic_access_during_construction",
    "frozen_before_annotation",
}
_RFC3339_UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_PACKET_TOP_LEVEL_FIELDS = {
    "schema_version",
    "packet_id",
    "parent_subject_sha",
    "source_set_id",
    "source_set_sha256",
    "source_set_frozen_at_utc",
    "frozen_at_utc",
    "protocol_id",
    "protocol_sha256",
    "rubric_id",
    "rubric_sha256",
    "negative_history_benchmark_sha256",
    "authority_status",
    "claim_boundary",
    "instructions",
    "items",
}
_LINKAGE_FIELDS = {
    "schema_version",
    "packet_id",
    "packet_sha256",
    "parent_subject_sha",
    "coordinator_only",
    "item_to_source_item",
    "negative_history_benchmark_sha256",
}
_BINDING_FIELDS = {
    "packet_id",
    "packet_sha256",
    "protocol_id",
    "protocol_sha256",
    "rubric_id",
    "rubric_sha256",
}
_SUBMISSION_FIELDS = {
    "schema_version",
    *_BINDING_FIELDS,
    "annotator_id",
    "attestation",
    "items",
}
_ADJUDICATION_FIELDS = {
    "schema_version",
    *_BINDING_FIELDS,
    "adjudicator_id",
    "input_submission_sha256",
    "attestation",
    "items",
}
_PROVENANCE_AUDIT_FIELDS = {
    "schema_version",
    *_BINDING_FIELDS,
    "coordinator_id",
    "auditor_id",
    "verified_source_curator_id",
    "verified_benchmark_author_ids",
    "auditor_is_external_human",
    "auditor_independent_of_benchmark_author",
    "auditor_verified_input_hashes",
    "verified_distinct_human_identities",
    "verified_domain_expertise",
    "verified_independence_from_benchmark_author",
    "verified_access_chronology",
    "verified_person_ids",
    "submission_sha256",
    "adjudication_sha256",
    "audited_at_utc",
}
_SUBMISSION_ATTESTATION_FIELDS = {
    "human_or_domain_expert",
    "independent_of_benchmark_author",
    "no_other_annotator_or_result_access",
    "conflicts_disclosed",
    "completed_at_utc",
}
_ADJUDICATION_ATTESTATION_FIELDS = {
    "human_or_domain_expert",
    "independent_of_benchmark_author",
    "no_result_access_before_resolution",
    "conflicts_disclosed",
    "completed_at_utc",
}
_JUDGEMENT_FIELDS = {
    "item_id",
    *ANNOTATION_FIELDS,
    "cannot_assess",
    "rationale",
    "evidence_refs",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def packet_sha256(packet: dict[str, Any]) -> str:
    return canonical_sha256(packet)


def _valid_hex(value: Any, length: int) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _utc_datetime(value: Any) -> datetime:
    if not isinstance(value, str) or not _RFC3339_UTC_PATTERN.fullmatch(value):
        raise ValueError("timestamp must be RFC3339 UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("timestamp must be valid RFC3339 UTC") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed


def _opaque_item_id(*, subject_sha: str, packet_id: str, source_item_id: str) -> str:
    digest = hashlib.sha256(
        f"{subject_sha}:{packet_id}:{source_item_id}".encode("utf-8")
    ).hexdigest()
    return f"p3item-{digest[:20]}"


def _packet_item_from_source(source_item: dict[str, Any], *, item_id: str) -> dict[str, Any]:
    item = {"item_id": item_id}
    for field in _PACKET_FIELDS:
        if field in source_item:
            item[field] = deepcopy(source_item[field])
    return item


def _validate_label_blind_source_set(source_set: dict[str, Any]) -> None:
    if not isinstance(source_set, dict):
        raise ValueError("source set must be an object")
    unexpected_source_fields = set(source_set) - _SOURCE_SET_FIELDS
    if unexpected_source_fields:
        raise ValueError(
            "source set must use the strict top-level allowlist; unexpected fields: "
            + ", ".join(sorted(unexpected_source_fields))
        )
    if source_set.get("authority_status") != "fresh_label_blind_source_items":
        raise ValueError("source set must be a fresh label-blind v2 item set")
    if source_set.get("schema_version") != "paper3-label-blind-source-set-v2":
        raise ValueError("source set must use paper3-label-blind-source-set-v2")
    if not isinstance(source_set.get("items"), list) or not source_set["items"]:
        raise ValueError("fresh label-blind source set must contain items")
    if not isinstance(source_set.get("source_set_id"), str) or not source_set["source_set_id"]:
        raise ValueError("source_set_id must be a non-empty string")
    _utc_datetime(source_set.get("frozen_at_utc"))
    for field in ("protocol_id", "rubric_id"):
        if not isinstance(source_set.get(field), str) or not source_set[field]:
            raise ValueError(f"{field} must be a non-empty string")
    for field in ("protocol_sha256", "rubric_sha256"):
        if not _valid_hex(source_set.get(field), 64):
            raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    attestation = source_set.get("label_blind_attestation")
    benchmark_author_ids = (
        attestation.get("benchmark_author_ids") if isinstance(attestation, dict) else None
    )
    if not (
        isinstance(attestation, dict)
        and set(attestation) == _LABEL_BLIND_ATTESTATION_FIELDS
        and isinstance(attestation.get("curator_id"), str)
        and attestation["curator_id"]
        and isinstance(benchmark_author_ids, list)
        and bool(benchmark_author_ids)
        and len(set(benchmark_author_ids)) == len(benchmark_author_ids)
        and all(isinstance(value, str) and value for value in benchmark_author_ids)
        and attestation.get("no_v1_item_copying") is True
        and attestation.get("no_outcome_or_diagnostic_access_during_construction") is True
        and attestation.get("frozen_before_annotation") is True
    ):
        raise ValueError("fresh label-blind source set requires a complete curator attestation")
    seen: set[str] = set()
    for item in source_set["items"]:
        if not isinstance(item, dict):
            raise ValueError("source-set items must be objects")
        source_item_id = item.get("source_item_id")
        if not isinstance(source_item_id, str) or not source_item_id or source_item_id in seen:
            raise ValueError("source_item_id values must be unique non-empty strings")
        seen.add(source_item_id)
        unexpected = set(item) - _SOURCE_ITEM_FIELDS
        if unexpected:
            raise ValueError(
                "source set must use the strict label-blind field allowlist; unexpected fields: "
                + ", ".join(sorted(unexpected))
            )
        forbidden = [
            key
            for key in item
            if any(fragment in key.lower() for fragment in _FORBIDDEN_SOURCE_FRAGMENTS)
        ]
        if forbidden:
            raise ValueError(
                "source set must be a fresh label-blind v2 item set; forbidden fields: "
                + ", ".join(sorted(forbidden))
            )
        for field in ("family", "source_domain", "target_domain", "qoi"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"source item {source_item_id} requires non-empty {field}")
        for field in ("source_evidence", "target_evidence"):
            value = item.get(field)
            if not (
                isinstance(value, list)
                and value
                and all(isinstance(ref, str) and ref.strip() for ref in value)
            ):
                raise ValueError(f"source item {source_item_id} requires non-empty {field}")


def _source_fingerprint(item: dict[str, Any]) -> str:
    normalized = {
        "family": item.get("family"),
        "source_domain": item.get("source_domain"),
        "target_domain": item.get("target_domain"),
        "source_surface_terms": item.get("source_surface_terms"),
        "target_surface_terms": item.get("target_surface_terms"),
        "source_skill_tags": item.get("source_skill_tags"),
        "target_skill_tags": item.get("target_skill_tags"),
        "source_dependencies": item.get("source_dependencies"),
        "target_dependencies": item.get("target_dependencies"),
        "candidate_load_bearing_invariant": item.get(
            "candidate_load_bearing_invariant",
            item.get("load_bearing_invariant_proposal"),
        ),
        "candidate_load_bearing_boundary": item.get(
            "candidate_load_bearing_boundary",
            item.get("load_bearing_boundary_proposal"),
        ),
        "qoi": item.get("qoi"),
    }
    return canonical_sha256(normalized)


def build_annotation_packet(
    source_set: dict[str, Any],
    *,
    packet_id: str,
    subject_sha: str,
    frozen_at_utc: str,
    negative_history_benchmarks: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    _validate_label_blind_source_set(source_set)
    if not _valid_hex(subject_sha, 40):
        raise ValueError("subject_sha must be a lowercase 40-character hexadecimal Git SHA")
    if not packet_id:
        raise ValueError("packet_id is required")
    packet_frozen = _utc_datetime(frozen_at_utc)
    source_frozen = _utc_datetime(source_set["frozen_at_utc"])
    if packet_frozen <= source_frozen:
        raise ValueError("packet must be frozen after the source-item set")
    if not negative_history_benchmarks:
        raise ValueError("at least one negative-history benchmark is required")
    negative_hashes = sorted(canonical_sha256(value) for value in negative_history_benchmarks)
    if REQUIRED_V1_BENCHMARK_CANONICAL_SHA256 not in negative_hashes:
        raise ValueError("exact frozen v1 negative-history benchmark is required")
    negative_fingerprints = {
        _source_fingerprint(case)
        for benchmark in negative_history_benchmarks
        for case in benchmark.get("cases", [])
    }
    overlap = [
        item["source_item_id"]
        for item in source_set["items"]
        if _source_fingerprint(item) in negative_fingerprints
    ]
    if overlap:
        raise ValueError(
            "fresh source set overlaps negative-history benchmark: " + ", ".join(overlap)
        )

    items: list[dict[str, Any]] = []
    item_to_source_item: dict[str, str] = {}
    for source_item in source_set["items"]:
        item_id = _opaque_item_id(
            subject_sha=subject_sha,
            packet_id=packet_id,
            source_item_id=source_item["source_item_id"],
        )
        item = _packet_item_from_source(source_item, item_id=item_id)
        items.append(item)
        item_to_source_item[item_id] = source_item["source_item_id"]

    packet = {
        "schema_version": "paper3-external-annotation-packet-v2",
        "packet_id": packet_id,
        "parent_subject_sha": subject_sha,
        "source_set_id": source_set["source_set_id"],
        "source_set_sha256": canonical_sha256(source_set),
        "source_set_frozen_at_utc": source_set["frozen_at_utc"],
        "frozen_at_utc": frozen_at_utc,
        "protocol_id": source_set["protocol_id"],
        "protocol_sha256": source_set["protocol_sha256"],
        "rubric_id": source_set["rubric_id"],
        "rubric_sha256": source_set["rubric_sha256"],
        "negative_history_benchmark_sha256": negative_hashes,
        "authority_status": "awaiting_genuinely_independent_annotation",
        "claim_boundary": (
            "Fresh label-blind source items only; this packet is not annotation evidence "
            "and does not authorize training or inference."
        ),
        "instructions": {
            "required_independent_submissions_per_item": 2,
            "distinct_adjudicator_required": True,
            "external_provenance_audit_required": True,
            "direct_identifiers_prohibited": True,
            "judgement_fields": list(ANNOTATION_FIELDS),
            "cannot_assess_fails_confirmatory_eligibility": True,
        },
        "items": items,
    }
    linkage = {
        "schema_version": "paper3-annotation-linkage-v2",
        "packet_id": packet_id,
        "packet_sha256": packet_sha256(packet),
        "parent_subject_sha": subject_sha,
        "coordinator_only": True,
        "item_to_source_item": item_to_source_item,
        "negative_history_benchmark_sha256": negative_hashes,
    }
    return packet, linkage


def _binding_failures(evidence: dict[str, Any], packet: dict[str, Any], role: str) -> list[str]:
    failures = []
    for field in ("packet_id", "protocol_id", "protocol_sha256", "rubric_id", "rubric_sha256"):
        if evidence.get(field) != packet.get(field):
            failures.append(f"{role}_{field}_mismatch")
    if evidence.get("packet_sha256") != packet_sha256(packet):
        failures.append(f"{role}_packet_sha256_mismatch")
    return failures


def _valid_submission_attestation(evidence: dict[str, Any]) -> bool:
    attestation = evidence.get("attestation")
    return bool(
        isinstance(attestation, dict)
        and set(attestation) == _SUBMISSION_ATTESTATION_FIELDS
        and attestation.get("human_or_domain_expert") is True
        and attestation.get("independent_of_benchmark_author") is True
        and attestation.get("no_other_annotator_or_result_access") is True
        and attestation.get("conflicts_disclosed") is True
        and _timestamp_valid(attestation.get("completed_at_utc"))
    )


def _valid_adjudication_attestation(evidence: dict[str, Any]) -> bool:
    attestation = evidence.get("attestation")
    return bool(
        isinstance(attestation, dict)
        and set(attestation) == _ADJUDICATION_ATTESTATION_FIELDS
        and attestation.get("human_or_domain_expert") is True
        and attestation.get("independent_of_benchmark_author") is True
        and attestation.get("no_result_access_before_resolution") is True
        and attestation.get("conflicts_disclosed") is True
        and _timestamp_valid(attestation.get("completed_at_utc"))
    )


def _timestamp_valid(value: Any) -> bool:
    try:
        _utc_datetime(value)
    except ValueError:
        return False
    return True


def _validate_items(
    *, evidence: dict[str, Any], expected_item_ids: set[str], identity: str, adjudication: bool
) -> list[str]:
    failures: list[str] = []
    items = evidence.get("items")
    if not isinstance(items, list):
        return [f"items_not_array:{identity}"]
    received_ids = {
        row.get("item_id") for row in items if isinstance(row, dict) and row.get("item_id")
    }
    if received_ids != expected_item_ids or len(items) != len(expected_item_ids):
        failures.append(
            "adjudication_item_coverage_mismatch"
            if adjudication
            else f"submission_item_coverage_mismatch:{identity}"
        )
    for row in items:
        if not isinstance(row, dict) or row.get("item_id") not in expected_item_ids:
            continue
        allowed_fields = _JUDGEMENT_FIELDS | ({"resolution_rationale"} if adjudication else set())
        unexpected = set(row) - allowed_fields
        if unexpected:
            failures.append(f"unexpected_judgement_fields:{identity}:{row.get('item_id')}")
        if any(type(row.get(field)) is not bool for field in ANNOTATION_FIELDS):
            failures.append(f"non_boolean_judgement:{identity}:{row.get('item_id')}")
        if row.get("cannot_assess") is not False:
            failures.append(f"cannot_assess:{identity}:{row.get('item_id')}")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            failures.append(f"missing_rationale:{identity}:{row.get('item_id')}")
        if not isinstance(row.get("evidence_refs"), list) or not row["evidence_refs"]:
            failures.append(f"missing_evidence_refs:{identity}:{row.get('item_id')}")
        if adjudication and (
            not isinstance(row.get("resolution_rationale"), str)
            or not row["resolution_rationale"].strip()
        ):
            failures.append(f"missing_resolution_rationale:{row.get('item_id')}")
    return failures


def _quadrant(row: dict[str, Any]) -> str:
    semantic = row["semantic_similarity_high"]
    structural = row["structural_match"]
    return {
        (True, True): "Q1",
        (False, True): "Q2",
        (True, False): "Q3",
        (False, False): "Q4",
    }[(semantic, structural)]


def compile_adjudicated_benchmark(
    *,
    source_set: dict[str, Any],
    subject_sha: str,
    packet: dict[str, Any],
    linkage: dict[str, Any],
    submissions: list[dict[str, Any]],
    adjudication: dict[str, Any],
    provenance_audit: dict[str, Any],
    negative_history_benchmarks: list[dict[str, Any]],
    observed_protocol_id: str,
    observed_protocol_sha256: str,
    observed_rubric_id: str,
    observed_rubric_sha256: str,
    minimum_independent_annotators: int = 2,
) -> dict[str, Any]:
    failures: list[str] = []
    source_frozen_at: datetime | None = None
    packet_source_frozen_at: datetime | None = None
    packet_frozen_at: datetime | None = None
    if not _valid_hex(subject_sha, 40):
        failures.append("subject_sha_invalid")
    try:
        _validate_label_blind_source_set(source_set)
        source_frozen_at = _utc_datetime(source_set["frozen_at_utc"])
    except ValueError as error:
        failures.append(f"source_set_invalid:{error}")
    if packet.get("schema_version") != "paper3-external-annotation-packet-v2":
        failures.append("packet_schema_mismatch")
    if set(packet) != _PACKET_TOP_LEVEL_FIELDS:
        failures.append("packet_fields_mismatch")
    if set(linkage) != _LINKAGE_FIELDS or linkage.get("schema_version") != "paper3-annotation-linkage-v2":
        failures.append("linkage_fields_or_schema_mismatch")
    packet_items = packet.get("items")
    if not isinstance(packet_items, list) or any(
        not isinstance(item, dict)
        or set(item) - ({"item_id"} | set(_PACKET_FIELDS))
        for item in packet_items
    ):
        failures.append("packet_item_fields_mismatch")
    try:
        packet_source_frozen_at = _utc_datetime(packet.get("source_set_frozen_at_utc"))
        packet_frozen_at = _utc_datetime(packet.get("frozen_at_utc"))
    except ValueError:
        failures.append("packet_timestamp_invalid")
    if (
        source_frozen_at is not None
        and packet_source_frozen_at is not None
        and packet_source_frozen_at != source_frozen_at
    ):
        failures.append("packet_source_freeze_binding_mismatch")
    if (
        source_frozen_at is not None
        and packet_frozen_at is not None
        and packet_frozen_at <= source_frozen_at
    ):
        failures.append("packet_does_not_follow_source_freeze")
    expected_hash = packet_sha256(packet)
    expected_item_ids = set(linkage.get("item_to_source_item", {}))
    if linkage.get("packet_id") != packet.get("packet_id") or linkage.get("packet_sha256") != expected_hash:
        failures.append("packet_linkage_binding_mismatch")
    if packet.get("parent_subject_sha") != subject_sha or linkage.get("parent_subject_sha") != subject_sha:
        failures.append("subject_packet_linkage_mismatch")
    if {item.get("item_id") for item in packet.get("items", [])} != expected_item_ids:
        failures.append("packet_item_linkage_mismatch")
    if _valid_hex(subject_sha, 40) and isinstance(packet.get("packet_id"), str):
        expected_mapping: dict[str, str] = {}
        expected_packet_items: dict[str, dict[str, Any]] = {}
        for source_item in source_set.get("items", []):
            if not isinstance(source_item, dict) or not isinstance(
                source_item.get("source_item_id"), str
            ):
                continue
            item_id = _opaque_item_id(
                subject_sha=subject_sha,
                packet_id=packet["packet_id"],
                source_item_id=source_item["source_item_id"],
            )
            expected_mapping[item_id] = source_item["source_item_id"]
            expected_packet_items[item_id] = _packet_item_from_source(
                source_item, item_id=item_id
            )
        if linkage.get("item_to_source_item") != expected_mapping:
            failures.append("opaque_linkage_mapping_mismatch")
        observed_packet_items = {
            item.get("item_id"): item
            for item in packet.get("items", [])
            if isinstance(item, dict) and isinstance(item.get("item_id"), str)
        }
        if (
            len(observed_packet_items) != len(packet.get("items", []))
            or observed_packet_items != expected_packet_items
        ):
            failures.append("packet_payload_source_binding_mismatch")
    if packet.get("source_set_sha256") != canonical_sha256(source_set):
        failures.append("source_set_packet_hash_mismatch")
    negative_hashes = sorted(canonical_sha256(value) for value in negative_history_benchmarks)
    if REQUIRED_V1_BENCHMARK_CANONICAL_SHA256 not in negative_hashes:
        failures.append("required_v1_negative_history_missing")
    if packet.get("negative_history_benchmark_sha256") != negative_hashes or linkage.get("negative_history_benchmark_sha256") != negative_hashes:
        failures.append("negative_history_hash_binding_mismatch")
    negative_fingerprints = {
        _source_fingerprint(case)
        for benchmark in negative_history_benchmarks
        for case in benchmark.get("cases", [])
    }
    if any(_source_fingerprint(item) in negative_fingerprints for item in source_set.get("items", [])):
        failures.append("source_item_overlaps_negative_history")
    expected_artifact_bindings = {
        "protocol_id": observed_protocol_id,
        "protocol_sha256": observed_protocol_sha256,
        "rubric_id": observed_rubric_id,
        "rubric_sha256": observed_rubric_sha256,
    }
    for field, observed in expected_artifact_bindings.items():
        if source_set.get(field) != observed or packet.get(field) != observed:
            failures.append(f"frozen_artifact_binding_mismatch:{field}")

    eligible_submissions: list[dict[str, Any]] = []
    annotator_ids: list[str] = []
    submission_times: list[str] = []
    for submission in submissions:
        annotator_id = submission.get("annotator_id")
        identity = annotator_id if isinstance(annotator_id, str) and annotator_id else "missing"
        local_failures: list[str] = []
        if submission.get("schema_version") != "paper3-external-annotation-submission-v2":
            local_failures.append(f"submission_schema_mismatch:{identity}")
        if set(submission) != _SUBMISSION_FIELDS:
            local_failures.append(f"submission_fields_mismatch:{identity}")
        local_failures.extend(_binding_failures(submission, packet, f"submission:{identity}"))
        if not _valid_submission_attestation(submission):
            local_failures.append(f"submission_attestation_invalid:{identity}")
        else:
            completed = submission["attestation"]["completed_at_utc"]
            submission_times.append(completed)
            if packet_frozen_at is None or _utc_datetime(completed) <= packet_frozen_at:
                local_failures.append(f"submission_precedes_packet_freeze:{identity}")
        local_failures.extend(
            _validate_items(
                evidence=submission,
                expected_item_ids=expected_item_ids,
                identity=identity,
                adjudication=False,
            )
        )
        failures.extend(local_failures)
        if identity != "missing" and not local_failures:
            eligible_submissions.append(submission)
            annotator_ids.append(identity)
    if len(set(annotator_ids)) < minimum_independent_annotators:
        failures.append("distinct_eligible_annotators_below_minimum")

    adjudicator_id = adjudication.get("adjudicator_id")
    adjudicator_identity = adjudicator_id if isinstance(adjudicator_id, str) and adjudicator_id else "missing"
    if adjudication.get("schema_version") != "paper3-external-adjudication-v2":
        failures.append("adjudication_schema_mismatch")
    if set(adjudication) != _ADJUDICATION_FIELDS:
        failures.append("adjudication_fields_mismatch")
    failures.extend(_binding_failures(adjudication, packet, "adjudication"))
    if not _valid_adjudication_attestation(adjudication):
        failures.append("adjudication_attestation_invalid")
    else:
        adjudication_time = adjudication["attestation"]["completed_at_utc"]
        if submission_times and _utc_datetime(adjudication_time) <= max(_utc_datetime(value) for value in submission_times):
            failures.append("adjudication_precedes_submission_freeze")
    failures.extend(
        _validate_items(
            evidence=adjudication,
            expected_item_ids=expected_item_ids,
            identity=adjudicator_identity,
            adjudication=True,
        )
    )
    if adjudicator_identity == "missing" or adjudicator_identity in set(annotator_ids):
        failures.append("adjudicator_not_distinct")
    expected_submission_hashes = sorted(canonical_sha256(item) for item in submissions)
    if sorted(adjudication.get("input_submission_sha256", [])) != expected_submission_hashes:
        failures.append("adjudication_submission_hash_mismatch")

    adjudication_people = set(annotator_ids) | {adjudicator_identity}
    if provenance_audit.get("schema_version") != "paper3-external-provenance-audit-v2":
        failures.append("provenance_audit_schema_mismatch")
    if set(provenance_audit) != _PROVENANCE_AUDIT_FIELDS:
        failures.append("provenance_audit_fields_mismatch")
    failures.extend(_binding_failures(provenance_audit, packet, "provenance_audit"))
    coordinator_id = provenance_audit.get("coordinator_id")
    if (
        not isinstance(coordinator_id, str)
        or not coordinator_id
        or coordinator_id in adjudication_people
    ):
        failures.append("provenance_coordinator_not_distinct")
    auditor_id = provenance_audit.get("auditor_id")
    if (
        not isinstance(auditor_id, str)
        or not auditor_id
        or auditor_id in adjudication_people
        or auditor_id == coordinator_id
    ):
        failures.append("provenance_auditor_not_distinct")
    operational_people = adjudication_people | {
        identity
        for identity in (coordinator_id, auditor_id)
        if isinstance(identity, str) and identity
    }
    source_attestation = source_set.get("label_blind_attestation", {})
    curator_id = source_attestation.get("curator_id")
    benchmark_author_ids = source_attestation.get("benchmark_author_ids", [])
    if (
        provenance_audit.get("verified_source_curator_id") != curator_id
        or provenance_audit.get("verified_benchmark_author_ids")
        != benchmark_author_ids
    ):
        failures.append("provenance_source_identity_binding_mismatch")
    protected_source_people = {
        identity
        for identity in [curator_id, *benchmark_author_ids]
        if isinstance(identity, str) and identity
    }
    overlapping_roles = sorted(protected_source_people & operational_people)
    if overlapping_roles:
        failures.append(
            "source_governance_role_independence_violated:"
            + ",".join(overlapping_roles)
        )
    for field in (
        "auditor_is_external_human",
        "auditor_independent_of_benchmark_author",
        "auditor_verified_input_hashes",
        "verified_distinct_human_identities",
        "verified_domain_expertise",
        "verified_independence_from_benchmark_author",
        "verified_access_chronology",
    ):
        if provenance_audit.get(field) is not True:
            failures.append(f"provenance_not_verified:{field}")
    if set(provenance_audit.get("verified_person_ids", [])) != operational_people:
        failures.append("provenance_person_coverage_mismatch")
    if sorted(provenance_audit.get("submission_sha256", [])) != expected_submission_hashes:
        failures.append("provenance_submission_hash_mismatch")
    if provenance_audit.get("adjudication_sha256") != canonical_sha256(adjudication):
        failures.append("provenance_adjudication_hash_mismatch")
    audited_at = provenance_audit.get("audited_at_utc")
    if not _timestamp_valid(audited_at):
        failures.append("provenance_audit_timestamp_invalid")
    elif _valid_adjudication_attestation(adjudication) and _utc_datetime(audited_at) <= _utc_datetime(adjudication["attestation"]["completed_at_utc"]):
        failures.append("provenance_audit_precedes_adjudication")

    receipt_base = {
        "schema_version": "paper3-annotation-import-receipt-v2",
        "subject_sha": subject_sha,
        "protocol_id": packet.get("protocol_id"),
        "protocol_sha256": observed_protocol_sha256,
        "source_set_sha256": canonical_sha256(source_set),
        "packet_sha256": expected_hash,
        "submission_sha256": sorted(canonical_sha256(item) for item in submissions),
        "adjudication_sha256": canonical_sha256(adjudication),
        "provenance_audit_sha256": canonical_sha256(provenance_audit),
        "negative_history_benchmark_sha256": negative_hashes,
        "training_authorized": False,
    }

    failures = list(dict.fromkeys(failures))
    if failures:
        import_receipt = {
            **receipt_base,
            "passed": False,
            "failures": failures,
            "coordinate_exact_agreement": {},
            "coordinate_conflict_count": {},
            "benchmark_sha256": None,
        }
        return {
            "passed": False,
            "failures": failures,
            "packet_id": packet.get("packet_id"),
            "packet_sha256": expected_hash,
            "eligible_distinct_annotator_count": len(set(annotator_ids)),
            "benchmark": None,
            "import_receipt": import_receipt,
        }

    adjudicated_by_item = {row["item_id"]: row for row in adjudication["items"]}
    case_by_source_id = {item["source_item_id"]: item for item in source_set["items"]}
    submission_rows = {
        item_id: [next(row for row in submission["items"] if row["item_id"] == item_id) for submission in eligible_submissions]
        for item_id in expected_item_ids
    }
    compiled_cases = []
    for item_id, source_item_id in linkage["item_to_source_item"].items():
        case = deepcopy(case_by_source_id[source_item_id])
        case["case_id"] = case.pop("source_item_id")
        resolved = adjudicated_by_item[item_id]
        for field in ANNOTATION_FIELDS:
            case[field] = resolved[field]
        case["quadrant"] = _quadrant(resolved)
        case["annotation_records"] = [
            {
                "annotation_id": f"{item_id}:{submission['annotator_id']}",
                "annotator_id": submission["annotator_id"],
                "annotator_type": "externally_provenanced_human_or_domain_expert",
                "human_or_expert": True,
                "independent_of_benchmark_author": True,
                "status": "final",
                "judgements": {field: row[field] for field in ANNOTATION_FIELDS},
                "rationale": row["rationale"],
                "evidence_refs": row["evidence_refs"],
                "completed_at_utc": submission["attestation"]["completed_at_utc"],
            }
            for submission, row in zip(eligible_submissions, submission_rows[item_id], strict=True)
        ]
        case["adjudication"] = {
            "adjudicator_id": adjudicator_identity,
            "human_or_expert": True,
            "independent_of_benchmark_author": True,
            "status": "final",
            "judgements": {field: resolved[field] for field in ANNOTATION_FIELDS},
            "resolution_rationale": resolved["resolution_rationale"],
            "evidence_refs": resolved["evidence_refs"],
            "completed_at_utc": adjudication["attestation"]["completed_at_utc"],
        }
        case["confirmatory_eligible"] = True
        compiled_cases.append(case)

    agreement = {
        field: sum(
            len({row[field] for row in rows}) == 1 for rows in submission_rows.values()
        )
        / len(submission_rows)
        for field in ANNOTATION_FIELDS
    }
    conflicts = {
        field: sum(len({row[field] for row in rows}) > 1 for rows in submission_rows.values())
        for field in ANNOTATION_FIELDS
    }
    benchmark = {
        "schema_version": "paper3-confirmatory-benchmark-v2",
        "benchmark_id": f"{source_set['source_set_id']}:adjudicated:{packet['packet_id']}",
        "authority_status": "independently_annotated_and_adjudicated_v2",
        "subject_sha": subject_sha,
        "source_set_id": source_set["source_set_id"],
        "source_set_sha256": canonical_sha256(source_set),
        "source_set_frozen_at_utc": source_set["frozen_at_utc"],
        "packet_id": packet["packet_id"],
        "packet_sha256": expected_hash,
        "packet_frozen_at_utc": packet["frozen_at_utc"],
        "protocol_id": packet["protocol_id"],
        "protocol_sha256": packet["protocol_sha256"],
        "rubric_id": packet["rubric_id"],
        "rubric_sha256": packet["rubric_sha256"],
        "provenance_audit_sha256": canonical_sha256(provenance_audit),
        "negative_history_benchmark_sha256": negative_hashes,
        "annotation_completed_at_utc": sorted(submission_times),
        "adjudication_completed_at_utc": adjudication["attestation"]["completed_at_utc"],
        "coordinate_exact_agreement": agreement,
        "coordinate_conflict_count": conflicts,
        "cases": compiled_cases,
    }
    import_receipt = {
        **receipt_base,
        "passed": True,
        "failures": [],
        "coordinate_exact_agreement": agreement,
        "coordinate_conflict_count": conflicts,
        "benchmark_sha256": canonical_sha256(benchmark),
    }
    return {
        "passed": True,
        "failures": [],
        "packet_id": packet["packet_id"],
        "packet_sha256": expected_hash,
        "eligible_distinct_annotator_count": len(set(annotator_ids)),
        "benchmark": benchmark,
        "import_receipt": import_receipt,
    }


def evaluate_annotation_gate_v2(
    benchmark: dict[str, Any],
    protocol: dict[str, Any],
    import_receipt: dict[str, Any],
) -> dict[str, Any]:
    chronology = protocol.get("chronology", {})
    requirement = protocol.get("annotation_gate", {})
    failures: list[str] = []
    if chronology.get("fresh_label_blind_item_set_required") is not True:
        failures.append("protocol_does_not_require_fresh_label_blind_items")
    if chronology.get("confirmatory_use_permitted_after_gate") is not True:
        failures.append("protocol_forbids_confirmatory_use")
    if benchmark.get("protocol_id") != protocol.get("protocol_id"):
        failures.append("protocol_id_mismatch")
    protocol_hash = canonical_sha256(protocol)
    if benchmark.get("protocol_sha256") != protocol_hash:
        failures.append("benchmark_protocol_hash_mismatch")
    if import_receipt.get("schema_version") != "paper3-annotation-import-receipt-v2":
        failures.append("import_receipt_schema_mismatch")
    if import_receipt.get("passed") is not True:
        failures.append("annotation_import_not_passed")
    if import_receipt.get("training_authorized") is not False:
        failures.append("annotation_import_receipt_overclaims_authorization")
    if import_receipt.get("benchmark_sha256") != canonical_sha256(benchmark):
        failures.append("annotation_import_benchmark_hash_mismatch")
    if import_receipt.get("protocol_id") != protocol.get("protocol_id"):
        failures.append("annotation_import_protocol_mismatch")
    if import_receipt.get("protocol_sha256") != protocol_hash:
        failures.append("annotation_import_protocol_hash_mismatch")
    if benchmark.get("subject_sha") != import_receipt.get("subject_sha"):
        failures.append("annotation_import_subject_mismatch")
    benchmark_negative = benchmark.get("negative_history_benchmark_sha256", [])
    import_negative = import_receipt.get("negative_history_benchmark_sha256", [])
    if (
        REQUIRED_V1_BENCHMARK_CANONICAL_SHA256 not in benchmark_negative
        or benchmark_negative != import_negative
    ):
        failures.append("required_negative_history_binding_missing")
    minimum = requirement.get("minimum_independent_human_or_expert_annotations_per_confirmatory_item", 2)
    ineligible = []
    for case in benchmark.get("cases", []):
        records = [
            row
            for row in case.get("annotation_records", [])
            if row.get("human_or_expert") is True
            and row.get("independent_of_benchmark_author") is True
            and row.get("status") == "final"
            and isinstance(row.get("annotator_id"), str)
        ]
        ids = {row["annotator_id"] for row in records}
        adjudication = case.get("adjudication", {})
        valid = bool(
            case.get("confirmatory_eligible") is True
            and len(ids) >= minimum
            and all(type(case.get(field)) is bool for field in ANNOTATION_FIELDS)
            and adjudication.get("human_or_expert") is True
            and adjudication.get("independent_of_benchmark_author") is True
            and adjudication.get("status") == "final"
            and adjudication.get("adjudicator_id") not in ids
        )
        if not valid:
            ineligible.append(case.get("case_id", "missing"))
    if not benchmark.get("cases"):
        failures.append("benchmark_has_no_cases")
    if ineligible:
        failures.append("items_not_confirmatory_eligible")
    return {
        "passed": not failures,
        "failures": failures,
        "confirmatory_item_count": len(benchmark.get("cases", [])) - len(ineligible),
        "missing_or_ineligible_case_ids": ineligible,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-set", type=Path, required=True)
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--frozen-at-utc", required=True)
    parser.add_argument("--negative-history-benchmark", type=Path, action="append", required=True)
    parser.add_argument("--packet-output", type=Path, required=True)
    parser.add_argument("--linkage-output", type=Path, required=True)
    args = parser.parse_args()
    source_set = json.loads(args.source_set.read_text(encoding="utf-8"))
    packet, linkage = build_annotation_packet(
        source_set,
        packet_id=args.packet_id,
        subject_sha=args.subject_sha,
        frozen_at_utc=args.frozen_at_utc,
        negative_history_benchmarks=[
            json.loads(path.read_text(encoding="utf-8"))
            for path in args.negative_history_benchmark
        ],
    )
    for path, value in ((args.packet_output, packet), (args.linkage_output, linkage)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.packet_output)
    print(args.linkage_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
