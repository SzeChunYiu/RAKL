"""Independent-human novelty residual after #255 demoted AI_OPERATOR closeout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RESIDUAL = ROOT / "research/paper5_independent_novelty_human_residual_v1"
PHASE0 = ROOT / "research/paper5_novelty_audit_v1"
SCHEMA = ROOT / "schemas/paper5-independent-novelty-blocked-human-freeze-v1.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_blocked_human_freeze_schema_and_invariants() -> None:
    freeze = _load(RESIDUAL / "BLOCKED_HUMAN_PACKET_FREEZE.json")
    Draft202012Validator(_load(SCHEMA)).validate(freeze)
    assert freeze["freeze_status"] == "BLOCKED_HUMAN"
    assert freeze["terminal_status"] == "CANNOT_OBTAIN_INDEPENDENT_EXTERNAL_HUMANS"
    assert freeze["parent_issue"] == 255
    assert freeze["successor_issue"] == 353
    assert freeze["humans_invented"] is False
    assert freeze["independent_external_human"] is False
    assert freeze["independent_review_claimed"] is False
    assert freeze["grants_scientific_authority"] is False
    assert freeze["demoted_track_non_authority"]["may_satisfy_this_issue"] is False
    assert all(v is None for v in freeze["human_roles_assigned"].values())


def test_phase0_substrate_hashes_match_disk() -> None:
    freeze = _load(RESIDUAL / "BLOCKED_HUMAN_PACKET_FREEZE.json")
    substrate = freeze["phase0_substrate"]
    assert _sha256(ROOT / substrate["audit_universe_manifest_path"]) == substrate[
        "audit_universe_manifest_sha256"
    ]
    assert _sha256(ROOT / substrate["zero_external_novelty_labels_path"]) == substrate[
        "zero_external_novelty_labels_sha256"
    ]
    assert _sha256(ROOT / substrate["blinded_audit_candidate_frame_path"]) == substrate[
        "blinded_audit_candidate_frame_sha256"
    ]


def test_track_separation_forbids_demoted_as_independent() -> None:
    separation = _load(RESIDUAL / "TRACK_SEPARATION.json")
    demoted = separation["tracks"]["ai_operator_demoted"]
    independent = separation["tracks"]["independent_human"]
    assert demoted["authority_class"] == "DEMOTED_AI_OPERATOR_NON_INDEPENDENT"
    assert demoted["may_mint_construct_validity"] is False
    assert demoted["independent_external_human"] is False
    assert independent["status"] == "BLOCKED_HUMAN"
    assert independent["labels_present"] is False
    honesty = _load(PHASE0 / "ai_operator_demoted_v1/HONESTY_STAMP_AI_OPERATOR.json")
    assert honesty["independent_external_human"] is False
    assert honesty["constitution_grade_independent_peer_review"] is False


def test_chronology_orders_phase0_before_demoted_before_residual() -> None:
    chronology = _load(RESIDUAL / "CHRONOLOGY.json")
    ids = [event["event_id"] for event in chronology["events"]]
    assert ids.index("PHASE0_AUDIT_UNIVERSE_FROZEN") < ids.index(
        "AI_OPERATOR_DEMOTED_TRACK_COMPLETE"
    )
    assert ids.index("AI_OPERATOR_DEMOTED_TRACK_COMPLETE") < ids.index(
        "INDEPENDENT_HUMAN_RESIDUAL_BLOCKED_HUMAN_FROZEN"
    )
    assert chronology["grants_scientific_authority"] is False


def test_independent_packet_manifest_blocks_demoted_reuse() -> None:
    manifest = _load(RESIDUAL / "INDEPENDENT_HUMAN_PACKET_MANIFEST.json")
    assert manifest["release_status"] == "BLOCKED_HUMAN_UNRELEASED"
    assert manifest["humans_invented"] is False
    assert "ai_operator_demoted_v1/FINAL_AUDIT_RECEIPT.json" in "\n".join(
        manifest["must_not_reuse_as_independent"]
    )
    for name in (
        "SAMPLE_PLAN.json",
        "PRECISION_POWER_RECEIPT.json",
        "PUBLIC_AUDIT_PACKET.json",
    ):
        assert manifest["artifact_status"][name] == "BLOCKED_HUMAN"


def test_issue_353_terminal_receipt_honest_close() -> None:
    receipt = _load(RESIDUAL / "ISSUE_353_TERMINAL_RECEIPT.json")
    freeze = _load(RESIDUAL / "BLOCKED_HUMAN_PACKET_FREEZE.json")
    assert receipt["issue"] == 353
    assert receipt["parent_issue"] == 255
    assert receipt["terminal_status"] == "CANNOT_OBTAIN_INDEPENDENT_EXTERNAL_HUMANS"
    assert receipt["acceptance_path"] == 2
    assert receipt["humans_invented"] is False
    assert receipt["independent_external_human"] is False
    assert receipt["grants_scientific_authority"] is False
    assert receipt["promotional_lift_claim_allowed"] is False
    assert receipt["capable_model_available"] == "NO_REFUTED"
    assert receipt["acceptance_assessment"]["demoted_track_treated_as_independent"] is False
    assert (
        receipt["evidence_pointers"]["blocked_human_freeze_sha256"]
        == _sha256(RESIDUAL / "BLOCKED_HUMAN_PACKET_FREEZE.json")
    )
    assert freeze["successor_issue"] == 353
    assert freeze["terminal_status"] == receipt["terminal_status"]
