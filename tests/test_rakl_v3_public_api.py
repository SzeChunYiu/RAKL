from __future__ import annotations

from rakl.v3 import (
    DriverResult,
    DriverTask,
    EpisodeOutcome,
    ProblemAtom,
    RAKLV3State,
    SaturationAxis,
    TaskEpisode,
    run_learning_turn,
)


def test_public_v3_facade_exposes_learning_runtime() -> None:
    atom = ProblemAtom(
        atom_id="A1",
        goal="solve",
        context_hash="ctx",
        structural_coordinates=("structure",),
        desired_effects=("solve",),
    )
    task = DriverTask(
        task_id="task",
        atom=atom,
        problem_signature=("structure",),
        timestamp="2026-08-11T08:50:00+00:00",
    )

    def driver(_request):
        return DriverResult(
            operator_ids=("op",),
            action_trace=("act",),
            observation_ids=("obs",),
            verification_ids=("verify",),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("artifact:api",),
            artifact_hash="sha256:api",
        )

    report = run_learning_turn(RAKLV3State(), task, driver, episode_id="E1")
    assert isinstance(report.episode, TaskEpisode)
    assert report.state.experience.episodes == (report.episode,)
    assert SaturationAxis.KNOWLEDGE.value == "KNOWLEDGE"
