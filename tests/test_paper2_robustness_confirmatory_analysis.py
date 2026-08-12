from scripts.paper2_robustness_confirmatory import (
    CONFIRMATORY_SEED,
    FROZEN_LEXICAL_THRESHOLD,
    _two_sided_sign_p,
    summarize,
)


def test_sign_test_all_six_positive_is_registered_p_value() -> None:
    assert _two_sided_sign_p(6, 6) == 0.03125
    assert _two_sided_sign_p(5, 6) == 0.21875


def test_confirmatory_analysis_shape_on_nonregistered_test_seed() -> None:
    result = summarize(
        seed=20260812991,
        n_per_cell=1,
        bootstrap_reps=200,
        bootstrap_seed=991,
    )
    assert result["seed"] != CONFIRMATORY_SEED
    assert result["development_selected_lexical_threshold"] == FROZEN_LEXICAL_THRESHOLD
    assert set(result["family"]) == {
        "algorithm_invariants",
        "causal_transport",
        "linear_systems",
        "local_global_gluing",
        "optimization",
        "pgm_dseparation",
    }
    assert set(result["arms"]) == {"lexical", "relational", "mechanism", "twin", "full"}
    assert len(result["primary_paired_binary_brier"]["bootstrap_95pct"]) == 2
    assert isinstance(result["broad_known_world_robustness_supported"], bool)
    assert isinstance(result["gate_reasons"], list)
