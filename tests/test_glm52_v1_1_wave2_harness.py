from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1_1"
V1 = ROOT / "research" / "glm52_mechanism_suite_v1"
SRC = ROOT / "src"

for path in (SRC, SUITE, V1):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load(name: str):
    return importlib.import_module(name)


def test_lane2_retrieval_arms_and_headroom_gate() -> None:
    mod = _load("harness.selective_retrieval_harness")
    mod.offline_selftest()
    panel = mod.run_offline_panel(phase="dev", n_per_cell=1, pressures=(32_000,))
    assert panel["summary"]["outcome_access"] == "NO_NEW_GLM_OUTCOME"
    assert panel["summary"]["model_runs"] == 0
    assert set(panel["summary"]["arms"]) == set(mod.RETRIEVAL_ARMS)


def test_lane3_experience_arms_and_hostile_cases() -> None:
    mod = _load("harness.experience_transfer_harness")
    mod.offline_selftest()
    panel = mod.run_offline_panel(phase="dev", n_per_family=1)
    assert panel["summary"]["model_runs"] == 0
    assert set(panel["summary"]["arms"]) == set(mod.EXPERIENCE_ARMS)
    assert "hostile_near_miss" in mod.HOSTILE_FAMILIES


def test_lane4_governance_evaluator_and_noninferiority() -> None:
    mod = _load("harness.trajectory_governance_harness")
    mod.offline_selftest()
    panel = mod.run_offline_panel(phase="dev", n_per_kind=1)
    assert panel["summary"]["model_runs"] == 0
    assert set(panel["summary"]["arms"]) == set(mod.GOVERNANCE_ARMS)
    assert panel["summary"]["noninferiority"]["leakage_improvement_required"] == 0.05


def test_harness_stubs_delegate_without_hosted_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    sel = _load("harness_stubs.selective_retrieval_stub")
    exp = _load("harness_stubs.experience_transfer_stub")
    gov = _load("harness_stubs.trajectory_governance_stub")
    task = {
        "task_id": "RET-001",
        "family": "scope",
        "question": "Assess claim",
        "entity": "alpha",
        "qoi": "period",
        "context": "target",
        "docs": [],
        "verdict": "SUPPORT",
        "support_ids": [],
        "refute_ids": [],
    }
    assert sel.run_stub(task)["lane"] == 2
    assert exp.run_stub({"task_id": "T", "question": "q"})["lane"] == 3
    assert gov.run_stub({"action": "CANNOT_CHECK"}, {})["lane"] == 4


def test_offline_selftest_entrypoint() -> None:
    assert _load("offline_selftest").main() == 0
