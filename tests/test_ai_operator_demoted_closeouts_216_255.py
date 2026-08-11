from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.ai_operator_demoted_closeout import (
    paper1_demoted_closeout_ok,
    paper5_demoted_completion_ok,
)

ROOT = Path(__file__).resolve().parents[1]


def test_paper1_ai_operator_demoted_responses_validate_and_demote() -> None:
    schema = json.loads((ROOT / "schemas/paper1-external-review-response.schema.json").read_text())
    close_schema = json.loads((ROOT / "schemas/paper1-ai-operator-demoted-closeout.schema.json").read_text())
    base = ROOT / "paper/review/paper1/external_solicitation/ai_operator_demoted"
    close = json.loads((base / "CLOSEOUT_RECEIPT_AI_OPERATOR.json").read_text())
    assert paper1_demoted_closeout_ok(close)
    Draft202012Validator(close_schema).validate(close)
    for name in close["responses"]:
        payload = json.loads((base / name).read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
        assert payload["attestations"]["human_reviewer"] is False
        assert payload["reviewer"]["independent_of_authors_and_project"] is False
        assert payload["declaration"]["peer_review_acceptance"] is False


def test_paper5_ai_operator_demoted_completion_validates() -> None:
    schema = json.loads((ROOT / "schemas/paper5-novelty-audit-freeze-stub-v1.schema.json").read_text())
    payload = json.loads(
        (ROOT / "research/paper5_novelty_audit_v1/AI_OPERATOR_DEMOTED_COMPLETION.json").read_text()
    )
    Draft202012Validator(schema).validate(payload)
    assert paper5_demoted_completion_ok(payload)
