from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from rakl.paper3_annotation import build_annotation_packet, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
OLD_PATH = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_20260810.json"
NEW_PATH = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_1_20260810.json"
RECEIPT_PATH = ROOT / "research/receipts/PAPER3_V2_SOURCE_ID_REPAIR_20260810.json"
REVIEW_PATH = ROOT / "research/receipts/PAPER3_V2_SOURCE_ID_REPAIR_INTERNAL_REVIEW_20260810.json"
V1_PATH = ROOT / "research/PAPER3_CHEAP_GATE_BENCHMARK_PROPOSAL_20260810.json"
PROTOCOL_PATH = ROOT / "research/PAPER3_CONFIRMATORY_GATE_PROTOCOL_V2_20260810.json"
RUBRIC_PATH = ROOT / "research/paper3/annotation/RUBRIC_V2.md"
MANUSCRIPT_PATH = ROOT / "paper/structural_amortization/sections/03_benchmark_v4.tex"
HINTS = ("near_miss", "positive", "negative", "valid", "invalid", "q1", "q2", "q3", "q4")


def test_repaired_source_ids_are_neutral_before_any_external_judgement() -> None:
    old = json.loads(OLD_PATH.read_text(encoding="utf-8"))
    new = json.loads(NEW_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    v1 = json.loads(V1_PATH.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    assert any(any(hint in item["source_item_id"].lower() for hint in HINTS) for item in old["items"])
    assert new["source_set_id"] == "paper3-natural-cross-domain-source-set-v2-1-20260810"
    assert new["frozen_at_utc"] == "2026-08-10T21:08:00Z"
    assert new["protocol_sha256"] == canonical_sha256(protocol)
    assert new["rubric_sha256"] == hashlib.sha256(RUBRIC_PATH.read_bytes()).hexdigest()
    assert len(new["items"]) == 16
    assert [item["source_item_id"] for item in new["items"]] == [
        f"p3src-{index:03d}" for index in range(1, 17)
    ]
    assert all(
        re.fullmatch(r"p3src-\d{3}", item["source_item_id"])
        and not any(hint in item["source_item_id"].lower() for hint in HINTS)
        for item in new["items"]
    )

    for old_item, new_item in zip(old["items"], new["items"], strict=True):
        assert {k: v for k, v in old_item.items() if k != "source_item_id"} == {
            k: v for k, v in new_item.items() if k != "source_item_id"
        }

    packet, linkage = build_annotation_packet(
        new,
        packet_id="paper3-v2-1-repair-test-packet",
        subject_sha="b" * 40,
        frozen_at_utc="2026-08-10T23:59:59Z",
        negative_history_benchmarks=[v1],
    )
    assert len(packet["items"]) == len(linkage["item_to_source_item"]) == 16
    public_packet = json.dumps(packet["items"], sort_keys=True).lower()
    assert "near_miss" not in public_packet
    assert all(item["source_item_id"] not in public_packet for item in new["items"])

    assert receipt["superseded_source_set"]["canonical_sha256"] == canonical_sha256(old)
    assert receipt["repaired_source_set"]["canonical_sha256"] == canonical_sha256(new)
    assert receipt["gate_state"]["genuine_external_annotation_count"] == 0
    assert receipt["gate_state"]["training_inference_authorized"] is False
    assert receipt["discarded_precommit_packet"]["public_packet_committed"] is False
    assert receipt["discarded_precommit_packet"]["private_linkage_removed"] is True
    assert review["review_class"] == "same_context_internal_review_not_independent_peer_review"
    assert review["blocking_code_or_artifact_findings_remaining"] == []
    assert review["external_evidence_gate"]["passed"] is False
    assert review["training_inference_authorized"] is False
    for relative, digest in review["subject_artifact_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_v4_manuscript_records_identifier_leakage_without_overclaim() -> None:
    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    assert "identifier-leakage audit" in manuscript
    assert "superseded before any external judgement" in manuscript
    assert "no training or inference job is authorized" in manuscript
