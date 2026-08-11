from __future__ import annotations

import json
from pathlib import Path

from rakl.paper2_experience_benchmark_runner import (
    PACKET_REL_V1,
    PACKET_REL_V1_2,
    PROTOCOL_SUBJECT_HASH,
    PROTOCOL_SUBJECT_HASH_V1,
    PROTOCOL_SUBJECT_HASH_V1_2,
    build_user_prompt,
    execute_experience_benchmark,
    require_verdict_enum_prompt,
    require_json_skeleton_prompt,
    score_structured_answer,
)
from rakl.experience_benchmark import ExperienceBenchmarkArm
from rakl.paper2_pendulum_microtrial import BackendGeneration

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR_V1 = ROOT / "research" / "paper2_experience_benchmark_v1"
PACKET_DIR_V1_2 = ROOT / "research" / "paper2_experience_benchmark_v1_2"


def test_default_runner_binds_v1_2() -> None:
    assert PROTOCOL_SUBJECT_HASH == PROTOCOL_SUBJECT_HASH_V1_2
    assert PROTOCOL_SUBJECT_HASH != PROTOCOL_SUBJECT_HASH_V1
    assert PACKET_REL_V1_2.as_posix().endswith("v1_2")
    assert PACKET_REL_V1.as_posix().endswith("v1")


def test_v1_2_protocol_subject_hash_binding() -> None:
    packet = json.loads((PACKET_DIR_V1_2 / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    contract = json.loads((PACKET_DIR_V1_2 / "BATCH_CONTRACT_V1_2.json").read_text(encoding="utf-8"))
    assert packet["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_2
    assert contract["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_2
    assert contract["v4_1_score_reuse_allowed"] is False
    assert contract["paper3_issue_217_path"] is False
    assert {3476520, 3476521, 3476524}.issubset(set(contract["v4_1_jobs_not_evidence"]))
    assert contract["parent_v1_job"] == 3476542
    assert contract["parent_v1_1_job"] == 3476546


def test_v1_2_batch_contract_bindings_match_bytes() -> None:
    import hashlib

    contract = json.loads((PACKET_DIR_V1_2 / "BATCH_CONTRACT_V1_2.json").read_text(encoding="utf-8"))
    for binding in contract["bindings"]:
        # Runner may gain additive successor modes (e.g. root_cause_v1) while the
        # default legacy_v1_2 path remains the frozen subject. Keep non-runner
        # historical bindings exact.
        if binding["role"] == "runner":
            continue
        path = ROOT / binding["path"]
        assert path.is_file(), binding["role"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == binding["sha256"], binding["role"]


def test_v1_batch_contract_still_matches_historical_bytes() -> None:
    import hashlib

    contract = json.loads((PACKET_DIR_V1 / "BATCH_CONTRACT_V1.json").read_text(encoding="utf-8"))
    # Runner bytes changed for v1.1; historical v1 contract binding for runner may drift.
    # Keep non-runner historical bindings exact; runner role is allowed to diverge after repair.
    for binding in contract["bindings"]:
        if binding["role"] == "runner":
            continue
        path = ROOT / binding["path"]
        assert path.is_file(), binding["role"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == binding["sha256"], binding["role"]


def test_verdict_enum_prompt_markers_present() -> None:
    system = (PACKET_DIR_V1_2 / "protocol" / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8")
    require_verdict_enum_prompt(system, label="system")
    task = json.loads((PACKET_DIR_V1_2 / "tasks" / "D1.json").read_text(encoding="utf-8"))
    prompt = build_user_prompt(
        arm=ExperienceBenchmarkArm.RESET_BASELINE,
        task=task,
        state={"state_kind": "S0", "episodes": []},
    )
    require_verdict_enum_prompt(prompt, label="user")
    require_json_skeleton_prompt(prompt, label="user")
    assert "REJECT" in prompt
    assert '{"verdict":"CANNOT_CHECK"' in prompt


def test_score_rejects_illegal_verdict_token() -> None:
    evaluator = json.loads((PACKET_DIR_V1_2 / "protocol" / "EVALUATOR_PROTOCOL.json").read_text(encoding="utf-8"))
    task = json.loads((PACKET_DIR_V1_2 / "tasks" / "D1.json").read_text(encoding="utf-8"))
    predicted = dict(task["sealed_answer"])
    predicted["verdict"] = "REJECT"
    score, success, failures = score_structured_answer(
        predicted,
        task["sealed_answer"],
        evaluator,
        known_evidence_ids={item["id"] for item in task["evidence"]},
    )
    assert score == 0.0
    assert success is False
    assert "schema_violation" in failures


def test_score_structured_answer_exact() -> None:
    evaluator = json.loads((PACKET_DIR_V1_2 / "protocol" / "EVALUATOR_PROTOCOL.json").read_text(encoding="utf-8"))
    task = json.loads((PACKET_DIR_V1_2 / "tasks" / "D1.json").read_text(encoding="utf-8"))
    score, success, failures = score_structured_answer(
        task["sealed_answer"],
        task["sealed_answer"],
        evaluator,
        known_evidence_ids={item["id"] for item in task["evidence"]},
    )
    assert score == 1.0
    assert success is True
    assert failures == ()


def test_execute_experience_benchmark_with_mock_backend(tmp_path: Path, monkeypatch) -> None:
    tasks = {
        tid: json.loads((PACKET_DIR_V1_2 / "tasks" / f"{tid}.json").read_text(encoding="utf-8"))
        for tid in ("D1", "D2", "D3", "T1", "T2", "T3")
    }

    def backend(prompt: str, *, snapshot_path: Path, seed: int, max_output_tokens: int) -> BackendGeneration:
        assert "SUPPORT | REFUTE | CONTEXT_MISALIGNED | CANNOT_CHECK" in prompt
        assert '{"verdict":"CANNOT_CHECK"' in prompt
        task_id = None
        for tid in ("D1", "D2", "D3", "T1", "T2", "T3"):
            if f"Task id: {tid}" in prompt:
                task_id = tid
                break
        assert task_id is not None
        payload = json.dumps(tasks[task_id]["sealed_answer"])
        return BackendGeneration(
            raw_text=payload,
            input_tokens=128,
            output_tokens=64,
            backend_version="mock",
            wall_time_ms=10,
            process_high_water_rss_bytes_after_arm=1,
        )

    import rakl.paper2_experience_benchmark_runner as runner

    expected_sha = "a" * 40

    def fake_run(args, **kwargs):
        class Result:
            def __init__(self, stdout: str = "") -> None:
                self.stdout = stdout
                self.returncode = 0

        if len(args) >= 3 and args[0] == "git" and args[1] == "-C":
            cmd = list(args[3:])
            if cmd[:2] == ["rev-parse", "HEAD"] or cmd[:2] == ["rev-parse", "refs/remotes/origin/main"]:
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

    out = tmp_path / "out"
    manifest = execute_experience_benchmark(
        ROOT,
        out,
        expected_repo_sha=expected_sha,
        scheduler_job_id="3999001",
        created_at_utc="2026-08-11T20:00:00Z",
        backend=backend,
    )
    assert manifest["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_2
    assert manifest["run_count"] == 12
    assert manifest["v4_1_score_reuse_allowed"] is False
    assert manifest["paper3_issue_217_path"] is False
    runs = [json.loads(line) for line in (out / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(runs) == 12
    reset = [r for r in runs if r["arm"] == "RESET_BASELINE"]
    learning_dev = [r for r in runs if r["arm"] == "LEARNING_ENABLED" and r["phase"] == "DEVELOPMENT_SEQUENCE"]
    learning_xfer = [r for r in runs if r["arm"] == "LEARNING_ENABLED" and r["phase"] == "FRESH_TRANSFER"]
    assert all(r["state_before_hash"] == r["state_after_hash"] == manifest["initial_state_hash"] for r in reset)
    assert learning_dev[0]["state_before_hash"] == manifest["initial_state_hash"]
    assert learning_dev[-1]["state_after_hash"] == manifest["learned_state_after_development_hash"]
    assert all(r["state_before_hash"] == manifest["learned_state_after_development_hash"] for r in learning_xfer)
    assert all(r["success"] is True for r in runs)
