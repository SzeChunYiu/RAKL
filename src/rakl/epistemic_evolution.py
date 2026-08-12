"""Governed Self-RAKL tournament policy for epistemic/search variants (#434).

RAKL already has the core self-evolution machinery in :mod:`rakl.evolution`
and :mod:`rakl.evolution_archive`: blind assurance reserves, protected
attestations, append-only variants, rollback targets and governance-gated
incumbent promotion.

This module adds a stricter *selection/evidence policy* around that machinery.
It prevents a framework challenger from earning promotion eligibility by:

* reusing cases that motivated or tuned the challenger;
* relying on positive point estimates without typed inferential evidence;
* trading a hard epistemic/safety regression for a larger capability gain;
* winning only because it consumed more resources; or
* treating competitor/literature inspiration as promotion evidence.

A successful assessment is only **promotion eligibility**.  Actual incumbent
promotion remains owned by the protected governance path in
``evolution_archive.promote_incumbent``.  Nothing here can mint scientific
claim authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple

from .evolution import EvolutionTrial, EvolutionVerdict, SelfEvolutionAssessor

__all__ = [
    "EvolutionSurface",
    "FrameworkVariantCard",
    "InferentialState",
    "MetaOverfitReport",
    "QoIInference",
    "TournamentAssessment",
    "TournamentDecision",
    "TournamentEvidence",
    "assess_framework_challenger",
    "detect_meta_overfit",
]


class EvolutionSurface(str, Enum):
    CLAIM_EVIDENCE_BINDING = "CLAIM_EVIDENCE_BINDING"
    AUTHORITY_TRANSPORT = "AUTHORITY_TRANSPORT"
    ROOT_INDEPENDENCE = "ROOT_INDEPENDENCE"
    EVIDENCE_SUFFICIENCY = "EVIDENCE_SUFFICIENCY"
    MECHANISM_FIDELITY = "MECHANISM_FIDELITY"
    REVISION_SUPERSESSION = "REVISION_SUPERSESSION"
    CRAWL_POLICY = "CRAWL_POLICY"
    QUERY_COMPILATION = "QUERY_COMPILATION"
    RETRIEVAL_POLICY = "RETRIEVAL_POLICY"
    RANKING = "RANKING"
    DIVERSIFICATION = "DIVERSIFICATION"
    INTERACTION_SPACE = "INTERACTION_SPACE"
    ANTI_EPISTEMIC_SPAM = "ANTI_EPISTEMIC_SPAM"
    SEARCH_FEEDBACK = "SEARCH_FEEDBACK"
    PLANNING_SEARCH = "PLANNING_SEARCH"


class InferentialState(str, Enum):
    DISTINGUISHABLE_BENEFIT = "DISTINGUISHABLE_BENEFIT"
    DISTINGUISHABLE_HARM = "DISTINGUISHABLE_HARM"
    MEASURED_BUT_INDISTINGUISHABLE = "MEASURED_BUT_INDISTINGUISHABLE"
    UNDERPOWERED = "UNDERPOWERED"
    CANNOT_IDENTIFY = "CANNOT_IDENTIFY"
    INVALID_CONTAMINATED = "INVALID_CONTAMINATED"


class TournamentDecision(str, Enum):
    CHALLENGER_DEVELOPMENT_PROMISING = "CHALLENGER_DEVELOPMENT_PROMISING"
    PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE = "PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE"
    PROMOTE_SCOPED_IMPROVEMENT_ELIGIBLE = "PROMOTE_SCOPED_IMPROVEMENT_ELIGIBLE"
    REJECT_NO_FRESH_GAIN = "REJECT_NO_FRESH_GAIN"
    REJECT_NONCOMPENSATORY_REGRESSION = "REJECT_NONCOMPENSATORY_REGRESSION"
    REJECT_RESOURCE_ONLY_GAIN = "REJECT_RESOURCE_ONLY_GAIN"
    REJECT_OVERFIT = "REJECT_OVERFIT"
    CANNOT_IDENTIFY = "CANNOT_IDENTIFY"
    KEEP_EXPERIMENTAL = "KEEP_EXPERIMENTAL"
    INVALID = "INVALID"


@dataclass(frozen=True)
class FrameworkVariantCard:
    """Frozen identity/provenance card for one framework challenger."""

    variant_id: str
    parent_version: str
    surfaces_changed: Tuple[EvolutionSurface, ...]
    triggering_evidence_ids: Tuple[str, ...]
    root_cause_receipt_ids: Tuple[str, ...]
    external_inspirations: Tuple[str, ...]
    difference_witness_hash: str
    hypothesized_gain_qois: Tuple[str, ...]
    specific_falsifiers: Tuple[str, ...]
    protected_invariants: Tuple[str, ...]
    motivating_case_ids: Tuple[str, ...]
    development_case_ids: Tuple[str, ...]
    fresh_assurance_case_ids: Tuple[str, ...]
    rollback_variant_id: str
    resource_delta: Tuple[Tuple[str, float], ...] = ()
    frozen_before_fresh_assurance: bool | None = None

    def __post_init__(self) -> None:
        if not self.variant_id.strip() or not self.parent_version.strip():
            raise ValueError("framework variant card requires variant and parent identities")
        if not self.surfaces_changed:
            raise ValueError("framework variant card requires at least one changed surface")
        if not self.difference_witness_hash.strip():
            raise ValueError("framework variant card requires a DifferenceWitness hash")
        if not self.root_cause_receipt_ids:
            raise ValueError("framework challenger requires a root-cause receipt")
        if not self.specific_falsifiers:
            raise ValueError("framework challenger requires a specific falsifier")
        if not self.protected_invariants:
            raise ValueError("framework challenger requires protected invariants")
        if not self.development_case_ids:
            raise ValueError("framework challenger requires development cases")
        if not self.fresh_assurance_case_ids:
            raise ValueError("framework challenger requires fresh assurance cases")
        if self.variant_id == self.parent_version:
            raise ValueError("challenger variant must differ from parent")
        if len(set(self.surfaces_changed)) != len(self.surfaces_changed):
            raise ValueError("changed surfaces must be unique")
        if len(set(self.development_case_ids)) != len(self.development_case_ids):
            raise ValueError("development case ids must be unique")
        if len(set(self.fresh_assurance_case_ids)) != len(self.fresh_assurance_case_ids):
            raise ValueError("fresh assurance case ids must be unique")
        exposed = set(self.motivating_case_ids) | set(self.development_case_ids)
        overlap = exposed & set(self.fresh_assurance_case_ids)
        if overlap:
            raise ValueError(
                "fresh assurance overlaps motivating/development cases: "
                + ",".join(sorted(overlap))
            )
        resource_names = [name for name, _ in self.resource_delta]
        if len(resource_names) != len(set(resource_names)):
            raise ValueError("resource delta keys must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class QoIInference:
    """Typed inference for a QoI, oriented so positive delta means better."""

    qoi: str
    state: InferentialState
    point_delta: float | None = None
    hard_protected: bool = False

    def __post_init__(self) -> None:
        if not self.qoi.strip():
            raise ValueError("QoI inference requires a qoi name")


@dataclass(frozen=True)
class TournamentEvidence:
    trial: EvolutionTrial
    development_inference: Tuple[QoIInference, ...]
    fresh_assurance_inference: Tuple[QoIInference, ...]
    regression_atlas_passed: bool | None
    resource_only_gain: bool = False
    history_preserved: bool = True
    competitor_or_parent_control_bound: bool | None = None


@dataclass(frozen=True)
class TournamentAssessment:
    decision: TournamentDecision
    reasons: Tuple[str, ...]
    development_benefit_qois: Tuple[str, ...] = ()
    fresh_benefit_qois: Tuple[str, ...] = ()
    hard_regression_qois: Tuple[str, ...] = ()
    underlying_evolution_verdict: EvolutionVerdict | None = None

    @property
    def promotion_eligible(self) -> bool:
        return self.decision in {
            TournamentDecision.PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE,
            TournamentDecision.PROMOTE_SCOPED_IMPROVEMENT_ELIGIBLE,
        }

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def promotes_incumbent(self) -> bool:
        return False


@dataclass(frozen=True)
class MetaOverfitReport:
    evaluated_epochs: int
    development_promising_epochs: int
    fresh_failure_epochs: int
    meta_overfit: bool
    affected_variant_ids: Tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _by_qoi(items: Sequence[QoIInference]) -> Mapping[str, QoIInference]:
    result: dict[str, QoIInference] = {}
    for item in items:
        if item.qoi in result:
            raise ValueError(f"duplicate inferential QoI: {item.qoi}")
        result[item.qoi] = item
    return result


def assess_framework_challenger(
    card: FrameworkVariantCard,
    evidence: TournamentEvidence,
) -> TournamentAssessment:
    """Evaluate fresh promotion eligibility without mutating the evolution archive."""

    reasons: list[str] = []
    trial = evidence.trial
    if trial.parent_version != card.parent_version:
        reasons.append("trial_parent_does_not_match_variant_card")
    if trial.child_version != card.variant_id:
        reasons.append("trial_child_does_not_match_variant_card")
    if trial.development_benchmark_id == trial.assurance_benchmark_id:
        reasons.append("development_and_assurance_benchmark_identity_must_differ")
    if card.frozen_before_fresh_assurance is None:
        return TournamentAssessment(
            TournamentDecision.CANNOT_IDENTIFY,
            ("challenger_freeze_chronology_unknown",),
        )
    if card.frozen_before_fresh_assurance is False:
        reasons.append("challenger_was_mutated_after_fresh_assurance_access")
    if not evidence.history_preserved:
        reasons.append("variant_history_not_preserved")
    if reasons:
        return TournamentAssessment(TournamentDecision.INVALID, tuple(reasons))

    development = _by_qoi(evidence.development_inference)
    fresh = _by_qoi(evidence.fresh_assurance_inference)
    if not development or not fresh:
        return TournamentAssessment(
            TournamentDecision.CANNOT_IDENTIFY,
            ("typed_development_and_fresh_inference_are_required",),
        )

    invalid_states = {InferentialState.INVALID_CONTAMINATED}
    cannot_states = {InferentialState.CANNOT_IDENTIFY}
    if any(item.state in invalid_states for item in (*development.values(), *fresh.values())):
        return TournamentAssessment(
            TournamentDecision.INVALID,
            ("at_least_one_registered_qoi_is_invalid_or_contaminated",),
        )
    if any(item.state in cannot_states for item in fresh.values()):
        return TournamentAssessment(
            TournamentDecision.CANNOT_IDENTIFY,
            ("fresh_assurance_contains_cannot_identify_qoi",),
        )

    development_benefits = tuple(
        sorted(qoi for qoi, item in development.items() if item.state is InferentialState.DISTINGUISHABLE_BENEFIT)
    )
    fresh_benefits = tuple(
        sorted(qoi for qoi, item in fresh.items() if item.state is InferentialState.DISTINGUISHABLE_BENEFIT)
    )
    hard_regressions = tuple(
        sorted(
            qoi
            for qoi, item in fresh.items()
            if item.hard_protected and item.state is InferentialState.DISTINGUISHABLE_HARM
        )
    )

    if evidence.resource_only_gain:
        return TournamentAssessment(
            TournamentDecision.REJECT_RESOURCE_ONLY_GAIN,
            ("fresh gain is attributed only to additional resources",),
            development_benefits,
            fresh_benefits,
            hard_regressions,
        )
    if hard_regressions:
        return TournamentAssessment(
            TournamentDecision.REJECT_NONCOMPENSATORY_REGRESSION,
            tuple(f"hard protected regression: {qoi}" for qoi in hard_regressions),
            development_benefits,
            fresh_benefits,
            hard_regressions,
        )
    if evidence.regression_atlas_passed is None:
        return TournamentAssessment(
            TournamentDecision.CANNOT_IDENTIFY,
            ("regression atlas status is unknown",),
            development_benefits,
            fresh_benefits,
        )
    if evidence.regression_atlas_passed is False:
        return TournamentAssessment(
            TournamentDecision.REJECT_NONCOMPENSATORY_REGRESSION,
            ("historical hostile regression atlas failed",),
            development_benefits,
            fresh_benefits,
        )

    evolution = SelfEvolutionAssessor.assess(trial)

    if not development_benefits:
        underpowered = any(item.state is InferentialState.UNDERPOWERED for item in development.values())
        decision = TournamentDecision.KEEP_EXPERIMENTAL if underpowered else TournamentDecision.REJECT_NO_FRESH_GAIN
        return TournamentAssessment(
            decision,
            ("no distinguishable development benefit under typed inference",),
            development_benefits,
            fresh_benefits,
            underlying_evolution_verdict=evolution.verdict,
        )

    fresh_harms = tuple(
        sorted(qoi for qoi, item in fresh.items() if item.state is InferentialState.DISTINGUISHABLE_HARM)
    )
    if fresh_harms or evolution.verdict is EvolutionVerdict.META_OVERFIT:
        return TournamentAssessment(
            TournamentDecision.REJECT_OVERFIT,
            tuple(f"fresh assurance harm/regression: {qoi}" for qoi in fresh_harms)
            or ("underlying SelfEvolutionAssessor classified META_OVERFIT",),
            development_benefits,
            fresh_benefits,
            hard_regressions,
            evolution.verdict,
        )

    if not fresh_benefits:
        if any(item.state is InferentialState.UNDERPOWERED for item in fresh.values()):
            decision = TournamentDecision.KEEP_EXPERIMENTAL
            why = "fresh assurance is underpowered; no promotion decision"
        else:
            decision = TournamentDecision.REJECT_NO_FRESH_GAIN
            why = "development benefit did not generalize distinguishably to fresh assurance"
        return TournamentAssessment(
            decision,
            (why,),
            development_benefits,
            fresh_benefits,
            hard_regressions,
            evolution.verdict,
        )

    # Existing SelfEvolutionAssessor is necessary but no longer sufficient: its
    # point-estimate layer must also clear the typed inference and freshness
    # policy above.
    if evolution.verdict is not EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE:
        return TournamentAssessment(
            TournamentDecision.CANNOT_IDENTIFY,
            ("underlying protected SelfEvolutionAssessor did not reach scoped evolution evidence",)
            + tuple(evolution.reasons),
            development_benefits,
            fresh_benefits,
            hard_regressions,
            evolution.verdict,
        )

    if evidence.competitor_or_parent_control_bound is False:
        return TournamentAssessment(
            TournamentDecision.KEEP_EXPERIMENTAL,
            ("registered strongest parent/competitor control was not bound",),
            development_benefits,
            fresh_benefits,
            hard_regressions,
            evolution.verdict,
        )

    hypothesized = set(card.hypothesized_gain_qois)
    fresh_set = set(fresh_benefits)
    if hypothesized and hypothesized.issubset(fresh_set):
        decision = TournamentDecision.PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE
        why = "all preregistered gain QoIs generalized distinguishably with no hard regression"
    else:
        decision = TournamentDecision.PROMOTE_SCOPED_IMPROVEMENT_ELIGIBLE
        why = "a proper subset/new subset of QoIs generalized; promotion must remain scoped"

    return TournamentAssessment(
        decision,
        (why, "actual incumbent promotion still requires protected governance"),
        development_benefits,
        fresh_benefits,
        hard_regressions,
        evolution.verdict,
    )


def detect_meta_overfit(
    assessments: Sequence[tuple[str, TournamentAssessment]],
    *,
    minimum_promising_epochs: int = 2,
) -> MetaOverfitReport:
    """Detect a recurring dev-success/fresh-failure pattern across variants."""

    if minimum_promising_epochs < 1:
        raise ValueError("minimum_promising_epochs must be positive")
    promising = 0
    fresh_failures = 0
    affected: list[str] = []
    for variant_id, assessment in assessments:
        if assessment.development_benefit_qois:
            promising += 1
        if assessment.development_benefit_qois and assessment.decision in {
            TournamentDecision.REJECT_NO_FRESH_GAIN,
            TournamentDecision.REJECT_OVERFIT,
            TournamentDecision.REJECT_NONCOMPENSATORY_REGRESSION,
        }:
            fresh_failures += 1
            affected.append(variant_id)
    meta = promising >= minimum_promising_epochs and fresh_failures == promising
    return MetaOverfitReport(
        evaluated_epochs=len(assessments),
        development_promising_epochs=promising,
        fresh_failure_epochs=fresh_failures,
        meta_overfit=meta,
        affected_variant_ids=tuple(affected),
    )
