from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class ContextGateVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


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
    "formulate_minimal_repair_questions",
    "bind_primary_or_authoritative_source_anchors",
    "freeze_and_hash_context_packet_before_candidate_generation",
)


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def audit_math_context_fiber(fiber: MathContextFiber | None) -> ContextGateReport:
    """Fail closed unless context/analogue transfer is frozen before invention.

    This gate governs the *research process*, not theorem truth. A mathematically
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

    frozen_at = _parse_time(fiber.frozen_at)
    if frozen_at is None:
        reasons.append("context_freeze_time_missing_or_invalid")
    first_candidate_at = None
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

    if reasons:
        return ContextGateReport(ContextGateVerdict.FAIL, tuple(reasons))
    return ContextGateReport(
        ContextGateVerdict.PASS,
        ("context_and_analogue_method_transfer_frozen_before_candidate_generation",),
    )
