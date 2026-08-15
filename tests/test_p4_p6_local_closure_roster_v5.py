from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = (
    ROOT
    / "research"
    / "self_rakl_p4_p6_question_saturation_v6"
    / "LOCAL_CLOSURE_ROSTER_V5.json"
)


def _roster() -> dict:
    return json.loads(ROSTER.read_text(encoding="utf-8"))


def test_final_publication_roster_is_scoped_and_nonsovereign() -> None:
    data = _roster()
    assert data["status"] == "FROZEN_FOR_FINAL_STRICT_PUBLICATION_CLOSURE"
    assert data["global_completeness_claimed"] is False
    assert data["grants_scientific_authority"] is False
    assert data["grants_publication_authority"] is False
    assert data["publication_rule"].strip()
    assert data["local_trust_root_boundary"].strip()


def test_every_final_local_artifact_exists() -> None:
    missing = []
    for item in _roster()["local_obligations"]:
        if not (ROOT / item["artifact"]).is_file():
            missing.append((item["id"], item["artifact"]))
    assert missing == []


def test_current_strict_facades_and_companion_publication_are_load_bearing() -> None:
    items = {item["id"]: item["artifact"] for item in _roster()["local_obligations"]}
    assert items["P5-STRICT-PROMOTION-FACADE"] == "src/rakl/math_research_promotion_strict.py"
    assert items["P6-STRICT-EVOLUTION-FACADE-V5"] == "src/rakl/meta_evolution_v5.py"
    assert items["P5-STRICT-COMPANION-ENTRYPOINT"].endswith("main_strict_20260815.tex")
    assert items["P5-STRICT-PDF-SECTION"].endswith("17_strict_current_promotion_path_20260815.tex")


def test_external_science_remains_open_or_scientifically_blocked() -> None:
    ext = {item["id"]: item for item in _roster()["external_obligations"]}
    assert ext["P4-Q1-INCREMENTAL-INFORMATION"]["status"] == "OPEN_EXTERNAL"
    assert ext["P4-Q2-FIVE-ARM-PHASE2"]["status"] == "OPEN_EXTERNAL"
    assert ext["P4-Q3-TRAIN-INFERENCE-IDENTITY"]["status"] == "BLOCKED_ON_Q2"
    assert ext["P4-GENERALIZATION"]["status"] == "BLOCKED_ON_Q2"
    assert ext["P5-PUBLIC-RESEARCH-PERFORMANCE"]["status"] == "OPEN_EXTERNAL"
    assert ext["P5-CONCRETE-NOVELTY-AND-VALUE"]["status"] == "OPEN_EXTERNAL"
    assert ext["P6-EXTERNAL-AGENT-EPOCH1-EPOCH2"]["status"] == "OPEN_EXTERNAL"


def test_exact_head_closure_requires_strict_paper5_companion_and_all_other_gates() -> None:
    workflows = set(_roster()["required_exact_head_workflows"])
    assert {
        "test",
        "paper5-formal-assurance",
        "paper5-strict-current-publication",
        "paper5-verified-discovery-release",
        "publication-pdfs",
        "active-packet-registry",
        "p4-scheduler-promotion",
        "p4-adaptive-receipt-admission",
        "p4-phase2-execution-provenance-v1",
        "p1-p4-claim-frontier-regression",
        "trusted-parent-evaluator",
    } <= workflows
