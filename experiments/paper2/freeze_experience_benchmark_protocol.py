#!/usr/bin/env python3
"""Freeze the Paper-II ExperienceBenchmark protocol packet (issue #138 §B1).

Builds a pre-execution protocol freeze from sealed artifacts under
``research/paper2_experience_benchmark_v1/``.  Emits:

- ``PROTOCOL_FREEZE_PACKET.json`` — protocol fields only (no runs / no Sn)
- ``PROTOCOL_FREEZE_RECEIPT.json`` — hash-bound freeze chronology

This script refuses if evaluated run/result artifacts are already present in the
packet directory.  It does **not** execute models and does **not** treat
pendulum V4.1 harvests as experience-benchmark evidence.
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
from rakl.v3_authority import canonical_json_bytes, canonical_sha256  # noqa: E402

PACKET_DIR = ROOT / "research" / "paper2_experience_benchmark_v1"
FORBIDDEN_NAME_FRAGMENTS = (
    "runs.jsonl",
    "run_results",
    "evaluated",
    "model_output",
    "harvest-result",
    "NATIVE_JOB_",
)
PENDING_LEARNED = "PENDING_AFTER_DEVELOPMENT_NOT_YET_EXECUTED"


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
        # Harvested native job trees are post-execution receipts, not protocol inputs.
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


def build_protocol_packet(packet_dir: Path, frozen_at: str, *, benchmark_id: str) -> tuple[dict, ExperienceBenchmarkPacket, dict]:
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

    development_task_ids = ("D1", "D2", "D3")
    transfer_task_ids = ("T1", "T2", "T3")
    task_artifact_ids: list[tuple[str, str]] = []
    task_bindings: dict[str, dict] = {}
    for task_id in development_task_ids + transfer_task_ids:
        path = tasks_dir / f"{task_id}.json"
        payload = _load_json(path)
        if payload.get("task_id") != task_id:
            raise SystemExit(f"{path}: task_id mismatch")
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

    if set(development_task_ids) & set(transfer_task_ids):
        raise SystemExit("development and transfer task ids must be disjoint")

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

    packet = ExperienceBenchmarkPacket(
        benchmark_id=benchmark_id,
        model=model,
        resource_ceiling=ceiling,
        tool_policy_id=tool_policy["tool_policy_id"],
        output_schema_id=output_schema["output_schema_id"],
        evaluator_protocol_hash=evaluator_hash,
        initial_state_hash=initial_state_hash,
        development_task_ids=development_task_ids,
        transfer_task_ids=transfer_task_ids,
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

    issue = 247 if benchmark_id.endswith("v1_3") else 138
    section = "PHASE0_1_ORACLE_FIRST" if benchmark_id.endswith("v1_3") else "B1"
    arms = (
        [
            "ORACLE_PROCEDURE_UPPER_BOUND",
            "RESET",
            "FAILURE_MEMORY_ONLY",
            "VERIFIED_DEVELOPMENT_LESSONS",
            "FULL_RAKL_SELECTIVE",
        ]
        if benchmark_id.endswith("v1_3")
        else ["RESET_BASELINE", "LEARNING_ENABLED"]
    )
    learning_loop_mode = "root_cause_v1" if benchmark_id.endswith("v1_3") else "legacy_v1_2"
    primary_execution = (
        {
            "first_job_arm": "ORACLE_PROCEDURE_UPPER_BOUND",
            "first_job_scope": "FRESH_TRANSFER_ONLY",
            "oracle_pass_min_success_rate": 2.0 / 3.0,
            "model_scale": "Qwen2.5-0.5B-Instruct",
            "forbid_1_5B_until_oracle_gate": True,
            "forbid_scale_only_difference_witness_on_v1_2": True,
        }
        if benchmark_id.endswith("v1_3")
        else None
    )

    freeze_packet = {
        "schema_version": "rakl-experience-benchmark-protocol-freeze-v1",
        "benchmark_id": packet.benchmark_id,
        "issue": issue,
        "section": section,
        "status": "PROTOCOL_FROZEN_AWAITING_EXECUTION",
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "arms": arms,
        "phases": ["DEVELOPMENT_SEQUENCE", "FRESH_TRANSFER"],
        "learning_loop_mode": learning_loop_mode,
        "parent_negative_history": (
            {
                "parent_packet": "paper2-experience-benchmark-v1_2",
                "parent_job_id": "3476548",
                "parent_protocol_subject_hash": "c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352",
                "reopen_issue_138": False,
                "reinterpret_as_lift": False,
            }
            if benchmark_id.endswith("v1_3")
            else None
        ),
        "primary_execution": primary_execution,
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
            "bind exact Sn only after LEARNING_ENABLED development completes; every "
            "fresh-transfer LEARNING run must start from that frozen Sn. RESET transfer "
            "continues from S0."
            if benchmark_id.endswith("v1_3")
            else (
                "Bind exact Sn hash only after LEARNING_ENABLED development completes; "
                "every fresh-transfer LEARNING run must start from that frozen Sn. "
                "RESET_BASELINE transfer continues from S0."
            )
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
            "Protocol freeze only. No RESET vs LEARNING delta, no Paper-II "
            "empirical claim, and no manuscript result ingest is authorized by this file. "
            "ORACLE Phase-1 success/failure classifies MODEL_CAPABILITY_FLOOR or "
            "INSTRUMENT_DEFECT only after parse-validity guard; it does not mint "
            "experience-learning efficacy."
            if benchmark_id.endswith("v1_3")
            else (
                "Protocol freeze only. No RESET vs LEARNING delta, no Paper-II "
                "empirical claim, and no manuscript result ingest is authorized by this file."
            )
        ),
    }
    # Drop null parent block for legacy packets to preserve exact freeze shape.
    if freeze_packet["parent_negative_history"] is None:
        del freeze_packet["parent_negative_history"]
    if freeze_packet["primary_execution"] is None:
        del freeze_packet["primary_execution"]
    if not benchmark_id.endswith("v1_3"):
        # Preserve historical freeze field set for v1/v1.1 check-only.
        del freeze_packet["learning_loop_mode"]

    receipt = {
        "schema_version": "rakl-experience-benchmark-protocol-freeze-receipt-v1",
        "benchmark_id": packet.benchmark_id,
        "issue": issue,
        "section": section,
        "verdict": "PROTOCOL_FREEZE_PASS",
        "packet_frozen_at": frozen_at,
        "protocol_subject_hash": protocol_subject_hash,
        "initial_state_hash": packet.initial_state_hash,
        "evaluator_protocol_hash": packet.evaluator_protocol_hash,
        "system_prompt_hash": model.system_prompt_hash,
        "development_task_ids": list(packet.development_task_ids),
        "transfer_task_ids": list(packet.transfer_task_ids),
        "runs_present": False,
        "learned_state_bound": False,
        "evaluated_model_outputs_opened": False,
        "empirical_section_b_status": "NOT_DONE",
        "next_compute_step": (
            "On LUNARC FS9 Paper-II checkout at exact origin/main: submit "
            "ORACLE_PROCEDURE_UPPER_BOUND @ Qwen2.5-0.5B on FRESH_TRANSFER only "
            "(learning_loop_mode=root_cause_v1). Do not submit staircase/1.5B. "
            "Do not reopen #138. Apply parse-validity guard before "
            "MODEL_CAPABILITY_FLOOR. Later Phase-0 arms require separate jobs "
            "under this same frozen packet."
            if benchmark_id.endswith("v1_3")
            else (
                "On LUNARC FS9 Paper-II checkout at exact origin/main: materialize S0, "
                "execute RESET_BASELINE and LEARNING_ENABLED development (D1→D3) under the "
                "frozen ceiling, freeze Sn, then run fresh transfer (T1–T3) with every "
                "LEARNING transfer starting independently from Sn; harvest runs.jsonl; "
                "validate via validate_experience_benchmark; only then analyze/plot."
            )
        ),
        "forbidden": [
            "reuse V4.1 pendulum scores/jobs 3476520/3476521/3476524 as §B evidence",
            "claim §B empirical completion from this freeze alone",
            "mutate evaluator/tasks after opening evaluated outputs under this packet id",
            *(
                [
                    "scale-only DifferenceWitness reusing broken v1.2 learning loop",
                    "ExperienceBenchmark@1.5B before ORACLE 0.5B gate",
                    "reopen #138 or reinterpret job 3476548 as lift",
                ]
                if benchmark_id.endswith("v1_3")
                else []
            ),
        ],
        "artifact_sha256": {
            "PROTOCOL_FREEZE_PACKET.json": None,  # filled after write
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
    }
    return freeze_packet, packet, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=PACKET_DIR,
        help="Experience-benchmark packet directory",
    )
    parser.add_argument(
        "--frozen-at",
        default=None,
        help="Timezone-aware freeze timestamp (UTC Z)",
    )
    parser.add_argument(
        "--benchmark-id",
        default=None,
        help="Benchmark id (default derived from packet directory)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate and print hashes without rewriting outputs",
    )
    args = parser.parse_args()
    packet_dir = args.packet_dir if args.packet_dir.is_absolute() else ROOT / args.packet_dir
    _refuse_if_results_present(packet_dir)
    if args.benchmark_id:
        benchmark_id = args.benchmark_id
    elif packet_dir.name.endswith("v1_3"):
        benchmark_id = "paper2-experience-benchmark-v1_3"
    elif packet_dir.name.endswith("v1_2"):
        benchmark_id = "paper2-experience-benchmark-v1_2"
    elif packet_dir.name.endswith("v1_1"):
        benchmark_id = "paper2-experience-benchmark-v1_1"
    else:
        benchmark_id = "paper2-experience-benchmark-v1"
    if args.frozen_at:
        frozen_at = args.frozen_at
    elif benchmark_id.endswith("v1_3"):
        frozen_at = "2026-08-11T21:10:00Z"
    elif benchmark_id.endswith("v1_1"):
        frozen_at = "2026-08-11T19:05:00Z"
    else:
        frozen_at = "2026-08-11T18:21:15Z"
    freeze_packet, _packet, receipt = build_protocol_packet(
        packet_dir, frozen_at, benchmark_id=benchmark_id
    )

    out_packet = packet_dir / "PROTOCOL_FREEZE_PACKET.json"
    out_receipt = packet_dir / "PROTOCOL_FREEZE_RECEIPT.json"
    if args.check_only:
        if not out_packet.exists() or not out_receipt.exists():
            raise SystemExit("check-only requires existing freeze packet and receipt")
        existing = _load_json(out_packet)
        if existing.get("protocol_subject_hash") != freeze_packet["protocol_subject_hash"]:
            raise SystemExit("protocol_subject_hash drift versus sealed artifacts")
        if existing.get("packet_frozen_at") != frozen_at:
            raise SystemExit("packet_frozen_at drift")
        print(json.dumps({"verdict": "PROTOCOL_FREEZE_CHECK_PASS", "protocol_subject_hash": freeze_packet["protocol_subject_hash"]}, indent=2))
        return 0

    packet_bytes = canonical_json_bytes(freeze_packet) + b"\n"
    receipt["artifact_sha256"]["PROTOCOL_FREEZE_PACKET.json"] = sha256(packet_bytes).hexdigest()
    receipt_bytes = canonical_json_bytes(receipt) + b"\n"

    out_packet.write_bytes(packet_bytes)
    out_receipt.write_bytes(receipt_bytes)

    # Refresh manifest without null entries.
    manifest = {
        "schema_version": "rakl-experience-benchmark-artifact-manifest-v1",
        "benchmark_id": freeze_packet["benchmark_id"],
        "issue": 138,
        "section": "B1",
        "arms": freeze_packet["arms"],
        "phases": freeze_packet["phases"],
        "development_task_ids": freeze_packet["development_task_ids"],
        "transfer_task_ids": freeze_packet["transfer_task_ids"],
        "frozen_at_utc": frozen_at,
        "evaluated_model_outputs_present": False,
        "learned_state_after_development_hash": PENDING_LEARNED,
        "protocol_subject_hash": freeze_packet["protocol_subject_hash"],
        "protocol_artifacts": {
            name: {
                "path": f"{packet_dir.relative_to(ROOT).as_posix()}/protocol/{name}",
                "sha256": receipt["artifact_sha256"][name],
                "bytes": (packet_dir / "protocol" / name).stat().st_size,
            }
            for name in (
                "EVALUATOR_PROTOCOL.json",
                "TOOL_POLICY.json",
                "OUTPUT_SCHEMA.json",
                "INITIAL_STATE_S0.json",
                "MODEL_CONFIG.json",
                "RESOURCE_CEILING.json",
                "SYSTEM_PROMPT.txt",
            )
        },
        "task_artifacts": freeze_packet["task_bindings"],
        "v4_1_pendulum_reuse": freeze_packet["v4_1_pendulum_compatibility"],
    }
    (packet_dir / "ARTIFACT_MANIFEST.json").write_bytes(canonical_json_bytes(manifest) + b"\n")

    print(
        json.dumps(
            {
                "verdict": "PROTOCOL_FREEZE_PASS",
                "protocol_subject_hash": freeze_packet["protocol_subject_hash"],
                "packet": str(out_packet.relative_to(ROOT)),
                "receipt": str(out_receipt.relative_to(ROOT)),
                "empirical_section_b_status": "NOT_DONE",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
