from __future__ import annotations

from rakl.driver_learning import DriverResult, DriverTask, run_learning_turn
from rakl.experience_substrate import EpisodeOutcome
from rakl.failure_lattice import FailureDiagnosisStatus
from rakl.problem_fibre import FibreKnowledgeItem, ProblemAtom
from rakl.v3_runtime import FailureProjectionSpec, RAKLV3State


def test_learning_driver_freezes_failure_episode_and_updates_failure_memory() -> None:
    atom = ProblemAtom(
        atom_id="A1",
        goal="construct bridge",
        context_hash="ctx-1",
        structural_coordinates=("bridge", "graph"),
        desired_effects=("connect",),
    )
    task = DriverTask(
        task_id="task-1",
        atom=atom,
        problem_signature=("bridge", "graph"),
        timestamp="2026-08-11T08:45:00+00:00",
    )

    def driver(request):
        assert request.fibre.atom.atom_id == "A1"
        assert tuple(item.item_id for item in request.fibre.knowledge_items) == ("K1",)
        return DriverResult(
            operator_ids=("bridge-op",),
            action_trace=("try bridge", "check interface"),
            observation_ids=("obs-1",),
            verification_ids=("verify-1",),
            outcome=EpisodeOutcome.FAILURE,
            residual_signature=("interface_mismatch",),
            evidence_pointers=("artifact:driver-1",),
            artifact_hash="sha256:driver-1",
            cost=2.0,
        )

    def failure_spec(_result):
        return FailureProjectionSpec(
            failure_id="F1",
            candidate_id="candidate-1",
            method_family="bridge-method",
            failure_mode="interface mismatch",
            competing_diagnoses=("bad bridge", "scope mismatch"),
        )

    report = run_learning_turn(
        RAKLV3State(),
        task,
        driver,
        episode_id="E1",
        knowledge_items=(
            FibreKnowledgeItem(
                item_id="K1",
                kind="epistemic",
                structural_signature=("bridge", "graph"),
                effects=("connect",),
                context_tags=("ctx-1",),
                authority="VERIFIED",
                payload_hash="sha256:K1",
            ),
        ),
        candidate_method_families=("bridge-method",),
        failure_spec_factory=failure_spec,
    )

    assert report.episode.fibre_snapshot_hash == report.fibre.snapshot_hash
    assert report.state.experience.episodes[0].episode_id == "E1"
    assert report.state.failures.experiences[0].failure_id == "F1"
    assert report.state.failures.experiences[0].diagnosis_status is FailureDiagnosisStatus.OBSERVED_ONLY


def test_successful_learning_turn_records_experience_without_failure_projection() -> None:
    atom = ProblemAtom("A1", "solve", "ctx", ("structure",), ("solve",))
    task = DriverTask("task-success", atom, ("structure",), "2026-08-11T08:46:00+00:00")

    def driver(_request):
        return DriverResult(
            operator_ids=("op",),
            action_trace=("apply op",),
            observation_ids=("obs",),
            verification_ids=("verify",),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("artifact:success",),
            artifact_hash="sha256:success",
        )

    report = run_learning_turn(RAKLV3State(), task, driver, episode_id="E-success")
    assert tuple(episode.episode_id for episode in report.state.experience.episodes) == ("E-success",)
    assert report.state.failures.experiences == ()
