from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPERS = (
    "experiments/paper5/build_attribution_schedule.py",
    "experiments/paper5/analyze_attribution_results.py",
    "experiments/paper5/plot_attribution_results.py",
    "experiments/paper5/analyze_novelty_audit.py",
    "experiments/paper5/plot_novelty_audit.py",
    "experiments/paper5/plot_longitudinal_metrics.py",
    "experiments/paper5/analyze_process_telemetry.py",
    "experiments/paper5/plot_process_dashboard.py",
    "experiments/paper3/plot_confirmatory_metrics.py",
    "experiments/paper2/analyze_v3_experience_benchmark.py",
    "experiments/paper2/plot_v3_experience_benchmark.py",
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_helper_scripts_compile() -> None:
    for relative in HELPERS:
        source = (ROOT / relative).read_text(encoding="utf-8")
        compile(source, relative, "exec")


def test_paper5_schedule_and_analysis_round_trip(tmp_path: Path) -> None:
    tasks = {
        "packet_id": "test-packet",
        "tasks": [
            {"task_id": "T1", "stratum": "REPEATED_FAMILY"},
            {"task_id": "T2", "stratum": "CROSS_DOMAIN_TRANSFER"},
            {"task_id": "T3", "stratum": "HOSTILE_NEAR_MISS"},
        ],
    }
    task_path = tmp_path / "tasks.json"
    schedule_path = tmp_path / "schedule.json"
    result_path = tmp_path / "results.jsonl"
    analysis_dir = tmp_path / "analysis"
    task_path.write_text(json.dumps(tasks), encoding="utf-8")

    run(
        "experiments/paper5/build_attribution_schedule.py",
        "--tasks",
        str(task_path),
        "--out",
        str(schedule_path),
        "--seed",
        "17",
        "--repetitions",
        "3",
        "--allow-nonstandard-task-count",
    )
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    assert schedule["run_count"] == 36
    assert len({row["run_id"] for row in schedule["runs"]}) == 36

    arm_values = {
        "MODEL_ONLY": (False, 0.30),
        "RAKL_RESET": (False, 0.40),
        "RAKL_SHAM_MEMORY": (True, 0.55),
        "RAKL_LEARNING": (True, 0.75),
    }
    records = []
    for row in schedule["runs"]:
        success, score = arm_values[row["arm"]]
        records.append(
            {
                **row,
                "success": success,
                "score": score,
                "state_before_hash": f"before-{row['arm']}",
                "state_after_hash": f"after-{row['arm']}",
                "output_hash": f"output-{row['run_id']}",
                "validity_failures": [],
                "failure_signature": [] if success else ["TEST_FAILURE"],
                "model_input_tokens": 100,
                "model_output_tokens": 20,
                "preprocessing_model_tokens": 10,
                "tool_calls": 1,
                "retrieval_calls": 1,
                "wall_time_ms": 1000,
                "false_transfer": row["stratum"] == "HOSTILE_NEAR_MISS" and row["arm"] == "RAKL_LEARNING",
                "repeated_failure": not success,
                "memory_changed_action": row["arm"] == "RAKL_LEARNING",
            }
        )
    result_path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")

    run(
        "experiments/paper5/analyze_attribution_results.py",
        "--tasks",
        str(task_path),
        "--schedule",
        str(schedule_path),
        "--results",
        str(result_path),
        "--out-dir",
        str(analysis_dir),
        "--bootstrap-iterations",
        "100",
        "--permutation-iterations",
        "200",
    )
    summary = json.loads((analysis_dir / "summary.json").read_text(encoding="utf-8"))
    total = next(row for row in summary["contrasts"] if row["contrast"] == "TOTAL")
    assert total["mean_score_delta"] > 0
    paired = next(row for row in summary["paired_outcomes"] if row["contrast"] == "TOTAL")
    assert paired["rakl_only_success"] == 3
    assert paired["baseline_only_success"] == 0


def test_paper2_v3_analysis_enforces_chronology_and_fresh_start(tmp_path: Path) -> None:
    packet = {
        "initial_state_hash": "S0",
        "learned_state_after_development_hash": "S2",
        "development_task_ids": ["D1", "D2"],
        "transfer_task_ids": ["T1", "T2"],
    }
    packet_path = tmp_path / "packet.json"
    runs_path = tmp_path / "runs.jsonl"
    out_dir = tmp_path / "out"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    rows = []
    for task, phase in (("D1", "DEVELOPMENT_SEQUENCE"), ("D2", "DEVELOPMENT_SEQUENCE"), ("T1", "FRESH_TRANSFER"), ("T2", "FRESH_TRANSFER")):
        rows.append(
            {
                "run_id": f"reset-{task}",
                "task_id": task,
                "arm": "RESET_BASELINE",
                "phase": phase,
                "state_before_hash": "S0",
                "state_after_hash": "S0",
                "success": False,
                "score": 0.25,
                "failure_signature": ["F"],
                "model_input_tokens": 100,
                "model_output_tokens": 20,
                "preprocessing_model_tokens": 0,
                "tool_calls": 0,
                "retrieval_calls": 0,
                "wall_time_ms": 100,
            }
        )
    rows.extend(
        [
            {
                "run_id": "learn-D1", "task_id": "D1", "arm": "LEARNING_ENABLED", "phase": "DEVELOPMENT_SEQUENCE",
                "state_before_hash": "S0", "state_after_hash": "S1", "success": True, "score": 0.5,
                "failure_signature": [], "model_input_tokens": 100, "model_output_tokens": 20,
                "preprocessing_model_tokens": 10, "tool_calls": 1, "retrieval_calls": 1, "wall_time_ms": 110,
            },
            {
                "run_id": "learn-D2", "task_id": "D2", "arm": "LEARNING_ENABLED", "phase": "DEVELOPMENT_SEQUENCE",
                "state_before_hash": "S1", "state_after_hash": "S2", "success": True, "score": 0.6,
                "failure_signature": [], "model_input_tokens": 100, "model_output_tokens": 20,
                "preprocessing_model_tokens": 10, "tool_calls": 1, "retrieval_calls": 1, "wall_time_ms": 110,
            },
            {
                "run_id": "learn-T1", "task_id": "T1", "arm": "LEARNING_ENABLED", "phase": "FRESH_TRANSFER",
                "state_before_hash": "S2", "state_after_hash": "T1-local", "success": True, "score": 0.8,
                "failure_signature": [], "model_input_tokens": 100, "model_output_tokens": 20,
                "preprocessing_model_tokens": 10, "tool_calls": 1, "retrieval_calls": 1, "wall_time_ms": 110,
            },
            {
                "run_id": "learn-T2", "task_id": "T2", "arm": "LEARNING_ENABLED", "phase": "FRESH_TRANSFER",
                "state_before_hash": "S2", "state_after_hash": "T2-local", "success": True, "score": 0.9,
                "failure_signature": [], "model_input_tokens": 100, "model_output_tokens": 20,
                "preprocessing_model_tokens": 10, "tool_calls": 1, "retrieval_calls": 1, "wall_time_ms": 110,
            },
        ]
    )
    runs_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    run(
        "experiments/paper2/analyze_v3_experience_benchmark.py",
        "--packet",
        str(packet_path),
        "--runs",
        str(runs_path),
        "--out-dir",
        str(out_dir),
    )
    summary = json.loads((out_dir / "paper2_v3_summary.json").read_text(encoding="utf-8"))
    assert summary["transfer_success_delta"] == 1.0
    assert summary["grants_global_capability_claim"] is False


def test_novelty_and_process_telemetry_analysis(tmp_path: Path) -> None:
    annotations = tmp_path / "audit.jsonl"
    annotations.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "E1", "axis": "KNOWLEDGE", "internal_retained": True, "annotator_a_label": "SEMANTICALLY_NEW", "annotator_b_label": "SEMANTICALLY_NEW", "adjudicated_label": "SEMANTICALLY_NEW"}),
                json.dumps({"event_id": "E2", "axis": "KNOWLEDGE", "internal_retained": False, "annotator_a_label": "DUPLICATE_OR_EQUIVALENT", "annotator_b_label": "DUPLICATE_OR_EQUIVALENT", "adjudicated_label": "DUPLICATE_OR_EQUIVALENT"}),
            ]
        ) + "\n",
        encoding="utf-8",
    )
    novelty_dir = tmp_path / "novelty"
    run(
        "experiments/paper5/analyze_novelty_audit.py",
        "--annotations",
        str(annotations),
        "--out-dir",
        str(novelty_dir),
    )
    summary = json.loads((novelty_dir / "novelty_audit_summary.json").read_text(encoding="utf-8"))
    pooled = next(row for row in summary["metrics"] if row["axis"] == "POOLED")
    assert pooled["retained_novelty_precision"] == 1.0
    assert pooled["false_collapse_rate"] == 0.0

    telemetry = tmp_path / "telemetry.jsonl"
    telemetry.write_text(
        json.dumps(
            {
                "invocation_id": "I1",
                "process_surface": "routing",
                "task_id": "T1",
                "episode_id": "E1",
                "input_state_hash": "S0",
                "output_state_hash": "S1",
                "input_fibre_hash": "F0",
                "output_hash": "O1",
                "outcome": "SUCCESS",
                "cost": 2.0,
                "cost_policy_id": "tokens-v1",
                "residual_before": ["a", "b"],
                "residual_after": ["b"],
                "retained_novelty": {"PATH": 1},
                "retrieved_ids": ["x", "y"],
                "selected_ids": ["x"],
                "rejected_ids": ["y"],
                "verification_ids": [],
                "evidence_pointers": [],
                "timestamp": "2026-08-11T12:00:00Z",
                "authority_scope": "MEASUREMENT_ONLY",
            }
        ) + "\n",
        encoding="utf-8",
    )
    process_dir = tmp_path / "process"
    run(
        "experiments/paper5/analyze_process_telemetry.py",
        "--telemetry",
        str(telemetry),
        "--out-dir",
        str(process_dir),
    )
    process = json.loads((process_dir / "process_dashboard_summary.json").read_text(encoding="utf-8"))
    assert process["aggregates"][0]["retained_novelty_total"] == 1
    assert process["aggregates"][0]["mean_raw_residual_contraction"] == 1
