from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .similarity import (
    SimilarityRelation,
    SimilarityWitness,
    WitnessReport,
    WitnessVerdict,
    validate_similarity_witness,
)


class BridgePathVerdict(str, Enum):
    NAVIGABLE_ONLY = "NAVIGABLE_ONLY"
    COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY = "COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY"
    REJECT = "REJECT"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class BridgeTargetVerdict(str, Enum):
    TRANSFER_HYPOTHESIS_ONLY = "TRANSFER_HYPOTHESIS_ONLY"
    TARGET_REFUTED_PATH_WITNESSES_PRESERVED = (
        "TARGET_REFUTED_PATH_WITNESSES_PRESERVED"
    )
    TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED = (
        "TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED"
    )
    PATH_NOT_COMPOSABLE = "PATH_NOT_COMPOSABLE"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class BridgeHop:
    """One locally witnessed relation used as a multi-hop bridge edge."""

    witness: SimilarityWitness
    approximation_error_upper_bound: Optional[float]
    evidence_lineage_ids: Tuple[str, ...]


@dataclass(frozen=True)
class BridgeHandoff:
    """Compatibility witness for the shared object between adjacent hops."""

    junction_id: str
    role_pairs: Tuple[Tuple[str, str], ...]
    compatibility_passed: Optional[bool]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class BridgePath:
    """Frozen path claim. BRIDGE_TO remains navigation unless composition earns more."""

    path_id: str
    question_or_qoi: str
    hops: Tuple[BridgeHop, ...]
    handoffs: Tuple[BridgeHandoff, ...]
    claimed_end_to_end_invariants: Tuple[str, ...]
    max_accumulated_error: Optional[float]
    hidden_labels_exposed: Optional[bool]
    declared_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class BridgePathReport:
    verdict: BridgePathVerdict
    reasons: Tuple[str, ...]
    hop_reports: Tuple[WitnessReport, ...]
    common_regime: Tuple[str, ...]
    carried_invariants: Tuple[str, ...]
    accumulated_error_upper_bound: Optional[float]
    evidence_lineage_ids: Tuple[str, ...]
    correlated_evidence: Optional[bool]

    @property
    def inferred_endpoint_relation(self) -> Optional[SimilarityRelation]:
        """A path never silently mints a typed endpoint relation."""
        return None

    @property
    def grants_target_authority(self) -> bool:
        """Path composition produces at most a transfer hypothesis."""
        return False


@dataclass(frozen=True)
class BridgeTransferTrial:
    trial_id: str
    path: BridgePath
    target_tested: Optional[bool]
    target_passed: Optional[bool]


@dataclass(frozen=True)
class BridgeTargetReport:
    verdict: BridgeTargetVerdict
    reasons: Tuple[str, ...]
    path_report: BridgePathReport

    @property
    def activates_canonical_knowledge(self) -> bool:
        return False


def _empty_report(
    verdict: BridgePathVerdict,
    reasons: Tuple[str, ...],
    hop_reports: Tuple[WitnessReport, ...] = (),
) -> BridgePathReport:
    return BridgePathReport(
        verdict=verdict,
        reasons=reasons,
        hop_reports=hop_reports,
        common_regime=(),
        carried_invariants=(),
        accumulated_error_upper_bound=None,
        evidence_lineage_ids=(),
        correlated_evidence=None,
    )


def _lineage_state(hops: Tuple[BridgeHop, ...]) -> tuple[Tuple[str, ...], bool]:
    flattened = [lineage for hop in hops for lineage in hop.evidence_lineage_ids]
    unique = tuple(sorted(set(flattened)))
    return unique, len(flattened) != len(set(flattened))


def evaluate_bridge_path(path: BridgePath) -> BridgePathReport:
    """Fail-closed evaluation of a multi-hop analogy path.

    Local validity is necessary but insufficient for end-to-end transfer. The
    evaluator requires invariant continuity, shared-node role compatibility,
    a common QoI/regime, and explicit error accounting. Even a composable path
    remains proposal-only and does not infer a typed endpoint relation.
    """

    if not path.path_id or not path.question_or_qoi:
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("path_identity_or_question_missing",),
        )

    if path.hidden_labels_exposed is None:
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("hidden_label_exposure_unknown",),
        )
    if path.hidden_labels_exposed:
        return _empty_report(
            BridgePathVerdict.TRIAL_INVALID,
            ("hidden_endpoint_or_outcome_label_exposed",),
        )

    if path.declared_before_outcomes is None:
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("path_freeze_chronology_unknown",),
        )
    if path.declared_before_outcomes is False:
        return _empty_report(
            BridgePathVerdict.TRIAL_INVALID,
            ("posthoc_path_or_invariant_selection",),
        )

    if len(path.hops) < 2:
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("multi_hop_path_requires_at_least_two_hops",),
        )

    if len(path.handoffs) != len(path.hops) - 1:
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("handoff_count_must_equal_hop_count_minus_one",),
        )

    hop_reports = tuple(validate_similarity_witness(hop.witness) for hop in path.hops)
    if any(report.verdict is WitnessVerdict.REJECT for report in hop_reports):
        return _empty_report(
            BridgePathVerdict.REJECT,
            ("one_or_more_hop_witnesses_rejected",),
            hop_reports,
        )
    if any(report.verdict is WitnessVerdict.CANNOT_CHECK for report in hop_reports):
        return _empty_report(
            BridgePathVerdict.CANNOT_CHECK,
            ("one_or_more_hop_witnesses_incomplete",),
            hop_reports,
        )

    for index, hop in enumerate(path.hops):
        if hop.witness.question_or_qoi != path.question_or_qoi:
            return _empty_report(
                BridgePathVerdict.REJECT,
                (f"question_or_qoi_drift_at_hop:{index}",),
                hop_reports,
            )
        if hop.witness.relation is SimilarityRelation.BRIDGE_TO:
            return _empty_report(
                BridgePathVerdict.CANNOT_CHECK,
                ("nested_bridge_to_hop_requires_separate_flattening_contract",),
                hop_reports,
            )

    for index, handoff in enumerate(path.handoffs):
        left = path.hops[index].witness
        right = path.hops[index + 1].witness
        if left.target_id != right.source_id:
            return _empty_report(
                BridgePathVerdict.REJECT,
                (f"intermediate_object_identity_mismatch:{index}",),
                hop_reports,
            )
        if handoff.junction_id != left.target_id:
            return _empty_report(
                BridgePathVerdict.REJECT,
                (f"handoff_junction_identity_mismatch:{index}",),
                hop_reports,
            )
        if not handoff.role_pairs:
            return _empty_report(
                BridgePathVerdict.CANNOT_CHECK,
                (f"handoff_role_pairs_missing:{index}",),
                hop_reports,
            )
        if not handoff.evidence_ids:
            return _empty_report(
                BridgePathVerdict.CANNOT_CHECK,
                (f"handoff_evidence_missing:{index}",),
                hop_reports,
            )

        left_target_roles = {target for _, target in left.mapping_pairs}
        right_source_roles = {source for source, _ in right.mapping_pairs}
        for left_role, right_role in handoff.role_pairs:
            if left_role not in left_target_roles:
                return _empty_report(
                    BridgePathVerdict.REJECT,
                    (f"handoff_left_role_not_delivered_by_prior_hop:{index}:{left_role}",),
                    hop_reports,
                )
            if right_role not in right_source_roles:
                return _empty_report(
                    BridgePathVerdict.REJECT,
                    (f"handoff_right_role_not_consumed_by_next_hop:{index}:{right_role}",),
                    hop_reports,
                )

        if handoff.compatibility_passed is None:
            return _empty_report(
                BridgePathVerdict.CANNOT_CHECK,
                (f"handoff_role_compatibility_unknown:{index}",),
                hop_reports,
            )
        if handoff.compatibility_passed is False:
            return _empty_report(
                BridgePathVerdict.REJECT,
                (f"handoff_role_compatibility_failed:{index}",),
                hop_reports,
            )

    regimes = set(path.hops[0].witness.regime)
    for hop in path.hops[1:]:
        regimes.intersection_update(hop.witness.regime)
    common_regime = tuple(sorted(regimes))

    lineage_ids, correlated_evidence = _lineage_state(path.hops)
    if any(not hop.evidence_lineage_ids for hop in path.hops):
        return BridgePathReport(
            verdict=BridgePathVerdict.CANNOT_CHECK,
            reasons=("one_or_more_hops_missing_evidence_lineage",),
            hop_reports=hop_reports,
            common_regime=common_regime,
            carried_invariants=(),
            accumulated_error_upper_bound=None,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=None,
        )

    if not path.claimed_end_to_end_invariants:
        return BridgePathReport(
            verdict=BridgePathVerdict.NAVIGABLE_ONLY,
            reasons=(
                "locally_witnessed_path_has_no_declared_end_to_end_invariant",
                "bridge_to_is_navigation_not_equivalence",
            ),
            hop_reports=hop_reports,
            common_regime=common_regime,
            carried_invariants=(),
            accumulated_error_upper_bound=None,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=correlated_evidence,
        )

    for invariant in path.claimed_end_to_end_invariants:
        for index, hop in enumerate(path.hops):
            if invariant in hop.witness.not_preserved:
                return BridgePathReport(
                    verdict=BridgePathVerdict.REJECT,
                    reasons=(f"carried_invariant_explicitly_broken:{invariant}:hop:{index}",),
                    hop_reports=hop_reports,
                    common_regime=common_regime,
                    carried_invariants=(),
                    accumulated_error_upper_bound=None,
                    evidence_lineage_ids=lineage_ids,
                    correlated_evidence=correlated_evidence,
                )
            if invariant not in hop.witness.preserved:
                return BridgePathReport(
                    verdict=BridgePathVerdict.CANNOT_CHECK,
                    reasons=(f"carried_invariant_unresolved:{invariant}:hop:{index}",),
                    hop_reports=hop_reports,
                    common_regime=common_regime,
                    carried_invariants=(),
                    accumulated_error_upper_bound=None,
                    evidence_lineage_ids=lineage_ids,
                    correlated_evidence=correlated_evidence,
                )

    if not common_regime:
        return BridgePathReport(
            verdict=BridgePathVerdict.NAVIGABLE_ONLY,
            reasons=(
                "local_hops_valid_but_no_end_to_end_regime_intersection",
                "path_cannot_support_end_to_end_transfer",
            ),
            hop_reports=hop_reports,
            common_regime=(),
            carried_invariants=path.claimed_end_to_end_invariants,
            accumulated_error_upper_bound=None,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=correlated_evidence,
        )

    if path.max_accumulated_error is None:
        return BridgePathReport(
            verdict=BridgePathVerdict.CANNOT_CHECK,
            reasons=("path_error_tolerance_missing",),
            hop_reports=hop_reports,
            common_regime=common_regime,
            carried_invariants=path.claimed_end_to_end_invariants,
            accumulated_error_upper_bound=None,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=correlated_evidence,
        )
    if path.max_accumulated_error < 0:
        return BridgePathReport(
            verdict=BridgePathVerdict.REJECT,
            reasons=("negative_path_error_tolerance",),
            hop_reports=hop_reports,
            common_regime=common_regime,
            carried_invariants=path.claimed_end_to_end_invariants,
            accumulated_error_upper_bound=None,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=correlated_evidence,
        )

    errors: list[float] = []
    for index, hop in enumerate(path.hops):
        error = hop.approximation_error_upper_bound
        if error is None:
            return BridgePathReport(
                verdict=BridgePathVerdict.CANNOT_CHECK,
                reasons=(f"hop_error_bound_unknown:{index}",),
                hop_reports=hop_reports,
                common_regime=common_regime,
                carried_invariants=path.claimed_end_to_end_invariants,
                accumulated_error_upper_bound=None,
                evidence_lineage_ids=lineage_ids,
                correlated_evidence=correlated_evidence,
            )
        if error < 0:
            return BridgePathReport(
                verdict=BridgePathVerdict.REJECT,
                reasons=(f"negative_hop_error_bound:{index}",),
                hop_reports=hop_reports,
                common_regime=common_regime,
                carried_invariants=path.claimed_end_to_end_invariants,
                accumulated_error_upper_bound=None,
                evidence_lineage_ids=lineage_ids,
                correlated_evidence=correlated_evidence,
            )
        errors.append(error)

    accumulated_error = sum(errors)
    if accumulated_error > path.max_accumulated_error:
        return BridgePathReport(
            verdict=BridgePathVerdict.NAVIGABLE_ONLY,
            reasons=(
                "conservative_accumulated_error_exceeds_frozen_path_tolerance",
                "local_hops_preserved_but_end_to_end_transfer_not_supported",
            ),
            hop_reports=hop_reports,
            common_regime=common_regime,
            carried_invariants=path.claimed_end_to_end_invariants,
            accumulated_error_upper_bound=accumulated_error,
            evidence_lineage_ids=lineage_ids,
            correlated_evidence=correlated_evidence,
        )

    reasons = [
        "all_hop_witnesses_valid",
        "shared_node_roles_compatible",
        "declared_invariants_preserved_across_all_hops",
        "end_to_end_regime_intersection_nonempty",
        "accumulated_error_within_frozen_tolerance",
        "composed_result_is_transfer_hypothesis_not_endpoint_equivalence",
    ]
    if correlated_evidence:
        reasons.append("correlated_evidence_not_counted_as_independent_corroboration")

    return BridgePathReport(
        verdict=BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY,
        reasons=tuple(reasons),
        hop_reports=hop_reports,
        common_regime=common_regime,
        carried_invariants=path.claimed_end_to_end_invariants,
        accumulated_error_upper_bound=accumulated_error,
        evidence_lineage_ids=lineage_ids,
        correlated_evidence=correlated_evidence,
    )


def evaluate_bridge_transfer(trial: BridgeTransferTrial) -> BridgeTargetReport:
    path_report = evaluate_bridge_path(trial.path)

    if path_report.verdict is BridgePathVerdict.TRIAL_INVALID:
        return BridgeTargetReport(
            BridgeTargetVerdict.TRIAL_INVALID,
            ("bridge_path_trial_invalid",),
            path_report,
        )
    if path_report.verdict is BridgePathVerdict.REJECT:
        return BridgeTargetReport(
            BridgeTargetVerdict.PATH_NOT_COMPOSABLE,
            ("bridge_path_rejected",),
            path_report,
        )
    if path_report.verdict is BridgePathVerdict.CANNOT_CHECK:
        return BridgeTargetReport(
            BridgeTargetVerdict.CANNOT_CHECK,
            ("bridge_path_incomplete",),
            path_report,
        )
    if path_report.verdict is BridgePathVerdict.NAVIGABLE_ONLY:
        return BridgeTargetReport(
            BridgeTargetVerdict.PATH_NOT_COMPOSABLE,
            ("navigable_path_has_no_end_to_end_transfer_authority",),
            path_report,
        )

    if trial.target_tested is None:
        return BridgeTargetReport(
            BridgeTargetVerdict.CANNOT_CHECK,
            ("target_test_status_unknown",),
            path_report,
        )
    if trial.target_tested is False:
        return BridgeTargetReport(
            BridgeTargetVerdict.TRANSFER_HYPOTHESIS_ONLY,
            ("composable_bridge_not_yet_tested_in_target",),
            path_report,
        )
    if trial.target_passed is None:
        return BridgeTargetReport(
            BridgeTargetVerdict.CANNOT_CHECK,
            ("target_test_outcome_unknown",),
            path_report,
        )
    if trial.target_passed is False:
        return BridgeTargetReport(
            BridgeTargetVerdict.TARGET_REFUTED_PATH_WITNESSES_PRESERVED,
            ("target_refuted_transfer_local_path_witnesses_preserved",),
            path_report,
        )

    return BridgeTargetReport(
        BridgeTargetVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED,
        ("target_test_passed_separate_scientific_promotion_still_required",),
        path_report,
    )
