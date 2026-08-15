"""QUESTION-vs-MEASUREMENT responsibility discriminator for Recursive Framework Audit.

The retrospective negative frontier cannot express QUESTION-level causes, so
`QUESTION: 0` is a CANNOT_CHECK rather than evidence that the programme's
question is correct.  The frozen RFA already returns RUN_DISCRIMINATOR when
QUESTION and MEASUREMENT are both plausible.  This module supplies the missing
intervention evidence object; it does not alter the RFA decision chain or grant
scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .recursive_framework_audit import AuditCoordinate, AuditResidual


class InterventionOutcome(str, Enum):
    RESIDUAL_RESOLVED = "RESIDUAL_RESOLVED"
    RESIDUAL_PERSISTS = "RESIDUAL_PERSISTS"
    CANNOT_CHECK = "CANNOT_CHECK"


class ResponsibilityVerdict(str, Enum):
    QUESTION_RESPONSIBLE = "QUESTION_RESPONSIBLE"
    MEASUREMENT_RESPONSIBLE = "MEASUREMENT_RESPONSIBLE"
    BOTH_PLAUSIBLE = "BOTH_PLAUSIBLE"
    JOINT_ONLY = "JOINT_ONLY"
    NEITHER_LOCAL = "NEITHER_LOCAL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ResponsibilityDiscriminatorContract:
    residual_id: str
    question_intervention_id: str
    measurement_intervention_id: str
    evaluator_epoch: str
    evidence_cutoff: str
    resource_contract: str

    def __post_init__(self) -> None:
        for field_name in (
            "residual_id",
            "question_intervention_id",
            "measurement_intervention_id",
            "evaluator_epoch",
            "evidence_cutoff",
            "resource_contract",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")
        if self.question_intervention_id == self.measurement_intervention_id:
            raise ValueError("question and measurement interventions must be distinct")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ResponsibilityDiscriminatorEvidence:
    residual_id: str
    question_intervention_id: str
    measurement_intervention_id: str
    evaluator_epoch: str
    evidence_cutoff: str
    resource_contract: str
    baseline_outcome: InterventionOutcome
    question_only_outcome: InterventionOutcome
    measurement_only_outcome: InterventionOutcome
    joint_outcome: InterventionOutcome
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResponsibilityDecision:
    residual_id: str
    verdict: ResponsibilityVerdict
    identified_coordinates: tuple[AuditCoordinate, ...]
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def uniquely_localized(self) -> bool:
        return self.verdict in {
            ResponsibilityVerdict.QUESTION_RESPONSIBLE,
            ResponsibilityVerdict.MEASUREMENT_RESPONSIBLE,
        }


def _identity_mismatches(
    contract: ResponsibilityDiscriminatorContract,
    evidence: ResponsibilityDiscriminatorEvidence,
) -> tuple[str, ...]:
    mismatches: list[str] = []
    for field_name in (
        "residual_id",
        "question_intervention_id",
        "measurement_intervention_id",
        "evaluator_epoch",
        "evidence_cutoff",
        "resource_contract",
    ):
        if getattr(contract, field_name) != getattr(evidence, field_name):
            mismatches.append(field_name)
    return tuple(mismatches)


def assess_responsibility(
    contract: ResponsibilityDiscriminatorContract,
    evidence: ResponsibilityDiscriminatorEvidence,
) -> ResponsibilityDecision:
    """Localize responsibility without revising either coordinate by default."""

    mismatches = _identity_mismatches(contract, evidence)
    if mismatches:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.CANNOT_CHECK,
            (),
            (f"evidence is not bound to the frozen contract: {list(mismatches)}",),
        )

    outcomes = (
        evidence.baseline_outcome,
        evidence.question_only_outcome,
        evidence.measurement_only_outcome,
        evidence.joint_outcome,
    )
    if InterventionOutcome.CANNOT_CHECK in outcomes:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.CANNOT_CHECK,
            (),
            ("at least one registered intervention outcome is unavailable; missing evidence is not no effect",),
        )
    if evidence.baseline_outcome is InterventionOutcome.RESIDUAL_RESOLVED:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.CANNOT_CHECK,
            (),
            ("baseline residual is already resolved, so there is no live responsibility question to localize",),
        )

    q = evidence.question_only_outcome is InterventionOutcome.RESIDUAL_RESOLVED
    m = evidence.measurement_only_outcome is InterventionOutcome.RESIDUAL_RESOLVED
    joint = evidence.joint_outcome is InterventionOutcome.RESIDUAL_RESOLVED

    if q and not m:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.QUESTION_RESPONSIBLE,
            (AuditCoordinate.QUESTION,),
            ("question-only intervention resolves the residual while measurement-only does not",),
        )
    if m and not q:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.MEASUREMENT_RESPONSIBLE,
            (AuditCoordinate.MEASUREMENT,),
            ("measurement-only intervention resolves the residual while question-only does not",),
        )
    if q and m:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.BOTH_PLAUSIBLE,
            (AuditCoordinate.QUESTION, AuditCoordinate.MEASUREMENT),
            ("both single-coordinate interventions resolve the residual; responsibility is not uniquely identified",),
        )
    if joint:
        return ResponsibilityDecision(
            contract.residual_id,
            ResponsibilityVerdict.JOINT_ONLY,
            (AuditCoordinate.QUESTION, AuditCoordinate.MEASUREMENT),
            ("neither coordinate alone resolves the residual but their joint intervention does; interaction remains",),
        )
    return ResponsibilityDecision(
        contract.residual_id,
        ResponsibilityVerdict.NEITHER_LOCAL,
        (),
        ("neither local coordinate nor their joint intervention resolves the residual; broaden the audit rather than force a reframe",),
    )


def project_identified_residual(decision: ResponsibilityDecision) -> AuditResidual | None:
    """Project only identified responsibility into the existing RFA residual.

    `NEITHER_LOCAL` and `CANNOT_CHECK` deliberately return ``None``: inventing a
    cause merely to make the frozen chain return an action would undo the point
    of the discriminator.
    """

    if not decision.identified_coordinates:
        return None
    return AuditResidual(plausible_causes=decision.identified_coordinates)


__all__ = [
    "InterventionOutcome",
    "ResponsibilityDecision",
    "ResponsibilityDiscriminatorContract",
    "ResponsibilityDiscriminatorEvidence",
    "ResponsibilityVerdict",
    "assess_responsibility",
    "project_identified_residual",
]
