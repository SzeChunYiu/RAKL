from rakl.training_policy_authority import _phase2_cost_allows_active_default


def _receipt(e_gpu: float, d_gpu: float) -> dict:
    return {
        "arms": {
            "E_ADAPTIVE_RAKL_STRUCTURAL": {"resources": {"gpu_seconds": e_gpu}},
            "D_STATIC_RAKL_STRUCTURAL": {"resources": {"gpu_seconds": d_gpu}},
        }
    }


def test_registered_cost_boundary_recomputed_from_resources():
    assert _phase2_cost_allows_active_default(_receipt(20.0, 10.0)) is True
    assert _phase2_cost_allows_active_default(_receipt(20.0001, 10.0)) is False


def test_invalid_or_zero_parent_cost_fails_closed():
    assert _phase2_cost_allows_active_default(None) is False
    assert _phase2_cost_allows_active_default(_receipt(1.0, 0.0)) is False
    assert _phase2_cost_allows_active_default(_receipt(-1.0, 1.0)) is False
