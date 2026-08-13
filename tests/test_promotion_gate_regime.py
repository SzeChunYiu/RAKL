"""#543: regime-conditional promotion gate + applicability contract.

Two layers are tested:

  (1) the applicability contract + classifier (rakl.applicability) is validated
      FIRST, against both the live path-quotient regime_analysis and synthetic
      shapes (disjoint boxes, overlapping boxes, missing axis, non-crossover).
      This is the "validate the checker before trusting it" rule: a false
      positive (unconditional promote where there is a crossover) costs more than
      a miss.

  (2) the gate itself: the live path_equivalence_quotient candidate no longer
      yields an unconditional PROMOTE_TO_MECHANIC; it yields PROMOTE_CONDITIONALLY
      carrying the contract, and the contract routes negative / unknown cells to
      baseline and supported cells to the mechanic.

Acceptance (issue #543):
  - path-quotient can no longer yield unconditional PROMOTE_TO_MECHANIC;
  - a negative cell (k=3, p=1.0) routes to baseline;
  - a supported cell (k=6, p=0.6) routes to the mechanic;
  - unknown regime parameters fail closed to baseline;
  - the gate, registry, and controller consume one consistent contract.
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

from rakl.applicability import (  # noqa: E402
    build_applicability_contract,
    classify_regime_point,
    route_decision,
)
from promotion_gate import verdict_for, CANDIDATES  # noqa: E402

RES = ROOT / "research" / "unified_problem_solving_v1" / "results"
PQ = json.loads((RES / "path_quotient_savings.json").read_text())


# --------------------------------------------------------------------------- #
# (1) applicability contract + classifier
# --------------------------------------------------------------------------- #
def _live_contract():
    c = build_applicability_contract(PQ["regime_analysis"])
    assert c is not None, "live path-quotient regime_analysis must yield a contract"
    return c


def test_live_regime_analysis_builds_crossover_contract():
    c = _live_contract()
    assert c["kind"] == "regime_crossover_applicability"
    assert c["opposing_sign"] is True
    assert c["positive_regime_significant"] is True
    axis_names = {a["name"] for a in c["axes"]}
    assert axis_names == {"k", "p"}
    assert len(c["positive_subset"]["cells"]) == 6   # k=5,6 x p in {0.3,0.6,1.0}
    assert len(c["negative_subset"]["cells"]) == 10  # k=3,4 all p + k=5,6 p=0
    # positive box nested inside negative box -> NOT disjoint -> no interpolation
    assert c["boxes"]["boxes_disjoint"] is False


@pytest.mark.parametrize("point", [
    {"k": 5, "p": 0.3}, {"k": 5, "p": 0.6}, {"k": 5, "p": 1.0},
    {"k": 6, "p": 0.3}, {"k": 6, "p": 0.6}, {"k": 6, "p": 1.0},
])
def test_exact_positive_cells_are_supported(point):
    assert classify_regime_point(_live_contract(), point) == "SUPPORTED"


@pytest.mark.parametrize("point", [
    {"k": 3, "p": 0.0}, {"k": 3, "p": 1.0}, {"k": 4, "p": 0.6},
    {"k": 5, "p": 0.0}, {"k": 6, "p": 0.0},
])
def test_exact_negative_cells_are_negative(point):
    assert classify_regime_point(_live_contract(), point) == "NEGATIVE"


def test_untested_interior_of_overlapping_boxes_is_unknown():
    # k=5.5, p=0.5 sits inside BOTH the positive and negative boxes (positive box
    # is nested in the negative box), so it cannot be interpolated -> UNKNOWN.
    c = _live_contract()
    assert classify_regime_point(c, {"k": 5.5, "p": 0.5}) == "UNKNOWN"


def test_out_of_grid_point_is_unknown():
    assert classify_regime_point(_live_contract(), {"k": 7, "p": 0.6}) == "UNKNOWN"


def test_missing_axis_value_is_unknown():
    # a regime the contract cannot read on a tested axis fails closed
    assert classify_regime_point(_live_contract(), {"k": 6}) == "UNKNOWN"


def test_clean_disjoint_boxes_interpolate_to_supported():
    # synthetic regime with genuinely disjoint positive/negative boxes: a point
    # inside the positive box (but not an exact cell) interpolates to SUPPORTED.
    ra = {
        "positive_subset": {
            "cells": [{"k": 8, "p": 0.5}, {"k": 8, "p": 1.0},
                      {"k": 9, "p": 0.5}, {"k": 9, "p": 1.0}],
            "net_saving_ci95": [40.0, 120.0], "net_saving_mean": 80.0, "n": 4,
        },
        "negative_subset": {
            "cells": [{"k": 3, "p": 0.0}, {"k": 3, "p": 0.3},
                      {"k": 4, "p": 0.0}, {"k": 4, "p": 0.3}],
            "net_saving_ci95": [-12.0, -3.0], "net_saving_mean": -7.0, "n": 4,
        },
    }
    c = build_applicability_contract(ra)
    assert c is not None and c["boxes"]["boxes_disjoint"] is True
    # k=8.5, p=0.7 inside positive box, outside negative box -> SUPPORTED
    assert classify_regime_point(c, {"k": 8.5, "p": 0.7}) == "SUPPORTED"
    # k=3.5, p=0.1 inside negative box, outside positive box -> NEGATIVE
    assert classify_regime_point(c, {"k": 3.5, "p": 0.1}) == "NEGATIVE"
    # k=6, p=0.5 inside neither box -> UNKNOWN
    assert classify_regime_point(c, {"k": 6, "p": 0.5}) == "UNKNOWN"


# --------------------------------------------------------------------------- #
# (1b) builder honesty guards: no contract without a genuine opposing-sign crossover
# --------------------------------------------------------------------------- #
def test_no_contract_without_regime_analysis():
    assert build_applicability_contract(None) is None
    assert build_applicability_contract({}) is None


def test_no_contract_when_subset_ci_straddles_zero():
    # the "positive_subset" label is NOT trusted: its CI includes 0 -> no contract
    ra = {
        "positive_subset": {"cells": [{"k": 5, "p": 0.6}],
                            "net_saving_ci95": [-2.0, 5.0], "net_saving_mean": 1.5, "n": 1},
        "negative_subset": {"cells": [{"k": 3, "p": 0.6}],
                            "net_saving_ci95": [-8.0, -1.0], "net_saving_mean": -4.0, "n": 1},
    }
    assert build_applicability_contract(ra) is None


def test_no_contract_when_subsets_same_sign():
    ra = {
        "positive_subset": {"cells": [{"k": 5, "p": 0.6}],
                            "net_saving_ci95": [10.0, 50.0], "net_saving_mean": 30.0, "n": 1},
        "negative_subset": {"cells": [{"k": 3, "p": 0.6}],
                            "net_saving_ci95": [5.0, 20.0], "net_saving_mean": 12.0, "n": 1},
    }
    assert build_applicability_contract(ra) is None


def test_no_contract_when_a_subset_has_no_cells():
    ra = {
        "positive_subset": {"cells": [], "net_saving_ci95": [10.0, 50.0], "n": 0},
        "negative_subset": {"cells": [{"k": 3, "p": 0.6}],
                            "net_saving_ci95": [-8.0, -1.0], "n": 1},
    }
    assert build_applicability_contract(ra) is None


# --------------------------------------------------------------------------- #
# (2) the gate verdict + routing on the LIVE path-quotient artifact
# --------------------------------------------------------------------------- #
def test_live_path_quotient_verdict_is_conditional_not_unconditional():
    v = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])
    assert v["verdict"] == "PROMOTE_CONDITIONALLY", v
    assert v["verdict"] != "PROMOTE_TO_MECHANIC", (
        "#543 regression: path-quotient must NOT promote unconditionally on the pooled mean"
    )
    assert v["reason"] == "regime_crossover_positive_subregime_ci_excludes_null"
    assert v["applicability"]["kind"] == "regime_crossover_applicability"


def test_acceptance_negative_cell_routes_to_baseline():
    c = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])["applicability"]
    rd = route_decision(c, {"k": 3, "p": 1.0})
    assert rd["route"] == "baseline"
    assert rd["classification"] == "NEGATIVE"


def test_acceptance_supported_cell_routes_to_mechanic():
    c = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])["applicability"]
    rd = route_decision(c, {"k": 6, "p": 0.6})
    assert rd["route"] == "mechanic"
    assert rd["classification"] == "SUPPORTED"


def test_acceptance_unknown_regime_fails_closed_to_baseline():
    c = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])["applicability"]
    for point in ({"k": 7, "p": 0.6}, {"k": 5.5, "p": 0.5}, {"k": 6}):
        rd = route_decision(c, point)
        assert rd["route"] == "baseline", (point, rd)
        assert rd["classification"] == "UNKNOWN"


# --------------------------------------------------------------------------- #
# (2b) no-alarm guard: a clean uniform win (no crossover) still promotes
# --------------------------------------------------------------------------- #
@pytest.fixture
def repo_tmp():
    d = Path(tempfile.mkdtemp(prefix="regtest_", dir=str(ROOT)))
    yield d
    shutil.rmtree(str(d), ignore_errors=True)


def _net_spec(repo_tmp: Path) -> dict:
    spec = copy.deepcopy(CANDIDATES["path_equivalence_quotient"])
    spec["artifact"] = repo_tmp / "artifact.json"
    return spec


def test_uniform_positive_artifact_promotes_unconditionally(repo_tmp):
    spec = _net_spec(repo_tmp)
    spec["artifact"].write_text(json.dumps({
        "grants_scientific_authority": False,
        "net_saving_mean": 70.18,
        "net_saving_ci95": [4.68, 145.13],
        # NO regime_analysis -> no crossover -> pooled-mean verdict stands.
        # #544: include the required EFFICIENCY telemetry (sample, seed, a measured
        # quantity, and the witness/certification cost the net is net-of) so this
        # no-alarm guard isolates CROSSOVER detection from the telemetry gate.
        "n_instances_per_cell": 200,
        "seed": 461,
        "mean_witnesses_registered": 1.73,
    }))
    v = verdict_for("path_equivalence_quotient", spec)
    assert v["verdict"] == "PROMOTE_TO_MECHANIC", v
    assert "applicability" not in v
    assert v["telemetry"]["status"] == "COMPLETE"


def test_crossover_with_no_clean_positive_subregime_is_proposal_only(repo_tmp):
    # mirrored labels: the subset labelled "positive" is net-negative, the one
    # labelled "negative" is net-positive. opposing_sign holds but there is no
    # clean POSITIVE subregime, so the gate must NOT promote.
    spec = _net_spec(repo_tmp)
    spec["artifact"].write_text(json.dumps({
        "grants_scientific_authority": False,
        "net_saving_mean": 5.0,
        "net_saving_ci95": [-10.0, 20.0],
        "regime_analysis": {
            "positive_subset": {"cells": [{"k": 3, "p": 0.6}],
                                "net_saving_ci95": [-9.0, -2.0], "net_saving_mean": -5.0, "n": 1},
            "negative_subset": {"cells": [{"k": 6, "p": 0.6}],
                                "net_saving_ci95": [20.0, 60.0], "net_saving_mean": 40.0, "n": 1},
        },
    }))
    v = verdict_for("path_equivalence_quotient", spec)
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["reason"] == "regime_crossover_no_clean_positive_subregime"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
