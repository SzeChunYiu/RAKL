#!/usr/bin/env python3
"""Harvest a completed frozen Paper-IV Phase-2 execution.

This is an execution/provenance bridge.  It does not change the frozen Phase-2
scientific analysis.  Positive active-policy eligibility is delegated to the
canonical raw-bundle admission path; negative/resource terminals are preserved
without being reinterpreted as scheduler failures.  Standalone Paper-IV
publication is never authorized here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from experiments.training_ladder.validate_phase2_v1_terminal import validate_terminal_pair
from rakl.phase2_adaptive_receipt_admission import (
    ARMS,
    _analysis_matches,
    _resources_complete,
    _validate_assurance,
    _validate_manifest,
    admit_phase2_adaptive_result_bundle,
    recompute_phase2_analysis,
)
from rakl.training_policy_authority import (
    TrainingPolicyMode,
    choose_active_training_policy_from_phase2_bundle,
)


FULL_TERMINALS = {
    "ADAPTIVE_RESIDUAL_SUPPORTED",
    "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST",
    "PARENT_MATCHES_OR_BEATS",
    "STATIC_EQUALS_ADAPTIVE",
    "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
    "UNDERPOWERED",
}
COMPUTE_BOUND_PATHS = {
    "research/paper4_phase2_v1/PROTOCOL_V3.json",
    "research/paper4_phase2_v1/INFERENCE_PLAN.json",
    "experiments/training_ladder/generator_v2.py",
    "experiments/training_ladder/phase2_adaptive_v1.py",
    "src/rakl/phase2_adaptive_receipt_admission.py",
    "src/rakl/training_policy_authority.py",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_assurance(outdir: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for arm in ARMS:
        path = outdir / f"ASSURANCE_{arm}.jsonl"
        if not path.is_file():
            raise ValueError(f"missing_assurance_file:{arm}")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        out[arm] = rows
    return out


def _cost_ratio(final_receipt: Mapping[str, object]) -> float:
    arms = final_receipt["arms"]
    e = float(arms["E_ADAPTIVE_RAKL_STRUCTURAL"]["resources"]["gpu_seconds"])
    d = float(arms["D_STATIC_RAKL_STRUCTURAL"]["resources"]["gpu_seconds"])
    if d <= 0 or e < 0:
        raise ValueError("invalid_E_D_gpu_seconds")
    return e / d


def harvest(
    *,
    outdir: Path,
    submission_path: Path,
    transport_path: Path,
    subject_sha: str,
    job_id: str,
    scheduler_state: str,
) -> dict:
    if scheduler_state != "COMPLETED":
        raise ValueError(f"scheduler_not_completed:{scheduler_state}")

    transport = _load(transport_path)
    submission = _load(submission_path)
    execution_subject_path = outdir / "EXECUTION_SUBJECT.json"
    final_path = outdir / "FINAL_RECEIPT.json"
    manifest_path = outdir / "DATA_MANIFEST.json"
    runner_code_path = outdir / "LOCAL_RUNNER_CODE.txt"
    for path in (execution_subject_path, final_path, manifest_path, runner_code_path):
        if not path.is_file():
            raise ValueError(f"completed_job_missing_artifact:{path.name}")

    execution = _load(execution_subject_path)
    final = _load(final_path)
    manifest = _load(manifest_path)
    runner_code = int(runner_code_path.read_text(encoding="utf-8").strip())

    if transport.get("schema_version") != "paper4-phase2-execution-transport-v1":
        raise ValueError("transport_protocol_schema_mismatch")
    if submission.get("schema_version") != "paper4-phase2-submission-receipt-v1":
        raise ValueError("submission_schema_mismatch")
    if submission.get("subject_sha") != subject_sha or str(submission.get("slurm_job_id")) != str(job_id):
        raise ValueError("submission_subject_or_job_mismatch")
    if execution.get("schema_version") != "paper4-phase2-compute-subject-v1":
        raise ValueError("compute_subject_schema_mismatch")
    if execution.get("subject_sha") != subject_sha or str(execution.get("slurm_job_id")) != str(job_id):
        raise ValueError("compute_subject_or_job_mismatch")
    scientific = transport["scientific_subject_unchanged"]
    if execution.get("model_id") != scientific["model_id"] or execution.get("model_revision") != scientific["model_revision"]:
        raise ValueError("compute_model_subject_mismatch")
    if execution.get("grants_scientific_authority") is not False:
        raise ValueError("compute_subject_authority_boundary_invalid")
    if execution.get("standalone_paper4_authorized") is not False:
        raise ValueError("compute_subject_standalone_boundary_invalid")

    frozen = transport["frozen_git_blobs"]
    compute_blobs = execution.get("git_blobs")
    if not isinstance(compute_blobs, Mapping):
        raise ValueError("compute_git_blob_binding_missing")
    if set(compute_blobs) != COMPUTE_BOUND_PATHS:
        raise ValueError("compute_git_blob_binding_incomplete_or_extra")
    for path in COMPUTE_BOUND_PATHS:
        observed = compute_blobs[path]
        expected = frozen.get(path)
        if expected is None or observed != expected:
            raise ValueError(f"compute_git_blob_mismatch:{path}")
    if submission.get("frozen_git_blobs") != frozen:
        raise ValueError("submission_frozen_blob_binding_mismatch")

    ok, terminal_detail = validate_terminal_pair(final, runner_code)
    if not ok:
        raise ValueError(terminal_detail)
    terminal = str(final["terminal"])
    if final.get("grants_scientific_authority") is not False:
        raise ValueError("raw_receipt_scientific_authority_boundary_invalid")

    training_policy_mode = TrainingPolicyMode.STATIC_STRUCTURAL.value
    canonical_admission_receipt_id = None
    recomputed_terminal = None
    e_over_d_gpu_ratio = None

    if runner_code == 0:
        if terminal not in FULL_TERMINALS:
            raise ValueError(f"full_runner_terminal_not_registered:{terminal}")
        manifest_ok, manifest_reason, manifest_hash = _validate_manifest(manifest)
        if not manifest_ok or manifest_hash is None:
            raise ValueError(manifest_reason or "manifest_invalid")
        if final.get("data_manifest_hash") != manifest_hash:
            raise ValueError("receipt_manifest_hash_mismatch")
        assurance = _load_assurance(outdir)
        assurance_ok, assurance_reason = _validate_assurance(assurance, manifest)
        if not assurance_ok:
            raise ValueError(assurance_reason or "assurance_invalid")
        if not _resources_complete(final):
            raise ValueError("resource_accounting_incomplete_or_invalid")
        recomputed = recompute_phase2_analysis(assurance)
        recomputed_terminal = str(recomputed["terminal"])

        if terminal == "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST":
            if recomputed_terminal != "ADAPTIVE_RESIDUAL_SUPPORTED":
                raise ValueError(f"high_cost_efficacy_recompute_mismatch:{recomputed_terminal}")
            analysis = dict(final.get("analysis") or {})
            analysis["terminal"] = "ADAPTIVE_RESIDUAL_SUPPORTED"
            if not _analysis_matches(analysis, recomputed):
                raise ValueError("high_cost_receipt_analysis_recompute_mismatch")
            e_over_d_gpu_ratio = _cost_ratio(final)
            if e_over_d_gpu_ratio <= 2.0:
                raise ValueError("high_cost_terminal_without_gt_2x_gpu_ratio")
        elif terminal == "ADAPTIVE_RESIDUAL_SUPPORTED":
            admission = admit_phase2_adaptive_result_bundle(
                final_receipt=final, data_manifest=manifest, assurance_by_arm=assurance
            )
            if not admission.admitted:
                raise ValueError("ordinary_positive_failed_canonical_admission:" + ";".join(admission.reasons))
            decision = choose_active_training_policy_from_phase2_bundle(
                final_receipt=final, data_manifest=manifest, assurance_by_arm=assurance
            )
            if decision.mode is not TrainingPolicyMode.ADAPTIVE_STRUCTURAL:
                raise ValueError("ordinary_positive_failed_training_policy_cost_gate")
            training_policy_mode = decision.mode.value
            canonical_admission_receipt_id = admission.receipt_id
            e_over_d_gpu_ratio = _cost_ratio(final)
            if e_over_d_gpu_ratio > 2.0:
                raise ValueError("ordinary_positive_exceeds_frozen_cost_boundary")
        else:
            if recomputed_terminal != terminal:
                raise ValueError(f"nonpositive_recomputed_terminal_mismatch:{terminal}:{recomputed_terminal}")
            if not _analysis_matches(final.get("analysis"), recomputed):
                raise ValueError("nonpositive_receipt_analysis_recompute_mismatch")
            decision = choose_active_training_policy_from_phase2_bundle(
                final_receipt=final, data_manifest=manifest, assurance_by_arm=assurance
            )
            if decision.mode is not TrainingPolicyMode.STATIC_STRUCTURAL:
                raise ValueError("nonpositive_bundle_must_retain_static_policy")
    else:
        # rc=1 is the complete early-harm terminal; rc=2 is RESOURCE_BLOCKED.
        # Neither has a full assurance bundle and neither can activate Adaptive.
        if terminal == "ADAPTIVE_RESIDUAL_SUPPORTED":
            raise ValueError("positive_terminal_cannot_use_reduced_bundle")

    raw_standalone_flag = final.get("paper4_standalone_authorized")
    receipt = {
        "schema_version": "paper4-phase2-harvest-receipt-v1",
        "subject_sha": subject_sha,
        "slurm_job_id": str(job_id),
        "scheduler_state": scheduler_state,
        "local_runner_code": runner_code,
        "scientific_terminal": terminal,
        "recomputed_terminal": recomputed_terminal,
        "model_id": scientific["model_id"],
        "model_revision": scientific["model_revision"],
        "training_policy_mode_after_canonical_gate": training_policy_mode,
        "canonical_admission_receipt_id": canonical_admission_receipt_id,
        "E_over_D_gpu_ratio": e_over_d_gpu_ratio,
        "raw_paper4_standalone_authorized_field": raw_standalone_flag,
        "raw_standalone_field_is_non_authoritative": True,
        "standalone_paper4_authorized": False,
        "standalone_requires_issue_462_and_fresh_467_468_evidence": True,
        "execution_subject_sha256": _sha256(execution_subject_path),
        "raw_final_receipt_sha256": _sha256(final_path),
        "raw_data_manifest_sha256": _sha256(manifest_path),
        "transport_protocol_sha256": _sha256(transport_path),
        "grants_scientific_authority": False,
    }
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--transport", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--scheduler-state", required=True)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    try:
        receipt = harvest(
            outdir=args.outdir,
            submission_path=args.submission,
            transport_path=args.transport,
            subject_sha=args.subject_sha,
            job_id=args.job_id,
            scheduler_state=args.scheduler_state,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"CANNOT_CHECK_EXECUTION_STATE: {exc}") from exc
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
