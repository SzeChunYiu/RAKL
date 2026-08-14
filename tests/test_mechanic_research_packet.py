from __future__ import annotations

from dataclasses import replace

from rakl.mechanic_research_packet import (
    ApplicabilityGateState,
    MechanicResearchCoverageVerdict,
    MechanicResearchPacket,
    MechanicResearchPacketVerdict,
    MechanismGateState,
    StrongestParentSpec,
    audit_mechanic_research_packet_coverage,
    validate_mechanic_research_packet,
)


PARENT_SHA = "d7aa764e1ccf2eedca7e81ec827bbb355376ab04"


def _parent() -> StrongestParentSpec:
    return StrongestParentSpec(
        parent_id="astar-exact-parent",
        implementation_refs=("src/rakl/navigation_successor.py",),
        cost_model_id="serial-node-equivalent-v1",
        cost_equation="build + update + query + verify",
        justification="tight admissible exact parent under the registered graph subject",
        evidence_pointers=("research:parent-benchmark",),
    )


def _packet(*, variant_id: str = "nav-successor-v2") -> MechanicResearchPacket:
    return MechanicResearchPacket(
        packet_id=f"mrp:{variant_id}",
        mechanic_id="navigation_dynamics",
        variant_id=variant_id,
        parent_method_sha=PARENT_SHA,
        object_description="field-guided verified navigation over a frozen solver graph",
        qoi="paired fully-costed root-level search advantage over strongest parent",
        scope=("known finite graph worlds", "matched verifier", "registered cost model"),
        assumptions=("nonnegative edge costs", "same root goal and verifier"),
        strongest_parents=(_parent(),),
        prior_art_equivalence_map=("A* exact heuristic", "incremental shortest-path repair"),
        oracle_or_lower_bound="exact reverse shortest-path distance is the oracle cost-to-go",
        minimal_counterexamples=("greedy false attractor", "dynamic update invalidates stale field"),
        development_benchmark_id="dev-nav-v2",
        development_case_ids=("dev-1", "dev-2"),
        fresh_assurance_benchmark_id="assurance-nav-v2",
        fresh_assurance_case_ids=("assure-1", "assure-2"),
        selection_case_ids=("dev-1",),
        falsifier="paired fully-costed advantage fails to beat the strongest parent",
        same_system_ablation="same solver and verifier with the candidate mechanic disabled",
        hard_gate_obligations=("optimality preserved", "authority noninterference"),
        required_telemetry_fields=("sample", "seed", "measured_quantity", "total_cost"),
        total_cost_equation="candidate_total = build + repair + query + verifier",
        novelty_residual="reduce update cost without weakening admissibility or exact-parent control",
        permitted_publication_claim="routing efficiency only in the registered tested scope",
        evidence_pointers=("issue:#546", "issue:#528"),
    ).with_content_hash()


def test_valid_packet_is_only_eligible_for_existing_gate() -> None:
    packet = _packet()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE
    assert report.eligible_for_existing_promotion_gate is True
    assert report.reasons == ()
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False
    assert packet.to_dict()["replaces_promotion_gate"] is False


def test_missing_packet_fails_closed() -> None:
    report = validate_mechanic_research_packet(None)
    assert report.verdict is MechanicResearchPacketVerdict.CANNOT_CHECK
    assert report.eligible_for_existing_promotion_gate is False


def test_missing_strongest_parent_is_proposal_only() -> None:
    packet = replace(_packet(), strongest_parents=()).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.PROPOSAL_ONLY_INCOMPLETE
    assert "strongest_parents_missing" in report.reasons


def test_parent_requires_implementation_and_cost_model() -> None:
    weak_parent = replace(
        _parent(),
        implementation_refs=(),
        cost_model_id="",
        cost_equation="",
        justification="",
    )
    packet = replace(_packet(), strongest_parents=(weak_parent,)).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.PROPOSAL_ONLY_INCOMPLETE
    assert "strongest_parent_0_implementation_refs_missing" in report.reasons
    assert "strongest_parent_0_cost_model_missing" in report.reasons
    assert "strongest_parent_0_cost_equation_missing" in report.reasons
    assert "strongest_parent_0_justification_missing" in report.reasons


def test_missing_oracle_or_lower_bound_is_proposal_only() -> None:
    packet = replace(_packet(), oracle_or_lower_bound="").with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.PROPOSAL_ONLY_INCOMPLETE
    assert "oracle_or_lower_bound_missing" in report.reasons


def test_development_and_fresh_assurance_must_be_disjoint() -> None:
    packet = replace(
        _packet(),
        fresh_assurance_case_ids=("dev-2", "assure-2"),
    ).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.INVALID_CHRONOLOGY
    assert "development_and_fresh_assurance_cases_overlap" in report.reasons


def test_selection_cases_cannot_touch_fresh_assurance() -> None:
    packet = replace(
        _packet(),
        selection_case_ids=("assure-1",),
    ).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.INVALID_CHRONOLOGY
    assert "selection_and_fresh_assurance_cases_overlap" in report.reasons
    assert "selection_cases_must_be_subset_of_development_cases" in report.reasons


def test_packet_must_precede_implementation_and_outcomes() -> None:
    packet = replace(
        _packet(),
        frozen_before_implementation=False,
        frozen_before_outcome_access=False,
    ).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.INVALID_CHRONOLOGY
    assert "packet_not_frozen_before_implementation" in report.reasons
    assert "packet_not_frozen_before_outcome_access" in report.reasons


def test_outcome_gate_states_cannot_be_smuggled_into_preregistration() -> None:
    packet = replace(
        _packet(),
        mechanism_gate_state=MechanismGateState.MECHANISM_SUPPORTED,
        applicability_gate_state=ApplicabilityGateState.UNCONDITIONAL,
    ).with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.INVALID_CHRONOLOGY
    assert "preregistration_packet_cannot_contain_outcome_mechanism_state" in report.reasons
    assert "preregistration_packet_cannot_contain_outcome_applicability_state" in report.reasons


def test_content_hash_detects_post_freeze_tampering() -> None:
    packet = _packet()
    tampered = replace(packet, novelty_residual="different post-result story")
    report = validate_mechanic_research_packet(tampered)
    assert report.verdict is MechanicResearchPacketVerdict.CANNOT_CHECK
    assert "packet_content_sha256_mismatch" in report.reasons


def test_full_parent_sha_is_required() -> None:
    packet = replace(_packet(), parent_method_sha="deadbeef").with_content_hash()
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.CANNOT_CHECK
    assert "parent_method_sha_must_be_full_git_sha" in report.reasons


def test_shadow_coverage_identifies_missing_and_invalid_variants() -> None:
    valid = _packet(variant_id="valid")
    invalid = replace(
        _packet(variant_id="invalid"),
        oracle_or_lower_bound="",
    ).with_content_hash()
    report = audit_mechanic_research_packet_coverage(
        ("valid", "invalid", "missing"),
        (valid, invalid),
    )
    assert report.verdict is MechanicResearchCoverageVerdict.INCOMPLETE_SHADOW_COVERAGE
    assert report.valid_variant_ids == ("valid",)
    assert report.invalid_variant_ids == ("invalid",)
    assert report.missing_variant_ids == ("missing",)
    assert report.grants_promotion_authority is False


def test_shadow_coverage_can_be_complete_without_promoting_anything() -> None:
    one = _packet(variant_id="one")
    two = _packet(variant_id="two")
    report = audit_mechanic_research_packet_coverage(("one", "two"), (one, two))
    assert report.verdict is MechanicResearchCoverageVerdict.COMPLETE_SHADOW_COVERAGE
    assert report.complete is True
    assert report.valid_variant_ids == ("one", "two")
    assert report.grants_promotion_authority is False
