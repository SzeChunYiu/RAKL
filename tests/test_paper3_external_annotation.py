from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import (
    ANNOTATION_FIELDS,
    build_annotation_packet,
    canonical_sha256,
    compile_adjudicated_benchmark,
    evaluate_annotation_gate_v2,
    packet_sha256,
)


RUBRIC_SHA = "c" * 64
SUBJECT_SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


def _source_set() -> dict:
    items = []
    for index in range(1, 3):
        items.append(
            {
                "source_item_id": f"fresh-case-{index}",
                "family": "queue_flow",
                "source_domain": "packet router",
                "target_domain": "emergency department" if index == 1 else "finite batch queue",
                "source_surface_terms": ["packet", "arrival", "service"],
                "target_surface_terms": ["patient", "arrival", "service"],
                "source_skill_tags": ["flow", "capacity"],
                "target_skill_tags": ["flow", "capacity"],
                "source_dependencies": ["arrival>backlog", "service<backlog"],
                "target_dependencies": ["arrival>backlog", "service<backlog"],
                "candidate_load_bearing_invariant": "arrival above service grows backlog",
                "candidate_load_bearing_boundary": "continual flow",
                "qoi": "backlog stability",
                "source_evidence": ["evidence:source:1"],
                "target_evidence": ["evidence:target:1"],
            }
        )
    return {
        "schema_version": "paper3-label-blind-source-set-v2",
        "source_set_id": "fresh-source-set-v2",
        "authority_status": "fresh_label_blind_source_items",
        "frozen_at_utc": "2026-08-10T19:00:00Z",
        "protocol_id": "paper3-confirmatory-gate-v2",
        "protocol_sha256": canonical_sha256(_protocol()),
        "rubric_id": "paper3-annotation-rubric-v2",
        "rubric_sha256": RUBRIC_SHA,
        "label_blind_attestation": {
            "curator_id": "fresh-curator-z",
            "benchmark_author_ids": ["benchmark-author-primary"],
            "no_v1_item_copying": True,
            "no_outcome_or_diagnostic_access_during_construction": True,
            "frozen_before_annotation": True,
        },
        "items": items,
    }


def _negative_history(*, copy_first_source_item: bool = False) -> list[dict]:
    frozen_v1 = json.loads(
        (ROOT / "research/PAPER3_CHEAP_GATE_BENCHMARK_PROPOSAL_20260810.json").read_text()
    )
    if not copy_first_source_item:
        return [frozen_v1]
    item = deepcopy(_source_set()["items"][0])
    item["case_id"] = item.pop("source_item_id")
    item["load_bearing_invariant_proposal"] = item.pop("candidate_load_bearing_invariant")
    item["load_bearing_boundary_proposal"] = item.pop("candidate_load_bearing_boundary")
    return [frozen_v1, {"benchmark_id": "copied-v1-item", "cases": [item]}]


def _packet() -> tuple[dict, dict]:
    return build_annotation_packet(
        _source_set(),
        packet_id="packet-v2",
        subject_sha=SUBJECT_SHA,
        frozen_at_utc="2026-08-10T19:30:00Z",
        negative_history_benchmarks=_negative_history(),
    )


def _judgements(packet: dict, *, transfer_values: tuple[bool, bool] = (True, False)) -> list[dict]:
    rows = []
    for index, (item, transfer_valid) in enumerate(
        zip(packet["items"], transfer_values, strict=True)
    ):
        semantic_high = index == 1
        rows.append(
            {
                "item_id": item["item_id"],
                "semantic_similarity_high": semantic_high,
                "structural_match": transfer_valid,
                "roles_preserved": transfer_valid,
                "typed_relations_preserved": transfer_valid,
                "invariant_preserved": transfer_valid,
                "boundary_matched": transfer_valid,
                "qoi_matched": True,
                "directional_mapping_complete": transfer_valid,
                "transfer_valid": transfer_valid,
                "cannot_assess": False,
                "rationale": "independent item-level judgement",
                "evidence_refs": ["evidence:source:1", "evidence:target:1"],
            }
        )
    return rows


def _submission(packet: dict, annotator_id: str, completed_at: str) -> dict:
    return {
        "schema_version": "paper3-external-annotation-submission-v2",
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "protocol_id": packet["protocol_id"],
        "protocol_sha256": packet["protocol_sha256"],
        "rubric_id": packet["rubric_id"],
        "rubric_sha256": packet["rubric_sha256"],
        "annotator_id": annotator_id,
        "attestation": {
            "human_or_domain_expert": True,
            "independent_of_benchmark_author": True,
            "no_other_annotator_or_result_access": True,
            "conflicts_disclosed": True,
            "completed_at_utc": completed_at,
        },
        "items": _judgements(packet),
    }


def _adjudication(
    packet: dict, submissions: list[dict], adjudicator_id: str = "adjudicator-c"
) -> dict:
    return {
        "schema_version": "paper3-external-adjudication-v2",
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "protocol_id": packet["protocol_id"],
        "protocol_sha256": packet["protocol_sha256"],
        "rubric_id": packet["rubric_id"],
        "rubric_sha256": packet["rubric_sha256"],
        "adjudicator_id": adjudicator_id,
        "input_submission_sha256": [canonical_sha256(item) for item in submissions],
        "attestation": {
            "human_or_domain_expert": True,
            "independent_of_benchmark_author": True,
            "no_result_access_before_resolution": True,
            "conflicts_disclosed": True,
            "completed_at_utc": "2026-08-10T21:00:00Z",
        },
        "items": [
            {**row, "resolution_rationale": "resolved after both submissions were frozen"}
            for row in _judgements(packet, transfer_values=(False, False))
        ],
    }


def _provenance_audit(
    packet: dict, submissions: list[dict], adjudication: dict
) -> dict:
    return {
        "schema_version": "paper3-external-provenance-audit-v2",
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "protocol_id": packet["protocol_id"],
        "protocol_sha256": packet["protocol_sha256"],
        "rubric_id": packet["rubric_id"],
        "rubric_sha256": packet["rubric_sha256"],
        "coordinator_id": "external-coordinator-d",
        "auditor_id": "external-auditor-e",
        "verified_source_curator_id": "fresh-curator-z",
        "verified_benchmark_author_ids": ["benchmark-author-primary"],
        "verified_distinct_human_identities": True,
        "verified_domain_expertise": True,
        "verified_independence_from_benchmark_author": True,
        "verified_access_chronology": True,
        "auditor_is_external_human": True,
        "auditor_independent_of_benchmark_author": True,
        "auditor_verified_input_hashes": True,
        "verified_person_ids": sorted(
            {item["annotator_id"] for item in submissions}
            | {
                adjudication["adjudicator_id"],
                "external-coordinator-d",
                "external-auditor-e",
            }
        ),
        "submission_sha256": [canonical_sha256(item) for item in submissions],
        "adjudication_sha256": canonical_sha256(adjudication),
        "audited_at_utc": "2026-08-10T21:30:00Z",
    }


def _protocol() -> dict:
    return {
        "protocol_id": "paper3-confirmatory-gate-v2",
        "chronology": {
            "fresh_label_blind_item_set_required": True,
            "confirmatory_use_permitted_after_gate": True,
        },
        "annotation_gate": {
            "minimum_independent_human_or_expert_annotations_per_confirmatory_item": 2,
            "adjudication_required": True,
            "all_evaluated_items_confirmatory_eligible": True,
        },
    }


def _valid_bundle() -> tuple[dict, dict, list[dict], dict, dict, dict]:
    packet, linkage = _packet()
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    audit = _provenance_audit(packet, submissions, adjudication)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is True
    return packet, linkage, submissions, adjudication, audit, result


def test_packet_rejects_label_visible_v1_or_any_prior_outcome_fields() -> None:
    source_set = _source_set()
    source_set["authority_status"] = "internal_proposal_only"
    source_set["items"][0]["transfer_valid_proposal"] = True

    with pytest.raises(ValueError, match="fresh label-blind"):
        build_annotation_packet(
            source_set,
            packet_id="packet-v2",
            subject_sha=SUBJECT_SHA,
            frozen_at_utc="2026-08-10T19:30:00Z",
            negative_history_benchmarks=_negative_history(),
        )


def test_packet_rejects_any_source_item_reused_from_v1_negative_history() -> None:
    with pytest.raises(ValueError, match="overlaps negative-history benchmark"):
        build_annotation_packet(
            _source_set(),
            packet_id="packet-v2",
            subject_sha=SUBJECT_SHA,
            frozen_at_utc="2026-08-10T19:30:00Z",
            negative_history_benchmarks=_negative_history(copy_first_source_item=True),
        )


def test_frozen_v1_stays_byte_identical_and_forbids_confirmatory_use() -> None:
    expected = {
        "research/PAPER3_CHEAP_GATE_BENCHMARK_PROPOSAL_20260810.json": "5527d3589d44b20ad3e42cb379eb0e3e0220a95dd27276581381231267e32767",
        "research/PAPER3_CHEAP_GATE_PROTOCOL_20260810.json": "d9da1b5f5437e393fa072fef3bafea1ed19972ee8c18a6aabef1cd07e088e8e1",
        "src/rakl/paper3_cheap_gate.py": "cc00be7a39eddaf61ab9770cc1b9f7bb93f113624b0d1257ff765bdffb349eb8",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    protocol = json.loads(
        (ROOT / "research/PAPER3_CHEAP_GATE_PROTOCOL_20260810.json").read_text()
    )
    assert protocol["chronology"]["benchmark_labels_visible_during_construction"] is True
    assert protocol["chronology"]["confirmatory_use_permitted"] is False


def test_v2_preparation_receipt_binds_artifacts_and_keeps_compute_closed() -> None:
    receipt = json.loads(
        (ROOT / "research/receipts/PAPER3_V2_GATE_PREPARATION_20260810.json").read_text()
    )
    for relative, digest in receipt["v2_artifacts"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    assert receipt["v1_negative_history"]["confirmatory_use_permitted"] is False
    assert receipt["gate_state"]["fresh_v2_source_set_received"] is False
    assert receipt["gate_state"]["genuine_external_annotation_count"] == 0
    assert receipt["gate_state"]["training_inference_authorized"] is False


def test_annotation_packet_has_no_labels_and_uses_opaque_item_ids() -> None:
    packet, linkage = _packet()
    assert packet["authority_status"] == "awaiting_genuinely_independent_annotation"
    assert {row["item_id"] for row in packet["items"]} == set(linkage["item_to_source_item"])
    assert {row["source_item_id"] for row in _source_set()["items"]}.isdisjoint(
        {row["item_id"] for row in packet["items"]}
    )
    forbidden_fragments = ("proposal", "quadrant", "transfer_valid", "annotation", "adjudication")
    assert all(
        all(not any(fragment in key for fragment in forbidden_fragments) for key in item)
        for item in packet["items"]
    )


def test_compiler_rejects_swapped_opaque_linkage_values() -> None:
    packet, linkage = _packet()
    item_ids = sorted(linkage["item_to_source_item"])
    first_source = linkage["item_to_source_item"][item_ids[0]]
    linkage["item_to_source_item"][item_ids[0]] = linkage["item_to_source_item"][item_ids[1]]
    linkage["item_to_source_item"][item_ids[1]] = first_source
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "opaque_linkage_mapping_mismatch" in result["failures"]


def test_compiler_rejects_packet_payload_swapped_between_opaque_ids() -> None:
    packet, linkage = _packet()
    first_id, second_id = (row["item_id"] for row in packet["items"])
    first_payload = {key: value for key, value in packet["items"][0].items() if key != "item_id"}
    second_payload = {key: value for key, value in packet["items"][1].items() if key != "item_id"}
    packet["items"][0] = {"item_id": first_id, **second_payload}
    packet["items"][1] = {"item_id": second_id, **first_payload}
    linkage["packet_sha256"] = packet_sha256(packet)
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "packet_payload_source_binding_mismatch" in result["failures"]


@pytest.mark.parametrize("role", ["annotator", "adjudicator", "coordinator", "auditor"])
@pytest.mark.parametrize(
    "protected_id", ["fresh-curator-z", "benchmark-author-primary"]
)
def test_compiler_enforces_source_governance_role_independence(
    role: str, protected_id: str
) -> None:
    source_set = _source_set()
    packet, linkage = build_annotation_packet(
        source_set,
        packet_id="packet-v2",
        subject_sha=SUBJECT_SHA,
        frozen_at_utc="2026-08-10T19:30:00Z",
        negative_history_benchmarks=_negative_history(),
    )
    first_annotator = protected_id if role == "annotator" else "annotator-a"
    submissions = [
        _submission(packet, first_annotator, "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudicator_id = protected_id if role == "adjudicator" else "adjudicator-c"
    adjudication = _adjudication(packet, submissions, adjudicator_id=adjudicator_id)
    audit = _provenance_audit(packet, submissions, adjudication)
    if role == "coordinator":
        audit["coordinator_id"] = protected_id
    if role == "auditor":
        audit["auditor_id"] = protected_id
    audit["verified_person_ids"] = sorted(
        {submission["annotator_id"] for submission in submissions}
        | {
            adjudication["adjudicator_id"],
            audit["coordinator_id"],
            audit["auditor_id"],
        }
    )
    result = compile_adjudicated_benchmark(
        source_set=source_set,
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert any(
        failure.startswith("source_governance_role_independence_violated:")
        for failure in result["failures"]
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("verified_source_curator_id", "wrong-curator"),
        ("verified_benchmark_author_ids", ["wrong-author"]),
    ],
)
def test_compiler_binds_audited_source_identity_contract(field: str, value: object) -> None:
    packet, linkage = _packet()
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    audit = _provenance_audit(packet, submissions, adjudication)
    audit[field] = value
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "provenance_source_identity_binding_mismatch" in result["failures"]


def test_compiler_fails_closed_for_duplicate_annotators() -> None:
    packet, linkage = _packet()
    duplicate = _submission(packet, "annotator-a", "2026-08-10T20:00:00Z")
    submissions = [duplicate, deepcopy(duplicate)]
    adjudication = _adjudication(packet, submissions)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "distinct_eligible_annotators_below_minimum" in result["failures"]
    assert result["benchmark"] is None


def test_compiler_rejects_subject_packet_linkage_or_frozen_artifact_mismatch() -> None:
    packet, linkage = _packet()
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    linkage["parent_subject_sha"] = "0" * 40
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256="0" * 64,
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "subject_packet_linkage_mismatch" in result["failures"]
    assert "frozen_artifact_binding_mismatch:protocol_sha256" in result["failures"]


def test_compiler_fails_closed_for_self_adjudication_incomplete_or_bad_chronology() -> None:
    packet, linkage = _packet()
    first = _submission(packet, "annotator-a", "2026-08-10T20:00:00Z")
    second = _submission(packet, "annotator-b", "2026-08-10T19:00:00Z")
    second["items"].pop()
    submissions = [first, second]
    adjudication = _adjudication(packet, submissions, adjudicator_id="annotator-a")
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "submission_item_coverage_mismatch:annotator-b" in result["failures"]
    assert "submission_precedes_packet_freeze:annotator-b" in result["failures"]
    assert "adjudicator_not_distinct" in result["failures"]


def test_compiler_uses_only_adjudicated_values_and_opens_v2_annotation_gate() -> None:
    packet, linkage = _packet()
    submissions = [
        _submission(packet, "annotator-a", "2026-08-10T20:00:00Z"),
        _submission(packet, "annotator-b", "2026-08-10T20:05:00Z"),
    ]
    adjudication = _adjudication(packet, submissions)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=_provenance_audit(packet, submissions, adjudication),
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is True
    benchmark = result["benchmark"]
    assert benchmark is not None
    assert benchmark["authority_status"] == "independently_annotated_and_adjudicated_v2"
    assert set(ANNOTATION_FIELDS).issubset(benchmark["cases"][0])
    assert not any("proposal" in key for key in benchmark["cases"][0])
    assert benchmark["cases"][0]["transfer_valid"] is False
    assert benchmark["cases"][0]["quadrant"] == "Q4"
    import_receipt = result["import_receipt"]
    assert import_receipt["passed"] is True
    assert import_receipt["training_authorized"] is False
    assert evaluate_annotation_gate_v2(benchmark, _protocol(), import_receipt)["passed"] is True


def test_compiler_rejects_subject_argument_not_bound_to_packet_and_linkage() -> None:
    packet, linkage, submissions, adjudication, audit, _ = _valid_bundle()
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha="b" * 40,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "subject_packet_linkage_mismatch" in result["failures"]
    assert result["benchmark"] is None


def test_compiler_requires_exact_frozen_v1_and_rechecks_overlap() -> None:
    packet, linkage, submissions, adjudication, audit, _ = _valid_bundle()
    fake_history = [{"benchmark_id": "not-v1", "cases": []}]
    packet["negative_history_benchmark_sha256"] = [canonical_sha256(fake_history[0])]
    linkage["negative_history_benchmark_sha256"] = [canonical_sha256(fake_history[0])]
    linkage["packet_sha256"] = packet_sha256(packet)
    for evidence in [*submissions, adjudication, audit]:
        evidence["packet_sha256"] = packet_sha256(packet)
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=fake_history,
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert "required_v1_negative_history_missing" in result["failures"]


@pytest.mark.parametrize(
    ("artifact", "bad_timestamp", "failure"),
    [
        ("source", "2026-08-10T21:00:00+00:00", "source_set_invalid:"),
        ("packet", "2026-08-10T19:30:00+00:00", "packet_timestamp_invalid"),
        ("submission", "2026-08-10T20:00:00+00:00", "submission_attestation_invalid:annotator-a"),
        ("adjudication", "2026-08-10T21:00:00+00:00", "adjudication_attestation_invalid"),
        ("audit", "2026-08-10T21:30:00+00:00", "provenance_audit_timestamp_invalid"),
    ],
)
def test_compiler_rejects_non_z_or_unparsed_chronology(
    artifact: str, bad_timestamp: str, failure: str
) -> None:
    packet, linkage, submissions, adjudication, audit, _ = _valid_bundle()
    source_set = _source_set()
    if artifact == "source":
        source_set["frozen_at_utc"] = bad_timestamp
    elif artifact == "packet":
        packet["frozen_at_utc"] = bad_timestamp
        linkage["packet_sha256"] = packet_sha256(packet)
        for evidence in [*submissions, adjudication, audit]:
            evidence["packet_sha256"] = packet_sha256(packet)
    elif artifact == "submission":
        submissions[0]["attestation"]["completed_at_utc"] = bad_timestamp
    elif artifact == "adjudication":
        adjudication["attestation"]["completed_at_utc"] = bad_timestamp
    else:
        audit["audited_at_utc"] = bad_timestamp
    result = compile_adjudicated_benchmark(
        source_set=source_set,
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert any(item.startswith(failure) for item in result["failures"])


@pytest.mark.parametrize(
    "field",
    [
        "auditor_is_external_human",
        "auditor_independent_of_benchmark_author",
        "auditor_verified_input_hashes",
    ],
)
def test_compiler_requires_external_human_provenance_auditor(field: str) -> None:
    packet, linkage, submissions, adjudication, audit, _ = _valid_bundle()
    audit[field] = False
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert f"provenance_not_verified:{field}" in result["failures"]


def test_source_set_strictly_rejects_unknown_or_label_bearing_fields() -> None:
    for field in ("unknown_metadata", "gold_outcome", "proposal_note"):
        source_set = _source_set()
        source_set["items"][0][field] = "forbidden"
        with pytest.raises(ValueError, match="strict label-blind field allowlist"):
            build_annotation_packet(
                source_set,
                packet_id="packet-v2",
                subject_sha=SUBJECT_SHA,
                frozen_at_utc="2026-08-10T19:30:00Z",
                negative_history_benchmarks=_negative_history(),
            )


@pytest.mark.parametrize(
    ("artifact", "failure"),
    [
        ("packet", "packet_fields_mismatch"),
        ("linkage", "linkage_fields_or_schema_mismatch"),
        ("submission", "submission_fields_mismatch:annotator-a"),
        ("submission_item", "unexpected_judgement_fields:annotator-a:"),
        ("adjudication", "adjudication_fields_mismatch"),
        ("provenance", "provenance_audit_fields_mismatch"),
    ],
)
def test_compiler_runtime_rejects_fields_forbidden_by_strict_schemas(
    artifact: str, failure: str
) -> None:
    packet, linkage, submissions, adjudication, audit, _ = _valid_bundle()
    target = {
        "packet": packet,
        "linkage": linkage,
        "submission": submissions[0],
        "submission_item": submissions[0]["items"][0],
        "adjudication": adjudication,
        "provenance": audit,
    }[artifact]
    target["unexpected_field"] = "must fail closed"
    result = compile_adjudicated_benchmark(
        source_set=_source_set(),
        subject_sha=SUBJECT_SHA,
        packet=packet,
        linkage=linkage,
        submissions=submissions,
        adjudication=adjudication,
        provenance_audit=audit,
        negative_history_benchmarks=_negative_history(),
        observed_protocol_id="paper3-confirmatory-gate-v2",
        observed_protocol_sha256=canonical_sha256(_protocol()),
        observed_rubric_id="paper3-annotation-rubric-v2",
        observed_rubric_sha256=RUBRIC_SHA,
    )
    assert result["passed"] is False
    assert any(item.startswith(failure) for item in result["failures"])


def test_all_owned_v2_schemas_validate_synthetic_runtime_artifacts() -> None:
    packet, _, submissions, adjudication, audit, result = _valid_bundle()
    instances = {
        "paper3-label-blind-source-set.schema.json": _source_set(),
        "paper3-annotation-packet.schema.json": packet,
        "paper3-annotation-submission.schema.json": submissions[0],
        "paper3-adjudication.schema.json": adjudication,
        "paper3-provenance-audit.schema.json": audit,
        "paper3-confirmatory-benchmark-v2.schema.json": result["benchmark"],
        "paper3-annotation-import-receipt.schema.json": result["import_receipt"],
    }
    for filename, instance in instances.items():
        schema = json.loads((ROOT / "schemas" / filename).read_text())
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
        assert errors == [], f"{filename}: {[error.message for error in errors]}"
