from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "research/paper3_semantic_descriptor_lunarc"
CONTRACT = LANE / "CONTRACT_V1.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _common_module():
    path = ROOT / "experiments/paper3/lunarc/semantic_descriptor_common.py"
    spec = importlib.util.spec_from_file_location("semantic_descriptor_common", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_is_label_blind_cpu_and_two_allocated_jobs() -> None:
    contract = _load(CONTRACT)
    assert contract["frozen_parent_sha"] == "23f18c73740aefbfbf3bb4f49ab3a3f548b5ee2a"
    assert contract["chronology"] == {
        "descriptor_before_external_labels": True,
        "evaluated_results_accessed": False,
        "jobs_submitted_at_freeze": 0,
        "model_stage_before_descriptor": True,
    }
    assert contract["scheduler"] == {
        "account": "lu2026-2-51",
        "descriptor_device": "cpu",
        "descriptor_is_separate_allocated_batch": True,
        "partition": "lu48",
        "stage_is_allocated_batch": True,
    }
    assert contract["runtime"]["shared_assets_read_only"] is True
    assert contract["runtime"]["fast_tokenizer_required"] is True
    assert contract["runtime"]["sentencepiece_optional_only_if_fast_probe_passes"] is True
    assert contract["model"]["revision"] == "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    assert len(contract["model"]["required_files"]) == 6


def test_contract_binds_every_executable_and_frozen_input() -> None:
    contract = _load(CONTRACT)
    roles = {binding["role"] for binding in contract["bindings"]}
    assert {
        "common_runtime",
        "stage_runtime",
        "stage_batch",
        "stage_submitter",
        "descriptor_runtime",
        "descriptor_batch",
        "descriptor_submitter",
        "harvest_builder",
        "harvest_wrapper",
        "frozen_descriptor_implementation",
        "frozen_protocol",
        "frozen_source_set",
        "shared_runtime_provenance",
    } <= roles
    assert len(roles) == len(contract["bindings"])
    for binding in contract["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["role"]
        assert _sha(path) == binding["sha256"], binding["role"]


def test_contract_and_receipt_schemas_are_valid() -> None:
    checker = jsonschema.FormatChecker()
    schema_names = (
        "paper3-semantic-lunarc-contract-v1.schema.json",
        "paper3-semantic-lunarc-submission-v1.schema.json",
        "paper3-semantic-model-stage-execution-v1.schema.json",
        "paper3-semantic-descriptor-execution-v1.schema.json",
        "paper3-semantic-lunarc-harvest-v1.schema.json",
    )
    for name in schema_names:
        schema = _load(ROOT / "schemas" / name)
        jsonschema.Draft202012Validator.check_schema(schema)
    contract_schema = _load(
        ROOT / "schemas/paper3-semantic-lunarc-contract-v1.schema.json"
    )
    jsonschema.Draft202012Validator(
        contract_schema, format_checker=checker
    ).validate(_load(CONTRACT))


def test_submission_schema_requires_stage_lineage_for_descriptor() -> None:
    schema = _load(ROOT / "schemas/paper3-semantic-lunarc-submission-v1.schema.json")
    validator = jsonschema.Draft202012Validator(schema)
    sha = "a" * 64
    gitsha = "b" * 40
    receipt = {
        "schema_version": "paper3-semantic-lunarc-submission-v1",
        "created_at_utc": "2026-08-11T05:30:00Z",
        "phase": "DESCRIPTOR",
        "verdict": "SUBMITTED_DESCRIPTOR_BATCH_AFTER_STAGE_PASS",
        "expected_repo_sha": gitsha,
        "frozen_parent_sha": "c" * 40,
        "contract_sha256": sha,
        "slurm_job_id": "123",
        "parent_stage_job_id": "122",
        "parent_stage_harvest_sha256": sha,
        "model_execution_observed_by_submitter": False,
        "descriptor_record_count_observed_by_submitter": 0,
        "claim_boundary": "submission only",
    }
    assert list(validator.iter_errors(receipt)) == []
    invalid = dict(receipt, parent_stage_job_id=None)
    assert list(validator.iter_errors(invalid))


def test_model_inspection_fails_closed_on_missing_or_mutated_asset(tmp_path: Path) -> None:
    common = _common_module()
    expected = [
        {
            "path": "tiny.bin",
            "bytes": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
        }
    ]
    observed, failures = common.inspect_model_files(tmp_path, expected)
    assert observed == []
    assert failures == ["model_asset_missing:tiny.bin"]
    (tmp_path / "tiny.bin").write_bytes(b"abd")
    observed, failures = common.inspect_model_files(tmp_path, expected)
    assert observed[0]["bytes"] == 3
    assert failures == ["model_asset_sha256_mismatch:tiny.bin"]


def test_repo_binding_requires_exact_origin_main_not_clean_side_branch(
    tmp_path: Path,
) -> None:
    common = _common_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("parent\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "parent"], cwd=repo, check=True)
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/SzeChunYiu/RAKL.git"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", parent], cwd=repo, check=True)
    (repo / "a.txt").write_text("side branch\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "side"], cwd=repo, check=True)
    side = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()
    contract_path = repo / "contract.json"
    contract_path.write_text(
        json.dumps({"frozen_parent_sha": parent, "bindings": []}) + "\n",
        encoding="utf-8",
    )
    _, failures = common.validate_repo_and_contract(
        repo=repo, contract_path=contract_path, expected_repo_sha=side
    )
    assert "origin_main_sha_mismatch" in failures


def test_stage_runtime_types_missing_model_parent_instead_of_crashing() -> None:
    source = (
        ROOT / "experiments/paper3/lunarc/stage_semantic_model.py"
    ).read_text(encoding="utf-8")
    assert "model_parent_directory_missing" in source
    assert "if not final.parent.is_dir()" in source


def test_sacct_parser_requires_completed_successful_root_row() -> None:
    common = _common_module()
    success = {
        "jobs": [
            {
                "job_id": 123,
                "state": {"current": ["COMPLETED"]},
                "exit_code": {
                    "status": ["SUCCESS"],
                    "return_code": {"number": 0},
                },
            }
        ]
    }
    _, failures = common.root_sacct_row(success, "123")
    assert failures == []
    success["jobs"][0]["state"]["current"] = ["FAILED"]
    _, failures = common.root_sacct_row(success, "123")
    assert "slurm_root_not_completed" in failures


def test_shells_parse_and_only_descriptor_batch_can_run_model() -> None:
    scripts = [
        ROOT / "experiments/paper3/lunarc/stage_semantic_model.sbatch",
        ROOT / "experiments/paper3/lunarc/submit_semantic_model_stage.sh",
        ROOT / "experiments/paper3/lunarc/run_semantic_descriptor.sbatch",
        ROOT / "experiments/paper3/lunarc/submit_semantic_descriptor.sh",
        ROOT / "experiments/paper3/lunarc/harvest_semantic_descriptor.sh",
    ]
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)
    stage_submit = scripts[1].read_text(encoding="utf-8")
    descriptor_submit = scripts[3].read_text(encoding="utf-8")
    stage_batch = scripts[0].read_text(encoding="utf-8")
    descriptor_batch = scripts[2].read_text(encoding="utf-8")
    assert "sbatch --parsable" in stage_submit
    assert "sbatch --parsable" in descriptor_submit
    assert "semantic_descriptor_runtime.py" not in stage_batch
    assert "semantic_descriptor_runtime.py" in descriptor_batch
    assert "HARVEST_MODEL_STAGE_PASS" in descriptor_submit
    assert "#SBATCH --partition=lu48" in stage_batch
    assert "#SBATCH --partition=lu48" in descriptor_batch


def test_runtime_enforces_offline_fast_tokenizer_and_immutability() -> None:
    batch = (
        ROOT / "experiments/paper3/lunarc/run_semantic_descriptor.sbatch"
    ).read_text(encoding="utf-8")
    runtime = (
        ROOT / "experiments/paper3/lunarc/semantic_descriptor_runtime.py"
    ).read_text(encoding="utf-8")
    assert "HF_HUB_OFFLINE=1" in batch
    assert "TRANSFORMERS_OFFLINE=1" in batch
    assert "use_fast=True" in runtime
    assert "tree_sha256(runtime_root)" in runtime
    assert "model_assets_changed_during_inference" in runtime
    assert "shared_runtime_changed_during_inference" in runtime
    assert "build_semantic_descriptor_receipt" in runtime


def test_current_readiness_contains_no_result_or_job() -> None:
    receipt = _load(
        ROOT
        / "research/receipts/PAPER3_SEMANTIC_DESCRIPTOR_LUNARC_READINESS_20260811.json"
    )
    assert receipt["verdict"] == "CANNOT_CHECK_NOT_MERGED_NOT_SUBMITTED"
    assert receipt["counts"] == {
        "descriptor_records": 0,
        "descriptor_jobs_submitted": 0,
        "model_executions": 0,
        "model_stage_jobs_submitted": 0,
        "quantitative_figures_generated": 0,
    }
    assert receipt["label_access"] == {
        "adjudication_accessed": False,
        "evaluated_result_accessed": False,
        "external_annotation_accessed": False,
    }
