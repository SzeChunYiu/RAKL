from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1_1"
V1 = ROOT / "research" / "glm52_mechanism_suite_v1"
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SUITE) not in sys.path:
    sys.path.insert(0, str(SUITE))


def _load_adapter_module():
    return importlib.import_module("framework_adapter")


def _sample_task() -> dict:
    return {
        "task_id": "RET-001",
        "family": "scope_alignment",
        "question": "Assess target-context claim for entity alpha",
        "entity": "alpha",
        "qoi": "period",
        "context": "target",
        "docs": [
            {
                "doc_id": "D1",
                "entity": "alpha",
                "qoi": "period",
                "context": "target",
                "root": "r1",
                "kind": "measurement",
                "date": 2024,
                "summary": "target measurement supports claim",
            },
            {
                "doc_id": "D2",
                "entity": "alpha",
                "qoi": "period",
                "context": "neighbor",
                "root": "r2",
                "kind": "measurement",
                "date": 2023,
                "summary": "neighboring context measurement",
            },
        ],
        "verdict": "SUPPORT",
        "support_ids": ["D1"],
        "refute_ids": [],
    }


def test_adapter_binds_framework_identity() -> None:
    mod = _load_adapter_module()
    adapter = mod.CanonicalFrameworkAdapter(repo_root=ROOT)
    manifest = adapter.subject_manifest()
    assert manifest["protocol_id"] == "GLM52-MECHANISM-SUITE-V1.1"
    assert manifest["adapter_version"] == "1.1.0"
    assert manifest["outcome_access_status"] == "NO_NEW_GLM_OUTCOME"
    assert len(adapter.framework_sha) == 40
    assert adapter.method_version == "3.0.0"
    assert len(adapter.framework_module_hashes) >= 5
    registered = json.loads((SUITE / "FRAMEWORK_SUBJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert registered["protocol_id"] == manifest["protocol_id"]


def test_retrieve_receipt_uses_epistemic_search_binding() -> None:
    mod = _load_adapter_module()
    adapter = mod.CanonicalFrameworkAdapter(repo_root=ROOT)
    receipt = adapter.retrieve(_sample_task(), budget=2)
    assert receipt.protocol_id == mod.PROTOCOL_ID
    assert receipt.interaction_space_id is not None
    assert len(receipt.selected_candidate_ids) <= 2
    assert receipt.grants_scientific_authority is False
    assert "src/rakl/epistemic_search.py" in dict(receipt.framework_module_hashes)


def test_materialize_and_govern_bindings() -> None:
    mod = _load_adapter_module()
    adapter = mod.CanonicalFrameworkAdapter(repo_root=ROOT)
    task = {
        "task_id": "EXP-001",
        "question": "Apply scoped lesson",
        "entity": "beta",
        "qoi": "stability",
        "context": "target",
        "family": "scope_alignment",
        "verdict": "SUPPORT",
    }
    material = adapter.materialize_experience(task, {}, budget=4)
    assert material.fibre_snapshot_hash
    assert material.grants_scientific_authority is False

    proposal = {
        "step_id": "S1",
        "family": "CLAIM_EVIDENCE_BINDING",
        "action": "COMMIT_SUPPORT",
        "evidence_ids": ["E1"],
        "sequence_index": 1,
        "authority_before": "auth-0",
    }
    case = {
        "case_id": "C1",
        "target_scope": "scope_a",
        "target_axis": "axis_x",
        "initial_authority_fingerprint": "auth-0",
        "evidence": [
            {
                "evidence_id": "E1",
                "root": "root_a",
                "scope": "scope_a",
                "axis": "axis_x",
                "polarity": "SUPPORT",
                "reviewed": True,
            }
        ],
        "gold_steps": [{"step_id": "S1", "licensed_action": "COMMIT_SUPPORT"}],
    }
    step = adapter.govern_trajectory(proposal, case)
    assert step.action == "CANNOT_CHECK"
    assert step.authority_after == step.authority_before


def test_harness_stubs_wire_without_hosted_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    sel = importlib.import_module("harness_stubs.selective_retrieval_stub")
    exp = importlib.import_module("harness_stubs.experience_transfer_stub")
    gov = importlib.import_module("harness_stubs.trajectory_governance_stub")
    assert sel.run_stub(_sample_task())["outcome_access"] == "NO_NEW_GLM_OUTCOME"
    assert exp.run_stub({"task_id": "T", "question": "q", "entity": "e", "qoi": "q", "context": "c", "family": "f"})[
        "outcome_access"
    ] == "NO_NEW_GLM_OUTCOME"
    assert gov.run_stub({"action": "CANNOT_CHECK", "step_id": "S"}, {"initial_authority_fingerprint": "a"})[
        "outcome_access"
    ] == "NO_NEW_GLM_OUTCOME"
