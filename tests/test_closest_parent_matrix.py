"""Validation suite for the closest-parent matrix gate (issue #156).

The committed matrix must pass. More importantly, the gate must be shown able
to fail: every rule is tripped here by mutating a copy of the real matrix. A
gate that cannot reject anything is decoration, and this one exists specifically
to stop novelty language outrunning the reading behind it.
"""

from __future__ import annotations

import copy
import json
from typing import Any, MutableMapping

import pytest

from rakl.closest_parent_matrix import (
    MATRIX_PATH,
    REQUIRED_FUNCTIONS,
    load_matrix,
    validate_matrix,
)


@pytest.fixture()
def matrix() -> MutableMapping[str, Any]:
    return copy.deepcopy(dict(load_matrix()))


def _row(matrix: MutableMapping[str, Any], claim: str) -> MutableMapping[str, Any]:
    for row in matrix["functions"]:
        if row["claim_allowed_today"] == claim:
            return row
    raise AssertionError(f"no row with claim {claim}")


def _rules(matrix: MutableMapping[str, Any]) -> set[str]:
    return {v.rule for v in validate_matrix(matrix).violations}


# --------------------------------------------------------------------------
# the committed artifact
# --------------------------------------------------------------------------


def test_committed_matrix_is_valid() -> None:
    report = validate_matrix()
    assert report.ok, [str(v) for v in report.violations]


def test_committed_matrix_covers_every_required_function() -> None:
    named = {row["function"] for row in load_matrix()["functions"]}  # type: ignore[index]
    assert set(REQUIRED_FUNCTIONS) <= named
    assert len(named) == len(REQUIRED_FUNCTIONS)


def test_matrix_is_not_self_serving() -> None:
    """A novelty-defence matrix that finds RAKL ahead everywhere is not a defence.

    The committed matrix must concede functions to prior art and must record at
    least one function where a parent is strictly stronger. CANNOT_CHECK is
    required only while some residual-candidate parent remains unread; after a
    full-text adjudication pass the count may honestly be zero.
    """

    report = validate_matrix()
    counts = report.claim_counts
    assert counts.get("INHERITED_NO_CLAIM", 0) >= 5
    assert counts.get("PARENT_STRONGER_ADOPT", 0) >= 1
    parents = {p["id"]: p for p in load_matrix()["parents"]}  # type: ignore[index]
    unread_residual_parents = {
        row["closest_parent"]
        for row in load_matrix()["functions"]  # type: ignore[index]
        if parents[row["closest_parent"]]["evidence_level"]
        not in {"FULL_TEXT", "FULL_TEXT_PARTIAL"}
        and row["claim_allowed_today"] in {"CANNOT_CHECK", "NARROW_RESIDUAL"}
    }
    if unread_residual_parents:
        assert counts.get("CANNOT_CHECK", 0) >= 1


def test_every_residual_row_rests_on_primary_full_text() -> None:
    parents = {p["id"]: p for p in load_matrix()["parents"]}  # type: ignore[index]
    for row in load_matrix()["functions"]:  # type: ignore[index]
        if row["claim_allowed_today"] != "NARROW_RESIDUAL":
            continue
        level = parents[row["closest_parent"]]["evidence_level"]
        assert level in {"FULL_TEXT", "FULL_TEXT_PARTIAL"}, row["function"]
        assert row["falsifier"].strip()


def test_no_arm_is_named_after_an_external_system() -> None:
    for arm in load_matrix()["ladder"]:  # type: ignore[index]
        upper = arm["arm"].upper()
        for system in ("AUTOSCI", "MEMTX", "PPMF", "MEMCLAW"):
            assert system not in upper


# --------------------------------------------------------------------------
# the gate must be able to reject
# --------------------------------------------------------------------------


def test_rejects_residual_claimed_on_an_abstract_only_parent(
    matrix: MutableMapping[str, Any],
) -> None:
    """The central rule. Conceding is cheap; claiming needs the full text."""

    row = _row(matrix, "NARROW_RESIDUAL")
    parent = next(p for p in matrix["parents"] if p["id"] == row["closest_parent"])
    parent["evidence_level"] = "ABSTRACT_ONLY"
    row["evidence_level"] = "ABSTRACT_ONLY"
    row["claim_allowed_today"] = "NARROW_RESIDUAL"
    row["falsifier"] = "some falsifier"
    row["rakl_residual"] = "some residual"
    assert "residual_needs_full_text" in _rules(matrix)


def test_rejects_residual_without_a_falsifier(matrix: MutableMapping[str, Any]) -> None:
    _row(matrix, "NARROW_RESIDUAL")["falsifier"] = "  "
    assert "residual_needs_falsifier" in _rules(matrix)


def test_rejects_residual_without_a_discriminator(matrix: MutableMapping[str, Any]) -> None:
    _row(matrix, "NARROW_RESIDUAL")["required_discriminator"] = ""
    assert "residual_needs_discriminator" in _rules(matrix)


def test_rejects_cannot_check_without_a_next_reading(
    matrix: MutableMapping[str, Any],
) -> None:
    row = _row(matrix, "INHERITED_NO_CLAIM")
    row["claim_allowed_today"] = "CANNOT_CHECK"
    row["required_discriminator"] = ""
    assert "cannot_check_needs_next_step" in _rules(matrix)


def test_rejects_an_arm_named_after_an_external_system(
    matrix: MutableMapping[str, Any],
) -> None:
    matrix["ladder"][3]["arm"] = "A3_MEMTX"
    assert "arm_not_named_after_system" in _rules(matrix)


def test_rejects_an_arm_that_does_not_state_the_gap(
    matrix: MutableMapping[str, Any],
) -> None:
    matrix["ladder"][3]["not_the_system"] = ""
    assert "arm_states_the_gap" in _rules(matrix)


def test_rejects_an_incomplete_intervention_contract(
    matrix: MutableMapping[str, Any],
) -> None:
    matrix["intervention_contracts"][0]["falsifier"] = ""
    assert "contract_complete" in _rules(matrix)


def test_rejects_a_missing_required_function(matrix: MutableMapping[str, Any]) -> None:
    matrix["functions"] = matrix["functions"][:-1]
    assert "required_coverage" in _rules(matrix)


def test_rejects_a_row_with_no_rakl_pointer(matrix: MutableMapping[str, Any]) -> None:
    matrix["functions"][0]["rakl_implementation"] = ""
    assert "rakl_pointer" in _rules(matrix)


def test_rejects_evidence_level_inconsistent_with_the_parent(
    matrix: MutableMapping[str, Any],
) -> None:
    matrix["functions"][0]["evidence_level"] = "ABSTRACT_ONLY"
    assert "evidence_level_consistent" in _rules(matrix)


def test_rejects_result_language(matrix: MutableMapping[str, Any]) -> None:
    matrix["functions"][0]["rakl_residual"] = "RAKL outperform the parent here"
    assert "no_results_claimed" in _rules(matrix)


def test_rejects_an_authority_granting_matrix(matrix: MutableMapping[str, Any]) -> None:
    matrix["grants_scientific_authority"] = True
    assert "no_authority" in _rules(matrix)


def test_rejects_a_feasible_parent_without_a_note(
    matrix: MutableMapping[str, Any],
) -> None:
    for parent in matrix["parents"]:
        if parent["feasibility"] == "FUNCTION_MATCHED_ABLATION_FEASIBLE":
            parent["feasibility_note"] = ""
            break
    assert "feasibility_justified" in _rules(matrix)


def test_rejects_an_unknown_parent_reference(matrix: MutableMapping[str, Any]) -> None:
    matrix["functions"][0]["closest_parent"] = "nonexistent"
    assert "parent_known" in _rules(matrix)


def test_report_grants_no_authority() -> None:
    assert validate_matrix().grants_authority is False


def test_matrix_file_is_valid_json_and_committed() -> None:
    assert MATRIX_PATH.is_file()
    json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
