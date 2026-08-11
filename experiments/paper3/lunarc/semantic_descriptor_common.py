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


def root_sacct_row(value: dict[str, Any], job_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    rows = value.get("jobs")
    if not isinstance(rows, list):
        return None, ["sacct_jobs_missing"]
    matches = [row for row in rows if str(row.get("job_id")) == job_id]
    if len(matches) != 1:
        return None, ["sacct_root_job_not_unique"]
    row = matches[0]
    states = row.get("state", {}).get("current", [])
    if states != ["COMPLETED"]:
        failures.append("slurm_root_not_completed")
    status = row.get("exit_code", {}).get("status", [])
    number = row.get("exit_code", {}).get("return_code", {}).get("number")
    if status != ["SUCCESS"] or number != 0:
        failures.append("slurm_root_exit_nonzero")
    return row, failures
