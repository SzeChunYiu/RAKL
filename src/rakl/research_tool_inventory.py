from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class ResearchToolAuthority(str, Enum):
    HEURISTIC = "HEURISTIC"
    VERIFIED_LOCAL = "VERIFIED_LOCAL"
    CONDITIONALLY_REUSABLE = "CONDITIONALLY_REUSABLE"
    PROOF_BACKED = "PROOF_BACKED"
    SUPERSEDED = "SUPERSEDED"


class ToolApplicabilityVerdict(str, Enum):
    APPLICABLE = "APPLICABLE"
    APPLICABLE_WITH_VALIDATION = "APPLICABLE_WITH_VALIDATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    BLOCKED_BY_KNOWN_FAILURE = "BLOCKED_BY_KNOWN_FAILURE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ResearchTool:
    """A reusable method distilled from a successful research step.

    Success does not make a method universal.  Every tool carries its source,
    preconditions, scope, guarantees, validation obligations, and known failure
    warnings so future reuse can be checked rather than assumed.
    """

    tool_id: str
    name: str
    kind: str
    abstraction: str
    source_atom_id: str
    source_candidate_id: str
    source_result_ids: Tuple[str, ...]
    source_context_hash: str
    authority: ResearchToolAuthority
    preconditions: Tuple[str, ...]
    structural_signature: Tuple[str, ...]
    operation: str
    guaranteed_effects: Tuple[str, ...]
    non_guarantees: Tuple[str, ...]
    validation_obligations: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    known_failure_ids: Tuple[str, ...] = ()
    successful_reuse_ids: Tuple[str, ...] = ()
    proof_backing: Tuple[str, ...] = ()
    artifact_hash: str = ""


@dataclass(frozen=True)
class ToolApplicabilityWitness:
    target_atom_id: str
    target_context_hash: str
    tool_id: str
    matched_preconditions: Tuple[str, ...]
    unmatched_preconditions: Tuple[str, ...]
    shared_structural_coordinates: Tuple[str, ...]
    changed_structural_coordinates: Tuple[str, ...]
    known_failure_ids_reviewed: Tuple[str, ...]
    target_validation_plan: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]


@dataclass(frozen=True)
class ResearchToolInventory:
    tools: Tuple[ResearchTool, ...] = ()


@dataclass(frozen=True)
class ToolApplicabilityAssessment:
    verdict: ToolApplicabilityVerdict
    reasons: Tuple[str, ...]


def validate_research_tool(tool: ResearchTool) -> Tuple[str, ...]:
    reasons: list[str] = []
    for field_name in (
        "tool_id",
        "name",
        "kind",
        "abstraction",
        "source_atom_id",
        "source_candidate_id",
        "source_context_hash",
        "operation",
        "artifact_hash",
    ):
        if not getattr(tool, field_name):
            reasons.append(f"tool:{field_name}_missing")
    if not tool.source_result_ids:
        reasons.append("tool:source_result_ids_missing")
    if not tool.preconditions:
        reasons.append("tool:preconditions_missing")
    if not tool.structural_signature:
        reasons.append("tool:structural_signature_missing")
    if not tool.guaranteed_effects:
        reasons.append("tool:guaranteed_effects_missing")
    if not tool.non_guarantees:
        reasons.append("tool:non_guarantees_missing")
    if not tool.validation_obligations:
        reasons.append("tool:validation_obligations_missing")
    if not tool.evidence_pointers:
        reasons.append("tool:evidence_pointers_missing")
    if tool.authority is ResearchToolAuthority.PROOF_BACKED and not tool.proof_backing:
        reasons.append("tool:proof_backed_authority_missing_proof")
    return tuple(reasons)


def add_research_tool(
    inventory: ResearchToolInventory,
    tool: ResearchTool,
) -> ResearchToolInventory:
    reasons = validate_research_tool(tool)
    if reasons:
        raise ValueError("invalid research tool: " + ", ".join(reasons))
    if any(item.tool_id == tool.tool_id for item in inventory.tools):
        raise ValueError(f"duplicate research tool id: {tool.tool_id}")
    return ResearchToolInventory(tools=inventory.tools + (tool,))


def query_research_tools(
    inventory: ResearchToolInventory,
    *,
    structural_coordinates: Tuple[str, ...] = (),
    desired_effects: Tuple[str, ...] = (),
    kind: str = "",
) -> Tuple[ResearchTool, ...]:
    structures = set(structural_coordinates)
    effects = set(desired_effects)
    scored: list[tuple[int, str, ResearchTool]] = []
    for tool in inventory.tools:
        if tool.authority is ResearchToolAuthority.SUPERSEDED:
            continue
        score = 0
        if kind and tool.kind == kind:
            score += 4
        score += 2 * len(structures & set(tool.structural_signature))
        score += 2 * len(effects & set(tool.guaranteed_effects))
        if score > 0:
            scored.append((-score, tool.tool_id, tool))
    scored.sort(key=lambda row: (row[0], row[1]))
    return tuple(tool for _, _, tool in scored)


def assess_tool_applicability(
    tool: ResearchTool,
    witness: ToolApplicabilityWitness | None,
) -> ToolApplicabilityAssessment:
    """Check scoped reuse of a success-derived tool.

    A local success is never silently generalized.  Higher-authority tools can
    still require target-specific validation when structural coordinates change.
    """

    reasons = validate_research_tool(tool)
    if reasons:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            reasons,
        )
    if witness is None:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("tool_applicability_witness_missing",),
        )
    if witness.tool_id != tool.tool_id:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("tool_applicability_witness_tool_mismatch",),
        )
    if not witness.target_atom_id or not witness.target_context_hash:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("tool_target_identity_missing",),
        )
    if witness.unmatched_preconditions:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.OUT_OF_SCOPE,
            tuple(f"unmatched_precondition:{item}" for item in witness.unmatched_preconditions),
        )
    if set(tool.preconditions) - set(witness.matched_preconditions):
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("not_all_tool_preconditions_were_assessed",),
        )
    if tool.known_failure_ids and not set(tool.known_failure_ids).issubset(
        set(witness.known_failure_ids_reviewed)
    ):
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.BLOCKED_BY_KNOWN_FAILURE,
            ("known_tool_failure_history_not_reviewed",),
        )
    if not witness.shared_structural_coordinates:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("tool_structural_match_missing",),
        )
    if not witness.evidence_pointers:
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.CANNOT_CHECK,
            ("tool_applicability_evidence_missing",),
        )

    needs_validation = (
        tool.authority in {ResearchToolAuthority.HEURISTIC, ResearchToolAuthority.VERIFIED_LOCAL}
        or bool(witness.changed_structural_coordinates)
        or bool(tool.validation_obligations)
    )
    if needs_validation:
        if not witness.target_validation_plan:
            return ToolApplicabilityAssessment(
                ToolApplicabilityVerdict.CANNOT_CHECK,
                ("target_validation_plan_missing",),
            )
        return ToolApplicabilityAssessment(
            ToolApplicabilityVerdict.APPLICABLE_WITH_VALIDATION,
            ("tool_scope_matches_but_target_specific_validation_is_required",),
        )
    return ToolApplicabilityAssessment(
        ToolApplicabilityVerdict.APPLICABLE,
        ("tool_preconditions_and_structural_scope_match",),
    )


def tool_inventory_portrait(inventory: ResearchToolInventory) -> dict[str, object]:
    by_kind: dict[str, int] = {}
    by_authority: dict[str, int] = {}
    with_failures: list[str] = []
    for tool in inventory.tools:
        by_kind[tool.kind] = by_kind.get(tool.kind, 0) + 1
        key = tool.authority.value
        by_authority[key] = by_authority.get(key, 0) + 1
        if tool.known_failure_ids:
            with_failures.append(tool.tool_id)
    return {
        "tool_count": len(inventory.tools),
        "kind_counts": dict(sorted(by_kind.items())),
        "authority_counts": dict(sorted(by_authority.items())),
        "tools_with_failure_warnings": tuple(sorted(with_failures)),
    }
