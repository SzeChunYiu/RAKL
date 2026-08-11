"""Tests for the Paper 5 executor contract schema and builder.

``run_attribution_schedule.py`` hard-requires a `paper5-executor-contract-v1`
document, and the #138 addendum comment stated that
`schemas/paper5-executor-contract-v1.schema.json` had been added. It had not:
`ls schemas/paper5*` returned only the run-record schema. There was also no
builder, so the contract had to be hand-written with hand-computed hashes.

The load-bearing test here is `test_built_contract_is_accepted_by_the_orchestrator`:
the builder's output must satisfy the orchestrator's own `validate_contract`,
otherwise the two halves drift apart exactly as the record schema did.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = ROOT / "schemas" / "paper5-executor-contract-v1.schema.json"

PACKET_ID = "paper5-selftest-packet"
STATE = {
    "MODEL_ONLY": "0" * 64,
    "RAKL_RESET": "1" * 64,
    "RAKL_SHAM_MEMORY": "2" * 64,
    "RAKL_LEARNING": "3" * 64,
}
CEILING = {
    "model_input_tokens": 8000,
    "model_output_tokens": 2000,
    "preprocessing_model_tokens": 4000,
    "tool_calls": 20,
    "retrieval_calls": 20,
    "wall_time_ms": 300000,
}


def _load_module(relative: str, name: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _builder() -> Any:
    return _load_module("experiments/paper5/build_executor_contract.py", "build_executor_contract")


def _runner() -> Any:
    return _load_module("experiments/paper5/run_attribution_schedule.py", "run_attribution_schedule")


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(
        json.dumps(
            {
                "packet_id": PACKET_ID,
                "tasks": [
                    {"task_id": "T001", "stratum": "REPEATED_FAMILY"},
                    {"task_id": "T002", "stratum": "CROSS_DOMAIN_TRANSFER"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    tasks_sha = hashlib.sha256(tasks_path.read_bytes()).hexdigest()

    schedule_path = tmp_path / "schedule.json"
    schedule_path.write_text(
        json.dumps({"packet_id": PACKET_ID, "task_file_sha256": tasks_sha, "runs": []}, indent=2),
        encoding="utf-8",
    )

    adapter_path = tmp_path / "adapter.py"
    adapter_path.write_text("# frozen adapter bytes\n", encoding="utf-8")
    return tasks_path, schedule_path, adapter_path


def _argv(tmp_path: Path, out: Path, **overrides: Any) -> list[str]:
    tasks_path, schedule_path, adapter_path = _write_inputs(tmp_path)
    argv = [
        "build_executor_contract.py",
        "--tasks", str(overrides.get("tasks", tasks_path)),
        "--schedule", str(overrides.get("schedule", schedule_path)),
        "--adapter", str(adapter_path),
        "--packet-id", overrides.get("packet_id", PACKET_ID),
        "--model-id", "frozen-model",
        "--model-revision", "rev-1",
        "--evaluator-protocol-hash", "e" * 64,
        "--tool-policy-id", "tool-policy-1",
        "--source-cutoff-id", "cutoff-1",
        "--out", str(out),
    ]
    arms = overrides.get("arms", STATE)
    for arm, value in arms.items():
        argv += ["--arm-state-hash", f"{arm}={value}"]
    ceiling = overrides.get("ceiling", CEILING)
    for field, value in ceiling.items():
        argv += ["--ceiling", f"{field}={value}"]
    if "sham" in overrides:
        if overrides["sham"] is not None:
            argv += ["--sham-policy-hash", overrides["sham"]]
    else:
        argv += ["--sham-policy-hash", "s" * 64]
    return argv


def _run_builder(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    builder = _builder()
    monkeypatch.setattr("sys.argv", argv)
    builder.main()


def test_contract_schema_is_a_valid_draft202012_schema() -> None:
    Draft202012Validator.check_schema(json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8")))


def test_built_contract_is_accepted_by_the_orchestrator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Builder output must satisfy run_attribution_schedule.validate_contract."""
    out = tmp_path / "contract.json"
    argv = _argv(tmp_path, out)
    _run_builder(monkeypatch, argv)

    contract = json.loads(out.read_text(encoding="utf-8"))
    runner = _runner()
    tasks_path = Path(argv[argv.index("--tasks") + 1])
    schedule_path = Path(argv[argv.index("--schedule") + 1])
    adapter_path = Path(contract["adapter_path"])
    runner.validate_contract(contract, tasks_path, schedule_path, adapter_path)


def test_contract_supplies_every_field_the_orchestrator_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "contract.json"
    _run_builder(monkeypatch, _argv(tmp_path, out))
    contract = json.loads(out.read_text(encoding="utf-8"))
    # Fields the orchestrator copies into every run envelope.
    for field in (
        "packet_id",
        "model_id",
        "model_revision",
        "evaluator_protocol_hash",
        "tool_policy_id",
        "source_cutoff_id",
        "resource_ceiling",
        "tasks_sha256",
        "schedule_sha256",
        "adapter_sha256",
        "arm_state_hashes",
    ):
        assert field in contract, field
    assert set(contract["resource_ceiling"]) == set(_runner().RESOURCE_FIELDS)
    assert set(contract["arm_state_hashes"]) == set(_runner().ARMS)
    assert contract["grants_scientific_authority"] is False


def test_builder_refuses_to_overwrite_a_frozen_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "contract.json"
    _run_builder(monkeypatch, _argv(tmp_path, out))
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, _argv(tmp_path, out))


def test_builder_requires_all_four_arm_state_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    partial = {key: value for key, value in STATE.items() if key != "RAKL_SHAM_MEMORY"}
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, _argv(tmp_path, tmp_path / "c.json", arms=partial))


def test_builder_requires_the_full_resource_ceiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    partial = {key: value for key, value in CEILING.items() if key != "retrieval_calls"}
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, _argv(tmp_path, tmp_path / "c.json", ceiling=partial))


def test_builder_rejects_packet_identity_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, _argv(tmp_path, tmp_path / "c.json", packet_id="other-packet"))


def test_builder_rejects_a_schedule_built_against_different_task_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "c.json"
    argv = _argv(tmp_path, out)
    schedule_path = Path(argv[argv.index("--schedule") + 1])
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule["task_file_sha256"] = "f" * 64
    schedule_path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    builder = _builder()
    monkeypatch.setattr("sys.argv", argv)
    with pytest.raises(SystemExit):
        builder.main()


def test_non_self_test_contract_requires_a_frozen_sham_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RAKL_SHAM_MEMORY is uninterpretable without the frozen sham construction policy."""
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, _argv(tmp_path, tmp_path / "c.json", sham=None))


def test_self_test_contract_may_omit_sham_policy_but_must_declare_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "contract.json"
    argv = _argv(tmp_path, out, sham=None) + [
        "--self-test-adapter-id", "paper5_selftest_adapter",
        "--self-test-mode", "NULL_CONSTANT",
        "--self-test-expected-outcome", "all primary lifts exactly 0.0",
    ]
    _run_builder(monkeypatch, argv)
    contract = json.loads(out.read_text(encoding="utf-8"))
    assert contract["harness_self_test"]["mode"] == "NULL_CONSTANT"
    assert contract["sham_policy_hash"] is None


def test_partial_self_test_declaration_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = _argv(tmp_path, tmp_path / "c.json", sham=None) + [
        "--self-test-adapter-id", "paper5_selftest_adapter",
    ]
    with pytest.raises(SystemExit):
        _run_builder(monkeypatch, argv)
