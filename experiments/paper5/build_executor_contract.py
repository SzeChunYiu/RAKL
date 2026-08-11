#!/usr/bin/env python3
"""Assemble and freeze the Paper 5 executor contract.

``run_attribution_schedule.py`` refuses to execute without a contract that pins
the task packet, the schedule, the provider-specific adapter bytes, one
evaluation-state identity per arm, the shared resource ceiling and the
model/evaluator/tool/source identities. No builder existed, so the contract had
to be hand-written with hand-computed hashes.

This builder computes only what is mechanically derivable from files that
already exist on disk: the SHA-256 of the task packet, the schedule and the
adapter. Everything that is a *freeze of external state* -- per-arm state
identities, evaluator protocol hash, model revision, tool policy, source cutoff,
sham policy -- must be supplied by the operator. The builder never invents,
defaults or back-fills those values, because doing so would manufacture the
appearance of a freeze that never happened.

It also refuses to overwrite an existing contract: re-freezing in place after
seeing outcomes is exactly the failure mode the preregistration forbids.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_SCHEMA_PATH = ROOT / "schemas" / "paper5-executor-contract-v1.schema.json"

ARMS = ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING")
RESOURCE_FIELDS = (
    "model_input_tokens",
    "model_output_tokens",
    "preprocessing_model_tokens",
    "tool_calls",
    "retrieval_calls",
    "wall_time_ms",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    return value


def parse_pairs(values: list[str], label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"{label} entries must be KEY=VALUE, got: {item}")
        key, _, value = item.partition("=")
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise SystemExit(f"{label} entries must have a non-empty key and value, got: {item}")
        if key in out:
            raise SystemExit(f"duplicate {label} entry: {key}")
        out[key] = value
    return out


def build_contract(args: argparse.Namespace) -> dict[str, Any]:
    tasks = load_json(args.tasks)
    schedule = load_json(args.schedule)
    adapter = Path(args.adapter).expanduser().resolve()
    if not adapter.is_file():
        raise SystemExit(f"adapter is not a file: {adapter}")

    packet_id = args.packet_id
    if tasks.get("packet_id") != packet_id:
        raise SystemExit(f"task packet_id {tasks.get('packet_id')!r} != --packet-id {packet_id!r}")
    if schedule.get("packet_id") != packet_id:
        raise SystemExit(f"schedule packet_id {schedule.get('packet_id')!r} != --packet-id {packet_id!r}")

    schedule_task_hash = schedule.get("task_file_sha256")
    tasks_sha = sha256_file(args.tasks)
    if schedule_task_hash and schedule_task_hash != tasks_sha:
        raise SystemExit(
            "schedule was built against different task bytes: "
            f"schedule.task_file_sha256={schedule_task_hash} actual={tasks_sha}"
        )

    arm_state_hashes = parse_pairs(args.arm_state_hash, "--arm-state-hash")
    if set(arm_state_hashes) != set(ARMS):
        missing = sorted(set(ARMS) - set(arm_state_hashes))
        extra = sorted(set(arm_state_hashes) - set(ARMS))
        raise SystemExit(f"--arm-state-hash must cover exactly the four arms; missing={missing} extra={extra}")

    raw_ceiling = parse_pairs(args.ceiling, "--ceiling")
    if set(raw_ceiling) != set(RESOURCE_FIELDS):
        missing = sorted(set(RESOURCE_FIELDS) - set(raw_ceiling))
        extra = sorted(set(raw_ceiling) - set(RESOURCE_FIELDS))
        raise SystemExit(f"--ceiling must cover exactly the six resource fields; missing={missing} extra={extra}")
    ceiling: dict[str, int] = {}
    for field, value in raw_ceiling.items():
        try:
            parsed = int(value)
        except ValueError as exc:
            raise SystemExit(f"--ceiling {field} must be an integer, got {value!r}") from exc
        if parsed < 0:
            raise SystemExit(f"--ceiling {field} must be >= 0")
        ceiling[field] = parsed

    self_test: dict[str, Any] | None = None
    if args.self_test_adapter_id or args.self_test_mode or args.self_test_expected_outcome:
        if not (args.self_test_adapter_id and args.self_test_mode and args.self_test_expected_outcome):
            raise SystemExit(
                "harness self-test requires --self-test-adapter-id, --self-test-mode "
                "and --self-test-expected-outcome together"
            )
        self_test = {
            "adapter_id": args.self_test_adapter_id,
            "mode": args.self_test_mode,
            "expected_outcome": args.self_test_expected_outcome,
        }

    if args.sham_policy_hash is None and self_test is None:
        raise SystemExit(
            "--sham-policy-hash is required for a non-self-test contract: the RAKL_SHAM_MEMORY arm "
            "cannot be interpreted without the frozen sham construction policy"
        )

    return {
        "schema_version": "paper5-executor-contract-v1",
        "packet_id": packet_id,
        "tasks_sha256": tasks_sha,
        "schedule_sha256": sha256_file(args.schedule),
        "adapter_path": str(adapter),
        "adapter_sha256": sha256_file(adapter),
        "arm_state_hashes": arm_state_hashes,
        "resource_ceiling": ceiling,
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "evaluator_protocol_hash": args.evaluator_protocol_hash,
        "tool_policy_id": args.tool_policy_id,
        "source_cutoff_id": args.source_cutoff_id,
        "sham_policy_hash": args.sham_policy_hash,
        "grants_scientific_authority": False,
        "harness_self_test": self_test,
        "frozen_at": args.frozen_at,
        "notes": args.notes,
    }


def validate_contract_document(contract: dict[str, Any]) -> None:
    if not CONTRACT_SCHEMA_PATH.is_file():
        raise SystemExit(f"contract schema missing, cannot validate: {CONTRACT_SCHEMA_PATH}")
    schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda err: list(err.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in err.path) or '<root>'}: {err.message}" for err in errors[:5]
        )
        raise SystemExit(f"contract violates paper5-executor-contract-v1: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--evaluator-protocol-hash", required=True)
    parser.add_argument("--tool-policy-id", required=True)
    parser.add_argument("--source-cutoff-id", required=True)
    parser.add_argument(
        "--arm-state-hash",
        action="append",
        default=[],
        metavar="ARM=HASH",
        help="frozen evaluation-state identity for one arm; required once per arm",
    )
    parser.add_argument(
        "--ceiling",
        action="append",
        default=[],
        metavar="FIELD=INT",
        help="shared resource ceiling; required once per resource field",
    )
    parser.add_argument("--sham-policy-hash", default=None)
    parser.add_argument("--frozen-at", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--self-test-adapter-id", default=None)
    parser.add_argument("--self-test-mode", default=None)
    parser.add_argument("--self-test-expected-outcome", default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if args.out.exists():
        raise SystemExit(f"refusing to overwrite an existing frozen contract: {args.out}")

    contract = build_contract(args)
    validate_contract_document(contract)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)
    print(sha256_file(args.out))


if __name__ == "__main__":
    main()
