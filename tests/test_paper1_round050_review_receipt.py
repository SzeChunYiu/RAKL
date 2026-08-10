from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research" / "receipts" / "PAPER1_ROUND050_PUBLICATION_REVIEW.json"


def test_round050_review_receipt_is_fail_closed_and_traceable() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    subject = receipt["subject"]
    assert subject["frozen_sha"] == "ed34da627af3533ab2e1f860d73e7637c574f73d"
    assert subject["observed_origin_sha"] == subject["frozen_sha"]
    assert subject["branch_moved"] is False

    retained = {source["source_id"]: source for source in receipt["retained_sources"]}
    assert set(retained) == {
        "arxiv:2509.25236v3",
        "arxiv:2608.01679v2",
        "arxiv:2608.05235v1",
    }
    for source in retained.values():
        assert len(source["pdf_sha256"]) == 64
        assert source["mapping"]
        assert source["novelty_effect"]
        assert source["evidence_scope"]
        assert source["reported_results"]

    authority = retained["arxiv:2608.01679v2"]["reported_results"]
    assert authority["configurations_with_authority_upgrade"] == 48
    assert authority["configurations_total"] == 49
    assert authority["end_to_end_predicted_metadata"]["unauthorized_actions"] == 0

    trajectory = retained["arxiv:2608.05235v1"]["reported_results"]
    assert trajectory["methods_with_last_valid_round_below_earlier_best"] == 22
    assert trajectory["adaptation_methods_total"] == 30

    for route in receipt["route_receipts"]:
        path = ROOT / route["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == route["sha256"]

    review = receipt["review"]
    assert review["independent"] is False
    assert review["mutually_blind"] is False
    assert review["peer_review"] is False
    assert receipt["claim_state"]["accepted_or_published"] is False
    assert receipt["claim_state"]["absolute_complete"] is False
    assert "exact_ci_on_committed_subject" in review["lenses"][2]["blocking_open"]


def test_round050_has_two_flat_rounds_after_material_growth() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["growth_round"]["previous_saturation_reopened"] is True
    assert any(value > 0 for value in receipt["growth_round"]["growth"].values())

    rounds = receipt["post_assimilation_flat_rounds"]
    assert len(rounds) == 2
    assert all(all(value == 0 for value in round_["growth"].values()) for round_ in rounds)
    assert len({round_["basis_fingerprint"] for round_ in rounds}) == 1
