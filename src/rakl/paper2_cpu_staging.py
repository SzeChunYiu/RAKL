from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
from typing import Any, Callable, Mapping
import urllib.request


_EXPECTED_RUNTIME = {
    "torch": "2.8.0+cpu",
    "transformers": "4.55.0",
    "tokenizers": "0.21.4",
    "safetensors": "0.6.2",
}
_EXPECTED_PYTHON = {
    "filename": "cpython-3.11.13+20250604-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "bytes": 48610589,
    "sha256": "13f898a7ac7a54e97d3efd6a958ef5e16e9329bd9639b03fc95146227d18706c",
}
_EXPECTED_WHEEL_LOCK_SHA256 = "e06c27464d15b46617b1b8c8f79544f6173267b080189257b2d0e28d006afff3"
_EXPECTED_REQUIREMENTS_SHA256 = "291752036b264369795967b2599ca401a1707750a213b0992c2ef4a3b55c87b0"
FS9_ROOT = PurePosixPath("/projects/hep/fs9/users/scyiu/RAKL-paper2")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _hex(value: object, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(c in "0123456789abcdef" for c in value)


def _bound_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def validate_staging_manifest(
    manifest: Mapping[str, object], *, repository_root: Path
) -> tuple[str, ...]:
    failures: list[str] = []
    if manifest.get("schema_version") != "paper2-cpu-staging-asset-manifest-v3":
        failures.append("asset_manifest_schema_invalid")
    if manifest.get("authority_status") != "frozen_proposal_before_any_lunarc_submission":
        failures.append("asset_manifest_authority_invalid")
    if manifest.get("execution_performed") is not False or manifest.get("model_execution_performed") is not False:
        failures.append("asset_manifest_execution_state_invalid")
    if manifest.get("required_runtime_versions") != _EXPECTED_RUNTIME:
        for name, version in _EXPECTED_RUNTIME.items():
            if not isinstance(manifest.get("required_runtime_versions"), Mapping) or manifest["required_runtime_versions"].get(name) != version:
                failures.append(f"runtime_version_mismatch:{name}")
    target = manifest.get("target")
    if not isinstance(target, Mapping) or target.get("python") != "3.11.13" or target.get("os") != "Linux" or target.get("architecture") != "x86_64":
        failures.append("target_platform_invalid")
    wheel_binding = manifest.get("wheel_lock")
    wheel_lock: dict[str, Any] = {}
    if not isinstance(wheel_binding, Mapping):
        failures.append("wheel_lock_binding_missing")
    else:
        if wheel_binding.get("sha256") != _EXPECTED_WHEEL_LOCK_SHA256:
            failures.append("wheel_lock_expected_hash_mismatch")
        if wheel_binding.get("requirements_sha256") != _EXPECTED_REQUIREMENTS_SHA256:
            failures.append("requirements_expected_hash_mismatch")
        if wheel_binding.get("offline_install_required") is not True or wheel_binding.get("unconstrained_resolution_permitted") is not False:
            failures.append("offline_lock_policy_invalid")
        wheel_path = _bound_path(repository_root, wheel_binding.get("path"))
        requirements_path = _bound_path(repository_root, wheel_binding.get("requirements_path"))
        if wheel_path is None or not wheel_path.is_file() or _sha256(wheel_path) != wheel_binding.get("sha256"):
            failures.append("wheel_lock_file_mismatch")
        else:
            try:
                wheel_lock = json.loads(wheel_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                failures.append("wheel_lock_json_invalid")
        if requirements_path is None or not requirements_path.is_file() or _sha256(requirements_path) != wheel_binding.get("requirements_sha256"):
            failures.append("requirements_lock_file_mismatch")
    wheels = wheel_lock.get("wheels", []) if isinstance(wheel_lock, dict) else []
    if len(wheels) != 29 or wheel_lock.get("wheel_count") != 29 or wheel_lock.get("total_bytes") != 233304796:
        failures.append("wheel_lock_cardinality_or_bytes_invalid")
    torch = [w for w in wheels if isinstance(w, Mapping) and w.get("name") == "torch"]
    if len(torch) != 1 or torch[0].get("version") != "2.8.0+cpu" or torch[0].get("requirement") != "torch==2.8.0+cpu":
        failures.append("torch_cpu_equality_not_exact")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        failures.append("artifacts_missing")
        artifacts = []
    ids: list[object] = []
    destinations: list[object] = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            failures.append(f"artifact_invalid:{index}")
            continue
        ids.append(artifact.get("artifact_id"))
        destinations.append(artifact.get("destination"))
        if not _hex(artifact.get("sha256"), 64):
            failures.append("artifact_sha256_invalid")
        if not isinstance(artifact.get("bytes"), int) or int(artifact["bytes"]) < 1:
            failures.append("artifact_bytes_invalid")
        if not isinstance(artifact.get("url"), str) or not str(artifact["url"]).startswith("https://"):
            failures.append("artifact_url_invalid")
        destination = PurePosixPath(str(artifact.get("destination", "")))
        if destination.is_absolute() or ".." in destination.parts or not destination.parts:
            failures.append("artifact_destination_invalid")
    if len(set(ids)) != len(ids):
        failures.append("artifact_id_duplicate")
    if len(set(destinations)) != len(destinations):
        failures.append("artifact_destination_duplicate")
    if manifest.get("artifact_count") != len(artifacts):
        failures.append("artifact_count_mismatch")
    if manifest.get("total_download_bytes") != sum(int(a.get("bytes", 0)) for a in artifacts if isinstance(a, Mapping)):
        failures.append("artifact_total_bytes_mismatch")
    python = [a for a in artifacts if isinstance(a, Mapping) and a.get("role") == "python_archive"]
    if len(python) != 1 or any(python[0].get(k) != v for k, v in _EXPECTED_PYTHON.items()):
        failures.append("python_archive_identity_invalid")
    wheel_artifacts = {a.get("filename"): a for a in artifacts if isinstance(a, Mapping) and a.get("role") == "wheel"}
    for wheel in wheels:
        if not isinstance(wheel, Mapping):
            failures.append("wheel_lock_entry_invalid")
            continue
        artifact = wheel_artifacts.get(wheel.get("filename"))
        if artifact is None or any(artifact.get(field) != wheel.get(field) for field in ("url", "bytes", "sha256")):
            failures.append(f"wheel_artifact_mismatch:{wheel.get('name')}")
    if len(wheel_artifacts) != 29:
        failures.append("wheel_artifact_count_invalid")
    if sum(isinstance(a, Mapping) and a.get("role") == "model_snapshot" for a in artifacts) != 8:
        failures.append("model_snapshot_artifact_count_invalid")
    return tuple(dict.fromkeys(failures))


def validate_staging_contract(
    contract: Mapping[str, object], *, repository_root: Path
) -> tuple[str, ...]:
    failures: list[str] = []
    if contract.get("schema_version") != "paper2-cpu-staging-contract-v3":
        failures.append("contract_schema_invalid")
    if contract.get("model_execution_permitted") is not False:
        failures.append("model_execution_must_be_forbidden")
    bootstrap = contract.get("bootstrap_policy")
    if (
        not isinstance(bootstrap, Mapping)
        or bootstrap.get("exact_repo_sha_required") is not True
        or bootstrap.get("successful_bootstrap_receipt_required_before_submission") is not True
        or bootstrap.get("existing_repo_never_silently_mutated") is not True
    ):
        failures.append("bootstrap_policy_invalid")
    submission = contract.get("submission_policy")
    if not isinstance(submission, Mapping) or submission.get("exact_repo_sha_required") is not True or submission.get("network_probe_must_precede_staging") is not True:
        failures.append("submission_policy_invalid")
    promotion = contract.get("promotion_policy")
    if not isinstance(promotion, Mapping) or promotion.get("atomic_rename_required") is not True:
        failures.append("atomic_promotion_policy_missing")
    failure_policy = contract.get("failure_policy")
    if not isinstance(failure_policy, Mapping) or failure_policy.get("preserve_failed_candidate_and_receipt") is not True:
        failures.append("failure_preservation_policy_missing")
    staging_attestation = contract.get("staging_attestation_policy")
    if (
        not isinstance(staging_attestation, Mapping)
        or staging_attestation.get("torch_version") != "2.8.0+cpu"
        or staging_attestation.get("torch_cuda_must_be_null") is not True
        or staging_attestation.get("tensor_device") != "cpu"
        or not isinstance(staging_attestation.get("minimum_free_bytes"), int)
        or int(staging_attestation.get("minimum_free_bytes", 0)) < 6_000_000_000
    ):
        failures.append("staging_attestation_policy_invalid")
    for field in ("fs9_root", "candidate_root", "final_root", "receipt_root", "failure_root"):
        raw = contract.get(field)
        if not isinstance(raw, str):
            failures.append(f"contract_path_invalid:{field}")
            continue
        path = PurePosixPath(raw)
        if not path.is_absolute() or ".." in path.parts or FS9_ROOT not in (path, *path.parents):
            failures.append(f"contract_path_invalid:{field}")
    candidate_root = contract.get("candidate_root")
    final_root = contract.get("final_root")
    if isinstance(candidate_root, str) and isinstance(final_root, str):
        if PurePosixPath(candidate_root).parent != PurePosixPath(final_root).parent:
            failures.append("promotion_paths_not_same_parent")
    bindings = contract.get("bindings")
    if not isinstance(bindings, list):
        failures.append("contract_bindings_missing")
        bindings = []
    roles: list[object] = []
    asset_manifest: dict[str, Any] | None = None
    for binding in bindings:
        if not isinstance(binding, Mapping):
            failures.append("contract_binding_invalid")
            continue
        roles.append(binding.get("role"))
        path = _bound_path(repository_root, binding.get("path"))
        if path is None or not path.is_file():
            failures.append(f"contract_binding_missing:{binding.get('role')}")
        elif not _hex(binding.get("sha256"), 64) or _sha256(path) != binding.get("sha256"):
            failures.append(f"contract_binding_hash_mismatch:{binding.get('role')}")
        elif binding.get("role") == "asset_manifest":
            try:
                asset_manifest = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                failures.append("asset_manifest_json_invalid")
    required_roles = {
        "asset_manifest", "wheel_lock", "requirements_lock", "network_probe_batch",
        "staging_batch", "submission_script", "harvest_script", "staging_runtime",
        "repo_bootstrap_script", "contract_schema", "construction_receipt_schema",
    }
    if not required_roles <= set(roles):
        failures.append("contract_required_binding_missing")
    if len(roles) != len(set(roles)):
        failures.append("contract_binding_role_duplicate")
    if asset_manifest is not None:
        failures.extend(validate_staging_manifest(asset_manifest, repository_root=repository_root))
    return tuple(dict.fromkeys(failures))


@dataclass(frozen=True)
class SubmissionObservation:
    observed_repo_sha: str
    checkout_clean: bool
    execution_host: str
    observed_associations: frozenset[tuple[str, str]]


def _binding_path(contract: Mapping[str, object], role: str, root: Path) -> Path:
    for binding in contract.get("bindings", []):
        if isinstance(binding, Mapping) and binding.get("role") == role:
            path = _bound_path(root, binding.get("path"))
            if path is not None:
                return path
    raise ValueError(f"missing binding:{role}")


def build_submission_receipt(
    *,
    contract: Mapping[str, object],
    repository_root: Path,
    expected_repo_sha: str,
    observation: SubmissionObservation,
    account: str,
    partition: str,
    submit: bool,
    bootstrap_receipt_path: Path | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    failures = list(validate_staging_contract(contract, repository_root=repository_root))
    if not _hex(expected_repo_sha, 40) or observation.observed_repo_sha != expected_repo_sha:
        failures.append("repo_sha_mismatch")
    if not observation.checkout_clean:
        failures.append("checkout_not_clean")
    if not observation.execution_host.startswith("cosmos"):
        failures.append("submission_not_on_lunarc_login_host")
    if (account, partition) not in observation.observed_associations:
        failures.append("account_partition_association_missing")
    bootstrap_sha256: str | None = None
    bootstrap: dict[str, Any] = {}
    if bootstrap_receipt_path is None or not bootstrap_receipt_path.is_file():
        failures.append("bootstrap_receipt_missing")
    else:
        try:
            loaded = json.loads(bootstrap_receipt_path.read_text(encoding="utf-8"))
            bootstrap = loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError):
            failures.append("bootstrap_receipt_invalid")
        else:
            bootstrap_sha256 = _sha256(bootstrap_receipt_path)
            if bootstrap.get("verdict") not in {
                "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
                "BOOTSTRAP_PASS_ATOMICALLY_PROMOTED",
            } or bootstrap.get("exit_status") != 0:
                failures.append("bootstrap_receipt_not_successful")
            if (
                bootstrap.get("expected_repo_sha") != expected_repo_sha
                or bootstrap.get("observed_repo_sha") != expected_repo_sha
            ):
                failures.append("bootstrap_receipt_repo_sha_mismatch")
            if Path(str(bootstrap.get("repo_path", ""))).resolve() != repository_root.resolve():
                failures.append("bootstrap_receipt_repo_path_mismatch")
            if bootstrap.get("checkout_clean") is not True or bootstrap.get("detached_head") is not True:
                failures.append("bootstrap_receipt_checkout_attestation_invalid")
            if bootstrap.get("jobs_submitted") != 0 or bootstrap.get("model_execution_performed") is not False:
                failures.append("bootstrap_receipt_scope_invalid")
    contract_sha = _canonical_sha256(contract)
    receipt: dict[str, Any] = {
        "schema_version": "paper2-cpu-staging-submission-receipt-v3",
        "created_at_utc": _now(),
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_repo_sha,
        "observed_repo_sha": observation.observed_repo_sha,
        "execution_host": observation.execution_host,
        "account": account,
        "partition": partition,
        "bootstrap_receipt_path": str(bootstrap_receipt_path) if bootstrap_receipt_path else None,
        "bootstrap_receipt_sha256": bootstrap_sha256,
        "failures": list(dict.fromkeys(failures)),
        "submitted_job_ids": [],
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
        "failure_history_preserved": True,
    }
    if receipt["failures"]:
        receipt["verdict"] = "REFUSE_PREFLIGHT_VALIDATION"
        return receipt
    contract_path = _binding_path(contract, "contract_self", repository_root) if any(
        isinstance(b, Mapping) and b.get("role") == "contract_self" for b in contract.get("bindings", [])
    ) else repository_root / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3.json"
    probe_script = _binding_path(contract, "network_probe_batch", repository_root)
    stage_script = _binding_path(contract, "staging_batch", repository_root)
    common_export = (
        "ALL,"
        f"RAKL_STAGING_CONTRACT={contract_path},"
        f"RAKL_EXPECTED_REPO_SHA={expected_repo_sha},"
        f"RAKL_REPO_PATH={repository_root}"
    )
    probe_argv = [
        "sbatch", "--parsable", f"--account={account}", f"--partition={partition}",
        f"--export={common_export}", str(probe_script),
    ]
    planned_stage = [
        "sbatch", "--parsable", f"--account={account}", f"--partition={partition}",
        "--dependency=afterok:<PROBE_JOB_ID>", f"--export={common_export},RAKL_PROBE_JOB_ID=<PROBE_JOB_ID>",
        str(stage_script),
    ]
    receipt["planned_sbatch_argv"] = [probe_argv, planned_stage]
    if not submit:
        receipt["verdict"] = "READY_NOT_SUBMITTED"
        return receipt
    try:
        probe_result = runner(probe_argv, capture_output=True, text=True, check=True, shell=False)
        probe_id = str(probe_result.stdout).strip().split(";", 1)[0]
        if not probe_id.isdigit():
            raise ValueError("invalid probe job id")
    except Exception as exc:
        receipt["failures"] = ["network_probe_submission_failed"]
        receipt["submission_error_type"] = type(exc).__name__
        receipt["verdict"] = "SUBMISSION_FAILURE"
        return receipt
    receipt["submitted_job_ids"].append(probe_id)
    stage_argv = [
        "sbatch", "--parsable", f"--account={account}", f"--partition={partition}",
        f"--dependency=afterok:{probe_id}",
        f"--export={common_export},RAKL_PROBE_JOB_ID={probe_id}", str(stage_script),
    ]
    try:
        stage_result = runner(stage_argv, capture_output=True, text=True, check=True, shell=False)
        stage_id = str(stage_result.stdout).strip().split(";", 1)[0]
        if not stage_id.isdigit():
            raise ValueError("invalid staging job id")
    except Exception as exc:
        receipt["failures"] = ["staging_submission_failed"]
        receipt["submission_error_type"] = type(exc).__name__
        receipt["verdict"] = "PARTIAL_SUBMISSION_FAILURE"
        receipt["executed_sbatch_argv"] = [probe_argv, stage_argv]
        return receipt
    receipt["submitted_job_ids"].append(stage_id)
    receipt["executed_sbatch_argv"] = [probe_argv, stage_argv]
    receipt["verdict"] = "SUBMITTED_TWO_PHASE_STAGING"
    return receipt


def _git_observation(repo: Path) -> tuple[str, bool]:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True, shell=False).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo, capture_output=True, text=True, check=True, shell=False).stdout
    return sha, not status.strip()


def _load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("contract must be an object")
    return value


def run_network_probe(*, contract: Mapping[str, object], repository_root: Path, expected_repo_sha: str, receipt_output: Path) -> dict[str, Any]:
    failures = list(validate_staging_contract(contract, repository_root=repository_root))
    observed_sha, clean = _git_observation(repository_root)
    if observed_sha != expected_repo_sha:
        failures.append("repo_sha_mismatch")
    if not clean:
        failures.append("checkout_not_clean")
    manifest_path = _binding_path(contract, "asset_manifest", repository_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observations = []
    if not failures:
        for artifact in manifest["artifacts"]:
            request = urllib.request.Request(artifact["url"], method="HEAD", headers={"User-Agent": "RAKL-Paper2-Staging-V3/1"})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    observations.append({"artifact_id": artifact["artifact_id"], "http_status": response.status, "reachable": 200 <= response.status < 400})
            except Exception as exc:
                observations.append({"artifact_id": artifact["artifact_id"], "http_status": None, "reachable": False, "error_type": type(exc).__name__})
                failures.append(f"network_probe_failed:{artifact['artifact_id']}")
    receipt = {
        "schema_version": "paper2-cpu-staging-network-probe-receipt-v3",
        "created_at_utc": _now(), "contract_canonical_sha256": _canonical_sha256(contract),
        "expected_repo_sha": expected_repo_sha, "observed_repo_sha": observed_sha,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "observations": observations,
        "failures": list(dict.fromkeys(failures)), "model_execution_performed": False,
        "verdict": "NETWORK_PROBE_PASS" if not failures else "NETWORK_PROBE_FAIL",
    }
    _atomic_json(receipt_output, receipt)
    return receipt


def _safe_extract(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, "r:gz") as bundle:
        root = destination.resolve()
        for member in bundle.getmembers():
            member_path = PurePosixPath(member.name)
            if (
                member_path.is_absolute()
                or ".." in member_path.parts
                or member.issym()
                or member.islnk()
                or member.isdev()
                or member.isfifo()
                or not (member.isdir() or member.isfile())
            ):
                raise ValueError(f"archive unsafe member:{member.name}")
            target = (destination / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"archive unsafe member:{member.name}") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = bundle.extractfile(member)
            if source is None:
                raise ValueError(f"archive unsafe member:{member.name}")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            target.chmod(member.mode & 0o755)


def _git_attestation(repo: Path, construction_parent_sha: str) -> dict[str, object]:
    observed_sha, clean = _git_observation(repo)
    tree_sha = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", construction_parent_sha, observed_sha],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    ).returncode == 0
    return {
        "repo_sha": observed_sha,
        "repo_tree_sha": tree_sha,
        "checkout_clean": clean,
        "construction_parent_sha": construction_parent_sha,
        "construction_parent_ancestor": ancestor,
    }


def _commit_staging_candidate(candidate: Path, final: Path, receipt: Mapping[str, object]) -> None:
    """Write the commit record before rename; successful rename is the terminal operation.

    The pass verdict is authoritative only when harvested at ``final/staging_receipt.json``.
    If rename fails, the candidate and its conditional commit record remain preserved and the
    caller records a separate negative receipt.
    """

    _atomic_json(candidate / "staging_receipt.json", receipt)
    candidate.replace(final)


def _stage_assets_impl(*, contract: Mapping[str, object], repository_root: Path, expected_repo_sha: str, probe_receipt_path: Path) -> dict[str, Any]:
    failures = list(validate_staging_contract(contract, repository_root=repository_root))
    repo_attestation = _git_attestation(repository_root, str(contract.get("construction_parent_sha", "")))
    if repo_attestation["repo_sha"] != expected_repo_sha:
        failures.append("repo_sha_mismatch")
    if not repo_attestation["checkout_clean"]:
        failures.append("checkout_not_clean")
    if not repo_attestation["construction_parent_ancestor"]:
        failures.append("construction_parent_not_ancestor")
    try:
        probe = json.loads(probe_receipt_path.read_text(encoding="utf-8"))
    except Exception:
        probe = {}
    manifest = json.loads(_binding_path(contract, "asset_manifest", repository_root).read_text(encoding="utf-8"))
    expected_artifact_ids = {str(item["artifact_id"]) for item in manifest["artifacts"]}
    probe_job_id = os.environ.get("RAKL_PROBE_JOB_ID")
    observations = probe.get("observations")
    observed_ids = [str(item.get("artifact_id")) for item in observations if isinstance(item, Mapping)] if isinstance(observations, list) else []
    probe_observations_valid = bool(
        isinstance(observations, list)
        and len(observations) == len(expected_artifact_ids) == 38
        and len(observed_ids) == len(set(observed_ids))
        and set(observed_ids) == expected_artifact_ids
        and all(
            isinstance(item, Mapping)
            and item.get("reachable") is True
            and isinstance(item.get("http_status"), int)
            and 200 <= int(item["http_status"]) < 400
            for item in observations
        )
    )
    if (
        probe.get("verdict") != "NETWORK_PROBE_PASS"
        or probe.get("contract_canonical_sha256") != _canonical_sha256(contract)
        or not probe_job_id
        or str(probe.get("slurm_job_id")) != probe_job_id
        or probe.get("expected_repo_sha") != expected_repo_sha
        or probe.get("observed_repo_sha") != expected_repo_sha
        or not probe_observations_valid
    ):
        failures.append("network_probe_receipt_invalid")
    candidate = Path(str(contract["candidate_root"]) + f"-{os.environ.get('SLURM_JOB_ID', 'NOJOB')}")
    final = Path(str(contract["final_root"]))
    failure_root = Path(str(contract["failure_root"]))
    disk = shutil.disk_usage(Path(str(contract["fs9_root"])))
    minimum_free_bytes = int(contract.get("staging_attestation_policy", {}).get("minimum_free_bytes", 0)) if isinstance(contract.get("staging_attestation_policy"), Mapping) else 0
    if disk.free < minimum_free_bytes:
        failures.append("insufficient_fs9_free_bytes")
    if candidate.exists() or final.exists():
        failures.append("candidate_or_final_already_exists")
    if failures:
        receipt = {"schema_version":"paper2-cpu-staging-result-receipt-v3","created_at_utc":_now(),"contract_canonical_sha256":_canonical_sha256(contract),"expected_repo_sha":expected_repo_sha,"repository_attestation":repo_attestation,"probe_receipt_path":str(probe_receipt_path),"probe_receipt_sha256":_sha256(probe_receipt_path) if probe_receipt_path.is_file() else None,"probe_slurm_job_id":probe_job_id,"slurm_job_id":os.environ.get("SLURM_JOB_ID"),"verdict":"STAGING_REFUSED","failures":list(dict.fromkeys(failures)),"candidate_path":str(candidate),"final_path":str(final),"model_execution_performed":False,"evaluated_result_record_count":0}
        _atomic_json(failure_root / f"staging-refused-{os.environ.get('SLURM_JOB_ID','NOJOB')}.json", receipt)
        return receipt
    candidate.mkdir(parents=True, exist_ok=False)
    observed_files = []
    try:
        for artifact in manifest["artifacts"]:
            destination = candidate / artifact["destination"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(artifact["url"], timeout=1800) as response, destination.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            observed_hash = _sha256(destination)
            if destination.stat().st_size != artifact["bytes"] or observed_hash != artifact["sha256"]:
                raise ValueError(f"artifact identity mismatch:{artifact['artifact_id']}")
            observed_files.append({"artifact_id":artifact["artifact_id"],"path":str(destination.relative_to(candidate)),"bytes":destination.stat().st_size,"sha256":observed_hash})
        python_archive = next(candidate / a["destination"] for a in manifest["artifacts"] if a["role"] == "python_archive")
        runtime = candidate / "runtime"
        runtime.mkdir()
        _safe_extract(python_archive, runtime)
        python_exe = runtime / "python/bin/python3.11"
        requirements = _binding_path(contract, "requirements_lock", repository_root)
        shutil.copy2(requirements, candidate / "requirements.lock")
        env = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1")
        subprocess.run([str(python_exe), "-m", "pip", "install", "--no-index", "--no-deps", f"--find-links={candidate / 'wheelhouse'}", "--require-hashes", "-r", str(candidate / "requirements.lock")], check=True, shell=False, env=env)
        pip_check = subprocess.run(
            [str(python_exe), "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
            env=env,
        )
        version_code = "import importlib.metadata as m,json; print(json.dumps({k:m.version(k) for k in ['torch','transformers','tokenizers','safetensors']},sort_keys=True))"
        installed = json.loads(subprocess.run([str(python_exe), "-c", version_code], capture_output=True, text=True, check=True, shell=False, env=env).stdout)
        if installed != _EXPECTED_RUNTIME:
            raise ValueError(f"installed runtime mismatch:{installed}")
        wheel_lock = json.loads(_binding_path(contract, "wheel_lock", repository_root).read_text(encoding="utf-8"))
        expected_distributions = {
            str(wheel["name"]).lower().replace("_", "-"): str(wheel["version"])
            for wheel in wheel_lock["wheels"]
        }
        expected_distributions.update({"pip": "24.3.1", "setuptools": "75.6.0"})
        distribution_code = (
            "import importlib.metadata,json; "
            "print(json.dumps({d.metadata['Name'].lower().replace('_','-'):d.version "
            "for d in importlib.metadata.distributions()},sort_keys=True))"
        )
        installed_distributions = json.loads(
            subprocess.run(
                [str(python_exe), "-c", distribution_code],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                env=env,
            ).stdout
        )
        if installed_distributions != expected_distributions:
            raise ValueError("installed distribution set mismatch")
        pip_freeze_all = subprocess.run(
            [str(python_exe), "-m", "pip", "freeze", "--all"],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
            env=env,
        ).stdout.splitlines()
        torch_smoke = json.loads(
            subprocess.run(
                [
                    str(python_exe),
                    "-c",
                    (
                        "import json,torch; "
                        "print(json.dumps({'version':torch.__version__,"
                        "'cuda':torch.version.cuda,'device':torch.ones(1).device.type},sort_keys=True))"
                    ),
                ],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                env=env,
            ).stdout
        )
        if torch_smoke != {"version": "2.8.0+cpu", "cuda": None, "device": "cpu"}:
            raise ValueError(f"torch cpu smoke mismatch:{torch_smoke}")
        python_smoke = json.loads(
            subprocess.run(
                [
                    str(python_exe),
                    "-c",
                    (
                        "import json,sys; "
                        "print(json.dumps({'version':'.'.join(map(str,sys.version_info[:3])),"
                        "'executable':sys.executable},sort_keys=True))"
                    ),
                ],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                env=env,
            ).stdout
        )
        if python_smoke != {"version": "3.11.13", "executable": str(python_exe)}:
            raise ValueError(f"standalone python smoke mismatch:{python_smoke}")
        platform_receipt = subprocess.run(
            [
                str(python_exe),
                "-c",
                "import json,platform; print(json.dumps({'platform':platform.platform(),'architecture':platform.machine(),'libc':platform.libc_ver()},sort_keys=True))",
            ],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
            env=env,
        ).stdout
        platform_observation = json.loads(platform_receipt)
        if platform_observation.get("architecture") != "x86_64":
            raise ValueError(f"platform architecture mismatch:{platform_observation}")
        receipt = {"schema_version":"paper2-cpu-staging-result-receipt-v3","created_at_utc":_now(),"contract_canonical_sha256":_canonical_sha256(contract),"expected_repo_sha":expected_repo_sha,"repository_attestation":repo_attestation,"slurm_job_id":os.environ.get("SLURM_JOB_ID"),"verdict":"STAGING_PASS_ATOMICALLY_PROMOTED","authority_condition":"This pass verdict is authoritative only when this receipt is harvested from final_path after the atomic candidate rename succeeds.","failures":[],"candidate_path":str(candidate),"final_path":str(final),"artifact_count":len(observed_files),"observed_files":observed_files,"installed_versions":installed,"installed_distributions":installed_distributions,"pip_check_stdout":pip_check.stdout.strip(),"pip_freeze_all":pip_freeze_all,"torch_cpu_smoke":torch_smoke,"standalone_python_smoke":python_smoke,"platform_receipt":platform_observation,"fs9_disk_usage_before_staging":{"total":disk.total,"used":disk.used,"free":disk.free},"model_execution_performed":False,"evaluated_result_record_count":0}
        final.parent.mkdir(parents=True, exist_ok=True)
        _commit_staging_candidate(candidate, final, receipt)
        return receipt
    except Exception as exc:
        receipt = {"schema_version":"paper2-cpu-staging-result-receipt-v3","created_at_utc":_now(),"contract_canonical_sha256":_canonical_sha256(contract),"expected_repo_sha":expected_repo_sha,"repository_attestation":repo_attestation,"probe_receipt_path":str(probe_receipt_path),"probe_receipt_sha256":_sha256(probe_receipt_path) if probe_receipt_path.is_file() else None,"probe_slurm_job_id":probe_job_id,"slurm_job_id":os.environ.get("SLURM_JOB_ID"),"verdict":"STAGING_FAILED_PRESERVED","failures":["staging_exception"],"error_type":type(exc).__name__,"error_detail":str(exc),"candidate_path":str(candidate),"candidate_preserved":candidate.exists(),"final_path":str(final),"final_exists":final.exists(),"model_execution_performed":False,"evaluated_result_record_count":0}
        _atomic_json(failure_root / f"staging-failed-{os.environ.get('SLURM_JOB_ID','NOJOB')}.json", receipt)
        return receipt


def stage_assets(*, contract: Mapping[str, object], repository_root: Path, expected_repo_sha: str, probe_receipt_path: Path) -> dict[str, Any]:
    """Run staging with an outer receipt boundary covering every setup/promotion step."""

    job_id = os.environ.get("SLURM_JOB_ID", "NOJOB")
    probe_job_id = os.environ.get("RAKL_PROBE_JOB_ID")
    candidate = Path(str(contract.get("candidate_root", FS9_ROOT / "assets/.invalid-candidate")) + f"-{job_id}")
    final = Path(str(contract.get("final_root", FS9_ROOT / "assets/.invalid-final")))
    failure_root = Path(str(contract.get("failure_root", FS9_ROOT / "failures/v3")))
    try:
        return _stage_assets_impl(
            contract=contract,
            repository_root=repository_root,
            expected_repo_sha=expected_repo_sha,
            probe_receipt_path=probe_receipt_path,
        )
    except Exception as exc:
        receipt = {
            "schema_version": "paper2-cpu-staging-result-receipt-v3",
            "created_at_utc": _now(),
            "contract_canonical_sha256": _canonical_sha256(contract),
            "expected_repo_sha": expected_repo_sha,
            "repository_attestation": None,
            "probe_receipt_path": str(probe_receipt_path),
            "probe_receipt_sha256": _sha256(probe_receipt_path) if probe_receipt_path.is_file() else None,
            "probe_slurm_job_id": probe_job_id,
            "slurm_job_id": job_id,
            "verdict": "STAGING_FAILED_PRESERVED",
            "failures": ["staging_setup_or_promotion_exception"],
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "candidate_path": str(candidate),
            "candidate_preserved": candidate.exists(),
            "final_path": str(final),
            "final_exists": final.exists(),
            "model_execution_performed": False,
            "evaluated_result_record_count": 0,
        }
        _atomic_json(failure_root / f"staging-failed-{job_id}.json", receipt)
        return receipt


def _main_submit(args: argparse.Namespace) -> int:
    contract = _load_contract(args.contract)
    observed_sha, clean = _git_observation(args.repo)
    associations = frozenset(tuple(value.split(":", 1)) for value in args.association if ":" in value)
    receipt = build_submission_receipt(contract=contract, repository_root=args.repo, expected_repo_sha=args.expected_repo_sha, observation=SubmissionObservation(observed_sha, clean, os.uname().nodename, associations), account=args.account, partition=args.partition, submit=args.submit, bootstrap_receipt_path=args.bootstrap_receipt)
    _atomic_json(args.receipt_output, receipt)
    return 0 if receipt["verdict"] in {"READY_NOT_SUBMITTED", "SUBMITTED_TWO_PHASE_STAGING"} else 2


def _main_probe(args: argparse.Namespace) -> int:
    receipt = run_network_probe(contract=_load_contract(args.contract), repository_root=args.repo, expected_repo_sha=args.expected_repo_sha, receipt_output=args.receipt_output)
    return 0 if receipt["verdict"] == "NETWORK_PROBE_PASS" else 2


def _main_stage(args: argparse.Namespace) -> int:
    receipt = stage_assets(contract=_load_contract(args.contract), repository_root=args.repo, expected_repo_sha=args.expected_repo_sha, probe_receipt_path=args.probe_receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["verdict"] == "STAGING_PASS_ATOMICALLY_PROMOTED" else 2


def build_harvest_receipt(
    *,
    submission_receipt: Mapping[str, object],
    submission_receipt_path: Path,
    receipt_root: Path,
    final_root: Path,
    failure_root: Path,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    failures: list[str] = []
    jobs = submission_receipt.get("submitted_job_ids")
    if (
        submission_receipt.get("verdict") != "SUBMITTED_TWO_PHASE_STAGING"
        or not isinstance(jobs, list)
        or len(jobs) != 2
        or any(not str(job).isdigit() for job in jobs)
    ):
        failures.append("submission_receipt_invalid")
        jobs = []
    bootstrap_path_raw = submission_receipt.get("bootstrap_receipt_path")
    bootstrap_expected_hash = submission_receipt.get("bootstrap_receipt_sha256")
    bootstrap_path = Path(str(bootstrap_path_raw)) if isinstance(bootstrap_path_raw, str) else None
    if (
        bootstrap_path is None
        or not bootstrap_path.is_file()
        or not _hex(bootstrap_expected_hash, 64)
        or _sha256(bootstrap_path) != bootstrap_expected_hash
    ):
        failures.append("bootstrap_receipt_lineage_invalid")
    rows: list[dict[str, str]] = []
    if not failures:
        try:
            completed = runner(
                [
                    "sacct",
                    "-nP",
                    "-j",
                    ",".join(str(job) for job in jobs),
                    "--format=JobIDRaw,State,ExitCode,Elapsed,MaxRSS,NodeList",
                ],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )
            for line in completed.stdout.splitlines():
                fields = line.split("|")
                if len(fields) >= 6 and fields[0] in {str(job) for job in jobs}:
                    rows.append(
                        dict(
                            zip(
                                ("job_id", "state", "exit_code", "elapsed", "max_rss", "node_list"),
                                fields[:6],
                                strict=True,
                            )
                        )
                    )
        except Exception:
            failures.append("scheduler_history_query_failed")
    if len(rows) != 2:
        failures.append("scheduler_root_rows_missing")
    by_job = {row["job_id"]: row for row in rows}
    probe_path = receipt_root / f"network-probe-{jobs[0]}.json" if jobs else receipt_root / "missing"
    stage_path = final_root / "staging_receipt.json"
    failure_candidates = (
        [
            failure_root / f"staging-failed-{jobs[1]}.json",
            failure_root / f"staging-refused-{jobs[1]}.json",
        ]
        if jobs
        else []
    )
    existing_failure_paths = [path for path in failure_candidates if path.is_file()]
    failure_path = existing_failure_paths[0] if len(existing_failure_paths) == 1 else failure_root / "missing"
    if len(existing_failure_paths) > 1:
        failures.append("staging_failure_receipt_ambiguous")

    def load(path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    probe = load(probe_path)
    stage = load(stage_path)
    failed_stage = load(failure_path)
    contract_sha = submission_receipt.get("contract_canonical_sha256")
    expected_sha = submission_receipt.get("expected_repo_sha")
    if probe is None or probe.get("verdict") != "NETWORK_PROBE_PASS" or probe.get(
        "contract_canonical_sha256"
    ) != contract_sha or probe.get("expected_repo_sha") != expected_sha:
        failures.append("network_probe_receipt_invalid")
    scheduler_success = bool(
        jobs
        and all(
            by_job.get(str(job), {}).get("state") == "COMPLETED"
            and by_job.get(str(job), {}).get("exit_code") == "0:0"
            for job in jobs
        )
    )
    stage_success = bool(
        stage
        and stage.get("verdict") == "STAGING_PASS_ATOMICALLY_PROMOTED"
        and stage.get("contract_canonical_sha256") == contract_sha
        and stage.get("expected_repo_sha") == expected_sha
        and stage.get("model_execution_performed") is False
    )
    stage_negative = bool(
        failed_stage
        and failed_stage.get("verdict") in {"STAGING_FAILED_PRESERVED", "STAGING_REFUSED"}
        and failed_stage.get("contract_canonical_sha256") == contract_sha
        and failed_stage.get("expected_repo_sha") == expected_sha
        and failed_stage.get("model_execution_performed") is False
    )
    if not stage_success:
        failures.append("staging_job_or_receipt_failed")
    if scheduler_success and stage_success and failures == []:
        verdict = "HARVEST_STAGING_PASS"
    elif stage_negative and not any(
        failure in {"bootstrap_receipt_lineage_invalid", "staging_failure_receipt_ambiguous"}
        for failure in failures
    ):
        failures = [failure for failure in failures if failure != "scheduler_root_rows_missing"]
        verdict = "HARVEST_STAGING_NEGATIVE_PRESERVED"
    else:
        verdict = "HARVEST_CANNOT_CHECK"
    return {
        "schema_version": "paper2-cpu-staging-harvest-receipt-v3",
        "created_at_utc": _now(),
        "submission_receipt_sha256": _sha256(submission_receipt_path),
        "bootstrap_receipt_path": str(bootstrap_path) if bootstrap_path else None,
        "bootstrap_receipt_sha256": bootstrap_expected_hash,
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_sha,
        "job_ids": jobs,
        "scheduler_rows": rows,
        "probe_receipt_sha256": _sha256(probe_path) if probe_path.is_file() else None,
        "staging_receipt_sha256": _sha256(stage_path) if stage_path.is_file() else None,
        "failure_receipt_sha256": _sha256(failure_path) if failure_path.is_file() else None,
        "failures": list(dict.fromkeys(failures)),
        "negative_history_preserved": stage_negative,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
        "verdict": verdict,
    }


def _main_harvest(args: argparse.Namespace) -> int:
    submission = json.loads(args.submission_receipt.read_text(encoding="utf-8"))
    receipt = build_harvest_receipt(
        submission_receipt=submission,
        submission_receipt_path=args.submission_receipt,
        receipt_root=args.receipt_root,
        final_root=args.final_root,
        failure_root=args.failure_root,
    )
    _atomic_json(args.receipt_output, receipt)
    return 0 if receipt["verdict"] in {"HARVEST_STAGING_PASS", "HARVEST_STAGING_NEGATIVE_PRESERVED"} else 2


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Paper 2 CPU staging V3; never executes the model")
    sub=parser.add_subparsers(dest="command",required=True)
    submit=sub.add_parser("submit"); submit.add_argument("--contract",type=Path,required=True); submit.add_argument("--repo",type=Path,required=True); submit.add_argument("--expected-repo-sha",required=True); submit.add_argument("--bootstrap-receipt",type=Path,required=True); submit.add_argument("--account",required=True); submit.add_argument("--partition",required=True); submit.add_argument("--association",action="append",default=[]); submit.add_argument("--receipt-output",type=Path,required=True); submit.add_argument("--submit",action="store_true"); submit.set_defaults(handler=_main_submit)
    probe=sub.add_parser("network-probe"); probe.add_argument("--contract",type=Path,required=True); probe.add_argument("--repo",type=Path,required=True); probe.add_argument("--expected-repo-sha",required=True); probe.add_argument("--receipt-output",type=Path,required=True); probe.set_defaults(handler=_main_probe)
    stage=sub.add_parser("stage-assets"); stage.add_argument("--contract",type=Path,required=True); stage.add_argument("--repo",type=Path,required=True); stage.add_argument("--expected-repo-sha",required=True); stage.add_argument("--probe-receipt",type=Path,required=True); stage.set_defaults(handler=_main_stage)
    harvest=sub.add_parser("harvest"); harvest.add_argument("--submission-receipt",type=Path,required=True); harvest.add_argument("--receipt-root",type=Path,required=True); harvest.add_argument("--final-root",type=Path,required=True); harvest.add_argument("--failure-root",type=Path,required=True); harvest.add_argument("--receipt-output",type=Path,required=True); harvest.set_defaults(handler=_main_harvest)
    args=parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
