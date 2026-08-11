from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .paper3_annotation import canonical_sha256


FS9_ROOT = PurePosixPath("/projects/hep/fs9/users/scyiu/RAKL-paper3")
ALLOWED_PARTITIONS = {"gpua100", "gpua100i", "gpua40", "gpua40i"}
ALLOWED_BATCH_SCRIPT_SHA256 = {
    "9f80ca559630abe8800b3be2d14d39a3743a282d4c829fa9125af293bba3cb43"
}


def _schema_valid(value: dict[str, Any], schema_name: str) -> bool:
    try:
        from jsonschema import Draft202012Validator, FormatChecker

        schema_path = Path(__file__).resolve().parents[2] / "schemas" / schema_name
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    except Exception:
        return False
    return True


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _hex(value: Any, length: int) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_and_submit(
    *,
    manifest: dict[str, Any],
    gate_receipt: dict[str, Any],
    observed_subject_sha: str,
    checkout_clean: bool,
    output_exists: bool,
    execution_host: str,
    observed_associations: set[tuple[str, str]],
    observed_repo_path: str | None = None,
    runner: Callable[..., Any] = subprocess.run,
    submit: bool = False,
) -> dict[str, Any]:
    failures: list[str] = []
    demoted_authorized = bool(
        gate_receipt.get("schema_version") == "paper3-confirmatory-gate-result-v2"
        and gate_receipt.get("annotation_gate", {}).get("passed") is True
        and gate_receipt.get("expensive_training_authorized") is True
        and gate_receipt.get("gate_verdict") == "PASS_AUTHORIZE_DEMOTED_AI_OPERATOR_TRAIN"
        and gate_receipt.get("authority_class") == "DEMOTED_AI_OPERATOR"
        and gate_receipt.get("overall_cheap_gate_passed") is False
    )
    confirmatory_authorized = bool(
        gate_receipt.get("schema_version") == "paper3-confirmatory-gate-result-v2"
        and gate_receipt.get("annotation_gate", {}).get("passed") is True
        and gate_receipt.get("diagnostic_signal_gate", {}).get("passed") is True
        and gate_receipt.get("overall_cheap_gate_passed") is True
        and gate_receipt.get("expensive_training_authorized") is True
        and gate_receipt.get("gate_verdict") == "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
    )
    gate_passed = confirmatory_authorized or demoted_authorized
    if not gate_passed:
        failures.append("gate_receipt_not_authorized")
    if not _schema_valid(
        gate_receipt, "paper3-confirmatory-gate-result.schema.json"
    ):
        failures.append("gate_receipt_schema_invalid")
    if manifest.get("schema_version") != "paper3-lunarc-run-manifest-v1":
        failures.append("manifest_schema_mismatch")
    if not _schema_valid(manifest, "paper3-lunarc-run-manifest.schema.json"):
        failures.append("manifest_schema_invalid")
    subject_sha = manifest.get("subject_sha")
    if not _hex(subject_sha, 40) or subject_sha != observed_subject_sha:
        failures.append("subject_sha_mismatch")
    if gate_receipt.get("subject_sha") != subject_sha:
        failures.append("gate_subject_sha_mismatch")
    if manifest.get("gate_receipt_sha256") != canonical_sha256(gate_receipt):
        failures.append("gate_receipt_hash_mismatch")
    if manifest.get("protocol_sha256") != gate_receipt.get("protocol_sha256"):
        failures.append("gate_protocol_hash_mismatch")
    if manifest.get("benchmark_sha256") != gate_receipt.get("benchmark_sha256"):
        failures.append("gate_benchmark_hash_mismatch")
    lineage: dict[str, dict[str, Any]] = {}
    for artifact in ("protocol", "benchmark", "annotation_import_receipt"):
        artifact_path = Path(str(manifest.get(f"{artifact}_path", "")))
        if not artifact_path.is_absolute() or not artifact_path.is_file():
            failures.append(f"lineage_path_invalid:{artifact}")
            continue
        value = _load_json(artifact_path)
        expected_hash = manifest.get(f"{artifact}_sha256")
        if value is None or canonical_sha256(value) != expected_hash:
            failures.append(f"lineage_hash_mismatch:{artifact}")
            continue
        lineage[artifact] = value
    benchmark = lineage.get("benchmark", {})
    annotation_import = lineage.get("annotation_import_receipt", {})
    if benchmark and (
        benchmark.get("subject_sha") != subject_sha
        or benchmark.get("protocol_sha256") != manifest.get("protocol_sha256")
    ):
        failures.append("benchmark_lineage_mismatch")
    if annotation_import and (
        not _schema_valid(
            annotation_import, "paper3-annotation-import-receipt.schema.json"
        )
        or annotation_import.get("schema_version")
        != "paper3-annotation-import-receipt-v2"
        or annotation_import.get("subject_sha") != subject_sha
        or annotation_import.get("protocol_sha256") != manifest.get("protocol_sha256")
        or annotation_import.get("benchmark_sha256") != manifest.get("benchmark_sha256")
        or annotation_import.get("passed") is not True
        or annotation_import.get("training_authorized") is not False
        or annotation_import.get("failures") != []
    ):
        failures.append("annotation_import_lineage_mismatch")
    if not checkout_clean:
        failures.append("checkout_not_clean")
    if not execution_host.startswith("cosmos"):
        failures.append("not_running_on_lunarc_login_host")
    if manifest.get("workload") not in {"training", "inference"}:
        failures.append("unsupported_workload")
    for field in (
        "protocol_sha256",
        "benchmark_sha256",
        "task_set_sha256",
        "environment_sha256",
        "seed_schedule_sha256",
        "model_artifact_sha256",
    ):
        if not _hex(manifest.get(field), 64):
            failures.append(f"invalid_hash:{field}")
    if not isinstance(manifest.get("model_revision"), str) or re.fullmatch(
        r"[^@\s]+@[0-9a-f]{40}", manifest["model_revision"]
    ) is None:
        failures.append("model_revision_not_immutable")
    for artifact in ("task_set", "environment", "seed_schedule", "model_artifact"):
        artifact_path = Path(str(manifest.get(f"{artifact}_path", "")))
        if not artifact_path.is_absolute():
            failures.append(f"artifact_path_not_absolute:{artifact}")
        elif not artifact_path.is_file():
            failures.append(f"artifact_path_missing:{artifact}")
        elif hashlib.sha256(artifact_path.read_bytes()).hexdigest() != manifest.get(
            f"{artifact}_sha256"
        ):
            failures.append(f"artifact_hash_mismatch:{artifact}")
        else:
            artifact_value = _load_json(artifact_path)
            if (
                artifact_value is None
                or not _schema_valid(
                    artifact_value, "paper3-lunarc-bound-artifact.schema.json"
                )
                or artifact_value.get("artifact_type") != artifact
                or artifact_value.get("subject_sha") != subject_sha
                or (
                    artifact == "model_artifact"
                    and artifact_value.get("payload", {}).get("model_revision")
                    != manifest.get("model_revision")
                )
            ):
                failures.append(f"artifact_contract_invalid:{artifact}")
    account = manifest.get("account")
    partition = manifest.get("partition")
    if partition not in ALLOWED_PARTITIONS:
        failures.append("partition_not_registered_for_paper3")
    if (account, partition) not in observed_associations:
        failures.append("account_partition_association_missing")
    output_dir = manifest.get("fs9_output_dir")
    if not isinstance(output_dir, str):
        failures.append("fs9_output_outside_registered_root")
    else:
        output_path = PurePosixPath(output_dir)
        if ".." in output_path.parts or not output_path.is_absolute():
            failures.append("fs9_output_outside_registered_root")
        elif output_path.parent != FS9_ROOT:
            if FS9_ROOT not in output_path.parents:
                failures.append("fs9_output_outside_registered_root")
            else:
                failures.append("fs9_output_not_exactly_one_new_child")
    if output_exists:
        failures.append("fs9_output_already_exists")
    batch_script = Path(str(manifest.get("batch_script", "")))
    if batch_script.suffix != ".sbatch" or not batch_script.is_file():
        failures.append("batch_script_missing_or_not_sbatch")
    elif manifest.get("batch_script_sha256") != hashlib.sha256(
        batch_script.read_bytes()
    ).hexdigest():
        failures.append("batch_script_hash_mismatch")
    elif manifest.get("batch_script_sha256") not in ALLOWED_BATCH_SCRIPT_SHA256:
        failures.append("batch_script_not_allowlisted")
    repo_path = Path(str(manifest.get("repo_path", "")))
    if not repo_path.is_dir():
        failures.append("repo_path_missing")
    if observed_repo_path is None or repo_path.resolve() != Path(observed_repo_path).resolve():
        failures.append("repo_path_mismatch")
    manifest_path = Path(str(manifest.get("manifest_path", "")))
    gate_receipt_path = Path(str(manifest.get("gate_receipt_path", "")))
    if not manifest_path.is_file():
        failures.append("manifest_path_missing")
    else:
        try:
            observed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            observed_manifest = None
        if observed_manifest is None or canonical_sha256(observed_manifest) != canonical_sha256(manifest):
            failures.append("manifest_path_content_mismatch")
    if not gate_receipt_path.is_file():
        failures.append("gate_receipt_path_missing")
    else:
        try:
            observed_gate = json.loads(gate_receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            observed_gate = None
        if observed_gate is None or canonical_sha256(observed_gate) != canonical_sha256(gate_receipt):
            failures.append("gate_path_content_mismatch")

    failures = list(dict.fromkeys(failures))
    receipt = {
        "schema_version": "paper3-lunarc-preflight-receipt-v1",
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "manifest_sha256": canonical_sha256(manifest),
        "gate_receipt_sha256": canonical_sha256(gate_receipt),
        "subject_sha": subject_sha,
        "execution_host": execution_host,
        "account": account,
        "partition": partition,
        "fs9_output_dir": output_dir,
        "batch_script_sha256": manifest.get("batch_script_sha256"),
        "repo_path": manifest.get("repo_path"),
        "failures": failures,
        "submitted": False,
        "slurm_job_id": None,
    }
    if failures:
        receipt["verdict"] = (
            "REFUSE_GATE_CLOSED"
            if "gate_receipt_not_authorized" in failures
            else "REFUSE_PREFLIGHT_VALIDATION"
        )
        return receipt
    if not submit:
        receipt["verdict"] = "READY_NOT_SUBMITTED"
        return receipt

    export = (
        "ALL,"
        f"RAKL_EXPERIMENT_MANIFEST={manifest_path},"
        f"RAKL_GATE_RECEIPT={gate_receipt_path},"
        f"RAKL_EXPECTED_SUBJECT_SHA={subject_sha},"
        f"RAKL_EXPECTED_MANIFEST_SHA256={canonical_sha256(manifest)},"
        f"RAKL_EXPECTED_GATE_SHA256={canonical_sha256(gate_receipt)},"
        f"RAKL_REPO_PATH={repo_path}"
    )
    argv = [
        "sbatch",
        "--parsable",
        f"--account={account}",
        f"--partition={partition}",
        f"--export={export}",
        str(batch_script),
    ]
    receipt["sbatch_argv"] = argv
    try:
        completed = runner(
            argv,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
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


def _git_state(repo: Path) -> tuple[str, bool]:
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout
    return sha, not status.strip()


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
    gate_receipt = json.loads(args.gate_receipt.read_text(encoding="utf-8"))
    observed_sha, clean = _git_state(args.repo)
    associations = {
        tuple(value.split(":", 1))
        for value in args.association
        if ":" in value
    }
    output_dir = Path(str(manifest.get("fs9_output_dir", "")))
    receipt = validate_and_submit(
        manifest=manifest,
        gate_receipt=gate_receipt,
        observed_subject_sha=observed_sha,
        checkout_clean=clean,
        output_exists=output_dir.exists(),
        execution_host=socket.gethostname(),
        observed_associations=associations,
        observed_repo_path=str(args.repo.resolve()),
        submit=args.submit,
    )
    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.receipt_output)
    return 0 if receipt["verdict"] in {"READY_NOT_SUBMITTED", "SUBMITTED_AFTER_EXACT_GATE_PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
