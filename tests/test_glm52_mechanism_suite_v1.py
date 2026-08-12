from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1"
if str(SUITE) not in sys.path:
    sys.path.insert(0, str(SUITE))


def test_selective_retrieval_offline_controls() -> None:
    mod = importlib.import_module("selective_retrieval")
    mod.offline_selftest()


def test_experience_transfer_offline_controls() -> None:
    mod = importlib.import_module("experience_transfer")
    mod.offline_selftest()


def test_trajectory_governance_offline_controls() -> None:
    mod = importlib.import_module("trajectory_governance")
    mod.offline_selftest()


def test_confirmatory_gate_reads_only_registered_dev_gate(tmp_path: Path) -> None:
    mod = importlib.import_module("run_suite")
    p = tmp_path / "dev.json"
    p.write_text(json.dumps({"summary": {"dev_gate": {"passes": False}, "success_rule": {"passes": True}}}))
    assert mod._gate(p) is False
    p.write_text(json.dumps({"summary": {"dev_gate": {"passes": True}, "success_rule": {"passes": False}}}))
    assert mod._gate(p) is True


def test_protocol_has_no_credential_value() -> None:
    text = (SUITE / "PROTOCOL.json").read_text(encoding="utf-8")
    assert "ANTHROPIC_AUTH_TOKEN" not in text
    assert "72bd139f" not in text
