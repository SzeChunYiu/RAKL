"""Done-for-now contract tests for research issue closeout stubs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from rakl.issue_closeout_stubs import ISSUE_SCHEMA, freeze_all_closeout_stubs, freeze_stub

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


@pytest.mark.parametrize("issue,schema_version", sorted(ISSUE_SCHEMA.items()))
def test_schema_file_exists_and_validates_stub(issue: int, schema_version: str) -> None:
    path = SCHEMAS / f"{schema_version}.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    report = freeze_stub(issue, "fixture_reason")
    payload = report.to_dict()
    Draft202012Validator(schema).validate(payload)
    assert payload["grants_scientific_authority"] is False
    assert payload["issue"] == issue
    assert payload["schema_version"] == schema_version


def test_freeze_all_covers_target_issues() -> None:
    reports = freeze_all_closeout_stubs()
    assert {r.issue for r in reports} == {129, 130, 132, 155, 156, 157}
    assert all(r.grants_scientific_authority is False for r in reports)


def test_cannot_grant_authority() -> None:
    with pytest.raises(ValueError, match="cannot grant"):
        freeze_stub(129, "x").__class__(
            schema_version=ISSUE_SCHEMA[129],
            status=freeze_stub(129, "x").status,
            issue=129,
            reasons=("x",),
            grants_scientific_authority=True,
        )


def test_inventory_doc_names_all_issues() -> None:
    text = (ROOT / "research" / "ISSUE_CLOSEOUT_STUBS_20260811.md").read_text(encoding="utf-8")
    for issue in (129, 130, 132, 155, 156, 157):
        assert f"#{issue}" in text
    assert "NO_SCIENTIFIC_AUTHORITY" in text


def test_alias_modules_import() -> None:
    from rakl import (
        associative_experience,
        closest_parent_ablation,
        conceptual_basis_independence,
        epistemic_gps,
        experience_to_method_promotion,
        learning_governance_factorial,
    )

    assert associative_experience.freeze_report("a").issue == 129
    assert epistemic_gps.freeze_report("a").issue == 130
    assert conceptual_basis_independence.freeze_report("a").issue == 132
    assert learning_governance_factorial.freeze_report("a").issue == 155
    assert closest_parent_ablation.freeze_report("a").issue == 156
    assert experience_to_method_promotion.freeze_report("a").issue == 157
