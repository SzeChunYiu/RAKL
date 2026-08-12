import pytest

from scripts.tcsq_sq1_oracle_upper_bound import (
    PAPER2_CONFIRMATORY_SEED_DO_NOT_USE,
    oracle_quotient,
    run_sq1,
    verify_oracle_quotient,
)
from rakl.objective_transfer_benchmark import generate, verify


def test_oracle_quotient_matches_original_verifier_on_fresh_development_panel() -> None:
    result = run_sq1(seed=20260812972, n_per_cell=2)
    assert result["paper2_confirmatory_seed_used"] is False
    assert result["exact_original_verifier_agreement"] == 1.0
    assert set(result["family_agreement"]) == {"flow", "logic", "state", "units"}
    assert all(value == 1.0 for value in result["family_agreement"].values())
    assert result["aggregate_public_primitive_reduction_fraction"] > 0
    assert result["mean_raw_semantic_text_tokens_excluded_from_oracle_quotient"] > 0


def test_oracle_quotient_never_reads_hidden_item_type_or_perturbation_for_decision() -> None:
    tasks = generate(20260812973, n_per_cell=1, include_controls=True)
    for task in tasks:
        quotient = oracle_quotient(task)
        assert "item_type" not in quotient
        assert "perturbation" not in quotient
        assert verify_oracle_quotient(quotient) is verify(task).decision


def test_sq1_refuses_paper2_confirmatory_seed() -> None:
    with pytest.raises(ValueError, match="confirmatory seed"):
        run_sq1(seed=PAPER2_CONFIRMATORY_SEED_DO_NOT_USE, n_per_cell=1)
