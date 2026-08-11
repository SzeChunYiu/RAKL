from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import subprocess

import pytest

jsonschema = pytest.importorskip("jsonschema")

from rakl.paper2_pendulum_microtrial import MicrotrialPreflightVerdict, audit_execution_packet

from frozen_source_snapshots import execution_time_base_dir, resolve_frozen_binding


ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "research/paper2_microtrial_v4"
PACKET = V4 / "EXECUTION_PACKET_V4_20260811.json"
CONTRACT = V4 / "BATCH_CONTRACT_V4.json"
READINESS = V4 / "PAPER2_V4_FROZEN_BATCH_READINESS_RECEIPT_20260811.json"
REVIEW = V4 / "PAPER2_V4_INTERNAL_HOSTILE_REVIEW_20260811.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v4_packet_is_chronology_fresh_and_narrowly_scoped() -> None:
    packet = _load(PACKET)
    assert packet["subject_sha"] == "af2d0be61522d1f8f657a48daaf6369ff3e44a3e"
    assert packet["evaluated_results_opened_before_freeze"] is False
    assert packet["evaluated_task_seed_unit_count_before_freeze"] == 0
    assert packet["registered_task_id"] == "PENDULUM_SEALED_KNOWN_ANSWER_001"
    assert packet["seed_schedule"] == [17]
    assert packet["evidence_access_level"] == "COMPLETE_SEALED"
    assert packet["architecture_scope"] == ["DIRECT_CORPUS", "RAKL_CONTEXT"]
    assert "cannot establish architecture superiority" in packet["claim_boundary"]


def test_v4_packet_has_no_invalid_binding_and_fails_closed_off_lunarc(tmp_path) -> None:
    packet = _load(PACKET)
    report = audit_execution_packet(
        packet,
        base_dir=execution_time_base_dir(ROOT, packet, tmp_path),
        runtime_versions={
            "python": "3.11.13",
            "torch": "2.8.0+cpu",
            "transformers": "4.55.0",
            "tokenizers": "0.21.4",
            "safetensors": "0.6.2",
        },
        observed_at_utc="2026-08-11T03:40:00Z",
    )
    assert report.verdict is MicrotrialPreflightVerdict.CANNOT_CHECK
    assert report.invalid_bindings == ()
    assert any(item.startswith("local_model_file_missing:") for item in report.blockers)
    if platform.system() != "Linux":
        assert f"runtime_platform_mismatch:os:{platform.system()}!=Linux" in report.blockers
    assert report.evaluated_result_record_count == 0


def test_v4_batch_contract_binds_every_executable_and_native_parent() -> None:
    contract = _load(CONTRACT)
    assert contract["status"] == "FROZEN_READY_NOT_SUBMITTED"
    assert contract["task_id"] == "PENDULUM_SEALED_KNOWN_ANSWER_001"
    assert contract["seed_schedule"] == [17]
    assert contract["expected_output"] == {
        "arm_records": 2,
        "output_root": "/projects/hep/fs9/users/scyiu/RAKL-paper2/runs/v4",
        "receipt_root": "/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v4",
        "task_seed_units": 1,
    }
    roles = {binding["role"] for binding in contract["bindings"]}
    assert {
        "execution_packet",
        "batch_script",
        "submission_wrapper",
        "harvest_wrapper",
        "task_seed_receipt_builder",
        "native_staging_receipt",
        "native_staging_harvest",
        "chronology_corrected_staging_synthesis",
    } <= roles
    for binding in contract["bindings"]:
        path = resolve_frozen_binding(ROOT, binding["path"], binding.get("sha256", ""))
        assert path.is_file(), binding["role"]
        assert _sha256(path) == binding["sha256"], binding["role"]


def test_v4_scheduler_account_matches_the_successful_native_parent() -> None:
    contract = _load(CONTRACT)
    sacct = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/"
        "SACCT_NATIVE_V3_2_JOBS_3475123_3475124.json"
    )
    stage = next(row for row in sacct["jobs"] if row["job_id"] == 3475124)
    assert contract["resource_request"]["account"] == stage["account"] == "lu2026-2-51"
    assert contract["resource_request"]["partition"] == stage["partition"] == "lu48"


def test_v4_shell_artifacts_parse_and_execute_only_inside_slurm() -> None:
    scripts = (
        ROOT / "experiments/paper2/lunarc/run_pendulum_microtrial_v4.sbatch",
        ROOT / "experiments/paper2/lunarc/submit_pendulum_microtrial_v4.sh",
        ROOT / "experiments/paper2/lunarc/harvest_pendulum_microtrial_v4.sh",
    )
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)
    batch = scripts[0].read_text(encoding="utf-8")
    submit = scripts[1].read_text(encoding="utf-8")
    assert "${SLURM_JOB_ID:?" in batch
    assert "-m rakl.paper2_pendulum_microtrial run" in batch
    assert "build_task_seed_receipt_v4.py" in batch
    assert "paper2_pendulum_microtrial run" not in submit


def test_v4_harvester_matches_real_lunarc_sacct_json_shape() -> None:
    helper = ROOT / "experiments/paper2/lunarc/build_native_harvest_receipt_v4.py"
    spec = importlib.util.spec_from_file_location("paper2_v4_harvest", helper)
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
    assert row["job_id"] == 3475124
    assert row["state"]["current"] == ["COMPLETED"]
    assert row["exit_code"]["status"] == ["SUCCESS"]
    assert row["exit_code"]["return_code"]["number"] == 0


def test_v4_receipt_schemas_accept_only_typed_identity_bound_examples() -> None:
    checker = jsonschema.FormatChecker()
    sha = "a" * 64
    gitsha = "b" * 40
    submission = {
        "schema_version": "paper2-pendulum-submission-receipt-v4",
        "created_at_utc": "2026-08-11T03:45:00Z",
        "verdict": "SUBMITTED_NONCONFIRMATORY_TASK_SEED_BATCH",
        "expected_repo_sha": gitsha,
        "packet_parent_sha": "c" * 40,
        "batch_contract_sha256": sha,
        "slurm_job_id": "123",
        "model_execution_observed_by_submitter": False,
        "evaluated_result_record_count_observed_by_submitter": 0,
        "claim_boundary": "submission only",
    }
    schema = _load(ROOT / "schemas/paper2-pendulum-submission-receipt-v4.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=checker).validate(submission)
    mutated = dict(submission, packet_parent_sha=submission["expected_repo_sha"])
    # Equal values are schema-valid but remain separately named coordinates; runtime
    # provenance checks, not the schema, decide whether equality is factual.
    jsonschema.Draft202012Validator(schema, format_checker=checker).validate(mutated)
    invalid = dict(submission, evaluated_result_record_count_observed_by_submitter=1)
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(invalid))


def test_v4_batch_attests_all_eight_snapshot_files_before_and_after() -> None:
    model = _load(V4 / "MODEL_MANIFEST_V4.json")
    tokenizer = _load(V4 / "TOKENIZER_MANIFEST_V4.json")
    assert len(model["files"]) + len(tokenizer["files"]) == 8
    assert len({entry["path"] for entry in model["files"] + tokenizer["files"]}) == 8
    batch = (ROOT / "experiments/paper2/lunarc/run_pendulum_microtrial_v4.sbatch").read_text(
        encoding="utf-8"
    )
    assert batch.count("attest_model_snapshot_v4.py") >= 1
    assert "--phase PRE_INFERENCE" in batch
    assert "--phase POST_INFERENCE" in batch
    builder = (
        ROOT / "experiments/paper2/lunarc/build_task_seed_receipt_v4.py"
    ).read_text(encoding="utf-8")
    assert "snapshot changed across inference" in builder
    assert '"packet_parent_sha": result["subject_sha"]' in builder
    assert '"execution_checkout": result["execution_checkout"]' in builder


def test_v4_readiness_and_internal_review_remain_fail_closed() -> None:
    receipt = _load(READINESS)
    assert receipt["verdict"] == "CANNOT_CHECK_NOT_MERGED_NOT_SUBMITTED"
    assert receipt["counts"] == {
        "evaluated_arm_records": 0,
        "evaluated_task_seed_units": 0,
        "jobs_submitted": 0,
        "model_executions": 0,
        "quantitative_figures_generated": 0,
    }
    assert receipt["bindings"]["batch_contract"]["sha256"] == _sha256(CONTRACT)
    assert "v4_job_not_submitted" in receipt["blockers"]
    assert len(receipt["matched_study_residuals"]) == 6

    review = _load(REVIEW)
    assert review["review_class"] == "same_context_internal_not_independent"
    assert review["subject"]["sha256"] == _sha256(READINESS)
    assert review["blocking_concerns"] == []
    assert review["verdict"].endswith("NATIVE_EXECUTION_STILL_CANNOT_CHECK")
