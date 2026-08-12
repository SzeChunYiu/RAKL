import pytest

from scripts.tcsq_sq2_intervention_fidelity import (
    EXACT_REQUIRED_PATHS,
    PAPER2_CONFIRMATORY_SEED_DO_NOT_USE,
    run_sq2,
)


def test_finite_interventions_recover_exact_verifier_dependencies_on_fresh_panel() -> None:
    result = run_sq2(seed=20260812982, n_per_cell=2)
    assert result["paper2_confirmatory_seed_used"] is False
    assert result["aggregate"]["all_family_exact_dependency_recovery"] is True
    assert result["aggregate"]["false_positive"] == 0
    assert result["aggregate"]["false_negative"] == 0
    assert result["aggregate"]["precision"] == 1.0
    assert result["aggregate"]["recall"] == 1.0
    assert result["aggregate"]["specificity"] == 1.0
    for family, expected in EXACT_REQUIRED_PATHS.items():
        assert set(result["family"][family]["discovered_sensitive"]) == set(expected)


def test_sq2_refuses_paper2_confirmatory_seed() -> None:
    with pytest.raises(ValueError, match="confirmatory seed"):
        run_sq2(seed=PAPER2_CONFIRMATORY_SEED_DO_NOT_USE, n_per_cell=1)
