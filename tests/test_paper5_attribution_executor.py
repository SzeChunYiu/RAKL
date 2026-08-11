"""Regression tests binding the Paper 5 attribution record schema to its consumers.

Before this suite, ``schemas/paper5-attribution-run-v1.schema.json`` and
``experiments/paper5/run_attribution_schedule.py`` were mutually unsatisfiable:

* the orchestrator required ``repetition`` to equal the frozen schedule row, but
  the schema declared no ``repetition`` property under ``additionalProperties:
  false``;
* the orchestrator read all six resource counters at the top level of the
  record, but the schema nested them inside ``resource_usage`` and forbade
  top-level extras, additionally naming two of them differently
  (``preprocessing_tool_calls`` / ``external_retrieval_calls`` versus the
  ``tool_calls`` / ``retrieval_calls`` used by both Python consumers).

Either way round, no record could satisfy both, so the four-arm study could not
execute. Nothing enforced the schema either, so the contradiction was invisible.
These tests keep the schema, the orchestrator and the analyzer in one contract.
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
SCHEMA_PATH = ROOT / "schemas" / "paper5-attribution-run-v1.schema.json"


def _load_module(relative: str, name: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runner() -> Any:
    return _load_module("experiments/paper5/run_attribution_schedule.py", "run_attribution_schedule")


def _analyzer() -> Any:
    return _load_module("experiments/paper5/analyze_attribution_results.py", "analyze_attribution_results")


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


STATE_HASH = "a" * 64


def _contract() -> dict[str, Any]:
    return {
        "arm_state_hashes": {
            "MODEL_ONLY": STATE_HASH,
            "RAKL_RESET": STATE_HASH,
            "RAKL_SHAM_MEMORY": STATE_HASH,
            "RAKL_LEARNING": STATE_HASH,
        },
        "resource_ceiling": {
            "model_input_tokens": 10000,
            "model_output_tokens": 10000,
            "preprocessing_model_tokens": 10000,
            "tool_calls": 50,
            "retrieval_calls": 50,
            "wall_time_ms": 600000,
        },
    }


def _schedule_row() -> dict[str, Any]:
    return {
        "sequence": 1,
        "task_id": "T001",
        "stratum": "REPEATED_FAMILY",
        "repetition": 1,
        "arm_order_position": 1,
        "arm": "RAKL_LEARNING",
        "run_id": "T001-r1-RAKL_LEARNING",
    }


def _raw_output(tmp_path: Path) -> Path:
    raw = tmp_path / "raw_output.json"
    raw.write_text(json.dumps({"answer": "x"}), encoding="utf-8")
    return raw


def _record(raw_path: Path, **overrides: Any) -> dict[str, Any]:
    record = {
        "run_id": "T001-r1-RAKL_LEARNING",
        "task_id": "T001",
        "repetition": 1,
        "arm": "RAKL_LEARNING",
        "state_before_hash": STATE_HASH,
        "state_after_hash": STATE_HASH,
        "success": True,
        "score": 0.75,
        "failure_signature": [],
        "validity_failures": [],
        "output_hash": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "model_input_tokens": 1200,
        "model_output_tokens": 300,
        "preprocessing_model_tokens": 0,
        "tool_calls": 2,
        "retrieval_calls": 3,
        "wall_time_ms": 4200,
    }
    record.update(overrides)
    return record


def test_schema_is_a_valid_draft202012_schema() -> None:
    Draft202012Validator.check_schema(_schema())


def test_schema_valid_record_also_passes_the_orchestrator(tmp_path: Path) -> None:
    """The regression that blocked execution: both checks must accept one record."""
    runner = _runner()
    raw = _raw_output(tmp_path)
    record = _record(raw)

    Draft202012Validator(_schema()).validate(record)
    runner.validate_record(record, _schedule_row(), _contract(), raw, runner.load_record_validator())


def test_orchestrator_resource_fields_are_all_declared_by_the_schema() -> None:
    runner = _runner()
    properties = set(_schema()["properties"])
    assert set(runner.RESOURCE_FIELDS) <= properties
    assert set(runner.RESOURCE_FIELDS) <= set(_schema()["required"])


def test_analyzer_and_orchestrator_agree_on_resource_field_names() -> None:
    assert tuple(_analyzer().RESOURCE_FIELDS) == tuple(_runner().RESOURCE_FIELDS)


def test_schema_requires_every_identity_field_the_orchestrator_pins() -> None:
    required = set(_schema()["required"])
    assert {"run_id", "task_id", "repetition", "arm"} <= required
    assert {"state_before_hash", "state_after_hash", "output_hash"} <= required


def test_analyzer_optional_secondary_endpoints_remain_schema_valid(tmp_path: Path) -> None:
    """additionalProperties is false, so the analyzer's optional fields must be declared."""
    raw = _raw_output(tmp_path)
    record = _record(raw)
    for field in _analyzer().OPTIONAL_BOOLEAN_FIELDS:
        record[field] = False
    Draft202012Validator(_schema()).validate(record)


def test_legacy_nested_resource_usage_record_is_rejected(tmp_path: Path) -> None:
    """The pre-fix schema shape must not silently enter the results JSONL."""
    runner = _runner()
    raw = _raw_output(tmp_path)
    legacy = {
        "run_id": "T001-r1-RAKL_LEARNING",
        "task_id": "T001",
        "arm": "RAKL_LEARNING",
        "state_before_hash": STATE_HASH,
        "state_after_hash": STATE_HASH,
        "success": True,
        "score": 0.75,
        "failure_signature": [],
        "validity_failures": [],
        "output_hash": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "resource_usage": {
            "model_input_tokens": 1200,
            "model_output_tokens": 300,
            "preprocessing_model_tokens": 0,
            "preprocessing_tool_calls": 2,
            "external_retrieval_calls": 3,
            "wall_time_ms": 4200,
        },
    }
    assert not Draft202012Validator(_schema()).is_valid(legacy)
    with pytest.raises(SystemExit):
        runner.validate_record(legacy, _schedule_row(), _contract(), raw, runner.load_record_validator())


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"repetition": 2}, "repetition drifts from the frozen schedule row"),
        ({"task_id": "T999"}, "task identity drifts"),
        ({"state_after_hash": "b" * 64}, "evaluation state mutated"),
        ({"retrieval_calls": 51}, "resource ceiling exceeded"),
        ({"success": False, "failure_signature": []}, "failed run without a failure signature"),
        ({"score": 1.5}, "score outside [0,1]"),
    ],
)
def test_orchestrator_rejects_invalid_records(tmp_path: Path, overrides: dict[str, Any], reason: str) -> None:
    runner = _runner()
    raw = _raw_output(tmp_path)
    record = _record(raw, **overrides)
    with pytest.raises(SystemExit):
        runner.validate_record(record, _schedule_row(), _contract(), raw, runner.load_record_validator())


def test_orchestrator_rejects_output_hash_not_binding_raw_bytes(tmp_path: Path) -> None:
    runner = _runner()
    raw = _raw_output(tmp_path)
    record = _record(raw, output_hash="c" * 64)
    with pytest.raises(SystemExit):
        runner.validate_record(record, _schedule_row(), _contract(), raw, runner.load_record_validator())


def test_missing_schema_file_is_cannot_check_not_a_silent_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner()
    monkeypatch.setattr(runner, "RECORD_SCHEMA_PATH", ROOT / "schemas" / "does-not-exist.json")
    with pytest.raises(SystemExit):
        runner.load_record_validator()
