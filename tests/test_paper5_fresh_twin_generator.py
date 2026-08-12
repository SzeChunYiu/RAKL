"""Hostile tests for Paper 5 fresh replay twin generator (#446 lane 7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper5_fresh_twin_generator import (
    DEFAULT_REGISTRY_PATH,
    build_freeze_stub,
    generate_dev_universe,
    generate_twin_task,
    load_failure_family_registry,
    split_solver_evaluator,
    sweep_leakage,
    task_id_for,
    verify_action,
)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SCRIPT = ROOT / "experiments" / "paper5" / "freeze_fresh_twin_protocol.py"


def test_registry_has_six_families():
    registry = load_failure_family_registry()
    assert len(registry["families"]) == 6
    assert registry["outcome_access_status"] == "NO_OUTCOME_ACCESSED"


@pytest.mark.parametrize(
    "family_id",
    [
        "QUANTIFIER_SCOPE_LOCAL_GLOBAL",
        "POINTWISE_UNIFORM_FAMILY",
        "NORM_CONORM_MISMATCH",
        "PRODUCER_CONSUMER_SCOPE",
        "SAME_ROOT_CORROBORATION",
        "LOCAL_CORRECT_WRONG_CONSUMER",
    ],
)
def test_valid_and_invalid_twins_have_opposite_gold(family_id: str):
    valid = generate_twin_task(family_id=family_id, seed=7, twin_kind="VALID")
    invalid = generate_twin_task(family_id=family_id, seed=7, twin_kind="INVALID")
    assert valid["evaluator_bundle"]["correct_action"] == "ACCEPT_VALID_GLUE"
    assert invalid["evaluator_bundle"]["correct_action"] == "REJECT_FALSE_TRANSFER"
    assert valid["task_id"] != invalid["task_id"]


def test_solver_bundle_excludes_hidden_gold():
    task = generate_twin_task(
        family_id="QUANTIFIER_SCOPE_LOCAL_GLOBAL",
        seed=0,
        twin_kind="INVALID",
    )
    solver, evaluator = split_solver_evaluator(task)
    solver_text = json.dumps(solver, sort_keys=True)
    assert "correct_action" not in solver_text
    assert "hidden_gold_hash" not in solver_text
    assert "family_id_internal" not in solver_text
    assert "QUANTIFIER_SCOPE" not in solver_text
    assert evaluator["correct_action"] == "REJECT_FALSE_TRANSFER"


def test_task_ids_are_stable_and_blinded():
    first = task_id_for(family_id="POINTWISE_UNIFORM_FAMILY", seed=3, twin_kind="VALID")
    second = task_id_for(family_id="POINTWISE_UNIFORM_FAMILY", seed=3, twin_kind="VALID")
    assert first == second
    assert first.startswith("FT-")
    assert "POINTWISE" not in first


def test_verify_action_matches_evaluator():
    task = generate_twin_task(
        family_id="SAME_ROOT_CORROBORATION",
        seed=1,
        twin_kind="VALID",
    )
    _, evaluator = split_solver_evaluator(task)
    ok = verify_action("ACCEPT_VALID_GLUE", evaluator)
    bad = verify_action("REJECT_FALSE_TRANSFER", evaluator)
    assert ok["is_correct"] is True
    assert bad["is_correct"] is False


def test_dev_universe_leakage_sweep_passes():
    tasks = generate_dev_universe(seeds_per_family=2)
    report = sweep_leakage(tasks)
    assert report["passed"] is True
    assert report["task_count"] == 24


def test_freeze_stub_refuses_scientific_authority():
    stub = build_freeze_stub(seeds_per_family=1)
    assert stub["grants_scientific_authority"] is False
    assert stub["outcome_access_status"] == "NO_OUTCOME_ACCESSED"
    assert stub["status"] == "DESIGN_FROZEN_NO_OUTCOME_ACCESSED"
    assert stub["family_count"] == 6


def test_registry_path_exists():
    assert DEFAULT_REGISTRY_PATH.is_file()


def test_freeze_script_is_present():
    assert FREEZE_SCRIPT.is_file()
