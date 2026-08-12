"""Logic tests for the Paper IV Phase-1 (#461) exposure executor.

These tests never load a real model, download weights, or import torch. Heavy
deep-learning dependencies are imported lazily inside the executor's training
function, so importing the module here is cheap. Everything below exercises the
honesty-critical logic: the packet-hash gate, no-label-leakage rendering,
train/probe disjointness, the outcome-row schema, and the terminal classifier on
hand-built synthetic outcome tables.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR_DIR = ROOT / "experiments" / "training_ladder"
if str(EXECUTOR_DIR) not in sys.path:
    sys.path.insert(0, str(EXECUTOR_DIR))

import exposure_executor as ee  # noqa: E402
from orion.training_ladder import (  # noqa: E402
    ExposureProbeKind,
    FamilyId,
    GoldLabel,
    generate_family_cases,
    verify_case,
)

REAL_PACKET_DIR = ROOT / "research" / "paper4_training_ladder_461"


# --------------------------------------------------------------------------- #
# Packet-hash validation gate
# --------------------------------------------------------------------------- #


def test_gate_accepts_frozen_packet():
    packet, subject_hash = ee.load_frozen_packet(REAL_PACKET_DIR)
    assert subject_hash == packet["protocol_subject_hash"]
    assert packet["grants_scientific_authority"] is False


def test_gate_refuses_missing_packet(tmp_path):
    with pytest.raises(ee.ProtocolFreezeError):
        ee.load_frozen_packet(tmp_path)


def test_gate_refuses_tampered_packet(tmp_path):
    shutil.copy(REAL_PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json", tmp_path / "PROTOCOL_FREEZE_PACKET.json")
    packet = json.loads((tmp_path / "PROTOCOL_FREEZE_PACKET.json").read_text())
    # Tamper a hashed subject field: the recomputed protocol_subject_hash no
    # longer matches, so the gate must refuse.
    packet["repo_sha"] = "0000000000000000000000000000000000000000"
    (tmp_path / "PROTOCOL_FREEZE_PACKET.json").write_text(json.dumps(packet, indent=2, sort_keys=True))
    with pytest.raises(ee.ProtocolFreezeError):
        ee.load_frozen_packet(tmp_path)


# --------------------------------------------------------------------------- #
# render_problem: no label leakage, reachability edges shown
# --------------------------------------------------------------------------- #


def _pair(family: FamilyId, seed_offset: int = 0):
    cases = [verify_case(c) for c in generate_family_cases(family, seed_offset=seed_offset)]
    valid = next(c for c in cases if c.gold_label == GoldLabel.VALID)
    invalid = next(c for c in cases if c.gold_label == GoldLabel.INVALID)
    return valid, invalid


def test_render_no_label_leakage():
    valid, invalid = _pair(FamilyId.SEQUENCE_COMPOSITION)
    p_valid = ee.render_problem(valid)
    p_invalid = ee.render_problem(invalid)

    for prompt, case in ((p_valid, valid), (p_invalid, invalid)):
        # case_id encodes the a/b (valid/invalid) choice -> must never appear.
        assert case.case_id not in prompt
        # gold / control kind / twin metadata must never appear.
        assert "NORMAL" not in prompt
        assert "gold" not in prompt.lower()
        assert case.gold_label is not None
        # The answer is never pre-filled: the prompt ends at the empty Answer slot.
        assert prompt.rstrip().endswith("Answer:")

    # The two siblings differ only in payload facts, not in a label marker.
    assert p_valid != p_invalid


def test_render_reachability_shows_edges():
    valid, _ = _pair(FamilyId.STATE_REACHABILITY)
    payload = dict(valid.executable_payload)
    edges = tuple(payload["edges"])
    prompt = ee.render_problem(valid)
    # Every payload edge must be present in the full render.
    for src, dst in edges:
        assert f"{src}->{dst}" in prompt
    # Sanity: surface_text alone omits the edges (that is why we render payload).
    assert "->" not in valid.surface_text


def test_render_ablation_hides_edges():
    valid, _ = _pair(FamilyId.STATE_REACHABILITY)
    ablated = ee.render_problem(valid, ablate=True)
    # The decisive coordinate (edges) is removed in the ablated twin render.
    assert "->" not in ablated


def test_render_target_is_verifier_gold():
    valid, invalid = _pair(FamilyId.BALANCE_CONSERVATION)
    assert ee.render_target(valid) == GoldLabel.VALID.value
    assert ee.render_target(invalid) == GoldLabel.INVALID.value


# --------------------------------------------------------------------------- #
# Train / probe disjointness
# --------------------------------------------------------------------------- #


def test_offset_bands_are_disjoint():
    bands = ee.build_offset_bands(max_exposure=64)
    all_bands = [
        bands.train,
        bands.same_structure,
        bands.new_composition,
        bands.new_boundary,
        bands.new_representation,
        bands.new_domain,
    ]
    seen: set[int] = set()
    for band in all_bands:
        assert not (seen & set(band)), "offset bands overlap"
        seen |= set(band)
    # Train band must be large enough to supply the full ladder (2 cases/offset).
    assert len(bands.train) * 2 >= 64


def test_train_and_probe_sets_disjoint():
    family = FamilyId.SEQUENCE_COMPOSITION
    bands = ee.build_offset_bands(max_exposure=16)
    pool = ee.build_training_pool(family, bands, seed=ee.FROZEN_SEED)
    probes = ee.build_probe_sets(family, bands, hostile_seed_offset=bands.new_domain[0])

    # Should not raise.
    ee.assert_disjoint(pool, probes)

    train_ids = {ex.case_id for ex in pool}
    for kind, examples in probes.items():
        assert examples, f"probe set {kind.value} is empty"
        probe_ids = {ex.case_id for ex in examples}
        assert not (train_ids & probe_ids), f"leakage in {kind.value}"

    # NEW_DOMAIN must draw from the *other* families only (genuine transfer).
    domain_families = {ex.family for ex in probes[ExposureProbeKind.NEW_DOMAIN]}
    assert family.value not in domain_families
    assert domain_families


def test_training_pool_is_deterministic():
    family = FamilyId.STATE_REACHABILITY
    bands = ee.build_offset_bands(max_exposure=8)
    a = ee.build_training_pool(family, bands, seed=ee.FROZEN_SEED)
    b = ee.build_training_pool(family, bands, seed=ee.FROZEN_SEED)
    assert [ex.case_id for ex in a] == [ex.case_id for ex in b]


# --------------------------------------------------------------------------- #
# Outcome-row schema
# --------------------------------------------------------------------------- #


def _row(**overrides):
    base = dict(
        family=FamilyId.SEQUENCE_COMPOSITION.value,
        exposure_count=4,
        probe_kind=ExposureProbeKind.SAME_STRUCTURE,
        accuracy=0.75,
        n=6,
        checkpoint_hash="deadbeef",
        marginal_gain=0.1,
        prev_exposure_count=2,
        protocol_subject_hash="hash123",
        smoke=True,
    )
    base.update(overrides)
    return ee.make_outcome_row(**base)


def test_outcome_row_schema_shape():
    row = _row()
    assert set(row) == set(ee.OUTCOME_FIELDS)
    assert row["coordinate"] == ee.PROBE_TO_COORDINATE[ExposureProbeKind.SAME_STRUCTURE].value
    ee.validate_outcome_row(row)  # must not raise


def test_outcome_row_rejects_bad_accuracy():
    row = _row(accuracy=1.5)
    with pytest.raises(ValueError):
        ee.validate_outcome_row(row)


def test_outcome_row_rejects_extra_field():
    row = _row()
    row["surprise"] = 1
    with pytest.raises(ValueError):
        ee.validate_outcome_row(row)


def test_write_outcomes_roundtrip(tmp_path):
    rows = [_row(), _row(probe_kind=ExposureProbeKind.NEW_DOMAIN, accuracy=0.5)]
    out = tmp_path / "exposure_outcomes.jsonl"
    ee.write_outcomes(rows, out)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert set(parsed) == set(ee.OUTCOME_FIELDS)


# --------------------------------------------------------------------------- #
# Terminal classifier (synthetic outcome tables)
# --------------------------------------------------------------------------- #


def _acc_rows(traj_by_kind, family="fam"):
    """Build synthetic accuracy rows: {probe_kind: {exposure: accuracy}}."""
    rows = []
    for kind, by_exp in traj_by_kind.items():
        for exp, acc in by_exp.items():
            rows.append(
                {
                    "family": family,
                    "exposure_count": exp,
                    "probe_kind": kind.value,
                    "accuracy": acc,
                    "n": 6,
                }
            )
    return rows


ALLOWED_TERMINALS = {
    "MECHANISM_SIGNAL_PRESENT",
    "REPETITION_REMAINS_VALUABLE",
    "NO_STATE_DEPENDENT_RESIDUAL",
    "INSTRUMENT_OR_GENERATOR_DEFECT",
    "MODEL_FLOOR",
}


def _assert_clean(result):
    assert result["terminal"] in ALLOWED_TERMINALS
    assert result["grants_scientific_authority"] is False
    assert result["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert result["forbidden_claims_asserted"] == []
    blob = json.dumps(result)
    for claim in ee.FORBIDDEN_CLAIMS:
        assert claim not in blob


def test_terminal_model_floor():
    rows = _acc_rows({ExposureProbeKind.SAME_STRUCTURE: {1: 0.50, 2: 0.52, 4: 0.55}})
    result = ee.classify_phase1_terminal(rows)
    assert result["terminal"] == "MODEL_FLOOR"
    _assert_clean(result)


def test_terminal_mechanism_signal_present():
    rows = _acc_rows(
        {
            # Principle mastered by exposure 2, then flat (same-structure repetition stops paying).
            ExposureProbeKind.SAME_STRUCTURE: {1: 0.70, 2: 0.90, 4: 0.90, 8: 0.90},
            # A different coordinate keeps improving after that point (still valuable).
            ExposureProbeKind.NEW_DOMAIN: {1: 0.50, 2: 0.60, 4: 0.75, 8: 0.90},
        }
    )
    result = ee.classify_phase1_terminal(rows)
    assert result["terminal"] == "MECHANISM_SIGNAL_PRESENT"
    _assert_clean(result)


def test_terminal_repetition_remains_valuable():
    rows = _acc_rows(
        {
            # Never reaches mastery but keeps gaining -> repetition still pays.
            ExposureProbeKind.SAME_STRUCTURE: {1: 0.60, 2: 0.70, 4: 0.80, 8: 0.88},
            ExposureProbeKind.NEW_DOMAIN: {1: 0.55, 2: 0.58, 4: 0.60, 8: 0.62},
        }
    )
    result = ee.classify_phase1_terminal(rows)
    assert result["terminal"] == "REPETITION_REMAINS_VALUABLE"
    _assert_clean(result)


def test_terminal_no_state_dependent_residual():
    rows = _acc_rows(
        {
            # Principle mastered early, flat late; other coords also flat late.
            ExposureProbeKind.SAME_STRUCTURE: {1: 0.70, 2: 0.90, 4: 0.90, 8: 0.90},
            ExposureProbeKind.NEW_DOMAIN: {1: 0.70, 2: 0.72, 4: 0.72, 8: 0.72},
            ExposureProbeKind.NEW_COMPOSITION: {1: 0.71, 2: 0.72, 4: 0.72, 8: 0.72},
        }
    )
    result = ee.classify_phase1_terminal(rows)
    assert result["terminal"] == "NO_STATE_DEPENDENT_RESIDUAL"
    _assert_clean(result)


def test_terminal_instrument_or_generator_defect():
    rows = _acc_rows(
        {
            ExposureProbeKind.SAME_STRUCTURE: {1: 0.70, 2: 0.90, 4: 0.90, 8: 0.90},
            ExposureProbeKind.NEW_DOMAIN: {1: 0.50, 2: 0.60, 4: 0.75, 8: 0.90},
        }
    )
    # Coordinate-ablated twin classifier matches the full classifier -> the probe
    # carries no structural signal -> defect takes precedence over any signal.
    ablation_rows = [
        {"family": "fam", "exposure_count": 8, "accuracy": 0.89, "n": 6},
    ]
    result = ee.classify_phase1_terminal(rows, ablation_rows=ablation_rows)
    assert result["terminal"] == "INSTRUMENT_OR_GENERATOR_DEFECT"
    _assert_clean(result)


# --------------------------------------------------------------------------- #
# Manifest never asserts forbidden claims
# --------------------------------------------------------------------------- #


def test_manifest_never_asserts_forbidden_claims():
    manifest = ee.build_run_manifest(
        model_id="Qwen/Qwen2.5-0.5B-Instruct",
        protocol_subject_hash="hash123",
        seed=ee.FROZEN_SEED,
        families=[FamilyId.SEQUENCE_COMPOSITION.value],
        exposure_counts=[1, 2, 4],
        smoke=True,
        started_at="2026-08-12T00:00:00Z",
        finished_at="2026-08-12T00:01:00Z",
        terminal={"terminal": "MODEL_FLOOR"},
    )
    assert manifest["grants_scientific_authority"] is False
    assert manifest["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert manifest["forbidden_claims_asserted"] == []
    blob = json.dumps(manifest)
    for claim in ee.FORBIDDEN_CLAIMS:
        assert claim not in blob
