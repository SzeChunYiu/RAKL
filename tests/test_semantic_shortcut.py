from dataclasses import replace

import pytest

from rakl.semantic_shortcut import (
    ExhaustionWitness,
    MissingTransformationSpecification,
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationReview,
    RouteSearchStatus,
    ShortcutMode,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationCompositionWitness,
    TransformationEpisodeAuthority,
    add_transformation_episode,
    audit_obstruction_transformation_review,
    build_transformation_memory,
    discover_shortcut_candidates,
    repeated_residual_features,
    synthesize_missing_transformation_specification,
    validate_transformation_memory,
)


def _target() -> ObstructionFingerprint:
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


def _source(domain: str, *, oid: str) -> ObstructionFingerprint:
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


def _episode(
    episode_id: str,
    domain: str,
    *,
    effects=("global_object_exposed", "search_reduced"),
    authority=TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
    breaks=(),
) -> ObstructionTransformationEpisode:
    return ObstructionTransformationEpisode(
        episode_id=episode_id,
        source_domain=domain,
        source_context=f"{domain} source case",
        source_obstruction=_source(domain, oid=f"O-{episode_id}"),
        transformation_name=f"transform-{episode_id}",
        operation="replace local expansion with an aggregate representation",
        preconditions=("finite", "typed"),
        resulting_relations=tuple(effects),
        preserved_invariants=("conservation",),
        relaxed_or_broken_constraints=tuple(breaks),
        known_breakpoints=("infinite untyped state",),
        evidence_pointers=(f"source:{episode_id}",),
        authority=authority,
        artifact_hash=f"sha256:{episode_id}",
    )


def _memory(*episodes: ObstructionTransformationEpisode):
    return build_transformation_memory(
        memory_id="OTM-1",
        source_universe=("mathematics", "logistics", "biology", "engineering"),
        episodes=tuple(episodes),
        evidence_pointers=("index:OTM-1",),
    )


def _mapping(episode_id: str) -> StructuralMappingWitness:
    return StructuralMappingWitness(
        witness_id=f"W-{episode_id}",
        episode_id=episode_id,
        target_obstruction_id="O-target",
        role_mapping=(("state", "state"), ("resource", "resource")),
        shared_relations=("depends_on", "aggregates"),
        shared_constraints=("finite", "typed"),
        precondition_mapping=(("finite", "finite"), ("typed", "typed")),
        unmatched_source_preconditions=(),
        disanalogies=("domain vocabulary and ontology differ",),
        target_validation_obligations=("prove transported operation preserves target invariants",),
        evidence_pointers=(f"mapping:{episode_id}",),
        artifact_hash=f"sha256:map-{episode_id}",
    )


def _base_review(memory, mode: ShortcutMode, **changes) -> ObstructionTransformationReview:
    values = dict(
        review_id="R-1",
        target_atom_id="atom-C",
        target_context_hash="sha256:context",
        research_memory_review_hash="sha256:memory-review",
        episode_memory_snapshot_hash=memory.snapshot_hash,
        obstruction=_target(),
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        selected_mode=mode,
        evidence_pointers=("review:evidence",),
        artifact_hash="sha256:review",
    )
    values.update(changes)
    return ObstructionTransformationReview(**values)


def _audit(review, memory):
    return audit_obstruction_transformation_review(
        review,
        atom_id="atom-C",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:memory-review",
        transformation_memory=memory,
    )


def test_memory_is_content_bound_and_append_rehashes() -> None:
    memory = _memory(_episode("E1", "mathematics"))
    assert validate_transformation_memory(memory) == ()
    tampered = replace(memory, episodes=memory.episodes + (_episode("E2", "biology"),))
    assert "transformation_memory_snapshot_hash_mismatch" in validate_transformation_memory(
        tampered
    )

    expanded = add_transformation_episode(memory, _episode("E2", "biology"))
    assert expanded.snapshot_hash != memory.snapshot_hash
    assert validate_transformation_memory(expanded) == ()


def test_query_separates_direct_jump_and_rejects_forbidden_loss() -> None:
    memory = _memory(
        _episode("D", "mathematics"),
        _episode("J", "biology"),
        _episode("BAD", "engineering", breaks=("conservation",)),
    )
    candidates = discover_shortcut_candidates(_target(), memory)
    assert [item.episode_id for item in candidates.direct_matches] == ["D"]
    assert [item.episode_id for item in candidates.jump_matches] == ["J"]


def test_proposal_only_episode_is_not_a_viable_shortcut() -> None:
    memory = _memory(
        _episode(
            "P",
            "biology",
            authority=TransformationEpisodeAuthority.PROPOSAL_ONLY,
        )
    )
    candidates = discover_shortcut_candidates(_target(), memory)
    assert candidates.direct_matches == ()
    assert candidates.jump_matches == ()


def test_proposal_only_episode_cannot_crow_verified_top_k_slot() -> None:
    memory = _memory(
        _episode(
            "A-proposal",
            "biology",
            authority=TransformationEpisodeAuthority.PROPOSAL_ONLY,
        ),
        _episode("Z-verified", "biology"),
    )
    candidates = discover_shortcut_candidates(_target(), memory, top_k=1)
    assert [item.episode_id for item in candidates.jump_matches] == ["Z-verified"]


def test_partial_effect_episode_is_glue_fragment_not_search_or_jump_route() -> None:
    memory = _memory(
        _episode("A-partial", "mathematics", effects=("global_object_exposed",)),
        _episode("B-partial", "engineering", effects=("search_reduced",)),
    )
    candidates = discover_shortcut_candidates(_target(), memory)
    assert candidates.direct_matches == ()
    assert candidates.jump_matches == ()
    assert candidates.glue_episode_sets == (("A-partial", "B-partial"),)


def test_search_requires_bound_episode_and_applicability_mapping() -> None:
    memory = _memory(_episode("D", "mathematics"))
    review = _base_review(
        memory,
        ShortcutMode.SEARCH,
        direct_search_status=RouteSearchStatus.MATCHES_FOUND,
        direct_candidate_episode_ids=("D",),
        direct_mapping_witnesses=(_mapping("D"),),
        selected_episode_ids=("D",),
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.PASS
    assert report.selected_mode is ShortcutMode.SEARCH


def test_search_rejects_unaccounted_source_precondition() -> None:
    memory = _memory(_episode("D", "mathematics"))
    broken_mapping = replace(
        _mapping("D"),
        precondition_mapping=(("finite", "finite"),),
        unmatched_source_preconditions=("typed",),
    )
    review = _base_review(
        memory,
        ShortcutMode.SEARCH,
        direct_search_status=RouteSearchStatus.MATCHES_FOUND,
        direct_candidate_episode_ids=("D",),
        direct_mapping_witnesses=(broken_mapping,),
        selected_episode_ids=("D",),
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "mapping_has_unrepaired_source_preconditions" in report.reasons


def test_jump_passes_only_after_direct_route_is_absent() -> None:
    memory = _memory(_episode("J", "biology"))
    review = _base_review(
        memory,
        ShortcutMode.JUMP,
        jump_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_mapping_witnesses=(_mapping("J"),),
        selected_episode_ids=("J",),
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.PASS
    assert report.selected_mode is ShortcutMode.JUMP


def test_jump_cannot_bypass_existing_direct_route() -> None:
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    review = _base_review(
        memory,
        ShortcutMode.JUMP,
        jump_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_mapping_witnesses=(_mapping("J"),),
        selected_episode_ids=("J",),
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "direct_search_status_disagrees_with_bound_memory_query" in report.reasons


def test_glue_requires_effect_coverage_mapping_and_interface_witness() -> None:
    left = _episode("A", "biology", effects=("global_object_exposed",))
    right = _episode("B", "engineering", effects=("search_reduced",))
    memory = _memory(left, right)
    candidates = discover_shortcut_candidates(_target(), memory)
    assert ("A", "B") in candidates.glue_episode_sets

    glue = TransformationCompositionWitness(
        composition_id="G-A-B",
        target_obstruction_id="O-target",
        episode_ids=("A", "B"),
        operation_order=("A", "B"),
        interface_obligations=("prove output of A is admissible input to B",),
        incompatibilities_checked=("no invariant conflict across interface",),
        target_validation_obligations=("verify composed target effect",),
        evidence_pointers=("glue:evidence",),
        artifact_hash="sha256:glue",
    )
    review = _base_review(
        memory,
        ShortcutMode.GLUE,
        glue_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witness=glue,
        selected_episode_ids=("A", "B"),
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.PASS


def test_repeated_residuals_drive_inverse_lift_specification() -> None:
    residuals = {
        "F1": ("local_expansion", "hidden_global_state"),
        "F2": ("local_expansion", "wrong_coordinate"),
        "F3": ("local_expansion",),
    }
    assert repeated_residual_features(residuals) == ("local_expansion",)
    spec = synthesize_missing_transformation_specification(
        _target(),
        spec_id="SPEC-1",
        residual_signatures=residuals,
        must_reduce=("proof search branching",),
        allowed_representation_changes=("auxiliary object", "coordinate change"),
        validation_obligations=("show target equivalence",),
        falsifiers=("candidate loses conservation",),
        evidence_pointers=("failures:F1-F3",),
        artifact_hash="sha256:spec",
    )
    assert spec.must_break == ("local_expansion",)
    assert spec.must_preserve == ("conservation",)


def test_lift_requires_cross_problem_coverage_and_multiple_failures() -> None:
    memory = _memory()
    spec = MissingTransformationSpecification(
        spec_id="SPEC",
        target_obstruction_id="O-target",
        residual_failure_ids=("F1", "F2"),
        must_preserve=("conservation",),
        must_break=("local_expansion",),
        must_expose=("global_object_exposed",),
        must_reduce=("search_reduced",),
        allowed_representation_changes=("auxiliary object",),
        forbidden_shortcuts=("conservation",),
        validation_obligations=("prove equivalence",),
        falsifiers=("conservation lost",),
        evidence_pointers=("failures:F1-F2",),
        artifact_hash="sha256:spec",
    )
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="registered transformation memory plus cross-domain coverage receipt",
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
    review = _base_review(
        memory,
        ShortcutMode.LIFT,
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert _audit(review, memory).verdict is ShortcutReviewVerdict.PASS

    no_coverage = replace(exhaustion, coverage_receipt_hash="")
    failed = _audit(replace(review, exhaustion_witness=no_coverage), memory)
    assert failed.verdict is ShortcutReviewVerdict.FAIL
    assert "exhaustion_cross_problem_coverage_receipt_hash_missing" in failed.reasons


def test_lift_must_account_for_every_memory_candidate_it_rejects() -> None:
    memory = _memory(_episode("J", "biology"))
    spec = MissingTransformationSpecification(
        spec_id="SPEC",
        target_obstruction_id="O-target",
        residual_failure_ids=("F1", "F2"),
        must_preserve=("conservation",),
        must_break=("local_expansion",),
        must_expose=("global_object_exposed",),
        must_reduce=("search_reduced",),
        allowed_representation_changes=("auxiliary object",),
        forbidden_shortcuts=("conservation",),
        validation_obligations=("prove equivalence",),
        falsifiers=("conservation lost",),
        evidence_pointers=("failures:F1-F2",),
        artifact_hash="sha256:spec",
    )
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="bounded",
        searched_domains=("mathematics", "biology"),
        searched_method_families=("representation", "invariant"),
        rejected_direct_episode_ids=(),
        rejected_jump_episode_ids=(),
        rejected_glue_composition_ids=(),
        rejection_reasons=("candidate J had an unresolved target disanalogy",),
        residual_failure_ids=("F1", "F2"),
        repeated_residual_features=("local_expansion",),
        evidence_pointers=("coverage:receipt",),
        artifact_hash="sha256:exhaustion",
        coverage_receipt_hash="sha256:coverage",
    )
    review = _base_review(
        memory,
        ShortcutMode.LIFT,
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    report = _audit(review, memory)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "exhaustion_did_not_account_for_all_jump_candidates" in report.reasons

    accounted = replace(exhaustion, rejected_jump_episode_ids=("J",))
    assert (
        _audit(replace(review, exhaustion_witness=accounted), memory).verdict
        is ShortcutReviewVerdict.PASS
    )


def test_memory_snapshot_mismatch_blocks_review() -> None:
    memory = _memory(_episode("J", "biology"))
    review = _base_review(
        memory,
        ShortcutMode.JUMP,
        jump_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_mapping_witnesses=(_mapping("J"),),
        selected_episode_ids=("J",),
    )
    report = _audit(replace(review, episode_memory_snapshot_hash="stale"), memory)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "shortcut_episode_memory_snapshot_hash_mismatch" in report.reasons


def test_lift_spec_requires_repeated_residual_structure() -> None:
    with pytest.raises(ValueError):
        synthesize_missing_transformation_specification(
            _target(),
            spec_id="SPEC",
            residual_signatures={"F1": ("a",), "F2": ("b",)},
            must_reduce=("search",),
            allowed_representation_changes=("auxiliary object",),
            validation_obligations=("prove equivalence",),
            falsifiers=("fails target",),
            evidence_pointers=("evidence",),
            artifact_hash="sha256:spec",
        )
