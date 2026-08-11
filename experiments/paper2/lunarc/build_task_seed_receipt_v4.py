#!/usr/bin/env python3
"""Build the narrow task/seed index for the Paper-2 V4 bridge microtrial.

This is post-run bookkeeping.  It does not aggregate across tasks, seeds,
architectures, evidence-access levels, or model families.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def build(
    packet_path: Path,
    result_path: Path,
    result_schema_path: Path,
    task_seed_schema_path: Path,
    pre_attestation_path: Path,
    post_attestation_path: Path,
    attestation_schema_path: Path,
    output_path: Path,
) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result_schema = json.loads(result_schema_path.read_text(encoding="utf-8"))
    validator_kwargs = {"format_checker": jsonschema.FormatChecker()}
    jsonschema.Draft202012Validator(result_schema, **validator_kwargs).validate(result)
    attestation_schema = json.loads(attestation_schema_path.read_text(encoding="utf-8"))
    pre_attestation = json.loads(pre_attestation_path.read_text(encoding="utf-8"))
    post_attestation = json.loads(post_attestation_path.read_text(encoding="utf-8"))
    for attestation in (pre_attestation, post_attestation):
        jsonschema.Draft202012Validator(attestation_schema, **validator_kwargs).validate(attestation)

    task_id = packet.get("registered_task_id")
    seed_schedule = packet.get("seed_schedule")
    if task_id != "PENDULUM_SEALED_KNOWN_ANSWER_001" or seed_schedule != [17]:
        raise RuntimeError("V4 task/seed freeze mismatch")
    if result.get("seed") != 17 or result.get("experiment_id") != packet.get("protocol_id"):
        raise RuntimeError("result does not match the V4 task/seed protocol")
    if pre_attestation["phase"] != "PRE_INFERENCE" or post_attestation["phase"] != "POST_INFERENCE":
        raise RuntimeError("snapshot attestation phase mismatch")
    if pre_attestation["snapshot_canonical_sha256"] != post_attestation["snapshot_canonical_sha256"]:
        raise RuntimeError("snapshot changed across inference")
    if post_attestation["result_receipt_sha256"] != _sha256(result_path):
        raise RuntimeError("post-inference attestation does not bind the result")
    if pre_attestation["packet_parent_sha"] != packet["subject_sha"]:
        raise RuntimeError("pre-attestation packet parent mismatch")
    if post_attestation["packet_parent_sha"] != packet["subject_sha"]:
        raise RuntimeError("post-attestation packet parent mismatch")
    if pre_attestation["execution_checkout"] != post_attestation["execution_checkout"]:
        raise RuntimeError("execution checkout changed across inference")
    if result.get("execution_checkout") != {
        "repo_path": result["execution_checkout"]["repo_path"],
        "head_sha": pre_attestation["execution_checkout"]["head_sha"],
        "tree_sha": pre_attestation["execution_checkout"]["tree_sha"],
        "clean": True,
        "subject_ancestor": True,
    }:
        raise RuntimeError("result execution checkout does not match snapshot attestations")
    records = result.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise RuntimeError("V4 requires exactly two arm records")
    if {record.get("condition") for record in records} != {"DIRECT_CORPUS", "RAKL_CONTEXT"}:
        raise RuntimeError("V4 arm set is incomplete or duplicated")

    indexed_records = []
    for record in sorted(records, key=lambda row: str(row["condition"])):
        indexed_records.append(
            {
                "blind_id": record["blind_id"],
                "condition": record["condition"],
                "parse_valid": record["score"]["parse_valid"],
                "raw_output_canonical_sha256": hashlib.sha256(
                    json.dumps(
                        record["raw_output"],
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                ).hexdigest(),
                "resource_receipt": record["resource_receipt"],
                "score": record["score"],
            }
        )

    receipt = {
        "schema_version": "paper2-pendulum-task-seed-receipt-v4",
        "receipt_type": "nonconfirmatory_task_seed_execution_index",
        "experiment_id": result["experiment_id"],
        "packet_parent_sha": result["subject_sha"],
        "execution_checkout": result["execution_checkout"],
        "created_at_utc": result["created_at_utc"],
        "task_id": task_id,
        "seed": 17,
        "evidence_access_level": packet["evidence_access_level"],
        "architecture_scope": packet["architecture_scope"],
        "result_receipt_path": str(result_path),
        "result_receipt_sha256": _sha256(result_path),
        "snapshot_attestations": {
            "pre_path": str(pre_attestation_path),
            "pre_sha256": _sha256(pre_attestation_path),
            "post_path": str(post_attestation_path),
            "post_sha256": _sha256(post_attestation_path),
            "snapshot_canonical_sha256": pre_attestation["snapshot_canonical_sha256"],
        },
        "evaluated_task_seed_unit_count": 1,
        "arm_record_count": 2,
        "records": indexed_records,
        "claim_boundary": (
            "One non-confirmatory known-answer task/seed unit only. This index cannot support "
            "the Paper-2 matched architecture-by-evidence-access estimand or a general RAKL claim."
        ),
    }
    task_seed_schema = json.loads(task_seed_schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(task_seed_schema, **validator_kwargs).validate(receipt)
    _atomic_json(output_path, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    parser.add_argument("--task-seed-schema", type=Path, required=True)
    parser.add_argument("--pre-attestation", type=Path, required=True)
    parser.add_argument("--post-attestation", type=Path, required=True)
    parser.add_argument("--attestation-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(
        args.packet,
        args.result,
        args.result_schema,
        args.task_seed_schema,
        args.pre_attestation,
        args.post_attestation,
        args.attestation_schema,
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
