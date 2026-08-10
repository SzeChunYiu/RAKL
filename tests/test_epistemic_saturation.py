from rakl.epistemic_saturation import (
    EpistemicGrowthVector,
    SaturationBasis,
    SaturationRound,
    SaturationStatus,
    audit_bounded_epistemic_saturation,
)


def _basis() -> SaturationBasis:
    return SaturationBasis(
        basis_id="epistemic-mechanics-paper-v1",
        scope="long-form epistemic-mechanics paper and supporting framework",
        identity_policy_id="claim-mechanism-evidence-v1",
        route_family_version="owmd-v1",
        novelty_policy_id="nearest-work-equivalence-v1",
        evidence_policy_id="typed-authority-v1",
    )


def _round(round_id: str, *, growth: EpistemicGrowthVector | None = None, **overrides) -> SaturationRound:
    values = dict(
        round_id=round_id,
        basis_fingerprint=_basis().fingerprint,
        growth=growth or EpistemicGrowthVector(),
        bounded_discovery_closed=True,
        route_coverage_stable=True,
        omission_audit_passed=True,
        nearest_work_audit_passed=True,
        freshness_cutoff="2026-08-10",
        blocking_fibers=(),
        representation_only_changes=0,
    )
    values.update(overrides)
    return SaturationRound(**values)


def test_saturation_requires_repeated_zero_substantive_gain():
    rounds = (
        _round("R1", growth=EpistemicGrowthVector(mechanisms_added=2)),
        _round("R2"),
        _round("R3"),
    )
    report = audit_bounded_epistemic_saturation(
        rounds,
        basis=_basis(),
        required_consecutive_flat_rounds=2,
        required_freshness_cutoff="2026-08-10",
    )
    assert report.status is SaturationStatus.BOUNDED_SATURATED
    assert report.consecutive_flat_rounds == 2
    assert report.absolute_complete is False


def test_any_new_knowledge_reopens_saturation():
    rounds = (
        _round("R1"),
        _round("R2"),
        _round("R3", growth=EpistemicGrowthVector(contradictions_or_counterexamples_added=1)),
    )
    report = audit_bounded_epistemic_saturation(rounds, basis=_basis())
    assert report.status is SaturationStatus.OPEN
    assert report.consecutive_flat_rounds == 0
    assert "insufficient_consecutive_substantive_flat_rounds" in report.reasons


def test_representation_only_edits_do_not_manufacture_epistemic_growth():
    rounds = (
        _round("R1", representation_only_changes=17),
        _round("R2", representation_only_changes=4),
    )
    report = audit_bounded_epistemic_saturation(rounds, basis=_basis())
    assert report.status is SaturationStatus.BOUNDED_SATURATED


def test_blocking_fiber_or_unstable_routes_keep_state_open():
    rounds = (
        _round("R1"),
        _round("R2", blocking_fibers=("fiber:missing-prior-art",), route_coverage_stable=False),
    )
    report = audit_bounded_epistemic_saturation(rounds, basis=_basis())
    assert report.status is SaturationStatus.OPEN
    assert "R2:blocking_fibers_open" in report.reasons
    assert "R2:route_coverage_unstable" in report.reasons


def test_saturation_is_invalid_across_basis_change():
    other = SaturationBasis(
        basis_id="different",
        scope="different scope",
        identity_policy_id="claim-mechanism-evidence-v1",
        route_family_version="owmd-v1",
        novelty_policy_id="nearest-work-equivalence-v1",
        evidence_policy_id="typed-authority-v1",
    )
    rounds = (
        _round("R1"),
        SaturationRound(
            round_id="R2",
            basis_fingerprint=other.fingerprint,
            growth=EpistemicGrowthVector(),
            bounded_discovery_closed=True,
            route_coverage_stable=True,
            omission_audit_passed=True,
            nearest_work_audit_passed=True,
            freshness_cutoff="2026-08-10",
        ),
    )
    report = audit_bounded_epistemic_saturation(rounds, basis=_basis())
    assert report.status is SaturationStatus.INVALID_BASIS
    assert report.reasons == ("saturation_basis_fingerprint_changed",)


def test_freshness_horizon_can_expire_a_flat_certificate():
    rounds = (
        _round("R1", freshness_cutoff="2026-08-01"),
        _round("R2", freshness_cutoff="2026-08-01"),
    )
    report = audit_bounded_epistemic_saturation(
        rounds,
        basis=_basis(),
        required_freshness_cutoff="2026-08-10",
    )
    assert report.status is SaturationStatus.OPEN
    assert "R2:freshness_cutoff_stale" in report.reasons
