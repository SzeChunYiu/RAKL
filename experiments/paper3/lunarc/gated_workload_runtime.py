#!/usr/bin/env python3
"""Compute-node guard and receipt writer for gate-authorized Paper 3 workloads.

This file does not implement an experiment.  It verifies the frozen experiment
lineage, then invokes the separately content-bound runner recorded in the
manifest.  Missing or false gate evidence exits before the FS9 output directory
is created.
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
        "model_mode": "trainable_copy",
        "resource_profile": "single_gpu_training_v1",
        "batch_name": "training_after_gate.sbatch",
        "batch_sha256": "0853f749719b86e61301b70757c13637b7fd1e352b321fe8934c777d2201ac6c",
    },
    "inference": {
        "model_mode": "frozen",
        "resource_profile": "single_gpu_frozen_inference_v1",
        "batch_name": "frozen_inference_after_gate.sbatch",
        "batch_sha256": "c5356f1abefa3a063c9ceafb5d38cdd1fe666d238f6d87aea8f27211ff9e591a",
    },
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_schema(value: dict[str, Any], path: Path) -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def require(condition: bool, code: str) -> None:
    """Raise explicitly; unlike assert, this guard survives python -O."""
    if not condition:
        raise RuntimeError(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-workload", choices=("training", "inference"), required=True)
    args = parser.parse_args()

    manifest_path = Path(os.environ["RAKL_EXPERIMENT_MANIFEST"]).resolve()
    gate_path = Path(os.environ["RAKL_GATE_RECEIPT"]).resolve()
    repo = Path(os.environ["RAKL_REPO_PATH"]).resolve()
    expected_subject = os.environ["RAKL_EXPECTED_SUBJECT_SHA"]
    manifest = load_json(manifest_path)
    gate = load_json(gate_path)

    # Recheck the login-node submission contract on the allocated node.  These
    # are explicit exceptions rather than assertions so python -O cannot remove
    # a scientific or execution gate.
    require(manifest_path == Path(manifest["manifest_path"]).resolve(), "manifest_path_mismatch")
    require(gate_path == Path(manifest["gate_receipt_path"]).resolve(), "gate_path_mismatch")
    require(canonical_sha256(manifest) == os.environ["RAKL_EXPECTED_MANIFEST_SHA256"], "manifest_env_hash_mismatch")
    require(canonical_sha256(gate) == os.environ["RAKL_EXPECTED_GATE_SHA256"], "gate_env_hash_mismatch")
    require(canonical_sha256(gate) == manifest["gate_receipt_sha256"], "gate_manifest_hash_mismatch")
    require(manifest["workload"] == args.expected_workload, "workload_mismatch")
    binding = WORKLOAD_BINDINGS[args.expected_workload]
    require(manifest["model_mode"] == binding["model_mode"], "model_mode_mismatch")
    require(manifest["resource_profile"] == binding["resource_profile"], "resource_profile_mismatch")
    require(manifest["subject_sha"] == expected_subject, "subject_env_mismatch")
    require(manifest["repo_path"] == str(repo), "repo_path_mismatch")
    require(os.environ["RAKL_PYTHON_EXECUTABLE"] == manifest["python_executable"], "python_executable_mismatch")
    observed_subject = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
        check=True, shell=False,
    ).stdout.strip()
    observed_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True,
        text=True, check=True, shell=False,
    ).stdout
    require(observed_subject == expected_subject, "checkout_subject_mismatch")
    require(not observed_status.strip(), "checkout_dirty")

    schema_root = repo / "schemas"
    validate_schema(manifest, schema_root / "paper3-lunarc-workload-manifest.schema.json")
    validate_schema(gate, schema_root / "paper3-confirmatory-gate-result.schema.json")
    require(gate["subject_sha"] == expected_subject, "gate_subject_mismatch")
    require(gate["annotation_gate"]["passed"] is True, "gate_annotation_not_passed")
    require(gate["expensive_training_authorized"] is True, "gate_compute_not_authorized")
    demoted = gate.get("gate_verdict") == "PASS_AUTHORIZE_DEMOTED_AI_OPERATOR_TRAIN"
    confirmatory = gate.get("gate_verdict") == "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
    require(demoted or confirmatory, "gate_verdict_not_authorized")
    if confirmatory:
        require(gate["diagnostic_signal_gate"]["passed"] is True, "gate_signal_not_passed")
        require(gate["overall_cheap_gate_passed"] is True, "gate_overall_not_passed")
    else:
        require(gate.get("authority_class") == "DEMOTED_AI_OPERATOR", "demoted_authority_missing")
        require(gate.get("overall_cheap_gate_passed") is False, "demoted_must_not_claim_cheap_pass")

    require(manifest["account"] == "lu2026-2-51", "account_mismatch")
    require(manifest["partition"] in {"gpua100", "gpua100i", "gpua40", "gpua40i"}, "partition_not_allowed")
    require(os.environ.get("SLURM_JOB_ACCOUNT") == manifest["account"], "slurm_account_mismatch")
    require(os.environ.get("SLURM_JOB_PARTITION") == manifest["partition"], "slurm_partition_mismatch")
    batch = Path(manifest["batch_script"]).resolve()
    require(batch.name == binding["batch_name"], "batch_script_name_mismatch")
    require(batch.is_file(), "batch_script_missing")
    require(file_sha256(batch) == binding["batch_sha256"], "batch_script_allowlist_mismatch")
    require(manifest["batch_script_sha256"] == binding["batch_sha256"], "batch_script_manifest_hash_mismatch")

    for name in ("protocol", "benchmark", "annotation_import_receipt"):
        path = Path(manifest[f"{name}_path"])
        value = load_json(path)
        require(canonical_sha256(value) == manifest[f"{name}_sha256"], f"lineage_hash_mismatch:{name}")
    require(manifest["protocol_sha256"] == gate["protocol_sha256"], "gate_protocol_hash_mismatch")
    require(manifest["benchmark_sha256"] == gate["benchmark_sha256"], "gate_benchmark_hash_mismatch")
    for name in ("task_set", "environment", "seed_schedule", "model_artifact"):
        path = Path(manifest[f"{name}_path"])
        require(path.is_absolute() and path.is_file(), f"artifact_path_invalid:{name}")
        require(file_sha256(path) == manifest[f"{name}_sha256"], f"artifact_hash_mismatch:{name}")
        artifact = load_json(path)
        validate_schema(artifact, schema_root / "paper3-lunarc-bound-artifact.schema.json")
        require(artifact["artifact_type"] == name, f"artifact_type_mismatch:{name}")
        require(artifact["subject_sha"] == expected_subject, f"artifact_subject_mismatch:{name}")
    annotation_import = load_json(Path(manifest["annotation_import_receipt_path"]))
    validate_schema(annotation_import, schema_root / "paper3-annotation-import-receipt.schema.json")
    require(annotation_import["passed"] is True, "annotation_import_not_passed")
    require(annotation_import["training_authorized"] is False, "annotation_import_scope_violation")
    require(annotation_import["failures"] == [], "annotation_import_has_failures")
    require(annotation_import["subject_sha"] == expected_subject, "annotation_import_subject_mismatch")
    require(annotation_import["protocol_sha256"] == manifest["protocol_sha256"], "annotation_import_protocol_mismatch")
    require(annotation_import["benchmark_sha256"] == manifest["benchmark_sha256"], "annotation_import_benchmark_mismatch")

    runner = Path(manifest["runner_path"]).resolve()
    result_schema = Path(manifest["result_schema_path"]).resolve()
    weights = Path(manifest["input_weights_path"]).resolve()
    require(runner.is_file() and file_sha256(runner) == manifest["runner_sha256"], "runner_binding_invalid")
    require(result_schema.is_file() and file_sha256(result_schema) == manifest["result_schema_sha256"], "result_schema_binding_invalid")
    require(weights.is_file() and file_sha256(weights) == manifest["input_weights_sha256"], "input_weights_binding_invalid")
    require(str(runner).startswith(str(repo) + os.sep), "runner_outside_repo")
    require(str(result_schema).startswith(str(repo) + os.sep), "result_schema_outside_repo")
    model_artifact = load_json(Path(manifest["model_artifact_path"]))
    require(model_artifact["payload"]["model_revision"] == manifest["model_revision"], "model_revision_mismatch")
    require(model_artifact["payload"]["weights_artifact_sha256"] == manifest["input_weights_sha256"], "model_weights_hash_mismatch")

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
            manifest["python_executable"], str(runner), "--manifest",
            str(manifest_path), "--receipt-output", str(result_path),
        ],
        cwd=repo,
        check=False,
        shell=False,
    )
    weights_after = file_sha256(weights)

    failures: list[str] = []
    result_sha: str | None = None
    if completed.returncode != 0:
        failures.append("runner_nonzero_exit")
    elif not result_path.is_file():
        failures.append("result_receipt_missing")
    else:
        try:
            result = load_json(result_path)
            validate_schema(result, result_schema)
            require(result.get("subject_sha") == expected_subject, "result_subject_mismatch")
            require(result.get("experiment_id") == manifest["experiment_id"], "result_experiment_mismatch")
            result_sha = file_sha256(result_path)
        except Exception:
            failures.append("result_receipt_invalid")
    if weights_after != weights_before:
        failures.append("input_model_mutated")

    if "input_model_mutated" in failures:
        verdict = "FAIL_INPUT_MODEL_MUTATED"
    elif "runner_nonzero_exit" in failures:
        verdict = "FAIL_RUNNER"
    elif failures:
        verdict = "FAIL_RESULT_RECEIPT"
    else:
        verdict = "PASS"
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
        capture_output=True, text=True, check=True, shell=False,
    ).stdout.strip().splitlines()
    receipt = {
        "schema_version": "paper3-lunarc-workload-receipt-v1",
        "created_at_utc": utc_now(),
        "experiment_id": manifest["experiment_id"],
        "workload": manifest["workload"],
        "subject_sha": expected_subject,
        "manifest_sha256": canonical_sha256(manifest),
        "gate_receipt_sha256": canonical_sha256(gate),
        "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "slurm_account": os.environ.get("SLURM_JOB_ACCOUNT"),
        "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
        "node": platform.node(),
        "gpu": gpu,
        "input_weights_sha256_before": weights_before,
        "input_weights_sha256_after": weights_after,
        "runner_exit_code": completed.returncode,
        "result_receipt_sha256": result_sha,
        "failures": failures,
        "verdict": verdict,
    }
    validate_schema(receipt, schema_root / "paper3-lunarc-workload-receipt.schema.json")
    temporary = receipts / ".workload_receipt.json.tmp"
    final = receipts / "workload_receipt.json"
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(final)
    print(final)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
