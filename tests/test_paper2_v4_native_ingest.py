from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rakl.paper2_pendulum_microtrial import MicrotrialPreflightVerdict, audit_execution_packet
from rakl.paper2_pendulum_microtrial_v4_1 import normalize_pendulum_output_v4_1

jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "research/paper2_microtrial_v4"
NATIVE = V4 / "native_job_3475193"
RUN = NATIVE / "runs/v4/PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17-job-3475193"
INGEST = V4 / "PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json"
V41 = ROOT / "research/paper2_microtrial_v4_1"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_native_ingest_schema_and_every_copied_byte_are_bound() -> None:
    receipt = _load(INGEST)
    schema = _load(ROOT / "schemas/paper2-v4-native-ingest-receipt.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(receipt)
    bundle = receipt["source_bundle"]
    bundle_path = ROOT / bundle["path"]
    assert bundle_path.stat().st_size == bundle["bytes"]
    assert _sha(bundle_path) == bundle["sha256"] == "bd022645b0c61c02182c90e6208a59e10d9ed101c21bf5719a8322e034770481"
    assert len(receipt["source_files"]) == 19
    for item in receipt["source_files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert _sha(path) == item["sha256"]


def test_native_scheduler_and_snapshot_chain_pass_without_score_authority() -> None:
    receipt = _load(INGEST)
    native = receipt["native_execution"]
    assert native["scheduler_state"] == ["COMPLETED"]
    assert native["scheduler_exit_status"] == ["SUCCESS"]
    assert native["scheduler_return_code"] == 0
    assert native["scheduler_elapsed_seconds"] == 64
    assert native["governed_harvest_verdict"] == "HARVEST_TASK_SEED_PASS_NONCONFIRMATORY"
    assert native["pre_post_snapshot_identity_equal"] is True
    assert native["snapshot_file_count"] == 8
    assert native["execution_checkout"]["head_sha"] == "3bf46b505af249802faa277d3ec865f4d9664853"
    assert native["packet_parent_sha"] == "af2d0be61522d1f8f657a48daaf6369ff3e44a3e"


def test_v4_both_frozen_scores_remain_parse_invalid_nulls() -> None:
    result = _load(RUN / "result_receipt.json")
    blinded = _load(RUN / "blinded_scores.json")
    assert {record["condition"] for record in result["records"]} == {"DIRECT_CORPUS", "RAKL_CONTEXT"}
    assert all(record["score"]["parse_valid"] is False for record in result["records"])
    assert all(record["score"]["score"] is None for record in result["records"])
    assert all(score["parse_error"] == "model output is not a JSON object" for score in blinded["scores"])
    ingest = _load(INGEST)
    outcome = ingest["task_seed_outcome"]
    assert outcome["frozen_parse_valid_arm_count"] == 0
    assert outcome["frozen_scorable_arm_count"] == 0
    assert outcome["score_comparison_permitted"] is False
    assert outcome["posthoc_normalized_scores_authorized"] is False
    assert ingest["quantitative_figure_generated"] is False


def test_v4_1_candidate_does_not_rescue_v4_and_rejects_trailing_prose() -> None:
    records = {record["condition"]: record for record in _load(RUN / "result_receipt.json")["records"]}
    rakl_raw = records["RAKL_CONTEXT"]["raw_output"]["raw_text"]
    direct_raw = records["DIRECT_CORPUS"]["raw_output"]["raw_text"]
    assert normalize_pendulum_output_v4_1(rakl_raw).startswith("{")
    try:
        normalize_pendulum_output_v4_1(direct_raw)
    except ValueError as exc:
        assert "nonexact serialization" in str(exc)
    else:
        raise AssertionError("V4.1 must reject fenced JSON followed by prose")
    assert _load(V41 / "OUTPUT_NORMALIZATION_CONTRACT_V4_1.json")["v4_reinterpretation_permitted"] is False


def test_v4_1_packet_is_fresh_hash_bound_and_not_executed() -> None:
    packet_path = V41 / "EXECUTION_PACKET_V4_1_20260811.json"
    packet = _load(packet_path)
    assert packet["freeze_created_at_utc"] > "2026-08-11T04:03:09Z"
    assert packet["parent_v4_outputs_observed_before_v4_1_freeze"] is True
    assert packet["v4_1_outputs_opened_before_freeze"] is False
    assert packet["evaluated_results_opened_before_freeze"] is False
    assert packet["v4_negative_history"]["frozen_scorable_arm_count"] == 0
    for name in ("output_normalizer", "output_normalization_contract", "v4_native_ingest"):
        binding = packet["bindings"][name]
        assert _sha(ROOT / binding["path"]) == binding["sha256"]
    report = audit_execution_packet(
        packet,
        base_dir=ROOT,
        runtime_versions={
            "python": "3.11.13",
            "torch": "2.8.0+cpu",
            "transformers": "4.55.0",
            "tokenizers": "0.21.4",
            "safetensors": "0.6.2",
        },
        observed_at_utc="2026-08-11T04:11:00Z",
    )
    assert report.verdict is MicrotrialPreflightVerdict.CANNOT_CHECK
    assert report.invalid_bindings == ()
    readiness = _load(V41 / "PAPER2_V4_1_READINESS_RECEIPT_20260811.json")
    assert readiness["verdict"] == "FROZEN_NOT_MERGED_NOT_SUBMITTED"
    assert set(readiness["counts"].values()) == {0}
