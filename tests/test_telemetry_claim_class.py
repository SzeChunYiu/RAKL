"""#544: claim-class-conditional telemetry requirements + completeness status.

Validates the schema/audit machinery BEFORE trusting the gate (validate-the-
checker): asserts both the positive case (a complete artifact is COMPLETE) and
the no-alarm case (removing a load-bearing field makes it incomplete).

Required-test mapping (issue #544):
  * envelope-only rejected for PERFORMANCE/EFFICIENCY
  * correctness-only result does not need GPU/token fields
  * field/navigation/TCSQ/path-quotient/identity schemas each enforce their
    economically load-bearing counters
  * future runners fail before outcome generation when required collectors
    unconfigured  (INVALID_PROSPECTIVE)
  * historical missing metrics remain explicit CANNOT_CHECK, not silently
    zeroed/defaulted
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import telemetry_schema as ts  # noqa: E402

RES = ROOT / "research"
U = RES / "unified_problem_solving_v1" / "results"


def _load(rel):
    return json.loads((RES / rel).read_text())


# --------------------------------------------------------------------------- #
# schema documents the #544 claim-class requirements
# --------------------------------------------------------------------------- #
def test_schema_dict_documents_claim_class_requirements():
    d = ts.get_schema_dict()
    reqs = d["#544_claim_class_requirements"]
    assert set(reqs[ts.ClaimClass.EFFICIENCY]) == {"sample", "seed", "measured_quantity"}
    # economic cost components are added per-candidate, not globally
    assert "construction_cost" not in reqs[ts.ClaimClass.EFFICIENCY]
    assert ts.ClaimClass.CORRECTNESS in reqs
    # GPU/token fields are NOT required for plain CORRECTNESS
    assert "gpu_time_s" not in reqs[ts.ClaimClass.CORRECTNESS]
    assert "tokens_count" not in reqs[ts.ClaimClass.CORRECTNESS]
    assert set(d["#544_efficiency_claim_classes"]) == set(ts.EFFICIENCY_CLAIM_CLASSES)


def test_required_fields_for_adds_economic_cost_components():
    base = ts.required_fields_for(ts.ClaimClass.EFFICIENCY)
    names = {r["requirement"] for r in base}
    assert names == {"sample", "seed", "measured_quantity"}
    eco = ts.required_fields_for(ts.ClaimClass.EFFICIENCY,
                                 economic_cost_fields=["construction_cost"])
    assert {r["requirement"] for r in eco} == {
        "sample", "seed", "measured_quantity", "construction_cost"}


# --------------------------------------------------------------------------- #
# envelope-only rejected for PERFORMANCE/EFFICIENCY (the #544 root cause)
# --------------------------------------------------------------------------- #
def _envelope_only():
    return {
        "schema_version": "orion-test-v1",
        "grants_scientific_authority": False,
        # a hand-written net metric with ZERO performance evidence:
        "net_saving_mean": 70.0,
        "net_saving_ci95": [4.0, 145.0],
    }


@pytest.mark.parametrize("claim_class", [
    ts.ClaimClass.PERFORMANCE, ts.ClaimClass.EFFICIENCY,
    ts.ClaimClass.LLM_RUNTIME, ts.ClaimClass.GPU_TRAINING,
])
def test_envelope_only_is_incomplete_for_efficiency_classes(claim_class):
    s = ts.telemetry_completeness_status(_envelope_only(), claim_class)
    assert s["status"] != "COMPLETE", s
    assert set(["sample", "seed", "measured_quantity"]).issubset(set(s["missing"]))


def test_correctness_exempt_from_gpu_and_token_fields():
    # a correctness result graded on an outcome rate needs no GPU/token telemetry
    corr = {"n": 100, "correct_rate": 0.9, "grants_scientific_authority": False}
    s = ts.telemetry_completeness_status(corr, ts.ClaimClass.CORRECTNESS)
    assert s["status"] == "COMPLETE", s
    assert "tokens_count" not in s["required"]
    assert "gpu_time_s" not in s["required"]


# --------------------------------------------------------------------------- #
# each load-bearing artifact enforces its economically load-bearing counter
# (positive: live artifact is COMPLETE; no-alarm: removing the counter breaks it)
# --------------------------------------------------------------------------- #
LIVE_ECONOMIC = [
    ("unified_problem_solving_v1/results/field_construction.json",
     ts.ClaimClass.EFFICIENCY, ["construction_cost"]),
    ("unified_problem_solving_v1/results/path_quotient_savings.json",
     ts.ClaimClass.EFFICIENCY, ["verification_cost"]),
    ("identity_reuse_v1/results/identity_reuse.json",
     ts.ClaimClass.CACHE_REUSE, ["exact_cost", "generic_cost"]),
    ("tcsq_sq3_v1/results/sq3.json",
     ts.ClaimClass.EFFICIENCY, ["cost_model"]),
]


@pytest.mark.parametrize("rel,claim_class,cost_fields", LIVE_ECONOMIC)
def test_live_economic_artifact_is_complete(rel, claim_class, cost_fields):
    s = ts.telemetry_completeness_status(_load(rel), claim_class,
                                         economic_cost_fields=cost_fields)
    assert s["status"] == "COMPLETE", (rel, s)


@pytest.mark.parametrize("rel,claim_class,cost_fields", LIVE_ECONOMIC)
def test_removing_economic_cost_field_breaks_completeness(rel, claim_class, cost_fields):
    data = _load(rel)
    # strip every alias of the FIRST declared cost field from the whole artifact
    first = cost_fields[0]
    aliases = ts.FIELD_ALIASES[first]

    def _strip(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                if k in aliases:
                    del o[k]
                else:
                    _strip(o[k])
        elif isinstance(o, list):
            for it in o:
                _strip(it)
    _strip(data)
    s = ts.telemetry_completeness_status(data, claim_class,
                                         economic_cost_fields=cost_fields)
    assert s["status"] != "COMPLETE", (rel, first, s)
    assert first in s["missing"], (rel, first, s)


def test_field_construction_measured_quantity_is_the_expansion_counter():
    # the load-bearing work counter for a search mechanic is a node-expansion count
    data = _load("unified_problem_solving_v1/results/field_construction.json")
    s = ts.telemetry_completeness_status(data, ts.ClaimClass.EFFICIENCY,
                                         economic_cost_fields=["construction_cost"])
    assert "measured_quantity" in s["present"], s


# --------------------------------------------------------------------------- #
# future runners fail before outcome generation when collectors unconfigured
# (INVALID_PROSPECTIVE), and historical gaps are explicit CANNOT_CHECK/PARTIAL
# --------------------------------------------------------------------------- #
def test_prospective_run_missing_collectors_is_invalid_prospective():
    art = _envelope_only()
    art["prospective"] = True  # a run that CLAIMS to be reproducible-packaged
    s = ts.telemetry_completeness_status(art, ts.ClaimClass.EFFICIENCY)
    assert s["status"] == "INVALID_PROSPECTIVE", s


def test_historical_unrecoverable_missing_is_cannot_check():
    art = _envelope_only()
    art["telemetry_unrecoverable"] = True  # historical run, data not recoverable
    s = ts.telemetry_completeness_status(art, ts.ClaimClass.EFFICIENCY)
    assert s["status"] == "CANNOT_CHECK", s


def test_missing_metric_reported_not_silently_zeroed():
    s = ts.telemetry_completeness_status(_envelope_only(), ts.ClaimClass.EFFICIENCY)
    # the missing list is explicit and non-empty; nothing is defaulted to 0
    assert s["missing"], s
    assert s["present"] == [], s


def test_navigation_dynamics_honest_partial_gap():
    # navigation_dynamics genuinely recorded no primitive work counter (only the
    # advantage CI); that gap is reported, not hidden. It is PARTIAL (historical,
    # not flagged prospective/unrecoverable).
    data = _load("unified_problem_solving_v1/results/navigation_dynamics.json")
    s = ts.telemetry_completeness_status(data, ts.ClaimClass.EFFICIENCY)
    assert s["status"] == "PARTIAL", s
    assert "measured_quantity" in s["missing"], s


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
