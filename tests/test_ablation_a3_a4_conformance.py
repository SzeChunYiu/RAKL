"""Cheap A3 vs A4 ablation conformance (#156)."""

from __future__ import annotations

import json
from pathlib import Path

from rakl.ablation_a3_a4_conformance import (
    AblationArm,
    ConformanceDecision,
    decide,
    frozen_conformance_panel,
    run_conformance,
)
from rakl.authority_ledger import AuthorityAxis


def test_hostile_prediction_to_mechanism_differs_by_arm() -> None:
    case = next(c for c in frozen_conformance_panel() if c.case_id == "hostile-prediction-to-mechanism")
    a3 = decide(AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED, case.request)
    a4 = decide(AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING, case.request)
    assert a3.decision is ConformanceDecision.ACCEPT
    assert a4.decision is ConformanceDecision.REJECT
    assert case.request.requested_axis is AuthorityAxis.MECHANISM
    assert AuthorityAxis.MECHANISM not in case.request.licensed_axes


def test_legal_upgrade_accepted_by_both() -> None:
    case = next(c for c in frozen_conformance_panel() if c.case_id == "legal-mechanism-upgrade")
    a3 = decide(AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED, case.request)
    a4 = decide(AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING, case.request)
    assert a3.decision is ConformanceDecision.ACCEPT
    assert a4.decision is ConformanceDecision.ACCEPT


def test_run_conformance_passes_and_receipt_matches() -> None:
    report = run_conformance()
    assert report.all_passed
    assert report.grants_scientific_authority is False
    receipt = json.loads(
        Path("research/paper2_closest_parent/A3_A4_CONFORMANCE_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["artifact_hash"] == report.artifact_hash
    assert receipt["status"] == "CONFORMANCE_PASS"
