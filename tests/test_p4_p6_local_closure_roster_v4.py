from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = (
    ROOT
    / "research"
    / "self_rakl_p4_p6_question_saturation_v5"
    / "LOCAL_CLOSURE_ROSTER_V4.json"
)


def _roster() -> dict:
    return json.loads(ROSTER.read_text(encoding="utf-8"))


def test_final_strict_roster_is_scoped_and_nonsovereign() -> None:
    data = _roster()
    assert data["status"] == "FROZEN_FOR_FINAL_STRICT_EXACT_HEAD_CLOSURE"
    assert data["global_completeness_claimed"] is False
    assert data["grants_scientific_authority"] is False
    assert data["grants_publication_authority"] is False
    assert data["local_trust_root_boundary"].strip()
    assert data["historical_api_rule"].strip()


def test_every_final_strict_local_artifact_exists() -> None:
    data = _roster()
    missing = []
    for item in data["local_obligations"]:
        path = ROOT / item["artifact"]
        if not path.is_file():
            missing.append((item["id"], item["artifact"]))
    assert missing == []


def test_final_strict_roster_uses_current_facades() -> None:
    items = {item["id"]: item["artifact"] for item in _roster()["local_obligations"]}
    assert items["P5-STRICT-PROMOTION-FACADE"] == "src/rakl/math_research_promotion_strict.py"
    assert items["P6-STRICT-EVOLUTION-FACADE-V5"] == "src/rakl/meta_evolution_v5.py"
    assert items["P5-CURRENT-STRICT-CONTENT-BOUNDARY"].endswith("STRICT_PROMOTION_PATH_ADDENDUM_20260815.md")
    assert items["P6-CURRENT-STRICT-CONTENT-BOUNDARY"].endswith("STRICT_SELF_EVOLUTION_PATH_ADDENDUM_20260815.md")


def test_external_science_remains_open_or_blocked_by_scientific_predecessor() -> None:
    ext = {item["id"]: item for item in _roster()["external_obligations"]}
    assert ext["P4-Q1-INCREMENTAL-INFORMATION"]["status"] == "OPEN_EXTERNAL"
    assert ext["P4-Q2-FIVE-ARM-PHASE2"]["status"] == "OPEN_EXTERNAL"
    assert ext["P4-Q3-TRAIN-INFERENCE-IDENTITY"]["status"] == "BLOCKED_ON_Q2"
    assert ext["P4-GENERALIZATION"]["status"] == "BLOCKED_ON_Q2"
    assert ext["P5-PUBLIC-RESEARCH-PERFORMANCE"]["status"] == "OPEN_EXTERNAL"
    assert ext["P5-CONCRETE-NOVELTY-AND-VALUE"]["status"] == "OPEN_EXTERNAL"
    assert ext["P6-EXTERNAL-AGENT-EPOCH1-EPOCH2"]["status"] == "OPEN_EXTERNAL"


def test_exact_head_closure_requires_all_ten_load_bearing_workflows() -> None:
    workflows = set(_roster()["required_exact_head_workflows"])
    assert {
        "test",
        "paper5-formal-assurance",
        "paper5-verified-discovery-release",
        "publication-pdfs",
        "active-packet-registry",
        "p4-scheduler-promotion",
        "p4-adaptive-receipt-admission",
        "p4-phase2-execution-provenance-v1",
        "p1-p4-claim-frontier-regression",
        "trusted-parent-evaluator",
    } <= workflows
