"""Terminal floor receipts for #324 / #326 / #332."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_issue_324_cannot_execute_confirmatory_alr() -> None:
    receipt = _load("research/paper2_alr_confirmatory_v1/ISSUE_324_TERMINAL_RECEIPT.json")
    assert receipt["issue"] == 324
    assert receipt["terminal_status"] == "CANNOT_EXECUTE_CONFIRMATORY_MODEL_COMPARISON"
    assert receipt["grants_scientific_authority"] is False
    assert receipt["promotional_lift_claim_allowed"] is False
    harvest = _load(
        "research/paper2_alr_model_baselines_v1/native_job_3476748/receipts/alr_baselines_v1/harvest-3476748.json"
    )
    assert harvest["job_verdict"] == "MODEL_SCORED_NON_CONFIRMATORY"
    assert harvest["grants_authority"] is False


def test_issue_326_power_limited_retain_v21() -> None:
    terminal = _load("research/paper3_successor_validation_v1/ISSUE_326_TERMINAL_RECEIPT.json")
    decision = _load("research/paper3_successor_validation_v1/DECISION_RECEIPT.json")
    zero = _load("research/paper3_successor_validation_v1/ZERO_LABELS_REPO_WIDE_RECEIPT.json")
    assert terminal["terminal_status"] == "POWER_LIMITED_RETAIN_V2_1"
    assert decision["terminal_status"] == "POWER_LIMITED_RETAIN_V2_1"
    assert decision["expansion_feasible_within_ceiling"] is False
    assert zero["observation"] == "ZERO_LABELS_REPO_WIDE"
    assert zero["counts"]["external_annotations"] == 0
    assert terminal["grants_scientific_authority"] is False


def test_issue_332_cannot_obtain_independent_humans() -> None:
    receipt = _load("research/paper3_independent_human_residual_v1/ISSUE_332_TERMINAL_RECEIPT.json")
    harvest = _load(
        "research/paper3/ai_operator_v2_1/lunarc_demoted_v2/harvest-3476753-3476754.json"
    )
    assert receipt["issue"] == 332
    assert receipt["terminal_status"] == "CANNOT_OBTAIN_INDEPENDENT_EXTERNAL_HUMANS"
    assert receipt["acceptance_assessment"]["constitution_grade_independent_review_claimed"] is False
    assert harvest["authority_class"] == "DEMOTED_AI_OPERATOR"
    assert harvest["independent_external_human"] is False
    assert harvest["verdict"] == "HARVESTED_DEMOTED_AI_OPERATOR_PILOTS_PASS"
    assert {job["slurm_job_id"] for job in harvest["jobs"]} == {"3476753", "3476754"}
