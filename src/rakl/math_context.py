from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class ContextGateVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class AnalogyScanStatus(str, Enum):
    BRIDGES_RETAINED = "BRIDGES_RETAINED"
    NO_SAFE_BRIDGE_FOUND = "NO_SAFE_BRIDGE_FOUND"


@dataclass(frozen=True)
class MethodTransfer:
    """A witnessed attempt to transfer a method from an analogous solved context.

    The point is not merely to list similar papers. A transfer must state why the
    method works there, what structure is shared with the target atom, what breaks,
    and the smallest repair question exposed by that mismatch.
    """

    source_context: str
    method: str
    shared_structure: Tuple[str, ...]
    required_assumptions: Tuple[str, ...]
    disanalogies: Tuple[str, ...]
    repair_question: str
    source_anchors: Tuple[str, ...]


@dataclass(frozen=True)
class CrossDomainAnalogy:
    """A witnessed analogy used for proposal generation, never truth authority.

    The source may be another mathematical field, engineering, biology, a game,
    or an everyday human situation. The analogy is admissible only after the
    common abstract structure, source-to-target mapping, disanalogies and a
    falsifiable transfer obligation are explicit.
    """

    source_kind: str
    source_situation: str
    common_abstraction: Tuple[str, ...]
    source_to_target_mapping: Tuple[str, ...]
    shared_constraints: Tuple[str, ...]
    disanalogies: Tuple[str, ...]
    proposed_principle: str
    validation_obligation: str
    provenance_note: str


@dataclass(frozen=True)
class MathContextFiber:
    """Frozen pre-candidate context for one atomic mathematical obstruction."""

    atom_id: str
    object_context: str
    structural_coordinates: Tuple[str, ...]
    equivalent_formulations: Tuple[str, ...]
    solved_analogues: Tuple[str, ...] = ()
    near_solved_analogues: Tuple[str, ...] = ()
    method_transfers: Tuple[MethodTransfer, ...] = ()
    explicit_disanalogies: Tuple[str, ...] = ()
    source_anchors: Tuple[str, ...] = ()
    analogy_scan_status: str = ""
    cross_domain_analogies: Tuple[CrossDomainAnalogy, ...] = ()
    analogy_scan_notes: str = ""
    frozen_at: str = ""
    first_candidate_at: str | None = None
    packet_hash: str = ""


@dataclass(frozen=True)
class ContextGateReport:
    verdict: ContextGateVerdict
    reasons: Tuple[str, ...]


REQUIRED_PRE_CANDIDATE_ACTIONS: Tuple[str, ...] = (
    "freeze_exact_atomic_obstruction",
    "map_structural_coordinates_and_equivalent_formulations",
    "search_solved_and_near_solved_analogous_contexts",
    "extract_methods_and_required_assumptions",
    "record_shared_structure_and_disanalogies",
    "run_cross_domain_and_everyday_analogy_scan",
    "witness_any_retained_analogy_by_abstract_mapping_and_disanalogy",
    "formulate_minimal_repair_questions",
    "bind_primary_or_authoritative_source_anchors",
    "freeze_and_hash_context_packet_before_candidate_generation",
)


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


def audit_math_context_fiber(fiber: MathContextFiber | None) -> ContextGateReport:
    """Fail closed unless context/analogue transfer is frozen before invention.

    This gate governs the research process, not theorem truth. A mathematically
    valid proof discovered elsewhere may still be checked by the assurance layer,
    but it cannot be represented as a strict RAKL context-first discovery path
    unless this gate passed before candidate generation.
    """

    if fiber is None:
        return ContextGateReport(
            ContextGateVerdict.CANNOT_CHECK,
            ("math_context_fiber_missing",),
        )

    reasons: list[str] = []
    if not fiber.atom_id:
        reasons.append("context_atom_id_missing")
    if not fiber.object_context:
        reasons.append("context_object_description_missing")
    if not fiber.structural_coordinates:
        reasons.append("context_structural_coordinates_missing")
    if not fiber.equivalent_formulations:
        reasons.append("context_equivalent_formulations_missing")
    if not (fiber.solved_analogues or fiber.near_solved_analogues):
        reasons.append("context_analogues_missing")
    if not fiber.method_transfers:
        reasons.append("context_method_transfer_matrix_missing")
    if not fiber.explicit_disanalogies:
        reasons.append("context_global_disanalogies_missing")
    if not fiber.source_anchors:
        reasons.append("context_source_anchors_missing")
    if not fiber.packet_hash:
        reasons.append("context_packet_hash_missing")

    if fiber.analogy_scan_status not in {item.value for item in AnalogyScanStatus}:
        reasons.append("cross_domain_analogy_scan_missing_or_invalid")
    elif fiber.analogy_scan_status == AnalogyScanStatus.BRIDGES_RETAINED.value:
        if not fiber.cross_domain_analogies:
            reasons.append("analogy_scan_claims_bridges_without_bridge_records")
    elif fiber.analogy_scan_status == AnalogyScanStatus.NO_SAFE_BRIDGE_FOUND.value:
        if not fiber.analogy_scan_notes:
            reasons.append("no_safe_analogy_bridge_requires_notes")

    frozen_at = _parse_time(fiber.frozen_at)
    if frozen_at is None:
        reasons.append("context_freeze_time_missing_or_invalid")
    if fiber.first_candidate_at is not None:
        first_candidate_at = _parse_time(fiber.first_candidate_at)
        if first_candidate_at is None:
            reasons.append("first_candidate_time_invalid")
        elif frozen_at is not None and frozen_at >= first_candidate_at:
            reasons.append("context_not_frozen_before_candidate_generation")

    for index, transfer in enumerate(fiber.method_transfers):
        prefix = f"method_transfer_{index}"
        if not transfer.source_context:
            reasons.append(f"{prefix}:source_context_missing")
        if not transfer.method:
            reasons.append(f"{prefix}:method_missing")
        if not transfer.shared_structure:
            reasons.append(f"{prefix}:shared_structure_missing")
        if not transfer.required_assumptions:
            reasons.append(f"{prefix}:required_assumptions_missing")
        if not transfer.disanalogies:
            reasons.append(f"{prefix}:disanalogies_missing")
        if not transfer.repair_question:
            reasons.append(f"{prefix}:repair_question_missing")
        if not transfer.source_anchors:
            reasons.append(f"{prefix}:source_anchors_missing")

    for index, analogy in enumerate(fiber.cross_domain_analogies):
        prefix = f"cross_domain_analogy_{index}"
        if not analogy.source_kind:
            reasons.append(f"{prefix}:source_kind_missing")
        if not analogy.source_situation:
            reasons.append(f"{prefix}:source_situation_missing")
        if not analogy.common_abstraction:
            reasons.append(f"{prefix}:common_abstraction_missing")
        if not analogy.source_to_target_mapping:
            reasons.append(f"{prefix}:source_to_target_mapping_missing")
        if not analogy.shared_constraints:
            reasons.append(f"{prefix}:shared_constraints_missing")
        if not analogy.disanalogies:
            reasons.append(f"{prefix}:disanalogies_missing")
        if not analogy.proposed_principle:
            reasons.append(f"{prefix}:proposed_principle_missing")
        if not analogy.validation_obligation:
            reasons.append(f"{prefix}:validation_obligation_missing")
        if not analogy.provenance_note:
            reasons.append(f"{prefix}:provenance_note_missing")

    if reasons:
        return ContextGateReport(ContextGateVerdict.FAIL, tuple(reasons))
    return ContextGateReport(
        ContextGateVerdict.PASS,
        (
            "context_method_transfer_and_cross_domain_analogy_scan_frozen_before_candidate_generation",
        ),
    )
