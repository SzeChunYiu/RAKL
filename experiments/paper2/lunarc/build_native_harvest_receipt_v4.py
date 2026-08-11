#!/usr/bin/env python3
"""Validate LUNARC scheduler/result evidence and build the V4 native harvest."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

import jsonschema


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sacct_root_row(payload: object, job_id: str) -> tuple[dict[str, object] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        return None, ["sacct_jobs_missing"]
    rows = [row for row in payload["jobs"] if isinstance(row, dict) and str(row.get("job_id")) == job_id]
    if len(rows) != 1:
        return None, ["scheduler_root_row_not_unique"]
    row = rows[0]
    state = row.get("state")
    current = state.get("current") if isinstance(state, dict) else None
    if current != ["COMPLETED"]:
        failures.append("scheduler_job_not_completed")
    exit_code = row.get("exit_code")
    status = exit_code.get("status") if isinstance(exit_code, dict) else None
    return_code = exit_code.get("return_code") if isinstance(exit_code, dict) else None
    if status != ["SUCCESS"]:
        failures.append("scheduler_exit_status_not_success")
    if not isinstance(return_code, dict) or return_code.get("set") is not True or return_code.get("number") != 0:
        failures.append("scheduler_return_code_not_zero")
    elapsed = row.get("time", {}).get("elapsed") if isinstance(row.get("time"), dict) else None
    if not isinstance(elapsed, int) or elapsed < 0:
        failures.append("scheduler_elapsed_invalid")
    return row, failures


def build(args: argparse.Namespace) -> int:
    paths = {
        "result": args.run_dir / "result_receipt.json",
        "task_seed": args.run_dir / "task_seed_receipt.json",
        "pre": args.attestation_dir / "model_snapshot_pre.json",
        "post": args.attestation_dir / "model_snapshot_post.json",
    }
    failures: list[str] = []
    try:
        sacct = json.loads(args.sacct.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        sacct = {}
        failures.append("sacct_json_invalid")
    scheduler_row, scheduler_failures = validate_sacct_root_row(sacct, args.job_id)
    failures.extend(scheduler_failures)
    values: dict[str, object | None] = {}
    for name, path in paths.items():
        if not path.is_file():
            failures.append(f"{name}_receipt_missing")
            values[name] = None
            continue
        try:
            values[name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(f"{name}_receipt_invalid_json")
            values[name] = None

    checker = jsonschema.FormatChecker()
    schema_pairs = (
        ("result", args.result_schema),
        ("task_seed", args.task_seed_schema),
        ("pre", args.attestation_schema),
        ("post", args.attestation_schema),
    )
    for name, schema_path in schema_pairs:
        value = values.get(name)
        if value is None:
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema, format_checker=checker).iter_errors(value))
        if errors:
            failures.append(f"{name}_schema_invalid")

    result = values.get("result")
    task_seed = values.get("task_seed")
    pre = values.get("pre")
    post = values.get("post")
    if isinstance(task_seed, dict):
        if task_seed.get("task_id") != "PENDULUM_SEALED_KNOWN_ANSWER_001" or task_seed.get("seed") != 17:
            failures.append("task_seed_identity_mismatch")
        if task_seed.get("evaluated_task_seed_unit_count") != 1 or task_seed.get("arm_record_count") != 2:
            failures.append("task_seed_count_mismatch")
    if isinstance(result, dict) and isinstance(task_seed, dict):
        if task_seed.get("packet_parent_sha") != result.get("subject_sha"):
            failures.append("packet_parent_sha_mismatch")
        if task_seed.get("execution_checkout") != result.get("execution_checkout"):
            failures.append("execution_checkout_mismatch")
    if isinstance(pre, dict) and isinstance(post, dict):
        if pre.get("snapshot_canonical_sha256") != post.get("snapshot_canonical_sha256"):
            failures.append("snapshot_changed_across_inference")
        if pre.get("execution_checkout") != post.get("execution_checkout"):
            failures.append("attested_checkout_changed_across_inference")

    success = not failures
    receipt = {
        "schema_version": "paper2-pendulum-native-harvest-receipt-v4",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "slurm_job_id": args.job_id,
        "verdict": "HARVEST_TASK_SEED_PASS_NONCONFIRMATORY" if success else "HARVEST_CANNOT_CHECK",
        "failures": list(dict.fromkeys(failures)),
        "scheduler_evidence": {
            "path": str(args.sacct),
            "sha256": _sha256(args.sacct),
            "root_row": scheduler_row,
        },
        "packet_parent_sha": result.get("subject_sha") if isinstance(result, dict) else None,
        "execution_checkout": result.get("execution_checkout") if isinstance(result, dict) else None,
        "task_id": "PENDULUM_SEALED_KNOWN_ANSWER_001",
        "seed": 17,
        "result_receipt": {
            "path": str(paths["result"]),
            "sha256": _sha256(paths["result"]) if paths["result"].is_file() else None,
        },
        "task_seed_receipt": {
            "path": str(paths["task_seed"]),
            "sha256": _sha256(paths["task_seed"]) if paths["task_seed"].is_file() else None,
        },
        "snapshot_attestations": {
            "pre_path": str(paths["pre"]),
            "pre_sha256": _sha256(paths["pre"]) if paths["pre"].is_file() else None,
            "post_path": str(paths["post"]),
            "post_sha256": _sha256(paths["post"]) if paths["post"].is_file() else None,
        },
        "evaluated_task_seed_unit_count": 1 if success else 0,
        "arm_record_count": 2 if success else 0,
        "claim_boundary": "At most one non-confirmatory known-answer task/seed unit; no matched architecture-by-evidence-access or general superiority authority.",
    }
    harvest_schema = json.loads(args.harvest_schema.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(harvest_schema, format_checker=checker).validate(receipt)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(receipt["verdict"])
    return 0 if success else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--attestation-dir", type=Path, required=True)
    parser.add_argument("--sacct", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    parser.add_argument("--task-seed-schema", type=Path, required=True)
    parser.add_argument("--attestation-schema", type=Path, required=True)
    parser.add_argument("--harvest-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return build(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
