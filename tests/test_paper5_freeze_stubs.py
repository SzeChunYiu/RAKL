"""Tests for Paper 5 freeze stubs and coverage observation (#250/#253/#255)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
VALIDATE = ROOT / "experiments" / "paper5" / "validate_freeze_stubs.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_confirmatory_packet_stub_refuses_handoff() -> None:
    stub = _load(ROOT / "research/paper5_confirmatory_packet_v1/PACKET_FREEZE_STUB.json")
    schema = _load(SCHEMAS / "paper5-confirmatory-packet-freeze-stub-v1.schema.json")
    Draft202012Validator(schema).validate(stub)
    assert stub["handoff_status"] == "NOT_CONFIRMATORY_PACKET_FROZEN_AND_EXECUTABLE"
    assert stub["grants_scientific_authority"] is False
    assert stub["evaluated_results_accessed"] is False
    assert any(b["id"] == "lunarc-four-arm-resources" for b in stub["blockers"])
    assert any(b["id"] == "issue-238-learning-loop" for b in stub["blockers"])


def test_novelty_audit_stub_has_no_fabricated_humans() -> None:
    stub = _load(ROOT / "research/paper5_novelty_audit_v1/AUDIT_FREEZE_STUB.json")
    schema = _load(SCHEMAS / "paper5-novelty-audit-freeze-stub-v1.schema.json")
    Draft202012Validator(schema).validate(stub)
    assert stub["annotator_responses_present"] is False
    assert stub["adjudication_present"] is False
    assert stub["status"] == "AWAITING_HUMAN_ANNOTATORS"
    assert set(stub["human_roles_required"]) >= {
        "annotator_A",
        "annotator_B",
        "adjudicator",
        "provenance_auditor",
    }


def test_coverage_observation_refuses_pooling_and_authority() -> None:
    obs = _load(ROOT / "research/paper5_longitudinal_v1/COVERAGE_OBSERVATION_20260811.json")
    schema = _load(SCHEMAS / "paper5-longitudinal-coverage-observation-v1.schema.json")
    Draft202012Validator(schema).validate(obs)
    assert obs["comparable_across_declared_versions"] is False
    assert obs["grants_scientific_authority"] is False
    assert obs["status"] == "COVERAGE_OBSERVATION_ONLY"
    universe = ROOT / obs["universe_path"]
    assert universe.is_file()
    import hashlib

    assert hashlib.sha256(universe.read_bytes()).hexdigest() == obs["universe_sha256"]


def test_validate_freeze_stubs_cli_ok_and_refuses_handoff_flag() -> None:
    ok = subprocess.run([sys.executable, str(VALIDATE)], cwd=ROOT, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run(
        [sys.executable, str(VALIDATE), "--allow-confirmatory-handoff"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert bad.returncode != 0
    assert "refusing --allow-confirmatory-handoff" in bad.stderr + bad.stdout
