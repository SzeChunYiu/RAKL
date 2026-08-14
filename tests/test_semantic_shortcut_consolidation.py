from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.experience_substrate import (
    EpisodeAdmissionReceipt,
    EpisodeOutcome,
    EpisodeStorageAdmission,
    TaskEpisode,
    admission_receipt_content_bytes,
    episode_content_bytes,
)
from rakl.semantic_shortcut import (
    ExhaustionWitness,
    MissingTransformationSpecification,
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ShortcutMode,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationEpisodeAuthority,
    add_transformation_episode,
    build_transformation_memory,
)
from rakl.semantic_shortcut_consolidation import (
    StructuralConsolidationVerdict,
    consolidate_validated_target_transformation,
    transformation_episode_content_hash,
)
from rakl.semantic_shortcut_router import resolve_obstruction_transformation_route


def _target(*, obstruction_id: str = "O-target", domain: str = "mathematics") -> ObstructionFingerprint:
    return ObstructionFingerprint(
        obstruction_id=obstruction_id,
        domain=domain,
        roles=("state", "resource"),
        relations=("depends_on", "aggregates"),
        constraints=("finite", "typed"),
        failure_mechanisms=("local_reasoning_expands",),
        invariants_to_preserve=("conservation",),
        desired_transition=("global_object_exposed", "search_reduced"),
        forbidden_losses=("conservation",),
    )


def _source(domain: str, obstruction_id: str) -> ObstructionFingerprint:
    return replace(_target(obstruction_id=obstruction_id), domain=domain)


def _source_episode(
    episode_id: str = "D",
    *,
    domain: str = "mathematics",
) -> ObstructionTransformationEpisode:
    return ObstructionTransformationEpisode(
        episode_id=episode_id,
        source_domain=domain,
        source_context=f"{domain} verified source event",
        source_obstruction=_source(domain, f"O-{episode_id}"),
        transformation_name=f"T-{episode_id}",
        operation="replace local expansion with aggregate representation",
        preconditions=("finite", "typed"),
        resulting_relations=("global_object_exposed", "search_reduced"),
        preserved_invariants=("conservation",),
        relaxed_or_broken_constraints=(),
        known_breakpoints=("infinite untyped state",),
        evidence_pointers=(f"source:{episode_id}",),
        authority=TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
        artifact_hash=f"sha256:{episode_id}",
    )


def _memory(*episodes: ObstructionTransformationEpisode):
    return build_transformation_memory(
        memory_id="OTM-target-consolidation",
        source_universe=("mathematics", "biology", "engineering"),
        episodes=tuple(episodes),
        evidence_pointers=("memory:target-consolidation",),
    )


def _mapping(episode_id: str = "D") -> StructuralMappingWitness:
    return StructuralMappingWitness(
        witness_id=f"W-{episode_id}",
        episode_id=episode_id,
        target_obstruction_id="O-target",
        role_mapping=(("state", "state"), ("resource", "resource")),
        shared_relations=("depends_on", "aggregates"),
        shared_constraints=("finite", "typed"),
        precondition_mapping=(("finite", "finite"), ("typed", "typed")),
        unmatched_source_preconditions=(),
        disanalogies=("surface vocabulary differs",),
        target_validation_obligations=("execute target verifier",),
        evidence_pointers=(f"mapping:{episode_id}",),
        artifact_hash=f"sha256:map-{episode_id}",
    )


def _search_resolution(memory):
    resolution = resolve_obstruction_transformation_route(
        review_id="R-target",
        atom_id="atom-target",
        context_hash="sha256:target-context",
        research_memory_review_hash="sha256:research-memory-review",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("route:target-validation",),
        direct_mapping_witnesses=(_mapping(),),
    )
    assert resolution.selected_mode is ShortcutMode.SEARCH
    assert resolution.report.verdict is ShortcutReviewVerdict.PASS
    return resolution


def _lift_resolution(memory):
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="bound memory plus registered cross-domain universe",
        searched_domains=("mathematics", "biology"),
        searched_method_families=("representation", "invariant"),
        rejected_direct_episode_ids=(),
        rejected_jump_episode_ids=(),
        rejected_glue_composition_ids=(),
        rejection_reasons=("no structural candidates in bound memory",),
        residual_failure_ids=("F1", "F2"),
        repeated_residual_features=("local_expansion",),
        evidence_pointers=("coverage:receipt",),
        artifact_hash="sha256:exhaustion",
        coverage_receipt_hash="sha256:coverage",
    )
    spec = MissingTransformationSpecification(
        spec_id="SPEC-target",
        target_obstruction_id="O-target",
        residual_failure_ids=("F1", "F2"),
        must_preserve=("conservation",),
        must_break=("local_expansion",),
        must_expose=("global_object_exposed", "search_reduced"),
        must_reduce=("branching",),
        allowed_representation_changes=("auxiliary aggregate",),
        forbidden_shortcuts=("conservation",),
        validation_obligations=("execute target verifier",),
        falsifiers=("conservation lost",),
        evidence_pointers=("failures:F1-F2",),
        artifact_hash="sha256:spec",
    )
    resolution = resolve_obstruction_transformation_route(
        review_id="R-lift",
        atom_id="atom-target",
        context_hash="sha256:target-context",
        research_memory_review_hash="sha256:research-memory-review",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("route:lift-target-validation",),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert resolution.selected_mode is ShortcutMode.LIFT
    assert resolution.report.verdict is ShortcutReviewVerdict.PASS
    return resolution


def _target_episode(
    *,
    outcome: EpisodeOutcome = EpisodeOutcome.SUCCESS,
    admitted: bool = True,
    atom_id: str = "atom-target",
    context_hash: str = "sha256:target-context",
):
    storage = (
        EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED
        if admitted
        else EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED
    )
    draft = TaskEpisode(
        episode_id="TE-target",
        task_id="task-target-validation",
        atom_id=atom_id,
        context_hash=context_hash,
        problem_signature=("structural-target",),
        fibre_snapshot_hash="sha256:fibre",
        operator_ids=("operator:aggregate",),
        action_trace=("apply routed transformation", "run target verifier"),
        observation_ids=("obs:target",),
        verification_ids=("verify:target",),
        outcome=outcome,
        residual_signature=("residual",) if outcome is not EpisodeOutcome.SUCCESS else (),
        evidence_pointers=("target:evidence",),
        artifact_hash="",
        timestamp="2026-08-14T05:00:00+00:00",
        storage_admission=storage,
    )
    episode = replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())
    if not admitted:
        return episode, None
    receipt_draft = EpisodeAdmissionReceipt(
        receipt_id="AR-target",
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
        evidence_pointers=("admission:evidence",),
        artifact_hash="",
        timestamp="2026-08-14T05:01:00+00:00",
    )
    receipt = replace(
        receipt_draft,
        artifact_hash=sha256(admission_receipt_content_bytes(receipt_draft)).hexdigest(),
    )
    return episode, receipt


def _candidate(review, target_episode, *, authority=TransformationEpisodeAuthority.PROPOSAL_ONLY, include_lineage=True):
    lineage = [target_episode.episode_id, review.review_id]
    lineage.extend(review.selected_episode_ids)
    if review.selected_mode is ShortcutMode.LIFT and review.missing_transformation_specification:
        lineage.append(review.missing_transformation_specification.spec_id)
    if not include_lineage:
        lineage = [target_episode.episode_id]
    draft = ObstructionTransformationEpisode(
        episode_id="P-target",
        source_domain=review.obstruction.domain,
        source_context="validated target execution proposal",
        source_obstruction=review.obstruction,
        transformation_name="target aggregate representation",
        operation="replace local expansion with aggregate representation",
        preconditions=("finite", "typed"),
        resulting_relations=("global_object_exposed", "search_reduced"),
        preserved_invariants=("conservation",),
        relaxed_or_broken_constraints=(),
        known_breakpoints=("target outside registered boundary",),
        evidence_pointers=("candidate:proposal",),
        authority=authority,
        artifact_hash="",
        lineage_ids=tuple(lineage),
    )
    return replace(draft, artifact_hash=transformation_episode_content_hash(draft))


def _consolidate(memory, resolution, *, target_episode=None, receipt=None, candidate=None, promoted_episode_id="OT-target-v1"):
    if target_episode is None:
        target_episode, receipt = _target_episode()
    if candidate is None:
        candidate = _candidate(resolution.review, target_episode)
    return consolidate_validated_target_transformation(
        memory=memory,
        candidate=candidate,
        review=resolution.review,
        supplied_route_report=resolution.report,
        target_episode=target_episode,
        target_admission_receipt=receipt,
        promoted_episode_id=promoted_episode_id,
    )


def test_strongest_bare_parent_allows_caller_asserted_verified_local_without_target_validation():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, _ = _target_episode()
    caller_asserted = _candidate(
        resolution.review,
        target_episode,
        authority=TransformationEpisodeAuthority.VERIFIED_LOCAL,
    )
    # This is the exact atomic gap: the low-level compatibility API is syntactic.
    parent_memory = add_transformation_episode(memory, caller_asserted)
    assert parent_memory.episodes[-1].authority is TransformationEpisodeAuthority.VERIFIED_LOCAL

    successor = _consolidate(memory, resolution, target_episode=target_episode, receipt=None, candidate=caller_asserted)
    assert successor.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_authority_must_be_proposal_only" in successor.report.reasons
    assert successor.memory == memory


def test_exact_pass_plus_canonical_success_promotes_only_verified_local_structural_episode():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    before = memory
    result = _consolidate(
        memory,
        resolution,
        target_episode=target_episode,
        receipt=receipt,
        candidate=candidate,
    )
    assert result.report.verdict is StructuralConsolidationVerdict.VALIDATED_TARGET_CONSOLIDATED
    assert result.promoted_episode is not None
    assert result.promoted_episode.authority is TransformationEpisodeAuthority.VERIFIED_LOCAL
    assert result.promoted_episode.episode_id == "OT-target-v1"
    assert result.promoted_episode.artifact_hash == transformation_episode_content_hash(result.promoted_episode)
    assert result.promoted_episode.artifact_hash != candidate.artifact_hash
    assert result.report.grants_scientific_authority is False
    assert result.report.grants_research_tool_promotion is False
    assert len(result.memory.episodes) == len(before.episodes) + 1
    assert before == memory
    assert candidate.authority is TransformationEpisodeAuthority.PROPOSAL_ONLY


def test_shadow_only_target_episode_blocks_consolidation():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode(admitted=False)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "target_episode_not_canonically_admitted" in result.report.reasons
    assert result.memory == memory


def test_invalid_admission_receipt_blocks_consolidation():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    assert receipt is not None
    bad = replace(receipt, episode_artifact_hash="0" * 64)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=bad)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "target_episode_not_canonically_admitted" in result.report.reasons


@pytest.mark.parametrize(
    "outcome",
    [
        EpisodeOutcome.FAILURE,
        EpisodeOutcome.PARTIAL_SUCCESS,
        EpisodeOutcome.BLOCKED,
        EpisodeOutcome.UNKNOWN,
    ],
)
def test_non_success_target_outcomes_never_consolidate(outcome):
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode(outcome=outcome)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert f"target_episode_not_success:{outcome.value}" in result.report.reasons


def test_forged_supplied_pass_report_cannot_substitute_for_exact_reaudit():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    forged = replace(resolution.report, reasons=("caller says pass",))
    result = consolidate_validated_target_transformation(
        memory=memory,
        candidate=candidate,
        review=resolution.review,
        supplied_route_report=forged,
        target_episode=target_episode,
        target_admission_receipt=receipt,
        promoted_episode_id="OT-target-v1",
    )
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "supplied_route_report_does_not_match_exact_reaudit" in result.report.reasons


def test_stale_memory_snapshot_in_review_fails_exact_reaudit():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    stale_review = replace(resolution.review, episode_memory_snapshot_hash="stale-snapshot")
    candidate = _candidate(stale_review, target_episode)
    result = consolidate_validated_target_transformation(
        memory=memory,
        candidate=candidate,
        review=stale_review,
        supplied_route_report=resolution.report,
        target_episode=target_episode,
        target_admission_receipt=receipt,
        promoted_episode_id="OT-target-v1",
    )
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "route_review_not_pass_after_exact_reaudit" in result.report.reasons


def test_target_atom_and_context_are_bound_to_success_episode():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode(
        atom_id="atom-other",
        context_hash="sha256:other-context",
    )
    candidate = _candidate(resolution.review, target_episode)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt, candidate=candidate)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "target_episode_atom_mismatch" in result.report.reasons
    assert "target_episode_context_mismatch" in result.report.reasons


def test_candidate_obstruction_and_domain_must_equal_review_target():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    wrong_obstruction = replace(candidate, source_obstruction=_target(obstruction_id="O-other"))
    wrong_obstruction = replace(wrong_obstruction, artifact_hash=transformation_episode_content_hash(wrong_obstruction))
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt, candidate=wrong_obstruction)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_obstruction_does_not_equal_review_target" in result.report.reasons

    wrong_domain = replace(candidate, source_domain="biology")
    wrong_domain = replace(wrong_domain, artifact_hash=transformation_episode_content_hash(wrong_domain))
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt, candidate=wrong_domain)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_source_domain_does_not_equal_target_domain" in result.report.reasons


def test_missing_route_or_source_lineage_blocks_consolidation():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode, include_lineage=False)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt, candidate=candidate)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_lineage_missing_target_or_route_sources" in result.report.reasons


def test_lift_candidate_requires_missing_specification_lineage():
    memory = _memory()
    resolution = _lift_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    assert resolution.review.missing_transformation_specification is not None
    spec_id = resolution.review.missing_transformation_specification.spec_id
    without_spec = replace(
        candidate,
        lineage_ids=tuple(item for item in candidate.lineage_ids if item != spec_id),
    )
    without_spec = replace(without_spec, artifact_hash=transformation_episode_content_hash(without_spec))
    blocked = _consolidate(
        memory,
        resolution,
        target_episode=target_episode,
        receipt=receipt,
        candidate=without_spec,
    )
    assert blocked.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_lineage_missing_target_or_route_sources" in blocked.report.reasons
    assert "lift_candidate_missing_specification_lineage" in blocked.report.reasons

    accepted = _consolidate(
        memory,
        resolution,
        target_episode=target_episode,
        receipt=receipt,
        candidate=candidate,
        promoted_episode_id="OT-lift-target-v1",
    )
    assert accepted.report.verdict is StructuralConsolidationVerdict.VALIDATED_TARGET_CONSOLIDATED
    assert accepted.promoted_episode is not None
    assert spec_id in accepted.promoted_episode.lineage_ids


def test_forged_candidate_hash_is_rejected_even_when_semantic_fields_are_valid():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    forged = replace(candidate, artifact_hash="0" * 64)
    result = _consolidate(memory, resolution, target_episode=target_episode, receipt=receipt, candidate=forged)
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert "candidate_content_hash_mismatch" in result.report.reasons


def test_promotion_requires_new_episode_version_id():
    memory = _memory(_source_episode())
    resolution = _search_resolution(memory)
    target_episode, receipt = _target_episode()
    candidate = _candidate(resolution.review, target_episode)
    result = _consolidate(
        memory,
        resolution,
        target_episode=target_episode,
        receipt=receipt,
        candidate=candidate,
        promoted_episode_id=candidate.episode_id,
    )
    assert result.report.verdict is StructuralConsolidationVerdict.REJECT
    assert result.report.reasons == ("promotion_must_create_new_episode_version",)
    assert result.memory == memory
