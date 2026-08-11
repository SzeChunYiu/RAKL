from __future__ import annotations
import json
from pathlib import Path
import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_paper5_completion_does_not_false_freeze_missing_artifacts():
    completion = json.loads((ROOT / "research/paper5_novelty_audit_v1/AI_OPERATOR_DEMOTED_COMPLETION.json").read_text())
    schema = json.loads((ROOT / "schemas/paper5-novelty-audit-freeze-stub-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(completion)
    for missing in [
        "SAMPLE_PLAN.json",
        "PRECISION_POWER_RECEIPT.json",
        "PUBLIC_AUDIT_PACKET.json",
        "AUDIT_ANALYSIS.json",
    ]:
        assert completion["artifact_status"][missing] == "MISSING"
        assert not (ROOT / "research/paper5_novelty_audit_v1" / missing).exists()
    assert completion["independent_review_claimed"] is False
    assert completion["grants_scientific_authority"] is False


def test_paper5_substantive_demoted_track_present():
    track = ROOT / "research/paper5_novelty_audit_v1/ai_operator_demoted_v1"
    for name in [
        "SAMPLE_PLAN.json",
        "PUBLIC_AUDIT_PACKET.json",
        "ANNOTATOR_A_RESPONSE.json",
        "ANNOTATOR_B_RESPONSE.json",
        "ADJUDICATION.json",
        "AUDIT_ANALYSIS.json",
        "FINAL_AUDIT_RECEIPT.json",
        "HONESTY_STAMP_AI_OPERATOR.json",
    ]:
        assert (track / name).is_file(), name
    honesty = json.loads((track / "HONESTY_STAMP_AI_OPERATOR.json").read_text())
    final = json.loads((track / "FINAL_AUDIT_RECEIPT.json").read_text())
    assert honesty["annotator_class"] == "AI_OPERATOR"
    assert honesty["independent_external_human"] is False
    assert final["constitution_grade_independent_peer_review"] is False
    assert final["acceptance_under_demoted_authority"]["met"] is True


def test_paper1_dual_track_supplement_fail_closed():
    receipt = json.loads((ROOT / "review/paper1/ai_operator_demoted_v1/DUAL_TRACK_DEMOTED_REVIEW_RECEIPT.json").read_text())
    schema = json.loads((ROOT / "schemas/paper1-dual-track-demoted-review-receipt.schema.json").read_text())
    Draft202012Validator(schema).validate(receipt)
    assert receipt["independence_claim"] is False
    assert receipt["tracks"]["external_independent_human"]["status"] == "ABSENT"
