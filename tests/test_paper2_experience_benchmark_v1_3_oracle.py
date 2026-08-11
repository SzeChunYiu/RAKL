"""Freeze locks for ExperienceBenchmark v1.3 Phase-1 ORACLE (#247)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.experience_benchmark import ExperienceBenchmarkArm
from rakl.paper2_experience_benchmark_runner import (
    LEARNING_LOOP_ROOT_CAUSE_V1,
    PACKET_REL_V1_3,
    PROTOCOL_SUBJECT_HASH_V1_2,
    PROTOCOL_SUBJECT_HASH_V1_3,
    build_user_prompt,
    execute_experience_benchmark,
)
from rakl.paper2_experience_root_cause import (
    ORACLE_PASS_MIN_SUCCESS_RATE,
    RootCauseDiagnosticArm,
    oracle_procedure_upper_bound,
)
from rakl.paper2_pendulum_microtrial import BackendGeneration

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research" / "paper2_experience_benchmark_v1_3"


def test_v1_3_protocol_subject_hash_frozen() -> None:
    packet = json.loads((PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    assert packet["benchmark_id"] == "paper2-experience-benchmark-v1_3"
    assert packet["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_3
    assert packet["protocol_subject_hash"] != PROTOCOL_SUBJECT_HASH_V1_2
    assert packet["issue"] == 247
    assert packet["learning_loop_mode"] == "root_cause_v1"
    assert packet["arms"][0] == "ORACLE_PROCEDURE_UPPER_BOUND"
    assert packet["primary_execution"]["forbid_1_5B_until_oracle_gate"] is True
    assert packet["parent_negative_history"]["reopen_issue_138"] is False
    assert packet["parent_negative_history"]["reinterpret_as_lift"] is False
    assert packet["resource_ceiling"]["max_external_retrieval_calls"] == 16
    assert packet["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert packet["runs"] == []


def test_difference_witness_not_scale_only() -> None:
    witness = json.loads((PACKET_DIR / "DIFFERENCE_WITNESS_V1_3.json").read_text(encoding="utf-8"))
    assert witness["explicitly_not_scale_only"] is True
    assert witness["parent_job_id"] == "3476548"
    assert witness["reopen_issue_138"] is False
    assert witness["reinterpret_parent_job_3476548_as_lift"] is False
    changed = " ".join(witness["what_changed"]).lower()
    assert "root_cause_v1" in changed or "learning_loop" in changed
    assert "rc1" in changed and "rc2" in changed
    assert any("model" in item.lower() and "0.5b" in item.lower() for item in witness["what_did_not_change"])
    assert len(witness["restored_or_replaced_assumptions"]) >= 2


def test_phase0_causal_arms_oracle_first() -> None:
    phase0 = json.loads((PACKET_DIR / "PHASE0_CAUSAL_ARMS_V1_3.json").read_text(encoding="utf-8"))
    assert phase0["execution_order"][0] == "ORACLE_PROCEDURE_UPPER_BOUND"
    assert phase0["arms"]["ORACLE_PROCEDURE_UPPER_BOUND"]["phase1_first"] is True
    assert phase0["frozen_before_model_output"] is True
    assert ORACLE_PASS_MIN_SUCCESS_RATE == pytest.approx(2.0 / 3.0)


def test_oracle_prompt_injects_checklist_without_task_ids() -> None:
    task = json.loads((PACKET_DIR / "tasks" / "T1.json").read_text(encoding="utf-8"))
    state = json.loads((PACKET_DIR / "protocol" / "INITIAL_STATE_S0.json").read_text(encoding="utf-8"))
    receipt: dict = {}
    prompt = build_user_prompt(
        arm=ExperienceBenchmarkArm.LEARNING_ENABLED,
        task=task,
        state=state,
        learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
        diagnostic_arm=RootCauseDiagnosticArm.ORACLE_PROCEDURE_UPPER_BOUND,
        retrieval_receipt_out=receipt,
    )
    for line in oracle_procedure_upper_bound():
        assert line in prompt
    assert "E1" not in " ".join(oracle_procedure_upper_bound())
    assert receipt["retrieval_calls"] == 1
    assert receipt["whole_state_dump"] is False
    assert receipt["diagnostic_arm"] == "ORACLE_PROCEDURE_UPPER_BOUND"


def test_oracle_transfer_only_execution(tmp_path: Path, monkeypatch) -> None:
    import rakl.paper2_experience_benchmark_runner as runner

    expected_sha = "a" * 40

    def fake_run(args, **kwargs):
        class Result:
            def __init__(self, stdout: str = "") -> None:
                self.stdout = stdout
                self.returncode = 0

        if len(args) >= 4 and args[0] == "git" and args[1] == "-C":
            cmd = list(args[3:])
            if cmd == ["rev-parse", "HEAD"] or cmd == ["rev-parse", "refs/remotes/origin/main"]:
                return Result(expected_sha + "\n")
            if cmd[:2] == ["status", "--porcelain"]:
                return Result("")
            return Result("")
        raise AssertionError(args)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.socket, "gethostname", lambda: "compute-node-1")

    snap = tmp_path / "snap"
    snap.mkdir()
    original_load = runner.load_frozen_protocol

    def patched_load(repo: Path, *, packet_rel=None, protocol_subject_hash=None):
        bundle = original_load(repo, packet_rel=packet_rel, protocol_subject_hash=protocol_subject_hash)
        bundle["model"] = dict(bundle["model"])
        bundle["model"]["snapshot_path"] = str(snap)
        return bundle

    monkeypatch.setattr(runner, "load_frozen_protocol", patched_load)

    sealed = {
        task_id: json.loads((PACKET_DIR / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))["sealed_answer"]
        for task_id in ("T1", "T2", "T3")
    }

    def backend(prompt: str, *, snapshot_path, seed, max_output_tokens) -> BackendGeneration:
        task_id = "T1"
        for candidate in ("T1", "T2", "T3"):
            if f"Task id: {candidate}" in prompt:
                task_id = candidate
                break
        answer = {
            "verdict": "CANNOT_CHECK",
            "selected_evidence_ids": [],
            "rejected_evidence_ids": [],
            "rationale_tags": ["oracle_probe"],
        }
        assert sealed[task_id]["verdict"] not in " ".join(oracle_procedure_upper_bound())
        return BackendGeneration(
            raw_text=json.dumps(answer),
            input_tokens=100,
            output_tokens=20,
            backend_version="test-backend",
            wall_time_ms=10,
            process_high_water_rss_bytes_after_arm=1,
        )

    out = tmp_path / "oracle-out"
    manifest = execute_experience_benchmark(
        ROOT,
        out,
        expected_repo_sha=expected_sha,
        scheduler_job_id="3999100",
        packet_rel=PACKET_REL_V1_3,
        protocol_subject_hash=PROTOCOL_SUBJECT_HASH_V1_3,
        learning_loop_mode=LEARNING_LOOP_ROOT_CAUSE_V1,
        diagnostic_arm=RootCauseDiagnosticArm.ORACLE_PROCEDURE_UPPER_BOUND,
        backend=backend,
    )
    assert manifest["oracle_transfer_only"] is True
    assert manifest["arms"] == ["ORACLE_PROCEDURE_UPPER_BOUND"]
    assert manifest["run_count"] == 3
    assert manifest["issue"] == 247
    runs = [json.loads(line) for line in (out / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [run["task_id"] for run in runs] == ["T1", "T2", "T3"]
    assert all(run["retrieval_receipt"]["retrieval_calls"] == 1 for run in runs)
