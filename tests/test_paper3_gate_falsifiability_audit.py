"""The Paper III experience-to-action gate audit must stay reproducible and honest.

These tests pin the audit in *both* directions. A battery that reported
NON_FALSIFIABLE for every condition would catch the defect and be worthless; one
that reported FALSIFIABLE for every condition would be worse, because it would
read as reassurance. So the four dead conditions and the two live ones are each
asserted, and the control — that the baseline reproduces the recorded PASS — is
asserted before any probe verdict is trusted.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SRC = ROOT / "experiments" / "paper3" / "audit_p3_gate_falsifiability.py"
AUDIT_DIR = ROOT / "research" / "paper3_gate_falsifiability_audit_v1"


def _load_audit():
    spec = importlib.util.spec_from_file_location("p3_audit", AUDIT_SRC)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["p3_audit"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit():
    return _load_audit()


@pytest.fixture(scope="module")
def protocol(audit):
    return json.loads(audit.PROTOCOL_PATH.read_text())


@pytest.fixture(scope="module")
def evidence(audit, protocol):
    return audit.build_evidence(protocol)


def test_baseline_reproduces_the_recorded_receipt_exactly(audit, protocol, evidence):
    """Control. Probing a gate that does not reproduce its own receipt proves nothing."""
    recorded = json.loads(audit.RECEIPT_PATH.read_text())
    out = audit.pipeline(evidence, protocol["mutations"])
    assert len(evidence) == recorded["n_cases"] == 1792
    assert out["typed"] == recorded["typed_selective_experience"]


def test_typed_arm_is_a_self_identity_under_every_perturbation(audit, protocol, evidence):
    """The defect, measured exactly rather than against the gate threshold.

    ``execute`` assigns gold as ``strict_action(c)`` and then predicts with
    ``strict_action(c)``. The four typed metrics are pinned to their ceilings by
    construction, so no perturbation of the evidence can move them.
    """
    report = audit.analytic_identity_check(
        evidence, protocol["mutations"], trials=4, seed=20260814
    )
    assert report["exact_action_accuracy_always_exactly_1"]
    assert report["unsafe_apply_rate_always_exactly_0"]
    assert report["cannot_check_recall_always_exactly_1"]
    assert report["legitimate_apply_recall_always_exactly_1"]
    assert set(report["zero_variance_arms"]) == {
        "exact_action_accuracy",
        "unsafe_apply_rate",
        "cannot_check_recall",
        "legitimate_apply_recall",
    }


def test_the_two_live_conditions_actually_move(audit, protocol, evidence):
    """The liveness control: without this, the verdicts above are unfalsifiable themselves."""
    report = audit.analytic_identity_check(
        evidence, protocol["mutations"], trials=4, seed=20260814
    )
    low, high = report["composite_ceiling_range"]
    assert low < high, "composite parent ceiling never moved — the probes are not live"
    low_m, high_m = report["n_mutations_caught_range"]
    assert low_m < high_m, "mutation kill count never moved — the probes are not live"


def test_recorded_audit_receipt_matches_current_code(audit, protocol, evidence):
    """The committed verdicts must be regenerable, not a frozen snapshot of a lost run."""
    receipt = json.loads((AUDIT_DIR / "GATE_FALSIFIABILITY_AUDIT.json").read_text())
    assert receipt["non_falsifiable_conditions"] == [
        "typed_cannot_check",
        "typed_exact",
        "typed_legitimate_apply",
        "typed_unsafe",
    ]
    assert receipt["falsifiable_conditions"] == ["all_mutations_caught", "composite_residual"]
    assert receipt["controls"]["baseline_reproduces_recorded_metrics"] is True
    assert receipt["grants_scientific_authority"] is False

    conditions = audit.gate_conditions(protocol["hard_gate"], protocol["mutations"])
    assert set(conditions) == set(receipt["per_condition"])
    # Every condition still passes on the real evidence, exactly as recorded.
    assert all(fn(evidence) for fn in conditions.values())


def test_narrowing_preserves_rather_than_deletes_the_original_receipt(audit):
    """Negative history is immutable. The audit may narrow; it may not rewrite."""
    narrowing = json.loads((AUDIT_DIR / "INTERPRETATION_NARROWING.json").read_text())
    assert narrowing["narrowed_receipt_status"] == "PRESERVED_VERBATIM_NOT_DELETED_NOT_EDITED"
    assert narrowing["grants_scientific_authority"] is False
    # The original receipt must still be on disk and still carry its own terminal.
    original = json.loads(audit.RECEIPT_PATH.read_text())
    assert original["terminal"] == "PROMOTE_TO_MECHANIC_STRUCTURED_VERIFIED_EXPERIENCE_TO_ACTION"
    assert original["typed_selective_experience"]["exact_action_accuracy"] == 1.0


def test_v2_result_is_recorded_as_cannot_check_not_as_refuted(audit):
    """An unreproducible result is CANNOT_CHECK. Calling it refuted would be a fabrication."""
    v2 = json.loads((AUDIT_DIR / "UNREPRODUCIBLE_V2_RESULT.json").read_text())
    assert v2["status"] == "CANNOT_CHECK"
    assert v2["structurally_predicted_defect_pending_harness"]["status"] == "PREDICTED_NOT_VERIFIED"
    # The frozen protocol it refers to must still exist; only the harness is missing.
    assert (
        ROOT / "research" / "paper3_publication_validation_v2" / "PROTOCOL_FREEZE.json"
    ).is_file()
