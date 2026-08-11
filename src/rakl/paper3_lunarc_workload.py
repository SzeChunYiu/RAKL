from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .paper3_annotation import canonical_sha256
from .paper3_lunarc_preflight import _git_state, _load_json, _schema_valid


FS9_ROOT = PurePosixPath("/projects/hep/fs9/users/scyiu/RAKL-paper3")
ALLOWED_ASSOCIATIONS = {
    ("lu2026-2-51", "gpua100"),
    ("lu2026-2-51", "gpua100i"),
    ("lu2026-2-51", "gpua40"),
    ("lu2026-2-51", "gpua40i"),
}
WORKLOAD_SCRIPTS = {
    "training": (
        "training_after_gate.sbatch",
        "0853f749719b86e61301b70757c13637b7fd1e352b321fe8934c777d2201ac6c",
        "trainable_copy",
    ),
    "inference": (
        "frozen_inference_after_gate.sbatch",
        "c5356f1abefa3a063c9ceafb5d38cdd1fe666d238f6d87aea8f27211ff9e591a",
        "frozen",
    ),
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(
        character in "0123456789abcdef" for character in value
    )


def validate_and_submit_workload(
    *,
    manifest: dict[str, Any],
    gate_receipt: dict[str, Any],
    observed_subject_sha: str,
    checkout_clean: bool,
    output_exists: bool,
    execution_host: str,
    observed_associations: set[tuple[str, str]],
    observed_repo_path: str,
    runner: Callable[..., Any] = subprocess.run,
    submit: bool = False,
    schema_checker: Callable[[dict[str, Any], str], bool] = _schema_valid,
) -> dict[str, Any]:
    failures: list[str] = []
    gate_passed = bool(
        gate_receipt.get("schema_version") == "paper3-confirmatory-gate-result-v2"
        and gate_receipt.get("annotation_gate", {}).get("passed") is True
        and gate_receipt.get("diagnostic_signal_gate", {}).get("passed") is True
        and gate_receipt.get("overall_cheap_gate_passed") is True
        and gate_receipt.get("expensive_training_authorized") is True
        and gate_receipt.get("gate_verdict") == "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
    )
    if not gate_passed:
        failures.append("gate_receipt_not_authorized")
    if not schema_checker(gate_receipt, "paper3-confirmatory-gate-result.schema.json"):
        failures.append("gate_receipt_schema_invalid")
    if not schema_checker(manifest, "paper3-lunarc-workload-manifest.schema.json"):
        failures.append("manifest_schema_invalid")

    subject = manifest.get("subject_sha")
    if not _hex(subject, 40) or subject != observed_subject_sha:
        failures.append("subject_sha_mismatch")
    if gate_receipt.get("subject_sha") != subject:
        failures.append("gate_subject_sha_mismatch")
    if manifest.get("gate_receipt_sha256") != canonical_sha256(gate_receipt):
        failures.append("gate_receipt_hash_mismatch")
    if not checkout_clean:
        failures.append("checkout_not_clean")
    if not execution_host.startswith("cosmos"):
        failures.append("not_running_on_lunarc_login_host")

    repo = Path(str(manifest.get("repo_path", "")))
    if not repo.is_dir() or repo.resolve() != Path(observed_repo_path).resolve():
        failures.append("repo_path_mismatch")
    manifest_path = Path(str(manifest.get("manifest_path", "")))
    if not manifest_path.is_file() or canonical_sha256(_load_json(manifest_path) or {}) != canonical_sha256(manifest):
        failures.append("manifest_path_content_mismatch")
    gate_path = Path(str(manifest.get("gate_receipt_path", "")))
    if not gate_path.is_file() or canonical_sha256(_load_json(gate_path) or {}) != canonical_sha256(gate_receipt):
        failures.append("gate_path_content_mismatch")

    for name in ("protocol", "benchmark", "annotation_import_receipt"):
        path = Path(str(manifest.get(f"{name}_path", "")))
        value = _load_json(path) if path.is_absolute() else None
        if value is None or canonical_sha256(value) != manifest.get(f"{name}_sha256"):
            failures.append(f"lineage_hash_mismatch:{name}")
    if manifest.get("protocol_sha256") != gate_receipt.get("protocol_sha256"):
        failures.append("gate_protocol_hash_mismatch")
    if manifest.get("benchmark_sha256") != gate_receipt.get("benchmark_sha256"):
        failures.append("gate_benchmark_hash_mismatch")
    annotation_import = _load_json(Path(str(manifest.get("annotation_import_receipt_path", "")))) or {}
    if (
        annotation_import.get("passed") is not True
        or annotation_import.get("failures") != []
        or annotation_import.get("subject_sha") != subject
        or annotation_import.get("protocol_sha256") != manifest.get("protocol_sha256")
        or annotation_import.get("benchmark_sha256") != manifest.get("benchmark_sha256")
    ):
        failures.append("annotation_import_lineage_mismatch")

    for name in ("task_set", "environment", "seed_schedule", "model_artifact"):
        path = Path(str(manifest.get(f"{name}_path", "")))
        if not path.is_absolute() or not path.is_file():
            failures.append(f"artifact_path_invalid:{name}")
        elif _file_sha256(path) != manifest.get(f"{name}_sha256"):
            failures.append(f"artifact_hash_mismatch:{name}")
        else:
            value = _load_json(path)
            if (
                value is None
                or not schema_checker(value, "paper3-lunarc-bound-artifact.schema.json")
                or value.get("artifact_type") != name
                or value.get("subject_sha") != subject
            ):
                failures.append(f"artifact_contract_invalid:{name}")
            elif name == "model_artifact" and (
                value.get("payload", {}).get("model_revision") != manifest.get("model_revision")
                or value.get("payload", {}).get("weights_artifact_sha256")
                != manifest.get("input_weights_sha256")
            ):
                failures.append("model_artifact_lineage_mismatch")
    weights = Path(str(manifest.get("input_weights_path", "")))
    if not weights.is_absolute() or not weights.is_file() or _file_sha256(weights) != manifest.get("input_weights_sha256"):
        failures.append("input_weights_hash_mismatch")
    python = Path(str(manifest.get("python_executable", "")))
    if not python.is_absolute() or not python.is_file() or not os.access(python, os.X_OK):
        failures.append("python_executable_invalid")
    for field in (
        "manifest_path",
        "gate_receipt_path",
        "repo_path",
        "python_executable",
    ):
        value = manifest.get(field)
        if not isinstance(value, str) or any(character in value for character in ",\r\n"):
            failures.append(f"unsafe_sbatch_export_value:{field}")
    for name in ("runner", "result_schema"):
        path = Path(str(manifest.get(f"{name}_path", "")))
        if (
            not path.is_absolute()
            or not path.is_file()
            or _file_sha256(path) != manifest.get(f"{name}_sha256")
            or not str(path.resolve()).startswith(str(repo.resolve()) + os.sep)
        ):
            failures.append(f"{name}_binding_invalid")

    workload = manifest.get("workload")
    script = Path(str(manifest.get("batch_script", "")))
    expected = WORKLOAD_SCRIPTS.get(str(workload))
    if expected is None:
        failures.append("unsupported_workload")
    else:
        expected_name, expected_hash, expected_mode = expected
        if manifest.get("model_mode") != expected_mode:
            failures.append("workload_model_mode_mismatch")
        if script.name != expected_name or not script.is_file():
            failures.append("workload_batch_script_mismatch")
        elif _file_sha256(script) != expected_hash or manifest.get("batch_script_sha256") != expected_hash:
            failures.append("workload_batch_script_hash_mismatch")

    account = manifest.get("account")
    partition = manifest.get("partition")
    if (account, partition) not in ALLOWED_ASSOCIATIONS or (account, partition) not in observed_associations:
        failures.append("account_partition_association_missing")
    output = manifest.get("fs9_output_dir")
    if not isinstance(output, str):
        failures.append("fs9_output_outside_registered_root")
    else:
        output_path = PurePosixPath(output)
        if ".." in output_path.parts or output_path.parent != FS9_ROOT:
            failures.append("fs9_output_outside_registered_root")
    if output_exists:
        failures.append("fs9_output_already_exists")

    failures = list(dict.fromkeys(failures))
    receipt: dict[str, Any] = {
        "schema_version": "paper3-lunarc-workload-submission-receipt-v1",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "experiment_id": manifest.get("experiment_id"),
        "workload": workload,
        "model_mode": manifest.get("model_mode"),
        "manifest_sha256": canonical_sha256(manifest),
        "gate_receipt_sha256": canonical_sha256(gate_receipt),
        "subject_sha": subject,
        "execution_host": execution_host,
        "account": account,
        "partition": partition,
        "fs9_output_dir": output,
        "batch_script_sha256": manifest.get("batch_script_sha256"),
        "failures": failures,
        "submitted": False,
        "slurm_job_id": None,
    }
    if failures:
        receipt["verdict"] = "REFUSE_GATE_CLOSED" if "gate_receipt_not_authorized" in failures else "REFUSE_PREFLIGHT_VALIDATION"
        return receipt
    if not submit:
        receipt["verdict"] = "READY_NOT_SUBMITTED"
        return receipt

    export = (
        "NONE,"
        f"RAKL_EXPERIMENT_MANIFEST={manifest_path},"
        f"RAKL_GATE_RECEIPT={gate_path},"
        f"RAKL_EXPECTED_SUBJECT_SHA={subject},"
        f"RAKL_EXPECTED_MANIFEST_SHA256={canonical_sha256(manifest)},"
        f"RAKL_EXPECTED_GATE_SHA256={canonical_sha256(gate_receipt)},"
        f"RAKL_REPO_PATH={repo},"
        f"RAKL_PYTHON_EXECUTABLE={python}"
    )
    argv = [
        "sbatch", "--parsable", f"--account={account}", f"--partition={partition}",
        f"--chdir={repo}", f"--output={output}.slurm-%j.out", f"--export={export}", str(script),
    ]
    receipt["sbatch_argv"] = argv
    try:
        completed = runner(argv, capture_output=True, text=True, check=True, shell=False)
    except Exception as exc:
        receipt["failures"].append("sbatch_submission_failed")
        receipt["submission_error_type"] = type(exc).__name__
        receipt["verdict"] = "SUBMISSION_FAILED"
        return receipt
    job_id = str(completed.stdout).strip().split(";", 1)[0]
    if not job_id.isdigit():
        receipt["failures"].append("sbatch_invalid_job_id")
        receipt["submission_error_type"] = "InvalidParsableJobId"
        receipt["verdict"] = "SUBMISSION_FAILED"
        return receipt
    receipt["submitted"] = True
    receipt["slurm_job_id"] = job_id
    receipt["verdict"] = "SUBMITTED_AFTER_EXACT_GATE_PASS"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--gate-receipt", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--association", action="append", default=[])
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    gate = json.loads(args.gate_receipt.read_text(encoding="utf-8"))
    observed_sha, clean = _git_state(args.repo)
    associations = {tuple(value.split(":", 1)) for value in args.association if ":" in value}
    receipt = validate_and_submit_workload(
        manifest=manifest,
        gate_receipt=gate,
        observed_subject_sha=observed_sha,
        checkout_clean=clean,
        output_exists=Path(str(manifest.get("fs9_output_dir", ""))).exists(),
        execution_host=socket.gethostname(),
        observed_associations=associations,
        observed_repo_path=str(args.repo.resolve()),
        submit=args.submit,
    )
    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.receipt_output)
    return 0 if receipt["verdict"] in {"READY_NOT_SUBMITTED", "SUBMITTED_AFTER_EXACT_GATE_PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
