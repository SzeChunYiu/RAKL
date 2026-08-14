"""Known-answer and hostile worlds for the oracle-ceiling admissibility gate.

Each of the sealed packet's ``minimal_counterexamples`` appears as a test, plus
hostile cases asserting the direction-of-license rules: a policy (lower) bound
may never license INADMISSIBLE, an upper bound may never license ADMISSIBLE,
and an uncomputable oracle fails closed.
"""

from __future__ import annotations

import pytest

from rakl.instrument_admissibility import (
    AdmissibilityVerdict,
    BoundKind,
    CeilingBound,
    CeilingEvidence,
    FrozenAdmissibilityDeclaration,
    OracleComputability,
    decide_instrument_admissibility,
)


def declaration(*, mde: float = 0.05, kappa: float = 1.2) -> FrozenAdmissibilityDeclaration:
    return FrozenAdmissibilityDeclaration(
        instrument_id="TEST_INSTRUMENT",
        registered_primary_metric="E_minus_D_balanced_mastery",
        registered_minimum_detectable_effect=mde,
        frozen_kappa=kappa,
        declared_on="2026-08-14",
        rationale="test freeze",
    )


def evidence(
    bounds,
    *,
    computability: OracleComputability = OracleComputability.COMPUTABLE,
    equal_budget: bool = True,
    instrument_id: str = "TEST_INSTRUMENT",
) -> CeilingEvidence:
    return CeilingEvidence(
        instrument_id=instrument_id,
        oracle_computability=computability,
        equal_budget_verified=equal_budget,
        reference_parent_arm_id="D_STATIC_STRUCTURAL",
        bounds=tuple(bounds),
    )


def bound(kind: BoundKind, value: float, bound_id: str = "b") -> CeilingBound:
    return CeilingBound(bound_id=bound_id, kind=kind, value=value, method="test")


# --- packet minimal counterexamples -------------------------------------------------


def test_degenerate_zero_headroom_is_inadmissible() -> None:
    """An instrument whose every arm is forced to one allocation has exact ceiling 0."""
    decision = decide_instrument_admissibility(
        declaration(), evidence([bound(BoundKind.EXACT, 0.0, "exact_zero")])
    )
    assert decision.verdict is AdmissibilityVerdict.INADMISSIBLE
    assert decision.licensing_bound_kind is BoundKind.EXACT
    assert not decision.licenses_comparison_execution


def test_genuine_headroom_is_admissible_via_lower_bound() -> None:
    decision = decide_instrument_admissibility(
        declaration(),
        evidence(
            [
                bound(BoundKind.LOWER_BOUND, 0.11, "constructive"),
                bound(BoundKind.UPPER_BOUND, 0.30, "relaxation"),
            ]
        ),
    )
    assert decision.verdict is AdmissibilityVerdict.ADMISSIBLE
    assert decision.licensing_bound_id == "constructive"
    assert decision.licensing_bound_kind is BoundKind.LOWER_BOUND
    assert decision.licenses_comparison_execution


def test_uncomputable_oracle_fails_closed_never_admissible() -> None:
    decision = decide_instrument_admissibility(
        declaration(),
        evidence(
            [bound(BoundKind.LOWER_BOUND, 1.0, "huge")],
            computability=OracleComputability.UNCOMPUTABLE,
        ),
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK
    assert any("fail_closed" in r for r in decision.reasons)


def test_tight_ci_low_ceiling_is_inadmissible_regardless_of_power() -> None:
    """The observed Paper IV case: CIs ~0.0016 wide, upper bound 0.02457 vs 0.05 gate."""
    decision = decide_instrument_admissibility(
        declaration(mde=0.05, kappa=1.2),
        evidence(
            [
                CeilingBound(
                    "tier1_greedy_policy",
                    BoundKind.LOWER_BOUND,
                    0.00148,
                    "greedy oracle policy",
                    bootstrap_ci=(0.00135, 0.00160),
                ),
                bound(BoundKind.LOWER_BOUND, 0.004457, "tier2_constructive"),
                bound(BoundKind.UPPER_BOUND, 0.024571, "tier3_harm_free_relaxation"),
            ]
        ),
    )
    assert decision.verdict is AdmissibilityVerdict.INADMISSIBLE
    assert decision.licensing_bound_id == "tier3_harm_free_relaxation"
    # INADMISSIBLE here is kappa-insensitive down to 0.024571/0.05 ~ 0.49.
    assert "0.491" in decision.verdict_kappa_range


def test_ceiling_just_above_mde_but_below_kappa_mde_is_inadmissible() -> None:
    """kappa is frozen; the verdict may not be rescued by lowering it after the ceiling."""
    decision = decide_instrument_admissibility(
        declaration(mde=0.05, kappa=1.2),
        evidence([bound(BoundKind.EXACT, 0.055, "exact_marginal")]),
    )
    assert decision.verdict is AdmissibilityVerdict.INADMISSIBLE


def test_loose_bounds_straddling_threshold_cannot_check() -> None:
    """Lower below threshold, upper above it: too loose to decide either way."""
    decision = decide_instrument_admissibility(
        declaration(mde=0.05, kappa=1.2),
        evidence(
            [
                bound(BoundKind.LOWER_BOUND, 0.02, "low"),
                bound(BoundKind.UPPER_BOUND, 0.50, "high"),
            ]
        ),
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK
    assert any("bounds_too_loose" in r for r in decision.reasons)


# --- direction-of-license hostile cases ---------------------------------------------


def test_lower_bound_alone_never_licenses_inadmissible() -> None:
    """A tiny policy score does not prove the instrument lacks headroom."""
    decision = decide_instrument_admissibility(
        declaration(), evidence([bound(BoundKind.LOWER_BOUND, 1e-6, "tiny_policy")])
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


def test_upper_bound_alone_never_licenses_admissible() -> None:
    """A huge upper bound says nothing about achievability."""
    decision = decide_instrument_admissibility(
        declaration(), evidence([bound(BoundKind.UPPER_BOUND, 10.0, "loose_upper")])
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


def test_inconsistent_bounds_cannot_check() -> None:
    decision = decide_instrument_admissibility(
        declaration(),
        evidence(
            [
                bound(BoundKind.LOWER_BOUND, 0.5, "lower"),
                bound(BoundKind.UPPER_BOUND, 0.1, "upper"),
            ]
        ),
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK
    assert any("inconsistent_bounds" in r for r in decision.reasons)


def test_unequal_budget_is_out_of_scope() -> None:
    decision = decide_instrument_admissibility(
        declaration(), evidence([bound(BoundKind.EXACT, 0.5, "e")], equal_budget=False)
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


def test_instrument_identity_mismatch_cannot_check() -> None:
    decision = decide_instrument_admissibility(
        declaration(),
        evidence([bound(BoundKind.EXACT, 0.5, "e")], instrument_id="OTHER_INSTRUMENT"),
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


def test_no_bounds_cannot_check() -> None:
    decision = decide_instrument_admissibility(declaration(), evidence([]))
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


def test_non_finite_bound_cannot_check() -> None:
    decision = decide_instrument_admissibility(
        declaration(), evidence([bound(BoundKind.EXACT, float("nan"), "nan")])
    )
    assert decision.verdict is AdmissibilityVerdict.CANNOT_CHECK


# --- freeze discipline ---------------------------------------------------------------


@pytest.mark.parametrize("mde", [0.0, -0.05, float("nan"), float("inf")])
def test_invalid_mde_fails_at_freeze_time(mde: float) -> None:
    with pytest.raises(ValueError):
        declaration(mde=mde)


@pytest.mark.parametrize("kappa", [0.0, -1.0, float("nan")])
def test_invalid_kappa_fails_at_freeze_time(kappa: float) -> None:
    with pytest.raises(ValueError):
        declaration(kappa=kappa)


def test_declaration_hash_is_stable_and_content_bound() -> None:
    a = declaration()
    b = declaration()
    assert a.content_sha256 == b.content_sha256
    assert a.content_sha256 != declaration(kappa=1.3).content_sha256


# --- authority boundary --------------------------------------------------------------


def test_no_verdict_grants_scientific_authority_or_outcome_upgrade() -> None:
    for bounds, kwargs in [
        ([bound(BoundKind.EXACT, 0.5, "e")], {}),
        ([bound(BoundKind.EXACT, 0.0, "z")], {}),
        ([], {}),
    ]:
        decision = decide_instrument_admissibility(declaration(), evidence(bounds, **kwargs))
        assert decision.grants_scientific_authority is False
        assert decision.upgradeable_by_outcome_access is False
