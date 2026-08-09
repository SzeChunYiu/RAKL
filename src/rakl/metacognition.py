from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MetacognitiveAuditVerdict(str, Enum):
    """Scoped outcomes of a RAKL metacognitive audit.

    These verdicts diagnose where additional checking is warranted.  None of
    them mints scientific authority, activates a method, or promotes a method
    challenger.
    """

    NO_AUDIT_REQUIRED = "NO_AUDIT_REQUIRED"
    CALIBRATED_NO_NEW_GAP = "CALIBRATED_NO_NEW_GAP"
    KNOWN_WEAKNESS = "KNOWN_WEAKNESS"
    CALIBRATION_WEAKNESS = "CALIBRATION_WEAKNESS"
    EXPLANATION_GAP = "EXPLANATION_GAP"
    ONTOLOGY_GAP_CANDIDATE = "ONTOLOGY_GAP_CANDIDATE"
    METHOD_BASIS_GAP_CANDIDATE = "METHOD_BASIS_GAP_CANDIDATE"
    INDEPENDENT_REVIEW_REQUIRED = "INDEPENDENT_REVIEW_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


_HIGH_VALUE_TRIGGERS = frozenset(
    {
        "HIGH_CONFIDENCE_ERROR",
        "REPEATED_UNCLASSIFIED_RESIDUAL",
        "TARGET_UNREACHABLE",
        "EXPLANATION_RECONSTRUCTION",
        "BIAS_RISK",
        "EXTERNAL_REVIEW",
        "DOMAIN_TRANSFER",
        "FEEDBACK_UPDATE",
        "HIGH_VALUE_CHECKPOINT",
    }
)


@dataclass(frozen=True)
class MetacognitiveAuditCase:
    """Evidence packet for one triggered method-completeness check.

    The packet deliberately separates internal/self-reported signals from
    externally observed outcome evidence.  Domain calibration, outside review,
    explanatory reconstruction and target reachability remain independently
    scoped coordinates rather than one scalar "self-awareness" score.
    """

    trigger_signals: tuple[str, ...] = ()
    reflection_cost: float = 0.0
    expected_failure_cost: float = 0.0

    outcome_evidence_available: bool | None = None
    known_failure_fiber: str | None = None
    repeated_unclassified_residuals: int = 0

    target_reachable: bool | None = None
    epistemic_cut_identified: bool | None = None
    incumbent_operator_can_resolve_cut: bool | None = None

    explanation_required_elements: tuple[str, ...] = ()
    explanation_provided_elements: tuple[str, ...] = ()

    countermodel_requested: bool = False
    countermodel_supplied: bool = False
    generic_be_unbiased_instruction_only: bool = False

    external_review_present: bool = False
    external_review_process_independent: bool | None = None
    external_review_lineage_independent: bool | None = None

    calibrated_domains: tuple[str, ...] = ()
    target_domain: str | None = None

    calibration_improved: bool | None = None
    task_sensitivity_improved: bool | None = None

    def __post_init__(self) -> None:
        if self.reflection_cost < 0:
            raise ValueError("reflection_cost cannot be negative")
        if self.expected_failure_cost < 0:
            raise ValueError("expected_failure_cost cannot be negative")
        if self.repeated_unclassified_residuals < 0:
            raise ValueError("repeated_unclassified_residuals cannot be negative")
        if any(not signal for signal in self.trigger_signals):
            raise ValueError("trigger_signals cannot contain empty values")
        if any(not item for item in self.explanation_required_elements):
            raise ValueError("explanation_required_elements cannot contain empty values")
        if any(not item for item in self.explanation_provided_elements):
            raise ValueError("explanation_provided_elements cannot contain empty values")
        if any(not domain for domain in self.calibrated_domains):
            raise ValueError("calibrated_domains cannot contain empty values")


@dataclass(frozen=True)
class MetacognitiveAuditReport:
    verdict: MetacognitiveAuditVerdict
    reasons: tuple[str, ...]
    missing_explanation_elements: tuple[str, ...] = ()
    independent_review_credit: bool | None = None
    requires_new_operator_benchmark: bool = False
    requires_ontology_benchmark: bool = False

    @property
    def capability_upgrade_authorized(self) -> bool:
        """Metacognitive diagnosis never proves a capability improvement."""

        return False

    @property
    def audit_opened_a_gap(self) -> bool:
        return self.verdict in {
            MetacognitiveAuditVerdict.CALIBRATION_WEAKNESS,
            MetacognitiveAuditVerdict.EXPLANATION_GAP,
            MetacognitiveAuditVerdict.ONTOLOGY_GAP_CANDIDATE,
            MetacognitiveAuditVerdict.METHOD_BASIS_GAP_CANDIDATE,
            MetacognitiveAuditVerdict.KNOWN_WEAKNESS,
        }


class MetacognitiveCompletenessAuditor:
    """Fail-closed diagnostic for weaknesses in RAKL's current method basis.

    The auditor is intentionally external-evidence-first.  It does not trust a
    model's confidence or generic introspection as proof that the model knows
    its own limits.  It merely classifies evidence packets into follow-up
    actions; repair, benchmarking, scientific-state mutation, and promotion are
    separate gates.
    """

    @staticmethod
    def assess(case: MetacognitiveAuditCase) -> MetacognitiveAuditReport:
        signals = frozenset(case.trigger_signals)

        def report(
            verdict: MetacognitiveAuditVerdict,
            reasons: tuple[str, ...] | list[str],
            *,
            missing: tuple[str, ...] = (),
            review_credit: bool | None = None,
            new_operator: bool = False,
            new_ontology: bool = False,
        ) -> MetacognitiveAuditReport:
            return MetacognitiveAuditReport(
                verdict=verdict,
                reasons=tuple(reasons),
                missing_explanation_elements=missing,
                independent_review_credit=review_credit,
                requires_new_operator_benchmark=new_operator,
                requires_ontology_benchmark=new_ontology,
            )

        if not signals:
            return report(
                MetacognitiveAuditVerdict.NO_AUDIT_REQUIRED,
                ("no registered metacognitive trigger is active",),
            )

        high_value = bool(signals & _HIGH_VALUE_TRIGGERS)
        if (
            not high_value
            and case.reflection_cost > case.expected_failure_cost
        ):
            return report(
                MetacognitiveAuditVerdict.NO_AUDIT_REQUIRED,
                (
                    "reflection cost exceeds the registered expected failure cost",
                    "no high-value metacognitive trigger overrides the cost gate",
                ),
            )

        # A triggered audit that depends on correctness/outcome evidence must not
        # substitute self-report for an absent external result.
        if case.outcome_evidence_available is not True:
            return report(
                MetacognitiveAuditVerdict.CANNOT_CHECK,
                ("external outcome evidence required by the triggered audit is unavailable",),
            )

        if "DOMAIN_TRANSFER" in signals:
            if not case.target_domain:
                return report(
                    MetacognitiveAuditVerdict.CANNOT_CHECK,
                    ("target domain for metacognitive transfer is unspecified",),
                )
            if case.target_domain not in set(case.calibrated_domains):
                return report(
                    MetacognitiveAuditVerdict.CANNOT_CHECK,
                    (
                        f"metacognitive calibration was not measured in target domain: {case.target_domain}",
                        "calibration is not globalized across fibers/domains",
                    ),
                )

        if "EXTERNAL_REVIEW" in signals or case.external_review_present:
            if not case.external_review_present:
                return report(
                    MetacognitiveAuditVerdict.INDEPENDENT_REVIEW_REQUIRED,
                    ("outside review was requested but no external review is present",),
                    review_credit=False,
                )
            if (
                case.external_review_process_independent is not True
                or case.external_review_lineage_independent is not True
            ):
                return report(
                    MetacognitiveAuditVerdict.INDEPENDENT_REVIEW_REQUIRED,
                    (
                        "review is not independently qualified on both process/context and evidence lineage",
                    ),
                    review_credit=False,
                )

        if case.countermodel_requested and not case.countermodel_supplied:
            reason = "explicit countermodel challenge was requested but not supplied"
            if case.generic_be_unbiased_instruction_only:
                reason += "; generic be-unbiased instruction is not a countermodel"
            return report(
                MetacognitiveAuditVerdict.INDEPENDENT_REVIEW_REQUIRED,
                (reason,),
                review_credit=(
                    True
                    if case.external_review_present
                    and case.external_review_process_independent is True
                    and case.external_review_lineage_independent is True
                    else None
                ),
            )

        if case.explanation_required_elements:
            required = set(case.explanation_required_elements)
            provided = set(case.explanation_provided_elements)
            missing = tuple(sorted(required - provided))
            if missing:
                return report(
                    MetacognitiveAuditVerdict.EXPLANATION_GAP,
                    tuple(
                        f"required explanatory element missing: {item}" for item in missing
                    ),
                    missing=missing,
                    review_credit=(
                        True
                        if case.external_review_present
                        and case.external_review_process_independent is True
                        and case.external_review_lineage_independent is True
                        else None
                    ),
                )

        if case.target_reachable is False:
            if case.epistemic_cut_identified is not True:
                return report(
                    MetacognitiveAuditVerdict.CANNOT_CHECK,
                    ("target is unreachable but the blocking epistemic cut is not identified",),
                )
            if case.incumbent_operator_can_resolve_cut is True:
                if case.known_failure_fiber:
                    return report(
                        MetacognitiveAuditVerdict.KNOWN_WEAKNESS,
                        (
                            f"blocking cut is covered by existing fiber: {case.known_failure_fiber}",
                            "reopen the incumbent fiber before inventing a new method operator",
                        ),
                    )
                return report(
                    MetacognitiveAuditVerdict.KNOWN_WEAKNESS,
                    (
                        "an incumbent operator can resolve the blocking cut; route to the existing method basis",
                    ),
                )
            if case.incumbent_operator_can_resolve_cut is False:
                return report(
                    MetacognitiveAuditVerdict.METHOD_BASIS_GAP_CANDIDATE,
                    (
                        "target is blocked by an identified epistemic cut",
                        "no incumbent operator is registered as able to resolve that cut",
                    ),
                    new_operator=True,
                )
            return report(
                MetacognitiveAuditVerdict.CANNOT_CHECK,
                ("ability of the incumbent operator basis to resolve the cut is unknown",),
            )

        if case.known_failure_fiber:
            return report(
                MetacognitiveAuditVerdict.KNOWN_WEAKNESS,
                (
                    f"observed weakness is already represented by fiber: {case.known_failure_fiber}",
                ),
            )

        if case.repeated_unclassified_residuals >= 2:
            return report(
                MetacognitiveAuditVerdict.ONTOLOGY_GAP_CANDIDATE,
                (
                    f"{case.repeated_unclassified_residuals} repeated residuals remain outside the incumbent failure taxonomy",
                    "open a separately benchmarked ontology-completeness fiber",
                ),
                new_ontology=True,
            )

        if "HIGH_CONFIDENCE_ERROR" in signals:
            return report(
                MetacognitiveAuditVerdict.CALIBRATION_WEAKNESS,
                (
                    "external outcome contradicts a high-confidence internal judgment",
                    "one unclassified error is insufficient to establish an ontology gap",
                ),
            )

        if "FEEDBACK_UPDATE" in signals:
            if case.calibration_improved is True and case.task_sensitivity_improved is False:
                return report(
                    MetacognitiveAuditVerdict.CALIBRATED_NO_NEW_GAP,
                    (
                        "feedback improved calibration without measured task-sensitivity improvement",
                        "calibration change is not represented as a capability upgrade",
                    ),
                )
            if case.calibration_improved is None or case.task_sensitivity_improved is None:
                return report(
                    MetacognitiveAuditVerdict.CANNOT_CHECK,
                    ("feedback effects on calibration and task sensitivity are incompletely measured",),
                )

        recognized = _HIGH_VALUE_TRIGGERS | {"LOW_VALUE_UNCERTAINTY"}
        unknown_signals = tuple(sorted(signals - recognized))
        if unknown_signals:
            return report(
                MetacognitiveAuditVerdict.CANNOT_CHECK,
                tuple(f"unregistered metacognitive trigger: {signal}" for signal in unknown_signals),
            )

        review_credit = None
        if case.external_review_present:
            review_credit = (
                case.external_review_process_independent is True
                and case.external_review_lineage_independent is True
            )

        return report(
            MetacognitiveAuditVerdict.CALIBRATED_NO_NEW_GAP,
            (
                "registered audit completed without evidence for a new weakness class",
                "absence of a detected gap is scoped to this audit packet and is not global self-knowledge",
            ),
            review_credit=review_credit,
        )
