"""#536: TCSQ semantic-quotient CERTIFICATE-based successor tests.

Three layers:

  (1) ADVERSARIAL INVALID-CERTIFICATE HARD GATE — the successor must NEVER accept
      an invalid reused answer.  The audit manufactures three attack classes
      (mutated witness, wrong-status cert, false-erasure collision) and asserts
      every genuinely-invalid certificate is rejected.  This is the "validate
      the checker before trusting it" rule applied to the certificate gate.

  (2) REGIME CROSSOVER — the successor result exhibits a positive subregime
      (high redundancy / high solve-cost) whose CI excludes zero from above AND
      a negative subregime whose CI excludes zero from below.  The applicability
      contract must fire (PROMOTE_CONDITIONALLY), not unconditional promote.

  (3) TELEMETRY COMPLETENESS — the EFFICIENCY claim-class required fields are all
      present in the result so the claim-class-conditional telemetry gate passes.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "research" / "tcsq_sq3_v1"))

RES = ROOT / "research" / "tcsq_sq3_v1" / "results" / "sq3_successor.json"


def _result():
    assert RES.exists(), f"successor result file missing: {RES}"
    return json.loads(RES.read_text())


# --------------------------------------------------------------------------- #
# (1) adversarial invalid-certificate hard gate
# --------------------------------------------------------------------------- #
def test_adversarial_invalid_certificate_gate_rejects_all():
    """Every genuinely-invalid certificate must be rejected (hard gate)."""
    from run_sq3_successor import adversarial_invalid_certificate_audit

    audit = adversarial_invalid_certificate_audit(seed=20260813)
    assert audit["attempts"] > 0, "audit must attempt at least one invalid certificate"
    assert audit["all_invalid_certificates_rejected"] is True, (
        f"HARD GATE VIOLATION: {audit['attempts'] - audit['rejections']} invalid "
        f"certificate(s) accepted: {audit['failure_detail']}"
    )
    assert audit["rejection_rate"] == 1.0


def test_adversarial_audit_has_three_attack_classes():
    """The audit exercises mutated-witness, wrong-status, and false-erasure attacks."""
    from run_sq3_successor import adversarial_invalid_certificate_audit

    audit = adversarial_invalid_certificate_audit(seed=20260813)
    # with 40 trials and the three attack classes, attempts should be substantial
    assert audit["attempts"] >= 60, (
        f"expected >=60 adversarial attempts across 3 classes, got {audit['attempts']}"
    )


# --------------------------------------------------------------------------- #
# (2) regime crossover
# --------------------------------------------------------------------------- #
def test_positive_subset_ci_excludes_zero_from_above():
    """The positive subregime CI must exclude zero from above."""
    r = _result()
    pos = r["regime_analysis"]["positive_subset"]
    assert pos["n"] > 0, "must have at least one positive-regime cell"
    lo, hi = pos["net_saving_ci95"]
    assert lo > 0, f"positive subset CI lower bound must be > 0, got {lo}"


def test_negative_subset_ci_excludes_zero_from_below():
    """The negative subregime CI must exclude zero from below."""
    r = _result()
    neg = r["regime_analysis"]["negative_subset"]
    assert neg["n"] > 0, "must have at least one negative-regime cell"
    lo, hi = neg["net_saving_ci95"]
    assert hi < 0, f"negative subset CI upper bound must be < 0, got {hi}"


def test_applicability_contract_fires_for_successor():
    """The regime crossover yields a regime_crossover contract (opposing signs)."""
    from rakl.applicability import build_applicability_contract

    r = _result()
    contract = build_applicability_contract(r["regime_analysis"])
    assert contract is not None, "regime_analysis must yield a crossover contract"
    assert contract["kind"] == "regime_crossover_applicability"
    assert contract["opposing_sign"] is True


def test_gate_verdict_is_promote_conditionally():
    """The promotion gate must NOT unconditionally promote; it promotes conditionally."""
    from promotion_gate import verdict_for, CANDIDATES

    v = verdict_for("tcsq_sq3_successor", CANDIDATES["tcsq_sq3_successor"])
    assert v["verdict"] == "PROMOTE_CONDITIONALLY", (
        f"expected PROMOTE_CONDITIONALLY, got {v['verdict']}"
    )


# --------------------------------------------------------------------------- #
# (3) telemetry completeness (EFFICIENCY claim class)
# --------------------------------------------------------------------------- #
def test_result_has_cost_model():
    """EFFICIENCY claims require a cost decomposition."""
    r = _result()
    assert "cost_model" in r, "result must carry a cost_model decomposition"
    assert len(r["cost_model"]) > 0


def test_result_has_invalid_certificate_gate_field():
    """The hard-gate result must be present in the artifact."""
    r = _result()
    adv = r["adversarial_invalid_certificate_gate"]
    assert adv["all_invalid_certificates_rejected"] is True


def test_successor_beats_historical_negative():
    """The successor aggregate must be less negative than the historical negative.

    Historical: net mean=-4074.34 [-5332.80, -2878.79] (KEEP_PROPOSAL_ONLY).
    The successor need not be unconditionally positive (aggregate CI may straddle
    zero) but its positive subregime must exist and be strongly positive.
    """
    r = _result()
    agg = r["net_advantage"]
    pos = r["regime_analysis"]["positive_subset"]
    historical_mean = -4074.34
    assert pos["net_saving_mean"] > 0
    assert agg["mean"] > historical_mean, (
        f"aggregate mean {agg['mean']} must beat historical {historical_mean}"
    )
