from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureCause(str, Enum):
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    MEASUREMENT_OR_CLOCK_ERROR = "MEASUREMENT_OR_CLOCK_ERROR"
    REPRESENTATION_MISMATCH = "REPRESENTATION_MISMATCH"
    ASSUMPTION_FAILURE = "ASSUMPTION_FAILURE"
    INFERENCE_OR_STATISTICAL_ERROR = "INFERENCE_OR_STATISTICAL_ERROR"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    MODEL_CLASS_MISSPECIFICATION = "MODEL_CLASS_MISSPECIFICATION"
    ONTOLOGY_GAP = "ONTOLOGY_GAP"
    METHOD_BASIS_GAP = "METHOD_BASIS_GAP"
    STOCHASTIC_OR_UNIDENTIFIED = "STOCHASTIC_OR_UNIDENTIFIED"
    EXTERNAL_ENVIRONMENT_SHIFT = "EXTERNAL_ENVIRONMENT_SHIFT"


class LearningControlVerdict(str, Enum):
    PERSIST_STRATEGY = "PERSIST_STRATEGY"
    SWITCH_STRATEGY = "SWITCH_STRATEGY"
    SEEK_INDEPENDENT_HELP = "SEEK_INDEPENDENT_HELP"
    INVENT_OR_ASSIMILATE_OPERATOR = "INVENT_OR_ASSIMILATE_OPERATOR"
    ACQUIRE_EVIDENCE_OR_MEASUREMENT = "ACQUIRE_EVIDENCE_OR_MEASUREMENT"
    REPAIR_IMPLEMENTATION = "REPAIR_IMPLEMENTATION"
    RUN_DISCRIMINATING_CHALLENGE = "RUN_DISCRIMINATING_CHALLENGE"
    STOP_REFLECTION = "STOP_REFLECTION"
    REACTIVATE_AND_RETEST_SKILL = "REACTIVATE_AND_RETEST_SKILL"
    ADVANCE_CHALLENGE_FRONTIER = "ADVANCE_CHALLENGE_FRONTIER"
    DIAGNOSE_REGRESSION = "DIAGNOSE_REGRESSION"
    REPAIR_VALIDITY_FAILURE = "REPAIR_VALIDITY_FAILURE"
    ROUTE_SCIENCE_AND_METHOD_RESIDUALS = "ROUTE_SCIENCE_AND_METHOD_RESIDUALS"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ChallengeLearningCase:
    """Evidence packet for choosing a learning-control action after a challenge.

    This packet is deliberately outcome-linked.  Self-report, confidence, or a
    second reflection pass are not substitutes for an observed task outcome.
    The controller recommends a next action only; it cannot promote a method
    change or mint scientific authority.
    """

    outcome_evidence_available: bool | None

    competence_previous: float | None = None
    competence_current: float | None = None
    matched_competence_probe: bool = False
    current_challenge_mastered: bool = False

    failure_cause: FailureCause | None = None
    plausible_failure_causes: tuple[FailureCause, ...] = ()

    new_discriminating_residual: bool = False
    registered_discriminating_challenge_available: bool = False
    repeated_equivalent_failures: int = 0

    method_basis_gap_supported: bool = False
    incumbent_operator_available: bool | None = None

    independent_help_available: bool = False
    help_process_independent: bool | None = None
    help_lineage_independent: bool | None = None

    reflection_rounds_without_gain: int = 0
    reflection_new_residual: bool = False
    reflection_attribution_changed: bool = False
    reflection_action_policy_changed: bool = False
    reflection_calibration_improved: bool = False

    skill_previously_validated: bool = False
    environment_or_dependency_changed: bool = False

    blocking_validity_failure: bool = False
    science_residual_present: bool = False
    method_residual_present: bool = False

    def __post_init__(self) -> None:
        if self.repeated_equivalent_failures < 0:
            raise ValueError("repeated_equivalent_failures cannot be negative")
        if self.reflection_rounds_without_gain < 0:
            raise ValueError("reflection_rounds_without_gain cannot be negative")
        if (
            (self.competence_previous is None) !=
            (self.competence_current is None)
        ):
            raise ValueError(
                "competence_previous and competence_current must be supplied together"
            )
        for value in (self.competence_previous, self.competence_current):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError("competence values must be within [0, 1]")


@dataclass(frozen=True)
class ChallengeLearningReport:
    verdict: LearningControlVerdict
    reasons: tuple[str, ...]
    learning_progress: float | None
    independent_help_credit: bool | None = None
    failure_cause_identified: bool = False

    @property
    def capability_promotion_authorized(self) -> bool:
        """A learning-control recommendation never validates its own repair."""

        return False

    @property
    def scientific_authority_minted(self) -> bool:
        return False


def _learning_progress(case: ChallengeLearningCase) -> float | None:
    if case.competence_previous is None or case.competence_current is None:
        return None
    return case.competence_current - case.competence_previous


def _qualified_independent_help(case: ChallengeLearningCase) -> bool:
    return (
        case.independent_help_available
        and case.help_process_independent is True
        and case.help_lineage_independent is True
    )


def choose_learning_control(case: ChallengeLearningCase) -> ChallengeLearningReport:
    """Choose the next learning move using fail-closed evidence priorities.

    The priority order prevents attractive self-improvement narratives from
    overriding more mundane explanations such as missing measurements, code
    errors, stochastic variation, or blocking validity regressions.
    """

    progress = _learning_progress(case)
    help_credit = (
        _qualified_independent_help(case)
        if case.independent_help_available
        else None
    )

    def report(
        verdict: LearningControlVerdict,
        *reasons: str,
        cause_identified: bool = False,
    ) -> ChallengeLearningReport:
        return ChallengeLearningReport(
            verdict=verdict,
            reasons=tuple(reasons),
            learning_progress=progress,
            independent_help_credit=help_credit,
            failure_cause_identified=cause_identified,
        )

    if case.outcome_evidence_available is not True:
        return report(
            LearningControlVerdict.CANNOT_CHECK,
            "no external challenge outcome is available; introspection alone cannot establish a learning need",
        )

    if case.blocking_validity_failure:
        return report(
            LearningControlVerdict.REPAIR_VALIDITY_FAILURE,
            "a blocking epistemic validity failure dominates any nominal performance gain",
            "repair and re-evaluate before learning-capability attribution",
            cause_identified=True,
        )

    if case.science_residual_present and case.method_residual_present:
        return report(
            LearningControlVerdict.ROUTE_SCIENCE_AND_METHOD_RESIDUALS,
            "the challenge exposed both a domain-science residual and a framework-method residual",
            "route them to separate evidence-governed queues so method learning cannot rewrite domain evidence",
        )

    if (
        case.skill_previously_validated
        and case.environment_or_dependency_changed
        and progress is not None
        and progress < 0
    ):
        return report(
            LearningControlVerdict.REACTIVATE_AND_RETEST_SKILL,
            "a previously validated skill regressed after an environment/dependency change",
            "re-execute the skill contract before treating the regression as a new conceptual weakness",
        )

    if progress is not None and progress < 0 and case.matched_competence_probe:
        return report(
            LearningControlVerdict.DIAGNOSE_REGRESSION,
            "competence decreased on a matched repeated probe",
            "localize environment, implementation, representation, and method causes before further optimization",
        )

    if case.current_challenge_mastered and progress is not None and abs(progress) <= 1e-12:
        return report(
            LearningControlVerdict.ADVANCE_CHALLENGE_FRONTIER,
            "the current challenge is repeatedly mastered and no longer produces learning progress",
            "allocate learning budget to a harder or more diverse challenge while preserving project importance separately",
        )

    reflection_gain = any(
        (
            case.reflection_new_residual,
            case.reflection_attribution_changed,
            case.reflection_action_policy_changed,
            case.reflection_calibration_improved,
        )
    )
    if case.reflection_rounds_without_gain >= 2 and not reflection_gain:
        return report(
            LearningControlVerdict.STOP_REFLECTION,
            "successive reflection rounds produced no new residual, attribution, action-policy change, or calibration gain",
            "continued same-mode reflection is classified as rumination rather than learning",
        )

    if case.failure_cause in {
        FailureCause.EVIDENCE_MISSING,
        FailureCause.MEASUREMENT_OR_CLOCK_ERROR,
    }:
        return report(
            LearningControlVerdict.ACQUIRE_EVIDENCE_OR_MEASUREMENT,
            f"failure is attributed to {case.failure_cause.value}, not yet to a missing research method",
            "obtain or repair the observation before inventing a method operator",
            cause_identified=True,
        )

    if case.failure_cause == FailureCause.IMPLEMENTATION_ERROR:
        return report(
            LearningControlVerdict.REPAIR_IMPLEMENTATION,
            "known-answer or execution evidence localizes the failure to implementation",
            "repair implementation without escalating the defect into a new scientific method claim",
            cause_identified=True,
        )

    method_gap = (
        case.method_basis_gap_supported
        or case.failure_cause == FailureCause.METHOD_BASIS_GAP
    )
    if method_gap:
        if case.incumbent_operator_available is True:
            return report(
                LearningControlVerdict.SWITCH_STRATEGY,
                "a method gap was suspected but an incumbent operator is registered as able to address it",
                "route to the incumbent method before inventing a new operator",
                cause_identified=True,
            )
        if _qualified_independent_help(case):
            return report(
                LearningControlVerdict.SEEK_INDEPENDENT_HELP,
                "the current method basis is insufficient and genuinely independent expertise is available",
                "external advice enters as a proposal/source with provenance, not automatic authority",
                cause_identified=True,
            )
        return report(
            LearningControlVerdict.INVENT_OR_ASSIMILATE_OPERATOR,
            "evidence supports a method-basis gap and no qualified ready incumbent/help route is available",
            "freeze a method discriminator before constructing or assimilating a new operator",
            cause_identified=True,
        )

    if (
        len(set(case.plausible_failure_causes)) >= 2
        and case.registered_discriminating_challenge_available
    ):
        return report(
            LearningControlVerdict.RUN_DISCRIMINATING_CHALLENGE,
            "multiple failure causes remain viable and a registered challenge can separate them",
            "diagnose before repairing; failure attribution remains partially identified",
        )

    if case.failure_cause == FailureCause.STOCHASTIC_OR_UNIDENTIFIED:
        if case.registered_discriminating_challenge_available:
            return report(
                LearningControlVerdict.RUN_DISCRIMINATING_CHALLENGE,
                "the observed miss is compatible with stochastic variation or an unidentified cause",
                "one miss is insufficient to establish a framework weakness",
            )
        return report(
            LearningControlVerdict.CANNOT_CHECK,
            "the miss is not identified as a method failure and no discriminating challenge is registered",
        )

    flat = progress is not None and abs(progress) <= 1e-12
    if case.repeated_equivalent_failures >= 2 and flat:
        return report(
            LearningControlVerdict.SWITCH_STRATEGY,
            "repeated semantically equivalent failures produced no measured learning progress",
            "persistence has become redundant; move to a different representation/operator or obtain new evidence",
        )

    if case.new_discriminating_residual:
        if case.registered_discriminating_challenge_available:
            return report(
                LearningControlVerdict.RUN_DISCRIMINATING_CHALLENGE,
                "the failure produced a new discriminating residual",
                "use the registered challenge to convert productive failure into causal information",
            )
        return report(
            LearningControlVerdict.PERSIST_STRATEGY,
            "the current strategy is still generating genuinely new diagnostic information",
        )

    if progress is not None and progress > 0:
        return report(
            LearningControlVerdict.PERSIST_STRATEGY,
            "measured competence is improving on the current challenge family",
            "continue while progress or new discriminating information remains positive",
        )

    if case.independent_help_available and not _qualified_independent_help(case):
        if flat or case.repeated_equivalent_failures:
            return report(
                LearningControlVerdict.SWITCH_STRATEGY,
                "the proposed help lacks process/evidence-lineage independence and cannot receive independent-help credit",
                "same-context critique may inform a strategy switch but is not external assurance",
            )

    return report(
        LearningControlVerdict.CANNOT_CHECK,
        "the packet does not identify enough evidence to prefer persistence, switching, help, invention, or repair",
    )
