from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/cross_problem"


def _load(relative: str) -> dict:
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_xm001_positive_finite_gap_can_collapse_after_physical_scaling() -> None:
    # Abstract inference falsifier only: this is not asserted to be a Yang-Mills
    # transfer matrix. It tests whether pointwise finite-a positivity alone can
    # imply a positive inverse-spacing-normalized continuum gap.
    for a in (1.0, 0.5, 0.25, 0.125, 0.0625):
        r = math.exp(-(a * a))
        assert 0.0 < r < 1.0
        dimensionless_gap = -math.log(r)
        physical_gap = dimensionless_gap / a
        assert dimensionless_gap > 0.0
        assert math.isclose(dimensionless_gap, a * a, rel_tol=1e-12, abs_tol=1e-15)
        assert math.isclose(physical_gap, a, rel_tol=1e-12, abs_tol=1e-15)

    # Since Delta_phys(a)=a exactly, its continuum liminf is zero. The finite
    # values make the collapse executable while the identity supplies the exact
    # asymptotic conclusion.
    assert (0.0625) < (0.125) < (0.25) < (0.5) < 1.0


def test_xm001_result_artifact_hashes_and_trace_chain() -> None:
    tool_raw = _load("07_memory/XM001_RESEARCH_TOOL_DELTA_20260811.json")["tool"]
    tool_for_hash = copy.deepcopy(tool_raw)
    tool_hash = tool_for_hash["artifact_hash"]
    tool_for_hash["artifact_hash"] = ""
    assert tool_hash == _canonical_hash(tool_for_hash)

    failure_raw = _load("07_memory/XM001_FAILURE_EXPERIENCE_DELTA_20260811.json")[
        "experience"
    ]
    failure_for_hash = copy.deepcopy(failure_raw)
    failure_hash = failure_for_hash["artifact_hash"]
    failure_for_hash["artifact_hash"] = ""
    assert failure_hash == _canonical_hash(failure_for_hash)
    assert failure_raw["diagnosis_status"] == "SUPPORTED"
    assert "does not assert" in failure_raw["scope_conditions"][1]

    trace = _load("09_trace/XM001_RESEARCH_TRACE_20260811.json")
    previous = ""
    for entry in trace["entries"]:
        assert entry["previous_event_hash"] == previous
        payload = copy.deepcopy(entry)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash

    event_types = [entry["event_type"] for entry in trace["entries"]]
    assert event_types[:7] == [
        "ATOMIZED",
        "CONTEXT_FROZEN",
        "ANALOGY_SCAN",
        "METHOD_TRANSFER_REVIEW",
        "EXPERT_CONTEXT_REVIEW",
        "EXPERIENCE_MEMORY_REVIEW",
        "NEXT_STEP_PROPOSED",
    ]
    assert event_types[7:] == [
        "CANDIDATE_PROPOSED",
        "FALSIFIER_RUN",
        "RESULT_RECORDED",
        "RESIDUAL_OPENED",
    ]
