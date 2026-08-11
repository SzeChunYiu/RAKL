#!/usr/bin/env python3
"""Build the V4.3.1 task/seed receipt without reinterpreting any V4 output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema


POLICY_ID = "PENDULUM_EXACT_JSON_OR_FENCE_PLUS_REGISTERED_ENVELOPE_UNWRAP_V4_3_1"
PROTOCOL_ID = "PAPER2_PENDULUM_SEALED_KNOWN_ANSWER_V4_3_1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def build(args: argparse.Namespace) -> None:
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    run_manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    checker = jsonschema.FormatChecker()
    result_schema = json.loads(args.result_schema.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(result_schema, format_checker=checker).validate(result)

    attestation_schema = json.loads(args.attestation_schema.read_text(encoding="utf-8"))
    pre = json.loads(args.pre_attestation.read_text(encoding="utf-8"))
    post = json.loads(args.post_attestation.read_text(encoding="utf-8"))
    for value in (pre, post):
        jsonschema.Draft202012Validator(attestation_schema, format_checker=checker).validate(value)

    if packet.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("V4.3.1 protocol identity mismatch")
    if packet.get("chronology_class") != "ADAPTIVE_FLAT_SCHEMA_SHAPE_REPLAY_FRESH_ONLY_TO_V4_3_1_OUTPUTS":
        raise RuntimeError("V4.3.1 adaptive chronology class mismatch")
    if packet.get("parent_v4_3_results_opened_before_v4_3_1_freeze") is not True:
        raise RuntimeError("V4.3.1 parent-result access disclosure missing")
    if packet.get("v4_3_direct_parse_residual_known_before_freeze") is not True:
        raise RuntimeError("V4.3.1 parent-result access disclosure missing")
    if packet.get("evaluated_results_opened_before_freeze_scope") != "V4_3_1_OUTPUTS_ONLY_PARENT_V4_3_KNOWN":
        raise RuntimeError("V4.3.1 result-access scope mismatch")
    if packet.get("evaluated_task_seed_unit_count_before_freeze_scope") != "V4_3_1_OUTPUTS_ONLY_PARENT_V4_3_KNOWN":
        raise RuntimeError("V4.3.1 evaluated-unit scope mismatch")
    if packet.get("output_normalization_policy_id") != POLICY_ID:
        raise RuntimeError("V4.3.1 normalization policy identity mismatch")
    if packet.get("v4_3_1_outputs_opened_before_freeze") is not False:
        raise RuntimeError("V4.3.1 freeze chronology mismatch")
    if packet.get("threshold_or_score_change_permitted") is not False:
        raise RuntimeError("V4.3.1 exact-gate change prohibition missing")
    if packet.get("registered_task_id") != "PENDULUM_SEALED_KNOWN_ANSWER_001":
        raise RuntimeError("V4.3.1 task identity mismatch")
    if packet.get("seed_schedule") != [17]:
        raise RuntimeError("V4.3.1 seed schedule mismatch")

    packet_sha = _sha256(args.packet)
    policy_binding = packet.get("bindings", {}).get("output_normalization_contract", {})
    normalizer_binding = packet.get("bindings", {}).get("output_normalizer", {})
    if result.get("experiment_id") != PROTOCOL_ID or result.get("subject_sha") != packet.get("subject_sha"):
        raise RuntimeError("result does not match the V4.3.1 packet")
    if result.get("packet_sha256") != packet_sha:
        raise RuntimeError("result does not bind the exact V4.3.1 packet bytes")
    if result.get("seed") != 17:
        raise RuntimeError("result seed mismatch")
    if run_manifest.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("run manifest protocol mismatch")
    if run_manifest.get("packet_file_sha256") != packet_sha:
        raise RuntimeError("run manifest packet mismatch")
    if run_manifest.get("packet_canonical_sha256") != _canonical_sha256(packet):
        raise RuntimeError("run manifest canonical packet mismatch")
    if _sha256(args.run_manifest) != result.get("run_manifest_sha256"):
        raise RuntimeError("result run-manifest hash mismatch")
    bound = run_manifest.get("bound_artifact_sha256", {})
    if bound.get("output_normalization_contract") != policy_binding.get("sha256"):
        raise RuntimeError("run manifest normalization-contract binding mismatch")
    if bound.get("output_normalizer") != normalizer_binding.get("sha256"):
        raise RuntimeError("run manifest normalizer binding mismatch")

    if pre.get("phase") != "PRE_INFERENCE" or post.get("phase") != "POST_INFERENCE":
        raise RuntimeError("snapshot attestation phase mismatch")
    if pre.get("snapshot_canonical_sha256") != post.get("snapshot_canonical_sha256"):
        raise RuntimeError("snapshot changed across V4.3.1 inference")
    if pre.get("execution_checkout") != post.get("execution_checkout"):
        raise RuntimeError("execution checkout changed across V4.3.1 inference")
    if post.get("result_receipt_sha256") != _sha256(args.result):
        raise RuntimeError("post-inference attestation does not bind the V4.3.1 result")
    if pre.get("packet_parent_sha") != packet.get("subject_sha"):
        raise RuntimeError("pre-attestation packet parent mismatch")
    if post.get("packet_parent_sha") != packet.get("subject_sha"):
        raise RuntimeError("post-attestation packet parent mismatch")
    expected_checkout = {
        "repo_path": result["execution_checkout"]["repo_path"],
        "head_sha": pre["execution_checkout"]["head_sha"],
        "tree_sha": pre["execution_checkout"]["tree_sha"],
        "clean": True,
        "subject_ancestor": True,
    }
    if result.get("execution_checkout") != expected_checkout:
        raise RuntimeError("result checkout does not match V4.3.1 attestations")

    records = result.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise RuntimeError("V4.3.1 requires exactly two arm records")
    if {row.get("condition") for row in records} != {"DIRECT_CORPUS", "RAKL_CONTEXT"}:
        raise RuntimeError("V4.3.1 arm set is incomplete or duplicated")

    indexed: list[dict[str, object]] = []
    for row in sorted(records, key=lambda item: str(item["condition"])):
        score = row.get("score")
        if not isinstance(score, dict) or not isinstance(score.get("parse_valid"), bool):
            raise RuntimeError("V4.3.1 score state missing")
        indexed.append(
            {
                "blind_id": row["blind_id"],
                "condition": row["condition"],
                "parse_valid": score["parse_valid"],
                "raw_output_canonical_sha256": _canonical_sha256(row["raw_output"]),
                "resource_receipt": row["resource_receipt"],
                "score": score,
            }
        )
    parse_valid_count = sum(1 for row in indexed if row["parse_valid"] is True)
    scorable_count = sum(1 for row in indexed if isinstance(row["score"].get("score"), dict))
    if parse_valid_count != scorable_count:
        raise RuntimeError("V4.3.1 parse-valid and scorable counts diverge")

    receipt = {
        "schema_version": "paper2-pendulum-task-seed-receipt-v4.3.1",
        "receipt_type": "nonconfirmatory_v4_3_1_task_seed_execution_index",
        "experiment_id": PROTOCOL_ID,
        "packet_parent_sha": packet["subject_sha"],
        "execution_packet_sha256": packet_sha,
        "execution_checkout": result["execution_checkout"],
        "created_at_utc": result["created_at_utc"],
        "task_id": "PENDULUM_SEALED_KNOWN_ANSWER_001",
        "seed": 17,
        "evidence_access_level": "COMPLETE_SEALED",
        "architecture_scope": ["DIRECT_CORPUS", "RAKL_CONTEXT"],
        "output_normalization": {
            "policy_id": POLICY_ID,
            "contract_path": policy_binding["path"],
            "contract_sha256": policy_binding["sha256"],
            "normalizer_path": normalizer_binding["path"],
            "normalizer_sha256": normalizer_binding["sha256"],
            "v4_reinterpretation_permitted": False,
        },
        "run_manifest_path": str(args.run_manifest),
        "run_manifest_sha256": _sha256(args.run_manifest),
        "result_receipt_path": str(args.result),
        "result_receipt_sha256": _sha256(args.result),
        "snapshot_attestations": {
            "pre_path": str(args.pre_attestation),
            "pre_sha256": _sha256(args.pre_attestation),
            "post_path": str(args.post_attestation),
            "post_sha256": _sha256(args.post_attestation),
            "snapshot_canonical_sha256": pre["snapshot_canonical_sha256"],
        },
        "evaluated_task_seed_unit_count": 1,
        "arm_record_count": 2,
        "parse_valid_arm_count": parse_valid_count,
        "scorable_arm_count": scorable_count,
        "records": indexed,
        "claim_boundary": (
            "One fresh non-confirmatory V4.3.1 task/seed unit only. This receipt does not "
            "reinterpret V4 and cannot support an arm win or the matched Paper-2 estimand."
        ),
    }
    schema = json.loads(args.task_seed_schema.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=checker).validate(receipt)
    _atomic_json(args.output, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--result-schema", type=Path, required=True)
    parser.add_argument("--task-seed-schema", type=Path, required=True)
    parser.add_argument("--pre-attestation", type=Path, required=True)
    parser.add_argument("--post-attestation", type=Path, required=True)
    parser.add_argument("--attestation-schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
