"""AI_OPERATOR / NON_INDEPENDENT Paper3 annotation path.

Honest demoted authority: unlocks operator-override compute after complete
role-separated AI/operator annotations, but never mints independent external
human review or Constitution-grade confirmatory peer review.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .paper3_annotation import (
    ANNOTATION_AUTHORITY_DEMOTED_AI,
    ANNOTATION_FIELDS,
    ANNOTATOR_KIND_AI_OPERATOR,
    AUTHORITY_AI_OPERATOR_NON_INDEPENDENT_V2,
    INDEPENDENCE_NON_INDEPENDENT,
    REQUIRED_V1_BENCHMARK_CANONICAL_SHA256,
    SCHEMA_ADJUDICATION_AI_OPERATOR_V2,
    SCHEMA_PROVENANCE_AI_OPERATOR_V2,
    SCHEMA_SUBMISSION_AI_OPERATOR_V2,
    _ADJUDICATION_AI_OPERATOR_ATTESTATION_FIELDS,
    _ADJUDICATION_FIELDS,
    _JUDGEMENT_FIELDS,
    _LINKAGE_FIELDS,
    _PACKET_FIELDS,
    _PACKET_TOP_LEVEL_FIELDS,
    _PROVENANCE_AI_OPERATOR_FIELDS,
    _SUBMISSION_AI_OPERATOR_ATTESTATION_FIELDS,
    _SUBMISSION_FIELDS,
    _binding_failures,
    _opaque_item_id,
    _packet_item_from_source,
    _quadrant,
    _source_fingerprint,
    _timestamp_valid,
    _utc_datetime,
    _valid_hex,
    _validate_label_blind_source_set,
    canonical_sha256,
    packet_sha256,
)


def _valid_ai_submission_attestation(evidence: dict[str, Any]) -> bool:
    attestation = evidence.get("attestation")
    return bool(
        isinstance(attestation, dict)
        and set(attestation) == _SUBMISSION_AI_OPERATOR_ATTESTATION_FIELDS
        and attestation.get("annotator_class") == ANNOTATOR_KIND_AI_OPERATOR
        and attestation.get("independent_external_human") is False
        and attestation.get("same_session_critique_not_independent_review") is True
        and attestation.get("independent_of_benchmark_author") is False
        and attestation.get("no_other_annotator_or_result_access") is True
        and attestation.get("conflicts_disclosed") is True
        and _timestamp_valid(attestation.get("completed_at_utc"))
    )


def _valid_ai_adjudication_attestation(evidence: dict[str, Any]) -> bool:
    attestation = evidence.get("attestation")
    return bool(
        isinstance(attestation, dict)
        and set(attestation) == _ADJUDICATION_AI_OPERATOR_ATTESTATION_FIELDS
        and attestation.get("annotator_class") == ANNOTATOR_KIND_AI_OPERATOR
        and attestation.get("independent_external_human") is False
        and attestation.get("same_session_critique_not_independent_review") is True
        and attestation.get("independent_of_benchmark_author") is False
        and attestation.get("no_result_access_before_resolution") is True
        and attestation.get("conflicts_disclosed") is True
        and _timestamp_valid(attestation.get("completed_at_utc"))
    )


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
        if set(row) - allowed_fields:
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


def compile_ai_operator_adjudicated_benchmark(
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
    minimum_annotators: int = 2,
) -> dict[str, Any]:
    """Compile demoted AI_OPERATOR annotations. Confirmatory eligibility stays false."""
    failures: list[str] = []
    source_frozen_at = None
    packet_source_frozen_at = None
    packet_frozen_at = None
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
            if not isinstance(source_item, dict) or not isinstance(source_item.get("source_item_id"), str):
                continue
            item_id = _opaque_item_id(
                subject_sha=subject_sha,
                packet_id=packet["packet_id"],
                source_item_id=source_item["source_item_id"],
            )
            expected_mapping[item_id] = source_item["source_item_id"]
            expected_packet_items[item_id] = _packet_item_from_source(source_item, item_id=item_id)
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
    if (
        packet.get("negative_history_benchmark_sha256") != negative_hashes
        or linkage.get("negative_history_benchmark_sha256") != negative_hashes
    ):
        failures.append("negative_history_hash_binding_mismatch")
    negative_fingerprints = {
        _source_fingerprint(case)
        for benchmark in negative_history_benchmarks
        for case in benchmark.get("cases", [])
    }
    if any(_source_fingerprint(item) in negative_fingerprints for item in source_set.get("items", [])):
        failures.append("source_item_overlaps_negative_history")
    for field, observed in {
        "protocol_id": observed_protocol_id,
        "protocol_sha256": observed_protocol_sha256,
        "rubric_id": observed_rubric_id,
        "rubric_sha256": observed_rubric_sha256,
    }.items():
        if source_set.get(field) != observed or packet.get(field) != observed:
            failures.append(f"frozen_artifact_binding_mismatch:{field}")

    eligible_submissions: list[dict[str, Any]] = []
    annotator_ids: list[str] = []
    submission_times: list[str] = []
    for submission in submissions:
        annotator_id = submission.get("annotator_id")
        identity = annotator_id if isinstance(annotator_id, str) and annotator_id else "missing"
        local_failures: list[str] = []
        if submission.get("schema_version") != SCHEMA_SUBMISSION_AI_OPERATOR_V2:
            local_failures.append(f"submission_schema_mismatch:{identity}")
        if set(submission) != _SUBMISSION_FIELDS:
            local_failures.append(f"submission_fields_mismatch:{identity}")
        local_failures.extend(_binding_failures(submission, packet, f"submission:{identity}"))
        if not _valid_ai_submission_attestation(submission):
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
    if len(set(annotator_ids)) < minimum_annotators:
        failures.append("distinct_eligible_annotators_below_minimum")

    adjudicator_id = adjudication.get("adjudicator_id")
    adjudicator_identity = adjudicator_id if isinstance(adjudicator_id, str) and adjudicator_id else "missing"
    if adjudication.get("schema_version") != SCHEMA_ADJUDICATION_AI_OPERATOR_V2:
        failures.append("adjudication_schema_mismatch")
    if set(adjudication) != _ADJUDICATION_FIELDS:
        failures.append("adjudication_fields_mismatch")
    failures.extend(_binding_failures(adjudication, packet, "adjudication"))
    if not _valid_ai_adjudication_attestation(adjudication):
        failures.append("adjudication_attestation_invalid")
    else:
        adjudication_time = adjudication["attestation"]["completed_at_utc"]
        if submission_times and _utc_datetime(adjudication_time) <= max(
            _utc_datetime(value) for value in submission_times
        ):
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
    if provenance_audit.get("schema_version") != SCHEMA_PROVENANCE_AI_OPERATOR_V2:
        failures.append("provenance_audit_schema_mismatch")
    if set(provenance_audit) != _PROVENANCE_AI_OPERATOR_FIELDS:
        failures.append("provenance_audit_fields_mismatch")
    failures.extend(_binding_failures(provenance_audit, packet, "provenance_audit"))
    coordinator_id = provenance_audit.get("coordinator_id")
    if not isinstance(coordinator_id, str) or not coordinator_id or coordinator_id in adjudication_people:
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
        identity for identity in (coordinator_id, auditor_id) if isinstance(identity, str) and identity
    }
    source_attestation = source_set.get("label_blind_attestation", {})
    curator_id = source_attestation.get("curator_id")
    benchmark_author_ids = source_attestation.get("benchmark_author_ids", [])
    if (
        provenance_audit.get("verified_source_curator_id") != curator_id
        or provenance_audit.get("verified_benchmark_author_ids") != benchmark_author_ids
    ):
        failures.append("provenance_source_identity_binding_mismatch")
    protected_source_people = {
        identity for identity in [curator_id, *benchmark_author_ids] if isinstance(identity, str) and identity
    }
    overlapping_roles = sorted(protected_source_people & operational_people)
    if overlapping_roles:
        failures.append("source_governance_role_independence_violated:" + ",".join(overlapping_roles))
    for field, expected in (
        ("annotator_class", ANNOTATOR_KIND_AI_OPERATOR),
        ("independent_external_human", False),
        ("same_session_critique_not_independent_review", True),
        ("auditor_is_external_human", False),
        ("auditor_independent_of_benchmark_author", False),
        ("auditor_verified_input_hashes", True),
        ("verified_distinct_human_identities", False),
        ("verified_domain_expertise", False),
        ("verified_independence_from_benchmark_author", False),
        ("verified_access_chronology", True),
        ("authority_class", ANNOTATION_AUTHORITY_DEMOTED_AI),
    ):
        if provenance_audit.get(field) != expected:
            failures.append(f"provenance_ai_operator_stamp_mismatch:{field}")
    if not isinstance(provenance_audit.get("claim_boundary"), str) or not provenance_audit["claim_boundary"].strip():
        failures.append("provenance_ai_operator_claim_boundary_missing")
    if set(provenance_audit.get("verified_person_ids", [])) != operational_people:
        failures.append("provenance_person_coverage_mismatch")
    if sorted(provenance_audit.get("submission_sha256", [])) != expected_submission_hashes:
        failures.append("provenance_submission_hash_mismatch")
    if provenance_audit.get("adjudication_sha256") != canonical_sha256(adjudication):
        failures.append("provenance_adjudication_hash_mismatch")
    audited_at = provenance_audit.get("audited_at_utc")
    if not _timestamp_valid(audited_at):
        failures.append("provenance_audit_timestamp_invalid")
    elif _valid_ai_adjudication_attestation(adjudication) and _utc_datetime(audited_at) <= _utc_datetime(
        adjudication["attestation"]["completed_at_utc"]
    ):
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
        "annotator_class": ANNOTATOR_KIND_AI_OPERATOR,
        "independent_external_human": False,
        "same_session_critique_not_independent_review": True,
        "annotation_authority_class": ANNOTATION_AUTHORITY_DEMOTED_AI,
        "demoted_training_eligible": True,
    }
    failures = list(dict.fromkeys(failures))
    if failures:
        return {
            "passed": False,
            "failures": failures,
            "packet_id": packet.get("packet_id"),
            "packet_sha256": expected_hash,
            "eligible_distinct_annotator_count": len(set(annotator_ids)),
            "benchmark": None,
            "import_receipt": {
                **receipt_base,
                "passed": False,
                "failures": failures,
                "coordinate_exact_agreement": {},
                "coordinate_conflict_count": {},
                "benchmark_sha256": None,
                "demoted_training_eligible": False,
            },
        }

    adjudicated_by_item = {row["item_id"]: row for row in adjudication["items"]}
    case_by_source_id = {item["source_item_id"]: item for item in source_set["items"]}
    submission_rows = {
        item_id: [
            next(row for row in submission["items"] if row["item_id"] == item_id)
            for submission in eligible_submissions
        ]
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
                "annotator_type": "ai_operator_non_independent",
                "annotator_kind": ANNOTATOR_KIND_AI_OPERATOR,
                "independence_class": INDEPENDENCE_NON_INDEPENDENT,
                "human_or_expert": False,
                "independent_of_benchmark_author": False,
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
            "annotator_kind": ANNOTATOR_KIND_AI_OPERATOR,
            "independence_class": INDEPENDENCE_NON_INDEPENDENT,
            "human_or_expert": False,
            "independent_of_benchmark_author": False,
            "status": "final",
            "judgements": {field: resolved[field] for field in ANNOTATION_FIELDS},
            "resolution_rationale": resolved["resolution_rationale"],
            "evidence_refs": resolved["evidence_refs"],
            "completed_at_utc": adjudication["attestation"]["completed_at_utc"],
        }
        case["confirmatory_eligible"] = False
        compiled_cases.append(case)

    agreement = {
        field: sum(len({row[field] for row in rows}) == 1 for rows in submission_rows.values())
        / len(submission_rows)
        for field in ANNOTATION_FIELDS
    }
    conflicts = {
        field: sum(len({row[field] for row in rows}) > 1 for rows in submission_rows.values())
        for field in ANNOTATION_FIELDS
    }
    benchmark = {
        "schema_version": "paper3-confirmatory-benchmark-v2",
        "benchmark_id": (
            f"{source_set['source_set_id']}:ai-operator-adjudicated:{packet['packet_id']}"
        ),
        "authority_status": AUTHORITY_AI_OPERATOR_NON_INDEPENDENT_V2,
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


def evaluate_demoted_ai_operator_annotation_gate_v2(
    benchmark: dict[str, Any],
    protocol: dict[str, Any],
    import_receipt: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
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
    if import_receipt.get("demoted_training_eligible") is not True:
        failures.append("import_receipt_not_demoted_training_eligible")
    if import_receipt.get("annotation_authority_class") != ANNOTATION_AUTHORITY_DEMOTED_AI:
        failures.append("import_receipt_not_demoted_ai_operator_authority")
    if import_receipt.get("benchmark_sha256") != canonical_sha256(benchmark):
        failures.append("annotation_import_benchmark_hash_mismatch")
    if import_receipt.get("protocol_sha256") != protocol_hash:
        failures.append("annotation_import_protocol_hash_mismatch")
    if benchmark.get("subject_sha") != import_receipt.get("subject_sha"):
        failures.append("annotation_import_subject_mismatch")
    if benchmark.get("authority_status") != AUTHORITY_AI_OPERATOR_NON_INDEPENDENT_V2:
        failures.append("benchmark_not_ai_operator_non_independent")
    incomplete = []
    for case in benchmark.get("cases", []):
        records = [
            row
            for row in case.get("annotation_records", [])
            if row.get("annotator_type") == "ai_operator_non_independent"
            and row.get("annotator_kind") == ANNOTATOR_KIND_AI_OPERATOR
            and row.get("independence_class") == INDEPENDENCE_NON_INDEPENDENT
            and row.get("human_or_expert") is False
            and row.get("independent_of_benchmark_author") is False
            and row.get("status") == "final"
            and isinstance(row.get("annotator_id"), str)
        ]
        ids = {row["annotator_id"] for row in records}
        adjudication = case.get("adjudication", {})
        valid = bool(
            case.get("confirmatory_eligible") is False
            and len(ids) >= 2
            and all(type(case.get(field)) is bool for field in ANNOTATION_FIELDS)
            and adjudication.get("annotator_kind") == ANNOTATOR_KIND_AI_OPERATOR
            and adjudication.get("independence_class") == INDEPENDENCE_NON_INDEPENDENT
            and adjudication.get("human_or_expert") is False
            and adjudication.get("independent_of_benchmark_author") is False
            and adjudication.get("status") == "final"
            and adjudication.get("adjudicator_id") not in ids
        )
        if not valid:
            incomplete.append(case.get("case_id", "missing"))
    if not benchmark.get("cases"):
        failures.append("benchmark_has_no_cases")
    if incomplete:
        failures.append("items_not_demoted_ai_operator_complete")
    return {
        "passed": not failures,
        "failures": failures,
        "demoted_complete_item_count": len(benchmark.get("cases", [])) - len(incomplete),
        "missing_or_incomplete_case_ids": incomplete,
        "authority_class": ANNOTATION_AUTHORITY_DEMOTED_AI,
        "confirmatory_authority": False,
        "independent_review_claimed": False,
    }


def build_demoted_ai_operator_gate_receipt(
    *,
    benchmark: dict[str, Any],
    protocol: dict[str, Any],
    import_receipt: dict[str, Any],
    subject_sha: str,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Authorize demoted AI_OPERATOR compute without minting confirmatory authority.

    Does **not** claim frozen confirmatory evaluator binding success. Diagnostic
    metrics are not required for demoted unlock; confirmatory_authority stays false.
    """
    from datetime import datetime, timezone

    timestamp = created_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    annotation_gate = evaluate_demoted_ai_operator_annotation_gate_v2(
        benchmark, protocol, import_receipt
    )
    if benchmark.get("subject_sha") != subject_sha or import_receipt.get("subject_sha") != subject_sha:
        annotation_gate = {
            **annotation_gate,
            "passed": False,
            "failures": list(dict.fromkeys([*annotation_gate.get("failures", []), "gate_subject_sha_mismatch"])),
        }
    base = {
        "schema_version": "paper3-confirmatory-gate-result-v2",
        "experiment_id": "paper3-ai-operator-demoted-gate-v1",
        "subject_sha": subject_sha,
        "created_at_utc": timestamp,
        "frozen_protocol_id": protocol.get("protocol_id"),
        "protocol_sha256": canonical_sha256(protocol),
        "benchmark_id": benchmark.get("benchmark_id"),
        "benchmark_sha256": canonical_sha256(benchmark),
        "claim_boundary": (
            "AI_OPERATOR / NON_INDEPENDENT annotations authorize only demoted "
            "Paper 3 training/inference pilots. They do not mint independent review, "
            "confirmatory structural-signal authority, or Constitution-grade peer review. "
            "This receipt bypasses confirmatory evaluator-hash binding intentionally; "
            "it is not a PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE confirmatory result."
        ),
        "split": "leave_one_family_out",
        "authority_class": ANNOTATION_AUTHORITY_DEMOTED_AI,
        "family_count": len({case.get("family") for case in benchmark.get("cases", []) if isinstance(case, dict)}),
        "case_count": len(benchmark.get("cases", [])),
        "arm_metrics": {},
        "predictions": [],
        "annotation_gate": annotation_gate,
        "diagnostic_signal_gate": {
            "status": "NOT_RUN_DEMOTED_AI_OPERATOR_PATH",
            "passed": False,
            "checks": {},
            "note": "Diagnostic signal deliberately not used to mint confirmatory authority.",
        },
        "overall_cheap_gate_passed": False,
        "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
    }
    if not annotation_gate.get("passed"):
        return {
            **base,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_ANNOTATION_GATE",
            "negative_history": annotation_gate.get("failures", []),
        }
    return {
        **base,
        "expensive_training_authorized": True,
        "gate_verdict": "PASS_AUTHORIZE_DEMOTED_AI_OPERATOR_TRAIN",
        "negative_history": [
            "demoted AI_OPERATOR path: confirmatory evaluator binding and diagnostic "
            "signal not claimed; independent external human review still absent"
        ],
    }
