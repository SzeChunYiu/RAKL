from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_analyze_and_plot_helpers_round_trip(tmp_path: Path) -> None:
    packet = {
        "initial_state_hash": "S0",
        "learned_state_after_development_hash": "S2",
        "development_task_ids": ["D1", "D2"],
        "transfer_task_ids": ["T1", "T2"],
    }
    runs = []
    # RESET development
    for task in ("D1", "D2"):
        runs.append(
            {
                "run_id": f"reset-{task}",
                "task_id": task,
                "arm": "RESET_BASELINE",
                "phase": "DEVELOPMENT_SEQUENCE",
                "state_before_hash": "S0",
                "state_after_hash": "S0",
                "success": False,
                "score": 0.2,
                "failure_signature": ["repeat"],
                "model_input_tokens": 10,
                "model_output_tokens": 5,
                "preprocessing_model_tokens": 1,
                "tool_calls": 0,
                "retrieval_calls": 0,
                "wall_time_ms": 100,
            }
        )
    # LEARNING development chronology S0->S1->S2
    runs.append(
        {
            "run_id": "learn-D1",
            "task_id": "D1",
            "arm": "LEARNING_ENABLED",
            "phase": "DEVELOPMENT_SEQUENCE",
            "state_before_hash": "S0",
            "state_after_hash": "S1",
            "success": False,
            "score": 0.3,
            "failure_signature": ["repeat"],
            "model_input_tokens": 10,
            "model_output_tokens": 5,
            "preprocessing_model_tokens": 1,
            "tool_calls": 0,
            "retrieval_calls": 0,
            "wall_time_ms": 100,
        }
    )
    runs.append(
        {
            "run_id": "learn-D2",
            "task_id": "D2",
            "arm": "LEARNING_ENABLED",
            "phase": "DEVELOPMENT_SEQUENCE",
            "state_before_hash": "S1",
            "state_after_hash": "S2",
            "success": True,
            "score": 0.8,
            "failure_signature": [],
            "model_input_tokens": 10,
            "model_output_tokens": 5,
            "preprocessing_model_tokens": 1,
            "tool_calls": 0,
            "retrieval_calls": 0,
            "wall_time_ms": 100,
        }
    )
    for task, success, score in (("T1", True, 0.9), ("T2", True, 0.8)):
        runs.append(
            {
                "run_id": f"reset-{task}",
                "task_id": task,
                "arm": "RESET_BASELINE",
                "phase": "FRESH_TRANSFER",
                "state_before_hash": "S0",
                "state_after_hash": "S0",
                "success": False,
                "score": 0.25,
                "failure_signature": ["transfer"],
                "model_input_tokens": 10,
                "model_output_tokens": 5,
                "preprocessing_model_tokens": 1,
                "tool_calls": 0,
                "retrieval_calls": 0,
                "wall_time_ms": 100,
            }
        )
        runs.append(
            {
                "run_id": f"learn-{task}",
                "task_id": task,
                "arm": "LEARNING_ENABLED",
                "phase": "FRESH_TRANSFER",
                "state_before_hash": "S2",
                "state_after_hash": f"{task}-after",
                "success": success,
                "score": score,
                "failure_signature": [],
                "model_input_tokens": 10,
                "model_output_tokens": 5,
                "preprocessing_model_tokens": 1,
                "tool_calls": 0,
                "retrieval_calls": 0,
                "wall_time_ms": 100,
            }
        )

    packet_path = tmp_path / "packet.json"
    runs_path = tmp_path / "runs.jsonl"
    analysis_dir = tmp_path / "analysis"
    figures_dir = tmp_path / "figures"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    runs_path.write_text("\n".join(json.dumps(row) for row in runs) + "\n", encoding="utf-8")

    run(
        "experiments/paper2/analyze_v3_experience_benchmark.py",
        "--packet",
        str(packet_path),
        "--runs",
        str(runs_path),
        "--out-dir",
        str(analysis_dir),
    )
    summary = json.loads((analysis_dir / "paper2_v3_summary.json").read_text(encoding="utf-8"))
    assert summary["grants_global_capability_claim"] is False
    assert summary["transfer_success_delta"] == pytest.approx(1.0)
    assert (analysis_dir / "paper2_v3_metrics.csv").is_file()

    pytest.importorskip("matplotlib")
    run(
        "experiments/paper2/plot_v3_experience_benchmark.py",
        "--metrics",
        str(analysis_dir / "paper2_v3_metrics.csv"),
        "--out-dir",
        str(figures_dir),
    )
    assert (figures_dir / "paper2_v3_experience_benchmark.pdf").is_file()
    assert (figures_dir / "paper2_v3_fresh_transfer_resources.pdf").is_file()


def test_refuse_v4_1_as_experience_benchmark(tmp_path: Path) -> None:
    harvest = {
        "schema_version": "paper2-pendulum-microtrial-harvest-v4-1",
        "experiment_id": "PENDULUM_MATCHED_SAME_MODEL_MICROTRIAL_001_EXECUTION_V4_1_OUTPUT_NORMALIZATION",
        "verdict": "HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY",
        "records": [
            {"blind_id": "BLIND_A", "condition": "RAKL_CONTEXT"},
            {"blind_id": "BLIND_B", "condition": "DIRECT"},
        ],
    }
    path = tmp_path / "harvest-3476520.json"
    out = tmp_path / "compat.json"
    path.write_text(json.dumps(harvest), encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "experiments/paper2/refuse_v4_1_as_experience_benchmark.py",
            str(path),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["verdict"] == "CANNOT_CHECK"
    assert receipt["grants_experience_benchmark_authority"] is False
    assert receipt["inspections"][0]["blockers"]
