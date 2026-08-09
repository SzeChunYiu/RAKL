from dataclasses import FrozenInstanceError

import pytest

from rakl.bridge_composition import (
    BridgeHandoff,
    BridgeHop,
    BridgePath,
    BridgePathVerdict,
    BridgeTargetVerdict,
    BridgeTransferTrial,
    ErrorCompositionRule,
    ErrorCompositionRuleKind,
    evaluate_bridge_path,
    evaluate_bridge_transfer,
)
from rakl.similarity import MappingAdmissibility, ProbeFamily, SimilarityRelation, SimilarityWitness


QOI = "does stability structure transfer?"


def _witness(
    source_id: str,
    target_id: str,
    *,
    qoi: str = QOI,
    preserved: tuple[str, ...] = ("feedback_loop", "role_order"),
    not_preserved: tuple[str, ...] = ("substrate",),
    regime: tuple[str, ...] = ("bounded-input", "low-noise"),
    relation: SimilarityRelation = SimilarityRelation.RELATIONALLY_ANALOGOUS,
) -> SimilarityWitness:
    constraints = ("typed_roles", "causal_direction")
    if relation is SimilarityRelation.MATHEMATICALLY_ISOMORPHIC:
        constraints = ("typed_roles", "type_or_unit_compatibility")
    return SimilarityWitness(
        relation=relation,
        source_id=source_id,
        target_id=target_id,
        source_domain=f"domain-{source_id}",
        target_domain=f"domain-{target_id}",
        question_or_qoi=qoi,
        mapping_pairs=(("driver", "driver"), ("response", "response")),
        preserved=preserved,
        not_preserved=not_preserved,
        regime=regime,
        evidence_ids=(f"evidence-{source_id}-{target_id}",),
        mapping_admissibility=MappingAdmissibility(
            family_id="typed-map-v1",
            declared_before_fit=True,
            constraints=constraints,
            constraint_violations=(),
            null_calibration_passed=True,
        ),
        probe_family=ProbeFamily("bridge-probes-v1", ("role", "regime")),
    )


def _hop(
    source: str,
    target: str,
    *,
    error: float | None = 0.05,
    semantics: str = "certified_metric_v1",
    lineage: str = "lineage-independent",
    **witness_overrides,
) -> BridgeHop:
    return BridgeHop(
        witness=_witness(source, target, **witness_overrides),
        approximation_error_upper_bound=error,
        evidence_lineage_ids=(lineage,),
        error_semantics_id=semantics,
    )


def _rule(**overrides) -> ErrorCompositionRule:
    values = dict(
        rule_id="additive-certified-v1",
        error_semantics_id="certified_metric_v1",
        kind=ErrorCompositionRuleKind.ADDITIVE_UPPER_BOUND,
        certified_before_outcomes=True,
    )
    values.update(overrides)
    return ErrorCompositionRule(**values)


def _path(**overrides) -> BridgePath:
    values = dict(
        path_id="A-B-C",
        question_or_qoi=QOI,
        hops=(
            _hop("A", "B", error=0.05, lineage="lineage-A"),
            _hop("B", "C", error=0.07, lineage="lineage-B"),
        ),
        handoffs=(
            BridgeHandoff(
                junction_id="B",
                role_pairs=(("driver", "driver"), ("response", "response")),
                compatibility_passed=True,
                evidence_ids=("handoff-B",),
            ),
        ),
        claimed_end_to_end_invariants=("feedback_loop",),
        max_accumulated_error=0.20,
        hidden_labels_exposed=False,
        declared_before_outcomes=True,
        error_composition_rule=_rule(),
    )
    values.update(overrides)
    return BridgePath(**values)


def test_valid_two_hop_shared_invariant_is_transfer_hypothesis_only():
    report = evaluate_bridge_path(_path())
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.accumulated_error_upper_bound == pytest.approx(0.12)
    assert report.inferred_endpoint_relation is None
    assert report.grants_target_authority is False


def test_valid_hops_without_common_invariant_are_navigation_only():
    assert evaluate_bridge_path(_path(claimed_end_to_end_invariants=())).verdict is BridgePathVerdict.NAVIGABLE_ONLY


def test_intermediate_object_mismatch_is_rejected():
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), _hop("B2", "C"))))
    assert report.verdict is BridgePathVerdict.REJECT
    assert any("intermediate_object_identity_mismatch" in x for x in report.reasons)


def test_role_handoff_mismatch_is_rejected():
    bad = BridgeHandoff("B", (("missing", "driver"),), True, ("handoff-B",))
    assert evaluate_bridge_path(_path(handoffs=(bad,))).verdict is BridgePathVerdict.REJECT


def test_explicit_role_compatibility_failure_is_rejected():
    bad = BridgeHandoff("B", (("driver", "driver"),), False, ("handoff-B",))
    assert evaluate_bridge_path(_path(handoffs=(bad,))).verdict is BridgePathVerdict.REJECT


def test_qoi_drift_is_rejected():
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), _hop("B", "C", qoi="throughput"))))
    assert report.verdict is BridgePathVerdict.REJECT


def test_empty_global_regime_intersection_is_navigation_only():
    hops = (
        _hop("A", "B", regime=("low-noise",)),
        _hop("B", "C", regime=("high-noise",)),
    )
    report = evaluate_bridge_path(_path(hops=hops))
    assert report.verdict is BridgePathVerdict.NAVIGABLE_ONLY
    assert report.common_regime == ()


def test_broken_carried_invariant_is_rejected():
    second = _hop("B", "C", preserved=("role_order",), not_preserved=("substrate", "feedback_loop"))
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), second)))
    assert report.verdict is BridgePathVerdict.REJECT


def test_unresolved_carried_invariant_is_cannot_check():
    second = _hop("B", "C", preserved=("role_order",), not_preserved=("substrate",))
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), second)))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK


def test_unknown_hop_error_is_cannot_check():
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), _hop("B", "C", error=None))))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK


def test_certified_accumulated_error_over_budget_is_navigation_only():
    report = evaluate_bridge_path(_path(max_accumulated_error=0.10))
    assert report.verdict is BridgePathVerdict.NAVIGABLE_ONLY
    assert report.accumulated_error_upper_bound == pytest.approx(0.12)


def test_negative_hop_error_is_rejected():
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"), _hop("B", "C", error=-0.01))))
    assert report.verdict is BridgePathVerdict.REJECT


def test_correlated_evidence_is_flagged_not_promoted_to_independence():
    hops = (
        _hop("A", "B", lineage="same-lineage"),
        _hop("B", "C", lineage="same-lineage"),
    )
    report = evaluate_bridge_path(_path(hops=hops))
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.correlated_evidence is True
    assert "correlated_evidence_not_counted_as_independent_corroboration" in report.reasons


def test_hidden_endpoint_label_invalidates_trial():
    assert evaluate_bridge_path(_path(hidden_labels_exposed=True)).verdict is BridgePathVerdict.TRIAL_INVALID


def test_posthoc_path_selection_invalidates_trial():
    assert evaluate_bridge_path(_path(declared_before_outcomes=False)).verdict is BridgePathVerdict.TRIAL_INVALID


def test_single_hop_is_cannot_check():
    report = evaluate_bridge_path(_path(hops=(_hop("A", "B"),), handoffs=()))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK


def test_mixed_relations_never_mint_endpoint_relation():
    hops = (
        _hop("A", "B", relation=SimilarityRelation.OBSERVATIONALLY_EQUIVALENT, error=0.0),
        _hop("B", "C", relation=SimilarityRelation.MATHEMATICALLY_ISOMORPHIC, error=0.0),
    )
    report = evaluate_bridge_path(_path(hops=hops))
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.inferred_endpoint_relation is None
    assert report.grants_target_authority is False


def test_target_refutation_preserves_path_witnesses():
    report = evaluate_bridge_transfer(BridgeTransferTrial("refute", _path(), True, False))
    assert report.verdict is BridgeTargetVerdict.TARGET_REFUTED_PATH_WITNESSES_PRESERVED
    assert report.path_report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.activates_canonical_knowledge is False


def test_target_pass_requires_separate_promotion():
    report = evaluate_bridge_transfer(BridgeTransferTrial("pass", _path(), True, True))
    assert report.verdict is BridgeTargetVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED
    assert report.activates_canonical_knowledge is False


# Round-019 error-composition addendum.

def test_numeric_errors_without_composition_rule_are_cannot_check():
    report = evaluate_bridge_path(_path(error_composition_rule=None))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK
    assert "error_composition_rule_missing" in report.reasons


def test_mixed_error_semantics_are_rejected():
    hops = (
        _hop("A", "B", semantics="tv_bound"),
        _hop("B", "C", semantics="kl_divergence"),
    )
    report = evaluate_bridge_path(
        _path(hops=hops, error_composition_rule=_rule(error_semantics_id="tv_bound"))
    )
    assert report.verdict is BridgePathVerdict.REJECT
    assert "hop_error_semantics_mismatch_with_composition_rule" in report.reasons


def test_uncertified_generic_kl_addition_is_cannot_check():
    hops = (
        _hop("A", "B", semantics="kl_divergence"),
        _hop("B", "C", semantics="kl_divergence"),
    )
    report = evaluate_bridge_path(_path(hops=hops, error_composition_rule=None))
    assert report.verdict is BridgePathVerdict.CANNOT_CHECK


def test_predeclared_certified_error_rule_records_semantics_and_rule():
    report = evaluate_bridge_path(_path())
    assert report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
    assert report.error_semantics_id == "certified_metric_v1"
    assert report.error_composition_rule_id == "additive-certified-v1"


def test_posthoc_error_composition_rule_invalidates_trial():
    rule = _rule(certified_before_outcomes=False)
    report = evaluate_bridge_path(_path(error_composition_rule=rule))
    assert report.verdict is BridgePathVerdict.TRIAL_INVALID
    assert "posthoc_error_composition_rule_selection" in report.reasons


def test_bridge_contract_is_immutable():
    path = _path()
    with pytest.raises(FrozenInstanceError):
        path.path_id = "changed"  # type: ignore[misc]
