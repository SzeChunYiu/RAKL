from dataclasses import replace

from rakl.semantic_shortcut import (
    ExhaustionWitness,
    MissingTransformationSpecification,
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ShortcutMode,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationCompositionWitness,
    TransformationEpisodeAuthority,
    build_transformation_memory,
)
from rakl.semantic_shortcut_router import resolve_obstruction_transformation_route


def _target():
    return ObstructionFingerprint(
        obstruction_id="O-target",
        domain="mathematics",
        roles=("state", "resource"),
        relations=("depends_on", "aggregates"),
        constraints=("finite", "typed"),
        failure_mechanisms=("local_reasoning_expands",),
        invariants_to_preserve=("conservation",),
        desired_transition=("global_object_exposed", "search_reduced"),
        forbidden_losses=("conservation",),
    )


def _source(domain, oid):
    return ObstructionFingerprint(
        obstruction_id=oid,
        domain=domain,
        roles=("state", "resource"),
        relations=("depends_on", "aggregates"),
        constraints=("finite", "typed"),
        failure_mechanisms=("local_reasoning_expands",),
        invariants_to_preserve=("conservation",),
        desired_transition=("global_object_exposed", "search_reduced"),
    )


def _episode(eid, domain, *, effects=("global_object_exposed", "search_reduced"), authority=TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED, breaks=()):
    return ObstructionTransformationEpisode(
        episode_id=eid,
        source_domain=domain,
        source_context=f"{domain} case",
        source_obstruction=_source(domain, f"O-{eid}"),
        transformation_name=f"T-{eid}",
        operation="replace local expansion with aggregate representation",
        preconditions=("finite", "typed"),
        resulting_relations=tuple(effects),
        preserved_invariants=("conservation",),
        relaxed_or_broken_constraints=tuple(breaks),
        known_breakpoints=("infinite untyped state",),
        evidence_pointers=(f"source:{eid}",),
        authority=authority,
        artifact_hash=f"sha256:{eid}",
    )


def _memory(*episodes):
    return build_transformation_memory(
        memory_id="OTM-live-binding",
        source_universe=("mathematics", "biology", "engineering"),
        episodes=tuple(episodes),
        evidence_pointers=("memory:live-binding",),
    )


def _mapping(eid, *, unmatched=()):
    mapped = (("finite", "finite"), ("typed", "typed"))
    if unmatched:
        mapped = (("finite", "finite"),)
    return StructuralMappingWitness(
        witness_id=f"W-{eid}",
        episode_id=eid,
        target_obstruction_id="O-target",
        role_mapping=(("state", "state"), ("resource", "resource")),
        shared_relations=("depends_on", "aggregates"),
        shared_constraints=("finite", "typed"),
        precondition_mapping=mapped,
        unmatched_source_preconditions=tuple(unmatched),
        disanalogies=("domain vocabulary differs",),
        target_validation_obligations=("verify target invariant preservation",),
        evidence_pointers=(f"mapping:{eid}",),
        artifact_hash=f"sha256:map-{eid}",
    )


def _resolve(memory, **kwargs):
    return resolve_obstruction_transformation_route(
        review_id="R-live",
        atom_id="atom-live",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("resolver:live-binding",),
        **kwargs,
    )


def _lift_pair():
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="registered memory plus cross-domain coverage",
        searched_domains=("mathematics", "biology"),
        searched_method_families=("representation", "invariant"),
        rejected_direct_episode_ids=(),
        rejected_jump_episode_ids=(),
        rejected_glue_composition_ids=(),
        rejection_reasons=("no viable transformation survived",),
        residual_failure_ids=("F1", "F2"),
        repeated_residual_features=("local_expansion",),
        evidence_pointers=("coverage:receipt",),
        artifact_hash="sha256:exhaustion",
        coverage_receipt_hash="sha256:coverage",
    )
    spec = MissingTransformationSpecification(
        spec_id="SPEC-live",
        target_obstruction_id="O-target",
        residual_failure_ids=("F1", "F2"),
        must_preserve=("conservation",),
        must_break=("local_expansion",),
        must_expose=("global_object_exposed",),
        must_reduce=("search_reduced",),
        allowed_representation_changes=("auxiliary object",),
        forbidden_shortcuts=("conservation",),
        validation_obligations=("prove target equivalence",),
        falsifiers=("conservation lost",),
        evidence_pointers=("failures:F1-F2",),
        artifact_hash="sha256:spec",
    )
    return exhaustion, spec


def test_resolver_selects_search_before_jump_when_direct_is_witnessed():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve(
        memory,
        direct_mapping_witnesses=(_mapping("D"),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    assert result.selected_mode is ShortcutMode.SEARCH
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert result.considered_modes == (ShortcutMode.SEARCH,)


def test_unresolved_direct_candidate_fails_closed_instead_of_bypassing_to_jump():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK
    assert ShortcutMode.JUMP not in result.considered_modes


def test_resolver_selects_jump_when_no_direct_candidate_exists():
    memory = _memory(_episode("J", "biology"))
    result = _resolve(memory, jump_mapping_witnesses=(_mapping("J"),))
    assert result.selected_mode is ShortcutMode.JUMP
    assert result.report.verdict is ShortcutReviewVerdict.PASS


def test_unwitnessed_jump_fails_closed():
    memory = _memory(_episode("J", "biology"))
    result = _resolve(memory)
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK


def test_resolver_selects_glue_for_complementary_partial_effects():
    memory = _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    glue = TransformationCompositionWitness(
        composition_id="G-A-B",
        target_obstruction_id="O-target",
        episode_ids=("A", "B"),
        operation_order=("A", "B"),
        interface_obligations=("A output is admissible input to B",),
        incompatibilities_checked=("no invariant conflict",),
        target_validation_obligations=("verify composed target effect",),
        evidence_pointers=("glue:receipt",),
        artifact_hash="sha256:glue",
    )
    result = _resolve(
        memory,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witness=glue,
    )
    assert result.selected_mode is ShortcutMode.GLUE
    assert result.report.verdict is ShortcutReviewVerdict.PASS


def test_unsafe_glue_fails_closed():
    memory = _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    glue = TransformationCompositionWitness(
        composition_id="G-A-B",
        target_obstruction_id="O-target",
        episode_ids=("A", "B"),
        operation_order=("A", "B"),
        interface_obligations=("A output is admissible input to B",),
        incompatibilities_checked=(),
        target_validation_obligations=("verify composed target effect",),
        evidence_pointers=("glue:receipt",),
        artifact_hash="sha256:glue",
    )
    result = _resolve(
        memory,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witness=glue,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK


def test_resolver_selects_lift_only_with_empty_route_set_and_valid_exhaustion():
    exhaustion, spec = _lift_pair()
    result = _resolve(
        _memory(),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.LIFT
    assert result.report.verdict is ShortcutReviewVerdict.PASS


def test_lift_missing_cross_problem_coverage_fails_closed():
    exhaustion, spec = _lift_pair()
    result = _resolve(
        _memory(),
        exhaustion_witness=replace(exhaustion, coverage_receipt_hash=""),
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK


def test_proposal_only_episode_does_not_create_a_route():
    memory = _memory(
        _episode(
            "P",
            "biology",
            authority=TransformationEpisodeAuthority.PROPOSAL_ONLY,
        )
    )
    result = _resolve(memory)
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK


def test_forbidden_loss_episode_does_not_create_a_route():
    memory = _memory(_episode("BAD", "biology", breaks=("conservation",)))
    result = _resolve(memory)
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK
