from __future__ import annotations

from rakl.research_tool_inventory import (
    ResearchTool,
    ResearchToolAuthority,
    ResearchToolInventory,
    ToolApplicabilityVerdict,
    ToolApplicabilityWitness,
    add_research_tool,
    assess_tool_applicability,
    query_research_tools,
    tool_inventory_portrait,
)


def _tool(**overrides: object) -> ResearchTool:
    values: dict[str, object] = {
        "tool_id": "T1",
        "name": "dual-rail Boolean-to-intersection compiler",
        "kind": "representation compiler",
        "abstraction": "compile bounded-fanin Boolean computation into counted intersections",
        "source_atom_id": "A1",
        "source_candidate_id": "C020",
        "source_result_ids": ("C020-L4",),
        "source_context_hash": "ctx-source",
        "authority": ResearchToolAuthority.CONDITIONALLY_REUSABLE,
        "preconditions": ("free unions", "literal row/column generators", "bounded-fanin Boolean basis"),
        "structural_signature": ("Boolean circuit", "intersection complexity"),
        "operation": "maintain positive/negative rails and translate AND/OR/NOT",
        "guaranteed_effects": ("O(s) intersection construction from size-s De Morgan circuit",),
        "non_guarantees": ("does not prove lower bounds", "does not establish novelty"),
        "validation_obligations": ("bind target generator semantics", "check gate-basis translation"),
        "evidence_pointers": ("candidate:C020",),
        "known_failure_ids": ("F-model-mismatch",),
        "artifact_hash": "sha256:T1",
    }
    values.update(overrides)
    return ResearchTool(**values)  # type: ignore[arg-type]


def _witness(**overrides: object) -> ToolApplicabilityWitness:
    values: dict[str, object] = {
        "target_atom_id": "A2",
        "target_context_hash": "ctx-target",
        "tool_id": "T1",
        "matched_preconditions": ("free unions", "literal row/column generators", "bounded-fanin Boolean basis"),
        "unmatched_preconditions": (),
        "shared_structural_coordinates": ("Boolean circuit", "intersection complexity"),
        "changed_structural_coordinates": ("different target predicate",),
        "known_failure_ids_reviewed": ("F-model-mismatch",),
        "target_validation_plan": ("compile one target circuit and check exact semantics",),
        "evidence_pointers": ("context:ctx-target",),
    }
    values.update(overrides)
    return ToolApplicabilityWitness(**values)  # type: ignore[arg-type]


def test_success_can_be_distilled_into_scoped_tool() -> None:
    inventory = add_research_tool(ResearchToolInventory(), _tool())
    assert inventory.tools[0].tool_id == "T1"
    portrait = tool_inventory_portrait(inventory)
    assert portrait["tool_count"] == 1
    assert portrait["tools_with_failure_warnings"] == ("T1",)


def test_tool_query_matches_structure_and_effect() -> None:
    inventory = add_research_tool(ResearchToolInventory(), _tool())
    matches = query_research_tools(
        inventory,
        structural_coordinates=("intersection complexity",),
        desired_effects=("O(s) intersection construction from size-s De Morgan circuit",),
    )
    assert tuple(tool.tool_id for tool in matches) == ("T1",)


def test_tool_reuse_requires_known_failure_review_and_validation() -> None:
    assessment = assess_tool_applicability(_tool(), _witness(known_failure_ids_reviewed=()))
    assert assessment.verdict is ToolApplicabilityVerdict.BLOCKED_BY_KNOWN_FAILURE

    assessment = assess_tool_applicability(_tool(), _witness())
    assert assessment.verdict is ToolApplicabilityVerdict.APPLICABLE_WITH_VALIDATION


def test_missing_precondition_keeps_tool_out_of_scope() -> None:
    assessment = assess_tool_applicability(
        _tool(),
        _witness(
            matched_preconditions=("free unions", "literal row/column generators"),
            unmatched_preconditions=("bounded-fanin Boolean basis",),
        ),
    )
    assert assessment.verdict is ToolApplicabilityVerdict.OUT_OF_SCOPE


def test_proof_backed_authority_requires_proof_binding() -> None:
    tool = _tool(authority=ResearchToolAuthority.PROOF_BACKED, proof_backing=())
    try:
        add_research_tool(ResearchToolInventory(), tool)
    except ValueError as exc:
        assert "proof_backed_authority_missing_proof" in str(exc)
    else:
        raise AssertionError("invalid proof-backed tool should fail closed")
