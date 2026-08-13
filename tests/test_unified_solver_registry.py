from __future__ import annotations

from dataclasses import replace

from rakl.formal_contracts import AuthorityEffect, METHOD_SURFACES
from rakl.unified_solver_registry import UNIFIED_SOLVER_MECHANICS, validate_unified_solver_registry


def test_unified_solver_registry_is_scoped_owned_and_proposal_only():
    report = validate_unified_solver_registry()
    assert report.valid
    assert report.duplicate_ids == ()
    assert report.duplicate_modules == ()
    assert report.problems == ()
    assert report.grants_scientific_authority is False
    assert report.establishes_global_framework_completeness is False
    for spec in UNIFIED_SOLVER_MECHANICS:
        assert spec.owner_surface in METHOD_SURFACES
        assert spec.authority_effect in {AuthorityEffect.NONE, AuthorityEffect.PROPOSAL_ONLY}
        assert spec.test_paths
        assert spec.empirical_open_coordinates


def test_registry_rejects_unknown_owner_surface():
    bad = replace(UNIFIED_SOLVER_MECHANICS[0], owner_surface="invented_global_brain")
    report = validate_unified_solver_registry((bad,))
    assert not report.valid
    assert "owner_surface_not_canonical" in report.problems[0][1]


def test_registry_rejects_sidecar_that_mints_scoped_certificate_authority():
    bad = replace(UNIFIED_SOLVER_MECHANICS[0], authority_effect=AuthorityEffect.SCOPED_CERTIFICATE_ONLY)
    report = validate_unified_solver_registry((bad,))
    assert not report.valid
    assert "solver_sidecar_authority_too_strong" in report.problems[0][1]
