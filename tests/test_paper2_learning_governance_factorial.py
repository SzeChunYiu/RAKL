"""Tests for the Paper II learning x governance 2x2 factorial protocol (#155).

The design exists to make a *specific* past failure unrepeatable. LUNARC job
3476548 returned an honest negative, but two defects meant the LEARNING arm never
instantiated the mechanism under test:

* development success rate was 0.0 on both arms, so the frozen learned state held
  no verified corrective knowledge -- transfer was measured from the empty set;
* ``total_retrieval_calls`` was 0.0 on all four arm/phase rows while the learning
  arm used 4376 input tokens against the reset arm's 1502, the signature of
  whole-state prompt stuffing rather than selective retrieval.

So the protocol schema does not merely describe a 2x2. It structurally requires
the two gates that separate "experience did not help" from "there was no
experience", and it requires the design to admit outcomes other than success.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "paper2-learning-governance-factorial-protocol-v2.schema.json"
PROTOCOL_PATH = ROOT / "research" / "paper2_learning_governance_factorial_v1" / "PROTOCOL_V1_DRAFT.json"
PREREG_PATH = ROOT / "experiments" / "paper2" / "LEARNING_GOVERNANCE_FACTORIAL_PREREGISTRATION_V1.md"

CELLS = ("U-R", "U-L", "G-R", "G-L")


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _protocol() -> dict[str, Any]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def test_schema_is_a_valid_draft202012_schema() -> None:
    Draft202012Validator.check_schema(_schema())


def test_protocol_validates_against_the_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_protocol()), key=lambda err: list(err.path))
    assert not errors, [f"{'/'.join(str(p) for p in err.path)}: {err.message}" for err in errors]


def test_protocol_covers_exactly_the_four_factorial_cells() -> None:
    protocol = _protocol()
    assert set(protocol["cells"]) == set(CELLS)
    combos = {
        (cell["experience"], cell["authority_policy"]) for cell in protocol["cells"].values()
    }
    assert len(combos) == 4, "the four cells must be four distinct experience x authority combinations"


def test_g1_gate_rejects_pseudo_lessons_and_reports_cannot_identify() -> None:
    """A learning cell with no verified corrective knowledge is unidentified, not null."""
    gate = _protocol()["admissibility_gates"]["G1_verified_corrective_knowledge"]
    assert gate["pseudo_lessons_count_toward_gate"] is False
    assert gate["min_verified_objects_per_learning_cell"] >= 1
    assert gate["on_failure"] == "CANNOT_IDENTIFY"


def test_g2_gate_requires_retrieval_to_actually_run() -> None:
    gate = _protocol()["admissibility_gates"]["G2_selective_retrieval_ran"]
    assert gate["min_retrieval_calls_per_task"] >= 1
    assert gate["whole_state_injection_is_failure"] is True
    assert gate["retrieval_budget_matched_in_control"] is True


def test_schema_structurally_enforces_both_anti_defect_gates() -> None:
    """The gates must be unskippable, not merely present in this one instance."""
    gates = _schema()["properties"]["admissibility_gates"]
    assert {"G1_verified_corrective_knowledge", "G2_selective_retrieval_ran"} <= set(gates["required"])
    g1 = gates["properties"]["G1_verified_corrective_knowledge"]
    assert g1["properties"]["pseudo_lessons_count_toward_gate"]["const"] is False
    assert g1["properties"]["on_failure"]["const"] == "CANNOT_IDENTIFY"
    g2 = gates["properties"]["G2_selective_retrieval_ran"]
    assert g2["properties"]["min_retrieval_calls_per_task"]["minimum"] >= 1
    assert g2["properties"]["whole_state_injection_is_failure"]["const"] is True


def test_resource_ceiling_cannot_be_frozen_with_zero_retrieval_budget() -> None:
    """A zero retrieval allowance would make G2 unsatisfiable by construction."""
    ceiling = _schema()["properties"]["frozen_coordinates"]["properties"]["resource_ceiling"]
    assert ceiling["properties"]["retrieval_calls"]["minimum"] >= 1


def test_permissive_control_must_enumerate_what_it_removed() -> None:
    """'Governance disabled' is a strawman; the removed checks must be named."""
    control = _schema()["properties"]["permissive_control"]
    assert "removed_authority_checks" in control["required"]
    assert control["properties"]["removed_authority_checks"]["minItems"] >= 1
    assert control["properties"]["provenance_storage_retained"]["const"] is True
    assert control["properties"]["information_availability_unchanged"]["const"] is True


def test_permissive_control_declares_both_hostile_and_legal_fixtures() -> None:
    control = _protocol()["permissive_control"]
    assert control["hostile_control"]["expected_ungated"] == "ACCEPT"
    assert control["hostile_control"]["expected_gated"] == "REJECT"
    assert control["legal_control"]["expected_ungated"] == "ACCEPT"
    assert control["legal_control"]["expected_gated"] == "ACCEPT"


def test_capability_and_authority_are_never_one_scalar() -> None:
    protocol = _protocol()
    axes = protocol["outcome_axes"]
    assert axes["combined_into_single_scalar"] is False
    assert axes["capability"] and axes["authority"]
    assert _schema()["properties"]["outcome_axes"]["properties"]["combined_into_single_scalar"]["const"] is False
    assert protocol["estimands"]["reported_per_axis"] is True


def test_design_admits_outcomes_other_than_success() -> None:
    """A design that can only produce a positive result is not an experiment."""
    outcomes = _protocol()["admissible_outcomes"]
    assert _schema()["properties"]["admissible_outcomes"]["minItems"] >= 6
    joined = " ".join(outcomes).lower()
    for expected in ("no gain", "no leakage benefit", "null", "cannot_identify", "costs too much"):
        assert expected in joined, expected
    assert "CANNOT_IDENTIFY" in _schema()["properties"]["status"]["enum"]


def test_analysis_treats_the_task_as_the_inferential_unit() -> None:
    analysis = _protocol()["analysis"]
    assert analysis["inferential_unit"] == "task"
    assert analysis["repeated_generations_are_independent"] is False
    assert analysis["stratum_results_are_secondary"] is True


def test_draft_protocol_does_not_claim_a_freeze_it_has_not_made() -> None:
    """Pending sentinels and PROTOCOL_FROZEN are mutually exclusive."""
    protocol = _protocol()
    serialized = json.dumps(protocol)
    has_pending = "PENDING_FREEZE" in serialized
    if protocol["status"] == "PROTOCOL_FROZEN":
        assert not has_pending, "a frozen protocol may not carry PENDING_FREEZE sentinels"
    else:
        assert protocol["status"] == "DRAFT"
        assert has_pending, "a draft protocol should mark unfrozen coordinates explicitly"
    assert protocol["grants_scientific_authority"] is False


def test_protocol_records_its_upstream_blockers() -> None:
    assert set(_protocol()["upstream_blockers"]) == {238, 242}


def test_protocol_supersedes_the_six_field_closeout_stub() -> None:
    supersedes = " ".join(_protocol()["supersedes"])
    assert "learning-governance-factorial-protocol-v1" in supersedes
    stub = json.loads(
        (ROOT / "schemas" / "learning-governance-factorial-protocol-v1.schema.json").read_text(encoding="utf-8")
    )
    # The stub is a six-field closeout placeholder; it has no way to express a 2x2.
    assert "cells" not in stub["properties"]
    assert "cells" in _schema()["properties"]
    assert len(_schema()["required"]) > len(stub["required"])


def test_preregistration_document_exists_and_cites_the_prior_negative() -> None:
    text = PREREG_PATH.read_text(encoding="utf-8")
    for marker in ("3476548", "CANNOT_IDENTIFY", "retrieval_calls", "4376", "1502"):
        assert marker in text, marker


@pytest.mark.parametrize("field", ["U-R", "U-L", "G-R", "G-L"])
def test_learning_cells_carry_a_state_slot_and_reset_cells_do_not_learn(field: str) -> None:
    cell = _protocol()["cells"][field]
    if cell["experience"] == "LEARNING":
        assert "post_development_state_hash" in cell
        assert "verified_corrective_object_count" in cell
    else:
        assert cell["experience"] == "RESET"
        assert cell["post_development_state_hash"] is None
