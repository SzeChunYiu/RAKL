#!/usr/bin/env python3
"""Freeze executable ORACLE_CAPABILITY_GATE_V2_0_EXEC packet (#379).

Builds PROTOCOL_FREEZE_PACKET + RECEIPT from sealed artifacts under
``research/paper2_oracle_capability_gate_v2_exec/``.

Chronology: frozen before any evaluated v2 ORACLE outcome.
Does not soften EXPERIENCE_V1_EXACT_STRUCTURED_MATCH.
Does not authorize Phase-0 / confirmatory learning / 14B/32B.
"""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rakl.experience_benchmark import (  # noqa: E402
    ExperienceBenchmarkPacket,
    benchmark_protocol_subject_hash,
)
from rakl.matched_microtrial import MatchedModelConfig, TrialResourceCeiling  # noqa: E402
from rakl.v3_authority import canonical_sha256  # noqa: E402

PACKET_DIR = ROOT / "research" / "paper2_oracle_capability_gate_v2_exec"
BENCHMARK_ID = "paper2-oracle-capability-gate-v2-exec"
PROTOCOL_VERSION_ID = "ORACLE_CAPABILITY_GATE_V2_0_EXEC"
PARENT_PROTOCOL_VERSION_ID = "ORACLE_CAPABILITY_GATE_V2_0"
PARENT_PROTOCOL_SUBJECT_HASH = "7b186eae72ca69765c1702bc6280a9f5a1ca5c27527b88664dcfe53f644dae09"
PARENT_V1_3_3_SUBJECT_HASH = "dc7bff2e6fae3b54d0af87d116234081d4fd516645d735552fdc0d1b4f2141d6"
PENDING_LEARNED = "PENDING_AFTER_DEVELOPMENT_NOT_YET_EXECUTED"
DEFAULT_FROZEN_AT = "2026-08-11T23:10:00Z"
DEVELOPMENT_TASK_IDS = ("D1", "D2", "D3")
TRANSFER_TASK_IDS = ("T1", "T2", "T3", "T4", "T5")
FORBIDDEN_NAME_FRAGMENTS = (
    "runs.jsonl",
    "run_results",
    "evaluated",
    "model_output",
    "harvest-result",
    "NATIVE_JOB_",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _refuse_if_results_present(packet_dir: Path) -> None:
    offenders: list[str] = []
    for path in packet_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith("native_job_") for part in path.parts):
            continue
        name = path.name
        lower = name.lower()
        if any(fragment.lower() in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
            offenders.append(_display_path(path))
        elif lower.endswith(".jsonl") and "freeze" not in lower:
            offenders.append(_display_path(path))
    if offenders:
        raise SystemExit(
            "REFUSED: evaluated/result artifacts already present before protocol freeze:\n  "
            + "\n  ".join(sorted(set(offenders)))
        )


def build_protocol_packet(packet_dir: Path, frozen_at: str) -> tuple[dict, ExperienceBenchmarkPacket, dict]:
    protocol = packet_dir / "protocol"
    tasks_dir = packet_dir / "tasks"
    model_cfg = _load_json(protocol / "MODEL_CONFIG.json")
    ceiling_cfg = _load_json(protocol / "RESOURCE_CEILING.json")
    tool_policy = _load_json(protocol / "TOOL_POLICY.json")
    output_schema = _load_json(protocol / "OUTPUT_SCHEMA.json")
    evaluator = _load_json(protocol / "EVALUATOR_PROTOCOL.json")
    s0_path = protocol / "INITIAL_STATE_S0.json"
    system_prompt_path = protocol / "SYSTEM_PROMPT.txt"
    system_prompt = system_prompt_path.read_text(encoding="utf-8").rstrip("\n")
    if model_cfg["system_prompt"] != system_prompt:
        raise SystemExit("MODEL_CONFIG.system_prompt does not match SYSTEM_PROMPT.txt bytes")
    if evaluator.get("evaluator_protocol_id") != "EXPERIENCE_V1_EXACT_STRUCTURED_MATCH":
        raise SystemExit("evaluator protocol id must remain EXPERIENCE_V1_EXACT_STRUCTURED_MATCH")
    scoring = evaluator.get("scoring", {})
    if float(scoring.get("success_threshold", 0)) != 1.0:
        raise SystemExit("success_threshold must remain 1.0")
    if float(scoring.get("exact_verdict_match", 0)) != 0.5:
        raise SystemExit("exact_verdict_match must remain 0.5")
    if float(scoring.get("required_support_recall", 0)) != 0.25:
        raise SystemExit("required_support_recall must remain 0.25")
    if float(scoring.get("required_reject_recall", 0)) != 0.25:
        raise SystemExit("required_reject_recall must remain 0.25")

    task_artifact_ids: list[tuple[str, str]] = []
    task_bindings: dict[str, dict] = {}
    required_strata = {
        "T1": "REPEATED_FAMILY",
        "T2": "CROSS_DOMAIN_TRANSFER",
        "T3": "HOSTILE_NEAR_MISS",
        "T4": "CONTEXT_ALIGNMENT",
        "T5": "MISSING_EVIDENCE",
    }
    for task_id in DEVELOPMENT_TASK_IDS + TRANSFER_TASK_IDS:
        path = tasks_dir / f"{task_id}.json"
        payload = _load_json(path)
        if payload.get("task_id") != task_id:
            raise SystemExit(f"{path}: task_id mismatch")
        if payload.get("benchmark_id") != BENCHMARK_ID:
            raise SystemExit(f"{path}: benchmark_id mismatch")
        if task_id in required_strata and payload.get("stratum") != required_strata[task_id]:
            raise SystemExit(f"{path}: stratum must be {required_strata[task_id]}")
        digest = _sha256_file(path)
        artifact_id = f"task:{task_id}:{digest}"
        task_artifact_ids.append((task_id, artifact_id))
        task_bindings[task_id] = {
            "path": _display_path(path),
            "sha256": digest,
            "bytes": path.stat().st_size,
            "stratum": payload["stratum"],
            "phase": payload["phase"],
            "artifact_id": artifact_id,
        }

    initial_state_hash = _sha256_file(s0_path)
    evaluator_hash = _sha256_file(protocol / "EVALUATOR_PROTOCOL.json")
    tool_digest = _sha256_file(protocol / "TOOL_POLICY.json")
    schema_digest = _sha256_file(protocol / "OUTPUT_SCHEMA.json")

    model = MatchedModelConfig(
        model_id=model_cfg["model_id"],
        model_revision=model_cfg["model_revision"],
        temperature=float(model_cfg["temperature"]),
        max_output_tokens=int(model_cfg["max_output_tokens"]),
        seed=int(model_cfg["seed"]),
        system_prompt=system_prompt,
    )
    ceiling = TrialResourceCeiling(
        max_model_input_tokens=int(ceiling_cfg["max_model_input_tokens"]),
        max_model_output_tokens=int(ceiling_cfg["max_model_output_tokens"]),
        max_preprocessing_model_tokens=int(ceiling_cfg["max_preprocessing_model_tokens"]),
        max_preprocessing_tool_calls=int(ceiling_cfg["max_preprocessing_tool_calls"]),
        max_external_retrieval_calls=int(ceiling_cfg["max_external_retrieval_calls"]),
        max_wall_time_ms=int(ceiling_cfg["max_wall_time_ms"]),
    )
    if ceiling.max_model_output_tokens != model.max_output_tokens:
        raise SystemExit("model max_output_tokens must equal resource ceiling max_model_output_tokens")
    if model.model_id != "Qwen/Qwen2.5-7B-Instruct":
        raise SystemExit("first executable v2 ORACLE is bound to Qwen2.5-7B-Instruct")

    packet = ExperienceBenchmarkPacket(
        benchmark_id=BENCHMARK_ID,
        model=model,
        resource_ceiling=ceiling,
        tool_policy_id=tool_policy["tool_policy_id"],
        output_schema_id=output_schema["output_schema_id"],
        evaluator_protocol_hash=evaluator_hash,
        initial_state_hash=initial_state_hash,
        development_task_ids=DEVELOPMENT_TASK_IDS,
        transfer_task_ids=TRANSFER_TASK_IDS,
        learned_state_after_development_hash=PENDING_LEARNED,
        runs=(),
        frozen_before_runs=True,
        evaluator_artifact_id=f"evaluator:{evaluator_hash}",
        tool_policy_artifact_id=f"tool-policy:{tool_digest}",
        output_schema_artifact_id=f"output-schema:{schema_digest}",
        task_artifact_ids=tuple(task_artifact_ids),
        packet_frozen_at=frozen_at,
        freeze_attestation_id=None,
        match_attestation_id=None,
    )
    protocol_subject_hash = benchmark_protocol_subject_hash(packet)

    freeze_packet = {
        "schema_version": "rakl-experience-benchmark-protocol-freeze-v1",
        "benchmark_id": BENCHMARK_ID,
        "protocol_version_id": PROTOCOL_VERSION_ID,
        "parent_protocol_version_id": PARENT_PROTOCOL_VERSION_ID,
        "parent_protocol_subject_hash": PARENT_PROTOCOL_SUBJECT_HASH,
        "issue": 379,
        "section": "PHASE1_ORACLE_7B_V2_EXEC",
        "status": "PROTOCOL_FROZEN_AWAITING_EXECUTION",
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "frozen_before_any_new_oracle_outcome": True,
        "arms": [
            "ORACLE_PROCEDURE_UPPER_BOUND",
            "RESET",
            "FAILURE_MEMORY_ONLY",
            "VERIFIED_DEVELOPMENT_LESSONS",
            "FULL_RAKL_SELECTIVE",
        ],
        "phases": ["DEVELOPMENT_SEQUENCE", "FRESH_TRANSFER"],
        "learning_loop_mode": "root_cause_v1",
        "parent_negative_history": {
            "parent_protocol_packet": "paper2-oracle-capability-gate-v2",
            "parent_protocol_version_id": PARENT_PROTOCOL_VERSION_ID,
            "parent_protocol_subject_hash": PARENT_PROTOCOL_SUBJECT_HASH,
            "parent_v1_3_3_packet": "paper2-experience-benchmark-v1_3_3",
            "parent_v1_3_3_protocol_subject_hash": PARENT_V1_3_3_SUBJECT_HASH,
            "parent_job_id": "3476788",
            "parent_scientific_verdict": "MODEL_CAPABILITY_FLOOR_7B",
            "preserved_floor_jobs": [
                "3476730",
                "3476731",
                "3476742",
                "3476756",
                "3476778",
                "3476788",
            ],
            "reopen_issue_138": False,
            "reinterpret_as_lift": False,
            "not_scale_only_escape_from_v1_2": True,
            "explicitly_not_14B_32B_escalation": True,
            "successor_issue": 379,
        },
        "primary_execution": {
            "first_job_arm": "ORACLE_PROCEDURE_UPPER_BOUND",
            "first_job_scope": "FRESH_TRANSFER_ONLY",
            "oracle_pass_min_success_rate": 2.0 / 3.0,
            "oracle_pass_min_success_rate_fraction": "2/3",
            "transfer_task_count": len(TRANSFER_TASK_IDS),
            "model_scale": "Qwen2.5-7B-Instruct",
            "authorized_model_ceiling": "Qwen2.5-7B-Instruct",
            "forbid_14B_32B": True,
            "forbid_scale_only_difference_witness_on_v1_2": True,
            "parent_7B_oracle_floor_job": "3476788",
            "parent_7B_oracle_verdict": "MODEL_CAPABILITY_FLOOR_7B",
            "parent_3B_oracle_floor_job": "3476778",
            "parent_3B_oracle_verdict": "MODEL_CAPABILITY_FLOOR_3B",
            "parent_1_5B_oracle_floor_job": "3476756",
            "parent_1_5B_oracle_verdict": "MODEL_CAPABILITY_FLOOR_1_5B",
            "parent_1_5B_instrument_defect_job": "3476742",
            "parent_0_5B_oracle_floor_jobs": ["3476730", "3476731"],
            "parent_0_5B_oracle_verdict": "MODEL_CAPABILITY_FLOOR_0_5B",
            "preregistered_escalation": "task_gate_revisit_v2_exec_at_7B_ceiling",
            "oracle_job_authorized_by_this_packet": True,
            "phase0_architecture_authorized": False,
        },
        "execution_authority": {
            "oracle_job_authorized_by_this_packet": True,
            "authorized_first_oracle_scale": "Qwen2.5-7B-Instruct",
            "phase0_architecture_authorized": False,
            "confirmatory_alr_authorized": False,
            "confirmatory_a3a4_authorized": False,
            "four_arm_authorized": False,
            "pilot_diagnostic_job_authorized": False,
            "human_review_gate_required_before_submit": False,
            "reason": (
                "V2_0 required sealed transfer tasks + executable ORACLE freeze before any job. "
                "This packet supplies both; first authorized ORACLE is ORACLE_PROCEDURE_UPPER_BOUND "
                "at the V2 ceiling scale Qwen2.5-7B-Instruct (revisit after FLOOR_7B, not 14B/32B)."
            ),
        },
        "task_strata": {
            "capable_model_gate_set": list(TRANSFER_TASK_IDS),
            "required_transfer_strata": [
                {"task_id": "T1", "stratum": "REPEATED_FAMILY"},
                {"task_id": "T2", "stratum": "CROSS_DOMAIN_TRANSFER"},
                {"task_id": "T3", "stratum": "HOSTILE_NEAR_MISS"},
                {"task_id": "T4", "stratum": "CONTEXT_ALIGNMENT"},
                {"task_id": "T5", "stratum": "MISSING_EVIDENCE"},
            ],
            "hardness_axes_preserved_from_floor7b": [
                "CROSS_DOMAIN evidence-id binding under correct high-level misalignment verdict",
                "HOSTILE_NEAR_MISS QoI discrimination vs context-misalignment confusion",
                "REPEATED_FAMILY calibration-bound exact match",
            ],
            "sealed_task_bytes_status": "AUTHORED_AND_FROZEN",
        },
        "model": {
            "model_id": model.model_id,
            "model_revision": model.model_revision,
            "temperature": model.temperature,
            "max_output_tokens": model.max_output_tokens,
            "seed": model.seed,
            "system_prompt_hash": model.system_prompt_hash,
            "provider": model_cfg.get("provider"),
            "snapshot_path": model_cfg.get("snapshot_path"),
            "model_manifest_path": model_cfg.get("model_manifest_path"),
        },
        "resource_ceiling": {
            "max_model_input_tokens": ceiling.max_model_input_tokens,
            "max_model_output_tokens": ceiling.max_model_output_tokens,
            "max_preprocessing_model_tokens": ceiling.max_preprocessing_model_tokens,
            "max_preprocessing_tool_calls": ceiling.max_preprocessing_tool_calls,
            "max_external_retrieval_calls": ceiling.max_external_retrieval_calls,
            "max_wall_time_ms": ceiling.max_wall_time_ms,
        },
        "tool_policy_id": packet.tool_policy_id,
        "output_schema_id": packet.output_schema_id,
        "evaluator_protocol_hash": packet.evaluator_protocol_hash,
        "evaluator_protocol_id": evaluator["evaluator_protocol_id"],
        "initial_state_hash": packet.initial_state_hash,
        "development_task_ids": list(packet.development_task_ids),
        "transfer_task_ids": list(packet.transfer_task_ids),
        "learned_state_after_development_hash": PENDING_LEARNED,
        "learned_state_binding_rule": (
            "ORACLE_PROCEDURE_UPPER_BOUND Phase-1 jobs do not bind Sn from development; "
            "they inject the frozen family-general checklist only. Later learning arms "
            "remain unauthorized while CAPABLE_MODEL_AVAILABLE=NO_REFUTED."
        ),
        "runs": [],
        "frozen_before_runs": True,
        "packet_frozen_at": frozen_at,
        "evaluator_artifact_id": packet.evaluator_artifact_id,
        "tool_policy_artifact_id": packet.tool_policy_artifact_id,
        "output_schema_artifact_id": packet.output_schema_artifact_id,
        "task_artifact_ids": [[task_id, artifact_id] for task_id, artifact_id in packet.task_artifact_ids],
        "task_bindings": task_bindings,
        "protocol_subject_hash": protocol_subject_hash,
        "CAPABLE_MODEL_AVAILABLE": "NO_REFUTED",
        "capable_model_available": False,
        "learning_staircase_authorized": False,
        "promotional_lift_claim_allowed": False,
        "reopen_issue_138": False,
        "grants_scientific_authority": False,
        "v4_1_pendulum_compatibility": {
            "verdict": "CANNOT_CHECK_AS_EXPERIENCE_BENCHMARK",
            "score_reuse_allowed": False,
            "arm_reuse_allowed": False,
            "jobs_explicitly_not_experience_evidence": [3476520, 3476521, 3476524],
            "model_identity_reuse_allowed": True,
            "reason": (
                "V4.1 microtrials use RAKL_CONTEXT/DIRECT arms without "
                "RESET_BASELINE/LEARNING_ENABLED state chronology."
            ),
        },
        "authority_boundary": (
            "Executable ORACLE freeze for #379 under ORACLE_CAPABILITY_GATE_V2_0_EXEC. "
            "Authorizes only ORACLE_PROCEDURE_UPPER_BOUND @ Qwen2.5-7B-Instruct on the "
            "sealed T1–T5 transfer set. Does not authorize Phase-0, confirmatory ALR, "
            "A3↔A4, four-arm, or 14B/32B. Does not soften EXPERIENCE_V1_EXACT_STRUCTURED_MATCH. "
            "Preserves all prior floor jobs. CAPABLE_MODEL stays NO_REFUTED until a parse-valid "
            "receipt records exact success_rate >= 2/3."
        ),
    }

    receipt = {
        "schema_version": "paper2-oracle-capability-gate-executable-freeze-receipt-v1",
        "protocol_version_id": PROTOCOL_VERSION_ID,
        "benchmark_id": BENCHMARK_ID,
        "issue": 379,
        "section": "PHASE1_ORACLE_7B_V2_EXEC",
        "status": "PROTOCOL_FROZEN_AWAITING_EXECUTION",
        "created_at_utc": frozen_at,
        "protocol_subject_hash": protocol_subject_hash,
        "parent_protocol_subject_hash": PARENT_PROTOCOL_SUBJECT_HASH,
        "parent_v1_3_3_protocol_subject_hash": PARENT_V1_3_3_SUBJECT_HASH,
        "frozen_before_any_new_oracle_outcome": True,
        "oracle_job_authorized_by_this_packet": True,
        "authorized_first_oracle_scale": "Qwen2.5-7B-Instruct",
        "CAPABLE_MODEL_AVAILABLE": "NO_REFUTED",
        "transfer_task_ids": list(TRANSFER_TASK_IDS),
        "development_task_ids": list(DEVELOPMENT_TASK_IDS),
        "evaluator_protocol_hash": packet.evaluator_protocol_hash,
        "system_prompt_hash": model.system_prompt_hash,
        "runs_present": False,
        "evaluated_model_outputs_opened": False,
        "jobs_submitted": [],
        "next_compute_step": (
            "On LUNARC FS9 Paper-II checkout at exact origin/main containing this freeze: "
            "submit ORACLE_PROCEDURE_UPPER_BOUND @ Qwen2.5-7B-Instruct on FRESH_TRANSFER "
            "T1–T5 only (learning_loop_mode=root_cause_v1; staged assets paper2-model-qwen25-7b-v1). "
            "Do not submit learning/architecture staircase. Do not escalate to 14B/32B. "
            "Do not reopen #138. Preserve floor jobs 3476730/3476731/3476742/3476756/3476778/3476788."
        ),
        "forbidden": [
            "14B/32B ORACLE",
            "Phase-0 / RESET/FAILURE_MEMORY/VERIFIED/FULL_RAKL before CAPABLE_MODEL clearance",
            "softening success_threshold or dropping HOSTILE/CROSS_DOMAIN strata",
            "reopen #138 or reinterpret prior floors as lift",
            "reuse V4.1/V4.3 pendulum scores as ExperienceBenchmark evidence",
            "overwrite or rewrite prior floor receipts",
        ],
        "artifact_sha256": {
            "PROTOCOL_FREEZE_PACKET.json": None,
            "EVALUATOR_PROTOCOL.json": evaluator_hash,
            "TOOL_POLICY.json": tool_digest,
            "OUTPUT_SCHEMA.json": schema_digest,
            "INITIAL_STATE_S0.json": initial_state_hash,
            "MODEL_CONFIG.json": _sha256_file(protocol / "MODEL_CONFIG.json"),
            "RESOURCE_CEILING.json": _sha256_file(protocol / "RESOURCE_CEILING.json"),
            "SYSTEM_PROMPT.txt": _sha256_file(system_prompt_path),
            **{f"tasks/{task_id}.json": meta["sha256"] for task_id, meta in task_bindings.items()},
        },
        "freeze_packet_content_hash": canonical_sha256(freeze_packet),
        "claim_boundary": "Executable freeze receipt only. Not evaluated ORACLE outcomes. Not learning efficacy.",
        "grants_scientific_authority": False,
    }
    return freeze_packet, packet, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--frozen-at", default=DEFAULT_FROZEN_AT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    packet_dir = args.packet_dir if args.packet_dir.is_absolute() else ROOT / args.packet_dir
    _refuse_if_results_present(packet_dir)
    freeze_packet, _packet, receipt = build_protocol_packet(packet_dir, args.frozen_at)

    out_packet = packet_dir / "PROTOCOL_FREEZE_PACKET.json"
    out_receipt = packet_dir / "PROTOCOL_FREEZE_RECEIPT.json"
    if args.check_only:
        if not out_packet.exists() or not out_receipt.exists():
            raise SystemExit("check-only requires existing freeze packet and receipt")
        existing = _load_json(out_packet)
        if existing.get("protocol_subject_hash") != freeze_packet["protocol_subject_hash"]:
            raise SystemExit("protocol_subject_hash drift versus sealed artifacts")
        if existing.get("packet_frozen_at") != args.frozen_at:
            raise SystemExit("packet_frozen_at drift")
        print(
            json.dumps(
                {
                    "verdict": "PROTOCOL_FREEZE_CHECK_PASS",
                    "protocol_subject_hash": freeze_packet["protocol_subject_hash"],
                    "transfer_task_count": len(TRANSFER_TASK_IDS),
                },
                indent=2,
            )
        )
        return 0

    out_packet.write_text(json.dumps(freeze_packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["artifact_sha256"]["PROTOCOL_FREEZE_PACKET.json"] = _sha256_file(out_packet)
    out_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": "PROTOCOL_FROZEN_AWAITING_EXECUTION",
                "protocol_version_id": PROTOCOL_VERSION_ID,
                "protocol_subject_hash": freeze_packet["protocol_subject_hash"],
                "transfer_task_ids": list(TRANSFER_TASK_IDS),
                "oracle_job_authorized_by_this_packet": True,
                "authorized_first_oracle_scale": "Qwen2.5-7B-Instruct",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
