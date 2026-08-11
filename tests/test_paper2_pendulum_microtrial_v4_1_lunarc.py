from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

from frozen_source_snapshots import execution_time_base_dir, resolve_frozen_binding

jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
V41 = ROOT / "research/paper2_microtrial_v4_1"
CONTRACT = V41 / "BATCH_CONTRACT_V4_1.json"
READINESS = V41 / "PAPER2_V4_1_LUNARC_BATCH_READINESS_RECEIPT_20260811.json"
REVIEW = V41 / "PAPER2_V4_1_LUNARC_INTERNAL_REVIEW_20260811.json"
POLICY_ID = "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v4_1_batch_is_adaptive_but_fresh_to_v4_1_outputs() -> None:
    contract = _load(CONTRACT)
    assert contract["status"] == "FROZEN_READY_NOT_SUBMITTED"
    assert contract["chronology_class"] == "ADAPTIVE_PARSER_REPLAY_FRESH_ONLY_TO_V4_1_OUTPUTS"
    assert contract["parent_v4_results_opened_before_batch_freeze"] is True
    assert contract["v4_1_outputs_opened_before_batch_freeze"] is False
    assert contract["v4_1_evaluated_arm_record_count_at_batch_freeze"] == 0
    assert contract["v4_1_evaluated_task_seed_unit_count_at_batch_freeze"] == 0
    assert "fresh only to V4.1 outputs" in contract["adaptation_chronology"]
    assert contract["output_normalization_policy_id"] == POLICY_ID
    assert contract["v4_reinterpretation_permitted"] is False
    assert contract["packet_parent_sha"] == "3bf46b505af249802faa277d3ec865f4d9664853"
    assert contract["minimum_execution_ancestor_sha"] == contract["packet_parent_sha"]
    assert contract["post_merge_head_binding"] == {
        "environment_variable": "EXPECTED_REPO_SHA",
        "required_equal_refs": ["HEAD", "refs/remotes/origin/main"],
        "sha_frozen_pre_merge": False,
    }


def test_v4_1_batch_contract_binds_every_execution_and_negative_parent_byte() -> None:
    contract = _load(CONTRACT)
    roles = {binding["role"] for binding in contract["bindings"]}
    assert {
        "batch_script",
        "submission_wrapper",
        "harvest_wrapper",
        "task_seed_receipt_builder",
        "native_harvest_builder",
        "output_normalization_contract",
        "output_normalizing_runner",
        "parent_runner",
        "negative_parent_v4_ingest",
        "execution_packet",
        "execution_contract",
        "snapshot_attester",
        "model_manifest",
        "tokenizer_manifest",
    } <= roles
    for binding in contract["bindings"]:
        path = resolve_frozen_binding(ROOT, binding["path"], binding.get("sha256", ""))
        assert path.is_file(), binding["role"]
        assert _sha(path) == binding["sha256"], binding["role"]


def test_v4_1_shell_lane_is_separate_and_revalidates_on_allocated_node() -> None:
    batch = ROOT / "experiments/paper2/lunarc/run_pendulum_microtrial_v4_1.sbatch"
    submit = ROOT / "experiments/paper2/lunarc/submit_pendulum_microtrial_v4_1.sh"
    harvest = ROOT / "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4_1.sh"
    for script in (batch, submit, harvest):
        subprocess.run(["bash", "-n", str(script)], check=True)
    batch_text = batch.read_text(encoding="utf-8")
    submit_text = submit.read_text(encoding="utf-8")
    harvest_text = harvest.read_text(encoding="utf-8")
    assert "/logs/v4_1/" in batch_text
    assert 'RUN_ROOT="$ROOT/runs/v4_1"' in batch_text
    assert 'RECEIPT_DIR="$ROOT/receipts/v4_1/job-${SLURM_JOB_ID}"' in batch_text
    assert "/runs/v4/" not in batch_text + submit_text + harvest_text
    assert "/receipts/v4/" not in batch_text + submit_text + harvest_text
    assert "paper2_pendulum_microtrial_v4_1" in batch_text
    assert "allocated binding mismatch" in batch_text
    assert "parent_v4_results_opened_before_batch_freeze" in batch_text
    assert 'rev-parse refs/remotes/origin/main' in batch_text
    assert 'rev-parse","refs/remotes/origin/main' in submit_text
    assert '--expected-checkout-head-sha "$EXPECTED_REPO_SHA"' in batch_text
    assert "-m rakl.paper2_pendulum_microtrial preflight" in batch_text
    assert "status --porcelain --untracked-files=all" in batch_text
    assert "rev-parse HEAD" in batch_text
    assert "paper2_pendulum_microtrial_v4_1" not in submit_text


def test_v4_1_task_and_submission_schemas_are_policy_bound() -> None:
    checker = jsonschema.FormatChecker()
    sha = "a" * 64
    submission = {
        "schema_version": "paper2-pendulum-submission-receipt-v4.1",
        "created_at_utc": "2026-08-11T04:30:00Z",
        "verdict": "SUBMITTED_NONCONFIRMATORY_V4_1_TASK_SEED_BATCH",
        "expected_repo_sha": "b" * 40,
        "packet_parent_sha": "c" * 40,
        "batch_contract_sha256": sha,
        "execution_packet_sha256": sha,
        "output_normalization_contract_sha256": sha,
        "output_normalization_policy_id": POLICY_ID,
        "slurm_job_id": "123",
        "model_execution_observed_by_submitter": False,
        "evaluated_result_record_count_observed_by_submitter": 0,
        "v4_reinterpretation_permitted": False,
        "claim_boundary": "submission only",
    }
    schema = _load(ROOT / "schemas/paper2-pendulum-submission-receipt-v4-1.schema.json")
    validator = jsonschema.Draft202012Validator(schema, format_checker=checker)
    validator.validate(submission)
    assert list(validator.iter_errors(dict(submission, v4_reinterpretation_permitted=True)))
    assert list(validator.iter_errors(dict(submission, output_normalization_policy_id="POSTHOC")))


def test_v4_1_harvester_accepts_native_sacct_shape_and_rejects_ambiguity() -> None:
    helper = ROOT / "experiments/paper2/lunarc/build_native_harvest_receipt_v4_1.py"
    spec = importlib.util.spec_from_file_location("paper2_v41_harvest", helper)
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
    assert row is not None and row["job_id"] == 3475124
    assert module.validate_sacct_root_row({"jobs": []}, "3475124") == (
        None,
        ["scheduler_root_row_not_unique"],
    )
    duplicate = {"jobs": [row, dict(row)]}
    assert module.validate_sacct_root_row(duplicate, "3475124")[1] == [
        "scheduler_root_row_not_unique"
    ]


def test_v4_1_readiness_and_internal_review_make_no_result_claim() -> None:
    readiness = _load(READINESS)
    assert readiness["verdict"] == "READY_AFTER_MERGE_NOT_SUBMITTED"
    assert readiness["counts"] == {
        "v4_1_arm_records": 0,
        "v4_1_evaluated_task_seed_units": 0,
        "v4_1_jobs_submitted": 0,
        "v4_1_model_executions": 0,
        "quantitative_figures_generated": 0,
    }
    assert readiness["parent_v4_results_opened"] is True
    assert readiness["v4_1_outputs_observed"] is False
    assert readiness["bindings"]["batch_contract_sha256"] == _sha(CONTRACT)
    review = _load(REVIEW)
    assert review["review_class"] == "same_context_internal_not_independent"
    assert review["subject"]["sha256"] == _sha(READINESS)
    assert review["blocking_concerns"] == []
    assert review["verdict"] == "INTERNAL_PACKET_PASS_NATIVE_RESULT_ABSENT"


def test_original_v4_batch_contract_bytes_remain_unchanged() -> None:
    path = ROOT / "research/paper2_microtrial_v4/BATCH_CONTRACT_V4.json"
    assert _sha(path) == "07eda3b715e84deaa7565f6077ddbe71c0515e59925b714cab188e6b1672591d"
