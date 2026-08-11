"""RC1/RC2 learning-loop repair for ExperienceBenchmark (#238).

Locks the successor ``root_cause_v1`` path without mutating frozen v1/v1.1/v1.2
semantics or reinterpreting job 3476548.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.experience_benchmark import ExperienceBenchmarkArm
from rakl.paper2_experience_benchmark_runner import (
    LEARNING_LOOP_LEGACY_V1_2,
    LEARNING_LOOP_ROOT_CAUSE_V1,
    PROTOCOL_SUBJECT_HASH_V1_2,
    _append_learning_state,
    build_user_prompt,
    execute_experience_benchmark,
)
from rakl.paper2_experience_root_cause import (
    FROZEN_DEVELOPMENT_PRINCIPLES,
    RootCauseDiagnosticArm,
    apply_development_learning_step,
    materialize_selective_experience,
    oracle_procedure_upper_bound,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR_V1_2 = ROOT / "research" / "paper2_experience_benchmark_v1_2"


def _empty_state() -> dict:
    return {
        "schema_version": "rakl-experience-benchmark-initial-state-v1",
        "state_kind": "RESET_BASELINE_STATE",
        "episodes": [],
        "lessons": [],
        "failure_lattice_entries": [],
        "tools": [],
    }


def _task(task_id: str) -> dict:
    return json.loads((PACKET_DIR_V1_2 / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))


def test_legacy_v1_2_still_mints_pseudo_lesson_on_failure() -> None:
    """Historical path remains re-executable as recorded (immutable negative history)."""
    state = _append_learning_state(
        _empty_state(),
        task=_task("D1"),
        predicted={"verdict": "CONTEXT_MISALIGNED", "selected_evidence_ids": [], "rejected_evidence_ids": [], "rationale_tags": []},
        score=0.0,
        success=False,
        failure_signature=("verdict_mismatch",),
        output_hash="a" * 64,
        learning_loop_mode=LEARNING_LOOP_LEGACY_V1_2,
    )
    assert len(state["lessons"]) == 1
    assert "Do not repeat the same failure signature" in state["lessons"][0]["principle"]


def test_root_cause_failure_creates_no_reusable_lesson() -> None:
    state = _append_learning_state(
        _empty_state(),
        task=_task("D1"),
        predicted={"verdict": "CONTEXT_MISALIGNED", "selected_evidence_ids": ["E1"], "rejected_evidence_ids": [], "rationale_tags": []},
        score=0.25,
        success=False,
        failure_signature=("verdict_mismatch", "reject_recall_incomplete"),
        output_hash="b" * 64,
        learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
        diagnostic_arm=RootCauseDiagnosticArm.FAILURE_MEMORY_ONLY,
    )
    assert len(state["episodes"]) == 1
    assert state["episodes"][0]["sealed_answer_included"] is False
    assert state["lessons"] == []
    assert len(state["failure_lattice_entries"]) == 1


def test_verified_feedback_requires_frozen_output_chronology() -> None:
    with pytest.raises(ValueError, match="development_output_not_frozen"):
        apply_development_learning_step(
            _empty_state(),
            arm=RootCauseDiagnosticArm.VERIFIED_DEVELOPMENT_LESSONS,
            task=_task("D1"),
            predicted=None,
            score=0.0,
            success=False,
            failure_signature=("verdict_mismatch",),
            output_hash="c" * 64,
            output_frozen=False,
        )


def test_verified_lessons_admitted_after_failed_development_without_pseudo_lesson() -> None:
    """Even when D fails, verified method feedback may enter after freeze+score."""
    state = apply_development_learning_step(
        _empty_state(),
        arm=RootCauseDiagnosticArm.VERIFIED_DEVELOPMENT_LESSONS,
        task=_task("D1"),
        predicted={"verdict": "CONTEXT_MISALIGNED", "selected_evidence_ids": [], "rejected_evidence_ids": [], "rationale_tags": []},
        score=0.0,
        success=False,
        failure_signature=("verdict_mismatch",),
        output_hash="d" * 64,
        output_frozen=True,
    )
    assert len(state["episodes"]) == 1
    assert state["episodes"][0]["success"] is False
    assert len(state["lessons"]) == 1
    lesson = state["lessons"][0]
    assert lesson["authority"] == "VERIFIED_DEVELOPMENT_METHOD_ONLY"
    assert lesson["principle"] == FROZEN_DEVELOPMENT_PRINCIPLES["D1"]
    assert "E1" not in lesson["principle"]
    assert "T1" not in lesson["principle"]


def test_development_sequence_d1_d3_then_transfer_starts_from_same_sn() -> None:
    state = _empty_state()
    hashes = []
    for task_id in ("D1", "D2", "D3"):
        state = apply_development_learning_step(
            state,
            arm=RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
            task=_task(task_id),
            predicted={"verdict": "SUPPORT", "selected_evidence_ids": [], "rejected_evidence_ids": [], "rationale_tags": []},
            score=0.0,
            success=False,
            failure_signature=("verdict_mismatch",),
            output_hash=f"{ord(task_id[-1]):02x}" + "a" * 62,
            output_frozen=True,
        )
        hashes.append(json.dumps(state, sort_keys=True))
    sn = state
    assert len(sn["episodes"]) == 3
    assert len(sn["lessons"]) == 3
    assert all("Do not repeat the same failure signature" not in item["principle"] for item in sn["lessons"])

    # Transfer probes must not mutate Sn under root_cause_v1.
    after_t1 = _append_learning_state(
        sn,
        task=_task("T1"),
        predicted={"verdict": "SUPPORT", "selected_evidence_ids": [], "rejected_evidence_ids": [], "rationale_tags": []},
        score=0.0,
        success=False,
        failure_signature=("verdict_mismatch",),
        output_hash="e" * 64,
        learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
        diagnostic_arm=RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
    )
    assert after_t1 == sn


def test_selective_materialization_records_retrieval_not_whole_state_dump() -> None:
    state = apply_development_learning_step(
        _empty_state(),
        arm=RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
        task=_task("D1"),
        predicted={"verdict": "CONTEXT_MISALIGNED", "selected_evidence_ids": [], "rejected_evidence_ids": [], "rationale_tags": []},
        score=0.0,
        success=False,
        failure_signature=("verdict_mismatch",),
        output_hash="f" * 64,
        output_frozen=True,
    )
    receipt = materialize_selective_experience(
        state,
        arm=RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
        target_stratum="REPEATED_FAMILY",
    )
    assert receipt.whole_state_dump is False
    assert receipt.retrieval_calls >= 1
    assert receipt.selected_lesson_ids
    assert "episodes" not in receipt.rendered_state
    assert "verified_development_lessons" in receipt.rendered_state

    prompt_receipt: dict = {}
    prompt = build_user_prompt(
        arm=ExperienceBenchmarkArm.LEARNING_ENABLED,
        task=_task("T1"),
        state=state,
        learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
        diagnostic_arm=RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
        retrieval_receipt_out=prompt_receipt,
    )
    assert "Selective RAKL experience materialization" in prompt
    assert "whole-state dump" in prompt
    assert '"episodes"' not in prompt
    assert prompt_receipt["retrieval_calls"] >= 1
    assert prompt_receipt["whole_state_dump"] is False
    # No sealed T answers in development-derived state/prompt.
    sealed = _task("T1")["sealed_answer"]
    assert sealed["verdict"] not in json.dumps(state)
    assert str(sealed["selected_evidence_ids"]) not in prompt


def test_oracle_checklist_has_no_task_specific_ids() -> None:
    joined = " ".join(oracle_procedure_upper_bound())
    assert "E1" not in joined
    assert "T1" not in joined
    for principle in FROZEN_DEVELOPMENT_PRINCIPLES.values():
        assert "E1" not in principle and "T1" not in principle


def test_root_cause_mode_refuses_frozen_v1_2_subject_rebind(tmp_path: Path, monkeypatch) -> None:
    """Successor learning loop must not silently reinterpret job 3476548's subject."""
    import rakl.paper2_experience_benchmark_runner as runner

    def fake_run(args, **kwargs):
        class Result:
            def __init__(self, stdout: str = "") -> None:
                self.stdout = stdout
                self.returncode = 0

        if len(args) >= 3 and args[0] == "git" and args[1] == "-C":
            return Result("a" * 40 + "\n")
        raise AssertionError(args)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "compute-node-1")
    with pytest.raises(RuntimeError, match="cannot bind frozen"):
        execute_experience_benchmark(
            ROOT,
            tmp_path / "out",
            expected_repo_sha="a" * 40,
            scheduler_job_id="3999002",
            learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
            protocol_subject_hash=PROTOCOL_SUBJECT_HASH_V1_2,
        )


def test_v1_2_historical_hashes_unchanged() -> None:
    packet = json.loads((PACKET_DIR_V1_2 / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    assert packet["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_2
    sn = PACKET_DIR_V1_2 / "native_job_3476548" / "runs" / "experience_v1_2" / "paper2-experience-benchmark-v1_2-job-3476548" / "states" / "Sn.json"
    learned = json.loads(sn.read_text(encoding="utf-8"))
    # Parent negative still contains the RC1 pseudo-lessons; do not rewrite history.
    assert any(
        "Do not repeat the same failure signature" in item.get("principle", "")
        for item in learned.get("lessons", [])
    )
