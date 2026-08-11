from __future__ import annotations

from rakl.math_context import (
    AnalogyScanStatus,
    ContextGateVerdict,
    MathContextFiber,
    MethodTransfer,
)
from rakl.math_research_assurance import (
    FormalizationWitness,
    MathResearchRecord,
    NoveltyCertificate,
    ProofReceipt,
)
from rakl.math_research_runtime import plan_math_research, publication_ready
from rakl.problem_solving_algebra import ObstructionKind, ProblemSignature
from rakl.research_memory import (
    MemoryQueryStatus,
    ResearchMemoryReview,
    ResearchMemoryVerdict,
)
from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
)
from rakl.root_coordinate_preservation import (
    BridgeEdge,
    CoordinateAuthority,
    EdgeProofStatus,
    Obligation,
    PreservationGateVerdict,
    RegisteredStateObservation,
    RootCoordinatePreservationReceipt,
)
from rakl.semantic_shortcut import (
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationReview,
    RouteSearchStatus,
    ShortcutMode,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationEpisodeAuthority,
    build_transformation_memory,
)


def _signature() -> ProblemSignature:
    return ProblemSignature(
        objects=("claim",),
        domain="mathematics",
        goal_type="prove theorem",
    )


def _context() -> MathContextFiber:
    return MathContextFiber(
        atom_id="atom-C",
        object_context="one atomic mathematical obstruction",
        structural_coordinates=("symmetry", "composition law"),
        equivalent_formulations=("equivalent obstruction formulation",),
        solved_analogues=("solved sibling theorem",),
        method_transfers=(
            MethodTransfer(
                source_context="solved sibling theorem",
                method="transferable method",
                shared_structure=("shared invariant",),
                required_assumptions=("registered assumption",),
                disanalogies=("target lacks one source assumption",),
                repair_question="what weaker assumption makes the method survive?",
                source_anchors=("source:primary",),
            ),
        ),
        explicit_disanalogies=("source and target differ on the repair assumption",),
        source_anchors=("source:primary",),
        analogy_scan_status=AnalogyScanStatus.NO_SAFE_BRIDGE_FOUND.value,
        analogy_scan_notes="cross-domain scan completed; no bridge survived mapping/disanalogy checks",
        frozen_at="2026-08-11T04:00:00+00:00",
        first_candidate_at="2026-08-11T04:20:00+00:00",
        packet_hash="sha256:context",
    )


def _memory() -> ResearchMemoryReview:
    return ResearchMemoryReview(
        target_atom_id="atom-C",
        target_context_hash="sha256:context",
        tool_inventory_snapshot_hash="sha256:tools",
        failure_lattice_snapshot_hash="sha256:failures",
        tool_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH,
        failure_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH,
        candidate_method_families=("transferable method",),
        unresolved_warnings=("no prior experience match; proceed with ordinary falsifier",),
        evidence_pointers=("snapshot:tools", "snapshot:failures"),
        artifact_hash="sha256:memory",
    )


def _obstruction() -> ObstructionFingerprint:
    return ObstructionFingerprint(
        obstruction_id="obs-C",
        domain="mathematics",
        roles=("proof state", "proof obligation"),
        relations=("state blocks obligation",),
        constraints=("registered theorem statement",),
        failure_mechanisms=("search branching",),
        invariants_to_preserve=("formal statement meaning preserved",),
        desired_transition=("reduce search branching",),
        forbidden_losses=("do not alter theorem statement",),
    )


def _transformation_memory():
    episode = ObstructionTransformationEpisode(
        episode_id="episode-direct",
        source_domain="mathematics",
        source_context="a verified proof-search episode with the same obstruction morphology",
        source_obstruction=_obstruction(),
        transformation_name="compress equivalent proof states",
        operation="replace repeated local expansion with a reusable aggregate proof state",
        preconditions=("registered theorem statement",),
        resulting_relations=("reduce search branching",),
        preserved_invariants=("formal statement meaning preserved",),
        relaxed_or_broken_constraints=(),
        known_breakpoints=("formal statement changes under the representation",),
        evidence_pointers=("source:episode-direct",),
        authority=TransformationEpisodeAuthority.PROOF_BACKED,
        artifact_hash="sha256:episode-direct",
    )
    return build_transformation_memory(
        memory_id="OTM-C",
        source_universe=("mathematics", "science", "engineering", "ordinary situations"),
        episodes=(episode,),
        evidence_pointers=("snapshot:obstruction-transform-memory",),
    )


def _shortcut() -> ObstructionTransformationReview:
    transformation_memory = _transformation_memory()
    mapping = StructuralMappingWitness(
        witness_id="map-direct",
        episode_id="episode-direct",
        target_obstruction_id="obs-C",
        role_mapping=(("proof state", "proof state"), ("proof obligation", "proof obligation")),
        shared_relations=("state blocks obligation",),
        shared_constraints=("registered theorem statement",),
        precondition_mapping=(("registered theorem statement", "registered theorem statement"),),
        unmatched_source_preconditions=(),
        disanalogies=("source theorem identity differs from the target theorem",),
        target_validation_obligations=("prove the compressed proof state preserves the target theorem statement",),
        evidence_pointers=("mapping:episode-direct",),
        artifact_hash="sha256:map-direct",
    )
    return ObstructionTransformationReview(
        review_id="shortcut-C",
        target_atom_id="atom-C",
        target_context_hash="sha256:context",
        research_memory_review_hash="sha256:memory",
        episode_memory_snapshot_hash=transformation_memory.snapshot_hash,
        obstruction=_obstruction(),
        direct_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_search_status=RouteSearchStatus.NOT_RUN,
        glue_search_status=RouteSearchStatus.NOT_RUN,
        selected_mode=ShortcutMode.SEARCH,
        direct_candidate_episode_ids=("episode-direct",),
        direct_mapping_witnesses=(mapping,),
        selected_episode_ids=("episode-direct",),
        unresolved_warnings=("source success still requires target validation",),
        evidence_pointers=("snapshot:obstruction-transform-memory",),
        artifact_hash="sha256:shortcut",
    )


def _trace() -> MathResearchTrace:
    types = (
        ResearchTraceEventType.ATOMIZED,
        ResearchTraceEventType.CONTEXT_FROZEN,
        ResearchTraceEventType.ANALOGY_SCAN,
        ResearchTraceEventType.METHOD_TRANSFER_REVIEW,
        ResearchTraceEventType.EXPERT_CONTEXT_REVIEW,
        ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW,
        ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW,
        ResearchTraceEventType.NEXT_STEP_PROPOSED,
    )
    entries = []
    previous_hash = ""
    for i, event_type in enumerate(types, start=1):
        artifact_hash = f"sha256:event-{i}"
        outputs = (f"output:{i}",)
        if event_type is ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW:
            outputs = ("sha256:memory",)
        if event_type is ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW:
            outputs = ("sha256:shortcut",)
        entries.append(
            ResearchTraceEntry(
                event_id=f"e{i}",
                atom_id="atom-C",
                event_type=event_type,
                timestamp=f"2026-08-11T04:0{i}:00+00:00",
                state_summary=f"state {i}",
                action_summary=f"action {i}",
                evidence_pointers=("sha256:context",)
                if event_type is ResearchTraceEventType.CONTEXT_FROZEN
                else (f"artifact:{i}",),
                alternatives_considered=("A", "B"),
                decision_rationale="bounded public rationale",
                outputs=outputs,
                uncertainties=("one unresolved issue",),
                next_steps=("next atomic action",),
                artifact_hash=artifact_hash,
                previous_event_hash=previous_hash,
            )
        )
        previous_hash = artifact_hash
    return MathResearchTrace(trace_id="trace-C", entries=tuple(entries))


def _formalization() -> FormalizationWitness:
    return FormalizationWitness(
        informal_claim_hash="informal",
        formal_statement_hash="formal",
        accepted=True,
        roundtrip_checked=True,
        boundary_cases_checked=True,
        independent_reviewers=1,
    )


def _proof() -> ProofReceipt:
    return ProofReceipt(
        theorem_id="T",
        theorem_statement_hash="formal",
        checker="lean",
        checker_version="pinned",
        accepted=True,
        axioms=(),
        independent_checker="comparator",
        independent_checker_version="pinned",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash="proof-source",
    )


def _novelty() -> NoveltyCertificate:
    return NoveltyCertificate(
        corpus_cutoff="2026-08-10",
        corpora=("registered-corpus",),
        search_routes=("exact", "normalized", "structural"),
        canonical_fingerprint="fp",
        equivalent_found=False,
        independent_reviewers=1,
    )


def _strict_kwargs() -> dict[str, object]:
    return {
        "context_fiber": _context(),
        "memory_review": _memory(),
        "transformation_memory": _transformation_memory(),
        "shortcut_review": _shortcut(),
        "research_trace": _trace(),
    }


def test_missing_context_blocks_candidate_generation_fail_closed() -> None:
    plan = plan_math_research(signature=_signature(), record=MathResearchRecord(claim_id="C"))
    assert plan.context_gate.verdict is ContextGateVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert not plan.candidate_paths
    assert "search_solved_and_near_solved_analogous_contexts" in plan.pre_candidate_actions


def test_context_without_memory_review_blocks_candidate_generation() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        context_fiber=_context(),
    )
    assert plan.context_gate.verdict is ContextGateVerdict.PASS
    assert plan.memory_gate.verdict is ResearchMemoryVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert "query_global_failure_experience_lattice" in plan.pre_candidate_actions


def test_context_and_memory_without_shortcut_review_blocks_candidate_generation() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        context_fiber=_context(),
        memory_review=_memory(),
    )
    assert plan.memory_gate.verdict is ResearchMemoryVerdict.PASS
    assert plan.shortcut_gate.verdict is ShortcutReviewVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert "fingerprint_active_relational_obstruction" in plan.pre_candidate_actions


def test_shortcut_review_without_bound_transformation_memory_fails_closed() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        context_fiber=_context(),
        memory_review=_memory(),
        shortcut_review=_shortcut(),
    )
    assert plan.shortcut_gate.verdict is ShortcutReviewVerdict.FAIL
    assert "transformation_memory_missing" in plan.shortcut_gate.reasons
    assert not plan.candidate_generation_allowed
    assert "compile_or_load_content_bound_transformation_memory" in plan.pre_candidate_actions


def test_context_memory_and_shortcut_without_trace_still_block_candidate_generation() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        context_fiber=_context(),
        memory_review=_memory(),
        transformation_memory=_transformation_memory(),
        shortcut_review=_shortcut(),
    )
    assert plan.shortcut_gate.verdict is ShortcutReviewVerdict.PASS
    assert plan.trace_gate.verdict is TraceGateVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert "record_atomization_result" in plan.pre_candidate_actions


def test_all_process_gates_expose_normal_research_blockers_and_paths() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        **_strict_kwargs(),
    )
    blockers = set(plan.next_blockers)
    assert ObstructionKind.FORMALIZATION_GAP in blockers
    assert ObstructionKind.FORMALIZATION_ALIGNMENT_GAP in blockers
    assert ObstructionKind.PROOF_GAP in blockers
    assert ObstructionKind.NOVELTY_GAP in blockers
    assert ObstructionKind.RESEARCH_VALUE_GAP in blockers
    assert plan.context_gate.verdict is ContextGateVerdict.PASS
    assert plan.memory_gate.verdict is ResearchMemoryVerdict.PASS
    assert plan.shortcut_gate.verdict is ShortcutReviewVerdict.PASS
    assert plan.trace_gate.verdict is TraceGateVerdict.PASS
    assert plan.candidate_generation_allowed
    assert plan.candidate_paths
    assert plan.pre_candidate_actions == ()
    assert "obstruction_transformation_review_complete" in plan.planning_state.facts
    assert "semantic_shortcut_mode:SEARCH" in plan.planning_state.facts


def test_verified_proof_removes_proof_blocker_but_not_novelty_or_value() -> None:
    record = MathResearchRecord(claim_id="C", formalization=_formalization(), proof=_proof())
    plan = plan_math_research(signature=_signature(), record=record, **_strict_kwargs())
    blockers = set(plan.next_blockers)
    assert ObstructionKind.PROOF_GAP not in blockers
    assert ObstructionKind.NOVELTY_GAP in blockers
    assert ObstructionKind.RESEARCH_VALUE_GAP in blockers
    assert not publication_ready(record)


def test_only_all_noncompensatory_gates_make_record_publication_ready() -> None:
    record = MathResearchRecord(
        claim_id="C",
        formalization=_formalization(),
        proof=_proof(),
        novelty=_novelty(),
        interestingness_screened=True,
        external_mathematical_review=True,
    )
    plan = plan_math_research(signature=_signature(), record=record, **_strict_kwargs())
    assert plan.next_blockers == ()
    assert publication_ready(record)


def test_rediscovery_is_not_publication_ready_as_new_mathematics() -> None:
    novelty = NoveltyCertificate(
        corpus_cutoff="2026-08-10",
        corpora=("registered-corpus",),
        search_routes=("structural",),
        canonical_fingerprint="fp",
        equivalent_found=True,
        candidate_matches=("known theorem",),
        independent_reviewers=1,
    )
    record = MathResearchRecord(
        claim_id="C",
        formalization=_formalization(),
        proof=_proof(),
        novelty=novelty,
        interestingness_screened=True,
        external_mathematical_review=True,
    )
    assert not publication_ready(record)


def _preservation_receipt(*, root_claim_id: str = "C") -> RootCoordinatePreservationReceipt:
    return RootCoordinatePreservationReceipt(
        receipt_id="RCP-C",
        root_claim_id=root_claim_id,
        root_coordinate="root.registered_obligation",
        surrogate_coordinate="surrogate.projected_measure",
        bridge_edges=(
            BridgeEdge(
                edge_id="E-1",
                source_coordinate="surrogate.projected_measure",
                target_coordinate="root.registered_obligation",
                interface_map="pi: registered_state -> projected_state",
                proof_status=EdgeProofStatus.PROVED,
                enabling_assumptions=("projection defined on domain",),
            ),
        ),
        obligations=(
            Obligation(
                obligation_id="OB-1",
                description="root obligation",
                non_compensatory=True,
            ),
        ),
        known_disanalogies=("surrogate is coarser",),
        source_authority=CoordinateAuthority.ESTABLISHED,
        target_authority=CoordinateAuthority.PROPOSAL_ONLY,
        cheapest_hostile_world="equal projection, different root outcome",
        registered_observations=(
            RegisteredStateObservation("S-1", "P-a", "OUT-1"),
            RegisteredStateObservation("S-2", "P-b", "OUT-2"),
        ),
        reverification_triggers=("projection redefined",),
    )


def test_required_preservation_gate_missing_receipt_blocks_candidate_search() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        **_strict_kwargs(),
        require_preservation_gate=True,
    )
    assert plan.preservation_gate is not None
    assert plan.preservation_gate.verdict is PreservationGateVerdict.RECEIPT_MISSING
    assert not plan.candidate_generation_allowed
    assert not plan.candidate_paths
    assert "freeze_surrogate_to_root_preservation_receipt" in plan.pre_candidate_actions


def test_stale_preservation_receipt_blocks_candidate_search() -> None:
    receipt = _preservation_receipt(root_claim_id="C")
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        **_strict_kwargs(),
        preservation_receipt=receipt,
        expected_preservation_sha256="0" * 64,
    )
    assert plan.preservation_gate is not None
    assert plan.preservation_gate.verdict is PreservationGateVerdict.RECEIPT_STALE
    assert not plan.candidate_generation_allowed
    assert not plan.candidate_paths


def test_fresh_preservation_receipt_allows_candidate_search_after_other_gates() -> None:
    receipt = _preservation_receipt(root_claim_id="C")
    digest = receipt.document()["receipt_canonical_sha256"]
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        **_strict_kwargs(),
        preservation_receipt=receipt,
        expected_preservation_sha256=digest,
    )
    assert plan.preservation_gate is not None
    assert plan.preservation_gate.verdict is PreservationGateVerdict.SEARCH_LICENSED
    assert plan.candidate_generation_allowed
    assert plan.candidate_paths
    assert plan.preservation_gate.advances_root_claim is False


def test_absent_preservation_gate_stays_inactive_for_ordinary_planning() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        **_strict_kwargs(),
    )
    assert plan.preservation_gate is not None
    assert plan.preservation_gate.verdict is PreservationGateVerdict.NOT_REQUIRED
    assert plan.candidate_generation_allowed
