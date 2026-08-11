#!/usr/bin/env python3
"""Allocated CPU runtime for the frozen label-blind Paper 3 descriptor."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import os
import platform
from pathlib import Path
from typing import Any

from semantic_descriptor_common import (
    ACCOUNT,
    PARTITION,
    atomic_write_json,
    canonical_sha256,
    file_sha256,
    inspect_model_files,
    load_json,
    parse_utc,
    tree_sha256,
    utc_now,
    validate_repo_and_contract,
    validate_schema,
)


EXPECTED_PACKAGES = {
    "safetensors": "0.6.2",
    "tokenizers": "0.21.4",
    "torch": "2.8.0+cpu",
    "transformers": "4.55.0",
}


def _base(
    *, contract: dict[str, Any], expected_repo_sha: str, failures: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": "paper3-semantic-descriptor-execution-v1",
        "created_at_utc": utc_now(),
        "verdict": "DESCRIPTOR_EXECUTION_CANNOT_CHECK",
        "expected_repo_sha": expected_repo_sha,
        "frozen_parent_sha": contract.get("frozen_parent_sha"),
        "contract_sha256": os.environ.get("RAKL_CONTRACT_SHA256"),
        "stage_harvest_sha256": os.environ.get("RAKL_STAGE_HARVEST_SHA256"),
        "parent_stage_job_id": os.environ.get("RAKL_STAGE_JOB_ID"),
        "stage_runtime_tree_sha256": os.environ.get(
            "RAKL_STAGE_RUNTIME_TREE_SHA256"
        ),
        "pre_execution_label_observation_sha256": os.environ.get(
            "RAKL_PRE_LABEL_OBSERVATION_SHA256"
        ),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_account": os.environ.get("SLURM_JOB_ACCOUNT"),
        "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
        "node": platform.node(),
        "runtime": {
            "python": platform.python_version(),
            "packages": {},
            "sentencepiece_available": importlib.util.find_spec("sentencepiece")
            is not None,
            "fast_tokenizer_probe_passed": False,
            "device": "cpu",
            "dtype": "float32",
            "local_files_only": True,
        },
        "runtime_tree_sha256_before": None,
        "runtime_tree_sha256_after": None,
        "model_files_before": [],
        "model_files_after": [],
        "descriptor_path": None,
        "descriptor_sha256": None,
        "descriptor_status": None,
        "descriptor_record_count": 0,
        "failures": failures,
        "label_access": {
            "external_annotation_accessed": False,
            "adjudication_accessed": False,
            "evaluated_result_accessed": False,
        },
        "training_authorized": False,
        "claim_boundary": (
            "Label-blind content-semantic descriptor only; not a structural-signal, "
            "training-efficiency, inference-efficiency, break-even, independent-review "
            "or peer-review result."
        ),
    }


def run_descriptor(
    *, repo: Path, contract_path: Path, stage_harvest_path: Path, output: Path
) -> dict[str, Any]:
    expected_repo_sha = os.environ.get("RAKL_EXPECTED_REPO_SHA", "")
    contract, failures = validate_repo_and_contract(
        repo=repo, contract_path=contract_path, expected_repo_sha=expected_repo_sha
    )
    if file_sha256(contract_path) != os.environ.get("RAKL_CONTRACT_SHA256"):
        failures.append("contract_environment_hash_mismatch")
    if not os.environ.get("SLURM_JOB_ID"):
        failures.append("not_inside_slurm_allocation")
    if os.environ.get("SLURM_JOB_ACCOUNT") != ACCOUNT:
        failures.append("slurm_account_mismatch")
    if os.environ.get("SLURM_JOB_PARTITION") != PARTITION:
        failures.append("slurm_partition_mismatch")
    receipt = _base(
        contract=contract, expected_repo_sha=expected_repo_sha, failures=failures
    )
    execution_schema = (
        repo / "schemas/paper3-semantic-descriptor-execution-v1.schema.json"
    )

    try:
        stage_harvest = load_json(stage_harvest_path)
        validate_schema(
            stage_harvest,
            repo / "schemas/paper3-semantic-lunarc-harvest-v1.schema.json",
        )
        if file_sha256(stage_harvest_path) != os.environ.get(
            "RAKL_STAGE_HARVEST_SHA256"
        ):
            receipt["failures"].append("stage_harvest_environment_hash_mismatch")
        if stage_harvest.get("verdict") != "HARVEST_MODEL_STAGE_PASS":
            receipt["failures"].append("stage_harvest_not_passed")
        if stage_harvest.get("expected_repo_sha") != expected_repo_sha:
            receipt["failures"].append("stage_checkout_sha_mismatch")
        if stage_harvest.get("slurm_job_id") != os.environ.get("RAKL_STAGE_JOB_ID"):
            receipt["failures"].append("stage_harvest_job_id_mismatch")
        if stage_harvest.get("contract_sha256") != os.environ.get(
            "RAKL_CONTRACT_SHA256"
        ):
            receipt["failures"].append("stage_harvest_contract_mismatch")
        if stage_harvest.get("frozen_parent_sha") != contract.get(
            "frozen_parent_sha"
        ):
            receipt["failures"].append("stage_harvest_parent_mismatch")
        if stage_harvest.get("stage_runtime_tree_sha256") != os.environ.get(
            "RAKL_STAGE_RUNTIME_TREE_SHA256"
        ):
            receipt["failures"].append("stage_runtime_tree_hash_mismatch")
    except Exception:
        receipt["failures"].append("stage_harvest_invalid")

    try:
        observation_path = Path(os.environ["RAKL_PRE_LABEL_OBSERVATION_PATH"])
        observation = load_json(observation_path)
        validate_schema(
            observation,
            repo / "schemas/paper3-label-chronology-v1.schema.json",
        )
        if file_sha256(observation_path) != os.environ.get(
            "RAKL_PRE_LABEL_OBSERVATION_SHA256"
        ):
            receipt["failures"].append("pre_label_observation_hash_mismatch")
        if observation.get("state") != "ZERO_LABELS_OBSERVED":
            receipt["failures"].append("pre_label_observation_not_zero")
        if parse_utc(observation.get("created_at_utc")) < parse_utc(
            contract.get("chronology", {}).get("zero_label_observed_at_utc")
        ):
            receipt["failures"].append("pre_label_observation_predates_contract")
    except Exception:
        receipt["failures"].append("pre_label_observation_invalid")

    model_dir = Path(str(contract.get("fs9", {}).get("model_dir", "")))
    expected_files = contract.get("model", {}).get("required_files", [])
    observed_before, model_failures = inspect_model_files(model_dir, expected_files)
    receipt["model_files_before"] = observed_before
    receipt["failures"].extend(model_failures)

    runtime_root = Path(str(contract.get("runtime", {}).get("runtime_root", "")))
    runtime_receipt = Path(
        str(contract.get("runtime", {}).get("staging_receipt_path", ""))
    )
    if not runtime_root.is_dir():
        receipt["failures"].append("runtime_root_missing")
    else:
        receipt["runtime_tree_sha256_before"] = tree_sha256(runtime_root)
        if receipt["runtime_tree_sha256_before"] != receipt[
            "stage_runtime_tree_sha256"
        ]:
            receipt["failures"].append("stage_runtime_tree_sha256_mismatch")
    if (
        not runtime_receipt.is_file()
        or file_sha256(runtime_receipt)
        != contract.get("runtime", {}).get("staging_receipt_sha256")
    ):
        receipt["failures"].append("runtime_staging_receipt_mismatch")
    for package, expected in EXPECTED_PACKAGES.items():
        try:
            observed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            observed = "MISSING"
        receipt["runtime"]["packages"][package] = observed
        if observed != expected:
            receipt["failures"].append(f"runtime_package_mismatch:{package}")
    if platform.python_version() != "3.11.13":
        receipt["failures"].append("runtime_python_mismatch")

    source_path = repo / str(contract.get("source_set", {}).get("path", ""))
    protocol_path = repo / str(contract.get("protocol", {}).get("path", ""))
    try:
        source_set = load_json(source_path)
        protocol = load_json(protocol_path)
        if file_sha256(source_path) != contract["source_set"]["file_sha256"]:
            receipt["failures"].append("source_set_file_hash_mismatch")
        if canonical_sha256(source_set) != contract["source_set"]["canonical_sha256"]:
            receipt["failures"].append("source_set_canonical_hash_mismatch")
        if file_sha256(protocol_path) != contract["protocol"]["file_sha256"]:
            receipt["failures"].append("protocol_file_hash_mismatch")
        if canonical_sha256(protocol) != contract["protocol"]["canonical_sha256"]:
            receipt["failures"].append("protocol_canonical_hash_mismatch")
    except Exception:
        source_set = {}
        protocol = {}
        receipt["failures"].append("source_or_protocol_unreadable")

    if not receipt["failures"]:
        try:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                model_dir, local_files_only=True, use_fast=True
            )
            if not tokenizer.is_fast:
                raise RuntimeError("fast_tokenizer_not_selected")
            tokenizer(
                [["frozen source probe", "frozen target probe"]],
                padding=True,
                truncation=True,
                max_length=32,
                return_tensors="pt",
            )
            receipt["runtime"]["fast_tokenizer_probe_passed"] = True
        except Exception as exc:
            receipt["failures"].append(
                f"fast_tokenizer_probe_failed:{type(exc).__name__}"
            )

    descriptor_path = (
        Path(contract["fs9"]["run_root"])
        / f"descriptor-job-{os.environ.get('SLURM_JOB_ID', 'unknown')}"
        / "semantic_descriptor.json"
    )
    if descriptor_path.parent.exists():
        receipt["failures"].append("descriptor_run_path_already_exists")

    if not receipt["failures"]:
        try:
            from rakl.paper3_strong_control import (
                build_semantic_descriptor_receipt,
                validate_semantic_descriptor_receipt,
            )

            descriptor_path.parent.mkdir(parents=False, exist_ok=False)
            descriptor = build_semantic_descriptor_receipt(
                source_set=source_set,
                protocol=protocol,
                model_dir=model_dir,
                created_at_utc=utc_now(),
            )
            validate_schema(
                descriptor,
                repo / "schemas/paper3-content-bound-semantic-descriptor.schema.json",
            )
            descriptor_failures = validate_semantic_descriptor_receipt(
                source_set, protocol, descriptor
            )
            atomic_write_json(descriptor_path, descriptor)
            receipt["descriptor_path"] = str(descriptor_path)
            receipt["descriptor_sha256"] = file_sha256(descriptor_path)
            receipt["descriptor_status"] = descriptor.get("status")
            receipt["descriptor_record_count"] = len(
                descriptor.get("descriptors", [])
            )
            receipt["failures"].extend(descriptor_failures)
        except Exception as exc:
            receipt["failures"].append(
                f"descriptor_runtime_failed:{type(exc).__name__}"
            )

    observed_after, after_failures = inspect_model_files(model_dir, expected_files)
    receipt["model_files_after"] = observed_after
    receipt["failures"].extend(after_failures)
    if observed_after != receipt["model_files_before"]:
        receipt["failures"].append("model_assets_changed_during_inference")
    if runtime_root.is_dir():
        receipt["runtime_tree_sha256_after"] = tree_sha256(runtime_root)
    if receipt["runtime_tree_sha256_after"] != receipt["runtime_tree_sha256_before"]:
        receipt["failures"].append("shared_runtime_changed_during_inference")

    receipt["failures"] = list(dict.fromkeys(receipt["failures"]))
    if (
        not receipt["failures"]
        and receipt["descriptor_status"] == "READY"
        and receipt["descriptor_record_count"] > 0
    ):
        receipt["verdict"] = "DESCRIPTOR_EXECUTION_PASS"
    validate_schema(receipt, execution_schema)
    atomic_write_json(output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--stage-harvest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_descriptor(
        repo=args.repo.resolve(),
        contract_path=args.contract.resolve(),
        stage_harvest_path=args.stage_harvest.resolve(),
        output=args.output.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
