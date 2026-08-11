"""Wave-1 Lane B confirmatory ALR / A3↔A4 preparation packet.

Prep-only freeze. Does not authorize confirmatory model jobs or mint results.
Parent v1 packets remain immutable history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paper3_annotation import canonical_sha256

PREP_DIR = Path("research/paper2_alr_a3a4_confirmatory_prep_wave1_v1")
PREP_PACKET_PATH = PREP_DIR / "PREP_PACKET.json"
CAPABILITY_GATE_PATH = PREP_DIR / "CAPABILITY_GATE.json"
SUBMISSION_GATE_PATH = PREP_DIR / "MODEL_JOB_SUBMISSION_GATE.json"
EVALUATOR_BINDING_PATH = PREP_DIR / "EVALUATOR_PROTOCOL_BINDING.json"
NEGATIVE_HISTORY_PATH = PREP_DIR / "NEGATIVE_HISTORY.json"

REQUIRED_NEGATIVE_JOBS = ("3476730", "3476731", "3476742", "3476756")
REQUIRED_ALR_HISTORY_JOBS = ("3476735", "3476736", "3476737", "3476748")


def _load(repo_root: Path, rel: Path) -> dict[str, Any]:
    return json.loads((repo_root / rel).read_text(encoding="utf-8"))


def load_prep_packet(repo_root: Path) -> dict[str, Any]:
    return _load(repo_root, PREP_PACKET_PATH)


def validate_prep_packet(repo_root: Path) -> dict[str, Any]:
    prep = load_prep_packet(repo_root)
    capability = _load(repo_root, CAPABILITY_GATE_PATH)
    submission = _load(repo_root, SUBMISSION_GATE_PATH)
    binding = _load(repo_root, EVALUATOR_BINDING_PATH)
    history = _load(repo_root, NEGATIVE_HISTORY_PATH)

    if prep.get("grants_scientific_authority") is not False:
        raise AssertionError("prep packet must not grant scientific authority")
    if prep.get("CAPABLE_MODEL_AVAILABLE") is not False:
        raise AssertionError("CAPABLE_MODEL_AVAILABLE must remain false until ORACLE ≥2/3")
    if prep.get("model_job_submission_allowed") is not False:
        raise AssertionError("confirmatory model-job submission must be forbidden")
    if prep.get("evaluated_results_accessed") is not False:
        raise AssertionError("prep packet must not access confirmatory outcomes")
    if prep.get("confirmatory_results_present") is not False:
        raise AssertionError("prep packet must not contain confirmatory results")
    if capability.get("CAPABLE_MODEL_AVAILABLE") is not False:
        raise AssertionError("capability gate CAPABLE_MODEL_AVAILABLE must be false")
    if submission.get("model_job_submission_allowed") is not False:
        raise AssertionError("submission gate must forbid model jobs")

    body = {k: v for k, v in prep.items() if k != "artifact_hash"}
    digest = canonical_sha256(body)
    if prep.get("artifact_hash") != digest:
        raise AssertionError("PREP_PACKET artifact_hash mismatch")

    for key, path, payload in (
        ("capability_gate_sha256", CAPABILITY_GATE_PATH, capability),
        ("model_job_submission_gate_sha256", SUBMISSION_GATE_PATH, submission),
        ("evaluator_protocol_binding_sha256", EVALUATOR_BINDING_PATH, binding),
        ("negative_history_sha256", NEGATIVE_HISTORY_PATH, history),
    ):
        expected = prep.get("bound_hashes", {}).get(key)
        actual = canonical_sha256(payload)
        if expected != actual:
            raise AssertionError(f"{key} mismatch for {path}")

    freeze = _load(
        repo_root, Path("benchmarks/scientific_transition_authority/FREEZE_RECEIPT_V2.json")
    )
    if binding.get("freeze_receipt_artifact_hash") != freeze.get("artifact_hash"):
        raise AssertionError("evaluator binding freeze receipt hash mismatch")
    if binding.get("protocol_sha256") != freeze.get("protocol_sha256"):
        raise AssertionError("evaluator binding protocol_sha256 mismatch")
    if binding.get("scorer_source_sha256") != freeze.get("scorer_source_sha256"):
        raise AssertionError("evaluator binding scorer_source_sha256 mismatch")

    parent_v1 = repo_root / "research/paper2_alr_confirmatory_v1/ISSUE_324_TERMINAL_RECEIPT.json"
    if not parent_v1.is_file():
        raise AssertionError("parent ALR confirmatory v1 terminal receipt missing")
    a3_packet = repo_root / "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json"
    if not a3_packet.is_file():
        raise AssertionError("parent A3↔A4 matched packet v1 missing")

    oracle_jobs = {str(row.get("job_id")) for row in history.get("capability_oracle_jobs", [])}
    missing_oracle = [job for job in REQUIRED_NEGATIVE_JOBS if job not in oracle_jobs]
    if missing_oracle:
        raise AssertionError(f"missing capability negative-history jobs: {missing_oracle}")

    alr_jobs = {
        str(row.get("job_id")) for row in history.get("prior_alr_non_confirmatory_jobs", [])
    }
    missing_alr = [job for job in REQUIRED_ALR_HISTORY_JOBS if job not in alr_jobs]
    if missing_alr:
        raise AssertionError(f"missing prior ALR history jobs: {missing_alr}")

    return {
        "ok": True,
        "packet_id": prep.get("packet_id"),
        "status": prep.get("status"),
        "CAPABLE_MODEL_AVAILABLE": False,
        "model_job_submission_allowed": False,
        "artifact_hash": digest,
        "successor_issues": prep.get("successor_issues"),
        "grants_scientific_authority": False,
    }


def refuse_confirmatory_model_job(repo_root: Path) -> None:
    """Fail closed if a caller attempts confirmatory model-job submission."""
    prep = load_prep_packet(repo_root)
    if prep.get("CAPABLE_MODEL_AVAILABLE") is True and prep.get(
        "model_job_submission_allowed"
    ) is True:
        return
    raise PermissionError(
        "confirmatory model-job submission refused: CAPABLE_MODEL_AVAILABLE=false "
        "(need ORACLE success_rate ≥ 2/3 at some authorized scale)"
    )
