from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MissingOperatorFailureCause(str, Enum):
    NONE = "NONE"
    MISSING_EVIDENCE_OR_MEASUREMENT = "MISSING_EVIDENCE_OR_MEASUREMENT"
    IMPLEMENTATION = "IMPLEMENTATION"
    METHOD_BASIS = "METHOD_BASIS"
    UNKNOWN = "UNKNOWN"


class MissingOperatorVerdict(str, Enum):
    NO_NEW_OPERATOR_REQUIRED = "NO_NEW_OPERATOR_REQUIRED"
    EVIDENCE_ACQUISITION_REQUIRED = "EVIDENCE_ACQUISITION_REQUIRED"
    IMPLEMENTATION_REPAIR_REQUIRED = "IMPLEMENTATION_REPAIR_REQUIRED"
    METHOD_BASIS_GAP_DETECTED_OPERATOR_UNIDENTIFIED = "METHOD_BASIS_GAP_DETECTED_OPERATOR_UNIDENTIFIED"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    OPERATOR_FAMILY_PROPOSAL_ONLY = "OPERATOR_FAMILY_PROPOSAL_ONLY"
    REFUTED = "REFUTED"
    CANNOT_COMPARE = "CANNOT_COMPARE"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class MissingOperatorTrial:
    """Sealed evaluator packet for prospective missing-operator discovery.

    Hidden operator-family labels belong to the evaluator, not the solver-visible
    context.  The packet distinguishes detecting a method-basis gap from
    identifying a resolving operator and from demonstrating fresh transfer.
    """

    world_id: str
    world_sha256: str
    evaluator_frozen_before_run: bool | None
    outcome_evidence_available: bool | None
    failure_cause: MissingOperatorFailureCause

    hidden_label_exposed_to_solver: bool = False
    hidden_label_exposed_via_retrieval: bool = False
    negative_history_preserved: bool | None = None
    resource_budget_matched: bool | None = None

    epistemic_cut_id: str | None = None
    incumbent_operator_can_resolve_cut: bool | None = None

    candidate_operator_family: str | None = None
    candidate_definition_frozen_before_answer: bool | None = None
    primary_resolution_passed: bool | None = None
    surviving_alternative_operator_families: tuple[str, ...] = ()
    discriminating_probe_available: bool | None = None

    fresh_transfer_world_id: str | None = None
    fresh_transfer_world_sha256: str | None = None
    fresh_transfer_surface_shifted: bool | None = None
    fresh_transfer_passed: bool | None = None

    independent_review_present: bool = False
    independent_review_process_context: bool | None = None
    independent_review_evidence_lineage: bool | None = None

    scientific_or_target_authority_claimed: bool = False
    method_promotion_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.world_id:
            raise ValueError("world_id cannot be empty")
        if not _SHA256_RE.fullmatch(self.world_sha256):
            raise ValueError("world_sha256 must be lowercase sha256")
        if self.fresh_transfer_world_sha256 is not None and not _SHA256_RE.fullmatch(
            self.fresh_transfer_world_sha256
        ):
            raise ValueError("fresh_transfer_world_sha256 must be lowercase sha256")
        if any(not item for item in self.surviving_alternative_operator_families):
            raise ValueError("surviving alternative operator families cannot contain empty values")


@dataclass(frozen=True)
class MissingOperatorReport:
    verdict: MissingOperatorVerdict
    reasons: tuple[str, ...]
    gap_detected: bool
    operator_family_identified: bool
    fresh_transfer_validated: bool
    independent_review_credit: bool
    eligible_for_matched_class_b_comparison: bool

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def establishes_framework_saturation(self) -> bool:
        return False


def evaluate_missing_operator_trial(trial: MissingOperatorTrial) -> MissingOperatorReport:
    """Fail closed on leakage, chronology, non-identifiability and transfer gaps."""

    def report(
        verdict: MissingOperatorVerdict,
        reasons: tuple[str, ...] | list[str],
        *,
        gap: bool = False,
        identified: bool = False,
        transfer: bool = False,
    ) -> MissingOperatorReport:
        independent_credit = bool(
            trial.independent_review_present
            and trial.independent_review_process_context is True
            and trial.independent_review_evidence_lineage is True
        )
        eligible = bool(
            trial.resource_budget_matched is True
            and trial.negative_history_preserved is True
            and verdict == MissingOperatorVerdict.OPERATOR_FAMILY_PROPOSAL_ONLY
            and transfer
            and not trial.scientific_or_target_authority_claimed
            and not trial.method_promotion_claimed
        )
        return MissingOperatorReport(
            verdict=verdict,
            reasons=tuple(reasons),
            gap_detected=gap,
            operator_family_identified=identified,
            fresh_transfer_validated=transfer,
            independent_review_credit=independent_credit,
            eligible_for_matched_class_b_comparison=eligible,
        )

    if trial.hidden_label_exposed_to_solver or trial.hidden_label_exposed_via_retrieval:
        return report(
            MissingOperatorVerdict.TRIAL_INVALID,
            ("evaluator-only hidden operator label leaked into solver-visible evidence",),
        )
    if trial.evaluator_frozen_before_run is False:
        return report(
            MissingOperatorVerdict.TRIAL_INVALID,
            ("evaluator or answer key was not frozen before the trial",),
        )
    if trial.evaluator_frozen_before_run is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("evaluator freeze chronology is unknown",),
        )
    if trial.negative_history_preserved is False:
        return report(
            MissingOperatorVerdict.TRIAL_INVALID,
            ("prior failed/null operator history was rewritten or removed",),
        )
    if trial.negative_history_preserved is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("negative-history preservation was not attested",),
        )
    if trial.scientific_or_target_authority_claimed or trial.method_promotion_claimed:
        return report(
            MissingOperatorVerdict.TRIAL_INVALID,
            ("a sealed discovery benchmark cannot self-grant scientific, target, or method-promotion authority",),
        )
    if trial.resource_budget_matched is False:
        return report(
            MissingOperatorVerdict.CANNOT_COMPARE,
            ("baseline and challenger resource ceilings are not matched",),
        )
    if trial.outcome_evidence_available is not True:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("external outcome evidence for the sealed world is unavailable",),
        )

    if trial.failure_cause == MissingOperatorFailureCause.MISSING_EVIDENCE_OR_MEASUREMENT:
        return report(
            MissingOperatorVerdict.EVIDENCE_ACQUISITION_REQUIRED,
            ("failure is attributable to missing evidence or measurement, not a method-basis gap",),
        )
    if trial.failure_cause == MissingOperatorFailureCause.IMPLEMENTATION:
        return report(
            MissingOperatorVerdict.IMPLEMENTATION_REPAIR_REQUIRED,
            ("failure is attributable to implementation, not a missing method operator",),
        )
    if trial.failure_cause == MissingOperatorFailureCause.UNKNOWN:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("failure cause is not identified well enough to infer a method-basis gap",),
        )
    if trial.failure_cause == MissingOperatorFailureCause.NONE:
        if trial.incumbent_operator_can_resolve_cut is False:
            return report(
                MissingOperatorVerdict.CANNOT_CHECK,
                ("failure cause is NONE but incumbent resolution is declared impossible",),
            )
        return report(
            MissingOperatorVerdict.NO_NEW_OPERATOR_REQUIRED,
            ("no method-basis failure is established",),
        )

    if trial.epistemic_cut_id is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("method-basis failure was proposed without an identified epistemic cut",),
        )
    if trial.incumbent_operator_can_resolve_cut is True:
        return report(
            MissingOperatorVerdict.NO_NEW_OPERATOR_REQUIRED,
            ("an incumbent operator can resolve the identified cut; reopen the incumbent fiber",),
        )
    if trial.incumbent_operator_can_resolve_cut is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("incumbent-basis ability to resolve the epistemic cut is unknown",),
            gap=True,
        )

    if not trial.candidate_operator_family:
        return report(
            MissingOperatorVerdict.METHOD_BASIS_GAP_DETECTED_OPERATOR_UNIDENTIFIED,
            ("incumbent basis cannot resolve the cut, but no candidate operator family is identified",),
            gap=True,
        )
    if trial.candidate_definition_frozen_before_answer is False:
        return report(
            MissingOperatorVerdict.TRIAL_INVALID,
            ("candidate operator semantics were expanded after answer exposure",),
            gap=True,
        )
    if trial.candidate_definition_frozen_before_answer is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("candidate operator freeze chronology is unknown",),
            gap=True,
        )
    if trial.primary_resolution_passed is False:
        return report(
            MissingOperatorVerdict.REFUTED,
            ("candidate operator did not resolve the frozen primary world",),
            gap=True,
        )
    if trial.primary_resolution_passed is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("candidate operator has not been tested against the frozen primary world",),
            gap=True,
        )

    if trial.surviving_alternative_operator_families:
        reasons = [
            "multiple operator families remain compatible with the frozen primary result",
        ]
        if trial.discriminating_probe_available is True:
            reasons.append("a discriminating probe is available and should be executed before operator identification")
        elif trial.discriminating_probe_available is None:
            reasons.append("availability of a discriminating probe is unknown")
        else:
            reasons.append("no currently registered probe separates the surviving operator families")
        return report(
            MissingOperatorVerdict.PARTIALLY_IDENTIFIED,
            reasons,
            gap=True,
        )

    if not trial.fresh_transfer_world_id or not trial.fresh_transfer_world_sha256:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("fresh transfer world identity is required before transferable operator discovery can be credited",),
            gap=True,
            identified=True,
        )
    if trial.fresh_transfer_surface_shifted is not True:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("fresh transfer world is not established as a surface-shifted or domain-shifted realization",),
            gap=True,
            identified=True,
        )
    if trial.fresh_transfer_passed is False:
        return report(
            MissingOperatorVerdict.PARTIALLY_IDENTIFIED,
            ("candidate resolved the development world but failed fresh transfer",),
            gap=True,
            identified=True,
        )
    if trial.fresh_transfer_passed is None:
        return report(
            MissingOperatorVerdict.CANNOT_CHECK,
            ("fresh transfer result is unavailable",),
            gap=True,
            identified=True,
        )

    return report(
        MissingOperatorVerdict.OPERATOR_FAMILY_PROPOSAL_ONLY,
        (
            "incumbent basis cannot resolve the frozen epistemic cut",
            "candidate operator resolved the primary sealed world",
            "candidate operator also resolved a frozen surface-shifted fresh-transfer world",
            "result remains proposal-only pending ordinary method promotion and external scientific validation",
        ),
        gap=True,
        identified=True,
        transfer=True,
    )
