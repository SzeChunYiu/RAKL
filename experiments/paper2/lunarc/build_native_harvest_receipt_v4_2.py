#!/usr/bin/env python3
"""Build a fail-closed V4.2 native harvest receipt from exact LUNARC evidence."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

import jsonschema


POLICY_ID = "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
PROTOCOL_ID = "PENDULUM_MATCHED_SAME_MODEL_MICROTRIAL_001_EXECUTION_V4_2_PROMPT_INTERFACE"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sacct_root_row(payload: object, job_id: str) -> tuple[dict[str, object] | None, list[str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        return None, ["sacct_jobs_missing"]
    rows = [row for row in payload["jobs"] if isinstance(row, dict) and str(row.get("job_id")) == job_id]
    if len(rows) != 1:
        return None, ["scheduler_root_row_not_unique"]
    row = rows[0]
    failures: list[str] = []
    state = row.get("state")
    if not isinstance(state, dict) or state.get("current") != ["COMPLETED"]:
        failures.append("scheduler_job_not_completed")
    exit_code = row.get("exit_code")
    if not isinstance(exit_code, dict) or exit_code.get("status") != ["SUCCESS"]:
        failures.append("scheduler_exit_status_not_success")
    return_code = exit_code.get("return_code") if isinstance(exit_code, dict) else None
    if not isinstance(return_code, dict) or return_code.get("set") is not True or return_code.get("number") != 0:
        failures.append("scheduler_return_code_not_zero")
    elapsed = row.get("time", {}).get("elapsed") if isinstance(row.get("time"), dict) else None
    if not isinstance(elapsed, int) or elapsed < 0:
        failures.append("scheduler_elapsed_invalid")
    return row, failures


def _load(path: Path, name: str, failures: list[str]) -> object | None:
    if not path.is_file():
        failures.append(f"{name}_receipt_missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        failures.append(f"{name}_receipt_invalid_json")
        return None


def build(args: argparse.Namespace) -> int:
    paths = {
        "result": args.run_dir / "result_receipt.json",
        "task_seed": args.run_dir / "task_seed_receipt.json",
        "run_manifest": args.run_dir / "run_manifest.json",
        "preflight": args.attestation_dir / "allocated_preflight.json",
        "pre": args.attestation_dir / "model_snapshot_pre.json",
        "post": args.attestation_dir / "model_snapshot_post.json",
        "submission": args.submission,
    }
    failures: list[str] = []
    try:
        sacct = json.loads(args.sacct.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        sacct = {}
        failures.append("sacct_json_invalid")
    scheduler_row, scheduler_failures = validate_sacct_root_row(sacct, args.job_id)
    failures.extend(scheduler_failures)
    values = {name: _load(path, name, failures) for name, path in paths.items()}

    checker = jsonschema.FormatChecker()
    for name, schema_path in (
        ("result", args.result_schema),
        ("task_seed", args.task_seed_schema),
        ("pre", args.attestation_schema),
        ("post", args.attestation_schema),
        ("submission", args.submission_schema),
    ):
        value = values.get(name)
        if value is None:
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if list(jsonschema.Draft202012Validator(schema, format_checker=checker).iter_errors(value)):
            failures.append(f"{name}_schema_invalid")

    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        packet = {}
        failures.append("execution_packet_invalid")
    packet_sha = _sha256(args.packet) if args.packet.is_file() else None
    result = values.get("result")
    task_seed = values.get("task_seed")
    pre = values.get("pre")
    post = values.get("post")
    submission = values.get("submission")
    run_manifest = values.get("run_manifest")
    preflight = values.get("preflight")

    if packet.get("protocol_id") != PROTOCOL_ID or packet.get("output_normalization_policy_id") != POLICY_ID:
        failures.append("packet_v4_2_policy_or_protocol_mismatch")
    if packet.get("chronology_class") != "ADAPTIVE_PROMPT_INTERFACE_REPLAY_FRESH_ONLY_TO_V4_2_OUTPUTS":
        failures.append("packet_adaptive_chronology_class_mismatch")
    if packet.get("parent_v4_1_results_opened_before_v4_2_freeze") is not True:
        failures.append("packet_parent_result_access_disclosure_missing")
    if packet.get("evaluated_results_opened_before_freeze_scope") != "V4_2_OUTPUTS_ONLY_PARENT_V4_1_KNOWN":
        failures.append("packet_result_access_scope_mismatch")
    if packet.get("v4_1_negative_history", {}).get("reinterpretation_permitted") is not False:
        failures.append("v4_reinterpretation_prohibition_missing")
    if isinstance(preflight, dict):
        if preflight.get("verdict") != "PASS" or preflight.get("evaluated_result_record_count") != 0:
            failures.append("allocated_preflight_not_pass")
        if preflight.get("protocol_id") != PROTOCOL_ID:
            failures.append("allocated_preflight_protocol_mismatch")
    if isinstance(task_seed, dict):
        if task_seed.get("task_id") != "PENDULUM_SEALED_KNOWN_ANSWER_001" or task_seed.get("seed") != 17:
            failures.append("task_seed_identity_mismatch")
        if task_seed.get("evaluated_task_seed_unit_count") != 1 or task_seed.get("arm_record_count") != 2:
            failures.append("task_seed_count_mismatch")
        normalization = task_seed.get("output_normalization")
        if not isinstance(normalization, dict) or normalization.get("policy_id") != POLICY_ID:
            failures.append("task_seed_normalization_policy_mismatch")
        if not isinstance(normalization, dict) or normalization.get("v4_reinterpretation_permitted") is not False:
            failures.append("task_seed_v4_reinterpretation_state_invalid")
    if isinstance(result, dict):
        if result.get("experiment_id") != PROTOCOL_ID or result.get("packet_sha256") != packet_sha:
            failures.append("result_packet_or_protocol_mismatch")
    if isinstance(result, dict) and isinstance(task_seed, dict):
        if task_seed.get("packet_parent_sha") != result.get("subject_sha"):
            failures.append("packet_parent_sha_mismatch")
        if task_seed.get("execution_checkout") != result.get("execution_checkout"):
            failures.append("execution_checkout_mismatch")
        if task_seed.get("result_receipt_sha256") != _sha256(paths["result"]):
            failures.append("task_seed_result_hash_mismatch")
        if task_seed.get("run_manifest_sha256") != _sha256(paths["run_manifest"]):
            failures.append("task_seed_run_manifest_hash_mismatch")
        result_records = result.get("records")
        task_records = task_seed.get("records")
        if not isinstance(result_records, list) or not isinstance(task_records, list):
            failures.append("task_seed_records_missing")
        else:
            result_by_condition = {
                row.get("condition"): row for row in result_records if isinstance(row, dict)
            }
            task_by_condition = {
                row.get("condition"): row for row in task_records if isinstance(row, dict)
            }
            if set(result_by_condition) != {"DIRECT_CORPUS", "RAKL_CONTEXT"} or set(task_by_condition) != set(result_by_condition):
                failures.append("task_seed_arm_identity_mismatch")
            else:
                observed_parse = 0
                observed_scorable = 0
                for condition, result_row in result_by_condition.items():
                    score = result_row.get("score")
                    task_row = task_by_condition[condition]
                    if not isinstance(score, dict) or task_row.get("score") != score:
                        failures.append(f"task_seed_score_mismatch:{condition}")
                        continue
                    if task_row.get("resource_receipt") != result_row.get("resource_receipt"):
                        failures.append(f"task_seed_resource_mismatch:{condition}")
                    observed_parse += int(score.get("parse_valid") is True)
                    observed_scorable += int(isinstance(score.get("score"), dict))
                if task_seed.get("parse_valid_arm_count") != observed_parse:
                    failures.append("task_seed_parse_valid_count_mismatch")
                if task_seed.get("scorable_arm_count") != observed_scorable:
                    failures.append("task_seed_scorable_count_mismatch")
    if isinstance(run_manifest, dict) and isinstance(result, dict):
        if run_manifest.get("packet_file_sha256") != packet_sha:
            failures.append("run_manifest_packet_hash_mismatch")
        if _sha256(paths["run_manifest"]) != result.get("run_manifest_sha256"):
            failures.append("result_run_manifest_hash_mismatch")
        if run_manifest.get("execution_checkout") != result.get("execution_checkout"):
            failures.append("run_manifest_execution_checkout_mismatch")
    if isinstance(pre, dict) and isinstance(post, dict):
        if pre.get("snapshot_canonical_sha256") != post.get("snapshot_canonical_sha256"):
            failures.append("snapshot_changed_across_inference")
        if pre.get("execution_checkout") != post.get("execution_checkout"):
            failures.append("attested_checkout_changed_across_inference")
        if paths["result"].is_file() and post.get("result_receipt_sha256") != _sha256(paths["result"]):
            failures.append("post_attestation_result_hash_mismatch")
    if isinstance(submission, dict):
        if submission.get("slurm_job_id") != args.job_id:
            failures.append("submission_job_id_mismatch")
        if submission.get("execution_packet_sha256") != packet_sha:
            failures.append("submission_packet_hash_mismatch")
        if submission.get("output_normalization_policy_id") != POLICY_ID:
            failures.append("submission_normalization_policy_mismatch")
        if submission.get("packet_parent_sha") != packet.get("subject_sha"):
            failures.append("submission_packet_parent_mismatch")
        if isinstance(result, dict):
            checkout = result.get("execution_checkout")
            if not isinstance(checkout, dict) or submission.get("expected_repo_sha") != checkout.get("head_sha"):
                failures.append("submission_execution_head_mismatch")

    parse_valid_count = task_seed.get("parse_valid_arm_count", 0) if isinstance(task_seed, dict) else 0
    scorable_count = task_seed.get("scorable_arm_count", 0) if isinstance(task_seed, dict) else 0
    if not isinstance(parse_valid_count, int) or not 0 <= parse_valid_count <= 2:
        failures.append("parse_valid_arm_count_invalid")
        parse_valid_count = 0
    if not isinstance(scorable_count, int) or not 0 <= scorable_count <= 2:
        failures.append("scorable_arm_count_invalid")
        scorable_count = 0

    failures = list(dict.fromkeys(failures))
    success = not failures
    receipt = {
        "schema_version": "paper2-pendulum-native-harvest-receipt-v4.2",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "slurm_job_id": args.job_id,
        "verdict": "HARVEST_V4_2_TASK_SEED_PASS_NONCONFIRMATORY" if success else "HARVEST_V4_2_CANNOT_CHECK",
        "failures": failures,
        "scheduler_evidence": {
            "path": str(args.sacct),
            "sha256": _sha256(args.sacct) if args.sacct.is_file() else None,
            "root_row": scheduler_row,
        },
        "execution_packet": {"path": str(args.packet), "sha256": packet_sha},
        "output_normalization_policy_id": POLICY_ID,
        "v4_reinterpretation_permitted": False,
        "packet_parent_sha": result.get("subject_sha") if isinstance(result, dict) else None,
        "execution_checkout": result.get("execution_checkout") if isinstance(result, dict) else None,
        "task_id": "PENDULUM_SEALED_KNOWN_ANSWER_001",
        "seed": 17,
        "submission_receipt": {"path": str(paths["submission"]), "sha256": _sha256(paths["submission"]) if paths["submission"].is_file() else None},
        "allocated_preflight_receipt": {"path": str(paths["preflight"]), "sha256": _sha256(paths["preflight"]) if paths["preflight"].is_file() else None},
        "run_manifest": {"path": str(paths["run_manifest"]), "sha256": _sha256(paths["run_manifest"]) if paths["run_manifest"].is_file() else None},
        "result_receipt": {"path": str(paths["result"]), "sha256": _sha256(paths["result"]) if paths["result"].is_file() else None},
        "task_seed_receipt": {"path": str(paths["task_seed"]), "sha256": _sha256(paths["task_seed"]) if paths["task_seed"].is_file() else None},
        "snapshot_attestations": {
            "pre_path": str(paths["pre"]),
            "pre_sha256": _sha256(paths["pre"]) if paths["pre"].is_file() else None,
            "post_path": str(paths["post"]),
            "post_sha256": _sha256(paths["post"]) if paths["post"].is_file() else None,
        },
        "evaluated_task_seed_unit_count": 1 if success else 0,
        "arm_record_count": 2 if success else 0,
        "parse_valid_arm_count": parse_valid_count if success else 0,
        "scorable_arm_count": scorable_count if success else 0,
        "claim_boundary": (
            "At most one fresh non-confirmatory V4.2 task/seed unit. A pass is receipt-chain "
            "authority only, does not reinterpret V4, and does not establish an arm comparison."
        ),
    }
    schema = json.loads(args.harvest_schema.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=checker).validate(receipt)
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
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--sacct", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    parser.add_argument("--task-seed-schema", type=Path, required=True)
    parser.add_argument("--attestation-schema", type=Path, required=True)
    parser.add_argument("--submission-schema", type=Path, required=True)
    parser.add_argument("--harvest-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return build(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
