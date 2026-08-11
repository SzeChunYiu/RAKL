#!/usr/bin/env python3
"""Compute-node guard for demoted AI_OPERATOR Paper3 pilots.

Lineage subject (annotation packet parent) may differ from execution subject
(current clean checkout containing demoted runtime). Confirmatory human-gate
checks are intentionally not reused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FS9_ROOT = Path("/projects/hep/fs9/users/scyiu/RAKL-paper3")
WORKLOAD_BINDINGS = {
    "training": {
        "batch_name": "ai_operator_demoted_training.sbatch",
        "model_mode": "trainable_copy",
    },
    "inference": {
        "batch_name": "ai_operator_demoted_inference.sbatch",
        "model_mode": "frozen",
    },
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-workload", choices=("training", "inference"), required=True)
    args = parser.parse_args()

    manifest_path = Path(os.environ["RAKL_EXPERIMENT_MANIFEST"]).resolve()
    gate_path = Path(os.environ["RAKL_GATE_RECEIPT"]).resolve()
    repo = Path(os.environ["RAKL_REPO_PATH"]).resolve()
    expected_execution = os.environ["RAKL_EXPECTED_EXECUTION_SUBJECT_SHA"]
    manifest = load_json(manifest_path)
    gate = load_json(gate_path)

    require(canonical_sha256(manifest) == os.environ["RAKL_EXPECTED_MANIFEST_SHA256"], "manifest_env_hash_mismatch")
    require(canonical_sha256(gate) == os.environ["RAKL_EXPECTED_GATE_SHA256"], "gate_env_hash_mismatch")
    require(manifest["workload"] == args.expected_workload, "workload_mismatch")
    binding = WORKLOAD_BINDINGS[args.expected_workload]
    require(manifest["model_mode"] == binding["model_mode"], "model_mode_mismatch")
    require(manifest["execution_subject_sha"] == expected_execution, "execution_subject_env_mismatch")
    require(manifest["repo_path"] == str(repo), "repo_path_mismatch")

    observed_subject = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True, shell=False
    ).stdout.strip()
    observed_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True, shell=False
    ).stdout
    require(observed_subject == expected_execution, "checkout_execution_subject_mismatch")
    require(not observed_status.strip(), "checkout_dirty")

    require(gate["schema_version"] == "paper3-confirmatory-gate-result-v2", "gate_schema_mismatch")
    require(gate["gate_verdict"] == "PASS_AUTHORIZE_DEMOTED_AI_OPERATOR_TRAIN", "gate_verdict_not_demoted")
    require(gate["authority_class"] == "DEMOTED_AI_OPERATOR", "authority_not_demoted")
    require(gate["expensive_training_authorized"] is True, "train_not_authorized")
    require(gate["overall_cheap_gate_passed"] is False, "demoted_must_not_claim_cheap_pass")
    require(gate["annotation_gate"]["passed"] is True, "annotation_gate_not_passed")
    require(gate["subject_sha"] == manifest["lineage_subject_sha"], "lineage_subject_mismatch")

    annotation_import = load_json(Path(manifest["annotation_import_receipt_path"]))
    require(annotation_import["passed"] is True, "annotation_import_not_passed")
    require(annotation_import["training_authorized"] is False, "annotation_import_scope_violation")
    require(annotation_import.get("annotation_authority_class") == "DEMOTED_AI_OPERATOR", "import_not_demoted")
    require(annotation_import["subject_sha"] == manifest["lineage_subject_sha"], "import_lineage_mismatch")

    batch = Path(manifest["batch_script"]).resolve()
    require(batch.name == binding["batch_name"], "batch_script_name_mismatch")
    require(file_sha256(batch) == manifest["batch_script_sha256"], "batch_script_hash_mismatch")

    runner = Path(manifest["runner_path"]).resolve()
    require(runner.is_file() and file_sha256(runner) == manifest["runner_sha256"], "runner_binding_invalid")
    require(str(runner).startswith(str(repo) + os.sep), "runner_outside_repo")

    weights = Path(manifest["input_weights_path"]).resolve()
    require(weights.is_file() and file_sha256(weights) == manifest["input_weights_sha256"], "weights_hash_mismatch")

    output = Path(manifest["fs9_output_dir"])
    require(output.parent == FS9_ROOT, "fs9_output_outside_registered_root")
    require(not output.exists(), "fs9_output_already_exists")
    output.mkdir(parents=False, exist_ok=False)
    receipts = output / "receipts"
    receipts.mkdir()
    result_path = output / manifest["result_receipt_relpath"]
    require(result_path.parent == receipts, "result_receipt_path_invalid")

    weights_before = file_sha256(weights)
    completed = subprocess.run(
        [
            manifest["python_executable"],
            str(runner),
            "--manifest",
            str(manifest_path),
            "--receipt-output",
            str(result_path),
        ],
        cwd=repo,
        check=False,
        shell=False,
    )
    weights_after = file_sha256(weights)
    failures: list[str] = []
    if completed.returncode != 0:
        failures.append("runner_nonzero_exit")
    if not result_path.is_file():
        failures.append("result_receipt_missing")
    if weights_after != weights_before:
        failures.append("input_model_mutated")
    verdict = "PASS" if not failures else "FAIL_DEMOTED_PILOT"
    receipt = {
        "schema_version": "paper3-lunarc-workload-receipt-v1",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "experiment_id": manifest["experiment_id"],
        "workload": manifest["workload"],
        "subject_sha": expected_execution,
        "lineage_subject_sha": manifest["lineage_subject_sha"],
        "manifest_sha256": canonical_sha256(manifest),
        "gate_receipt_sha256": canonical_sha256(gate),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_account": os.environ.get("SLURM_JOB_ACCOUNT"),
        "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
        "node": platform.node(),
        "authority_class": "DEMOTED_AI_OPERATOR",
        "independent_external_human": False,
        "input_weights_sha256_before": weights_before,
        "input_weights_sha256_after": weights_after,
        "runner_exit_code": completed.returncode,
        "result_receipt_sha256": file_sha256(result_path) if result_path.is_file() else None,
        "failures": failures,
        "verdict": verdict,
    }
    final = receipts / "workload_receipt.json"
    final.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(final)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
