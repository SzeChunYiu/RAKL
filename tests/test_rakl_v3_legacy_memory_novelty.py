from __future__ import annotations

from rakl.core import Authority, KnowledgeFiber, Projection
from rakl.experience_memory import experience_memory_views
from rakl.experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    add_episode,
    add_lesson,
)
from rakl.multires_memory import MemoryViewKind, MemoryViewVerdict, validate_memory_view
from rakl.problem_fibre import ProblemAtom, compile_problem_fibre
from rakl.problem_novelty import (
    ProblemNoveltyClass,
    ProblemNoveltyEvidence,
    assess_rakl_triviality,
    classify_problem_novelty,
)


def _episode() -> TaskEpisode:
    return TaskEpisode(
        episode_id="E1",
        task_id="task",
        atom_id="A1",
        context_hash="ctx",
        problem_signature=("graph", "bridge"),
        fibre_snapshot_hash="fibre",
        operator_ids=("existing-op",),
        action_trace=("apply existing op",),
        observation_ids=("obs",),
        verification_ids=("verify",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("artifact:E1",),
        artifact_hash="sha256:E1",
        timestamp="2026-08-11T09:00:00+00:00",
    )


def _legacy(fiber_id: str, object_id: str, projection_id: str = "P1") -> KnowledgeFiber:
    legacy = KnowledgeFiber(fiber_id, object_id, "construct bridge")
    legacy.add_projection(
        Projection(
            projection_id=projection_id,
            object_id=object_id,
            facets=("graph", "bridge"),
            claim="a bridge construction exists under the registered scope",
            source=f"source-{fiber_id}",
            authority=Authority.NORMALIZED_CLAIM,
            tags=("connect",),
        )
    )
    return legacy


def test_existing_knowledge_fiber_projects_into_v3_problem_fibre() -> None:
    legacy = _legacy("KF1", "object-1")
    atom = ProblemAtom(
        atom_id="A1",
        goal="connect representations",
        context_hash="ctx",
        structural_coordinates=("graph", "bridge"),
        desired_effects=("connect",),
    )
    fibre = compile_problem_fibre(atom, legacy_knowledge_fibers=(legacy,))
    assert tuple(item.item_id for item in fibre.knowledge_items) == ("KF1:P1",)
    assert fibre.knowledge_items[0].authority == Authority.NORMALIZED_CLAIM.value
    assert fibre.knowledge_items[0].kind == "legacy_knowledge_projection"


def test_legacy_projection_ids_are_namespaced_by_owning_fibre() -> None:
    first = _legacy("KF1", "object-1", projection_id="P1")
    second = _legacy("KF2", "object-2", projection_id="P1")
    atom = ProblemAtom(
        atom_id="A1",
        goal="connect representations",
        context_hash="ctx",
        structural_coordinates=("graph", "bridge"),
        desired_effects=("connect",),
    )
    fibre = compile_problem_fibre(atom, legacy_knowledge_fibers=(first, second))
    assert {item.item_id for item in fibre.knowledge_items} == {"KF1:P1", "KF2:P1"}


def test_lessons_are_lossy_memory_views_over_canonical_episode_roots() -> None:
    ledger = add_episode(ExperienceLedger(), _episode())
    lesson = Lesson(
        lesson_id="L1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("graph",),
        context_scope=("ctx",),
        action="apply existing op",
        expected_effects=("connect",),
        boundaries=("scope-bound",),
        supporting_episode_ids=("E1",),
        contradicting_episode_ids=(),
        falsifier="registered counterexample",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=("validate target",),
        evidence_pointers=("artifact:E1",),
        artifact_hash="sha256:L1",
    )
    ledger = add_lesson(ledger, lesson)
    views = experience_memory_views(ledger)
    episode_view = next(view for view in views if view.record_id == "E1")
    lesson_view = next(view for view in views if view.record_id == "L1")
    assert episode_view.kind is MemoryViewKind.CANONICAL
    assert lesson_view.kind is MemoryViewKind.DERIVED_LOSSY
    assert lesson_view.source_pins[0].record_id == "E1"
    report = validate_memory_view("L1", views)
    assert report.verdict is MemoryViewVerdict.SOURCE_REHYDRATABLE
    assert report.canonical_root_ids == ("E1",)


def test_problem_novelty_distinguishes_composition_transfer_and_invention() -> None:
    trivial = classify_problem_novelty(
        ProblemNoveltyEvidence(
            problem_id="P-trivial",
            solution_verified=True,
            operator_ids=("op1", "op2"),
            preexisting_operator_ids=("op1", "op2", "op3"),
            all_required_resources_preexisting=True,
            evidence_pointers=("verification:P-trivial",),
        )
    )
    assert trivial.novelty_class is ProblemNoveltyClass.RAKL_TRIVIAL
    assert trivial.zero_invention_solution

    transfer = classify_problem_novelty(
        ProblemNoveltyEvidence(
            problem_id="P-transfer",
            solution_verified=True,
            operator_ids=("op1",),
            preexisting_operator_ids=("op1",),
            transfer_witness_ids=("map-domain-A-to-B",),
            all_required_resources_preexisting=True,
            evidence_pointers=("verification:P-transfer",),
        )
    )
    assert transfer.novelty_class is ProblemNoveltyClass.TRANSFER_NOVEL
    assert transfer.novel_structure_rank == 0

    invented = classify_problem_novelty(
        ProblemNoveltyEvidence(
            problem_id="P-new-op",
            solution_verified=True,
            operator_ids=("op-new",),
            preexisting_operator_ids=(),
            new_operator_ids=("op-new",),
            evidence_pointers=("verification:P-new-op",),
        )
    )
    assert invented.novelty_class is ProblemNoveltyClass.OPERATOR_NOVEL
    assert invented.required_new_problem_solving_structure

    portrait = assess_rakl_triviality(
        (
            ProblemNoveltyEvidence(
                problem_id="P-trivial",
                solution_verified=True,
                operator_ids=("op1", "op2"),
                preexisting_operator_ids=("op1", "op2"),
                all_required_resources_preexisting=True,
                evidence_pointers=("v1",),
            ),
            ProblemNoveltyEvidence(
                problem_id="P-transfer",
                solution_verified=True,
                operator_ids=("op1",),
                preexisting_operator_ids=("op1",),
                transfer_witness_ids=("map",),
                all_required_resources_preexisting=True,
                evidence_pointers=("v2",),
            ),
            ProblemNoveltyEvidence(
                problem_id="P-new-op",
                solution_verified=True,
                operator_ids=("op-new",),
                new_operator_ids=("op-new",),
                evidence_pointers=("v3",),
            ),
        )
    )
    assert portrait.solved_count == 3
    assert portrait.zero_invention_count == 2
    assert portrait.zero_invention_rate == 2 / 3
    assert portrait.operator_novel_count == 1
