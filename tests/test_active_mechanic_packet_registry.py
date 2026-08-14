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
    problems = validate_active_packet_registry(registry, repo_root=ROOT)
    assert problems == (), problems
    assert registry.grants_scientific_authority is False
    assert registry.grants_promotion_authority is False


def test_current_active_set_matches_frozen_challenger_expectation() -> None:
    registry = _registry()
    active = {entry.variant_id for entry in registry.entries if entry.status is PacketRegistryStatus.ACTIVE}
    # navigation_dynamic_parallel_portfolio_v3 and path_equivalence_stateful_por_v3
    # left this set at the 20260815 revalidation: RSHEA saturation round 004
    # expanded their required-parent basis (dependency-tracked incremental
    # recomputation; conflict/nogood learning), so their eligibility was demoted
    # to BLOCKED_BASIS_EXPANDED. See
    # research/mechanic_research_packets_v1/ACTIVE_REGISTRY_REVALIDATION_20260815.json.
    assert active == {
        "operational_map_belief_v1",
        "path_cost_algebra_v1",
        "trajectory_to_certificate_assembly_v1",
        "verification_scheduler_v1",
    }


def test_round004_expanded_variants_are_no_longer_eligible() -> None:
    """The demotion itself, asserted rather than left implicit in a set difference."""
    registry = _registry()
    by_id = {entry.variant_id: entry for entry in registry.entries}
    for variant_id, family in (
        ("navigation_dynamic_parallel_portfolio_v3", "navigation_dependency_tracked_incremental_v4"),
        ("path_equivalence_stateful_por_v3", "path_reduction_with_verified_nogoods_v4"),
    ):
        entry = by_id[variant_id]
        assert entry.status is PacketRegistryStatus.BLOCKED_BASIS_EXPANDED
        assert entry.replacement_family == family
        assert "round004" in entry.reason


def test_superseded_packet_stays_valid_history_but_is_not_eligible() -> None:
    report = resolve_packet_eligibility("vtg_lean_geometry_v1", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.SUPERSEDED, (report.status, report.reasons)
    assert report.eligible_for_existing_promotion_gate is False, report.reasons
    assert report.superseded_by == "vtg_lean_geometry_v2", report
    assert "packet_superseded" in report.reasons, report.reasons


def test_structurally_valid_packet_is_blocked_when_basis_expanded() -> None:
    report = resolve_packet_eligibility("vtg_lean_geometry_v2", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.BLOCKED_BASIS_EXPANDED, (report.status, report.reasons)
    assert report.eligible_for_existing_promotion_gate is False, report.reasons
    assert report.replacement_family == "vtg_lean_geometry_v3", report
    assert "candidate_basis_expanded_before_execution" in report.reasons, report.reasons


def test_active_replacement_packet_is_eligible_for_ordinary_gate_only() -> None:
    # Exemplar of a still-ACTIVE packet; see the note in
    # test_current_active_set_matches_frozen_challenger_expectation.
    report = resolve_packet_eligibility(
        "verification_scheduler_v1", _registry(), repo_root=ROOT
    )
    assert report.status is PacketRegistryStatus.ACTIVE, (report.status, report.reasons)
    assert report.eligible_for_existing_promotion_gate is True, report.reasons
    assert report.grants_scientific_authority is False
    assert report.grants_promotion_authority is False


def test_capstone_is_blocked_by_inactive_load_bearing_dependencies() -> None:
    report = resolve_packet_eligibility("capstone_integrated_solver_v1", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.BLOCKED_DEPENDENCY, (report.status, report.reasons)
    assert report.eligible_for_existing_promotion_gate is False, report.reasons
    assert "load_bearing_dependency_not_active" in report.reasons, report.reasons
    assert any("mechanic_value_of_computation_controller_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons), report.reasons
    assert any("navigation_quotient_validation_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons), report.reasons
    assert any("verified_solver_compilation_v1:BLOCKED_BASIS_EXPANDED" == reason for reason in report.reasons), report.reasons


def test_unknown_variant_fails_closed() -> None:
    report = resolve_packet_eligibility("not-registered", _registry(), repo_root=ROOT)
    assert report.status is PacketRegistryStatus.CANNOT_CHECK
    assert report.eligible_for_existing_promotion_gate is False
    assert report.reasons == ("variant_not_registered",)
