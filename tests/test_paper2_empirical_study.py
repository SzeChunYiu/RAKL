from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rakl.paper2_empirical_study import (
    PreflightVerdict,
    audit_study_packet,
    write_preflight_receipt,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _complete_packet(tmp_path: Path) -> dict[str, object]:
    artifacts = {}
    for name in (
        "tasks.json",
        "direct.txt",
        "rakl.txt",
        "public.json",
        "curated.json",
        "sealed.json",
        "evaluator.py",
        "prices.json",
    ):
        path = tmp_path / name
        path.write_text(f"artifact:{name}\n", encoding="utf-8")
        artifacts[name] = {"path": str(path), "sha256": _sha256(path)}

    return {
        "schema_version": "paper2-matched-study-freeze-v1",
        "protocol_id": "paper2-test-freeze-v1",
        "subject_sha": "a" * 40,
        "freeze_created_at_utc": "2026-08-10T20:00:00Z",
        "evaluated_results_opened_before_freeze": False,
        "object": "LLM-mediated scientific workflow",
        "qoi": "valid-scientific-success versus cost frontier",
        "context": "sealed paired task worlds",
        "task_set": {
            "confirmatory": True,
            **artifacts["tasks.json"],
        },
        "model": {
            "provider": "test-provider",
            "model_id": "test-model-v1",
            "model_revision": "immutable-test-revision",
            "architecture_neutral_interface": True,
            "adapter_command": "python",
            "adapter_version": "test-adapter-v1",
            "credential_mode": "none",
        },
        "architecture_arms": [
            {"id": "DIRECT_STRONG", **artifacts["direct.txt"]},
            {"id": "RAKL_FIXED", **artifacts["rakl.txt"]},
        ],
        "evidence_access_arms": [
            {"id": "public", **artifacts["public.json"]},
            {"id": "curated", **artifacts["curated.json"]},
            {"id": "complete_sealed", **artifacts["sealed.json"]},
        ],
        "resources": {
            "seed_schedule": [11, 23],
            "active_context_token_budgets": [512, 1024],
            "max_billable_tokens_per_run": 4096,
            "max_tool_calls_per_run": 8,
            "max_wall_time_seconds_per_run": 120,
        },
        "evaluator": {
            "id": "protected-evaluator-v1",
            "final_task_correctness_executable": True,
            "arm_identity_blinded": True,
            **artifacts["evaluator.py"],
        },
        "price_sheet": {"id": "test-price-v1", **artifacts["prices.json"]},
    }


def test_complete_bound_packet_passes_preflight(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)

    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")

    assert report.verdict is PreflightVerdict.PASS
    assert report.blockers == ()
    assert report.invalid_bindings == ()


def test_missing_empirical_assets_fail_closed_without_result_records(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)
    pilot_path = tmp_path / "pilot-only.json"
    pilot_path.write_text('{"status":"conformance-only"}\n', encoding="utf-8")
    packet["task_set"] = {
        "confirmatory": False,
        "path": str(pilot_path),
        "sha256": _sha256(pilot_path),
    }
    packet["architecture_arms"] = []
    packet["price_sheet"] = None

    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")

    assert report.verdict is PreflightVerdict.CANNOT_CHECK
    assert "confirmatory_task_payload_missing" in report.blockers
    assert "architecture_prompt_assets_missing" in report.blockers
    assert "provider_price_sheet_missing" in report.blockers
    assert report.evaluated_result_record_count == 0


def test_frozen_artifact_hash_mismatch_rejects_execution(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)
    task_path = Path(packet["task_set"]["path"])
    task_path.write_text("mutated after freeze\n", encoding="utf-8")

    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")

    assert report.verdict is PreflightVerdict.REJECT
    assert any(item.startswith("sha256_mismatch:task_set:") for item in report.invalid_bindings)


def test_receipt_writer_refuses_to_label_preflight_as_empirical_result(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)
    packet["price_sheet"] = None
    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")
    output = tmp_path / "preflight.json"

    write_preflight_receipt(
        report,
        packet=packet,
        output_path=output,
        created_at_utc="2026-08-10T20:15:00Z",
    )

    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["receipt_type"] == "execution_preflight_not_empirical_result"
    assert receipt["verdict"] == "CANNOT_CHECK"
    assert receipt["evaluated_result_record_count"] == 0
    assert receipt["empirical_claim_permitted"] is False


def test_result_chronology_violation_rejects_even_if_assets_exist(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)
    packet["evaluated_results_opened_before_freeze"] = True

    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")

    assert report.verdict is PreflightVerdict.REJECT
    assert "freeze_chronology_violated" in report.invalid_bindings


def test_agent_harness_or_unversioned_model_cannot_certify_matched_architecture(tmp_path: Path) -> None:
    packet = _complete_packet(tmp_path)
    packet["model"].pop("model_revision")
    packet["model"]["architecture_neutral_interface"] = False

    report = audit_study_packet(packet, command_finder=lambda _: "/usr/bin/python")

    assert report.verdict is PreflightVerdict.CANNOT_CHECK
    assert "model_revision_missing" in report.blockers
    assert "base_model_interface_not_architecture_neutral" in report.blockers
