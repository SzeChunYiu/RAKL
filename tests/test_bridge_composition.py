from dataclasses import FrozenInstanceError

import pytest

from rakl.bridge_composition import (
    BridgeHandoff,
    BridgeHop,
    BridgePath,
    BridgePathVerdict,
    BridgeTargetVerdict,
    BridgeTransferTrial,
    evaluate_bridge_path,
    evaluate_bridge_transfer,
)
from rakl.similarity import (
    MappingAdmissibility,
    ProbeFamily,
    SimilarityRelation,
    SimilarityWitness,
)


def _witness(
    *,
    source_id: str,
    target_id: str,
    question_or_qoi: str = "does stability structure transfer?",
    preserved: tuple[str, ...] = ("feedback_loop", "role_order"),
    not_preserved: tuple[str, ...] = ("substrate",),
    regime: tuple[str, ...] = ("bounded-input", "low-noise"),
    relation: SimilarityRelation = SimilarityRelation.RELATIONALLY_ANALOGOUS,
    source_role: str = "driver",
    target_role: str = "driver",
) -> SimilarityWitness:
    return SimilarityWitness(
        relation=relation,
        source_id=source_id,
        target_id=target_id,
        source_domain=f"domain-{source_id}",
        target_domain=f"domain-{target_id}",
        question_or_qoi=question_or_qoi,
        mapping_pairs=((source_role, target_role), ("response", "response")),
        preserved=preserved,
        not_preserved=not_preserved,
        regime=regime,
        evidence_ids=(f"evidence-{source_id}-{target_id}",),
        mapping_admissibility=MappingAdmissibility(
            family_id="typed-role-map-v1",
            declared_before_fit=True,
            constraints=("typed_roles", "causal_direction"),
            constraint_violations=(),
            null_calibration_passed=True,
        ),
        probe_family=ProbeFamily(
            family_id="bridge-probe-v1",
            probe_ids=("role-probe", "regime-probe"),
        ),
    )


def _path(**overrides) -> BridgePath:
    first = BridgeHop(
        witness=_witness(source_id="A", target_id="B"),
        approximation_error_upper_bound=0.05,
        evidence_lineage_ids=("lineage-A",),
    )
    second = BridgeHop(
        witness=_witness(source_id="B", target_id="C"),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B",),
    )
    values = dict(
        path_id="bridge-A-B-C",
        question_or_qoi="does stability structure transfer?",
        hops=(first, second),
        handoffs=(
            BridgeHandoff(
                junction_id="B",
                role_pairs=(("driver", "driver"), ("response", "response")),
                compatibility_passed=True,
                evidence_ids=("handoff-evidence-B",),
            ),
        ),
        claimed_end_to_end_invariants=("feedback_loop",),
        max_accumulated_error=0.20,
        hidden_labels_exposed=False,
        declared_before_outcomes=True,
    )
    values.update(overrides)
    return BridgePath(**values)


def test_valid_two_hop_shared_invariant_is_transfer_hypothesis_only():
    report = evaluate_bridge_path(_path())
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.carried_invariants == ("feedback_loop",)
    assert report.accumulated_error_upper_bound == pytest.approx(0.12)
    assert report.inferred_endpoint_relation is None
    assert report.grants_target_authority is False


def test_valid_hops_with_no_declared_common_invariant_are_navigation_only():
    report = evaluate_bridge_path(_path(claimed_end_to_end_invariants=()))
    assert report.verdict is BridgePathVerdict.NAVIGABLE_ONLY


def test_intermediate_object_identity_mismatch_is_rejected():
    first = _path().hops[0]
    second = BridgeHop(
        witness=_witness(source_id="B2", target_id="C"),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B2",),
    )
    report = evaluate_bridge_path(_path(hops=(first, second)))
    assert report.verdict is BridgePathVerdict.REJECT
    assert any("intermediate_object_identity_mismatch" in reason for reason in report.reasons)


def test_shared_node_role_handoff_mismatch_is_rejected():
    bad_handoff = BridgeHandoff(
        junction_id="B",
        role_pairs=(("missing-left-role", "driver"),),
        compatibility_passed=True,
        evidence_ids=("handoff-evidence-B",),
    )
    report = evaluate_bridge_path(_path(handoffs=(bad_handoff,)))
    assert report.verdict is BridgePathVerdict.REJECT


def test_explicit_role_compatibility_failure_is_rejected():
    bad_handoff = BridgeHandoff(
        junction_id="B",
        role_pairs=(("driver", "driver"),),
        compatibility_passed=False,
        evidence_ids=("handoff-evidence-B",),
    )
    report = evaluate_bridge_path(_path(handoffs=(bad_handoff,)))
    assert report.verdict is BridgePathVerdict.REJECT
    assert any("handoff_role_compatibility_failed" in reason for reason in report.reasons)


def test_qoi_drift_across_hops_is_rejected():
    first = _path().hops[0]
    second = BridgeHop(
        witness=_witness(
            source_id="B",
            target_id="C",
            question_or_qoi="does throughput structure transfer?",
        ),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(first, second)))
    assert report.verdict is BridgePathVerdict.REJECT
    assert any("question_or_qoi_drift" in reason for reason in report.reasons)


def test_empty_global_regime_intersection_is_navigation_only():
    first = BridgeHop(
        witness=_witness(source_id="A", target_id="B", regime=("low-noise",)),
        approximation_error_upper_bound=0.05,
        evidence_lineage_ids=("lineage-A",),
    )
    second = BridgeHop(
        witness=_witness(source_id="B", target_id="C", regime=("high-noise",)),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(first, second)))
    assert report.verdict is BridgePathVerdict.NAVIGABLE_ONLY
    assert report.common_regime == ()


def test_carried_invariant_explicitly_broken_is_rejected():
    second = BridgeHop(
        witness=_witness(
            source_id="B",
            target_id="C",
            preserved=("role_order",),
            not_preserved=("substrate", "feedback_loop"),
        ),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(_path().hops[0], second)))
    assert report.verdict is BridgePathVerdict.REJECT
    assert any("carried_invariant_explicitly_broken" in reason for reason in report.reasons)


def test_carried_invariant_unresolved_on_one_hop_is_cannot_check():
    second = BridgeHop(
        witness=_witness(
            source_id="B",
            target_id="C",
            preserved=("role_order",),
            not_preserved=("substrate",),
        ),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(_path().hops[0], second)))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK
    assert any("carried_invariant_unresolved" in reason for reason in report.reasons)


def test_unknown_hop_error_bound_is_cannot_check():
    second = BridgeHop(
        witness=_witness(source_id="B", target_id="C"),
        approximation_error_upper_bound=None,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(_path().hops[0], second)))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK
    assert "hop_error_bound_unknown:1" in report.reasons


def test_accumulated_error_over_budget_is_navigation_only():
    report = evaluate_bridge_path(_path(max_accumulated_error=0.10))
    assert report.verdict is BridgePathVerdict.NAVIGABLE_ONLY
    assert report.accumulated_error_upper_bound == pytest.approx(0.12)


def test_negative_hop_error_bound_is_rejected():
    second = BridgeHop(
        witness=_witness(source_id="B", target_id="C"),
        approximation_error_upper_bound=-0.01,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(_path().hops[0], second)))
    assert report.verdict is BridgePathVerdict.REJECT


def test_correlated_evidence_is_flagged_not_counted_as_independent_confirmation():
    first = BridgeHop(
        witness=_witness(source_id="A", target_id="B"),
        approximation_error_upper_bound=0.05,
        evidence_lineage_ids=("shared-lineage",),
    )
    second = BridgeHop(
        witness=_witness(source_id="B", target_id="C"),
        approximation_error_upper_bound=0.07,
        evidence_lineage_ids=("shared-lineage",),
    )
    report = evaluate_bridge_path(_path(hops=(first, second)))
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.correlated_evidence is True
    assert "correlated_evidence_not_counted_as_independent_corroboration" in report.reasons


def test_hidden_endpoint_label_exposure_invalidates_trial():
    report = evaluate_bridge_path(_path(hidden_labels_exposed=True))
    assert report.verdict is BridgePathVerdict.TRIAL_INVALID


def test_posthoc_path_or_invariant_selection_invalidates_trial():
    report = evaluate_bridge_path(_path(declared_before_outcomes=False))
    assert report.verdict is BridgePathVerdict.TRIAL_INVALID


def test_single_hop_cannot_be_called_multi_hop_bridge():
    report = evaluate_bridge_path(_path(hops=(_path().hops[0],), handoffs=()))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK


def test_mixed_relation_path_never_mints_endpoint_relation_or_authority():
    first = BridgeHop(
        witness=_witness(
            source_id="A",
            target_id="B",
            relation=SimilarityRelation.OBSERVATIONALLY_EQUIVALENT,
        ),
        approximation_error_upper_bound=0.0,
        evidence_lineage_ids=("lineage-A",),
    )
    second = BridgeHop(
        witness=_witness(
            source_id="B",
            target_id="C",
            relation=SimilarityRelation.MATHEMATICALLY_ISOMORPHIC,
        ),
        approximation_error_upper_bound=0.0,
        evidence_lineage_ids=("lineage-B",),
    )
    # Mathematical isomorphism needs an explicit type/unit constraint.
    second_witness = second.witness
    second = BridgeHop(
        witness=SimilarityWitness(
            relation=second_witness.relation,
            source_id=second_witness.source_id,
            target_id=second_witness.target_id,
            source_domain=second_witness.source_domain,
            target_domain=second_witness.target_domain,
            question_or_qoi=second_witness.question_or_qoi,
            mapping_pairs=second_witness.mapping_pairs,
            preserved=second_witness.preserved,
            not_preserved=second_witness.not_preserved,
            regime=second_witness.regime,
            evidence_ids=second_witness.evidence_ids,
            mapping_admissibility=MappingAdmissibility(
                family_id="iso-map-v1",
                declared_before_fit=True,
                constraints=("typed_roles", "type_or_unit_compatibility"),
                constraint_violations=(),
                null_calibration_passed=True,
            ),
            probe_family=second_witness.probe_family,
        ),
        approximation_error_upper_bound=0.0,
        evidence_lineage_ids=("lineage-B",),
    )
    report = evaluate_bridge_path(_path(hops=(first, second)))
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.inferred_endpoint_relation is None
    assert report.grants_target_authority is False


def test_target_refutation_preserves_composable_path_witnesses():
    report = evaluate_bridge_transfer(
        BridgeTransferTrial(
            trial_id="target-trial-refute",
            path=_path(),
            target_tested=True,
            target_passed=False,
        )
    )
    assert report.verdict is BridgeTargetVerdict.TARGET_REFUTED_PATH_WITNESSES_PRESERVED
    assert report.path_report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.activates_canonical_knowledge is False


def test_target_pass_still_requires_separate_promotion():
    report = evaluate_bridge_transfer(
        BridgeTransferTrial(
            trial_id="target-trial-pass",
            path=_path(),
            target_tested=True,
            target_passed=True,
        )
    )
    assert report.verdict is BridgeTargetVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED
    assert report.activates_canonical_knowledge is False


def test_bridge_contracts_are_immutable():
    path = _path()
    with pytest.raises(FrozenInstanceError):
        path.path_id = "changed"  # type: ignore[misc]
