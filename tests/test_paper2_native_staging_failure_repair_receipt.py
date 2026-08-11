from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_STAGING_FAILURE_REPAIR_RECEIPT_20260811.json"
CONTRACT_V3 = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3.json"
CONTRACT_V3_1 = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_1.json"
SUBJECT = "1a9d3079571e1f1278e32061665be885845bd5cf"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _contract_self_digest(contract: dict) -> str:
    candidate = json.loads(json.dumps(contract))
    self_binding = next(x for x in candidate["bindings"] if x["role"] == "contract_self")
    self_binding["sha256"] = "0" * 64
    return _canonical(candidate)


def test_failure_repair_receipt_binds_all_native_bytes_and_chronology() -> None:
    receipt = _load(RECEIPT)
    expected = {
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_1A9D307.json": "04491a6b7f19a273bf6999129ede1370e6e88155b9aa9cd1f1ce92fe30c29caa",
        "research/paper2_microtrial_v3/native_receipts/SUBMISSION_NATIVE_1A9D307.json": "b0201f857b0602609f9a60263838d8b8a7dc6dc30d2b80adc86f556393a7e11a",
        "research/paper2_microtrial_v3/native_receipts/NETWORK_PROBE_NATIVE_JOB_3475080.json": "0bbc37f1751e5aaf27b470a619571447dae9f938691c07ad75dc1a47ec29f1d5",
        "research/paper2_microtrial_v3/native_receipts/STAGING_FAILURE_NATIVE_JOB_3475081.json": "8a6a4f0f87adeedc1c4f48d8adad77e9482775cf52a4fac21000daae4c02f041",
        "research/paper2_microtrial_v3/native_receipts/HARVEST_FIRST_NATIVE_1A9D307.json": "69d9355be08b592994842168f54c96c8d1d76ab35a07ab78dcab6a4d115b5c6c",
        "research/paper2_microtrial_v3/native_receipts/HARVEST_REPEAT_NATIVE_JOBS_3475080_3475081.json": "a5f21c31d8af27e037e5ca8b853bd3ec13c30aa5c41bcaed7508cd9ceb5e012d",
        "research/paper2_microtrial_v3/native_receipts/SACCT_NATIVE_JOBS_3475080_3475081.json": "1b145f337474a52d6a3a1204eb34d5d95480a045beb417f8e25e18e8e2c0ecb3",
        "research/paper2_microtrial_v3/native_receipts/STAGING_FAILURE_LOCALIZATION_NATIVE_JOB_3475081.json": "2bc40351a262d454e8b09a11d76ef26654350228e48acc82e8c0e83da0877e8a",
        "research/paper2_microtrial_v3/native_logs/NETWORK_PROBE_JOB_3475080.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "research/paper2_microtrial_v3/native_logs/STAGE_CPU_JOB_3475081.out": "b743d4fbe080c6396f89703ffbcb38b01242702f1fc17e56808f1c94cde7eca0",
        "research/paper2_microtrial_v3/native_bundles/PAPER2_STAGE_NEGATIVE_JOBS_3475080_3475081.tar.gz": "d1af52f3d1cae6591a77763b5b6ad003c5a8b45585a5c16d2787f9769d2d6cce",
    }
    bound = {x["path"]: x["sha256"] for x in receipt["native_receipts_and_raw_evidence"]}
    assert bound == expected
    for relative, digest in expected.items():
        assert _sha256(ROOT / relative) == digest

    times = [x["created_or_observed_at_utc"] for x in receipt["chronology"]]
    assert times == sorted(times)
    assert [x["event"] for x in receipt["chronology"]][-2:] == [
        "repeat_harvest",
        "read_only_localization",
    ]


def test_native_failure_and_bounded_localization_are_not_promoted() -> None:
    receipt = _load(RECEIPT)
    assert receipt["subject_sha"] == SUBJECT
    assert receipt["execution_counts"] == {
        "evaluated_result_records": 0,
        "jobs_submitted": 2,
        "model_executions": 0,
    }
    assert receipt["scheduler_result"]["rows"] == [
        {"elapsed": "00:00:06", "exit_code": "0:0", "job_id": "3475080", "max_rss": "", "node_list": "cn004", "state": "COMPLETED"},
        {"elapsed": "00:00:04", "exit_code": "2:0", "job_id": "3475081", "max_rss": "", "node_list": "cn004", "state": "FAILED"},
    ]
    assert receipt["native_result"]["probe_all_reachable_http_200"] is True
    assert receipt["native_result"]["staging_verdict"] == "STAGING_FAILED_PRESERVED"
    assert receipt["native_result"]["candidate_preserved"] is True
    assert receipt["native_result"]["final_exists"] is False
    localization = receipt["localization"]
    assert localization["present_artifact_count"] == 25
    assert localization["identity_matching_present_artifact_count"] == 25
    assert localization["first_missing_artifact"]["artifact_id"] == "wheel:torch==2.8.0+cpu"
    assert "not direct proof" in localization["inference_boundary"]
    assert receipt["figure_update"]["quantitative_figure_generated"] is False


def test_v3_is_immutable_and_v3_1_repair_is_exactly_bound_not_submitted() -> None:
    receipt = _load(RECEIPT)
    v3 = _load(CONTRACT_V3)
    protected = receipt["protected_v3_negative_history"]
    assert protected["contract_file_sha256"] == _sha256(CONTRACT_V3) == "feb58629a45aca008cb148e815ba6cf1e6fc3f96822358248729ea8f7274edc3"
    assert protected["contract_canonical_sha256"] == _canonical(v3) == "22cee21eacefacae2af44c735ce37e73efabc41af1bd2952089e8fcb7ca0f2a1"
    assert protected["runtime_sha256"] == _sha256(ROOT / protected["runtime_path"]) == "73195a4368fcabef68520a5b666eb8cc2a96f26ceed0e1f62199060e96de62fb"
    assert protected["failed_candidate_superseded_or_deleted"] is False
    assert protected["v3_contract_mutated_for_repair"] is False

    repair = receipt["v3_1_repair"]
    contract = _load(CONTRACT_V3_1)
    assert receipt["chronology"][-1]["created_or_observed_at_utc"] < contract[
        "created_at_utc"
    ] <= receipt["created_at_utc"]
    assert repair["contract_file_sha256"] == _sha256(CONTRACT_V3_1)
    assert repair["contract_canonical_sha256"] == _canonical(contract)
    assert repair["contract_self_canonical_zeroed_sha256"] == _contract_self_digest(contract)
    assert repair["contract_self_canonical_zeroed_sha256"] == next(
        x["sha256"] for x in contract["bindings"] if x["role"] == "contract_self"
    )
    for binding in contract["bindings"]:
        if binding["role"] == "contract_self":
            continue
        assert _sha256(ROOT / binding["path"]) == binding["sha256"]
    assert repair["operator_state"] == "REPAIR_READY_NOT_SUBMITTED"
    assert repair["harvest_policy"][
        "missing_or_ambiguous_evidence_verdict"
    ] == "HARVEST_CANNOT_CHECK"
    assert repair["harvest_policy"][
        "exactly_one_scheduler_root_row_per_submitted_job_required"
    ] is True
    assert repair["native_submission_performed"] is False
    assert repair["native_result_available"] is False
    assert receipt["verdict"] == "NATIVE_V3_STAGING_FAILURE_PRESERVED__V3_1_REPAIR_READY_NOT_SUBMITTED"
    assert "not v3.1 native staging success" in receipt["claim_boundary"].lower()
