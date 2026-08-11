from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper3_annotation import canonical_sha256
from rakl.paper3_power_design import (
    CONFIG_PATH,
    DECISION_PATH,
    RESULTS_PATH,
    ZERO_LABELS_PATH,
    build_zero_labels_at_power_design,
    evaluate_power_decision,
    verify_issue_217_zero_public_responses,
    verify_public_annotation_directory,
)

ROOT = Path(__file__).resolve().parents[1]
POWER_DIR = ROOT / "research" / "paper3" / "power_design"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_issue_217_has_zero_imported_external_payloads() -> None:
    scan = verify_issue_217_zero_public_responses(ROOT)
    assert scan["verdict"] == "ZERO_IMPORTED_EXTERNAL_PAYLOADS"
    assert scan["imported_external_payload_paths"] == []
    # Demoted AI_OPERATOR lives under research/paper3/ai_operator_v2_1/ (outside
    # the public annotation dir scan) and must not appear as imported externals.
    assert (ROOT / "research/paper3/ai_operator_v2_1").is_dir()


def test_public_annotation_directory_has_no_completed_judgements() -> None:
    scan = verify_public_annotation_directory(ROOT)
    assert scan["verdict"] == "ZERO_PUBLIC_ANNOTATION_PAYLOADS"
    assert scan["forbidden_payload_files"] == []
    assert "EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json" in scan["files_observed"]
    assert "SOURCE_ITEM_SET_V2_1_20260810.json" in scan["files_observed"]
    # Demoted AI_OPERATOR payloads are not nested under the public annotation dir.
    assert scan.get("demoted_ai_operator_dirs") == []

def test_power_results_and_receipts_exist_and_bind_config() -> None:
    config = _load(CONFIG_PATH)
    results = _load(RESULTS_PATH)
    zero_labels = _load(ZERO_LABELS_PATH)
    decision = _load(DECISION_PATH)

    assert results["config_sha256"] == canonical_sha256(config)
    assert zero_labels["observation"] == "ZERO_LABELS_AT_POWER_DESIGN"
    assert zero_labels["state"] == "ZERO_LABELS_OBSERVED"
    assert zero_labels["counts"]["external_annotations"] == 0
    assert zero_labels["label_payload_accessed"] is False
    assert decision["frozen_artifacts"]["zero_labels_receipt_sha256"] == canonical_sha256(
        zero_labels
    )
    assert decision["frozen_artifacts"]["results_sha256"] == canonical_sha256(results)
    assert decision["confirmatory_packet_version"] == "v2.1"
    assert decision["confirmatory_item_count"] == 16


def test_zero_labels_receipt_matches_live_verification() -> None:
    live = build_zero_labels_at_power_design(ROOT, created_at_utc="2026-08-11T22:00:00Z")
    frozen = _load(ZERO_LABELS_PATH)
    for key in (
        "observation",
        "state",
        "counts",
        "annotation_directory_scan",
        "issue_217_scan",
    ):
        assert live[key] == frozen[key]


@pytest.mark.parametrize(
    "path,decision",
    [
        ("A", "RETAIN_V2_1_ADEQUATELY_POWERED"),
        ("B", "EXPAND_BEFORE_LABELS"),
        ("C", "CONFIRMATORY_PACKET_POWER_LIMITED"),
    ],
)
def test_decision_path_is_one_of_registered_paths(path: str, decision: str) -> None:
    receipt = _load(DECISION_PATH)
    if receipt["decision_path"] == path:
        assert receipt["decision"] == decision


def test_registered_decision_is_path_c_power_limited() -> None:
    config = _load(CONFIG_PATH)
    results = _load(RESULTS_PATH)
    evaluation = evaluate_power_decision(config, results)
    decision = _load(DECISION_PATH)

    assert evaluation["path"] == "C"
    assert evaluation["decision"] == "CONFIRMATORY_PACKET_POWER_LIMITED"
    assert decision["decision_path"] == "C"
    assert decision["material_effects"]["primary_paired_brier_reduction_mde"] == 0.05
    assert evaluation["minimum_n_for_adequacy_all_sigmas"] == 48
    assert decision["power_evaluation"]["underpowered_interpretation_rules"]


def test_primary_mde_not_adequately_powered_at_n16() -> None:
    config = _load(CONFIG_PATH)
    results = _load(RESULTS_PATH)
    evaluation = evaluate_power_decision(config, results)
    threshold = float(config["adequate_power_threshold"])
    for sigma, power in evaluation["analytic_power_at_n16"].items():
        assert float(power) < threshold
