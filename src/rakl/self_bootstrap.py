from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class BootstrapVerdict(str, Enum):
    SCOPED_BOOTSTRAP_EVOLUTION_EVIDENCE = "SCOPED_BOOTSTRAP_EVOLUTION_EVIDENCE"
    NO_IMPROVEMENT = "NO_IMPROVEMENT"
    LOCAL_IMPROVEMENT_ONLY = "LOCAL_IMPROVEMENT_ONLY"
    TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED = "TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED"
    META_OVERFIT = "META_OVERFIT"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    BLOCKED = "BLOCKED"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class BootstrapTrial:
    """Evidence packet for the claim that RAKL improved RAKL.

    This validator is deliberately stricter than a development benchmark.  It
    distinguishes weakness discovery, operator identification, local repair,
    fresh transfer, and protected assurance.  It never promotes a method itself.
    """

    benchmark_frozen_before_candidate: bool | None
    hidden_weakness_label_exposed: bool | None
    route_families_required: Tuple[str, ...]
    route_families_covered: Tuple[str, ...]
    route_semantically_flat_or_blocked: bool | None

    weakness_detected: bool | None
    weakness_correct: bool | None
    weakness_type: str | None
    epistemic_cut_localized: bool | None

    candidate_operator_family: str | None
    candidate_frozen_before_outcomes: bool | None
    candidate_semantically_equivalent_to_incumbent: bool | None
    alternatives_remain_compatible: bool | None

    development_delta: float | None
    development_material_threshold: float
    fresh_assurance_delta: float | None
    assurance_material_threshold: float
    fresh_assurance_executed: bool | None
    assurance_exposed_to_optimizer: bool | None
    assurance_evidence_lineage_independent: bool | None

    blocking_failures: Tuple[str, ...]
    negative_history_preserved: bool | None
    evaluator_separated_from_challenger: bool | None
    matched_resource_accounting: bool | None
    matched_baseline_complete: bool | None


@dataclass(frozen=True)
class BootstrapReport:
    verdict: BootstrapVerdict
    reasons: Tuple[str, ...]

    @property
    def grants_method_promotion(self) -> bool:
        return False

    @property
    def grants_independent_review_credit(self) -> bool:
        return False

    @property
    def grants_global_framework_saturation(self) -> bool:
        return False


def evaluate_bootstrap_trial(trial: BootstrapTrial) -> BootstrapReport:
    invalid: list[str] = []
    unknown: list[str] = []

    for value, label in (
        (trial.benchmark_frozen_before_candidate, "benchmark_freeze"),
        (trial.hidden_weakness_label_exposed, "hidden_label_exposure"),
        (trial.route_semantically_flat_or_blocked, "route_flatness"),
        (trial.candidate_frozen_before_outcomes, "candidate_freeze"),
        (trial.candidate_semantically_equivalent_to_incumbent, "candidate_equivalence"),
        (trial.assurance_exposed_to_optimizer, "assurance_exposure"),
        (trial.negative_history_preserved, "negative_history"),
        (trial.evaluator_separated_from_challenger, "evaluator_separation"),
        (trial.matched_resource_accounting, "resource_accounting"),
        (trial.matched_baseline_complete, "matched_baseline"),
    ):
        if value is None:
            unknown.append(f"{label}_unknown")

    if trial.development_material_threshold < 0 or trial.assurance_material_threshold < 0:
        invalid.append("material_threshold_negative")
    if trial.benchmark_frozen_before_candidate is False:
        invalid.append("benchmark_not_frozen_before_candidate")
    if trial.hidden_weakness_label_exposed is True:
        invalid.append("hidden_weakness_label_exposed")
    if trial.candidate_frozen_before_outcomes is False:
        invalid.append("candidate_not_frozen_before_outcomes")
    if trial.assurance_exposed_to_optimizer is True:
        invalid.append("assurance_contaminated_by_optimizer")
    if trial.blocking_failures:
        invalid.extend(f"blocking_failure:{item}" for item in trial.blocking_failures)
    if trial.negative_history_preserved is False:
        invalid.append("negative_history_not_preserved")
    if trial.evaluator_separated_from_challenger is False:
        invalid.append("evaluator_not_separated_from_challenger")

    required = set(trial.route_families_required)
    covered = set(trial.route_families_covered)
    missing_routes = tuple(sorted(required - covered))
    if missing_routes:
        invalid.extend(f"route_not_covered:{route}" for route in missing_routes)

    if invalid:
        return BootstrapReport(BootstrapVerdict.TRIAL_INVALID, tuple(invalid))
    if unknown:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, tuple(unknown))
    if trial.route_semantically_flat_or_blocked is False:
        return BootstrapReport(
            BootstrapVerdict.BLOCKED,
            ("search_not_semantically_flat_and_not_blocked",),
        )

    if trial.weakness_detected is None or trial.weakness_correct is None or trial.epistemic_cut_localized is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("weakness_discovery_evidence_incomplete",))

    if not trial.weakness_detected:
        return BootstrapReport(
            BootstrapVerdict.NO_IMPROVEMENT,
            ("no_nontrivial_weakness_survived_registered_audit",),
        )
    if not trial.weakness_correct or not trial.epistemic_cut_localized:
        return BootstrapReport(
            BootstrapVerdict.PARTIALLY_IDENTIFIED,
            ("weakness_or_epistemic_cut_not_correctly_localized",),
        )

    # Missing-data or implementation failures can be valid weaknesses but do not
    # establish a missing method operator.  Their repair is classified at the
    # project/support level unless a separately evidenced method defect remains.
    if trial.weakness_type in {"MISSING_EVIDENCE", "IMPLEMENTATION_DEFECT"}:
        return BootstrapReport(
            BootstrapVerdict.LOCAL_IMPROVEMENT_ONLY,
            (f"weakness_type:{trial.weakness_type}", "no_method_basis_evolution_claim"),
        )

    if trial.candidate_operator_family is None:
        return BootstrapReport(
            BootstrapVerdict.PARTIALLY_IDENTIFIED,
            ("method_weakness_detected_but_candidate_operator_unidentified",),
        )
    if trial.candidate_semantically_equivalent_to_incumbent is True:
        return BootstrapReport(
            BootstrapVerdict.NO_IMPROVEMENT,
            ("candidate_semantically_equivalent_to_incumbent",),
        )
    if trial.alternatives_remain_compatible is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("operator_identifiability_unknown",))
    if trial.alternatives_remain_compatible:
        return BootstrapReport(
            BootstrapVerdict.PARTIALLY_IDENTIFIED,
            ("multiple_operator_families_remain_compatible",),
        )

    if trial.development_delta is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("development_delta_missing",))
    development_positive = trial.development_delta > trial.development_material_threshold
    if not development_positive:
        return BootstrapReport(
            BootstrapVerdict.NO_IMPROVEMENT,
            ("development_gain_not_material",),
        )

    if trial.fresh_assurance_executed is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("fresh_assurance_execution_unknown",))
    if trial.fresh_assurance_executed is False:
        return BootstrapReport(
            BootstrapVerdict.LOCAL_IMPROVEMENT_ONLY,
            ("development_gain_without_fresh_assurance",),
        )
    if trial.fresh_assurance_delta is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("fresh_assurance_delta_missing",))
    if trial.fresh_assurance_delta < 0:
        return BootstrapReport(
            BootstrapVerdict.META_OVERFIT,
            ("development_gain_with_assurance_regression",),
        )
    assurance_positive = trial.fresh_assurance_delta > trial.assurance_material_threshold
    if not assurance_positive:
        return BootstrapReport(
            BootstrapVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED,
            ("fresh_assurance_gain_not_material",),
        )
    if trial.assurance_evidence_lineage_independent is None:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("assurance_lineage_independence_unknown",))
    if not trial.assurance_evidence_lineage_independent:
        return BootstrapReport(
            BootstrapVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED,
            ("fresh_task_process_distinct_but_evidence_lineage_not_independent",),
        )
    if trial.matched_resource_accounting is not True or trial.matched_baseline_complete is not True:
        return BootstrapReport(BootstrapVerdict.CANNOT_CHECK, ("matched_comparison_incomplete",))

    return BootstrapReport(
        BootstrapVerdict.SCOPED_BOOTSTRAP_EVOLUTION_EVIDENCE,
        (
            "previously_unlabelled_method_weakness_localized",
            "non_equivalent_operator_identified",
            "material_development_gain",
            "material_fresh_assurance_gain",
            "fresh_assurance_lineage_independent",
            "blocking_invariants_clean",
            "negative_history_preserved",
            "evaluator_separated",
            "matched_baselines_and_resources_complete",
            "verdict_is_scoped_and_does_not_self_promote_method",
        ),
    )
