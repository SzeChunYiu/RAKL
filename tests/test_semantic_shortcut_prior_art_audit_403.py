"""Internal prior-art audit packet for semantic-shortcut system claim (#403)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/semantic_shortcut_prior_art_audit_v1"
PARENT = ROOT / "research/FIVE_PAPER_SEMANTIC_SHORTCUT_NOVELTY_AUDIT_20260812.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


REQUIRED = [
    "NOVELTY_PROTOCOL.md",
    "FROZEN_CLAIM.json",
    "SEARCH_UNIVERSE.json",
    "QUERY_LOG.jsonl",
    "CANDIDATE_PRIOR_ART.jsonl",
    "COMPONENT_COMPARISON.json",
    "COMPONENT_COMPARISON.csv",
    "STRONGEST_PARENT_ANALYSIS.md",
    "REVIEWER_A.json",
    "REVIEWER_B.json",
    "ADJUDICATION.json",
    "PROVENANCE_RECEIPT.json",
    "FINAL_NOVELTY_RECEIPT.json",
    "ISSUE_403_TERMINAL_RECEIPT.json",
]


def test_required_artifacts_present() -> None:
    for name in REQUIRED:
        assert (PACKET / name).is_file(), name


def test_frozen_claim_before_conclusions_invariants() -> None:
    claim = _load(PACKET / "FROZEN_CLAIM.json")
    assert claim["issue"] == 403
    assert claim["authority_class"] == "INTERNAL_PRIOR_ART_AUDIT"
    assert claim["independent_external_review"] is False
    assert claim["humans_invented"] is False
    assert claim["capable_model_available"] == "NO_REFUTED"
    assert claim["implementation_subject"]["pr"] == 376
    assert claim["grants_scientific_authority"] is False
    for key, rel in claim["subject_files"].items():
        assert _sha256(ROOT / rel) == claim["subject_file_sha256"][key]


def test_reviewers_are_internal_not_invented_humans() -> None:
    a = _load(PACKET / "REVIEWER_A.json")
    b = _load(PACKET / "REVIEWER_B.json")
    adj = _load(PACKET / "ADJUDICATION.json")
    for obj in (a, b):
        assert obj["independent_external_human"] is False
        assert obj["same_process"] is True
        assert obj["grants_scientific_authority"] is False
    assert adj["independent_external_adjudicator"] is False
    assert adj["humans_invented"] is False


def test_final_and_terminal_receipts_honest() -> None:
    final = _load(PACKET / "FINAL_NOVELTY_RECEIPT.json")
    terminal = _load(PACKET / "ISSUE_403_TERMINAL_RECEIPT.json")
    assert final["scoped_verdict"] == "SYSTEM_COMBINATION_NOT_FOUND_WITHIN_REGISTERED_SEARCH"
    assert final["absolute_firstness_claimed"] is False
    assert final["independent_external_review"] is False
    assert (
        final["acceptance_checklist"]["independent_roles_mode"]
        == "EXPLICITLY_INTERNAL"
    )
    assert terminal["issue"] == 403
    assert terminal["terminal_status"] == (
        "INTERNAL_PRIOR_ART_AUDIT_COMPLETE__INDEPENDENT_REVIEW_ABSENT"
    )
    assert terminal["humans_invented"] is False
    assert terminal["grants_scientific_authority"] is False
    assert terminal["capable_model_available"] == "NO_REFUTED"
    assert (
        terminal["evidence_pointers"]["final_receipt_sha256"]
        == _sha256(PACKET / "FINAL_NOVELTY_RECEIPT.json")
    )
    assert PARENT.is_file()
