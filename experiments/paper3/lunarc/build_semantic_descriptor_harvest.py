#!/usr/bin/env python3
"""Build native scheduler-bound harvest receipts without running inference."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from semantic_descriptor_common import (
    atomic_write_json,
    file_sha256,
    inspect_model_files,
    load_json,
    root_sacct_row,
    utc_now,
    validate_schema,
)


def build_harvest(
    *,
    phase: str,
    job_id: str,
    repo: Path,
    contract_path: Path,
    submission_path: Path,
    execution_path: Path,
    sacct_path: Path,
    output: Path,
) -> dict[str, Any]:
    contract = load_json(contract_path)
    submission = load_json(submission_path)
    sacct = load_json(sacct_path)
    validate_schema(
        submission, repo / "schemas/paper3-semantic-lunarc-submission-v1.schema.json"
    )
    failures: list[str] = []
    row, sacct_failures = root_sacct_row(sacct, job_id)
    failures.extend(sacct_failures)
    if submission.get("slurm_job_id") != job_id:
        failures.append("submission_job_id_mismatch")
    expected_phase = "MODEL_STAGE" if phase == "model-stage" else "DESCRIPTOR"
    if submission.get("phase") != expected_phase:
        failures.append("submission_phase_mismatch")

    execution_sha: str | None = None
    descriptor_sha: str | None = None
    descriptor_status: str | None = None
    descriptor_count = 0
    try:
        execution = load_json(execution_path)
        execution_schema = (
            "paper3-semantic-model-stage-execution-v1.schema.json"
            if phase == "model-stage"
            else "paper3-semantic-descriptor-execution-v1.schema.json"
        )
        validate_schema(execution, repo / "schemas" / execution_schema)
        execution_sha = file_sha256(execution_path)
        if execution.get("slurm_job_id") != job_id:
            failures.append("execution_job_id_mismatch")
        if execution.get("expected_repo_sha") != submission.get("expected_repo_sha"):
            failures.append("execution_checkout_sha_mismatch")
        if execution.get("contract_sha256") != submission.get("contract_sha256"):
            failures.append("execution_contract_hash_mismatch")
        expected_verdict = (
            "STAGING_PASS_ATOMICALLY_PROMOTED"
            if phase == "model-stage"
            else "DESCRIPTOR_EXECUTION_PASS"
        )
        if execution.get("verdict") != expected_verdict:
            failures.append("execution_verdict_not_passed")
        if execution.get("failures") != []:
            failures.append("execution_has_failures")
        if phase == "model-stage":
            observed, asset_failures = inspect_model_files(
                Path(contract["fs9"]["model_dir"]),
                contract["model"]["required_files"],
            )
            failures.extend(asset_failures)
            if observed != execution.get("observed_model_files"):
                failures.append("promoted_model_differs_from_stage_receipt")
        else:
            descriptor_path = Path(str(execution.get("descriptor_path", "")))
            if not descriptor_path.is_file():
                failures.append("descriptor_receipt_missing")
            else:
                descriptor = load_json(descriptor_path)
                validate_schema(
                    descriptor,
                    repo
                    / "schemas/paper3-content-bound-semantic-descriptor.schema.json",
                )
                descriptor_sha = file_sha256(descriptor_path)
                descriptor_status = descriptor.get("status")
                descriptor_count = len(descriptor.get("descriptors", []))
                if descriptor_sha != execution.get("descriptor_sha256"):
                    failures.append("descriptor_hash_mismatch")
                if descriptor_status != "READY" or descriptor_count == 0:
                    failures.append("descriptor_not_ready")
                # This validation recomputes only frozen text hashes and score
                # transforms; it does not invoke the model.
                from rakl.paper3_strong_control import (
                    validate_semantic_descriptor_receipt,
                )

                source = load_json(repo / contract["source_set"]["path"])
                protocol = load_json(repo / contract["protocol"]["path"])
                failures.extend(
                    validate_semantic_descriptor_receipt(source, protocol, descriptor)
                )
    except Exception as exc:
        failures.append(f"execution_or_result_invalid:{type(exc).__name__}")

    failures = list(dict.fromkeys(failures))
    if phase == "model-stage":
        verdict = (
            "HARVEST_MODEL_STAGE_PASS"
            if not failures
            else "HARVEST_MODEL_STAGE_CANNOT_CHECK"
        )
    else:
        verdict = (
            "HARVEST_DESCRIPTOR_READY"
            if not failures
            else "HARVEST_DESCRIPTOR_CANNOT_CHECK"
        )
    receipt = {
        "schema_version": "paper3-semantic-lunarc-harvest-v1",
        "created_at_utc": utc_now(),
        "phase": expected_phase,
        "verdict": verdict,
        "slurm_job_id": job_id,
        "slurm_state": None if row is None else row.get("state", {}).get("current"),
        "slurm_exit_status": None
        if row is None
        else row.get("exit_code", {}).get("status"),
        "slurm_exit_code": None
        if row is None
        else row.get("exit_code", {}).get("return_code", {}).get("number"),
        "expected_repo_sha": submission.get("expected_repo_sha"),
        "frozen_parent_sha": submission.get("frozen_parent_sha"),
        "contract_sha256": submission.get("contract_sha256"),
        "submission_receipt_sha256": file_sha256(submission_path),
        "execution_receipt_sha256": execution_sha,
        "descriptor_receipt_sha256": descriptor_sha,
        "descriptor_status": descriptor_status,
        "descriptor_record_count": descriptor_count,
        "failures": failures,
        "training_authorized": False,
        "claim_boundary": (
            "Model-stage harvest only; no model execution or scientific result."
            if phase == "model-stage"
            else "Label-blind semantic descriptor harvest only; not a structural-signal, "
            "training-efficiency, inference-efficiency, break-even, independent-review "
            "or peer-review result."
        ),
    }
    validate_schema(
        receipt, repo / "schemas/paper3-semantic-lunarc-harvest-v1.schema.json"
    )
    atomic_write_json(output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("model-stage", "descriptor"), required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--sacct", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_harvest(
        phase=args.phase,
        job_id=args.job_id,
        repo=args.repo.resolve(),
        contract_path=args.contract.resolve(),
        submission_path=args.submission.resolve(),
        execution_path=args.execution.resolve(),
        sacct_path=args.sacct.resolve(),
        output=args.output.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
