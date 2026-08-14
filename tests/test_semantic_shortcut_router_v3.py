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
from rakl.semantic_shortcut_router_v2 import (
    resolve_obstruction_transformation_route_with_rejections,
)
from rakl.semantic_shortcut_router_v3 import (
    resolve_obstruction_transformation_route_with_composition_rejections,
    validate_composition_rejection_certificate,
    validate_composition_rejection_chain,
)


def _target(obstruction_id="O-target"):
    return ObstructionFingerprint(
        obstruction_id=obstruction_id,
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
        memory_id="OTM-glue-rejection",
        source_universe=("mathematics", "biology", "engineering"),
        episodes=tuple(episodes),
        evidence_pointers=("memory:glue-rejection",),
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


def _glue_witness(
    episode_ids=("A", "B"),
    *,
    composition_id=None,
    interface_obligations=("A output is admissible input to B",),
    incompatibilities_checked=("no invariant conflict",),
    artifact_hash=None,
):
    ids = tuple(episode_ids)
    return TransformationCompositionWitness(
        composition_id=composition_id or "G-" + "-".join(ids),
        target_obstruction_id="O-target",
        episode_ids=ids,
        operation_order=ids,
        interface_obligations=tuple(interface_obligations),
        incompatibilities_checked=tuple(incompatibilities_checked),
        target_validation_obligations=("verify composed target effect",),
        evidence_pointers=("glue:receipt:" + "+".join(ids),),
        artifact_hash=artifact_hash or "sha256:glue-" + "-".join(ids),
    )


def _lift_pair(*, direct=(), jump=(), glue=()):
    exhaustion = ExhaustionWitness(
        target_obstruction_id="O-target",
        search_boundary="registered memory plus cross-domain coverage",
        searched_domains=("mathematics", "biology", "engineering"),
        searched_method_families=("representation", "invariant"),
        rejected_direct_episode_ids=tuple(direct),
        rejected_jump_episode_ids=tuple(jump),
        rejected_glue_composition_ids=tuple(glue),
        rejection_reasons=("typed rejection certificates retained",),
        residual_failure_ids=("F1", "F2"),
        repeated_residual_features=("local_expansion",),
        evidence_pointers=("coverage:receipt",),
        artifact_hash="sha256:exhaustion",
        coverage_receipt_hash="sha256:coverage",
    )
    spec = MissingTransformationSpecification(
        spec_id="SPEC-glue",
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


def _resolve_v3(memory, **kwargs):
    return resolve_obstruction_transformation_route_with_composition_rejections(
        review_id="R-glue",
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("resolver:glue-rejection",),
        **kwargs,
    )


def _resolve_v2(memory, **kwargs):
    return resolve_obstruction_transformation_route_with_rejections(
        review_id="R-glue",
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        obstruction=_target(),
        transformation_memory=memory,
        evidence_pointers=("resolver:glue-rejection",),
        **kwargs,
    )


def _partial_memory_two():
    return _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )


def _rejected_glue_result():
    memory = _partial_memory_two()
    exhaustion, spec = _lift_pair(glue=("A+B",))
    witness = _glue_witness()
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
        ),
        glue_witnesses=(witness,),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    return memory, witness, result


def test_valid_glue_still_wins_without_rejection_certificate():
    memory = _partial_memory_two()
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witnesses=(_glue_witness(),),
    )
    assert result.selected_mode is ShortcutMode.GLUE
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert result.composition_rejection_certificates == ()


def test_conclusive_glue_rejection_can_reach_lift_with_complete_exhaustion():
    memory, witness, result = _rejected_glue_result()
    assert result.selected_mode is ShortcutMode.LIFT
    assert result.report.verdict is ShortcutReviewVerdict.PASS
    assert len(result.composition_rejection_certificates) == 1
    cert = result.composition_rejection_certificates[0]
    assert cert.candidate_key == "A+B"
    assert cert.audit_reasons == ("mapping_has_unrepaired_source_preconditions",)
    assert validate_composition_rejection_certificate(
        cert,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witness=witness,
    ) == ()


def test_same_conclusive_glue_failure_remains_cannot_check_under_v2():
    memory = _partial_memory_two()
    exhaustion, spec = _lift_pair(glue=("A+B",))
    v2 = _resolve_v2(
        memory,
        jump_mapping_witnesses=(
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
        ),
        glue_witness=_glue_witness(),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert v2.selected_mode is ShortcutMode.CANNOT_CHECK
    assert not v2.rejection_certificates


def test_missing_glue_witness_remains_cannot_check_and_mints_no_certificate():
    memory = _partial_memory_two()
    exhaustion, spec = _lift_pair(glue=("A+B",))
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witnesses=(),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.composition_rejection_certificates == ()


def test_nonconclusive_glue_audit_failure_remains_cannot_check():
    memory = _partial_memory_two()
    exhaustion, spec = _lift_pair(glue=("A+B",))
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(_mapping("A"), _mapping("B")),
        glue_witnesses=(
            _glue_witness(interface_obligations=()),
        ),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.composition_rejection_certificates == ()


def test_composition_certificate_binds_operation_order():
    memory, witness, result = _rejected_glue_result()
    cert = result.composition_rejection_certificates[0]
    tampered = replace(cert, operation_order=("B", "A"))
    reasons = validate_composition_rejection_certificate(
        tampered,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witness=witness,
    )
    assert "composition_rejection_operation_order_mismatch" in reasons
    assert "composition_rejection_witness_operation_order_mismatch" in reasons
    assert "composition_rejection_artifact_hash_mismatch" in reasons


def test_composition_certificate_binds_component_revisions():
    memory, witness, result = _rejected_glue_result()
    cert = result.composition_rejection_certificates[0]
    revised = _memory(
        _episode(
            "A",
            "biology",
            effects=("global_object_exposed",),
            artifact_hash="sha256:A-revision-2",
        ),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    reasons = validate_composition_rejection_certificate(
        cert,
        memory=revised,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witness=witness,
    )
    assert "composition_rejection_input_memory_snapshot_mismatch" in reasons
    assert "composition_rejection_component_revision_mismatch" in reasons


def test_composition_certificate_binds_target_and_context():
    memory, witness, result = _rejected_glue_result()
    cert = result.composition_rejection_certificates[0]
    reasons = validate_composition_rejection_certificate(
        cert,
        memory=memory,
        obstruction=_target("O-other"),
        atom_id="atom-glue",
        context_hash="sha256:other-context",
        research_memory_review_hash="sha256:research-memory",
        witness=witness,
    )
    assert "composition_rejection_target_obstruction_mismatch" in reasons
    assert "composition_rejection_target_context_mismatch" in reasons


def test_composition_witness_semantic_content_and_certificate_tampering_are_detected():
    memory, witness, result = _rejected_glue_result()
    cert = result.composition_rejection_certificates[0]
    altered_witness = replace(
        witness,
        interface_obligations=("different claimed interface",),
    )
    reasons = validate_composition_rejection_certificate(
        cert,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witness=altered_witness,
    )
    assert "composition_rejection_witness_content_hash_mismatch" in reasons
    tampered_cert = replace(cert, artifact_hash="sha256:tampered")
    reasons = validate_composition_rejection_certificate(
        tampered_cert,
        memory=memory,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witness=witness,
    )
    assert "composition_rejection_artifact_hash_mismatch" in reasons


def test_one_rejected_and_one_unresolved_glue_composition_still_blocks_lift():
    memory = _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
        _episode("C", "biology", effects=("search_reduced",)),
    )
    exhaustion, spec = _lift_pair(glue=("A+B", "A+C"))
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
            _mapping("C"),
        ),
        glue_witnesses=(_glue_witness(("A", "B")),),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert [c.candidate_key for c in result.composition_rejection_certificates] == [
        "A+B"
    ]


def test_lift_requires_exhaustion_to_account_for_every_glue_candidate_key():
    memory = _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
        _episode("C", "biology", effects=("search_reduced",)),
    )
    incomplete_exhaustion, spec = _lift_pair(glue=("A+B",))
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
            _mapping("C"),
        ),
        glue_witnesses=(
            _glue_witness(("A", "B")),
            _glue_witness(("A", "C")),
        ),
        exhaustion_witness=incomplete_exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert {c.candidate_key for c in result.composition_rejection_certificates} == {
        "A+B",
        "A+C",
    }


def test_negative_history_retains_search_jump_and_glue_rejections_before_lift():
    memory = _memory(
        _episode("D", "mathematics"),
        _episode("J", "biology"),
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    exhaustion, spec = _lift_pair(
        direct=("D",),
        jump=("J",),
        glue=("A+B",),
    )
    glue = _glue_witness()
    result = _resolve_v3(
        memory,
        direct_mapping_witnesses=(_mapping("D", unmatched=("typed",)),),
        jump_mapping_witnesses=(
            _mapping("J", unmatched=("typed",)),
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
        ),
        glue_witnesses=(glue,),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.LIFT
    assert [c.candidate_episode_id for c in result.candidate_rejection_certificates] == [
        "D",
        "J",
    ]
    assert [c.candidate_key for c in result.composition_rejection_certificates] == [
        "A+B"
    ]
    residual_memory = _memory(
        _episode("A", "biology", effects=("global_object_exposed",)),
        _episode("B", "engineering", effects=("search_reduced",)),
    )
    assert validate_composition_rejection_chain(
        result.composition_rejection_certificates,
        memory=residual_memory,
        obstruction=_target(),
        atom_id="atom-glue",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:research-memory",
        witnesses=(glue,),
    ) == ()


def test_duplicate_witnesses_for_one_composition_fail_closed():
    memory = _partial_memory_two()
    exhaustion, spec = _lift_pair(glue=("A+B",))
    result = _resolve_v3(
        memory,
        jump_mapping_witnesses=(
            _mapping("A", unmatched=("typed",)),
            _mapping("B"),
        ),
        glue_witnesses=(
            _glue_witness(("A", "B"), composition_id="G-1"),
            _glue_witness(("B", "A"), composition_id="G-2"),
        ),
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
    )
    assert result.selected_mode is ShortcutMode.CANNOT_CHECK
    assert result.composition_rejection_certificates == ()
