from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class FailureDiagnosisStatus(str, Enum):
    OBSERVED_ONLY = "OBSERVED_ONLY"
    HYPOTHESIS = "HYPOTHESIS"
    SUPPORTED = "SUPPORTED"
    VERIFIED_IMPOSSIBILITY = "VERIFIED_IMPOSSIBILITY"
    SUPERSEDED = "SUPERSEDED"


class FailureRelation(str, Enum):
    INSTANCE_OF = "INSTANCE_OF"
    SHARES_RESIDUAL_WITH = "SHARES_RESIDUAL_WITH"
    SHARES_BROKEN_ASSUMPTION_WITH = "SHARES_BROKEN_ASSUMPTION_WITH"
    SAME_METHOD_FAMILY_AS = "SAME_METHOD_FAMILY_AS"
    CONTEXT_SPECIALIZATION_OF = "CONTEXT_SPECIALIZATION_OF"
    SUPERSEDES_DIAGNOSIS = "SUPERSEDES_DIAGNOSIS"
    CONTRADICTED_BY_SUCCESS = "CONTRADICTED_BY_SUCCESS"
    RESOLVED_BY = "RESOLVED_BY"
    TRANSFER_WARNING_FOR = "TRANSFER_WARNING_FOR"
    MOTIVATES_META_ATOM = "MOTIVATES_META_ATOM"


class ReuseVerdict(str, Enum):
    NO_RELEVANT_FAILURE_FOUND = "NO_RELEVANT_FAILURE_FOUND"
    SAME_CONTEXT_RETRY = "SAME_CONTEXT_RETRY"
    DIFFERENCE_WITNESSED = "DIFFERENCE_WITNESSED"
    PRIOR_FAILURE_NOT_APPLICABLE = "PRIOR_FAILURE_NOT_APPLICABLE"
    GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY = "GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY"


@dataclass(frozen=True)
class FailureExperience:
    failure_id: str
    atom_id: str
    candidate_id: str
    context_packet_hash: str
    research_trace_event_id: str
    method_family: str
    failure_mode: str
    residual_signature: Tuple[str, ...]
    broken_assumptions: Tuple[str, ...]
    scope_conditions: Tuple[str, ...]
    competing_diagnoses: Tuple[str, ...]
    selected_diagnosis: str
    diagnosis_status: FailureDiagnosisStatus
    evidence_pointers: Tuple[str, ...]
    falsifier_or_attempt: str
    observed_result: str
    artifact_hash: str
    timestamp: str
    local_repair_attempts: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FailureLink:
    source_id: str
    target_id: str
    relation: FailureRelation
    rationale: str
    evidence_pointers: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FailureExperienceLattice:
    experiences: Tuple[FailureExperience, ...] = ()
    links: Tuple[FailureLink, ...] = ()


@dataclass(frozen=True)
class DifferenceWitness:
    target_atom_id: str
    target_context_hash: str
    method_family: str
    prior_failure_ids: Tuple[str, ...]
    changed_structural_coordinates: Tuple[str, ...]
    restored_or_replaced_assumptions: Tuple[str, ...]
    prior_falsifier_escape_reason: str
    cheapest_repeat_failure_test: str
    evidence_pointers: Tuple[str, ...]


@dataclass(frozen=True)
class FailureReuseAssessment:
    verdict: ReuseVerdict
    relevant_failure_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]


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


def validate_failure_experience(experience: FailureExperience) -> Tuple[str, ...]:
    reasons: list[str] = []
    for field_name in (
        "failure_id",
        "atom_id",
        "candidate_id",
        "context_packet_hash",
        "research_trace_event_id",
        "method_family",
        "failure_mode",
        "falsifier_or_attempt",
        "observed_result",
        "artifact_hash",
    ):
        if not getattr(experience, field_name):
            reasons.append(f"failure:{field_name}_missing")
    if _parse_time(experience.timestamp) is None:
        reasons.append("failure:timestamp_missing_or_invalid")
    if not experience.residual_signature:
        reasons.append("failure:residual_signature_missing")
    if not experience.scope_conditions:
        reasons.append("failure:scope_conditions_missing")
    if not experience.competing_diagnoses:
        reasons.append("failure:competing_diagnoses_missing")
    if not experience.evidence_pointers:
        reasons.append("failure:evidence_pointers_missing")
    if experience.diagnosis_status is not FailureDiagnosisStatus.OBSERVED_ONLY:
        if not experience.selected_diagnosis:
            reasons.append("failure:selected_diagnosis_missing")
    if experience.diagnosis_status is FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY:
        if not experience.broken_assumptions:
            reasons.append("failure:verified_impossibility_scope_not_explicit")
    return tuple(reasons)


def add_failure_experience(
    lattice: FailureExperienceLattice,
    experience: FailureExperience,
) -> FailureExperienceLattice:
    reasons = validate_failure_experience(experience)
    if reasons:
        raise ValueError("invalid failure experience: " + ", ".join(reasons))
    if any(item.failure_id == experience.failure_id for item in lattice.experiences):
        raise ValueError(f"duplicate failure id: {experience.failure_id}")
    return FailureExperienceLattice(
        experiences=lattice.experiences + (experience,),
        links=lattice.links,
    )


def add_failure_link(
    lattice: FailureExperienceLattice,
    link: FailureLink,
) -> FailureExperienceLattice:
    ids = {item.failure_id for item in lattice.experiences}
    if link.source_id not in ids or link.target_id not in ids:
        raise ValueError("failure links require existing source and target experiences")
    if not link.rationale:
        raise ValueError("failure links require a bounded rationale")
    if link in lattice.links:
        return lattice
    return FailureExperienceLattice(
        experiences=lattice.experiences,
        links=lattice.links + (link,),
    )


def query_related_failures(
    lattice: FailureExperienceLattice,
    *,
    method_family: str,
    residual_signature: Tuple[str, ...] = (),
    broken_assumptions: Tuple[str, ...] = (),
) -> Tuple[FailureExperience, ...]:
    """Return structural warnings without asserting causal equivalence."""

    residuals = set(residual_signature)
    assumptions = set(broken_assumptions)
    scored: list[tuple[int, str, FailureExperience]] = []
    for item in lattice.experiences:
        score = 0
        if method_family and item.method_family == method_family:
            score += 4
        score += 2 * len(residuals & set(item.residual_signature))
        score += 2 * len(assumptions & set(item.broken_assumptions))
        if score > 0:
            scored.append((-score, item.failure_id, item))
    scored.sort(key=lambda row: (row[0], row[1]))
    return tuple(item for _, _, item in scored)


def assess_method_reuse(
    lattice: FailureExperienceLattice,
    *,
    target_atom_id: str,
    target_context_hash: str,
    method_family: str,
    relevant_failure_ids: Tuple[str, ...],
    difference_witness: DifferenceWitness | None,
) -> FailureReuseAssessment:
    """Use experience as a warning prior, not a global blacklist.

    Only a VERIFIED_IMPOSSIBILITY whose registered scope is explicitly being
    reused may produce the global-block verdict. Ordinary failures require a
    difference witness for a deliberate retry but never prove that the method is
    universally invalid.
    """

    by_id = {item.failure_id: item for item in lattice.experiences}
    relevant = tuple(by_id[item_id] for item_id in relevant_failure_ids if item_id in by_id)
    if not relevant:
        return FailureReuseAssessment(
            ReuseVerdict.NO_RELEVANT_FAILURE_FOUND,
            (),
            ("no_registered_failure_selected_as_structurally_relevant",),
        )

    impossible = tuple(
        item.failure_id
        for item in relevant
        if item.diagnosis_status is FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY
        and item.method_family == method_family
        and item.context_packet_hash == target_context_hash
    )
    if impossible:
        return FailureReuseAssessment(
            ReuseVerdict.GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY,
            impossible,
            ("verified_impossibility_applies_to_same_registered_context",),
        )

    if difference_witness is None:
        return FailureReuseAssessment(
            ReuseVerdict.SAME_CONTEXT_RETRY,
            tuple(item.failure_id for item in relevant),
            ("prior_structural_failure_exists_but_no_difference_witness_was_supplied",),
        )

    reasons: list[str] = []
    if difference_witness.target_atom_id != target_atom_id:
        reasons.append("difference_witness_atom_mismatch")
    if difference_witness.target_context_hash != target_context_hash:
        reasons.append("difference_witness_context_mismatch")
    if difference_witness.method_family != method_family:
        reasons.append("difference_witness_method_family_mismatch")
    if not difference_witness.changed_structural_coordinates:
        reasons.append("difference_witness_changed_coordinates_missing")
    if not difference_witness.restored_or_replaced_assumptions:
        reasons.append("difference_witness_assumption_change_missing")
    if not difference_witness.prior_falsifier_escape_reason:
        reasons.append("difference_witness_prior_falsifier_escape_missing")
    if not difference_witness.cheapest_repeat_failure_test:
        reasons.append("difference_witness_repeat_failure_test_missing")
    if not difference_witness.evidence_pointers:
        reasons.append("difference_witness_evidence_missing")
    missing_ids = set(relevant_failure_ids) - set(difference_witness.prior_failure_ids)
    if missing_ids:
        reasons.append("difference_witness_does_not_cover_all_selected_prior_failures")

    if reasons:
        return FailureReuseAssessment(
            ReuseVerdict.SAME_CONTEXT_RETRY,
            tuple(item.failure_id for item in relevant),
            tuple(reasons),
        )
    return FailureReuseAssessment(
        ReuseVerdict.DIFFERENCE_WITNESSED,
        tuple(item.failure_id for item in relevant),
        ("reuse_allowed_with_targeted_repeat_failure_test",),
    )


def global_failure_portrait(lattice: FailureExperienceLattice) -> dict[str, object]:
    """Build a compact, non-causal global summary of accumulated experience."""

    by_method: dict[str, int] = {}
    by_mode: dict[str, int] = {}
    by_assumption: dict[str, int] = {}
    unresolved: list[str] = []
    verified_impossibilities: list[str] = []

    for item in lattice.experiences:
        by_method[item.method_family] = by_method.get(item.method_family, 0) + 1
        by_mode[item.failure_mode] = by_mode.get(item.failure_mode, 0) + 1
        for assumption in item.broken_assumptions:
            by_assumption[assumption] = by_assumption.get(assumption, 0) + 1
        if item.diagnosis_status in {
            FailureDiagnosisStatus.OBSERVED_ONLY,
            FailureDiagnosisStatus.HYPOTHESIS,
        }:
            unresolved.append(item.failure_id)
        if item.diagnosis_status is FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY:
            verified_impossibilities.append(item.failure_id)

    return {
        "experience_count": len(lattice.experiences),
        "link_count": len(lattice.links),
        "method_family_counts": dict(sorted(by_method.items())),
        "failure_mode_counts": dict(sorted(by_mode.items())),
        "broken_assumption_counts": dict(sorted(by_assumption.items())),
        "unresolved_diagnoses": tuple(sorted(unresolved)),
        "verified_impossibilities": tuple(sorted(verified_impossibilities)),
    }
