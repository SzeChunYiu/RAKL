from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import canonical_sha256
from rakl.paper3_strong_control import (
    STRONG_CONTROL_ARM_FEATURES,
    build_semantic_descriptor_receipt,
    canonical_semantic_pair,
    validated_semantic_scores,
    validate_semantic_descriptor_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SET_PATH = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_1_20260810.json"
PROTOCOL_PATH = ROOT / "research/PAPER3_STRONG_CONTROL_PROTOCOL_V1_20260811.json"
FREEZE_RECEIPT_PATH = ROOT / "research/receipts/PAPER3_STRONG_CONTROL_FREEZE_20260811.json"
PARENT_FREEZE_PATH = ROOT / "research/PAPER3_PARENT_CONTROL_APPLICABILITY_V1_20260811.json"
MODEL_PROVENANCE_PATH = ROOT / "research/PAPER3_BGE_MODEL_PROVENANCE_20260811.json"
REVIEW_PATH = ROOT / "research/receipts/PAPER3_STRONG_CONTROL_INTERNAL_REVIEW_20260811.json"
DESCRIPTOR_ATTEMPT_PATH = ROOT / "research/receipts/PAPER3_STRONG_CONTROL_DESCRIPTOR_ATTEMPT_20260811.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _synthetic_source_set() -> dict:
    return {
        "schema_version": "paper3-label-blind-source-set-v2",
        "source_set_id": "synthetic-label-blind-set",
        "authority_status": "fresh_label_blind_source_items",
        "frozen_at_utc": "2026-08-10T19:00:00Z",
        "protocol_id": "paper3-confirmatory-gate-v2",
        "protocol_sha256": "a" * 64,
        "rubric_id": "rubric-test",
        "rubric_sha256": "b" * 64,
        "label_blind_attestation": {
            "labels_present": False,
            "annotation_records_present": False,
            "adjudication_present": False,
            "evaluated_results_accessed": False,
        },
        "items": [
            {
                "source_item_id": "case-1",
                "family": "family-a",
                "source_domain": "source domain",
                "target_domain": "target domain",
                "source_surface_terms": ["source", "term"],
                "target_surface_terms": ["target", "term"],
                "source_skill_tags": ["source skill"],
                "target_skill_tags": ["target skill"],
                "source_dependencies": ["source dependency"],
                "target_dependencies": ["target dependency"],
                "candidate_load_bearing_invariant": "must not enter semantic text",
                "candidate_load_bearing_boundary": "must not enter semantic text",
                "qoi": "Can the source method answer the target question?",
                "source_evidence": ["source citation and title"],
                "target_evidence": ["target citation and title"],
            }
        ],
    }


def _protocol_for(source_set: dict) -> dict:
    protocol = _load(PROTOCOL_PATH)
    protocol["content_binding"]["source_set_id"] = source_set["source_set_id"]
    protocol["content_binding"]["source_set_sha256"] = canonical_sha256(source_set)
    return protocol


def _ready_descriptor(source_set: dict, protocol: dict) -> dict:
    pair = canonical_semantic_pair(source_set["items"][0], protocol)
    return {
        "schema_version": "paper3-content-bound-semantic-descriptor-v1",
        "descriptor_id": "synthetic-test-only",
        "status": "READY",
        "created_at_utc": "2026-08-10T19:30:00Z",
        "label_access": {
            "external_annotation_accessed": False,
            "adjudication_accessed": False,
            "evaluated_result_accessed": False,
        },
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": canonical_sha256(protocol),
        "source_set_id": source_set["source_set_id"],
        "source_set_sha256": canonical_sha256(source_set),
        "model": protocol["semantic_model"],
        "observed_model_files": protocol["semantic_model"]["required_files"],
        "runtime": {
            "device": "cpu",
            "dtype": "float32",
            "local_files_only": True,
            "batch_size": 1,
        },
        "descriptors": [
            {
                "case_id": "case-1",
                "source_text_sha256": pair["source_text_sha256"],
                "target_text_sha256": pair["target_text_sha256"],
                "pair_sha256": pair["pair_sha256"],
                "raw_logit": 0.25,
                "semantic_score": 0.5621765008857981,
            }
        ],
        "failures": [],
        "claim_boundary": "Synthetic unit-test descriptor only.",
        "training_authorized": False,
    }


def test_semantic_pair_is_content_bound_and_excludes_structural_proposals() -> None:
    source_set = _synthetic_source_set()
    protocol = _protocol_for(source_set)
    item = source_set["items"][0]
    original = canonical_semantic_pair(item, protocol)

    changed_evidence = deepcopy(item)
    changed_evidence["target_evidence"] = ["different target citation"]
    assert canonical_semantic_pair(changed_evidence, protocol)["pair_sha256"] != original["pair_sha256"]

    changed_proposals = deepcopy(item)
    changed_proposals["candidate_load_bearing_invariant"] = "outcome-suggestive proposal changed"
    changed_proposals["candidate_load_bearing_boundary"] = "outcome-suggestive proposal changed"
    assert canonical_semantic_pair(changed_proposals, protocol) == original
    assert "must not enter semantic text" not in original["source_text"]
    assert "must not enter semantic text" not in original["target_text"]


def test_missing_model_assets_fail_closed_without_scores_or_label_access(tmp_path: Path) -> None:
    source_set = _synthetic_source_set()
    protocol = _protocol_for(source_set)
    receipt = build_semantic_descriptor_receipt(
        source_set=source_set,
        protocol=protocol,
        model_dir=tmp_path,
        created_at_utc="2026-08-10T19:30:00Z",
    )
    assert receipt["status"] == "CANNOT_CHECK_MODEL_ASSET_MISSING"
    assert receipt["descriptors"] == []
    assert "model_asset_missing:model.safetensors" in receipt["failures"]
    assert receipt["label_access"] == {
        "external_annotation_accessed": False,
        "adjudication_accessed": False,
        "evaluated_result_accessed": False,
    }
    assert receipt["training_authorized"] is False


def test_actual_v2_1_source_set_reaches_model_asset_gate(tmp_path: Path) -> None:
    source_set = _load(SOURCE_SET_PATH)
    protocol = _load(PROTOCOL_PATH)
    receipt = build_semantic_descriptor_receipt(
        source_set=source_set,
        protocol=protocol,
        model_dir=tmp_path,
        created_at_utc="2026-08-11T03:56:30Z",
    )
    assert receipt["status"] == "CANNOT_CHECK_MODEL_ASSET_MISSING"
    assert receipt["descriptors"] == []
    assert "source_set_id_mismatch" not in receipt["failures"]
    assert "source_set_not_attested_label_blind" not in receipt["failures"]


def test_all_actual_v2_1_items_render_through_frozen_projection_before_labels() -> None:
    source_set = _load(SOURCE_SET_PATH)
    protocol = _load(PROTOCOL_PATH)
    pairs = [canonical_semantic_pair(item, protocol) for item in source_set["items"]]
    assert len(pairs) == 16
    assert all(len(row["pair_sha256"]) == 64 for row in pairs)
    for item, pair in zip(source_set["items"], pairs, strict=True):
        assert f"qoi: {item['qoi']}" in pair["source_text"]
        assert f"qoi: {item['qoi']}" in pair["target_text"]
        for side in ("source", "target"):
            text = pair[f"{side}_text"]
            for field in protocol["content_binding"]["side_fields"]:
                assert f"{field}: " in text
        assert "candidate_load_bearing_invariant:" not in pair["source_text"]
        assert "candidate_load_bearing_boundary:" not in pair["target_text"]


def test_ready_descriptor_is_rejected_if_any_content_binding_changes() -> None:
    source_set = _synthetic_source_set()
    protocol = _protocol_for(source_set)
    descriptor = _ready_descriptor(source_set, protocol)
    assert validate_semantic_descriptor_receipt(source_set, protocol, descriptor) == []

    mutated = deepcopy(source_set)
    mutated["items"][0]["target_surface_terms"].append("mutation")
    failures = validate_semantic_descriptor_receipt(mutated, protocol, descriptor)
    assert "source_set_sha256_mismatch" in failures
    assert "content_binding_mismatch:case-1" in failures


def test_ready_descriptor_must_predate_external_labels_and_use_exact_model() -> None:
    source_set = _synthetic_source_set()
    protocol = _protocol_for(source_set)
    descriptor = _ready_descriptor(source_set, protocol)
    wrong_model = deepcopy(descriptor)
    wrong_model["model"]["revision"] = "0" * 40
    assert "model_binding_mismatch" in validate_semantic_descriptor_receipt(
        source_set, protocol, wrong_model
    )

    wrong_score = deepcopy(descriptor)
    wrong_score["descriptors"][0]["semantic_score"] = 0.1
    assert "score_transform_mismatch:case-1" in validate_semantic_descriptor_receipt(
        source_set, protocol, wrong_score
    )


def test_frozen_successor_arm_contract_uses_cross_encoder_in_every_strong_arm() -> None:
    assert STRONG_CONTROL_ARM_FEATURES == {
        "content_cross_encoder": ("content_semantic",),
        "skill_aware_content": ("content_semantic", "skill"),
        "dependency_aware_content": ("content_semantic", "skill", "dependency"),
        "witnessed_structure_content": (
            "content_semantic",
            "skill",
            "dependency",
            "invariant",
            "boundary",
            "qoi",
            "directional",
        ),
    }
    source_set = _synthetic_source_set()
    protocol = _protocol_for(source_set)
    descriptor = _ready_descriptor(source_set, protocol)
    assert validated_semantic_scores(source_set, protocol, descriptor) == {
        "case-1": descriptor["descriptors"][0]["semantic_score"]
    }

    descriptor["descriptors"][0]["pair_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="content_binding_mismatch:case-1"):
        validated_semantic_scores(source_set, protocol, descriptor)

    descriptor["created_at_utc"] = "2026-08-10T21:00:00Z"
    assert "descriptor_not_frozen_before_label_access" in validate_semantic_descriptor_receipt(
        source_set,
        protocol,
        descriptor,
        first_external_label_at_utc="2026-08-10T20:00:00Z",
    )


def test_protocol_freezes_modern_cross_encoder_and_exact_content_projection() -> None:
    source_set = _load(SOURCE_SET_PATH)
    protocol = _load(PROTOCOL_PATH)
    assert protocol["frozen_before_external_labels_visible"] is True
    assert protocol["semantic_model"]["model_id"] == "BAAI/bge-reranker-v2-m3"
    assert protocol["semantic_model"]["license"] == "apache-2.0"
    assert protocol["semantic_model"]["revision"] == "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    files = {row["path"]: row for row in protocol["semantic_model"]["required_files"]}
    assert files["model.safetensors"]["sha256"] == "d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286"
    assert files["model.safetensors"]["bytes"] == 2271071852
    assert protocol["content_binding"]["source_set_sha256"] == canonical_sha256(source_set)
    assert "candidate_load_bearing_invariant" in protocol["content_binding"]["excluded_fields"]
    assert "candidate_load_bearing_boundary" in protocol["content_binding"]["excluded_fields"]
    assert protocol["label_policy"]["external_annotations_may_be_read"] is False
    assert protocol["semantic_model"]["provenance_sha256"] == hashlib.sha256(
        MODEL_PROVENANCE_PATH.read_bytes()
    ).hexdigest()


def test_parent_controls_have_faithful_non_interchangeable_applicability_boundaries() -> None:
    artifact = _load(PARENT_FREEZE_PATH)
    parents = {row["parent_id"]: row for row in artifact["parents"]}
    assert parents["skill_it"]["applicable_phases"] == ["training_data_selection"]
    assert parents["mass"]["applicable_phases"] == ["training_data_selection"]
    assert parents["swift"]["applicable_phases"] == ["inference_workflow_transfer"]
    assert parents["skill_it"]["full_fidelity_requirements"]
    assert parents["mass"]["full_fidelity_requirements"]
    assert parents["swift"]["full_fidelity_requirements"]
    assert all(row["current_execution_status"] == "NOT_RUN" for row in parents.values())
    assert artifact["claim_boundary"].startswith("Applicability freeze only")


@pytest.mark.parametrize(
    ("schema_name", "artifact_path"),
    [
        ("paper3-strong-control-protocol.schema.json", PROTOCOL_PATH),
        ("paper3-strong-control-freeze-receipt.schema.json", FREEZE_RECEIPT_PATH),
        ("paper3-parent-control-applicability.schema.json", PARENT_FREEZE_PATH),
        ("paper3-model-provenance.schema.json", MODEL_PROVENANCE_PATH),
        ("paper3-content-bound-semantic-descriptor.schema.json", DESCRIPTOR_ATTEMPT_PATH),
        ("paper3-internal-review.schema.json", REVIEW_PATH),
    ],
)
def test_frozen_artifacts_validate_exact_schemas(schema_name: str, artifact_path: Path) -> None:
    schema = _load(ROOT / "schemas" / schema_name)
    artifact = _load(artifact_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(artifact)


def test_freeze_receipt_preserves_block_instead_of_fabricating_control_results() -> None:
    receipt = _load(FREEZE_RECEIPT_PATH)
    assert receipt["status"] == "FROZEN_PROTOCOL_MODEL_ASSET_UNAVAILABLE"
    assert receipt["semantic_descriptor_generated"] is False
    assert receipt["external_annotations_accessed"] is False
    assert receipt["evaluated_results_accessed"] is False
    assert receipt["training_or_inference_authorized"] is False
    assert receipt["blocking_failures"] == ["model_asset_unavailable"]
    assert receipt["next_discriminator"].startswith("Stage and hash-verify")
    for path, expected_sha256 in receipt["artifact_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected_sha256


def test_protocol_binds_exact_implementation_source() -> None:
    protocol = _load(PROTOCOL_PATH)
    binding = protocol["implementation_binding"]
    assert binding["path"] == "src/rakl/paper3_strong_control.py"
    assert binding["sha256"] == hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest()
