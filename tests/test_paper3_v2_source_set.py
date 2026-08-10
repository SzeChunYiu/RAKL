from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import build_annotation_packet, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SET_PATH = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_20260810.json"
PROTOCOL_PATH = ROOT / "research/PAPER3_CONFIRMATORY_GATE_PROTOCOL_V2_20260810.json"
RUBRIC_PATH = ROOT / "research/paper3/annotation/RUBRIC_V2.md"
V1_PATH = ROOT / "research/PAPER3_CHEAP_GATE_BENCHMARK_PROPOSAL_20260810.json"
SCHEMA_PATH = ROOT / "schemas/paper3-label-blind-source-set.schema.json"
RECEIPT_PATH = ROOT / "research/receipts/PAPER3_V2_SOURCE_SET_FREEZE_20260810.json"
MANUSCRIPT_PATH = ROOT / "paper/structural_amortization/sections/03_benchmark_v3.tex"
REVIEW_PATH = ROOT / "research/receipts/PAPER3_V2_SOURCE_SET_INTERNAL_REVIEW_20260810.json"


def test_frozen_source_set_is_fresh_broad_and_packet_compilable() -> None:
    source_set = json.loads(SOURCE_SET_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    v1 = json.loads(V1_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(source_set)
    assert source_set["protocol_sha256"] == canonical_sha256(protocol)
    assert source_set["rubric_sha256"] == hashlib.sha256(RUBRIC_PATH.read_bytes()).hexdigest()
    assert source_set["label_blind_attestation"] == {
        "curator_id": "rakl-curator-ai-01",
        "benchmark_author_ids": ["rakl-author-01"],
        "no_v1_item_copying": True,
        "no_outcome_or_diagnostic_access_during_construction": True,
        "frozen_before_annotation": True,
    }

    families = Counter(item["family"] for item in source_set["items"])
    assert families == {
        "bottleneck_min_cut": 4,
        "diffusion_transport": 4,
        "matching_allocation": 4,
        "path_dependence_reinforcement": 4,
    }
    for item in source_set["items"]:
        for field in (
            "source_surface_terms",
            "target_surface_terms",
            "source_skill_tags",
            "target_skill_tags",
            "source_dependencies",
            "target_dependencies",
            "source_evidence",
            "target_evidence",
        ):
            assert item[field]
        assert item["source_domain"] != item["target_domain"] or item["source_item_id"].endswith("near_miss")

    assert receipt["source_set"]["canonical_sha256"] == canonical_sha256(source_set)
    assert receipt["source_set"]["file_sha256"] == hashlib.sha256(SOURCE_SET_PATH.read_bytes()).hexdigest()
    assert receipt["source_set"]["item_count"] == 16
    assert receipt["source_set"]["family_count"] == 4
    assert receipt["source_set"]["citation_resolution_check"]["http_200_records"] == 19
    assert receipt["gate_state"]["genuine_external_annotation_count"] == 0
    assert receipt["gate_state"]["training_inference_authorized"] is False
    assert receipt["lunarc"]["fs9_root_ready"] is True
    assert receipt["lunarc"]["slurm_jobs_submitted"] == 0
    assert review["review_class"] == "same_context_internal_review_not_independent_peer_review"
    assert review["blocking_code_or_artifact_findings_remaining"] == []
    assert review["external_evidence_gate"]["passed"] is False
    assert review["training_inference_authorized"] is False
    for relative, digest in review["subject_artifact_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    assert "16 fresh label-blind source--target descriptions" in manuscript
    assert "zero external judgements" in manuscript
    assert "no training or inference job is authorized" in manuscript

    packet, linkage = build_annotation_packet(
        source_set,
        packet_id="paper3-v2-source-set-test-packet",
        subject_sha="a" * 40,
        frozen_at_utc="2026-08-10T23:59:59Z",
        negative_history_benchmarks=[v1],
    )
    assert len(packet["items"]) == 16
    assert len(linkage["item_to_source_item"]) == 16
    serialized = json.dumps(packet["items"], sort_keys=True).lower()
    for forbidden in ("transfer_valid", "quadrant", "gold", "prediction", "result"):
        assert forbidden not in serialized
