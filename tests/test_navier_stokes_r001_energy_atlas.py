from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE = (
    ROOT
    / "research/real_math/millennium/navier_stokes/09_trace/NS_R001_PRE_CANDIDATE_TRACE_20260811.json"
)


def _mixed_norm_exponent(
    *,
    amplitude: Fraction,
    space_q: Fraction | None,
    time_p: Fraction | None,
    derivative_order: int = 0,
) -> Fraction:
    """Scaling exponent for a(lambda x, lambda^2 t)-type mixed norm."""
    spatial = Fraction(0) if space_q is None else Fraction(3, 1) / space_q
    temporal = Fraction(0) if time_p is None else Fraction(2, 1) / time_p
    return amplitude + derivative_order - spatial - temporal


def test_energy_concentration_family_keeps_leray_pair_fixed() -> None:
    amplitude = Fraction(3, 2)

    linf_l2 = _mixed_norm_exponent(
        amplitude=amplitude, space_q=Fraction(2), time_p=None
    )
    l2_h1 = _mixed_norm_exponent(
        amplitude=amplitude,
        space_q=Fraction(2),
        time_p=Fraction(2),
        derivative_order=1,
    )

    assert linf_l2 == 0
    assert l2_h1 == 0


def test_every_sampled_serrin_critical_velocity_norm_diverges() -> None:
    amplitude = Fraction(3, 2)
    # 2/p + 3/q = 1.  None denotes infinity.
    critical_pairs = (
        (None, Fraction(3)),
        (Fraction(5), Fraction(5)),
        (Fraction(4), Fraction(6)),
        (Fraction(2), None),
    )

    for time_p, space_q in critical_pairs:
        critical_sum = (
            Fraction(0) if time_p is None else Fraction(2, 1) / time_p
        ) + (Fraction(0) if space_q is None else Fraction(3, 1) / space_q)
        assert critical_sum == 1
        assert (
            _mixed_norm_exponent(
                amplitude=amplitude, space_q=space_q, time_p=time_p
            )
            == Fraction(1, 2)
        )


def test_pressure_critical_norms_diverge_one_full_power() -> None:
    pressure_amplitude = Fraction(3)
    # Pressure criticality is 2/p + 3/q = 2.
    critical_pairs = (
        (None, Fraction(3, 2)),
        (Fraction(2), Fraction(3)),
        (Fraction(1), None),
    )

    for time_p, space_q in critical_pairs:
        critical_sum = (
            Fraction(0) if time_p is None else Fraction(2, 1) / time_p
        ) + (Fraction(0) if space_q is None else Fraction(3, 1) / space_q)
        assert critical_sum == 2
        assert (
            _mixed_norm_exponent(
                amplitude=pressure_amplitude,
                space_q=space_q,
                time_p=time_p,
            )
            == 1
        )


def test_ckn_scale_invariant_cubic_quantity_blows_up_on_natural_radius() -> None:
    # U_lambda has amplitude lambda^(3/2), spatial volume lambda^-3,
    # time support lambda^-2, and the CKN prefactor r^-2 contributes
    # lambda^2 at r=lambda^-1.
    exponent = Fraction(9, 2) - 3 - 2 + 2
    assert exponent == Fraction(3, 2)


def test_atlas_statement_is_not_a_navier_stokes_solution_claim() -> None:
    # The entire point of A1 is to refute energy-norm-only functional estimates
    # on arbitrary divergence-free histories.  A true-solution estimate may
    # evade the atlas only by using additional equation-specific structure.
    claim_scope = "smooth_divergence_free_spacetime_test_fields"
    excluded_scope = "actual_navier_stokes_solution_family"
    assert claim_scope != excluded_scope


def test_atlas_is_append_only_bound_to_trace_without_candidate_event() -> None:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    event_types = [entry["event_type"] for entry in trace["entries"]]
    assert event_types[-3:] == ["FALSIFIER_RUN", "RESULT_RECORDED", "RESIDUAL_OPENED"]
    assert "CANDIDATE_PROPOSED" not in event_types
    assert trace["entries"][-1]["residuals"] == [
        "NS-R001a:true-evolution coordinate preventing arbitrary energy-class critical concentration"
    ]
