"""Tests for the soundness-vs-benefit ledger.

The live ledger is clean, which proves little on its own. The bulk of these tests
inject the exact mistakes this programme has already made once and require them to
be caught:

* crediting a benefit to a mechanism whose own definitions determine the outcome
  (the retracted Paper VI "3.31x fewer false promotions" claim);
* recording a non-interference result with no witness that the mechanic ever acts
  (the reason `certified_operator_may_change_canon` exists in the Lean development).
"""

from __future__ import annotations

import copy

import pytest

from rakl.mechanism_benefit import (
    BenefitStatus,
    LedgerError,
    OutcomeProvenance,
    SoundnessStatus,
    integrity_problems,
    load_ledger,
    programme_summary,
    rows,
)


@pytest.fixture
def ledger() -> dict:
    return load_ledger()


def test_live_ledger_has_no_integrity_problems(ledger):
    assert integrity_problems(ledger) == ()


def test_ledger_grants_no_authority(ledger):
    assert ledger["grants_scientific_authority"] is False
    assert ledger["grants_promotion_authority"] is False


def test_every_mechanized_row_names_a_non_vacuity_witness(ledger):
    """A non-interference theorem is satisfied by a system that never acts."""
    for row in rows(ledger):
        if row.soundness is SoundnessStatus.MECHANIZED:
            assert row.non_vacuity_witness, (
                f"{row.mechanic_id} is MECHANIZED but names no non-vacuity witness"
            )


def test_programme_finding_is_reported_honestly(ledger):
    """The headline must match the rows, not the hope."""
    summary = programme_summary(ledger)
    assert summary["benefit_demonstrated"] == 0
    assert summary["supports_working_mechanism_claim"] is False
    assert summary["demonstrated_ids"] == []


def test_the_retracted_paper6_claim_is_recorded_as_cost_not_benefit(ledger):
    """The surviving Paper VI result is a throughput tax. A cost is not a benefit."""
    row = next(r for r in rows(ledger) if r.mechanic_id == "MECH-FAIL-CLOSED-GOVERNED-ACCEPTANCE")
    assert row.benefit is BenefitStatus.COST_ONLY
    assert row.outcome_provenance is OutcomeProvenance.EXTERNAL


def test_paper2_contract_is_recorded_circular(ledger):
    """Its outcome is determined by the same construction as the mechanism."""
    row = next(r for r in rows(ledger) if r.mechanic_id == "MECH-TRANSPORT-APPLICABILITY-CONTRACT")
    assert row.benefit is BenefitStatus.CIRCULAR
    assert row.outcome_provenance is OutcomeProvenance.SELF_AUTHORED


def test_paper4_refutation_is_preserved(ledger):
    """The honest negative must not be quietly softened to NOT_ATTEMPTED."""
    row = next(r for r in rows(ledger) if r.mechanic_id == "MECH-ADAPTIVE-STRUCTURAL-ALLOCATION")
    assert row.benefit is BenefitStatus.REFUTED
    assert row.ablation_arm is not None


# --- the ledger must be able to catch overclaiming ---------------------------------


def test_self_authored_benefit_claim_is_caught(ledger):
    """The exact Paper VI retraction pattern, injected."""
    bad = copy.deepcopy(ledger)
    for entry in bad["mechanics"]:
        if entry["mechanic_id"] == "MECH-TRANSPORT-APPLICABILITY-CONTRACT":
            entry["benefit"] = "DEMONSTRATED"  # provenance stays SELF_AUTHORED
    problems = integrity_problems(bad)
    assert any("SELF_AUTHORED" in p for p in problems)


def test_benefit_without_an_ablation_arm_is_caught(ledger):
    """A benefit needs something to be better *than*."""
    bad = copy.deepcopy(ledger)
    for entry in bad["mechanics"]:
        if entry["mechanic_id"] == "MECH-BOUNDED-SATURATION":
            entry["benefit"] = "DEMONSTRATED"
            entry["outcome_provenance"] = "EXTERNAL"
            entry["ablation_arm"] = None
    problems = integrity_problems(bad)
    assert any("ablation_arm=None" in p for p in problems)


def test_mechanized_without_witness_is_caught(ledger):
    bad = copy.deepcopy(ledger)
    for entry in bad["mechanics"]:
        if entry["mechanic_id"] == "MECH-AUTHORITY-NON-ESCALATION":
            entry["non_vacuity_witness"] = None
    problems = integrity_problems(bad)
    assert any("non-vacuity witness" in p for p in problems)


def test_unanchored_cost_claim_is_caught(ledger):
    bad = copy.deepcopy(ledger)
    for entry in bad["mechanics"]:
        if entry["mechanic_id"] == "MECH-FAIL-CLOSED-GOVERNED-ACCEPTANCE":
            entry["outcome_provenance"] = "UNKNOWN"
    problems = integrity_problems(bad)
    assert any("unfalsifiable" in p for p in problems)


def test_a_legitimate_benefit_claim_is_accepted(ledger):
    """The no-alarm case: the ledger must be able to record a real benefit.

    A checker that rejected every benefit claim would be as useless as one that
    accepted every claim — it would make the benefit column unreachable by
    construction, which is exactly the vacuity trap it exists to prevent.
    """
    good = copy.deepcopy(ledger)
    for entry in good["mechanics"]:
        if entry["mechanic_id"] == "MECH-BOUNDED-SATURATION":
            entry["benefit"] = "DEMONSTRATED"
            entry["outcome_provenance"] = "EXTERNAL"
            entry["ablation_arm"] = "uniform-budget search with no saturation rule"
    assert integrity_problems(good) == ()
    assert programme_summary(good)["supports_working_mechanism_claim"] is True


def test_not_attempted_is_not_reported_as_no_benefit(ledger):
    """'Unmeasured' and 'measured and absent' are different, and stay different."""
    statuses = {r.benefit for r in rows(ledger)}
    assert BenefitStatus.NOT_ATTEMPTED in statuses
    assert BenefitStatus.NOT_ATTEMPTED is not BenefitStatus.REFUTED
    summary = programme_summary(ledger)
    assert summary["benefit_not_attempted"] > 0
    assert summary["benefit_refuted"] == 1
