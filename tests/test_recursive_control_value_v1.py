from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "research" / "self_rakl_p4_p6_question_saturation_v3"
PROTOCOL = LANE / "RECURSIVE_CONTROL_VALUE_PROTOCOL_V1.json"
RESULT = LANE / "RECURSIVE_CONTROL_VALUE_RESULT_V1.json"
RUNNER = LANE / "run_recursive_control_value_v1.py"


def _module():
    spec = importlib.util.spec_from_file_location("recursive_control_value_v1", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_precedes_result_and_grants_no_authority() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_EXECUTION"
    assert result["protocol_git_blob_sha"] == "2ffc092a00d30d9d233530616f059f98af877d70"
    assert result["grants_scientific_authority"] is False
    assert result["grants_method_promotion_authority"] is False


def test_committed_known_world_result_reproduces_exact_decision_endpoints() -> None:
    module = _module()
    committed = json.loads(RESULT.read_text(encoding="utf-8"))
    diagnosis = module.diagnosis()
    credit = module.credit()
    assert diagnosis == committed["diagnosis"]
    assert credit == committed["contextual_credit"]


def test_simpler_diagnosis_parent_is_preserved_as_terminal() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    arms = result["diagnosis"]["arms"]
    assert arms["DECISION_VOI"] == arms["INFO_GAIN_PER_COST"]
    assert arms["DECISION_VOI"] == arms["FIXED_SURFACE"]
    assert result["terminal"] == "SIMPLER_PARENT_SUFFICIENT"
    assert result["components"]["diagnosis_component"] == "SIMPLER_PARENT_SUFFICIENT"


def test_contextual_credit_reduces_harm_without_overwriting_overall_terminal() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    arms = result["contextual_credit"]["arms"]
    assert arms["CONTEXT_TRANSPORT_CREDIT"]["harmful_repair_rate"] == 0.0
    assert arms["GLOBAL_CREDIT"]["harmful_repair_rate"] > 0.0
    assert arms["CONTEXT_TRANSPORT_CREDIT"]["regret_vs_oracle"] == 0.0
    assert arms["GLOBAL_CREDIT"]["regret_vs_oracle"] > 0.0
    assert result["terminal"] == "SIMPLER_PARENT_SUFFICIENT"
