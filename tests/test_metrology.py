from __future__ import annotations

from rakl.metrology import (
    AffineTransform,
    FirstOrderTransform,
    MetrologyVerdict,
    combine_independent_standard_uncertainties,
    propagate_affine,
    propagate_first_order_covariance,
)


def test_affine_transform_executes_exact_mean_and_covariance_transport():
    transform = AffineTransform(
        transform_id="scale_shift",
        matrix=((2.0, 0.0), (0.0, -1.0)),
        offset=(1.0, 3.0),
        declared_before_results=True,
        invertibility_required=True,
    )
    report = propagate_affine(
        (2.0, 4.0),
        ((1.0, 0.5), (0.5, 4.0)),
        transform,
    )
    assert report.verdict is MetrologyVerdict.EXECUTED
    assert report.mean == (5.0, -1.0)
    assert report.covariance == ((4.0, -1.0), (-1.0, 4.0))
    assert report.grants_scientific_authority is False
    assert report.grants_mechanism_authority is False


def test_affine_dimension_mismatch_rejects():
    transform = AffineTransform(
        transform_id="bad",
        matrix=((1.0, 0.0),),
        offset=(0.0,),
        declared_before_results=True,
    )
    report = propagate_affine((1.0,), ((1.0,),), transform)
    assert report.verdict is MetrologyVerdict.REJECT
    assert "mean_dimension_mismatch" in report.reasons


def test_non_psd_covariance_rejects():
    transform = AffineTransform(
        transform_id="identity",
        matrix=((1.0, 0.0), (0.0, 1.0)),
        offset=(0.0, 0.0),
        declared_before_results=True,
    )
    report = propagate_affine((0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)), transform)
    assert report.verdict is MetrologyVerdict.REJECT
    assert "covariance_not_positive_semidefinite" in report.reasons


def test_root_sum_square_requires_explicit_independence():
    verdict, value, _ = combine_independent_standard_uncertainties(
        (3.0, 4.0), independence_witness=True
    )
    assert verdict is MetrologyVerdict.EXECUTED
    assert value == 5.0

    verdict, value, reasons = combine_independent_standard_uncertainties(
        (3.0, 4.0), independence_witness=False
    )
    assert verdict is MetrologyVerdict.REJECT
    assert value is None
    assert "root_sum_square_not_licensed_for_correlated_inputs" in reasons


def test_first_order_delta_method_is_explicitly_local():
    transform = FirstOrderTransform(
        transform_id="jac",
        jacobian=((2.0, 1.0),),
        declared_before_results=True,
        differentiability_witness=True,
    )
    report = propagate_first_order_covariance(
        ((1.0, 0.0), (0.0, 4.0)),
        transform,
    )
    assert report.verdict is MetrologyVerdict.EXECUTED
    assert report.covariance == ((8.0,),)
    assert any("local_linearization" in reason for reason in report.reasons)
