"""Unit tests for the Orion metric layer (``orion.metrics`` / ``rakl.metrics``)."""

from __future__ import annotations

import pytest

from rakl.metrics import (
    LICENSED,
    GateRecord,
    authority_coverage,
    gate_false_accept,
    mastery_vector,
    parse_exposure_rows,
    retention_ok,
    saturation_epoch,
    saturation_level,
)
from rakl.metrics.trajectory import Trajectory
from rakl.training_projection import MasteryCoordinate, StructuralMasteryEstimate


def _estimate(values):
    """Build a StructuralMasteryEstimate from a coordinate->value mapping."""

    coordinate_values = tuple(
        (coord, values.get(coord)) for coord in MasteryCoordinate
    )
    return StructuralMasteryEstimate(
        structure_id="S1",
        model_checkpoint_hash="ckpt",
        probe_family_hash="probe",
        coordinate_values=coordinate_values,
        measured_case_ids=("case-1",),
        frozen_before_allocation=True,
    )


# --------------------------------------------------------------------------- #
# mastery_vector
# --------------------------------------------------------------------------- #
def test_mastery_vector_preserves_none_not_zero():
    est = _estimate({MasteryCoordinate.PRINCIPLE: 0.8})
    vec = mastery_vector(est)
    assert vec[MasteryCoordinate.PRINCIPLE] == 0.8
    # Unmeasured coordinates stay None, never coerced to 0.0.
    assert vec[MasteryCoordinate.TRANSFER] is None
    assert set(vec) == set(MasteryCoordinate)


# --------------------------------------------------------------------------- #
# saturation level / epoch
# --------------------------------------------------------------------------- #
def test_saturation_level_is_latest_gain_clamped():
    assert saturation_level([0.4, 0.2, 0.05]) == 0.05
    # Negative observed gain clamps to 0.0 (cannot be less than saturated).
    assert saturation_level([0.4, -0.1]) == 0.0


def test_saturation_level_empty_raises():
    with pytest.raises(ValueError):
        saturation_level([])


def test_saturation_epoch_first_below_epsilon():
    gains = [0.5, 0.3, 0.12, 0.04, 0.01]
    # First gain strictly below 0.05 is index 3 (value 0.04).
    assert saturation_epoch(gains, epsilon=0.05) == 3


def test_saturation_epoch_never_saturates_returns_none():
    gains = [0.5, 0.4, 0.3, 0.2]
    assert saturation_epoch(gains, epsilon=0.05) is None


def test_saturation_epoch_saturates_immediately():
    assert saturation_epoch([0.0, 0.9], epsilon=0.05) == 0


# --------------------------------------------------------------------------- #
# retention floor (hard constraint)
# --------------------------------------------------------------------------- #
def test_retention_floor():
    assert retention_ok(0.9, floor=0.8) is True
    assert retention_ok(0.8, floor=0.8) is True  # floor is inclusive
    assert retention_ok(0.79, floor=0.8) is False
    # Unmeasured retention fails closed.
    assert retention_ok(None, floor=0.8) is False


# --------------------------------------------------------------------------- #
# authority coverage (non-compensatory)
# --------------------------------------------------------------------------- #
def test_authority_coverage_non_compensatory_blocking_axis():
    status = {
        "G": LICENSED,
        "R": LICENSED,
        "M": LICENSED,
        "I": "PENDING",  # one load-bearing axis not licensed
        "D": LICENSED,
    }
    cov = authority_coverage(status)
    assert cov.coverage == pytest.approx(4 / 5)
    assert cov.blocking_axes == ("I",)
    # High coverage does NOT compensate: the claim is still blocked.
    assert cov.fully_licensed is False


def test_authority_coverage_all_licensed():
    cov = authority_coverage({"G": LICENSED, "R": LICENSED})
    assert cov.coverage == 1.0
    assert cov.blocking_axes == ()
    assert cov.fully_licensed is True


def test_authority_coverage_empty_raises():
    with pytest.raises(ValueError):
        authority_coverage({})


# --------------------------------------------------------------------------- #
# gate false-accept
# --------------------------------------------------------------------------- #
def test_gate_false_accept_on_synthetic_records():
    records = [
        GateRecord(pred="ACCEPT", gold="REJECT"),  # false accept
        GateRecord(pred="REJECT", gold="REJECT"),  # correct reject
        GateRecord(pred="REJECT", gold="REJECT"),  # correct reject
        GateRecord(pred="ACCEPT", gold="ACCEPT"),  # not conditioned on
    ]
    # Among 3 gold=REJECT records, 1 was wrongly accepted -> 1/3.
    assert gate_false_accept(records) == pytest.approx(1 / 3)


def test_gate_false_accept_accepts_mappings():
    records = [
        {"pred": "ACCEPT", "gold": "REJECT"},
        {"pred": "REJECT", "gold": "REJECT"},
    ]
    assert gate_false_accept(records) == pytest.approx(0.5)


def test_gate_false_accept_undefined_without_rejects_raises():
    with pytest.raises(ValueError):
        gate_false_accept([GateRecord(pred="ACCEPT", gold="ACCEPT")])


# --------------------------------------------------------------------------- #
# trajectory parsing
# --------------------------------------------------------------------------- #
def _rows():
    rows = []
    for exposure, principle, composition in [
        (1, 0.30, 0.10),
        (2, 0.55, 0.20),
        (4, 0.80, 0.45),
        (8, 0.95, 0.70),
    ]:
        rows.append({"family": "F", "exposure_count": exposure, "probe_kind": "p",
                     "coordinate": "principle", "accuracy": principle, "n": 20})
        rows.append({"family": "F", "exposure_count": exposure, "probe_kind": "p",
                     "coordinate": "composition", "accuracy": composition, "n": 20})
    return rows


def test_trajectory_missing_coordinate_is_none():
    traj = parse_exposure_rows(_rows())["F"]
    assert traj.exposures == (1, 2, 4, 8)
    # Boundary was never measured -> all None, not 0.0.
    assert traj.mastery_series(MasteryCoordinate.BOUNDARY) == (None, None, None, None)
    assert traj.mastery_series(MasteryCoordinate.PRINCIPLE)[0] == pytest.approx(0.30)
    # Marginal gain: first is None, then diffs.
    gains = traj.marginal_gain_series(MasteryCoordinate.PRINCIPLE)
    assert gains[0] is None
    assert gains[1] == pytest.approx(0.25)
    assert not traj.is_empty


def test_trajectory_n_weighted_merge_of_probe_kinds():
    rows = [
        {"family": "F", "exposure_count": 1, "probe_kind": "a",
         "coordinate": "principle", "accuracy": 0.0, "n": 10},
        {"family": "F", "exposure_count": 1, "probe_kind": "b",
         "coordinate": "principle", "accuracy": 1.0, "n": 30},
    ]
    traj = parse_exposure_rows(rows)["F"]
    # n-weighted mean: (0*10 + 1*30)/40 = 0.75
    assert traj.mastery_series(MasteryCoordinate.PRINCIPLE)[0] == pytest.approx(0.75)
    assert traj.total_n == 40


# --------------------------------------------------------------------------- #
# figure rendering
# --------------------------------------------------------------------------- #
def _hand_built_trajectory() -> Trajectory:
    exposures = (1, 2, 4, 8)
    order = tuple(MasteryCoordinate)
    mastery = {}
    sample_n = {}
    for i, coord in enumerate(order):
        base = 0.2 + 0.1 * i
        mastery[coord] = tuple(min(1.0, base + 0.2 * k) for k in range(len(exposures)))
        sample_n[coord] = tuple(20 for _ in exposures)
    return Trajectory(family="F", exposures=exposures, mastery=mastery, sample_n=sample_n)


def test_render_trajectory_writes_nonempty_pdf(tmp_path):
    pytest.importorskip("matplotlib")
    from rakl.metrics import render_trajectory

    traj = _hand_built_trajectory()
    stem = tmp_path / "trajectory"
    written = render_trajectory(traj, stem, title="unit test run", seed=7, n=80)
    pdf = stem.with_suffix(".pdf")
    png = stem.with_suffix(".png")
    assert pdf in written and png in written
    assert pdf.exists() and pdf.stat().st_size > 0
    assert png.exists() and png.stat().st_size > 0


def test_render_trajectory_refuses_empty(tmp_path):
    pytest.importorskip("matplotlib")
    from rakl.metrics import render_trajectory

    order = tuple(MasteryCoordinate)
    empty = Trajectory(
        family="F",
        exposures=(1, 2),
        mastery={c: (None, None) for c in order},
        sample_n={c: (0, 0) for c in order},
    )
    with pytest.raises(ValueError):
        render_trajectory(empty, tmp_path / "x", title="t", seed=1, n=10)
