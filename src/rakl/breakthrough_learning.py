from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class BreakthroughMode(str, Enum):
    ROUTINE_REUSE = "ROUTINE_REUSE"
    REFLECTIVE_RESTRUCTURE = "REFLECTIVE_RESTRUCTURE"
    CONTRASTIVE_DISCRIMINATION = "CONTRASTIVE_DISCRIMINATION"
    RETRIEVAL_REHEARSAL = "RETRIEVAL_REHEARSAL"
    DELIBERATE_PRACTICE = "DELIBERATE_PRACTICE"
    FIXATION_RESET = "FIXATION_RESET"
    INCUBATION_CONTEXT_ROTATION = "INCUBATION_CONTEXT_ROTATION"
    EXPLORATORY_RECOMBINATION = "EXPLORATORY_RECOMBINATION"
    EFFECTUAL_PROBE = "EFFECTUAL_PROBE"
    META_METHOD_BASIS_AUDIT = "META_METHOD_BASIS_AUDIT"


class LearningControlVerdict(str, Enum):
    PROPOSE = "PROPOSE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class NaivePriorProbe:
    """Non-authoritative pre-source snapshot used only to expose priors/fixation.

    This object is deliberately *not* a mathematical candidate, proof attempt, or
    novelty artifact.  It may capture provisional representations and assumptions
    before external method exposure, then be compared with the later source-bound
    context.  Its contents should be withheld from candidate generation until the
    strict context packet has been frozen when anchoring is a material risk.
    """

    probe_id: str
    atom_id: str
    frozen_at: str
    source_exposure_at: str | None
    provisional_representations: Tuple[str, ...]
    provisional_assumptions: Tuple[str, ...]
    predicted_obstacles: Tuple[str, ...]
    artifact_hash: str
    isolated_from_candidate_generation: bool = True


@dataclass(frozen=True)
class ExpertiseChunk:
    """Compiled retrieval aid distilled from scoped verified experience.

    A chunk accelerates recognition/retrieval.  It never upgrades theorem,
    evidence, novelty, or review authority.
    """

    chunk_id: str
    cue_signature: Tuple[str, ...]
    deep_structure: Tuple[str, ...]
    tool_ids: Tuple[str, ...]
    failure_warning_ids: Tuple[str, ...]
    applicability_conditions: Tuple[str, ...]
    non_applicability_conditions: Tuple[str, ...]
    contrastive_near_misses: Tuple[str, ...]
    retrieval_probes: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class LearningControlSignals:
    """Externally supplied signals for proposal-only strategy switching.

    The controller deliberately consumes registered signals instead of inferring
    hidden model confidence from prose.  Unknown values stay explicit.
    """

    familiar_context_match: bool | None = None
    applicability_witness_passed: bool | None = None
    conflicting_cues: bool = False
    novel_structural_coordinate: bool = False
    repeated_failure_count: int = 0
    failure_redundancy_high: bool = False
    epistemic_gain_flat: bool = False
    search_diversity_high: bool = False
    context_coverage_high: bool = False
    fixation_risk: bool = False
    retrieval_uncertain: bool = False
    controllable_probe_available: bool = False
    mature_tool_available: bool = False
    transfer_boundary_unstable: bool = False

    def __post_init__(self) -> None:
        if self.repeated_failure_count < 0:
            raise ValueError("repeated_failure_count cannot be negative")


@dataclass(frozen=True)
class LearningControlReport:
    verdict: LearningControlVerdict
    modes: Tuple[BreakthroughMode, ...]
    reasons: Tuple[str, ...]

    @property
    def authority_created(self) -> bool:
        return False


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def validate_naive_prior_probe(probe: NaivePriorProbe) -> Tuple[str, ...]:
    reasons: list[str] = []
    for name in ("probe_id", "atom_id", "artifact_hash"):
        if not getattr(probe, name):
            reasons.append(f"naive_prior:{name}_missing")
    frozen_at = _parse_time(probe.frozen_at)
    if frozen_at is None:
        reasons.append("naive_prior:frozen_at_missing_or_invalid")
    if probe.source_exposure_at is not None:
        exposed = _parse_time(probe.source_exposure_at)
        if exposed is None:
            reasons.append("naive_prior:source_exposure_at_invalid")
        elif frozen_at is not None and frozen_at >= exposed:
            reasons.append("naive_prior:not_frozen_before_source_exposure")
    if not probe.provisional_representations:
        reasons.append("naive_prior:representations_missing")
    if not probe.provisional_assumptions:
        reasons.append("naive_prior:assumptions_missing")
    if not probe.predicted_obstacles:
        reasons.append("naive_prior:predicted_obstacles_missing")
    if not probe.isolated_from_candidate_generation:
        reasons.append("naive_prior:not_isolated_from_candidate_generation")
    return tuple(reasons)


def validate_expertise_chunk(chunk: ExpertiseChunk) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not chunk.chunk_id:
        reasons.append("expertise_chunk:id_missing")
    if not chunk.cue_signature:
        reasons.append("expertise_chunk:cue_signature_missing")
    if not chunk.deep_structure:
        reasons.append("expertise_chunk:deep_structure_missing")
    if not (chunk.tool_ids or chunk.failure_warning_ids):
        reasons.append("expertise_chunk:no_experience_links")
    if not chunk.applicability_conditions:
        reasons.append("expertise_chunk:applicability_conditions_missing")
    if not chunk.non_applicability_conditions:
        reasons.append("expertise_chunk:non_applicability_conditions_missing")
    if not chunk.contrastive_near_misses:
        reasons.append("expertise_chunk:contrastive_near_misses_missing")
    if not chunk.retrieval_probes:
        reasons.append("expertise_chunk:retrieval_probes_missing")
    if not chunk.evidence_pointers:
        reasons.append("expertise_chunk:evidence_pointers_missing")
    if not chunk.artifact_hash:
        reasons.append("expertise_chunk:artifact_hash_missing")
    return tuple(reasons)


def recommend_breakthrough_modes(signals: LearningControlSignals) -> LearningControlReport:
    """Recommend strategy modes without minting scientific authority.

    The ordering is intentional: safe routine reuse is preferred when exact scope
    evidence supports it; conflict/novelty/fixation override routine execution;
    persistent high-diversity/high-context stagnation escalates to a method-basis
    audit instead of endless same-basis search. Missing evidence alone never
    activates an expensive reflective/retrieval mode.
    """

    modes: list[BreakthroughMode] = []
    reasons: list[str] = []

    routine_safe = (
        signals.familiar_context_match is True
        and signals.applicability_witness_passed is True
        and not signals.conflicting_cues
        and not signals.novel_structural_coordinate
        and not signals.fixation_risk
    )
    if routine_safe:
        modes.append(BreakthroughMode.ROUTINE_REUSE)
        reasons.append("familiar_context_has_passing_applicability_witness_without_conflict")

    if (
        signals.conflicting_cues
        or signals.novel_structural_coordinate
        or signals.applicability_witness_passed is False
    ):
        modes.append(BreakthroughMode.REFLECTIVE_RESTRUCTURE)
        reasons.append("registered_conflict_or_scope_violation_requires_reflective_restructure")

    if signals.conflicting_cues or signals.novel_structural_coordinate:
        modes.append(BreakthroughMode.CONTRASTIVE_DISCRIMINATION)
        reasons.append("contrastive_cases_can_localize_the_discriminating_coordinate")

    if signals.retrieval_uncertain:
        modes.append(BreakthroughMode.RETRIEVAL_REHEARSAL)
        reasons.append("registered_retrieval_uncertainty_requires_a_retrieval_probe")

    if signals.mature_tool_available and signals.transfer_boundary_unstable:
        modes.append(BreakthroughMode.DELIBERATE_PRACTICE)
        reasons.append("mature_tool_has_unstable_transfer_boundary")

    repeated_flat = signals.epistemic_gain_flat and signals.repeated_failure_count >= 2
    if signals.fixation_risk or repeated_flat:
        modes.append(BreakthroughMode.FIXATION_RESET)
        reasons.append("fixation_or_repeated_flat_failure_detected")
        modes.append(BreakthroughMode.INCUBATION_CONTEXT_ROTATION)
        reasons.append("fresh_context_rehydration_may_reduce_candidate_narrative_lock_in")

    if signals.epistemic_gain_flat and signals.search_diversity_high:
        modes.append(BreakthroughMode.EXPLORATORY_RECOMBINATION)
        reasons.append("high_diversity_search_is_flat_so_bounded_cross_basis_recombination_is_warranted")

    if signals.controllable_probe_available and (
        signals.conflicting_cues
        or signals.novel_structural_coordinate
        or signals.epistemic_gain_flat
    ):
        modes.append(BreakthroughMode.EFFECTUAL_PROBE)
        reasons.append("controllable_probe_can_change_the_information_state_when_global_prediction_is_weak")

    if (
        signals.epistemic_gain_flat
        and signals.search_diversity_high
        and signals.context_coverage_high
        and signals.repeated_failure_count >= 2
        and signals.failure_redundancy_high
    ):
        modes.append(BreakthroughMode.META_METHOD_BASIS_AUDIT)
        reasons.append("high_coverage_high_diversity_stagnation_with_redundant_failures_supports_method_basis_audit")

    unique_modes = tuple(dict.fromkeys(modes))
    if not unique_modes:
        return LearningControlReport(
            LearningControlVerdict.CANNOT_CHECK,
            (),
            ("registered_signals_do_not_support_a_specific_learning_mode",),
        )
    return LearningControlReport(
        LearningControlVerdict.PROPOSE,
        unique_modes,
        tuple(reasons),
    )
