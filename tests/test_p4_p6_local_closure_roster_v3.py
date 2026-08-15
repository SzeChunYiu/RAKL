from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = (
    ROOT
    / "research"
    / "self_rakl_p4_p6_question_saturation_v4"
    / "LOCAL_CLOSURE_ROSTER_V3.json"
)


def _roster() -> dict:
    return json.loads(ROSTER.read_text(encoding="utf-8"))


def test_final_v3_roster_is_nonsovereign_and_not_global_completeness() -> None:
    data = _roster()
    assert data["status"] == "FROZEN_FOR_FINAL_EXACT_HEAD_CLOSURE"
    assert data["global_completeness_claimed"] is False
    assert data["grants_scientific_authority"] is False
    assert data["grants_publication_authority"] is False
    assert data["local_trust_root_boundary"].strip()


def test_every_final_local_artifact_exists_on_candidate_tree() -> None:
    data = _roster()
    missing: list[tuple[str, str]] = []
    for obligation in data["local_obligations"]:
        path = ROOT / obligation["artifact"]
        if not path.is_file():
            missing.append((obligation["id"], obligation["artifact"]))
    assert missing == []


def test_final_roster_points_to_latest_local_successors_not_weaker_identity_layers() -> None:
    data = _roster()
    artifacts = {item["id"]: item["artifact"] for item in data["local_obligations"]}
    assert artifacts["P5-CONTENT-ADDRESSED-RECEIPT-CHAIN"] == "src/rakl/math_research_assurance_v4.py"
    assert artifacts["P6-META-EVOLUTION-V4-CONTENT-IDENTITY"] == "src/rakl/meta_evolution_v4.py"
    assert artifacts["P5-CURRENT-CONTENT-BOUNDARY"].endswith("ASSURANCE_V4_CONTENT_IDENTITY_ADDENDUM_20260815.md")


def test_external_science_remains_explicit_and_noncompensable() -> None:
    data = _roster()
    external = {item["id"]: item for item in data["external_obligations"]}
    assert external["P4-Q1-INCREMENTAL-INFORMATION"]["status"] == "OPEN_EXTERNAL"
    assert external["P4-Q2-FIVE-ARM-PHASE2"]["status"] == "OPEN_EXTERNAL"
    assert external["P4-Q3-TRAIN-INFERENCE-IDENTITY"]["status"] == "BLOCKED_ON_Q2"
    assert external["P4-GENERALIZATION"]["status"] == "BLOCKED_ON_Q2"
    assert external["P5-PUBLIC-RESEARCH-PERFORMANCE"]["status"] == "OPEN_EXTERNAL"
    assert external["P5-CONCRETE-NOVELTY-AND-VALUE"]["status"] == "OPEN_EXTERNAL"
    assert external["P6-EXTERNAL-AGENT-EPOCH1-EPOCH2"]["status"] == "OPEN_EXTERNAL"


def test_exact_head_closure_requires_all_load_bearing_workflows() -> None:
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
