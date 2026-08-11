from __future__ import annotations

import pytest

from rakl.evolution import EvolutionTrial, EvolutionVerdict
from rakl.evolution_archive import (
    RAKLVariant,
    VariantStatus,
    initialize_evolution_archive,
    promote_incumbent,
    record_evolution_trial,
    register_challenger,
)
from rakl.experience_learning import ConsolidationVerdict, LessonConsolidationEvidence
from rakl.experience_policy import (
    assess_invention_readiness,
    induce_strategy_motifs,
    rank_operators_with_experience,
)
from rakl.experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    add_episode,
)
from rakl.failure_lattice import FailureDiagnosisStatus
from rakl.problem_fibre import (
    FibreKnowledgeItem,
    LocalSection,
    ProblemAtom,
    ProblemDecomposition,
    glue_local_sections,
)
from rakl.problem_solving_algebra import ObstructionKind, OperatorFamily, ProblemSignature, ProblemState, ResearchOperator
from rakl.saturation_vector import NoveltyRound, SaturationAxis, assess_saturation_vector
from rakl.v3_runtime import (
    FailureProjectionSpec,
    RAKLV3State,
    ToolProjectionSpec,
    compile_state_fibre,
    consolidate_lesson,
    record_task_episode,
)


def _episode(
    episode_id: str,
    outcome: EpisodeOutcome,
    *,
    operators: tuple[str, ...] = ("bridge-op",),
    context_hash: str = "ctx-1",
    signature: tuple[str, ...] = ("bridge", "graph"),
    residual: tuple[str, ...] = (),
    cost: float = 1.0,
) -> TaskEpisode:
    if outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.PARTIAL_SUCCESS} and not residual:
        residual = ("bridge",)
    return TaskEpisode(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="A1",
        context_hash=context_hash,
        problem_signature=signature,
        fibre_snapshot_hash=f"fibre-{episode_id}",
        operator_ids=operators,
        action_trace=("compile fibre", "apply operator", "verify outcome"),
        observation_ids=(f"obs-{episode_id}",),
        verification_ids=(f"verify-{episode_id}",),
        outcome=outcome,
        residual_signature=residual,
        evidence_pointers=(f"artifact:{episode_id}",),
        artifact_hash=f"sha256:{episode_id}",
        timestamp="2026-08-11T08:30:00+00:00",
        cost=cost,
    )


def _lesson() -> Lesson:
    return Lesson(
        lesson_id="L1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("bridge", "graph"),
        context_scope=("finite graph", "typed interface"),
        action="introduce a typed bridge object before global composition",
        expected_effects=("connect", "reduce_missing_bridge"),
        boundaries=("does not prove bridge correctness", "requires interface validation"),
        supporting_episode_ids=("E1",),
        contradicting_episode_ids=(),
        falsifier="old no-bridge counterexample still passes unchanged",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=("validate bridge mapping", "replay prior counterexample"),
        evidence_pointers=("artifact:E1",),
        artifact_hash="sha256:L1",
    )


def test_episode_is_preserved_as_immutable_evidence_root() -> None:
    episode = _episode("E1", EpisodeOutcome.SUCCESS)
    ledger = add_episode(ExperienceLedger(), episode)
    assert ledger.episodes == (episode,)
    assert ledger.nodes[0].node_id == "E1"
    with pytest.raises(ValueError, match="duplicate episode id"):
        add_episode(ledger, episode)


def test_legacy_ids_and_independence_boole_fail_closed() -> None:
    state = RAKLV3State()
    state = record_task_episode(state, _episode("E1", EpisodeOutcome.SUCCESS))
    state = record_task_episode(state, _episode("E2", EpisodeOutcome.SUCCESS, context_hash="ctx-transfer"))

    local = consolidate_lesson(
        state,
        _lesson(),
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            verification_artifact_ids=("external-check-1",),
        ),
        promoted_lesson_id="L1-local",
        promoted_artifact_hash="sha256:L1-local",
    )
    assert local.report.verdict is ConsolidationVerdict.CANNOT_CHECK
    assert local.promoted_lesson_id is None

    reusable = consolidate_lesson(
        state,
        _lesson(),
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_artifact_ids=("external-check-1",),
            evaluator_separated=True,
            evidence_lineage_independent=True,
        ),
        promoted_lesson_id="L1-reusable",
        promoted_artifact_hash="sha256:L1-reusable",
        tool_spec=ToolProjectionSpec("T1", "typed bridge construction", "bridge-method"),
    )
    assert reusable.report.verdict is ConsolidationVerdict.CANNOT_CHECK
    assert reusable.projected_tool_id is None
    assert tuple(tool.tool_id for tool in reusable.state.tools.tools) == ()
    assert tuple(episode.episode_id for episode in reusable.state.experience.episodes) == ("E1", "E2")


def test_failure_learning_records_observation_without_inventing_cause() -> None:
    state = record_task_episode(
        RAKLV3State(),
        _episode("FEP1", EpisodeOutcome.FAILURE, residual=("bridge", "interface_mismatch")),
        failure_spec=FailureProjectionSpec(
            failure_id="F1",
            candidate_id="candidate-1",
            method_family="bridge-method",
            failure_mode="interface mismatch after local success",
            competing_diagnoses=("wrong bridge", "wrong interface", "missing context"),
        ),
    )
    assert len(state.failures.experiences) == 1
    failure = state.failures.experiences[0]
    assert failure.diagnosis_status is FailureDiagnosisStatus.OBSERVED_ONLY
    assert failure.selected_diagnosis == ""
    assert failure.research_trace_event_id == "FEP1"


def test_problem_fibre_unifies_knowledge_tools_episodes_and_failures() -> None:
    state = RAKLV3State()
    state = record_task_episode(state, _episode("E1", EpisodeOutcome.SUCCESS))
    state = record_task_episode(state, _episode("E2", EpisodeOutcome.SUCCESS, context_hash="ctx-transfer"))
    promoted = consolidate_lesson(
        state,
        _lesson(),
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_artifact_ids=("external-check",),
            evaluator_separated=True,
            evidence_lineage_independent=True,
        ),
        promoted_lesson_id="L1-v2",
        promoted_artifact_hash="sha256:L1-v2",
        tool_spec=ToolProjectionSpec("T1", "typed bridge construction", "bridge-method"),
    )
    state = record_task_episode(
        promoted.state,
        _episode("E3", EpisodeOutcome.FAILURE, residual=("bridge", "interface_mismatch")),
        failure_spec=FailureProjectionSpec(
            failure_id="F1",
            candidate_id="candidate-3",
            method_family="bridge-method",
            failure_mode="interface mismatch",
            competing_diagnoses=("scope mismatch", "bad bridge"),
        ),
    )
    atom = ProblemAtom(
        atom_id="A-target",
        goal="connect two local representations",
        context_hash="ctx-1",
        structural_coordinates=("bridge", "graph"),
        desired_effects=("connect",),
    )
    fibre = compile_state_fibre(
        state,
        atom,
        knowledge_items=(
            FibreKnowledgeItem(
                item_id="K1",
                kind="epistemic",
                structural_signature=("graph", "bridge"),
                effects=("connect",),
                context_tags=("ctx-1",),
                authority="VERIFIED",
                payload_hash="sha256:K1",
            ),
        ),
        candidate_method_families=("bridge-method",),
    )
    assert tuple(item.item_id for item in fibre.knowledge_items) == ("K1",)
    assert tuple(tool.tool_id for tool in fibre.tools) == ()
    assert "F1" in {failure.failure_id for failure in fibre.failures}
    assert {episode.episode_id for episode in fibre.episodes} >= {"E1", "E3"}


def test_gluing_requires_compatibility_verification_and_complete_coverage() -> None:
    a1 = ProblemAtom("A1", "produce x", "ctx", ("x",), ("produce",))
    a2 = ProblemAtom("A2", "consume x", "ctx", ("x",), ("consume",), dependencies=("A1",))
    decomposition = ProblemDecomposition("P", (a1, a2))

    incomplete = glue_local_sections(
        decomposition,
        (LocalSection("S1", "A1", (("x", "1"),), (), ("op",), ("ev",), True),),
    )
    assert not incomplete.complete_coverage
    assert not incomplete.grants_solution_authority

    conflict = glue_local_sections(
        decomposition,
        (
            LocalSection("S1", "A1", (("x", "1"),), (), ("op",), ("ev1",), True),
            LocalSection("S2", "A2", (("x", "2"),), (), ("op",), ("ev2",), True),
        ),
    )
    assert not conflict.compatible
    assert conflict.obstructions[0].key == "x"
    assert not conflict.grants_solution_authority

    glued = glue_local_sections(
        decomposition,
        (
            LocalSection("S1", "A1", (("x", "1"),), (), ("op",), ("ev1",), True),
            LocalSection("S2", "A2", (("x", "1"),), (), ("op",), ("ev2",), True),
        ),
    )
    assert glued.compatible and glued.complete_coverage and not glued.all_sections_verified
    assert not glued.grants_solution_authority


def test_operator_routing_learns_from_success_and_failure_without_minting_authority() -> None:
    good = ResearchOperator(
        "good-op",
        OperatorFamily.META_DISCOVERY,
        targets=frozenset({ObstructionKind.MISSING_BRIDGE}),
        clears=frozenset({ObstructionKind.MISSING_BRIDGE}),
    )
    bad = ResearchOperator(
        "bad-op",
        OperatorFamily.META_DISCOVERY,
        targets=frozenset({ObstructionKind.MISSING_BRIDGE}),
        clears=frozenset({ObstructionKind.MISSING_BRIDGE}),
    )
    state = ProblemState(
        "S",
        ProblemSignature(domain="test"),
        obstructions=frozenset({ObstructionKind.MISSING_BRIDGE}),
    )
    ledger = ExperienceLedger()
    ledger = add_episode(ledger, _episode("G1", EpisodeOutcome.SUCCESS, operators=("good-op",)))
    ledger = add_episode(ledger, _episode("G2", EpisodeOutcome.SUCCESS, operators=("good-op",)))
    ledger = add_episode(ledger, _episode("B1", EpisodeOutcome.FAILURE, operators=("bad-op",), residual=("bridge",)))
    ranked = rank_operators_with_experience(
        state,
        (bad, good),
        ledger,
        target_signature=("bridge", "graph"),
        context_hash="ctx-1",
    )
    assert ranked[0].operator.operator_id == "good-op"
    assert "experience_affects_search_priority_only" in ranked[0].reasons


def test_strategy_motifs_are_induced_from_repeated_trajectories_with_failure_history() -> None:
    ledger = ExperienceLedger()
    ledger = add_episode(ledger, _episode("S1", EpisodeOutcome.SUCCESS, operators=("a", "b", "c")))
    ledger = add_episode(ledger, _episode("S2", EpisodeOutcome.SUCCESS, operators=("a", "b", "c"), context_hash="ctx-2"))
    ledger = add_episode(ledger, _episode("F1", EpisodeOutcome.FAILURE, operators=("a", "b", "c"), residual=("boundary",)))
    motifs = induce_strategy_motifs(ledger, min_support=2)
    full = next(item for item in motifs if item.motif.operator_ids == ("a", "b", "c"))
    assert full.support_count == 2
    assert full.contradiction_count == 1
    assert full.contradicting_episode_ids == ("F1",)


def _flat_round(round_id: str, route: str) -> NoveltyRound:
    return NoveltyRound(
        round_id=round_id,
        route_family=route,
        independent_route=True,
        retained_novelty=tuple((axis, 0) for axis in SaturationAxis),
    )


def test_saturation_is_vector_valued_and_native_residual_reopens_only_relevant_axis() -> None:
    base = (_flat_round("R1", "historical"), _flat_round("R2", "alien-domain"))
    report = assess_saturation_vector(base, required_axes=(SaturationAxis.KNOWLEDGE, SaturationAxis.OPERATOR, SaturationAxis.PATH))
    assert report.bounded_saturated

    reopened = base + (
        NoveltyRound(
            round_id="R3",
            route_family="native-test",
            independent_route=True,
            retained_novelty=tuple((axis, 0) for axis in SaturationAxis),
            residual_axes=(SaturationAxis.PATH,),
            residual_signature=("gluing failure",),
        ),
    )
    report2 = assess_saturation_vector(reopened, required_axes=(SaturationAxis.KNOWLEDGE, SaturationAxis.OPERATOR, SaturationAxis.PATH))
    assert report2.flat(SaturationAxis.KNOWLEDGE)
    assert not report2.flat(SaturationAxis.PATH)
    assert not report2.bounded_saturated


def test_invention_requires_bounded_flat_search_plus_identified_method_gap() -> None:
    report = assess_saturation_vector(
        (_flat_round("R1", "historical"), _flat_round("R2", "alien-domain")),
        required_axes=(SaturationAxis.KNOWLEDGE, SaturationAxis.OPERATOR, SaturationAxis.PATH),
    )
    not_ready = assess_invention_readiness(
        report,
        stable_residual_count=2,
        ordinary_causes_excluded=False,
        cross_domain_routes_exhausted=True,
        representation_gap_supported=False,
        method_basis_gap_supported=True,
    )
    assert not not_ready.ready

    ready = assess_invention_readiness(
        report,
        stable_residual_count=2,
        ordinary_causes_excluded=True,
        cross_domain_routes_exhausted=True,
        representation_gap_supported=False,
        method_basis_gap_supported=True,
    )
    assert ready.ready and ready.target == "OPERATOR"
    assert not ready.grants_invention_authority


def test_self_evolution_preserves_branching_and_never_auto_promotes() -> None:
    parent = RAKLVariant(
        variant_id="v1",
        method_hash="sha256:v1",
        parent_ids=(),
        capability_tags=("research",),
        resource_profile=(("token_cost", 1.0),),
        created_by_episode_ids=(),
        status=VariantStatus.INCUMBENT,
    )
    archive = initialize_evolution_archive(parent)
    archive = register_challenger(
        archive,
        RAKLVariant(
            variant_id="v2",
            method_hash="sha256:v2",
            parent_ids=("v1",),
            capability_tags=("research",),
            resource_profile=(("token_cost", 1.1),),
            created_by_episode_ids=("meta-E1",),
            status=VariantStatus.CHALLENGER,
        ),
    )
    trial = EvolutionTrial(
        parent_version="v1",
        child_version="v2",
        development_benchmark_id="dev-frozen",
        development_improvements={"known_answer_accuracy": 0.1},
        assurance_benchmark_id="assurance-frozen",
        transfer_improvements={"known_answer_accuracy": 0.05},
        transfer_regressions={},
        tests_passed=True,
        receipt_present=True,
        development_benchmark_frozen_before_result=True,
        assurance_benchmark_frozen_before_mutation=True,
        assurance_hidden_from_proposer=True,
        assurance_evaluator_separate=True,
        candidate_identity_verified=True,
        resource_comparability_verified=True,
        history_preserved=True,
        blocking_failures=(),
        assurance_exposure_limit=1,
        assurance_exposures_before_trial=0,
    )
    archive, assessment = record_evolution_trial(archive, trial_id="T1", child_variant_id="v2", trial=trial)
    assert assessment.verdict is EvolutionVerdict.CANNOT_CHECK
    assert archive.incumbent_id == "v1"
    assert next(v for v in archive.variants if v.variant_id == "v2").status is VariantStatus.CHALLENGER
