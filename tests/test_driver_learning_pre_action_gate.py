"""Wire the #123 pre-action gate into run_learning_turn (fail-closed).

Cheap turns without a receipt stay ungated but are marked RETROSPECTIVE_ONLY.
Consequential turns that require or supply a receipt are blocked before the
driver runs when the binding is missing or mismatched.
"""

from __future__ import annotations

import pytest

from rakl.driver_learning import DriverResult, DriverTask, run_learning_turn
from rakl.experience_substrate import EpisodeOutcome
from rakl.pre_action_receipt import (
    ChronologyStatus,
    OperatorExecutionGateVerdict,
    PreActionFibreReceipt,
    RejectedRetrieval,
    RetrievalAuthority,
    SelectedRetrieval,
)
from rakl.problem_fibre import ProblemAtom
from rakl.v3_runtime import RAKLV3State, compile_state_fibre

FRAMEWORK_COMMIT = "1fe6477aac2299a210e99e1624e9f7e795a2a6d4"
APPLICATION_COMMIT = "6557b1b25fa839fe71aba8047c958d5da892edd8"
PAYLOAD_HASH = "a" * 64
OPERATOR_ID = "bridge-op"
FALSIFIER = "interface_mismatch separates bridge failure from scope mismatch"


def _atom() -> ProblemAtom:
    return ProblemAtom(
        atom_id="A1",
        goal="construct bridge",
        context_hash="ctx-1",
        structural_coordinates=("bridge", "graph"),
        desired_effects=("connect",),
    )


def _task(timestamp: str = "2026-08-11T10:00:00Z") -> DriverTask:
    return DriverTask(
        task_id="task-1",
        atom=_atom(),
        problem_signature=("bridge", "graph"),
        timestamp=timestamp,
    )


def _driver_success(request):
    return DriverResult(
        operator_ids=(OPERATOR_ID,),
        action_trace=("try bridge",),
        observation_ids=("obs-1",),
        verification_ids=("verify-1",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("artifact:driver-1",),
        artifact_hash="sha256:driver-1",
    )


def _receipt(*, fibre_snapshot_hash: str, frozen_at_utc: str = "2026-08-11T09:00:00Z") -> PreActionFibreReceipt:
    return PreActionFibreReceipt(
        receipt_id="R-1",
        framework_repository="SzeChunYiu/RAKL",
        framework_commit=FRAMEWORK_COMMIT,
        application_repository="SzeChunYiu/RAKL_math",
        application_commit=APPLICATION_COMMIT,
        task_id="task-1",
        atom_id="A1",
        context_hash="ctx-1",
        fibre_snapshot_hash=fibre_snapshot_hash,
        operator_ids=(OPERATOR_ID,),
        selected_retrievals=(
            SelectedRetrieval(
                retrieval_id="K-canonical-1",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash=PAYLOAD_HASH,
            ),
        ),
        rejected_retrievals=(
            RejectedRetrieval(
                retrieval_id="K-rejected-1",
                rejection_reason="enabling assumption absent",
            ),
        ),
        predeclared_discriminator=FALSIFIER,
        allowed_outcome_branches=("SUCCESS", "FAILURE"),
        frozen_at_utc=frozen_at_utc,
        sequence_index=0,
    )


def test_missing_receipt_marks_retrospective_without_blocking_cheap_turn() -> None:
    called = {"n": 0}

    def driver(request):
        called["n"] += 1
        return _driver_success(request)

    report = run_learning_turn(RAKLV3State(), _task(), driver, episode_id="E1")
    assert called["n"] == 1
    assert report.execution_gate is None
    assert report.chronology_binding.chronology_status is ChronologyStatus.RETROSPECTIVE_ONLY
    assert not report.chronology_binding.prospective_gate_admissible


def test_require_receipt_blocks_before_driver() -> None:
    called = {"n": 0}

    def driver(request):
        called["n"] += 1
        return _driver_success(request)

    with pytest.raises(ValueError, match="pre-action fibre receipt gate"):
        run_learning_turn(
            RAKLV3State(),
            _task(),
            driver,
            episode_id="E1",
            require_pre_action_receipt=True,
            intended_operator_id=OPERATOR_ID,
            intended_falsifier=FALSIFIER,
        )
    assert called["n"] == 0


def test_fibre_mismatch_blocks_before_driver() -> None:
    called = {"n": 0}

    def driver(request):
        called["n"] += 1
        return _driver_success(request)

    with pytest.raises(ValueError, match="fibre_snapshot_hash_mismatch"):
        run_learning_turn(
            RAKLV3State(),
            _task(),
            driver,
            episode_id="E1",
            pre_action_receipt=_receipt(fibre_snapshot_hash="fibre-OTHER"),
            intended_operator_id=OPERATOR_ID,
            intended_falsifier=FALSIFIER,
        )
    assert called["n"] == 0


def test_bound_receipt_allows_turn_and_verifies_prospective_binding() -> None:
    state = RAKLV3State()
    task = _task()
    fibre = compile_state_fibre(state, task.atom)
    receipt = _receipt(fibre_snapshot_hash=fibre.snapshot_hash)

    report = run_learning_turn(
        state,
        task,
        _driver_success,
        episode_id="E1",
        pre_action_receipt=receipt,
        intended_operator_id=OPERATOR_ID,
        intended_falsifier=FALSIFIER,
    )

    assert report.execution_gate is not None
    assert report.execution_gate.verdict is OperatorExecutionGateVerdict.ALLOWED
    assert report.execution_gate.may_execute is True
    assert report.execution_gate.grants_prospective_or_theorem_authority is False
    assert receipt.episode_pointer in report.episode.evidence_pointers
    assert report.chronology_binding.chronology_status is ChronologyStatus.PROSPECTIVE_BOUND
    assert report.chronology_binding.prospective_gate_admissible is True
