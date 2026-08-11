from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any, Callable, Mapping

import rakl.paper2_cpu_staging_v3_2 as frozen

REPAIR_ID = "PAPER2_CPU_STAGING_V3_2_1_HARVEST_REPAIR"
REPAIR_SCHEMA = "paper2-cpu-staging-harvest-receipt-v3.2.1"
REPAIR_CONTRACT_SCHEMA = "paper2-cpu-staging-harvest-repair-contract-v3.2.1"
SOURCE_SUBJECT_SHA = "c10ba7a261af02cc42690022226555a3197351ae"
SOURCE_SUBJECT_TREE = "4f8053958d9ed4ea6e506ffa6dc8e60ee36715a5"
SOURCE_CONTRACT_CANONICAL_SHA256 = (
    "a9d3097bc7fa42b8e9d1431e84d4ab8189190706d281efc3474b692925df6c75"
)
REPAIR_BOUNDARY = (
    "Harvest-only additive validator correction. It must not mutate V3.2 source "
    "receipts, submit a job, execute a model, or reinterpret the original "
    "CANNOT_CHECK as a pass. A new receipt may promote only after exact "
    "revalidation of the same scheduler and receipt chain."
)
_BUNDLED_FREEZE_DIRECT_REFERENCES = {
    "pip": "pip @ file:///build/pip-24.3.1-py3-none-any.whl#sha256=3790624780082365f47549d032f3770eeb2b1e8bd1f7b2e02dace1afa361b4ed",
    "setuptools": "setuptools @ file:///build/setuptools-75.6.0-py3-none-any.whl#sha256=ce74b49e8f7110f9bf04883b730f4765b774ef3ef28f722cce7c273d253aaf7d",
}
_NATIVE_SCHEDULER_ROWS = [
    {
        "elapsed": "00:00:04",
        "exit_code": "0:0",
        "job_id": "3475123",
        "max_rss": "",
        "node_list": "cn004",
        "state": "COMPLETED",
    },
    {
        "elapsed": "00:02:05",
        "exit_code": "0:0",
        "job_id": "3475124",
        "max_rss": "",
        "node_list": "cn004",
        "state": "COMPLETED",
    },
]
_NATIVE_BUNDLE_MEMBERS = {
    "receipts/v3_2/bootstrap-c10ba7a261af02cc42690022226555a3197351ae.json":
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_V3_2_C10BA7A.json",
    "receipts/v3_2/submission-c10ba7a261af02cc42690022226555a3197351ae.json":
        "research/paper2_microtrial_v3/native_receipts/SUBMISSION_NATIVE_V3_2_C10BA7A.json",
    "receipts/v3_2/network-probe-3475123.json":
        "research/paper2_microtrial_v3/native_receipts/NETWORK_PROBE_NATIVE_V3_2_JOB_3475123.json",
    "assets/paper2-cpu-v3-2/staging_receipt.json":
        "research/paper2_microtrial_v3/native_receipts/STAGING_PASS_NATIVE_V3_2_JOB_3475124.json",
    "receipts/v3_2/harvest-3475123-3475124.json":
        "research/paper2_microtrial_v3/native_receipts/HARVEST_CANNOT_CHECK_NATIVE_V3_2_JOBS_3475123_3475124.json",
    "logs/network_probe_v3_2_3475123.out":
        "research/paper2_microtrial_v3/native_logs/NETWORK_PROBE_V3_2_JOB_3475123.out",
    "logs/stage_cpu_v3_2_3475124.out":
        "research/paper2_microtrial_v3/native_logs/STAGE_CPU_V3_2_JOB_3475124.out",
}


def _load_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding_sha(contract: Mapping[str, object], role: str) -> str | None:
    bindings = contract.get("bindings")
    if not isinstance(bindings, list):
        return None
    matches = [
        item.get("sha256")
        for item in bindings
        if isinstance(item, Mapping) and item.get("role") == role
    ]
    return matches[0] if len(matches) == 1 and frozen._hex(matches[0], 64) else None


def _parse_pip_freeze(lines: object) -> dict[str, str] | None:
    if not isinstance(lines, list) or len(lines) != 31:
        return None
    parsed: dict[str, str] = {}
    direct_by_line = {value: name for name, value in _BUNDLED_FREEZE_DIRECT_REFERENCES.items()}
    for line in lines:
        if not isinstance(line, str):
            return None
        if line in direct_by_line:
            name = direct_by_line[line]
            version = "24.3.1" if name == "pip" else "75.6.0"
        elif line.count("==") == 1 and " @ " not in line:
            name, version = line.split("==", 1)
            name = name.lower().replace("_", "-")
            if not name or not version or name in _BUNDLED_FREEZE_DIRECT_REFERENCES:
                return None
        else:
            return None
        if name in parsed:
            return None
        parsed[name] = version
    return parsed


def _hms(seconds: object) -> str | None:
    if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds < 0:
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _stage_max_rss_bytes(sacct: Mapping[str, object]) -> int | None:
    jobs = sacct.get("jobs")
    if not isinstance(jobs, list):
        return None
    stage_jobs = [
        job
        for job in jobs
        if isinstance(job, Mapping) and job.get("job_id") == 3475124
    ]
    if len(stage_jobs) != 1:
        return None
    steps = stage_jobs[0].get("steps")
    if not isinstance(steps, list):
        return None
    batch_steps = [
        step
        for step in steps
        if isinstance(step, Mapping)
        and isinstance(step.get("step"), Mapping)
        and step["step"].get("id") == "3475124.batch"
    ]
    if len(batch_steps) != 1:
        return None
    requested = batch_steps[0].get("tres")
    requested = requested.get("requested") if isinstance(requested, Mapping) else None
    maxima = requested.get("max") if isinstance(requested, Mapping) else None
    memory = [
        item.get("count")
        for item in maxima or []
        if isinstance(item, Mapping) and item.get("type") == "mem"
    ]
    return memory[0] if len(memory) == 1 and isinstance(memory[0], int) else None


def _native_evidence_failures(repair_repository_root: Path) -> tuple[str, ...]:
    failures: list[str] = []
    sacct_path = repair_repository_root / (
        "research/paper2_microtrial_v3/native_receipts/"
        "SACCT_NATIVE_V3_2_JOBS_3475123_3475124.json"
    )
    sacct = _load_object(sacct_path)
    jobs = sacct.get("jobs") if sacct is not None else None
    derived_rows: list[dict[str, str]] = []
    if isinstance(jobs, list):
        for job in jobs:
            if not isinstance(job, Mapping):
                continue
            state = job.get("state")
            exit_code = job.get("exit_code")
            time = job.get("time")
            current = state.get("current") if isinstance(state, Mapping) else None
            return_code = (
                exit_code.get("return_code")
                if isinstance(exit_code, Mapping)
                else None
            )
            signal = exit_code.get("signal") if isinstance(exit_code, Mapping) else None
            signal_id = signal.get("id") if isinstance(signal, Mapping) else None
            elapsed = time.get("elapsed") if isinstance(time, Mapping) else None
            if (
                isinstance(job.get("job_id"), int)
                and current == ["COMPLETED"]
                and isinstance(return_code, Mapping)
                and return_code.get("set") is True
                and return_code.get("number") == 0
                and isinstance(signal_id, Mapping)
                and signal_id.get("set") is False
                and _hms(elapsed) is not None
                and isinstance(job.get("nodes"), str)
            ):
                derived_rows.append(
                    {
                        "elapsed": str(_hms(elapsed)),
                        "exit_code": "0:0",
                        "job_id": str(job["job_id"]),
                        "max_rss": "",
                        "node_list": str(job["nodes"]),
                        "state": "COMPLETED",
                    }
                )
    if derived_rows != _NATIVE_SCHEDULER_ROWS:
        failures.append("native_sacct_semantics_invalid")
    if sacct is None or _stage_max_rss_bytes(sacct) != 2_156_756_992:
        failures.append("native_stage_max_rss_invalid")

    bundle_path = repair_repository_root / (
        "research/paper2_microtrial_v3/native_bundles/"
        "PAPER2_STAGE_V3_2_SUCCESS_HARVEST_CC_JOBS_3475123_3475124.tar.gz"
    )
    try:
        with tarfile.open(bundle_path, mode="r:gz") as bundle:
            members = bundle.getmembers()
            if (
                len(members) != len(_NATIVE_BUNDLE_MEMBERS)
                or {member.name for member in members} != set(_NATIVE_BUNDLE_MEMBERS)
                or any(not member.isfile() for member in members)
            ):
                failures.append("native_bundle_member_set_invalid")
            else:
                for member in members:
                    source = bundle.extractfile(member)
                    expected = repair_repository_root / _NATIVE_BUNDLE_MEMBERS[member.name]
                    if source is None or not expected.is_file() or source.read() != expected.read_bytes():
                        failures.append(f"native_bundle_member_mismatch:{member.name}")
    except (OSError, tarfile.TarError):
        failures.append("native_bundle_invalid")
    return tuple(dict.fromkeys(failures))


def _repair_contract_failures(
    contract: Mapping[str, object], *, repair_repository_root: Path
) -> tuple[str, ...]:
    failures: list[str] = []
    if contract.get("schema_version") != REPAIR_CONTRACT_SCHEMA:
        failures.append("repair_contract_schema_invalid")
    if contract.get("repair_id") != REPAIR_ID:
        failures.append("repair_contract_id_invalid")
    if contract.get("authority_status") != "repair_ready_not_reharvested":
        failures.append("repair_contract_authority_invalid")
    if contract.get("source_subject_sha") != SOURCE_SUBJECT_SHA:
        failures.append("repair_contract_source_subject_invalid")
    if contract.get("source_subject_tree") != SOURCE_SUBJECT_TREE:
        failures.append("repair_contract_source_tree_invalid")
    if contract.get("source_contract_canonical_sha256") != SOURCE_CONTRACT_CANONICAL_SHA256:
        failures.append("repair_contract_source_contract_invalid")
    if contract.get("source_job_ids") != ["3475123", "3475124"]:
        failures.append("repair_contract_jobs_invalid")
    if contract.get("job_submission_permitted") is not False:
        failures.append("repair_contract_submission_not_forbidden")
    if contract.get("model_execution_permitted") is not False:
        failures.append("repair_contract_model_execution_not_forbidden")
    if contract.get("evaluated_result_access_permitted") is not False:
        failures.append("repair_contract_result_access_not_forbidden")
    if contract.get("prior_harvest_verdict") != "HARVEST_CANNOT_CHECK":
        failures.append("repair_contract_prior_verdict_invalid")
    if contract.get("prior_harvest_failure") != ["staging_job_or_receipt_failed"]:
        failures.append("repair_contract_prior_failure_invalid")
    if contract.get("contract_self_hash_mode") != "canonical_contract_with_self_sha256_zeroed":
        failures.append("repair_contract_self_hash_mode_invalid")
    if contract.get("repair_boundary") != REPAIR_BOUNDARY:
        failures.append("repair_contract_boundary_invalid")
    if contract.get("accepted_bundled_direct_references") != _BUNDLED_FREEZE_DIRECT_REFERENCES:
        failures.append("repair_contract_direct_references_invalid")
    bindings = contract.get("bindings")
    if not isinstance(bindings, list):
        return tuple(failures + ["repair_contract_bindings_missing"])
    roles: list[object] = []
    for binding in bindings:
        if not isinstance(binding, Mapping):
            failures.append("repair_contract_binding_invalid")
            continue
        roles.append(binding.get("role"))
        raw = binding.get("path")
        if not isinstance(raw, str):
            failures.append(f"repair_contract_binding_path_invalid:{binding.get('role')}")
            continue
        relative = Path(raw)
        if relative.is_absolute() or ".." in relative.parts:
            failures.append(f"repair_contract_binding_path_invalid:{binding.get('role')}")
            continue
        path = repair_repository_root / relative
        if not path.is_file():
            failures.append(f"repair_contract_binding_missing:{binding.get('role')}")
        elif binding.get("role") == "contract_self":
            normalized = copy.deepcopy(dict(contract))
            normalized_binding = next(
                (
                    item
                    for item in normalized.get("bindings", [])
                    if isinstance(item, dict) and item.get("role") == "contract_self"
                ),
                None,
            )
            if normalized_binding is None:
                failures.append("repair_contract_self_binding_missing")
            else:
                normalized_binding["sha256"] = "0" * 64
                if binding.get("sha256") != frozen._canonical_sha256(normalized):
                    failures.append("repair_contract_self_hash_invalid")
        elif binding.get("sha256") != _sha256(path):
            failures.append(f"repair_contract_binding_hash_invalid:{binding.get('role')}")
    if len(roles) != len(set(roles)):
        failures.append("repair_contract_binding_role_duplicate")
    required = {
        "frozen_v3_2_contract",
        "frozen_v3_2_runtime",
        "harvest_repair_runtime",
        "harvest_repair_script",
        "harvest_repair_receipt_schema",
        "harvest_repair_contract_schema",
        "native_bootstrap",
        "native_submission",
        "native_probe",
        "native_staging_pass",
        "native_harvest_cannot_check",
        "native_sacct",
        "native_probe_log",
        "native_stage_log",
        "native_bundle",
        "contract_self",
    }
    if set(roles) != required or len(roles) != len(required):
        failures.append("repair_contract_binding_roles_not_exact")
    failures.extend(_native_evidence_failures(repair_repository_root))
    return tuple(dict.fromkeys(failures))


def _stage_success_failures(
    *,
    source_contract: Mapping[str, object],
    source_repository_root: Path,
    submission_receipt: Mapping[str, object],
    receipt_root: Path,
    final_root: Path,
    failure_root: Path,
) -> tuple[str, ...]:
    failures: list[str] = []
    jobs = submission_receipt.get("submitted_job_ids")
    if not isinstance(jobs, list) or len(jobs) != 2:
        return ("repair_stage_job_lineage_invalid",)
    probe_path = receipt_root / f"network-probe-{jobs[0]}.json"
    stage_path = final_root / "staging_receipt.json"
    failure_paths = [
        failure_root / f"staging-failed-{jobs[1]}.json",
        failure_root / f"staging-refused-{jobs[1]}.json",
    ]
    if final_root.is_symlink() or not final_root.is_dir():
        failures.append("repair_final_root_invalid")
    if stage_path.is_symlink() or not stage_path.is_file():
        failures.append("repair_stage_receipt_file_invalid")
    if any(path.exists() for path in failure_paths):
        failures.append("repair_contradictory_failure_receipt_present")
    expected_candidate = final_root.parent / f".{final_root.name}-candidate-{jobs[1]}"
    if expected_candidate.exists() or expected_candidate.is_symlink():
        failures.append("repair_promoted_candidate_still_present")
    probe = _load_object(probe_path)
    stage = _load_object(stage_path)
    if probe is None or stage is None:
        return tuple(dict.fromkeys(failures + ["repair_source_receipt_missing_or_invalid"]))
    manifest_path = frozen._binding_path(
        source_contract, "asset_manifest", source_repository_root
    )
    manifest = _load_object(manifest_path)
    wheel_lock = _load_object(
        frozen._binding_path(source_contract, "wheel_lock", source_repository_root)
    )
    if manifest is None or wheel_lock is None:
        return tuple(dict.fromkeys(failures + ["repair_bound_manifest_or_lock_invalid"]))
    manifest_artifacts = {
        str(item["artifact_id"]): {
            "path": str(item["destination"]),
            "bytes": int(item["bytes"]),
            "sha256": str(item["sha256"]),
        }
        for item in manifest["artifacts"]
    }
    observed_files = stage.get("observed_files")
    observed = (
        {str(item.get("artifact_id")): item for item in observed_files if isinstance(item, Mapping)}
        if isinstance(observed_files, list)
        else {}
    )
    observed_valid = bool(
        isinstance(observed_files, list)
        and len(observed_files) == len(observed) == len(manifest_artifacts) == 38
        and set(observed) == set(manifest_artifacts)
        and all(
            observed[artifact_id].get("path") == expected["path"]
            and observed[artifact_id].get("bytes") == expected["bytes"]
            and observed[artifact_id].get("sha256") == expected["sha256"]
            for artifact_id, expected in manifest_artifacts.items()
        )
    )
    if not observed_valid:
        failures.append("repair_observed_artifacts_invalid")
    expected_distributions = {
        str(item["name"]).lower().replace("_", "-"): str(item["version"])
        for item in wheel_lock["wheels"]
    }
    expected_distributions.update({"pip": "24.3.1", "setuptools": "75.6.0"})
    if stage.get("installed_distributions") != expected_distributions:
        failures.append("repair_installed_distributions_invalid")
    if _parse_pip_freeze(stage.get("pip_freeze_all")) != expected_distributions:
        failures.append("repair_pip_freeze_invalid")
    disk = stage.get("fs9_disk_usage_before_staging")
    minimum_free = int(
        source_contract.get("staging_attestation_policy", {}).get("minimum_free_bytes", 0)
    )
    disk_valid = bool(
        isinstance(disk, Mapping)
        and all(
            isinstance(disk.get(field), int)
            and not isinstance(disk.get(field), bool)
            and int(disk[field]) >= 0
            for field in ("total", "used", "free")
        )
        and int(disk["total"]) == int(disk["used"]) + int(disk["free"])
        and int(disk["free"]) >= minimum_free
    )
    if not disk_valid:
        failures.append("repair_disk_attestation_invalid")
    expected_sha = submission_receipt.get("expected_repo_sha")
    contract_sha = submission_receipt.get("contract_canonical_sha256")
    attestation = stage.get("repository_attestation")
    predicates = {
        "repair_stage_schema_invalid": stage.get("schema_version")
        == "paper2-cpu-staging-result-receipt-v3.2",
        "repair_stage_verdict_invalid": stage.get("verdict")
        == "STAGING_PASS_ATOMICALLY_PROMOTED",
        "repair_stage_contract_invalid": stage.get("contract_canonical_sha256")
        == contract_sha,
        "repair_stage_repo_sha_invalid": stage.get("expected_repo_sha") == expected_sha,
        "repair_stage_job_invalid": str(stage.get("slurm_job_id")) == str(jobs[1]),
        "repair_stage_probe_job_invalid": str(stage.get("probe_slurm_job_id"))
        == str(jobs[0]),
        "repair_stage_probe_path_invalid": stage.get("probe_receipt_path")
        == str(probe_path),
        "repair_stage_probe_hash_invalid": stage.get("probe_receipt_sha256")
        == _sha256(probe_path),
        "repair_stage_candidate_path_invalid": stage.get("candidate_path")
        == str(expected_candidate),
        "repair_stage_final_path_invalid": stage.get("final_path") == str(final_root),
        "repair_stage_failures_nonempty": stage.get("failures") == [],
        "repair_stage_artifact_count_invalid": stage.get("artifact_count") == 38,
        "repair_stage_versions_invalid": stage.get("installed_versions")
        == frozen._EXPECTED_RUNTIME,
        "repair_stage_pip_check_invalid": stage.get("pip_check_returncode") == 0
        and stage.get("pip_check_stdout") == "No broken requirements found.",
        "repair_stage_torch_smoke_invalid": stage.get("torch_cpu_smoke")
        == {"version": "2.8.0+cpu", "cuda": None, "device": "cpu"},
        "repair_stage_python_smoke_invalid": isinstance(
            stage.get("standalone_python_smoke"), Mapping
        )
        and stage["standalone_python_smoke"].get("version") == "3.11.13"
        and stage["standalone_python_smoke"].get("executable")
        == str(expected_candidate / "runtime/python/bin/python3.11"),
        "repair_stage_platform_invalid": isinstance(stage.get("platform_receipt"), Mapping)
        and stage["platform_receipt"].get("architecture") == "x86_64",
        "repair_stage_repository_attestation_invalid": isinstance(attestation, Mapping)
        and attestation.get("repo_sha") == expected_sha
        and attestation.get("checkout_clean") is True
        and attestation.get("construction_parent_sha")
        == source_contract.get("construction_parent_sha")
        and attestation.get("construction_parent_ancestor") is True
        and frozen._hex(attestation.get("repo_tree_sha"), 40),
        "repair_stage_scope_invalid": stage.get("model_execution_performed") is False
        and stage.get("evaluated_result_record_count") == 0,
    }
    failures.extend(name for name, passed in predicates.items() if not passed)
    return tuple(dict.fromkeys(failures))


def build_harvest_repair_receipt(
    *,
    repair_contract: Mapping[str, object],
    repair_repository_root: Path,
    expected_repair_sha: str,
    source_contract: Mapping[str, object],
    source_repository_root: Path,
    submission_receipt: Mapping[str, object],
    submission_receipt_path: Path,
    prior_harvest_receipt_path: Path,
    receipt_root: Path,
    final_root: Path,
    failure_root: Path,
    runner: Callable[..., Any] = subprocess.run,
    source_git_observer: Callable[[Path], tuple[str, bool]] = frozen._git_observation,
    repair_git_observer: Callable[[Path], tuple[str, bool]] = frozen._git_observation,
    path_mapper: Callable[[str], Path] = Path,
    binding_sha_observer: Callable[[Mapping[str, object], str], str | None] = _binding_sha,
) -> dict[str, Any]:
    failures = list(
        _repair_contract_failures(
            repair_contract, repair_repository_root=repair_repository_root
        )
    )
    if (
        binding_sha_observer(repair_contract, "native_submission") is None
        or not submission_receipt_path.is_file()
        or _sha256(submission_receipt_path)
        != binding_sha_observer(repair_contract, "native_submission")
    ):
        failures.append("native_submission_binding_mismatch")
    if (
        binding_sha_observer(repair_contract, "native_harvest_cannot_check") is None
        or not prior_harvest_receipt_path.is_file()
        or _sha256(prior_harvest_receipt_path)
        != binding_sha_observer(repair_contract, "native_harvest_cannot_check")
    ):
        failures.append("native_prior_harvest_binding_mismatch")
    try:
        observed_repair_sha, repair_clean = repair_git_observer(repair_repository_root)
    except Exception:
        observed_repair_sha, repair_clean = "", False
    if (
        not frozen._hex(expected_repair_sha, 40)
        or observed_repair_sha != expected_repair_sha
        or repair_clean is not True
    ):
        failures.append("repair_repository_observation_invalid")
    if submission_receipt.get("expected_repo_sha") != SOURCE_SUBJECT_SHA:
        failures.append("source_repository_subject_mismatch")
    if submission_receipt.get("submitted_job_ids") != ["3475123", "3475124"]:
        failures.append("source_job_lineage_mismatch")
    if frozen._canonical_sha256(source_contract) != SOURCE_CONTRACT_CANONICAL_SHA256:
        failures.append("source_contract_identity_mismatch")
    baseline = frozen.build_harvest_receipt(
        contract=source_contract,
        repository_root=source_repository_root,
        submission_receipt=submission_receipt,
        submission_receipt_path=submission_receipt_path,
        receipt_root=receipt_root,
        final_root=final_root,
        failure_root=failure_root,
        runner=runner,
        git_observer=source_git_observer,
        path_mapper=path_mapper,
    )
    prior = _load_object(prior_harvest_receipt_path)
    baseline_stable = {key: value for key, value in baseline.items() if key != "created_at_utc"}
    prior_stable = (
        {key: value for key, value in prior.items() if key != "created_at_utc"}
        if prior is not None
        else None
    )
    if (
        prior_stable != baseline_stable
        or baseline.get("schema_version")
        != "paper2-cpu-staging-harvest-receipt-v3.2"
        or baseline.get("verdict") != "HARVEST_CANNOT_CHECK"
        or baseline.get("failures") != ["staging_job_or_receipt_failed"]
        or baseline.get("model_execution_performed") is not False
        or baseline.get("evaluated_result_record_count") != 0
    ):
        failures.append("prior_harvest_cannot_check_reproduction_invalid")
    failures.extend(
        _stage_success_failures(
            source_contract=source_contract,
            source_repository_root=source_repository_root,
            submission_receipt=submission_receipt,
            receipt_root=receipt_root,
            final_root=final_root,
            failure_root=failure_root,
        )
    )
    attestation = _load_object(final_root / "staging_receipt.json")
    repository_attestation = (
        attestation.get("repository_attestation")
        if isinstance(attestation, Mapping)
        else None
    )
    if (
        not isinstance(repository_attestation, Mapping)
        or repository_attestation.get("repo_tree_sha") != SOURCE_SUBJECT_TREE
    ):
        failures.append("source_repository_tree_mismatch")
    failures = list(dict.fromkeys(failures))
    verdict = "HARVEST_STAGING_PASS" if not failures else "HARVEST_CANNOT_CHECK"
    return {
        "schema_version": REPAIR_SCHEMA,
        "created_at_utc": frozen._now(),
        "repair_id": REPAIR_ID,
        "repair_contract_canonical_sha256": frozen._canonical_sha256(repair_contract),
        "repair_repository_sha": observed_repair_sha,
        "source_repository_sha": submission_receipt.get("expected_repo_sha"),
        "source_repository_tree": SOURCE_SUBJECT_TREE,
        "source_contract_canonical_sha256": submission_receipt.get(
            "contract_canonical_sha256"
        ),
        "prior_harvest_receipt_path": str(prior_harvest_receipt_path),
        "prior_harvest_receipt_sha256": (
            _sha256(prior_harvest_receipt_path)
            if prior_harvest_receipt_path.is_file()
            else None
        ),
        "reproduced_v3_2_harvest_canonical_sha256": frozen._canonical_sha256(
            baseline_stable
        ),
        "submission_receipt_sha256": baseline.get("submission_receipt_sha256"),
        "bootstrap_receipt_sha256": baseline.get("bootstrap_receipt_sha256"),
        "probe_receipt_sha256": baseline.get("probe_receipt_sha256"),
        "staging_receipt_sha256": baseline.get("staging_receipt_sha256"),
        "failure_receipt_sha256": baseline.get("failure_receipt_sha256"),
        "job_ids": baseline.get("job_ids"),
        "scheduler_rows": baseline.get("scheduler_rows"),
        "failures": failures,
        "negative_history_preserved": False,
        "prior_negative_history_preserved": True,
        "jobs_submitted_by_repair": 0,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
        "verdict": verdict,
    }


def _main(args: argparse.Namespace) -> int:
    repair_root = args.repair_repo.resolve()
    source_root = args.source_repo.resolve()
    if repair_root == source_root:
        raise ValueError("repair and source repositories must be distinct checkouts")
    output = args.receipt_output.resolve()
    protected_roots = [
        repair_root,
        source_root,
        args.receipt_root.resolve(),
        args.final_root.resolve(),
        args.failure_root.resolve(),
    ]
    if any(output == root or output.is_relative_to(root) for root in protected_roots):
        raise ValueError("receipt output must be outside every protected source/evidence root")
    if args.receipt_output.exists() or args.receipt_output.is_symlink():
        raise FileExistsError("receipt output already exists; additive repair never overwrites")
    submission = _load_object(args.submission_receipt)
    if submission is None:
        raise ValueError("submission receipt must be an object")
    receipt = build_harvest_repair_receipt(
        repair_contract=frozen._load_contract(args.repair_contract),
        repair_repository_root=args.repair_repo,
        expected_repair_sha=args.expected_repair_sha,
        source_contract=frozen._load_contract(args.source_contract),
        source_repository_root=args.source_repo,
        submission_receipt=submission,
        submission_receipt_path=args.submission_receipt,
        prior_harvest_receipt_path=args.prior_harvest_receipt,
        receipt_root=args.receipt_root,
        final_root=args.final_root,
        failure_root=args.failure_root,
    )
    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.receipt_output.with_name(f".{args.receipt_output.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise FileExistsError("temporary receipt path already exists")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.receipt_output)
    return 0 if receipt["verdict"] == "HARVEST_STAGING_PASS" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Paper 2 V3.2.1 harvest-only repair; never submits jobs or executes a model"
    )
    parser.add_argument("--repair-contract", type=Path, required=True)
    parser.add_argument("--repair-repo", type=Path, required=True)
    parser.add_argument("--expected-repair-sha", required=True)
    parser.add_argument("--source-contract", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--submission-receipt", type=Path, required=True)
    parser.add_argument("--prior-harvest-receipt", type=Path, required=True)
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--final-root", type=Path, required=True)
    parser.add_argument("--failure-root", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    return _main(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
