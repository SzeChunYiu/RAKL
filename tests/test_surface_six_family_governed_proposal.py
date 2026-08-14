"""Tests for surface_six_family_governed_proposal.py (RSHEA P5 governance half of issue #683)."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from scripts.surface_six_family_governed_proposal import (
    DefectTelemetry,
    load_defect_telemetry,
    build_defect_epoch,
    defect_to_receipts_and_gates,
    build_defect_self_model,
    surface_governed_proposal_for_defect,
)
from rakl.evolution_trace import (
    MetricAuthority,
    HardGateStatus,
    canonical_hash,
)
from rakl.observability_adapters import rakl_canonical_metrics


@pytest.fixture
def defect_json_path(tmp_path):
    """Create a minimal DEFECT.json fixture for testing."""
    defect = {
        "schema": "paper2-six-family-governance-defect-v1",
        "status": "DEFECT_REPORTED__NO_VERDICT_REWRITTEN",
        "authority": "same-context analysis; not independent review",
        "date": "2026-08-14",
        "repo_commit": "60654878",
        "summary": "Test defect summary",
        "defects": [
            {
                "id": "D1_TEST",
                "severity": "HIGH",
                "record": "test_record.json",
                "findings": [{"issue": "test issue", "evidence": "test evidence"}],
            }
        ],
        "proposed_corrections": [
            {"target": "test_target", "proposal": "test proposal", "authority_note": "NOT APPLIED"}
        ],
    }
    defect_path = tmp_path / "DEFECT.json"
    with open(defect_path, "w") as f:
        json.dump(defect, f)
    return defect_path


def test_load_defect_telemetry(defect_json_path):
    """Defect telemetry projection reads and structures DEFECT.json correctly."""
    telemetry = load_defect_telemetry(defect_json_path)
    
    assert telemetry.defect_id == "paper2-six-family-governance-defect-v1"
    assert telemetry.summary == "Test defect summary"
    assert telemetry.severity_counts == (1, 0, 0)  # 1 HIGH
    assert len(telemetry.defects) == 1
    assert telemetry.defects[0] == ("D1_TEST", "HIGH")
    assert len(telemetry.proposed_corrections) == 1
    assert telemetry.authority_note == "same-context analysis; not independent review"


def test_build_defect_epoch():
    """Evaluation epoch construction for defect analysis."""
    epoch = build_defect_epoch(rakl_canonical_metrics, "test-defect-id")
    
    assert epoch.epoch_id.startswith("epoch:defect:")
    # evaluator_hash is the canonical_hash of the input string
    assert epoch.evaluator_hash == canonical_hash("six_family_governance_defect_v1")
    assert len(epoch.evaluator_hash) == 64  # sha256


def test_defect_to_receipts_and_gates():
    """Receipt and gate construction creates proper CONTROL_INPUT and HARD_PROTECTED receipts."""
    telemetry = DefectTelemetry(
        defect_id="test",
        summary="test summary",
        severity_counts=(1, 0, 0),
        defects=(("D1", "HIGH"),),
        proposed_corrections=(("target", "proposal"),),
        authority_note="test authority",
    )
    epoch = build_defect_epoch(rakl_canonical_metrics, "test")
    receipts, gates = defect_to_receipts_and_gates(telemetry, epoch, rakl_canonical_metrics)
    
    # Check we have both CONTROL_INPUT and HARD_PROTECTED receipts
    authorities = {r.authority for r in receipts}
    assert MetricAuthority.CONTROL_INPUT in authorities
    assert MetricAuthority.HARD_PROTECTED in authorities
    
    # Check gates exist and reference HARD_PROTECTED receipts
    assert len(gates) == 2
    gate_ids = {g.gate_id for g in gates}
    assert "authority_boundary_gate" in gate_ids
    assert "high_severity_gate" in gate_ids
    
    # Check gate receipt IDs reference actual receipts
    receipt_ids = {r.metric_id for r in receipts}
    for gate in gates:
        for rid in gate.metric_receipt_ids:
            assert rid in receipt_ids


def test_build_defect_self_model():
    """Self-model snapshot construction includes context signature."""
    telemetry = DefectTelemetry(
        defect_id="test-defect",
        summary="test",
        severity_counts=(2, 0, 0),
        defects=(),
        proposed_corrections=(()),
        authority_note="test",
    )
    epoch = build_defect_epoch(rakl_canonical_metrics, "test-defect")
    self_model = build_defect_self_model(telemetry, epoch)
    
    assert self_model.evaluation_epoch_id == epoch.epoch_id
    assert "defect_id:test-defect" in self_model.context_signature
    assert "high_severity:2" in self_model.context_signature
    assert "authority:external_governance_only" in self_model.context_signature


def test_governed_proposal_structure(tmp_path):
    """Full RSHEA P2-P5 flow produces a valid governed proposal artifact."""
    # Create minimal DEFECT.json with HIGH severity (to get SELECTED)
    defect = {
        "schema": "paper2-six-family-governance-defect-v1",
        "status": "DEFECT_REPORTED__NO_VERDICT_REWRITTEN",
        "authority": "same-context analysis",
        "date": "2026-08-14",
        "repo_commit": "abcdef",
        "summary": "Test defect",
        "defects": [
            {"id": "D1", "severity": "HIGH", "record": "r1", "findings": []},
        ],
        "proposed_corrections": [
            {"target": "t1", "proposal": "p1", "authority_note": "NOT APPLIED"},
        ],
    }
    defect_path = tmp_path / "DEFECT.json"
    with open(defect_path, "w") as f:
        json.dump(defect, f)
    
    # Run the full flow
    output_dir = tmp_path / "output"
    proposal_path = surface_governed_proposal_for_defect(defect_path, output_dir)
    
    # Verify artifact exists
    assert Path(proposal_path).exists()
    
    # Load and verify structure
    with open(proposal_path) as f:
        proposal = json.load(f)
    
    # Required top-level fields
    assert "schema" in proposal
    assert "proposal_id" in proposal
    assert "evaluation_epoch_id" in proposal
    assert "defect_id" in proposal
    assert "sign_off_status" in proposal
    
    # Sign-off must be PENDING_EXTERNAL (not self-signed)
    assert proposal["sign_off_status"] == "PENDING_EXTERNAL"
    assert proposal["external_governance_sign_off"] is None
    
    # Must include proposed actions
    assert isinstance(proposal["proposed_actions"], list)
    assert len(proposal["proposed_actions"]) > 0
    
    # Each action must require external governance
    for action in proposal["proposed_actions"]:
        assert action["authority_required"] == "external_governance_sign_off"
    
    # Must include defect evidence
    assert "defect_evidence" in proposal
    assert proposal["defect_evidence"]["defect_id"] == "paper2-six-family-governance-defect-v1"
    assert "defects" in proposal["defect_evidence"]
    
    # Must include controller receipt
    assert "controller_receipt" in proposal
    assert "status" in proposal["controller_receipt"]
    
    # Must include bridge verdict
    assert "bridge_verdict" in proposal
    assert "acted_upon" in proposal["bridge_verdict"]
    assert proposal["bridge_verdict"]["acted_upon"] is False  # Never acted upon in shadow mode
    
    # Metadata must state authority boundary
    assert "metadata" in proposal
    assert "external_governance" in proposal["metadata"].get("authority_boundary", "")


def test_governed_proposal_never_self_promotes(tmp_path):
    """The proposal must never embed a self-promotion or self-sign-off."""
    # Need HIGH severity defects to get a SELECTED proposal
    defect = {
        "schema": "paper2-six-family-governance-defect-v1",
        "status": "DEFECT_REPORTED",
        "authority": "same-context analysis",
        "date": "2026-08-14",
        "repo_commit": "abc",
        "summary": "Test",
        "defects": [
            {"id": "D1", "severity": "HIGH", "record": "r1", "findings": []},
        ],
        "proposed_corrections": [
            {"target": "t1", "proposal": "p1", "authority_note": "NOT APPLIED"},
        ],
    }
    defect_path = tmp_path / "DEFECT.json"
    with open(defect_path, "w") as f:
        json.dump(defect, f)
    
    output_dir = tmp_path / "output"
    proposal_path = surface_governed_proposal_for_defect(defect_path, output_dir)
    
    with open(proposal_path) as f:
        proposal = json.load(f)
    
    # Sign-off status must be PENDING_EXTERNAL, never SIGNED_OFF
    assert proposal["sign_off_status"] == "PENDING_EXTERNAL"
    assert proposal["external_governance_sign_off"] is None
    
    # Metadata must explicitly forbid self-promotion
    metadata = proposal["metadata"]
    assert "self-promotion" in metadata.get("what_must_not_happen", "")
