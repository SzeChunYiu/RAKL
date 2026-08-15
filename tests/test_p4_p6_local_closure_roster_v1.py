from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROSTER=ROOT/"research"/"self_rakl_p4_p6_question_saturation_v3"/"LOCAL_CLOSURE_ROSTER_V1.json"

def test_local_closure_roster_is_scoped_and_nonsovereign():
    data=json.loads(ROSTER.read_text())
    assert data["status"]=="FROZEN_FOR_LOCAL_CLOSURE_CHECK"
    assert data["global_completeness_claimed"] is False
    assert data["grants_scientific_authority"] is False
    assert data["grants_publication_authority"] is False
    assert data["local_obligations"] and data["external_obligations"]

def test_every_registered_local_artifact_exists_on_exact_candidate_tree():
    data=json.loads(ROSTER.read_text())
    missing=[]
    for obligation in data["local_obligations"]:
        path=ROOT/obligation["artifact"]
        if not path.is_file(): missing.append((obligation["id"],obligation["artifact"]))
    assert missing==[]

def test_external_obligations_are_never_smuggled_into_local_closed_set():
    data=json.loads(ROSTER.read_text())
    local_ids={x["id"] for x in data["local_obligations"]}; external_ids={x["id"] for x in data["external_obligations"]}
    assert local_ids.isdisjoint(external_ids)
    assert {"P4-Q2-FIVE-ARM-PHASE2","P5-PUBLIC-RESEARCH-PERFORMANCE","P6-EXTERNAL-AGENT-EPOCH1-EPOCH2"} <= external_ids
    assert all(x.get("reason","").strip() for x in data["external_obligations"])
