from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from .math_research_assurance import (
    FormalizationWitness,
    MathResearchRecord,
    NoveltyCertificate,
    ProofReceipt,
    classify_math_record,
)


def _construct_dataclass(cls, payload: dict[str, Any] | None):
    if payload is None:
        return None
    allowed = {field.name for field in fields(cls)}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")
    if cls is FormalizationWitness and "notes" in payload:
        payload = {**payload, "notes": tuple(payload["notes"])}
    if cls is ProofReceipt and "axioms" in payload:
        payload = {**payload, "axioms": tuple(payload["axioms"])}
    if cls is NoveltyCertificate:
        payload = {
            **payload,
            "corpora": tuple(payload.get("corpora", ())),
            "search_routes": tuple(payload.get("search_routes", ())),
            "candidate_matches": tuple(payload.get("candidate_matches", ())),
            "coverage_notes": tuple(payload.get("coverage_notes", ())),
        }
    return cls(**payload)


def record_from_dict(payload: dict[str, Any]) -> MathResearchRecord:
    data = dict(payload)
    data["formalization"] = _construct_dataclass(
        FormalizationWitness, data.get("formalization")
    )
    data["proof"] = _construct_dataclass(ProofReceipt, data.get("proof"))
    data["novelty"] = _construct_dataclass(NoveltyCertificate, data.get("novelty"))
    return MathResearchRecord(**data)


def evaluate_task(task: dict[str, Any]) -> dict[str, Any]:
    report = classify_math_record(record_from_dict(task["record"]))
    reasons = set(report.reasons)
    expected_reason = task.get("expected_reason")
    passed = report.stage.value == task["expected_stage"]
    if expected_reason is not None:
        passed = passed and expected_reason in reasons
    return {
        "id": task["id"],
        "passed": passed,
        "expected_stage": task["expected_stage"],
        "actual_stage": report.stage.value,
        "verdict": report.verdict.value,
        "reasons": list(report.reasons),
    }


def run_benchmark(path: str | Path) -> dict[str, Any]:
    tasks = json.loads(Path(path).read_text(encoding="utf-8"))
    results = [evaluate_task(task) for task in tasks]
    passed = sum(result["passed"] for result in results)
    return {
        "task_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "all_passed": passed == len(results),
        "results": results,
    }
