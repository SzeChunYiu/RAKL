from dataclasses import replace

from rakl.structural_types import BoundaryCondition, StructuralObject, StructuralRelation, StructuralRole
from rakl.training_parent_assimilation import (
    ParentAssimilationVerdict,
    build_parent_selection_bundle,
    select_with_parent_assimilation,
)
from rakl.training_policy_authority import TrainingPolicyMode, choose_active_training_policy
from rakl.training_projection import (
    MasteryCoordinate,
    StructuralMasteryEstimate,
    TrainingAllocationCandidate,
    TrainingUtilityVector,
    build_training_projection,
    structural_catalog_digest,
)


def _structure():
    return StructuralObject(
        structure_id="reachability",
        domain="synthetic",
        qoi="reachability_validity",
        context_id="p4-parent-assimilation",
        roles=(StructuralRole("state", "node"), StructuralRole("edge", "relation")),
        relations=(StructuralRelation("state", "connected_by", "state"),),
        invariants=frozenset({"directed_reachability"}),
        boundaries=(BoundaryCondition("regime", "finite_directed_graph"),),
        evidence_ids=("phase1-v2-7b",),
    )


def _mastery():
    values = {
        MasteryCoordinate.PRINCIPLE: 0.94,
        MasteryCoordinate.COMPOSITION: 0.62,
        MasteryCoordinate.BOUNDARY: 0.88,
        MasteryCoordinate.REPRESENTATION: 0.70,
        MasteryCoordinate.TRANSFER: 0.50,
        MasteryCoordinate.RETENTION: 0.82,
    }
    return StructuralMasteryEstimate(
        structure_id="reachability",
        model_checkpoint_hash="qwen25-7b-exp2",
        probe_family_hash="p4-phase2-probes",
        coordinate_values=tuple((coordinate, values[coordinate]) for coordinate in MasteryCoordinate),
        measured_case_ids=tuple(f"probe-{i}" for i in range(12)),
        frozen_before_allocation=True,
    )


def _utility(*, forgetting=0.03, negative=0.03):
    return TrainingUtilityVector(
        expected_principle_gain=0.1,
        expected_composition_gain=0.1,
        expected_boundary_gain=0.1,
        expected_representation_gain=0.1,
        expected_transfer_gain=0.1,
        expected_retention_gain=0.1,
        forgetting_risk=forgetting,
        negative_transfer_risk=negative,
        estimated_total_cost=1.0,
    )


def _candidate(i, *, forgetting=0.03, negative=0.03, leak=False):
    return TrainingAllocationCandidate(
        candidate_id=f"cand-{i}",
        raw_item_id=f"raw-{i}",
        derived_view_id=f"view-{i}",
        structure_id="reachability",
        model_checkpoint_hash="qwen25-7b-exp2",
        utility=_utility(forgetting=forgetting, negative=negative),
        data_provenance_ids=(f"source-{i}",),
        confirmatory_target_leak=leak,
    )


def _snapshot(candidates=None):
    structure = _structure()
    if candidates is None:
        candidates = tuple(_candidate(i) for i in range(1, 6))
    return build_training_projection(
        projection_id="p4-parent-assimilation-projection",
        model_checkpoint_hash="qwen25-7b-exp2",
        structural_catalog_hash=structural_catalog_digest((structure,)),
        probe_family_hash="p4-phase2-probes",
        structural_objects=(structure,),
        mastery_estimates=(_mastery(),),
        candidates=tuple(candidates),
        repetition_floor=0.25,
        frozen_before_outcome_access=True,
    )


def _bundle(order=None, *, checkpoint="qwen25-7b-exp2", frozen=True):
    if order is None:
        order = ("cand-2", "cand-5", "cand-1", "cand-4", "cand-3")
    return build_parent_selection_bundle(
        provider_id="phase2-strongest-model-aware-parent",
        provider_revision="frozen-parent-v1",
        model_checkpoint_hash=checkpoint,
        candidate_order=order,
        frozen_before_outcome_access=frozen,
    )


def test_safe_parent_fidelity_preserves_exact_parent_order():
    decision = select_with_parent_assimilation(_snapshot(), _bundle(), batch_size=4)
    assert decision.verdict is ParentAssimilationVerdict.SELECT_PROPOSAL
    assert decision.selected_candidate_ids == ("cand-2", "cand-5", "cand-1", "cand-4")
    assert decision.rejected_candidate_ids == ()


def test_structural_veto_is_stable_and_cannot_be_compensated_by_parent_priority():
    candidates = (
        _candidate(1),
        _candidate(2, forgetting=0.50),
        _candidate(3),
        _candidate(4, negative=0.50),
        _candidate(5),
    )
    decision = select_with_parent_assimilation(_snapshot(candidates), _bundle(), batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.SELECT_PROPOSAL
    assert decision.rejected_candidate_ids == ("cand-2", "cand-4")
    assert decision.selected_candidate_ids == ("cand-5", "cand-1", "cand-3")


def test_confirmatory_target_leak_invalidates_selection_before_parent_order_use():
    candidates = (_candidate(1), _candidate(2, leak=True), _candidate(3), _candidate(4), _candidate(5))
    decision = select_with_parent_assimilation(_snapshot(candidates), _bundle(), batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.INVALID
    assert not decision.selected_candidate_ids
    assert "confirmatory_target_leak_in_training_candidate" in decision.reasons


def test_stale_parent_checkpoint_fails_closed():
    decision = select_with_parent_assimilation(
        _snapshot(),
        _bundle(checkpoint="different-checkpoint"),
        batch_size=3,
    )
    assert decision.verdict is ParentAssimilationVerdict.CANNOT_CHECK
    assert decision.reasons == ("parent_selection_checkpoint_mismatch",)


def test_parent_order_coverage_missing_extra_and_duplicate_fail_closed():
    missing = _bundle(order=("cand-2", "cand-5", "cand-1", "cand-4"))
    decision = select_with_parent_assimilation(_snapshot(), missing, batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.CANNOT_CHECK
    assert "parent_selection_missing_candidate:cand-3" in decision.reasons

    extra = _bundle(order=("cand-2", "cand-5", "cand-1", "cand-4", "cand-3", "cand-X"))
    decision = select_with_parent_assimilation(_snapshot(), extra, batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.CANNOT_CHECK
    assert "parent_selection_unknown_candidate:cand-X" in decision.reasons

    duplicate = _bundle(order=("cand-2", "cand-5", "cand-1", "cand-1", "cand-4", "cand-3"))
    decision = select_with_parent_assimilation(_snapshot(), duplicate, batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.CANNOT_CHECK
    assert decision.reasons == ("parent_selection_duplicate_candidate_identity",)


def test_parent_selection_bundle_tamper_is_invalid():
    bundle = _bundle()
    tampered = replace(bundle, candidate_order=("cand-1", *bundle.candidate_order[1:]))
    decision = select_with_parent_assimilation(_snapshot(), tampered, batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.INVALID
    assert decision.reasons == ("parent_selection_bundle_content_hash_mismatch",)


def test_parent_selection_frozen_after_outcome_is_invalid():
    decision = select_with_parent_assimilation(_snapshot(), _bundle(frozen=False), batch_size=3)
    assert decision.verdict is ParentAssimilationVerdict.INVALID
    assert decision.reasons == ("parent_selection_defined_after_outcome_access",)


def test_assimilation_is_authority_inert_and_static_default_is_unchanged():
    decision = select_with_parent_assimilation(_snapshot(), _bundle(), batch_size=3)
    assert decision.grants_scientific_authority is False
    assert decision.grants_training_policy_authority is False
    assert decision.claims_scheduler_efficacy is False
    active = choose_active_training_policy()
    assert active.mode is TrainingPolicyMode.STATIC_STRUCTURAL
    assert active.grants_scientific_authority is False
