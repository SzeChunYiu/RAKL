from __future__ import annotations

import json
from pathlib import Path

from rakl.paper2_experience_benchmark_runner import (
    PROTOCOL_SUBJECT_HASH,
    execute_experience_benchmark,
    score_structured_answer,
)
from rakl.paper2_pendulum_microtrial import BackendGeneration

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research" / "paper2_experience_benchmark_v1"


def test_protocol_subject_hash_binding() -> None:
    packet = json.loads((PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    contract = json.loads((PACKET_DIR / "BATCH_CONTRACT_V1.json").read_text(encoding="utf-8"))
    assert packet["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH
    assert contract["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH
    assert contract["v4_1_score_reuse_allowed"] is False
    assert contract["paper3_issue_217_path"] is False
    assert {3476520, 3476521, 3476524}.issubset(set(contract["v4_1_jobs_not_evidence"]))


def test_batch_contract_bindings_match_bytes() -> None:
    import hashlib

    contract = json.loads((PACKET_DIR / "BATCH_CONTRACT_V1.json").read_text(encoding="utf-8"))
    for binding in contract["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["role"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == binding["sha256"], binding["role"]


def test_score_structured_answer_exact() -> None:
    evaluator = json.loads((PACKET_DIR / "protocol" / "EVALUATOR_PROTOCOL.json").read_text(encoding="utf-8"))
    task = json.loads((PACKET_DIR / "tasks" / "D1.json").read_text(encoding="utf-8"))
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
    # Avoid requiring a real git clean origin/main by stubbing checkout probes inside execute.
    # Use a fake backend that returns sealed answers so chronology/wiring can be checked.
    tasks = {
        tid: json.loads((PACKET_DIR / "tasks" / f"{tid}.json").read_text(encoding="utf-8"))
        for tid in ("D1", "D2", "D3", "T1", "T2", "T3")
    }

    def backend(prompt: str, *, snapshot_path: Path, seed: int, max_output_tokens: int) -> BackendGeneration:
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

    # Patch git checks by running from a temporary clone-like layout is heavy; instead
    # monkeypatch subprocess.run used by the runner for git.
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

    # Snapshot path must exist as a directory for the preflight check.
    snap = tmp_path / "snap"
    snap.mkdir()
    # Rewrite model config snapshot via monkeypatch of load path: easiest is to
    # temporarily point MODEL_CONFIG snapshot_path using a patched load_frozen_protocol.
    original_load = runner.load_frozen_protocol

    def patched_load(repo: Path):
        bundle = original_load(repo)
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
    assert manifest["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH
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
