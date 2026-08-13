"""#544: the promotion gate fails closed on telemetry-incomplete efficiency claims.

Acceptance (issue #544): "The promotion gate/controller may not emit an
unconditional positive efficiency verdict from an artifact whose required
telemetry for that claim class is incomplete."

Tests:
  * envelope-only artifact (positive net, zero telemetry) is NOT promoted for an
    EFFICIENCY claim.
  * a PROSPECTIVE run with unconfigured collectors is blocked
    (KEEP_PROPOSAL_ONLY) -- it must fail before outcome generation counts.
  * a CORRECTNESS promotion is NOT blocked by the absence of GPU/token telemetry.
  * an economic/cost promotion with the charged-cost field stripped is blocked.
  * the LIVE efficiency promotions are traceable to COMPLETE telemetry (no
    regression); path_quotient stays PROMOTE_CONDITIONALLY with COMPLETE telemetry.
"""
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from promotion_gate import verdict_for, CANDIDATES  # noqa: E402


@pytest.fixture
def repo_tmp():
    d = Path(tempfile.mkdtemp(prefix="telgate_", dir=str(ROOT)))
    yield d
    shutil.rmtree(str(d), ignore_errors=True)


def _spec_into(repo_tmp, candidate_name):
    spec = copy.deepcopy(CANDIDATES[candidate_name])
    spec["artifact"] = repo_tmp / "artifact.json"
    return spec


def _efficiency_complete_artifact():
    """An EFFICIENCY artifact with complete required telemetry + a positive net."""
    return {
        "grants_scientific_authority": False,
        "net_saving_mean": 70.18,
        "net_saving_ci95": [4.68, 145.13],
        "n_instances_per_cell": 200,   # sample
        "seed": 461,                    # seed
        "mean_witnesses_registered": 1.73,  # measured_quantity + verification_cost
    }


# --------------------------------------------------------------------------- #
# envelope-only / prospective: the gate must NOT promote
# --------------------------------------------------------------------------- #
def test_envelope_only_positive_net_not_promoted(repo_tmp):
    spec = _spec_into(repo_tmp, "path_equivalence_quotient")
    spec["artifact"].write_text(json.dumps({
        "grants_scientific_authority": False,
        "net_saving_mean": 70.18,
        "net_saving_ci95": [4.68, 145.13],
        # NO regime_analysis -> base verdict would be PROMOTE_TO_MECHANIC ...
        # ... but ZERO performance telemetry -> #544 blocks it
    }))
    v = verdict_for("path_equivalence_quotient", spec)
    assert v["verdict"] != "PROMOTE_TO_MECHANIC", v
    assert v["verdict"] == "CANNOT_CHECK", v
    assert v["reason"] == "telemetry_incomplete_for_claim_class"
    assert v["telemetry"]["status"] != "COMPLETE"
    assert "blocked_promotion" in v


def test_prospective_run_with_unconfigured_collectors_blocked(repo_tmp):
    spec = _spec_into(repo_tmp, "path_equivalence_quotient")
    spec["artifact"].write_text(json.dumps({
        "grants_scientific_authority": False,
        "net_saving_mean": 70.18,
        "net_saving_ci95": [4.68, 145.13],
        "prospective": True,   # claims reproducibility packaging but collected nothing
    }))
    v = verdict_for("path_equivalence_quotient", spec)
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["reason"] == "telemetry_invalid_prospective_collectors_unconfigured"
    assert v["telemetry"]["status"] == "INVALID_PROSPECTIVE"


# --------------------------------------------------------------------------- #
# complete telemetry + positive net still promotes (no false blocking)
# --------------------------------------------------------------------------- #
def test_complete_telemetry_positive_net_promotes(repo_tmp):
    spec = _spec_into(repo_tmp, "path_equivalence_quotient")
    spec["artifact"].write_text(json.dumps(_efficiency_complete_artifact()))
    v = verdict_for("path_equivalence_quotient", spec)
    assert v["verdict"] == "PROMOTE_TO_MECHANIC", v
    assert v["telemetry"]["status"] == "COMPLETE"
    assert "blocked_promotion" not in v


# --------------------------------------------------------------------------- #
# CORRECTNESS promotion is NOT blocked by absent GPU/token telemetry
# --------------------------------------------------------------------------- #
def test_correctness_promotion_not_blocked_by_missing_gpu_token(repo_tmp):
    spec = _spec_into(repo_tmp, "six_family_law")
    spec["artifact"].write_text(json.dumps({
        "grants_scientific_authority": False,
        # a deterministic sign test: no seed, no GPU/token, just the outcome
        "all_six_positive": True,
        "sign_test_p": 0.03125,
        "n_positive": 6,
        "n_instances": 54,
    }))
    v = verdict_for("six_family_law", spec)
    assert v["verdict"] == "PROMOTE_TO_MECHANIC", v
    assert v["telemetry"]["claim_class"] == "CORRECTNESS"
    assert v["telemetry"]["status"] == "COMPLETE"


# --------------------------------------------------------------------------- #
# economic cost verification: stripping the charged cost blocks the promotion
# --------------------------------------------------------------------------- #
def test_stripping_economic_cost_blocks_field_construction_promotion(repo_tmp):
    # field_construction promotes on a positive net; its net is net-of
    # construction_cost, so removing that cost field must block the promotion.
    spec = _spec_into(repo_tmp, "field_construction")
    art = {
        "grants_scientific_authority": False,
        "net_search_saving": {"mean": 12.0, "lo": 4.0, "hi": 20.0},
        "n_completed": 100,
        "seed": 572,
        "baseline_expanded": 25,
        "field_expanded": 10,
        "construction_cost": 40.0,
    }
    spec["artifact"].write_text(json.dumps(art))
    full = verdict_for("field_construction", spec)
    # with the cost present and a positive net, it promotes with COMPLETE telemetry
    assert full["verdict"] == "PROMOTE_TO_MECHANIC", full
    assert full["telemetry"]["status"] == "COMPLETE"

    del art["construction_cost"]
    spec["artifact"].write_text(json.dumps(art))
    stripped = verdict_for("field_construction", spec)
    # net metric is still positive, but the charged cost is no longer verifiable
    assert stripped["verdict"] != "PROMOTE_TO_MECHANIC", stripped
    assert "construction_cost" in stripped["telemetry"]["missing"]


# --------------------------------------------------------------------------- #
# LIVE candidates: promoted efficiency claims are traceable to COMPLETE telemetry
# --------------------------------------------------------------------------- #
def test_live_efficiency_promotions_have_complete_telemetry():
    g = json.loads((ROOT / "research/unified_problem_solving_v1/results/PROMOTION_GATE.json").read_text())
    eff_classes = {"PERFORMANCE", "EFFICIENCY", "LLM_RUNTIME", "GPU_TRAINING", "CACHE_REUSE"}
    for name, cand in g["candidates"].items():
        tel = cand.get("telemetry", {})
        cls = tel.get("claim_class")
        if cand["verdict"] == "PROMOTE_TO_MECHANIC" and cls in eff_classes:
            assert tel["status"] == "COMPLETE", (name, tel)
            assert "blocked_promotion" not in cand, name


def test_live_path_quotient_is_conditional_with_complete_telemetry():
    v = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])
    assert v["verdict"] == "PROMOTE_CONDITIONALLY", v
    assert v["telemetry"]["status"] == "COMPLETE", v


def test_live_navigation_dynamics_gap_caveated_not_blocking():
    # navigation_dynamics has no work counter (PARTIAL) but is net-negative, so the
    # telemetry gap is attached as a caveat and does not itself change the verdict.
    v = verdict_for("navigation_dynamics", CANDIDATES["navigation_dynamics"])
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["telemetry"]["status"] == "PARTIAL", v
    assert "measured_quantity" in v["telemetry"]["missing"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
