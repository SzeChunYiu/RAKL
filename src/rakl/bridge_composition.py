from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .similarity import SimilarityRelation, SimilarityWitness, WitnessReport, WitnessVerdict, validate_similarity_witness


class BridgePathVerdict(str, Enum):
    NAVIGABLE_ONLY = "NAVIGABLE_ONLY"
    COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY = "COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY"
    REJECT = "REJECT"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class BridgeTargetVerdict(str, Enum):
    TRANSFER_HYPOTHESIS_ONLY = "TRANSFER_HYPOTHESIS_ONLY"
    TARGET_REFUTED_PATH_WITNESSES_PRESERVED = "TARGET_REFUTED_PATH_WITNESSES_PRESERVED"
    TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED = "TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED"
    PATH_NOT_COMPOSABLE = "PATH_NOT_COMPOSABLE"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class ErrorCompositionRuleKind(str, Enum):
    ADDITIVE_UPPER_BOUND = "ADDITIVE_UPPER_BOUND"


@dataclass(frozen=True)
class ErrorCompositionRule:
    rule_id: str
    error_semantics_id: str
    kind: ErrorCompositionRuleKind
    certified_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class BridgeHop:
    witness: SimilarityWitness
    approximation_error_upper_bound: Optional[float]
    evidence_lineage_ids: Tuple[str, ...]
    error_semantics_id: str = ""


@dataclass(frozen=True)
class BridgeHandoff:
    junction_id: str
    role_pairs: Tuple[Tuple[str, str], ...]
    compatibility_passed: Optional[bool]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class BridgePath:
    path_id: str
    question_or_qoi: str
    hops: Tuple[BridgeHop, ...]
    handoffs: Tuple[BridgeHandoff, ...]
    claimed_end_to_end_invariants: Tuple[str, ...]
    max_accumulated_error: Optional[float]
    hidden_labels_exposed: Optional[bool]
    declared_before_outcomes: Optional[bool]
    error_composition_rule: Optional[ErrorCompositionRule] = None


@dataclass(frozen=True)
class BridgePathReport:
    verdict: BridgePathVerdict
    reasons: Tuple[str, ...]
    hop_reports: Tuple[WitnessReport, ...] = ()
    common_regime: Tuple[str, ...] = ()
    carried_invariants: Tuple[str, ...] = ()
    accumulated_error_upper_bound: Optional[float] = None
    evidence_lineage_ids: Tuple[str, ...] = ()
    correlated_evidence: Optional[bool] = None
    error_semantics_id: Optional[str] = None
    error_composition_rule_id: Optional[str] = None

    @property
    def inferred_endpoint_relation(self) -> Optional[SimilarityRelation]:
        return None

    @property
    def grants_target_authority(self) -> bool:
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


def _r(verdict: BridgePathVerdict, reasons: Tuple[str, ...], **kwargs) -> BridgePathReport:
    return BridgePathReport(verdict=verdict, reasons=reasons, **kwargs)


def _lineages(hops: Tuple[BridgeHop, ...]) -> tuple[Tuple[str, ...], bool]:
    values = [x for hop in hops for x in hop.evidence_lineage_ids]
    return tuple(sorted(set(values))), len(values) != len(set(values))


def evaluate_bridge_path(path: BridgePath) -> BridgePathReport:
    if not path.path_id or not path.question_or_qoi:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("path_identity_or_question_missing",))
    if path.hidden_labels_exposed is None:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("hidden_label_exposure_unknown",))
    if path.hidden_labels_exposed:
        return _r(BridgePathVerdict.TRIAL_INVALID, ("hidden_endpoint_or_outcome_label_exposed",))
    if path.declared_before_outcomes is None:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("path_freeze_chronology_unknown",))
    if path.declared_before_outcomes is False:
        return _r(BridgePathVerdict.TRIAL_INVALID, ("posthoc_path_or_invariant_selection",))
    if len(path.hops) < 2:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("multi_hop_path_requires_at_least_two_hops",))
    if len(path.handoffs) != len(path.hops) - 1:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("handoff_count_must_equal_hop_count_minus_one",))

    hop_reports = tuple(validate_similarity_witness(h.witness) for h in path.hops)
    if any(x.verdict is WitnessVerdict.REJECT for x in hop_reports):
        return _r(BridgePathVerdict.REJECT, ("one_or_more_hop_witnesses_rejected",), hop_reports=hop_reports)
    if any(x.verdict is WitnessVerdict.CANNOT_CHECK for x in hop_reports):
        return _r(BridgePathVerdict.CANNOT_CHECK, ("one_or_more_hop_witnesses_incomplete",), hop_reports=hop_reports)

    for i, hop in enumerate(path.hops):
        if hop.witness.question_or_qoi != path.question_or_qoi:
            return _r(BridgePathVerdict.REJECT, (f"question_or_qoi_drift_at_hop:{i}",), hop_reports=hop_reports)
        if hop.witness.relation is SimilarityRelation.BRIDGE_TO:
            return _r(BridgePathVerdict.CANNOT_CHECK, ("nested_bridge_to_hop_requires_separate_flattening_contract",), hop_reports=hop_reports)

    for i, handoff in enumerate(path.handoffs):
        left, right = path.hops[i].witness, path.hops[i + 1].witness
        if left.target_id != right.source_id:
            return _r(BridgePathVerdict.REJECT, (f"intermediate_object_identity_mismatch:{i}",), hop_reports=hop_reports)
        if handoff.junction_id != left.target_id:
            return _r(BridgePathVerdict.REJECT, (f"handoff_junction_identity_mismatch:{i}",), hop_reports=hop_reports)
        if not handoff.role_pairs or not handoff.evidence_ids:
            return _r(BridgePathVerdict.CANNOT_CHECK, (f"handoff_contract_incomplete:{i}",), hop_reports=hop_reports)
        left_roles = {b for _, b in left.mapping_pairs}
        right_roles = {a for a, _ in right.mapping_pairs}
        for a, b in handoff.role_pairs:
            if a not in left_roles:
                return _r(BridgePathVerdict.REJECT, (f"handoff_left_role_not_delivered_by_prior_hop:{i}:{a}",), hop_reports=hop_reports)
            if b not in right_roles:
                return _r(BridgePathVerdict.REJECT, (f"handoff_right_role_not_consumed_by_next_hop:{i}:{b}",), hop_reports=hop_reports)
        if handoff.compatibility_passed is None:
            return _r(BridgePathVerdict.CANNOT_CHECK, (f"handoff_role_compatibility_unknown:{i}",), hop_reports=hop_reports)
        if handoff.compatibility_passed is False:
            return _r(BridgePathVerdict.REJECT, (f"handoff_role_compatibility_failed:{i}",), hop_reports=hop_reports)

    regime = set(path.hops[0].witness.regime)
    for hop in path.hops[1:]:
        regime.intersection_update(hop.witness.regime)
    common_regime = tuple(sorted(regime))
    lineage_ids, correlated = _lineages(path.hops)
    base = dict(hop_reports=hop_reports, common_regime=common_regime, evidence_lineage_ids=lineage_ids, correlated_evidence=correlated)
    if any(not h.evidence_lineage_ids for h in path.hops):
        return _r(BridgePathVerdict.CANNOT_CHECK, ("one_or_more_hops_missing_evidence_lineage",), **base)
    if not path.claimed_end_to_end_invariants:
        return _r(BridgePathVerdict.NAVIGABLE_ONLY, ("locally_witnessed_path_has_no_declared_end_to_end_invariant", "bridge_to_is_navigation_not_equivalence"), **base)

    for inv in path.claimed_end_to_end_invariants:
        for i, hop in enumerate(path.hops):
            if inv in hop.witness.not_preserved:
                return _r(BridgePathVerdict.REJECT, (f"carried_invariant_explicitly_broken:{inv}:hop:{i}",), **base)
            if inv not in hop.witness.preserved:
                return _r(BridgePathVerdict.CANNOT_CHECK, (f"carried_invariant_unresolved:{inv}:hop:{i}",), **base)
    base["carried_invariants"] = path.claimed_end_to_end_invariants
    if not common_regime:
        return _r(BridgePathVerdict.NAVIGABLE_ONLY, ("local_hops_valid_but_no_end_to_end_regime_intersection",), **base)
    if path.max_accumulated_error is None:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("path_error_tolerance_missing",), **base)
    if path.max_accumulated_error < 0:
        return _r(BridgePathVerdict.REJECT, ("negative_path_error_tolerance",), **base)

    rule = path.error_composition_rule
    if rule is None:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("error_composition_rule_missing",), **base)
    base["error_semantics_id"] = rule.error_semantics_id or None
    base["error_composition_rule_id"] = rule.rule_id or None
    if not rule.rule_id or not rule.error_semantics_id:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("error_composition_rule_identity_or_semantics_missing",), **base)
    if rule.certified_before_outcomes is None:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("error_composition_rule_chronology_unknown",), **base)
    if rule.certified_before_outcomes is False:
        return _r(BridgePathVerdict.TRIAL_INVALID, ("posthoc_error_composition_rule_selection",), **base)
    semantics = tuple(h.error_semantics_id for h in path.hops)
    if any(not x for x in semantics):
        return _r(BridgePathVerdict.CANNOT_CHECK, ("one_or_more_hops_missing_error_semantics",), **base)
    if any(x != rule.error_semantics_id for x in semantics):
        return _r(BridgePathVerdict.REJECT, ("hop_error_semantics_mismatch_with_composition_rule",), **base)

    errors: list[float] = []
    for i, hop in enumerate(path.hops):
        value = hop.approximation_error_upper_bound
        if value is None:
            return _r(BridgePathVerdict.CANNOT_CHECK, (f"hop_error_bound_unknown:{i}",), **base)
        if value < 0:
            return _r(BridgePathVerdict.REJECT, (f"negative_hop_error_bound:{i}",), **base)
        errors.append(value)
    if rule.kind is not ErrorCompositionRuleKind.ADDITIVE_UPPER_BOUND:
        return _r(BridgePathVerdict.CANNOT_CHECK, ("unsupported_error_composition_rule_kind",), **base)
    accumulated = sum(errors)
    base["accumulated_error_upper_bound"] = accumulated
    if accumulated > path.max_accumulated_error:
        return _r(BridgePathVerdict.NAVIGABLE_ONLY, ("certified_accumulated_error_exceeds_frozen_path_tolerance",), **base)

    reasons = ["all_hop_witnesses_valid", "shared_node_roles_compatible", "declared_invariants_preserved_across_all_hops", "end_to_end_regime_intersection_nonempty", "error_semantics_match_predeclared_composition_rule", "certified_accumulated_error_within_frozen_tolerance", "composed_result_is_transfer_hypothesis_not_endpoint_equivalence"]
    if correlated:
        reasons.append("correlated_evidence_not_counted_as_independent_corroboration")
    return _r(BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY, tuple(reasons), **base)


def evaluate_bridge_transfer(trial: BridgeTransferTrial) -> BridgeTargetReport:
    report = evaluate_bridge_path(trial.path)
    if report.verdict is BridgePathVerdict.TRIAL_INVALID:
        return BridgeTargetReport(BridgeTargetVerdict.TRIAL_INVALID, ("bridge_path_trial_invalid",), report)
    if report.verdict is BridgePathVerdict.REJECT:
        return BridgeTargetReport(BridgeTargetVerdict.PATH_NOT_COMPOSABLE, ("bridge_path_rejected",), report)
    if report.verdict is BridgePathVerdict.CANNOT_CHECK:
        return BridgeTargetReport(BridgeTargetVerdict.CANNOT_CHECK, ("bridge_path_incomplete",), report)
    if report.verdict is BridgePathVerdict.NAVIGABLE_ONLY:
        return BridgeTargetReport(BridgeTargetVerdict.PATH_NOT_COMPOSABLE, ("navigable_path_has_no_end_to_end_transfer_authority",), report)
    if trial.target_tested is None:
        return BridgeTargetReport(BridgeTargetVerdict.CANNOT_CHECK, ("target_test_status_unknown",), report)
    if trial.target_tested is False:
        return BridgeTargetReport(BridgeTargetVerdict.TRANSFER_HYPOTHESIS_ONLY, ("composable_bridge_not_yet_tested_in_target",), report)
    if trial.target_passed is None:
        return BridgeTargetReport(BridgeTargetVerdict.CANNOT_CHECK, ("target_test_outcome_unknown",), report)
    if trial.target_passed is False:
        return BridgeTargetReport(BridgeTargetVerdict.TARGET_REFUTED_PATH_WITNESSES_PRESERVED, ("target_refuted_transfer_local_path_witnesses_preserved",), report)
    return BridgeTargetReport(BridgeTargetVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED, ("target_test_passed_separate_scientific_promotion_still_required",), report)
