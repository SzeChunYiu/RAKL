from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import (
    ANNOTATION_FIELDS,
    _validate_items,
    canonical_sha256,
    packet_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "research/paper3/annotation/EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json"
SOURCE_PATH = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_1_20260810.json"
RECEIPT_PATH = ROOT / "research/receipts/PAPER3_V2_1_ANNOTATION_PACKET_FREEZE_20260810.json"
PARENT_SHA = "f4cee8313ec64d02873b87f92c51c35c113cd70d"
PACKET_FILE_SHA = "a3444836090828daf55d8c16e6d477e756c5362a6d30989425587eb2012feda3"
PACKET_CANONICAL_SHA = "b5212517a0bb9cbe308727d7972ded38ce68bf7f52448aeb82f6512e584336eb"
ISSUE_URL = "https://github.com/SzeChunYiu/RAKL/issues/43"
IMMUTABLE_PACKET_URL = (
    "https://github.com/SzeChunYiu/RAKL/tree/"
    "c6f2639b0927566c473817b4ebaafaee3a35ad36/research/paper3/annotation"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v2_1_solicitation_is_discoverable_without_minting_authority() -> None:
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    packet_readme = (
        ROOT / "research/paper3/annotation/README_V2_1.md"
    ).read_text(encoding="utf-8")

    for text in (root_readme, packet_readme):
        assert ISSUE_URL in text
        assert IMMUTABLE_PACKET_URL in text
        assert "zero public responses" in text
        assert "`CANNOT_CHECK` from the public repository" in text

    assert (
        "This solicitation is not annotation evidence, review, adjudication, "
        "provenance-audit evidence, a gate pass, peer review, or publication."
    ) in root_readme
    assert (
        "A solicitation or public comment is not an annotation submission, review, "
        "adjudication, provenance-audit evidence, a gate pass, peer review, or publication."
    ) in packet_readme
    assert "Do not post response files" in packet_readme


def test_v2_1_packet_is_exact_subject_bound_opaque_and_schema_valid() -> None:
    packet = _load(PACKET_PATH)
    schema = _load(ROOT / "schemas/paper3-annotation-packet.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(packet)
    )

    assert errors == []
    assert packet["parent_subject_sha"] == PARENT_SHA
    assert packet["source_set_id"] == "paper3-natural-cross-domain-source-set-v2-1-20260810"
    assert packet["frozen_at_utc"] > packet["source_set_frozen_at_utc"]
    assert len(packet["items"]) == 16
    assert len({item["item_id"] for item in packet["items"]}) == 16
    assert _file_sha(PACKET_PATH) == PACKET_FILE_SHA
    assert packet_sha256(packet) == PACKET_CANONICAL_SHA
    assert canonical_sha256(packet) == PACKET_CANONICAL_SHA

    public_bytes = PACKET_PATH.read_text(encoding="utf-8").lower()
    assert "source_item_id" not in public_bytes
    assert "p3src-" not in public_bytes
    assert "near_miss" not in public_bytes


def test_packet_binds_exact_neutral_source_set_and_not_discarded_packet() -> None:
    packet = _load(PACKET_PATH)
    source = _load(SOURCE_PATH)
    receipt = _load(RECEIPT_PATH)

    assert packet["source_set_sha256"] == canonical_sha256(source)
    assert receipt["packet"]["file_sha256"] == _file_sha(PACKET_PATH)
    assert receipt["packet"]["canonical_sha256"] == canonical_sha256(packet)
    assert receipt["negative_history"]["discarded_packet_reused"] is False
    assert receipt["negative_history"]["discarded_packet_file_sha256"] != _file_sha(
        PACKET_PATH
    )
    assert receipt["negative_history"]["discarded_packet_canonical_sha256"] != canonical_sha256(
        packet
    )


def test_private_linkage_is_hash_receipted_but_absent_from_repository() -> None:
    receipt = _load(RECEIPT_PATH)
    linkage = receipt["private_linkage"]

    assert linkage["committed_to_git"] is False
    assert linkage["remote_path"] == (
        "/projects/hep/fs9/users/scyiu/RAKL-paper3/coordinator/"
        "PAPER3_LINKAGE_V2_1_20260810.json"
    )
    assert linkage["observed_mode"] == "0600"
    assert linkage["file_sha256"] == (
        "f60b780a0e2a3783b4ed1666e26baf022305f5069d02bf431693ab6d51f9443f"
    )
    assert not (ROOT / "research/paper3/annotation/PAPER3_LINKAGE_V2_1_20260810.json").exists()


def test_packet_freeze_preserves_closed_compute_and_review_claims() -> None:
    packet = _load(PACKET_PATH)
    receipt = _load(RECEIPT_PATH)

    assert packet["authority_status"] == "awaiting_genuinely_independent_annotation"
    assert "does not authorize training or inference" in packet["claim_boundary"]
    assert receipt["packet"]["external_judgement_count"] == 0
    assert receipt["gate_state"] == {
        "adjudication_received": False,
        "external_provenance_audit_received": False,
        "genuine_external_annotation_count": 0,
        "slurm_jobs_submitted": 0,
        "training_inference_authorized": False,
        "v2_signal_gate_run": False,
    }
    assert "No external annotation" in receipt["claim_boundary"]
    assert "independent review" in receipt["claim_boundary"]


@pytest.mark.parametrize(
    ("schema_name", "adjudication"),
    [
        ("paper3-annotation-submission-v2-1.schema.json", False),
        ("paper3-adjudication-v2-1.schema.json", True),
    ],
)
def test_additive_v2_1_schemas_preserve_truthful_cannot_assess(
    schema_name: str, adjudication: bool
) -> None:
    packet = _load(PACKET_PATH)
    row = {
        "item_id": packet["items"][0]["item_id"],
        **{field: None for field in ANNOTATION_FIELDS},
        "cannot_assess": True,
        "rationale": "The supplied evidence is insufficient; no Boolean was guessed.",
        "evidence_refs": ["missing-evidence:registered-source"],
    }
    binding = {
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "protocol_id": packet["protocol_id"],
        "protocol_sha256": packet["protocol_sha256"],
        "rubric_id": packet["rubric_id"],
        "rubric_sha256": packet["rubric_sha256"],
    }
    if adjudication:
        artifact = {
            "schema_version": "paper3-external-adjudication-v2",
            **binding,
            "adjudicator_id": "external-adjudicator-placeholder",
            "input_submission_sha256": ["1" * 64, "2" * 64],
            "attestation": {
                "human_or_domain_expert": True,
                "independent_of_benchmark_author": True,
                "no_result_access_before_resolution": True,
                "conflicts_disclosed": True,
                "completed_at_utc": "2026-08-10T23:00:00Z",
            },
            "items": [{**row, "resolution_rationale": "Evidence remains insufficient."}],
        }
    else:
        artifact = {
            "schema_version": "paper3-external-annotation-submission-v2",
            **binding,
            "annotator_id": "external-annotator-placeholder",
            "attestation": {
                "human_or_domain_expert": True,
                "independent_of_benchmark_author": True,
                "no_other_annotator_or_result_access": True,
                "conflicts_disclosed": True,
                "completed_at_utc": "2026-08-10T22:00:00Z",
            },
            "items": [row],
        }

    schema = _load(ROOT / "schemas" / schema_name)
    Draft202012Validator.check_schema(schema)
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(artifact)
    )
    assert errors == []

    failures = _validate_items(
        evidence=artifact,
        expected_item_ids={row["item_id"]},
        identity=(artifact.get("annotator_id") or artifact.get("adjudicator_id")),
        adjudication=adjudication,
    )
    assert any(item.startswith("cannot_assess:") for item in failures)
    assert any(item.startswith("non_boolean_judgement:") for item in failures)
