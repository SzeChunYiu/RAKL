from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROSTER=ROOT/"research"/"self_rakl_p4_p6_question_saturation_v4"/"LOCAL_CLOSURE_ROSTER_V2.json"

def test_final_local_roster_is_nonsovereign():
    d=json.loads(ROSTER.read_text())
    assert d["status"]=="FROZEN_FOR_FINAL_LOCAL_CLOSURE_CHECK"
    assert d["global_completeness_claimed"] is False and d["grants_scientific_authority"] is False and d["grants_publication_authority"] is False

def test_all_final_local_artifacts_exist():
    d=json.loads(ROSTER.read_text()); missing=[]
    for item in d["local_obligations"]:
        if not (ROOT/item["artifact"]).is_file(): missing.append((item["id"],item["artifact"]))
    assert missing==[]

def test_final_roster_includes_latest_receipt_and_identity_successors():
    d=json.loads(ROSTER.read_text()); ids={x["id"] for x in d["local_obligations"]}
    assert {"P5-TRANSITIVE-RECEIPT-BINDING","P6-META-EVOLUTION-V4-CONTENT-IDENTITY","P5-EXECUTOR-INVARIANCE-V3"} <= ids

def test_external_science_is_explicit_and_noncompensable():
    d=json.loads(ROSTER.read_text()); e={x["id"]:x for x in d["external_obligations"]}
    assert e["P4-Q2-FIVE-ARM-PHASE2"]["status"]=="OPEN_EXTERNAL"
    assert e["P4-Q3-TRAIN-INFERENCE-IDENTITY"]["status"]=="BLOCKED_ON_Q2"
    assert e["P6-EXTERNAL-AGENT-EPOCH1-EPOCH2"]["status"]=="OPEN_EXTERNAL"
    assert len(d["required_exact_head_workflows"])>=10
