"""Hostile LUNARC batch-contract completeness for Paper II microtrial v4.2–v4.4."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from frozen_source_snapshots import resolve_frozen_binding

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[1]

LANES = (
    {
        "label": "v4_2",
        "contract": "research/paper2_microtrial_v4_2/BATCH_CONTRACT_V4_2.json",
        "run_segment": "runs/v4_2",
        "receipt_segment": "receipts/v4_2",
        "log_segment": "logs/v4_2/",
        "batch_script": "experiments/paper2/lunarc/run_pendulum_microtrial_v4_2.sbatch",
        "submit_script": "experiments/paper2/lunarc/submit_pendulum_microtrial_v4_2.sh",
        "harvest_script": "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4_2.sh",
        "harvest_builder": "experiments/paper2/lunarc/build_native_harvest_receipt_v4_2.py",
        "submission_schema": "schemas/paper2-pendulum-submission-receipt-v4-2.schema.json",
        "runner_module": "paper2_pendulum_microtrial_v4_2",
        "required_roles": {
            "batch_script",
            "submission_wrapper",
            "harvest_wrapper",
            "task_seed_receipt_builder",
            "native_harvest_builder",
            "execution_packet",
            "execution_contract",
            "negative_parent_v4_1_ingest",
            "output_normalization_contract",
            "prompt_interface_contract",
            "output_normalizer",
            "prompt_interface_runner",
            "parent_runner",
            "snapshot_attester",
            "model_manifest",
            "tokenizer_manifest",
            "research_memory_review",
            "difference_witness",
        },
    },
    {
        "label": "v4_3",
        "contract": "research/paper2_microtrial_v4_3/BATCH_CONTRACT_V4_3.json",
        "run_segment": "runs/v4_3",
        "receipt_segment": "receipts/v4_3",
        "log_segment": "logs/v4_3/",
        "batch_script": "experiments/paper2/lunarc/run_pendulum_microtrial_v4_3.sbatch",
        "submit_script": "experiments/paper2/lunarc/submit_pendulum_microtrial_v4_3.sh",
        "harvest_script": "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4_3.sh",
        "harvest_builder": "experiments/paper2/lunarc/build_native_harvest_receipt_v4_3.py",
        "submission_schema": "schemas/paper2-pendulum-submission-receipt-v4-3.schema.json",
        "runner_module": "paper2_pendulum_microtrial_v4_3",
        "required_roles": {
            "batch_script",
            "submission_wrapper",
            "harvest_wrapper",
            "task_seed_receipt_builder",
            "native_harvest_builder",
            "execution_packet",
            "execution_contract",
            "negative_parent_v4_2_ingest",
            "model_staging_contract",
            "model_manifest",
            "tokenizer_manifest",
            "research_memory_review",
            "difference_witness",
        },
    },
    {
        "label": "v4_3_1",
        "contract": "research/paper2_microtrial_v4_3_1/BATCH_CONTRACT_V4_3_1.json",
        "run_segment": "runs/v4_3_1",
        "receipt_segment": "receipts/v4_3_1",
        "log_segment": "logs/v4_3_1/",
        "batch_script": "experiments/paper2/lunarc/run_pendulum_microtrial_v4_3_1.sbatch",
        "submit_script": "experiments/paper2/lunarc/submit_pendulum_microtrial_v4_3_1.sh",
        "harvest_script": "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4_3_1.sh",
        "harvest_builder": "experiments/paper2/lunarc/build_native_harvest_receipt_v4_3_1.py",
        "submission_schema": "schemas/paper2-pendulum-submission-receipt-v4-3-1.schema.json",
        "runner_module": "paper2_pendulum_microtrial_v4_3_1",
        "required_roles": {
            "batch_script",
            "submit_wrapper",
            "harvest_wrapper",
            "task_seed_builder",
            "native_harvest_builder",
            "execution_packet",
            "execution_contract",
            "negative_parent_v4_3_ingest",
            "output_normalization_contract",
            "prompt_interface_contract",
            "output_normalizer",
            "prompt_interface_runner",
            "parent_runner",
            "difference_witness",
            "research_memory_review",
        },
    },
    {
        "label": "v4_4",
        "contract": "research/paper2_microtrial_v4_4/BATCH_CONTRACT_V4_4.json",
        "run_segment": "runs/v4_4",
        "receipt_segment": "receipts/v4_4",
        "log_segment": "logs/v4_4/",
        "batch_script": "experiments/paper2/lunarc/run_pendulum_microtrial_v4_4.sbatch",
        "submit_script": "experiments/paper2/lunarc/submit_pendulum_microtrial_v4_4.sh",
        "harvest_script": "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4_4.sh",
        "harvest_builder": "experiments/paper2/lunarc/build_native_harvest_receipt_v4_4.py",
        "submission_schema": "schemas/paper2-pendulum-submission-receipt-v4-4.schema.json",
        "runner_module": "paper2_pendulum_microtrial_v4_4",
        "required_roles": {
            "batch_script",
            "submit_wrapper",
            "harvest_wrapper",
            "task_seed_builder",
            "native_harvest_builder",
            "execution_packet",
            "execution_contract",
            "parent_v4_3_1_type_b_disposition",
            "output_normalization_contract",
            "prompt_interface_contract",
            "output_normalizer",
            "prompt_interface_runner",
            "parent_runner",
            "difference_witness",
            "research_memory_review",
            "positive_control_sensitivity",
            "sealed_task",
            "direct_prompt",
            "rakl_prompt",
        },
    },
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("lane", LANES, ids=[lane["label"] for lane in LANES])
def test_batch_contract_binds_every_role_and_byte(lane: dict[str, object]) -> None:
    contract = _load(ROOT / str(lane["contract"]))
    roles = {binding["role"] for binding in contract["bindings"]}
    assert lane["required_roles"] <= roles
    for binding in contract["bindings"]:
        path = resolve_frozen_binding(ROOT, binding["path"], binding.get("sha256", ""))
        assert path.is_file(), binding["role"]
        assert _sha(path) == binding["sha256"], binding["role"]


@pytest.mark.parametrize("lane", LANES, ids=[lane["label"] for lane in LANES])
def test_shell_lane_is_separate_and_revalidates_on_allocated_node(lane: dict[str, object]) -> None:
    batch = ROOT / str(lane["batch_script"])
    submit = ROOT / str(lane["submit_script"])
    harvest = ROOT / str(lane["harvest_script"])
    for script in (batch, submit, harvest):
        subprocess.run(["bash", "-n", str(script)], check=True)
    batch_text = batch.read_text(encoding="utf-8")
    submit_text = submit.read_text(encoding="utf-8")
    assert lane["run_segment"] in batch_text
    assert lane["receipt_segment"] in batch_text
    assert lane["log_segment"] in batch_text
    assert lane["runner_module"] in batch_text
    assert lane["runner_module"] not in submit_text
    assert "rev-parse HEAD" in batch_text
    assert "refs/remotes/origin/main" in batch_text or "origin/main" in batch_text
    assert "/runs/v4/" not in batch_text
    assert "/receipts/v4/" not in batch_text


@pytest.mark.parametrize("lane", LANES, ids=[lane["label"] for lane in LANES])
def test_harvester_accepts_native_sacct_shape(lane: dict[str, object]) -> None:
    helper = ROOT / str(lane["harvest_builder"])
    spec = importlib.util.spec_from_file_location(f"harvest_{lane['label']}", helper)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sacct = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/"
        "SACCT_NATIVE_V3_2_JOBS_3475123_3475124.json"
    )
    row, failures = module.validate_sacct_root_row(sacct, "3475124")
    assert failures == []
    assert row is not None


@pytest.mark.parametrize("lane", LANES, ids=[lane["label"] for lane in LANES])
def test_submission_schema_is_valid(lane: dict[str, object]) -> None:
    schema = _load(ROOT / str(lane["submission_schema"]))
    jsonschema.Draft202012Validator.check_schema(schema)
