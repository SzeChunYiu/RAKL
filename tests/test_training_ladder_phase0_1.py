"""Hostile and structural tests for #461 training-ladder Phase 0/1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from rakl.training_ladder import (
    STRUCTURAL_FAMILIES,
    ControlKind,
    FamilyId,
    GoldLabel,
    build_exposure_curve_harness,
    build_hostile_control_suite,
    build_known_structure_catalog,
    build_protocol_freeze_packet,
    build_protocol_freeze_receipt,
    generate_family_cases,
    validate_protocol_freeze,
    verify_case,
)
from rakl.training_ladder.exposure import ExposureProbeKind, REGISTERED_EXPOSURE_COUNTS
from rakl.training_ladder.types import StructuralCoordinate

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research" / "training_time_rakl_phase0_1"
FREEZE_SCRIPT = ROOT / "experiments" / "training_ladder" / "freeze_protocol.py"


def test_at_least_three_heterogeneous_families() -> None:
    assert len(STRUCTURAL_FAMILIES) >= 3
    assert FamilyId.SEQUENCE_COMPOSITION in STRUCTURAL_FAMILIES
    assert FamilyId.BALANCE_CONSERVATION in STRUCTURAL_FAMILIES
    assert FamilyId.STATE_REACHABILITY in STRUCTURAL_FAMILIES


def test_gold_comes_from_verifier_not_perturbation_identity() -> None:
    for family in STRUCTURAL_FAMILIES:
        cases = [verify_case(c) for c in generate_family_cases(family, seed_offset=0)]
        assert len(cases) >= 2
        labels = {case.gold_label for case in cases}
        assert GoldLabel.VALID in labels
        assert GoldLabel.INVALID in labels
        for case in cases:
            assert case.gold_label is not None
            assert case.case_id.rsplit("-", 1)[-1] not in case.gold_label.value


def test_surface_text_does_not_leak_family_or_validity() -> None:
    cases = [verify_case(c) for c in build_known_structure_catalog(seed_offsets=(0,))]
    for case in cases:
        lowered = case.surface_text.lower()
        assert case.family_id.value not in lowered
        assert "valid" not in lowered
        assert "invalid" not in lowered


def test_template_leak_probe_same_template_different_gold() -> None:
    suite = build_hostile_control_suite(seed_offset=0)
    assert suite.template_leak_probes
    by_template: dict[str, set[GoldLabel]] = {}
    for case in suite.template_leak_probes:
        assert case.control_kind is ControlKind.TEMPLATE_LEAK_PROBE
        by_template.setdefault(case.surface_template_id, set()).add(case.gold_label)
    assert any(len(labels) > 1 for labels in by_template.values())


def test_coordinate_ablated_twins_differ_from_anchor_structure() -> None:
    suite = build_hostile_control_suite(seed_offset=0)
    assert suite.coordinate_ablated_twins
    for twin in suite.coordinate_ablated_twins:
        assert twin.control_kind is ControlKind.COORDINATE_ABLATED_TWIN
        assert twin.twin_of_case_id is not None
        assert "-abl-" in twin.structure.structure_id


def test_semantic_near_decoys_are_structure_wrong() -> None:
    suite = build_hostile_control_suite(seed_offset=0)
    assert suite.semantic_near_decoys
    for decoy in suite.semantic_near_decoys:
        assert decoy.control_kind is ControlKind.SEMANTIC_NEAR_DECOY
        assert decoy.gold_label is GoldLabel.INVALID


def test_coordinates_independently_registered() -> None:
    case = verify_case(generate_family_cases(FamilyId.SEQUENCE_COMPOSITION, seed_offset=1)[0])
    keys = {axis for axis, _ in case.coordinate_values}
    assert StructuralCoordinate.PRINCIPLE in keys
    assert StructuralCoordinate.COMPOSITION in keys
    assert StructuralCoordinate.BOUNDARY in keys
    assert StructuralCoordinate.REPRESENTATION in keys
    assert StructuralCoordinate.DOMAIN_SHELL in keys
    assert StructuralCoordinate.SURFACE_DETAIL in keys


def test_exposure_curve_harness_scaffold_is_pre_outcome() -> None:
    cases = [verify_case(c) for c in build_known_structure_catalog(seed_offsets=(0,))]
    harness = build_exposure_curve_harness(
        harness_id="test-harness",
        case_ids_by_probe={
            ExposureProbeKind.SAME_STRUCTURE: [cases[0].case_id],
            ExposureProbeKind.HOSTILE_NEAR_MISS: [cases[1].case_id],
        },
    )
    assert harness.frozen_before_outcomes is True
    assert harness.grants_efficacy_claim is False
    assert harness.learner_outcomes_accessed is False
    assert harness.exposure_counts == REGISTERED_EXPOSURE_COUNTS
    assert len(harness.schedule) == len(REGISTERED_EXPOSURE_COUNTS) * 2


def test_protocol_freeze_packet_pre_outcome() -> None:
    packet = build_protocol_freeze_packet(repo_sha="a" * 40, rakl_version="3.0.0")
    schema = json.loads((ROOT / "schemas" / "training-ladder-protocol-freeze-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(packet)
    assert packet["issue"] == 461
    assert packet["parent_issue"] == 455
    assert packet["frozen_before_outcomes"] is True
    assert packet["evaluated_results_accessed"] is False
    assert packet["learner_outcomes_accessed"] is False
    assert packet["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert packet["runs"] == []
    assert len(packet["structural_families"]) >= 3
    assert "adaptive_training_effective" in packet["forbidden_claims"]
    receipt = build_protocol_freeze_receipt(packet)
    assert receipt["verdict"] == "PROTOCOL_FREEZE_PASS"
    assert receipt["grants_scientific_authority"] is False


def test_committed_protocol_freeze_passes_validation() -> None:
    validation = validate_protocol_freeze(PACKET_DIR)
    assert validation.verdict == "PROTOCOL_FREEZE_PASS", validation.reasons


def test_freeze_script_check_only() -> None:
    proc = subprocess.run(
        [sys.executable, str(FREEZE_SCRIPT), "--check-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "PROTOCOL_FREEZE_PASS"


def test_freeze_refuses_outcome_artifacts(tmp_path: Path) -> None:
    import shutil

    staging = tmp_path / "packet"
    shutil.copytree(PACKET_DIR, staging)
    (staging / "results.jsonl").write_text("{}\n", encoding="utf-8")
    validation = validate_protocol_freeze(staging)
    assert validation.verdict == "PROTOCOL_FREEZE_FAIL"
    assert "forbidden_outcome_artifact:results.jsonl" in validation.reasons
