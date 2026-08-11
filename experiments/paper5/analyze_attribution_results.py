#!/usr/bin/env python3
"""Analyze the Paper 5 four-arm attribution experiment from frozen run records.

The inferential unit is the task. Repeated generations are aggregated *within*
each task/arm before cross-task inference. The default rule is mean score and
majority binary success, matching the intended 3-generation design. The final
packet must freeze these aggregation choices before evaluated outcomes are
opened.

Required result JSONL fields per run:
  run_id, task_id, repetition, arm, success, score,
  state_before_hash, state_after_hash, output_hash,
  validity_failures (list), failure_signature (list),
  model_input_tokens, model_output_tokens, preprocessing_model_tokens,
  tool_calls, retrieval_calls, wall_time_ms

Optional boolean safety/mechanism fields:
  false_transfer, repeated_failure, memory_changed_action,
  unsupported_scope_escalation, root_coordinate_surrogate_error,
  local_global_gluing_failure

Task JSON is the same file consumed by build_attribution_schedule.py and must
contain task_id + stratum for every task.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ARMS = ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING")
CONTRASTS = (
    ("ARCHITECTURE", "RAKL_RESET", "MODEL_ONLY"),
    ("EXPERIENCE", "RAKL_LEARNING", "RAKL_RESET"),
    ("CONTENT", "RAKL_LEARNING", "RAKL_SHAM_MEMORY"),
    ("TOTAL", "RAKL_LEARNING", "MODEL_ONLY"),
)
PRIMARY_CONTRASTS = ("TOTAL", "EXPERIENCE", "CONTENT")
OPTIONAL_BOOLEAN_FIELDS = (
    "false_transfer",
    "repeated_failure",
    "memory_changed_action",
    "unsupported_scope_escalation",
    "root_coordinate_surrogate_error",
    "local_global_gluing_failure",
)
RESOURCE_FIELDS = (
    "model_input_tokens",
    "model_output_tokens",
    "preprocessing_model_tokens",
    "tool_calls",
    "retrieval_calls",
    "wall_time_ms",
)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{lineno}: each line must be a JSON object")
        rows.append(row)
    return rows


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.fmean(values) if values else float("nan")


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    x = (len(values) - 1) * q
    lo = math.floor(x)
    hi = math.ceil(x)
    if lo == hi:
        return values[lo]
    w = x - lo
    return values[lo] * (1.0 - w) + values[hi] * w


def bootstrap_ci(values: list[float], rng: random.Random, iterations: int) -> tuple[float, float]:
    if not values:
        return float("nan"), float("nan")
    n = len(values)
    draws = [mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(iterations)]
    return quantile(draws, 0.025), quantile(draws, 0.975)


def paired_bootstrap_ci(diffs: list[float], rng: random.Random, iterations: int) -> tuple[float, float]:
    return bootstrap_ci(diffs, rng, iterations)


def sign_flip_pvalue(diffs: list[float], seed: int, iterations: int) -> float:
    if not diffs:
        return float("nan")
    observed = abs(mean(diffs))
    rng = random.Random(seed)
    extreme = 1
    for _ in range(iterations):
        simulated = mean(value if rng.random() < 0.5 else -value for value in diffs)
        if abs(simulated) >= observed - 1e-15:
            extreme += 1
    return extreme / (iterations + 1)


def exact_mcnemar_pvalue(rakl_only: int, baseline_only: int) -> float:
    n = rakl_only + baseline_only
    if n == 0:
        return 1.0
    k = min(rakl_only, baseline_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    finite = [(name, p) for name, p in pvalues.items() if not math.isnan(p)]
    ordered = sorted(finite, key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    m = len(ordered)
    for rank, (name, p) in enumerate(ordered):
        candidate = min(1.0, (m - rank) * p)
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def validate_input(tasks: list[dict[str, Any]], schedule: dict[str, Any], runs: list[dict[str, Any]]) -> None:
    task_ids = [str(item.get("task_id", "")) for item in tasks]
    if len(task_ids) != len(set(task_ids)) or any(not item for item in task_ids):
        raise SystemExit("task IDs must be non-empty and unique")
    expected_run_ids = {item["run_id"] for item in schedule.get("runs", [])}
    actual_run_ids = {str(item.get("run_id", "")) for item in runs}
    if len(actual_run_ids) != len(runs):
        raise SystemExit("run_id values must be unique")
    missing = expected_run_ids - actual_run_ids
    extra = actual_run_ids - expected_run_ids
    if missing or extra:
        raise SystemExit(f"result/schedule run identity mismatch: missing={len(missing)} extra={len(extra)}")
    if schedule.get("task_count") != len(tasks):
        raise SystemExit("schedule task_count does not match task packet")

    schedule_by_run = {item["run_id"]: item for item in schedule["runs"]}
    for row in runs:
        ref = schedule_by_run[row["run_id"]]
        for field in ("task_id", "repetition", "arm"):
            if row.get(field) != ref[field]:
                raise SystemExit(f"{row['run_id']}: {field} differs from frozen schedule")
        if row["arm"] not in ARMS:
            raise SystemExit(f"{row['run_id']}: unknown arm")
        score = float(row.get("score", -1))
        if not 0.0 <= score <= 1.0:
            raise SystemExit(f"{row['run_id']}: score outside [0,1]")
        for field in RESOURCE_FIELDS:
            if float(row.get(field, -1)) < 0:
                raise SystemExit(f"{row['run_id']}: missing/negative resource field {field}")
        if not row.get("state_before_hash") or not row.get("state_after_hash") or not row.get("output_hash"):
            raise SystemExit(f"{row['run_id']}: missing state/output identity")


def self_test_provenance(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Detect harness self-test records and refuse to mix them with real runs.

    Records produced by a non-model self-test adapter carry a ``harness_self_test``
    block. Such results validate the instrument; they are not evidence about RAKL.
    Silently pooling them with model runs, or presenting them under the ordinary
    claim boundary, would let synthetic numbers enter the Paper 5 record. Mixing
    is a hard error rather than a warning.
    """
    tagged = [row for row in runs if row.get("harness_self_test")]
    if not tagged:
        return None
    if len(tagged) != len(runs):
        raise SystemExit(
            f"results mix {len(tagged)} harness self-test records with {len(runs) - len(tagged)} "
            "non-self-test records; refusing to analyze a mixed set"
        )
    identities = {(row["harness_self_test"].get("adapter_id"), row["harness_self_test"].get("mode")) for row in tagged}
    if len(identities) != 1:
        raise SystemExit(f"results mix multiple self-test adapter/mode identities: {sorted(identities)}")
    adapter_id, mode = identities.pop()
    return {
        "adapter_id": adapter_id,
        "mode": mode,
        "model_invoked": False,
        "grants_scientific_authority": False,
        "interpretation": (
            "Instrument validation only. These numbers were produced by a synthetic adapter with no model "
            "in the loop and must never be reported as a Paper 5 attribution result."
        ),
    }


def aggregate_task_arm(
    tasks: list[dict[str, Any]], runs: list[dict[str, Any]], repetitions: int
) -> list[dict[str, Any]]:
    task_meta = {item["task_id"]: item for item in tasks}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in runs:
        grouped[(row["task_id"], row["arm"])].append(row)

    output: list[dict[str, Any]] = []
    for task in tasks:
        task_id = task["task_id"]
        for arm in ARMS:
            rows = sorted(grouped[(task_id, arm)], key=lambda item: int(item["repetition"]))
            if len(rows) != repetitions:
                raise SystemExit(f"{task_id}/{arm}: expected {repetitions} repetitions, found {len(rows)}")
            successes = sum(bool(item["success"]) for item in rows)
            record: dict[str, Any] = {
                "task_id": task_id,
                "stratum": task_meta[task_id]["stratum"],
                "arm": arm,
                "repetitions": repetitions,
                "success_count": successes,
                "success": successes > repetitions / 2.0,
                "score": mean(float(item["score"]) for item in rows),
                "validity_failure": any(bool(item.get("validity_failures", [])) for item in rows),
                "failure_signatures": sorted({sig for item in rows for sig in item.get("failure_signature", [])}),
            }
            for field in RESOURCE_FIELDS:
                record[field] = mean(float(item[field]) for item in rows)
            for field in OPTIONAL_BOOLEAN_FIELDS:
                present = [bool(item[field]) for item in rows if field in item and item[field] is not None]
                record[field] = any(present) if present else None
            output.append(record)
    return output


def arm_metrics(task_rows: list[dict[str, Any]], rng: random.Random, bootstrap_iterations: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arm in ARMS:
        rows = [row for row in task_rows if row["arm"] == arm]
        scores = [row["score"] for row in rows]
        successes = [float(row["success"]) for row in rows]
        score_lo, score_hi = bootstrap_ci(scores, rng, bootstrap_iterations)
        success_lo, success_hi = bootstrap_ci(successes, rng, bootstrap_iterations)
        item: dict[str, Any] = {
            "arm": arm,
            "task_count": len(rows),
            "mean_score": mean(scores),
            "score_ci_low": score_lo,
            "score_ci_high": score_hi,
            "success_rate": mean(successes),
            "success_ci_low": success_lo,
            "success_ci_high": success_hi,
            "validity_failure_rate": mean(float(row["validity_failure"]) for row in rows),
        }
        for field in RESOURCE_FIELDS:
            item[f"mean_{field}"] = mean(row[field] for row in rows)
        for field in OPTIONAL_BOOLEAN_FIELDS:
            available = [float(row[field]) for row in rows if row[field] is not None]
            item[f"{field}_rate"] = mean(available) if available else float("nan")
        out.append(item)
    return out


def contrast_metrics(
    task_rows: list[dict[str, Any]], bootstrap_seed: int, bootstrap_iterations: int, permutation_iterations: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lookup = {(row["task_id"], row["arm"]): row for row in task_rows}
    task_ids = sorted({row["task_id"] for row in task_rows})
    contrasts: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    score_pvalues: dict[str, float] = {}

    for index, (name, treatment, baseline) in enumerate(CONTRASTS):
        score_diffs = [lookup[(task, treatment)]["score"] - lookup[(task, baseline)]["score"] for task in task_ids]
        success_diffs = [float(lookup[(task, treatment)]["success"]) - float(lookup[(task, baseline)]["success"]) for task in task_ids]
        rng = random.Random(bootstrap_seed + index * 1009)
        score_lo, score_hi = paired_bootstrap_ci(score_diffs, rng, bootstrap_iterations)
        success_lo, success_hi = paired_bootstrap_ci(success_diffs, rng, bootstrap_iterations)

        both_success = rakl_only = baseline_only = both_fail = 0
        for task in task_ids:
            t = bool(lookup[(task, treatment)]["success"])
            b = bool(lookup[(task, baseline)]["success"])
            if t and b:
                both_success += 1
            elif t and not b:
                rakl_only += 1
            elif b and not t:
                baseline_only += 1
            else:
                both_fail += 1
        score_p = sign_flip_pvalue(score_diffs, bootstrap_seed + 50000 + index, permutation_iterations)
        score_pvalues[name] = score_p
        mcnemar_p = exact_mcnemar_pvalue(rakl_only, baseline_only)
        contrasts.append(
            {
                "contrast": name,
                "treatment": treatment,
                "baseline": baseline,
                "task_count": len(task_ids),
                "mean_score_delta": mean(score_diffs),
                "score_delta_ci_low": score_lo,
                "score_delta_ci_high": score_hi,
                "score_sign_flip_p": score_p,
                "success_rate_delta": mean(success_diffs),
                "success_delta_ci_low": success_lo,
                "success_delta_ci_high": success_hi,
                "mcnemar_exact_p": mcnemar_p,
            }
        )
        paired_rows.append(
            {
                "contrast": name,
                "both_success": both_success,
                "rakl_only_success": rakl_only,
                "baseline_only_success": baseline_only,
                "both_fail": both_fail,
                "mcnemar_exact_p": mcnemar_p,
            }
        )

    adjusted = holm_adjust({name: score_pvalues[name] for name in PRIMARY_CONTRASTS})
    for row in contrasts:
        row["score_holm_p"] = adjusted.get(row["contrast"], float("nan"))
    return contrasts, paired_rows


def stratum_metrics(task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strata = sorted({row["stratum"] for row in task_rows})
    output: list[dict[str, Any]] = []
    for stratum in strata:
        for arm in ARMS:
            rows = [row for row in task_rows if row["stratum"] == stratum and row["arm"] == arm]
            item: dict[str, Any] = {
                "stratum": stratum,
                "arm": arm,
                "task_count": len(rows),
                "mean_score": mean(row["score"] for row in rows),
                "success_rate": mean(float(row["success"]) for row in rows),
                "validity_failure_rate": mean(float(row["validity_failure"]) for row in rows),
            }
            for field in OPTIONAL_BOOLEAN_FIELDS:
                available = [float(row[field]) for row in rows if row[field] is not None]
                item[f"{field}_rate"] = mean(available) if available else float("nan")
            output.append(item)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-seed", type=int, default=20260811)
    parser.add_argument("--bootstrap-iterations", type=int, default=20000)
    parser.add_argument("--permutation-iterations", type=int, default=100000)
    args = parser.parse_args()

    task_payload = load_json(args.tasks)
    tasks = task_payload["tasks"]
    schedule = load_json(args.schedule)
    runs = load_jsonl(args.results)
    validate_input(tasks, schedule, runs)

    repetitions = int(schedule["repetitions"])
    task_rows = aggregate_task_arm(tasks, runs, repetitions)
    rng = random.Random(args.bootstrap_seed)
    arms = arm_metrics(task_rows, rng, args.bootstrap_iterations)
    contrasts, paired = contrast_metrics(
        task_rows,
        args.bootstrap_seed,
        args.bootstrap_iterations,
        args.permutation_iterations,
    )
    strata = stratum_metrics(task_rows)
    self_test = self_test_provenance(runs)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "task_level.csv", task_rows)
    write_csv(args.out_dir / "arm_metrics.csv", arms)
    write_csv(args.out_dir / "contrasts.csv", contrasts)
    write_csv(args.out_dir / "paired_outcomes.csv", paired)
    write_csv(args.out_dir / "stratum_metrics.csv", strata)

    summary = {
        "schema_version": "paper5-attribution-analysis-v1",
        "task_file_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
        "schedule_file_sha256": hashlib.sha256(args.schedule.read_bytes()).hexdigest(),
        "results_file_sha256": hashlib.sha256(args.results.read_bytes()).hexdigest(),
        "task_count": len(tasks),
        "repetitions": repetitions,
        "aggregation": {"score": "MEAN_WITHIN_TASK_ARM", "success": "STRICT_MAJORITY_WITHIN_TASK_ARM"},
        "bootstrap_seed": args.bootstrap_seed,
        "bootstrap_iterations": args.bootstrap_iterations,
        "permutation_iterations": args.permutation_iterations,
        "arm_metrics": arms,
        "contrasts": contrasts,
        "paired_outcomes": paired,
        "stratum_metrics": strata,
        "harness_self_test": self_test,
        "grants_scientific_authority": False,
        "claim_boundary": (
            "HARNESS SELF-TEST ONLY. Synthetic adapter, no model invoked. These numbers validate the measuring "
            "instrument and are not evidence about RAKL; they must not be reported as a Paper 5 attribution result."
            if self_test
            else "Descriptive/paired benchmark analysis only. Strong claims additionally require the frozen evaluator, "
            "state/resource/sham bindings, integrity gates, and any required protected assurance."
        ),
    }
    summary["analysis_core_sha256"] = canonical_sha256(summary)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out_dir / "summary.json")
    print(summary["analysis_core_sha256"])


if __name__ == "__main__":
    main()
