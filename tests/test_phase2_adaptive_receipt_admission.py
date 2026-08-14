from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from rakl.phase2_adaptive_receipt_admission import (
    ARMS,
    EXPOSURES,
    admit_phase2_adaptive_result_bundle,
    recompute_phase2_analysis,
)
from rakl.training_policy_authority import (
    AdaptivePolicyAuthorization,
    TrainingPolicyMode,
    choose_active_training_policy,
    choose_active_training_policy_from_phase2_bundle,
)


ROOT = Path(__file__).resolve().parents[1]


def _sha(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def _resource_block(arm: str) -> dict[str, float | int]:
    selection_examples = 480 if arm in {"C_STRONGEST_MODEL_AWARE_PARENT", "E_ADAPTIVE_RAKL_STRUCTURAL"} else 0
    selection_calls = 960 if arm == "E_ADAPTIVE_RAKL_STRUCTURAL" else (480 if arm == "C_STRONGEST_MODEL_AWARE_PARENT" else 0)
    selection_seconds = 2.0 if selection_examples else 0.0
    cpu_seconds = 0.5 if arm == "B_SEMANTIC_DIVERSITY" else 0.0
    training_seconds = 10.0
    assurance_seconds = 1.0
    return {
        "model_loads": 6 if arm in {"C_STRONGEST_MODEL_AWARE_PARENT", "E_ADAPTIVE_RAKL_STRUCTURAL"} else 1,
        "training_example_presentations": 576,
        "training_token_presentations": 12000,
        "selection_examples_scored": selection_examples,
        "selection_forward_calls": selection_calls,
        "assurance_examples_scored": 384,
        "assurance_forward_calls": 768,
        "training_wall_seconds": training_seconds,
        "selection_wall_seconds": selection_seconds,
        "assurance_wall_seconds": assurance_seconds,
        "cpu_selection_seconds": cpu_seconds,
        "total_accounted_seconds": training_seconds + selection_seconds + assurance_seconds + cpu_seconds,
        "gpu_seconds": training_seconds + selection_seconds + assurance_seconds,
        "peak_gpu_memory_bytes": 1_000_000_000,
    }


def _prediction(gold: str, correct: bool) -> str:
    if correct:
        return gold
    return "INVALID" if gold == "VALID" else "VALID"


def _positive_bundle() -> tuple[dict, dict, dict[str, list[dict]]]:
    train = {exposure: [f"train::{exposure}::{i}" for i in range(96)] for exposure in EXPOSURES}
    selection = {exposure: [f"select::{exposure}::{i}" for i in range(16)] for exposure in EXPOSURES}
    assurance_ids = {exposure: [f"assure::{exposure}::{i}" for i in range(64)] for exposure in EXPOSURES}
    manifest_payload = {"train": train, "selection": selection, "assurance": assurance_ids}
    manifest_hash = _sha(manifest_payload)
    manifest = {"sha256": manifest_hash, **manifest_payload}

    correct_cutoff = {
        "A_UNIFORM_RANDOM": 28,
        "B_SEMANTIC_DIVERSITY": 30,
        "C_STRONGEST_MODEL_AWARE_PARENT": 32,
        "D_STATIC_RAKL_STRUCTURAL": 32,
        "E_ADAPTIVE_RAKL_STRUCTURAL": 48,
    }
    assurance: dict[str, list[dict]] = {}
    for arm in ARMS:
        rows: list[dict] = []
        for exposure in EXPOSURES:
            for index, case_id in enumerate(assurance_ids[exposure]):
                gold = "VALID" if index % 2 == 0 else "INVALID"
                correct = index < correct_cutoff[arm]
                pred = _prediction(gold, correct)
                rows.append(
                    {
                        "case_id": case_id,
                        "exposure": exposure,
                        "gold": gold,
                        "prediction": pred,
                        "correct": int(correct),
                    }
                )
        assurance[arm] = rows

    analysis = recompute_phase2_analysis(assurance)
    assert analysis["terminal"] == "ADAPTIVE_RESIDUAL_SUPPORTED"
    receipt = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "protocol": "PROTOCOL_V3.json",
        "inference_plan": "INFERENCE_PLAN.json",
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "data_manifest_hash": manifest_hash,
        "arms": {arm: {"resources": _resource_block(arm)} for arm in ARMS},
        "analysis": analysis,
        "terminal": "ADAPTIVE_RESIDUAL_SUPPORTED",
        "total_wall_seconds": 100.0,
        "grants_scientific_authority": False,
        "paper4_standalone_authorized": True,
    }
    return receipt, manifest, assurance


@pytest.fixture(scope="module")
def positive_bundle():
    return _positive_bundle()


def test_strongest_parent_counterexample_caller_summary_can_self_assert_positive():
    fabricated = AdaptivePolicyAuthorization(
        receipt_id="fabricated",
        terminal="ADAPTIVE_RESIDUAL_SUPPORTED",
        evaluated_subject_hash="not-a-verified-subject",
        evidence_ids=("caller-says-fresh", "caller-says-cost"),
        fresh_assurance=True,
        strongest_parent_residual=True,
        hard_harms_pass=True,
        full_overhead_accounted=True,
    )
    assert choose_active_training_policy(fabricated).mode is TrainingPolicyMode.ADAPTIVE_STRUCTURAL
    assert choose_active_training_policy_from_phase2_bundle().mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_terminal_only_fabrication_cannot_activate_without_raw_bundle():
    receipt = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "terminal": "ADAPTIVE_RESIDUAL_SUPPORTED",
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "protocol": "PROTOCOL_V3.json",
        "inference_plan": "INFERENCE_PLAN.json",
        "grants_scientific_authority": False,
    }
    decision = choose_active_training_policy_from_phase2_bundle(final_receipt=receipt)
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_stale_model_revision_fails_closed(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    receipt["model_revision"] = "stale"
    decision = choose_active_training_policy_from_phase2_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_changed_protocol_or_inference_identifier_fails_closed(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    receipt["inference_plan"] = "POSTHOC_PLAN.json"
    decision = choose_active_training_policy_from_phase2_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_manifest_overlap_fails_fresh_assurance_gate(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    manifest["selection"]["SAME_STRUCTURE"][0] = manifest["train"]["SAME_STRUCTURE"][0]
    payload = {key: manifest[key] for key in ("train", "selection", "assurance")}
    manifest["sha256"] = _sha(payload)
    receipt["data_manifest_hash"] = manifest["sha256"]
    admission = admit_phase2_adaptive_result_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert admission.admitted is False
    assert "phase2_manifest_partition_overlap" in admission.reasons


def test_duplicate_or_unpaired_assurance_rows_fail_closed(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    rows = assurance["E_ADAPTIVE_RAKL_STRUCTURAL"]
    rows[1] = copy.deepcopy(rows[0])
    admission = admit_phase2_adaptive_result_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert admission.admitted is False
    assert any("duplicate" in reason for reason in admission.reasons)


def test_forged_receipt_analysis_is_rejected_by_independent_recomputation(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    receipt["analysis"]["contrasts"]["E-D"]["mean"] = 0.99
    admission = admit_phase2_adaptive_result_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert admission.admitted is False
    assert "phase2_receipt_analysis_does_not_match_independent_recomputation" in admission.reasons


def test_missing_negative_or_nonfinite_resource_accounting_fails_closed(positive_bundle):
    for mutation in ("missing", "negative", "nan"):
        receipt, manifest, assurance = copy.deepcopy(positive_bundle)
        resources = receipt["arms"]["E_ADAPTIVE_RAKL_STRUCTURAL"]["resources"]
        if mutation == "missing":
            resources.pop("selection_examples_scored")
        elif mutation == "negative":
            resources["training_wall_seconds"] = -1.0
        else:
            resources["gpu_seconds"] = float("nan")
        decision = choose_active_training_policy_from_phase2_bundle(
            final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
        )
        assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_high_cost_positive_does_not_gain_active_default_authority_in_v1(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    receipt["terminal"] = "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST"
    receipt["analysis"]["terminal"] = "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST"
    decision = choose_active_training_policy_from_phase2_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert decision.mode is TrainingPolicyMode.STATIC_STRUCTURAL


def test_fully_consistent_synthetic_positive_bundle_exercises_contract_only(positive_bundle):
    receipt, manifest, assurance = copy.deepcopy(positive_bundle)
    admission = admit_phase2_adaptive_result_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert admission.admitted is True
    assert admission.status == "PASS"
    assert admission.receipt_id and admission.receipt_id.startswith("sha256:")
    assert admission.evaluated_subject_hash and admission.evaluated_subject_hash.startswith("sha256:")
    assert len(admission.evidence_ids) == 6
    assert admission.grants_scientific_authority is False
    decision = choose_active_training_policy_from_phase2_bundle(
        final_receipt=receipt, data_manifest=manifest, assurance_by_arm=assurance
    )
    assert decision.mode is TrainingPolicyMode.ADAPTIVE_STRUCTURAL
    assert decision.authorization_receipt_id == admission.receipt_id
    assert decision.grants_scientific_authority is False


def test_p4_development_negative_blob_is_preserved_unchanged():
    path = ROOT / "research" / "orion_p1_p4_closure_v2" / "P4_ADAPTIVE_DEVELOPMENT_NEGATIVE.json"
    assert _git_blob_sha(path.read_bytes()) == "fc5d2363de1a6f1303ca9a80795fc291fe57a5a6"
