from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

STAGING_USER_AGENT = "RAKL-Paper2-ModelStaging-V4.3"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    ).stdout.strip()


def _validate_repo(repo: Path, expected_repo_sha: str) -> list[str]:
    failures: list[str] = []
    try:
        if _git(repo, "rev-parse", "HEAD") != expected_repo_sha:
            failures.append("exact_checkout_head_mismatch")
        if _git(repo, "rev-parse", "refs/remotes/origin/main") != expected_repo_sha:
            failures.append("origin_main_sha_mismatch")
        if _git(repo, "status", "--porcelain", "--untracked-files=all"):
            failures.append("checkout_dirty")
        if _git(repo, "remote", "get-url", "origin") != "https://github.com/SzeChunYiu/RAKL.git":
            failures.append("origin_remote_mismatch")
    except subprocess.CalledProcessError:
        failures.append("git_identity_check_failed")
    return failures


def _artifacts(contract: Mapping[str, Any], repo: Path) -> list[dict[str, Any]]:
    manifest_path = repo / str(contract["asset_manifest_path"])
    manifest = _load_json(manifest_path)
    artifacts = list(manifest.get("artifacts") or [])
    if len(artifacts) != int(contract["expected_artifact_count"]):
        raise RuntimeError("artifact_count_mismatch")
    return artifacts


def network_probe(
    *,
    contract_path: Path,
    repo: Path,
    expected_repo_sha: str,
    receipt_output: Path,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    failures = _validate_repo(repo, expected_repo_sha)
    if not os.environ.get("SLURM_JOB_ID"):
        failures.append("not_inside_slurm_allocation")
    observations: list[dict[str, Any]] = []
    if not failures:
        for artifact in _artifacts(contract, repo):
            request = urllib.request.Request(
                str(artifact["url"]),
                method="HEAD",
                headers={"User-Agent": STAGING_USER_AGENT},
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    status = int(getattr(response, "status", 200) or 200)
                    ok = 200 <= status < 400
                    observations.append(
                        {
                            "artifact_id": artifact["artifact_id"],
                            "ok": ok,
                            "http_status": status,
                            "error_type": None,
                        }
                    )
            except Exception as exc:  # noqa: BLE001 - preserve typed failure
                status = getattr(exc, "code", None)
                observations.append(
                    {
                        "artifact_id": artifact["artifact_id"],
                        "ok": False,
                        "http_status": int(status) if isinstance(status, int) else None,
                        "error_type": type(exc).__name__,
                    }
                )
        if not observations or not all(row["ok"] for row in observations):
            failures.append("network_probe_incomplete")
    receipt = {
        "schema_version": "paper2-model-staging-network-probe-receipt-v4-3",
        "created_at_utc": _now(),
        "verdict": "NETWORK_PROBE_PASS" if not failures else "NETWORK_PROBE_FAIL",
        "expected_repo_sha": expected_repo_sha,
        "contract_id": contract.get("contract_id"),
        "contract_sha256": _sha256(contract_path),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "observations": observations,
        "failures": failures,
        "model_execution_performed": False,
        "claim_boundary": "HEAD-only reachability for frozen model URLs; no download or inference.",
    }
    _atomic_write_json(receipt_output, receipt)
    return receipt


def stage_assets(
    *,
    contract_path: Path,
    repo: Path,
    expected_repo_sha: str,
    probe_receipt: Path,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    failures = _validate_repo(repo, expected_repo_sha)
    job_id = os.environ.get("SLURM_JOB_ID")
    if not job_id:
        failures.append("not_inside_slurm_allocation")
    runtime_python = Path(str(contract["runtime_python"]))
    if not runtime_python.is_file():
        failures.append("reuse_runtime_python_missing")
    final_root = Path(str(contract["final_root"]))
    candidate_root = Path(str(contract["candidate_root"]))
    failure_root = Path(str(contract["failure_root"]))
    if final_root.exists():
        failures.append("final_root_already_exists")
    if candidate_root.exists():
        failures.append("candidate_root_already_exists")
    probe = _load_json(probe_receipt) if probe_receipt.is_file() else {}
    if probe.get("verdict") != "NETWORK_PROBE_PASS":
        failures.append("probe_receipt_not_pass")
    if probe.get("expected_repo_sha") != expected_repo_sha:
        failures.append("probe_repo_sha_mismatch")
    if str(probe.get("slurm_job_id") or "") != str(os.environ.get("RAKL_PROBE_JOB_ID") or ""):
        failures.append("probe_job_id_mismatch")
    observed: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "schema_version": "paper2-model-staging-result-receipt-v4-3",
        "created_at_utc": _now(),
        "verdict": "STAGING_FAIL",
        "expected_repo_sha": expected_repo_sha,
        "contract_id": contract.get("contract_id"),
        "contract_sha256": _sha256(contract_path),
        "slurm_job_id": job_id,
        "probe_job_id": os.environ.get("RAKL_PROBE_JOB_ID"),
        "final_root": str(final_root),
        "candidate_root": str(candidate_root),
        "runtime_python": str(runtime_python),
        "observed_files": observed,
        "failures": list(failures),
        "model_execution_performed": False,
        "claim_boundary": "Model-only overlay staging; reuses V3.2 runtime; no inference.",
    }
    if failures:
        failure_root.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(failure_root / f"staging-{job_id or 'unknown'}.json", receipt)
        return receipt

    candidate_root.mkdir(parents=False, exist_ok=False)
    try:
        for artifact in _artifacts(contract, repo):
            destination = candidate_root / str(artifact["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.download")
            request = urllib.request.Request(
                str(artifact["url"]),
                method="GET",
                headers={"User-Agent": STAGING_USER_AGENT},
            )
            with urllib.request.urlopen(request, timeout=1800) as response, temporary.open(
                "wb"
            ) as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            temporary.replace(destination)
            observed_bytes = destination.stat().st_size
            observed_sha = _sha256(destination)
            observed.append(
                {
                    "artifact_id": artifact["artifact_id"],
                    "path": artifact["destination"],
                    "bytes": observed_bytes,
                    "sha256": observed_sha,
                }
            )
            if observed_bytes != int(artifact["bytes"]) or observed_sha != artifact["sha256"]:
                failures.append(f"artifact_mismatch:{artifact['artifact_id']}")
        if failures:
            raise RuntimeError("artifact_verification_failed")
        final_root.parent.mkdir(parents=True, exist_ok=True)
        receipt.update(
            {
                "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
                "observed_files": observed,
                "failures": [],
            }
        )
        pass_receipt = candidate_root / "STAGING_PASS_RECEIPT.json"
        _atomic_write_json(pass_receipt, receipt)
        candidate_root.replace(final_root)
        _atomic_write_json(final_root / "STAGING_PASS_RECEIPT.json", receipt)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"staging_exception:{type(exc).__name__}")
        receipt["failures"] = list(dict.fromkeys([*receipt.get("failures", []), *failures]))
        receipt["verdict"] = "STAGING_FAIL"
        failure_root.mkdir(parents=True, exist_ok=True)
        preserved = failure_root / f"candidate-{job_id}"
        if candidate_root.exists() and not preserved.exists():
            candidate_root.rename(preserved)
            receipt["preserved_candidate_path"] = str(preserved)
        _atomic_write_json(failure_root / f"staging-{job_id}.json", receipt)
        return receipt
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paper2_model_staging_v4_3")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("network-probe")
    probe.add_argument("--contract", type=Path, required=True)
    probe.add_argument("--repo", type=Path, required=True)
    probe.add_argument("--expected-repo-sha", required=True)
    probe.add_argument("--receipt-output", type=Path, required=True)

    stage = sub.add_parser("stage-assets")
    stage.add_argument("--contract", type=Path, required=True)
    stage.add_argument("--repo", type=Path, required=True)
    stage.add_argument("--expected-repo-sha", required=True)
    stage.add_argument("--probe-receipt", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "network-probe":
        receipt = network_probe(
            contract_path=args.contract.resolve(),
            repo=args.repo.resolve(),
            expected_repo_sha=args.expected_repo_sha,
            receipt_output=args.receipt_output.resolve(),
        )
        return 0 if receipt.get("verdict") == "NETWORK_PROBE_PASS" else 2
    if args.command == "stage-assets":
        receipt = stage_assets(
            contract_path=args.contract.resolve(),
            repo=args.repo.resolve(),
            expected_repo_sha=args.expected_repo_sha,
            probe_receipt=args.probe_receipt.resolve(),
        )
        return 0 if receipt.get("verdict") == "STAGING_PASS_ATOMICALLY_PROMOTED" else 2
    raise SystemExit(f"unknown command:{args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
