from __future__ import annotations

from pathlib import Path

from rakl.mechanic_research_packet_registry import (
    PacketRegistryStatus,
    load_active_packet_registry,
    resolve_packet_eligibility,
    validate_active_packet_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research/mechanic_research_packets_v1/ACTIVE_PACKET_REGISTRY.json"


def _registry():
    return load_active_packet_registry(REGISTRY_PATH)


def test_active_registry_is_content_valid_and_non_authoritative() -> None:
    registry = _registry()
    assert validate_active_packet_registry(registry, repo_root=ROOT) == ()
    assert registry.grants_scientific_authority is False
    assert registry.grants_promotion_authority is False


def test_current_active_set_matches_frozen_challenger_expectation() -> None:
    registry = _registry()
    active = {entry.variant_id for entry in registry.entries if entry.status is PacketRegistryStatus.ACTIVE}
    assert active == {
        "navigation_dynamic_parallel_portfolio_v3",
        "path_equivalence_stateful_por_v3",
        "operational_map_belief_v1",
        "path_cost_algebra_v1",
        "trajectory_to_certificate_assembly_v1",
        "verification_scheduler_v1",
    }


def test_superseded_packet_stays_valid_history_but_is_not_eligible() -> None:
    report = resolve_packet_eligibility("vtg_lean_geometry_v1", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.SUPERSEDED
    assert report.eligible_for_existing_promotion_gate is False
    assert report.superseded_by == "vtg_lean_geometry_v2"
    assert "packet_superseded" in report.reasons


def test_structurally_valid_packet_is_blocked_when_basis_expanded() -> None:
    report = resolve_packet_eligibility("vtg_lean_geometry_v2", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.BLOCKED_BASIS_EXPANDED
    assert report.eligible_for_existing_promotion_gate is False
    assert report.replacement_family == "vtg_lean_geometry_v3"
    assert "candidate_basis_expanded_before_execution" in report.reasons


def test_active_replacement_packet_is_eligible_for_ordinary_gate_only() -> None:
    report = resolve_packet_eligibility(
        "navigation_dynamic_parallel_portfolio_v3", _registry(), repo_root=ROOT
    )
    assert report.status is PacketRegistryStatus.ACTIVE
    assert report.eligible_for_existing_promotion_gate is True
    assert report.grants_scientific_authority is False
    assert report.grants_promotion_authority is False


def test_capstone_is_blocked_by_inactive_load_bearing_dependencies() -> None:
    report = resolve_packet_eligibility("capstone_integrated_solver_v1", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.BLOCKED_DEPENDENCY
    assert report.eligible_for_existing_promotion_gate is False
    assert "load_bearing_dependency_not_active" in report.reasons
    assert any("mechanic_value_of_computation_controller_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons)
    assert any("navigation_quotient_validation_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons)
    assert any("verified_solver_compilation_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons)


def test_unknown_variant_fails_closed() -> None:
    report = resolve_packet_eligibility("not-registered", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.CANNOT_CHECK
    assert report.eligible_for_existing_promotion_gate is False
    assert report.reasons == ("variant_not_registered",)
