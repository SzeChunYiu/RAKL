from __future__ import annotations

from rakl.core import Authority, KnowledgeFiber, Projection
from rakl.experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    SubstrateKind,
    SubstrateRelation,
    TaskEpisode,
    add_episode,
    add_lesson,
)
from rakl.failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    add_failure_experience,
)
from rakl.research_tool_inventory import (
    ResearchTool,
    ResearchToolAuthority,
    ResearchToolInventory,
    add_research_tool,
)
from rakl.unified_substrate import materialize_unified_substrate


def test_unified_substrate_links_episode_failure_lesson_tool_and_knowledge() -> None:
    episode = TaskEpisode(
        episode_id="E1",
        task_id="task",
        atom_id="A1",
        context_hash="ctx",
        problem_signature=("graph", "bridge"),
        fibre_snapshot_hash="fibre",
        operator_ids=("bridge-op",),
        action_trace=("act",),
        observation_ids=("obs",),
        verification_ids=("verify",),
        outcome=EpisodeOutcome.PARTIAL_SUCCESS,
        residual_signature=("boundary",),
        evidence_pointers=("artifact:E1",),
        artifact_hash="sha256:E1",
        timestamp="2026-08-11T09:05:00+00:00",
    )
    experience = add_episode(ExperienceLedger(), episode)
    lesson = Lesson(
        lesson_id="L1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("graph",),
        context_scope=("ctx",),
        action="apply bounded bridge",
        expected_effects=("connect",),
        boundaries=("boundary",),
        supporting_episode_ids=("E1",),
        contradicting_episode_ids=(),
        falsifier="boundary counterexample",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=("validate boundary",),
        evidence_pointers=("artifact:E1",),
        artifact_hash="sha256:L1",
    )
    experience = add_lesson(experience, lesson)

    failure = FailureExperience(
        failure_id="F1",
        atom_id="A1",
        candidate_id="candidate",
        context_packet_hash="ctx",
        research_trace_event_id="E1",
        method_family="bridge-method",
        failure_mode="boundary mismatch",
        residual_signature=("boundary",),
        broken_assumptions=(),
        scope_conditions=("ctx",),
        competing_diagnoses=("scope mismatch", "bad bridge"),
        selected_diagnosis="scope mismatch",
        diagnosis_status=FailureDiagnosisStatus.SUPPORTED,
        evidence_pointers=("artifact:E1",),
        falsifier_or_attempt="boundary test",
        observed_result="PARTIAL_SUCCESS",
        artifact_hash="sha256:F1",
        timestamp="2026-08-11T09:05:00+00:00",
    )
    failures = add_failure_experience(FailureExperienceLattice(), failure)

    tool = ResearchTool(
        tool_id="T1",
        name="bounded bridge",
        kind="bridge-method",
        abstraction="OPERATOR",
        source_atom_id="A1",
        source_candidate_id="L1",
        source_result_ids=("verify",),
        source_context_hash="ctx",
        authority=ResearchToolAuthority.VERIFIED_LOCAL,
        preconditions=("ctx",),
        structural_signature=("graph",),
        operation="apply bounded bridge",
        guaranteed_effects=("connect",),
        non_guarantees=("not outside boundary",),
        validation_obligations=("validate target",),
        evidence_pointers=("artifact:E1",),
        known_failure_ids=("F1",),
        artifact_hash="sha256:T1",
    )
    tools = add_research_tool(ResearchToolInventory(), tool)

    knowledge = KnowledgeFiber("KF1", "object", "bridge")
    knowledge.add_projection(
        Projection(
            projection_id="P1",
            object_id="object",
            facets=("graph",),
            claim="graph bridge fact",
            source="source",
            authority=Authority.NORMALIZED_CLAIM,
        )
    )

    snapshot = materialize_unified_substrate(
        experience=experience,
        tools=tools,
        failures=failures,
        legacy_knowledge_fibers=(knowledge,),
    )
    assert snapshot.unresolved_links == ()
    assert len(snapshot.nodes_of_kind(SubstrateKind.EPISTEMIC)) == 1
    assert len(snapshot.nodes_of_kind(SubstrateKind.OPERATOR)) >= 2  # lesson + ResearchTool
    assert len(snapshot.nodes_of_kind(SubstrateKind.OBSTRUCTION)) == 1
    edge_relations = {edge.relation for edge in snapshot.edges}
    assert SubstrateRelation.FAILED_WITH in edge_relations
    assert SubstrateRelation.DERIVED_FROM in edge_relations
    assert SubstrateRelation.CONTRADICTS in edge_relations
    assert snapshot.snapshot_hash
