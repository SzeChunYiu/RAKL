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
from rakl.semantic_shortcut_router_v2 import (
    resolve_obstruction_transformation_route_with_rejections,
    validate_candidate_rejection_certificate,
    validate_candidate_rejection_chain,
)


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


def _episode(
    eid,
    domain,
    *,
    effects=("global_object_exposed", "search_reduced"),
    artifact_hash=None,
):
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
        relaxed_or_broken_constraints=(),
        known_breakpoints=("infinite untyped state",),
        evidence_pointers=(f"source:{eid}",),
        authority=TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
        artifact_hash=artifact_hash or f"sha256:{eid}",
    )


def _memory(*episodes):
    return build_transformation_memory(
        memory_id="OTM-typed-rejection",
        source_universe=("mathematics", "biology", "engineering"),
        episodes=tuple(episodes),
        evidence_pointers=("memory:typed-rejection",),
    )


def _mapping(eid, *, unmatched=(), disanalogies=("domain vocabulary differs",)):
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
        disanalogies=tuple(disanalogies),
        target_validation_obligations=("verify target invariant preservation",),
        evidence_pointers=(f"mapping:{eid}",),
        artifact_hash=f"sha256:map-{eid}",
    )


def _resolve_v2(memory, **kwargs):
    return resolve_obstruction_transformation_route_with_rejections(
        review_id="R-typed",
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("resolver:typed-rejection",),
        **kwargs,
    )


def _resolve_v1(memory, **kwargs):
    return resolve_obstruction_transformation_route(
        review_id="R-typed",
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("resolver:typed-rejection",),
        **kwargs,
    )


def _lift_pair(*, rejected_direct=("D",), rejected_jump=("J",)):
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="registered memory plus cross-domain coverage",
        searched_domains=("mathematics", "biology"),
        searched_method_families=("representation", "invariant"),
        rejected_direct_episode_ids=tuple(rejected_direct),
        rejected_jump_episode_ids=tuple(rejected_jump),
        rejected_glue_composition_ids=(),
        rejection_reasons=("typed candidate rejection certificates retained",),
        residual_failure_ids=("F1", "F2"),
        repeated_residual_features=("local_expansion",),
        evidence_pointers=("coverage:receipt",),
        artifact_hash="sha256:exhaustion",
        coverage_receipt_hash="sha256:coverage",
    )
    spec = MissingTransformationSpecification(
        spec_id="SPEC-typed",
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


def _glue_witness():
    return TransformationCompositionWitness(
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


def test_conclusive_direct_rejection_permits_jump_and_retains_negative_trace():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    assert result.selected_mode is ShortcutMode.JUMP
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert len(result.rejection_certificates) == 1
    cert = result.rejection_certificates[0]
    assert cert.mode is ShortcutMode.SEARCH
    assert cert.candidate_episode_id == "D"
    assert cert.audit_reasons == ("mapping_has_unrepaired_source_preconditions",)
    assert result.considered_modes == (ShortcutMode.SEARCH, ShortcutMode.JUMP)


def test_missing_direct_witness_remains_cannot_check_and_does_not_fall_through():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(memory, jump_mapping_witnesses=(_mapping("J"),))
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK
    assert result.rejection_certificates == ()


def test_nonconclusive_mapping_failure_remains_cannot_check():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", disanalogies=()),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.rejection_certificates == ()


def test_cannot_check_state_never_mints_rejection_certificate():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(memory, direct_mapping_witnesses=(), jump_mapping_witnesses=())
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert not result.rejection_certificates


def test_certificate_validation_fails_after_candidate_revision_changes():
    direct = _episode("D", "mathematics")
    memory = _memory(direct, _episode("J", "biology"))
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    cert = result.rejection_certificates[0]
    assert validate_candidate_rejection_certificate(
        cert,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
    ) == ()
    revised = _memory(
        replace(direct, artifact_hash="sha256:D-revision-2"),
        _episode("J", "biology"),
    )
    reasons = validate_candidate_rejection_certificate(
        cert,
        memory=revised,
        obstruction=_target(),
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
    )
    assert "rejection_input_memory_snapshot_mismatch" in reasons
    assert "rejection_candidate_revision_mismatch" in reasons


def test_certificate_validation_binds_target_and_context():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    cert = result.rejection_certificates[0]
    wrong_target = replace(_target(), obstruction_id="O-other")
    reasons = validate_candidate_rejection_certificate(
        cert,
        memory=memory,
        obstruction=wrong_target,
        atom_id="atom-typed",
        context_hash="sha256:other-context",
        research_memory_review_hash="sha256:research-memory",
    )
    assert "rejection_target_obstruction_mismatch" in reasons
    assert "rejection_target_context_mismatch" in reasons


def test_certificate_artifact_hash_tampering_is_detected():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    tampered = replace(result.rejection_certificates[0], artifact_hash="sha256:tampered")
    reasons = validate_candidate_rejection_certificate(
        tampered,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
    )
    assert "rejection_artifact_hash_mismatch" in reasons


def test_rejected_jump_exposes_valid_glue_on_residual_view():
    memory = _memory(
        _episode("J", "biology"),
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    result = _resolve_v2(
        memory,
        jump_mapping_witnesses=(
            _mapping("J", unmatched=("typed",)),
            _mapping("A"),
            _mapping("B"),
        ),
        glue_witness=_glue_witness(),
    )
    assert result.selected_mode is ShortcutMode.GLUE
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert [c.candidate_episode_id for c in result.rejection_certificates] == ["J"]


def test_typed_search_and_jump_rejections_can_precede_lift_with_existing_audit():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    exhaustion, spec = _lift_pair()
    result = _resolve_v2(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J", unmatched=("typed",)),),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.LIFT
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert [c.candidate_episode_id for c in result.rejection_certificates] == ["D", "J"]
    assert result.considered_modes == (ShortcutMode.SEARCH, ShortcutMode.JUMP, ShortcutMode.LIFT)
    assert validate_candidate_rejection_chain(
        result.rejection_certificates,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-typed",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
    ) == ()


def test_existing_v1_fail_closed_behavior_is_unchanged_while_v2_unlocks_certified_fallthrough():
    memory = _memory(_episode("D", "mathematics"), _episode("J", "biology"))
    kwargs = dict(
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(_mapping("J"),),
    )
    v1 = _resolve_v1(memory, **kwargs)
    v2 = _resolve_v2(memory, **kwargs)
    assert v1.selected_mode is ShortcutMode.CANNOT_CHECK
    assert v1.report.verdict is ShortcutReviewVerdict.CANNOT_CHECK
    assert v2.selected_mode is ShortcutMode.JUMP
    assert v2.report.verdict is ShortcutReviewVerdict.PASS
