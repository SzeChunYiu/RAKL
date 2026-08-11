#!/usr/bin/env python3
"""Shared fail-closed helpers for the Paper 3 semantic-descriptor jobs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ORIGIN = "https://github.com/SzeChunYiu/RAKL.git"
FS9_ROOT = Path("/projects/hep/fs9/users/scyiu/RAKL-paper3")
ACCOUNT = "lu2026-2-51"
PARTITION = "lu48"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("expected_utc_timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    """Content digest a runtime tree so a shared environment cannot mutate silently."""

    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(str(path.stat().st_size).encode("ascii") + b"\0")
        digest.update(file_sha256(path).encode("ascii") + b"\n")
    return digest.hexdigest()


def validate_schema(value: dict[str, Any], schema_path: Path) -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).validate(value)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def command(repo: Path, *argv: str) -> str:
    return subprocess.run(
        argv,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()


def validate_repo_and_contract(
    *, repo: Path, contract_path: Path, expected_repo_sha: str
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    try:
        contract = load_json(contract_path)
    except Exception:
        return {}, ["contract_unreadable"]
    contract_schema = repo / "schemas/paper3-semantic-lunarc-contract-v1.schema.json"
    try:
        validate_schema(contract, contract_schema)
    except Exception:
        failures.append("contract_schema_invalid")
    try:
        observed = command(repo, "git", "rev-parse", "HEAD")
        if observed != expected_repo_sha:
            failures.append("exact_checkout_sha_mismatch")
        origin_main = command(repo, "git", "rev-parse", "refs/remotes/origin/main")
        if origin_main != expected_repo_sha:
            failures.append("origin_main_sha_mismatch")
        if command(repo, "git", "status", "--porcelain", "--untracked-files=all"):
            failures.append("checkout_dirty")
        if command(repo, "git", "remote", "get-url", "origin") != ORIGIN:
            failures.append("origin_mismatch")
        parent = str(contract.get("frozen_parent_sha", ""))
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", parent, expected_repo_sha],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if ancestor.returncode != 0:
            failures.append("frozen_parent_not_ancestor")
    except Exception:
        failures.append("git_state_unreadable")
    for binding in contract.get("bindings", []):
        path = repo / str(binding.get("path", ""))
        if not path.is_file():
            failures.append(f"binding_missing:{binding.get('role')}")
        elif file_sha256(path) != binding.get("sha256"):
            failures.append(f"binding_sha256_mismatch:{binding.get('role')}")
    return contract, list(dict.fromkeys(failures))


def inspect_model_files(
    model_dir: Path, expected_files: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    observed: list[dict[str, Any]] = []
    failures: list[str] = []
    for expected in expected_files:
        relative = str(expected["path"])
        path = model_dir / relative
        if not path.is_file():
            failures.append(f"model_asset_missing:{relative}")
            continue
        row = {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        observed.append(row)
        if row["bytes"] != expected["bytes"]:
            failures.append(f"model_asset_size_mismatch:{relative}")
        if row["sha256"] != expected["sha256"]:
            failures.append(f"model_asset_sha256_mismatch:{relative}")
    return observed, failures


def root_sacct_row(
    value: dict[str, Any], job_id: str
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    rows = value.get("jobs")
    if not isinstance(rows, list):
        return None, ["sacct_jobs_missing"]
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("job_id")) == job_id
    ]
    if len(matches) != 1:
        return None, ["sacct_root_job_not_unique"]
    row = matches[0]
    state = row.get("state")
    states = state.get("current") if isinstance(state, dict) else None
    if states != ["COMPLETED"]:
        failures.append("slurm_root_not_completed")
    exit_code = row.get("exit_code")
    status = exit_code.get("status") if isinstance(exit_code, dict) else None
    return_code = exit_code.get("return_code") if isinstance(exit_code, dict) else None
    if not isinstance(return_code, dict) or return_code.get("set") is not True:
        failures.append("slurm_root_exit_unset")
    number = return_code.get("number") if isinstance(return_code, dict) else None
    if status != ["SUCCESS"] or number != 0:
        failures.append("slurm_root_exit_nonzero")
    if row.get("account") != ACCOUNT:
        failures.append("slurm_root_account_mismatch")
    if row.get("partition") != PARTITION:
        failures.append("slurm_root_partition_mismatch")
    time = row.get("time")
    elapsed = time.get("elapsed") if isinstance(time, dict) else None
    if not isinstance(elapsed, int) or elapsed < 0:
        failures.append("slurm_root_elapsed_invalid")
    return row, failures


def validate_label_chronology(
    value: dict[str, Any], *, descriptor_created_at_utc: str
) -> list[str]:
    """Validate a payload-free chronology observation against one descriptor."""

    failures: list[str] = []
    try:
        descriptor_at = parse_utc(descriptor_created_at_utc)
        observation_at = parse_utc(value.get("created_at_utc"))
    except (TypeError, ValueError):
        return ["label_chronology_timestamp_invalid"]
    counts = value.get("counts")
    if not isinstance(counts, dict):
        failures.append("label_chronology_counts_invalid")
        counts = {}
    if value.get("label_payload_accessed") is not False:
        failures.append("label_chronology_payload_accessed")
    state = value.get("state")
    first_label = value.get("first_external_label_at_utc")
    if state == "ZERO_LABELS_OBSERVED":
        if first_label is not None or any(
            counts.get(key) != 0
            for key in ("external_annotations", "adjudications", "evaluated_results")
        ):
            failures.append("zero_label_observation_counts_invalid")
        if observation_at <= descriptor_at:
            failures.append("zero_label_observation_not_after_descriptor")
    elif state == "FIRST_LABEL_RECORDED":
        try:
            first_label_at = parse_utc(first_label)
        except (TypeError, ValueError):
            failures.append("first_external_label_timestamp_invalid")
        else:
            if descriptor_at >= first_label_at:
                failures.append("descriptor_not_before_first_external_label")
        if counts.get("external_annotations", 0) < 1:
            failures.append("first_label_count_invalid")
    else:
        failures.append("label_chronology_state_invalid")
    return list(dict.fromkeys(failures))
