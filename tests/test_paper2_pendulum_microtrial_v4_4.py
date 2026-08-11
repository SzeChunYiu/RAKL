"""V4.4 leak-free packet: positive-control sensitivity + DifferenceWitness gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rakl.degeneracy_probe import ArmPair, DegeneracyStatus, probe_arm_answer_leak
from rakl.paper2_pendulum_microtrial_v4_4 import validate_v4_4_candidate_packet
from rakl.paper2_v4_4_positive_control import (
    POSITIVE_CONTROL_ID,
    evaluate_positive_control_sensitivity,
)

ROOT = Path(__file__).resolve().parents[1]
V44 = ROOT / "research/paper2_microtrial_v4_4"


def _gold() -> dict[str, frozenset[str]]:
    return {
        "misaligned_source_ids": frozenset({"S4", "S5"}),
        "required_refuted_source_ids": frozenset({"S6"}),
    }


def test_v4_4_positive_control_passes_and_grants_no_authority() -> None:
    report = evaluate_positive_control_sensitivity(
        rakl_prompt=(V44 / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
        direct_prompt=(V44 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
        surface="paper2_microtrial_v4_4",
    )
    assert report.passed
    assert report.positive_control_id == POSITIVE_CONTROL_ID
    assert report.planted_exact_pass_delta > 0
    assert report.planted_misalignment_recall_delta > 0
    assert report.planted_refutation_recall_delta > 0
    assert report.grants_scientific_authority is False
    assert report.grants_capability_floor_clearance is False
    receipt = json.loads(
        (V44 / "POSITIVE_CONTROL_SENSITIVITY_RECEIPT.json").read_text(encoding="utf-8")
    )
    assert receipt["passed"] is True
    assert receipt["grants_capability_floor_clearance"] is False


def test_v4_4_arm_pair_is_clean() -> None:
    report = probe_arm_answer_leak(
        ArmPair(
            "paper2_microtrial_v4_4",
            (V44 / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
            (V44 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
            _gold(),
        )
    )
    assert report.status is DegeneracyStatus.CLEAN


def test_v4_4_candidate_packet_validates() -> None:
    packet = json.loads((V44 / "EXECUTION_PACKET_V4_4_20260811.json").read_text())
    validate_v4_4_candidate_packet(packet, base_dir=ROOT)
    assert packet["threshold_or_score_change_permitted"] is False
    assert packet["rakl_vs_direct_claim_from_leaked_parents_permitted"] is False


def test_v4_4_difference_witness_is_leak_repair_only() -> None:
    witness = json.loads((V44 / "DIFFERENCE_WITNESS_V4_4.json").read_text())
    changed = set(witness["changed_structural_coordinates"])
    assert changed == {"rakl_context_prompt_type_b_answer_key_leak_repair"}
    assert "exact_conceptual_pass_threshold" not in changed


def test_v4_4_batch_bindings_match_bytes() -> None:
    batch = json.loads((V44 / "BATCH_CONTRACT_V4_4.json").read_text())
    assert batch["threshold_or_score_change_permitted"] is False
    for binding in batch["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]
