"""Submit demoted AI_OPERATOR Paper3 LUNARC pilots.

Lineage subject = annotation packet parent.
Execution subject = clean checkout containing demoted runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .paper3_annotation import canonical_sha256
from .paper3_lunarc_preflight import _git_state


FS9_ROOT = PurePosixPath("/projects/hep/fs9/users/scyiu/RAKL-paper3")
ALLOWED_ASSOCIATIONS = {
    ("lu2026-2-51", "gpua100"),
    ("lu2026-2-51", "gpua100i"),
    ("lu2026-2-51", "gpua40"),
    ("lu2026-2-51", "gpua40i"),
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_and_submit_demoted_workload(
    *,
    manifest: dict[str, Any],
    gate_receipt: dict[str, Any],
    observed_execution_subject_sha: str,
    checkout_clean: bool,
    output_exists: bool,
    execution_host: str,
    observed_associations: set[tuple[str, str]],
    observed_repo_path: str,
    runner: Callable[..., Any] = subprocess.run,
    submit: bool = False,
) -> dict[str, Any]:
    failures: list[str] = []
    gate_ok = bool(
        gate_receipt.get("schema_version") == "paper3-confirmatory-gate-result-v2"
        and gate_receipt.get("gate_verdict") == "PASS_AUTHORIZE_DEMOTED_AI_OPERATOR_TRAIN"
        and gate_receipt.get("authority_class") == "DEMOTED_AI_OPERATOR"
        and gate_receipt.get("expensive_training_authorized") is True
        and gate_receipt.get("overall_cheap_gate_passed") is False
        and gate_receipt.get("annotation_gate", {}).get("passed") is True
    )
    if not gate_ok:
        failures.append("gate_receipt_not_demoted_authorized")
    if manifest.get("authority_class") != "DEMOTED_AI_OPERATOR":
        failures.append("manifest_not_demoted_authority")
    if manifest.get("independent_external_human") is not False:
        failures.append("manifest_claims_external_human")
    if not checkout_clean:
        failures.append("checkout_not_clean")
    if not execution_host.startswith("cosmos"):
        failures.append("not_running_on_lunarc_login_host")
    if manifest.get("execution_subject_sha") != observed_execution_subject_sha:
        failures.append("execution_subject_sha_mismatch")
    if gate_receipt.get("subject_sha") != manifest.get("lineage_subject_sha"):
        failures.append("lineage_subject_gate_mismatch")

    repo = Path(str(manifest.get("repo_path", "")))
    if not repo.is_dir() or repo.resolve() != Path(observed_repo_path).resolve():
        failures.append("repo_path_mismatch")
    for name in ("manifest_path", "gate_receipt_path", "annotation_import_receipt_path", "benchmark_path", "protocol_path"):
        path = Path(str(manifest.get(name, "")))
        if not path.is_file():
            failures.append(f"path_missing:{name}")
    if Path(str(manifest.get("gate_receipt_path", ""))).is_file():
        if canonical_sha256(json.loads(Path(manifest["gate_receipt_path"]).read_text())) != canonical_sha256(gate_receipt):
            failures.append("gate_path_content_mismatch")
    if Path(str(manifest.get("manifest_path", ""))).is_file():
        if canonical_sha256(json.loads(Path(manifest["manifest_path"]).read_text())) != canonical_sha256(manifest):
            failures.append("manifest_path_content_mismatch")

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

    script = Path(str(manifest.get("batch_script", "")))
    if not script.is_file() or _file_sha256(script) != manifest.get("batch_script_sha256"):
        failures.append("batch_script_hash_mismatch")
    runner_path = Path(str(manifest.get("runner_path", "")))
    if not runner_path.is_file() or _file_sha256(runner_path) != manifest.get("runner_sha256"):
        failures.append("runner_hash_mismatch")
    weights = Path(str(manifest.get("input_weights_path", "")))
    if not weights.is_file() or _file_sha256(weights) != manifest.get("input_weights_sha256"):
        failures.append("input_weights_hash_mismatch")
    python = Path(str(manifest.get("python_executable", "")))
    if not python.is_file():
        failures.append("python_executable_invalid")

    failures = list(dict.fromkeys(failures))
    receipt: dict[str, Any] = {
        "schema_version": "paper3-lunarc-workload-submission-receipt-v1",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "experiment_id": manifest.get("experiment_id"),
        "workload": manifest.get("workload"),
        "model_mode": manifest.get("model_mode"),
        "manifest_sha256": canonical_sha256(manifest),
        "gate_receipt_sha256": canonical_sha256(gate_receipt),
        "subject_sha": manifest.get("execution_subject_sha"),
        "lineage_subject_sha": manifest.get("lineage_subject_sha"),
        "authority_class": "DEMOTED_AI_OPERATOR",
        "independent_external_human": False,
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
        receipt["verdict"] = "REFUSE_DEMOTED_PREFLIGHT"
        return receipt
    if not submit:
        receipt["verdict"] = "READY_NOT_SUBMITTED"
        return receipt

    export = (
        "NONE,"
        f"RAKL_EXPERIMENT_MANIFEST={manifest['manifest_path']},"
        f"RAKL_GATE_RECEIPT={manifest['gate_receipt_path']},"
        f"RAKL_EXPECTED_EXECUTION_SUBJECT_SHA={manifest['execution_subject_sha']},"
        f"RAKL_EXPECTED_MANIFEST_SHA256={canonical_sha256(manifest)},"
        f"RAKL_EXPECTED_GATE_SHA256={canonical_sha256(gate_receipt)},"
        f"RAKL_REPO_PATH={manifest['repo_path']},"
        f"RAKL_PYTHON_EXECUTABLE={manifest['python_executable']}"
    )
    argv = [
        "sbatch",
        "--parsable",
        f"--account={account}",
        f"--partition={partition}",
        f"--chdir={manifest['repo_path']}",
        f"--output={output}.slurm-%j.out",
        f"--export={export}",
        str(script),
    ]
    receipt["sbatch_argv"] = argv
    try:
        completed = runner(argv, capture_output=True, text=True, check=True, shell=False)
    except Exception as exc:  # noqa: BLE001
        receipt["failures"].append("sbatch_submission_failed")
        receipt["submission_error_type"] = type(exc).__name__
        receipt["verdict"] = "SUBMISSION_FAILED"
        return receipt
    job_id = str(completed.stdout).strip().split(";", 1)[0]
    if not job_id.isdigit():
        receipt["failures"].append("sbatch_invalid_job_id")
        receipt["verdict"] = "SUBMISSION_FAILED"
        return receipt
    receipt["submitted"] = True
    receipt["slurm_job_id"] = job_id
    receipt["verdict"] = "SUBMITTED_AFTER_DEMOTED_AI_OPERATOR_GATE"
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
    receipt = validate_and_submit_demoted_workload(
        manifest=manifest,
        gate_receipt=gate,
        observed_execution_subject_sha=observed_sha,
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
    print(receipt.get("verdict"), receipt.get("slurm_job_id"), receipt.get("failures"))
    return 0 if receipt.get("submitted") or receipt.get("verdict") == "READY_NOT_SUBMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
