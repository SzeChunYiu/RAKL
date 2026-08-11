#!/usr/bin/env python3
"""Stage the frozen public BGE snapshot inside one allocated LUNARC job."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from semantic_descriptor_common import (
    ACCOUNT,
    PARTITION,
    atomic_write_json,
    file_sha256,
    inspect_model_files,
    utc_now,
    validate_repo_and_contract,
    validate_schema,
)


def _receipt_base(
    *, contract: dict[str, Any], expected_repo_sha: str, failures: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": "paper3-semantic-model-stage-execution-v1",
        "created_at_utc": utc_now(),
        "verdict": "STAGING_CANNOT_CHECK",
        "expected_repo_sha": expected_repo_sha,
        "frozen_parent_sha": contract.get("frozen_parent_sha"),
        "contract_sha256": os.environ.get("RAKL_CONTRACT_SHA256"),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_account": os.environ.get("SLURM_JOB_ACCOUNT"),
        "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
        "node": platform.node(),
        "model_id": contract.get("model", {}).get("model_id"),
        "model_revision": contract.get("model", {}).get("revision"),
        "final_model_path": contract.get("fs9", {}).get("model_dir"),
        "observed_model_files": [],
        "failures": failures,
        "model_execution_performed": False,
        "descriptor_record_count": 0,
        "label_access": {
            "external_annotation_accessed": False,
            "adjudication_accessed": False,
            "evaluated_result_accessed": False,
        },
        "claim_boundary": (
            "Allocated-job model staging and local hash verification only; no semantic "
            "descriptor, structural-signal, training, inference-efficiency, break-even, "
            "independent-review or peer-review result."
        ),
    }


def run_stage(*, repo: Path, contract_path: Path, output: Path) -> dict[str, Any]:
    expected_repo_sha = os.environ.get("RAKL_EXPECTED_REPO_SHA", "")
    contract, failures = validate_repo_and_contract(
        repo=repo, contract_path=contract_path, expected_repo_sha=expected_repo_sha
    )
    if file_sha256(contract_path) != os.environ.get("RAKL_CONTRACT_SHA256"):
        failures.append("contract_environment_hash_mismatch")
    if not os.environ.get("SLURM_JOB_ID"):
        failures.append("not_inside_slurm_allocation")
    if os.environ.get("SLURM_JOB_ACCOUNT") != ACCOUNT:
        failures.append("slurm_account_mismatch")
    if os.environ.get("SLURM_JOB_PARTITION") != PARTITION:
        failures.append("slurm_partition_mismatch")
    receipt = _receipt_base(
        contract=contract, expected_repo_sha=expected_repo_sha, failures=failures
    )
    schema = repo / "schemas/paper3-semantic-model-stage-execution-v1.schema.json"
    if failures:
        validate_schema(receipt, schema)
        atomic_write_json(output, receipt)
        return receipt

    final = Path(contract["fs9"]["model_dir"])
    candidate = final.parent / f".{final.name}.candidate-{os.environ['SLURM_JOB_ID']}"
    if not final.parent.is_dir():
        receipt["failures"].append("model_parent_directory_missing")
    if final.exists():
        receipt["failures"].append("final_model_path_already_exists")
    if candidate.exists():
        receipt["failures"].append("candidate_model_path_already_exists")
    if receipt["failures"]:
        validate_schema(receipt, schema)
        atomic_write_json(output, receipt)
        return receipt

    candidate.mkdir(parents=False, exist_ok=False)
    model = contract["model"]
    base = (
        f"https://huggingface.co/{model['model_id']}/resolve/"
        f"{model['revision']}"
    )
    try:
        for expected in model["required_files"]:
            relative = expected["path"]
            destination = candidate / relative
            temporary = destination.with_name(f".{destination.name}.download")
            completed = subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--retry",
                    "4",
                    "--connect-timeout",
                    "30",
                    "--output",
                    str(temporary),
                    f"{base}/{relative}?download=true",
                ],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            if completed.returncode != 0:
                receipt["failures"].append(f"model_download_failed:{relative}")
                break
            temporary.replace(destination)
        observed, asset_failures = inspect_model_files(
            candidate, model["required_files"]
        )
        receipt["observed_model_files"] = observed
        receipt["failures"].extend(asset_failures)
        if not receipt["failures"]:
            candidate.replace(final)
            receipt["verdict"] = "STAGING_PASS_ATOMICALLY_PROMOTED"
    except Exception as exc:
        receipt["failures"].append(f"staging_exception:{type(exc).__name__}")
    finally:
        if candidate.exists():
            shutil.rmtree(candidate)

    receipt["failures"] = list(dict.fromkeys(receipt["failures"]))
    validate_schema(receipt, schema)
    atomic_write_json(output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_stage(
        repo=args.repo.resolve(),
        contract_path=args.contract.resolve(),
        output=args.output.resolve(),
    )
    # Typed staging failures are harvested as CANNOT_CHECK rather than hidden by
    # an absent receipt. Unexpected crashes still make the SLURM job fail.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
