from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from active_packet_preflight import active_registration_problems  # noqa: E402
from promotion_gate import CANDIDATES  # noqa: E402
from rakl.mechanic_research_packet_registry import load_active_packet_registry  # noqa: E402


REGISTRY_PATH = ROOT / "research/mechanic_research_packets_v1/ACTIVE_PACKET_REGISTRY.json"


def _synthetic_spec(variant_id: str | None) -> dict:
    spec = {
        "artifact": ROOT / "research/unified_problem_solving_v1/results/field_hypothesis.json",
        "net_keys": ["search_reduction_vs_bfs"],
        "cost_charged": True,
        "note": "synthetic registration preflight only",
    }
    if variant_id is not None:
        spec["research_packet_variant_id"] = variant_id
    return spec


def test_live_candidate_registry_has_no_active_preflight_problem() -> None:
    assert active_registration_problems() == ()


def test_future_candidate_missing_packet_id_is_blocked() -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _synthetic_spec(None)
    problems = active_registration_problems(candidates=synthetic)
    assert problems == ("future_candidate:research_packet_variant_id_missing",)


def test_future_candidate_bound_to_superseded_packet_is_blocked() -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _synthetic_spec("vtg_lean_geometry_v1")
    problems = active_registration_problems(candidates=synthetic)
    assert len(problems) == 1
    assert "SUPERSEDED" in problems[0]
    assert "packet_superseded" in problems[0]


def test_future_candidate_bound_to_basis_expanded_packet_is_blocked() -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _synthetic_spec("vtg_lean_geometry_v2")
    problems = active_registration_problems(candidates=synthetic)
    assert len(problems) == 1
    assert "BLOCKED_BASIS_EXPANDED" in problems[0]
    assert "candidate_basis_expanded_before_execution" in problems[0]


def test_future_candidate_bound_to_blocked_capstone_packet_is_blocked() -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _synthetic_spec("capstone_integrated_solver_v1")
    problems = active_registration_problems(candidates=synthetic)
    assert len(problems) == 1
    assert "BLOCKED_DEPENDENCY" in problems[0]
    assert "load_bearing_dependency_not_active" in problems[0]


def test_future_candidate_bound_to_active_packet_passes_preflight() -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _synthetic_spec("verified_failure_constraint_compilation_v1")
    registry = load_active_packet_registry(REGISTRY_PATH)
    assert active_registration_problems(candidates=synthetic, registry=registry) == ()
