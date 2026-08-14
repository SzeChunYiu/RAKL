from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from experiments.training_ladder.harvest_phase2_v1 import COMPUTE_BOUND_PATHS, harvest as harvest_v1
from experiments.training_ladder.harvest_phase2_v2 import V2_IMPLEMENTATION_PATHS, harvest_v2


ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_V1 = ROOT / "research" / "paper4_phase2_execution_transport_v1" / "PROTOCOL.json"
TRANSPORT_V2 = ROOT / "research" / "paper4_phase2_execution_transport_v2" / "PROTOCOL.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def _write_reduced_bundle(tmp_path: Path, *, subject: str, v2_submission: bool) -> tuple[Path, Path, str]:
    p1 = json.loads(TRANSPORT_V1.read_text())
    job_id = "24680"
    outdir = tmp_path / job_id
    outdir.mkdir(parents=True)
    compute_blobs = {path: p1["frozen_git_blobs"][path] for path in COMPUTE_BOUND_PATHS}
    execution = {
        "schema_version": "paper4-phase2-compute-subject-v1",
        "subject_sha": subject,
        "slurm_job_id": job_id,
        "model_id": p1["scientific_subject_unchanged"]["model_id"],
        "model_revision": p1["scientific_subject_unchanged"]["model_revision"],
        "git_blobs": compute_blobs,
        "grants_scientific_authority": False,
        "standalone_paper4_authorized": False,
    }
    final = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "terminal": "RESOURCE_BLOCKED",
        "grants_scientific_authority": False,
        "paper4_standalone_authorized": True,
    }
    submission = {
        "schema_version": "paper4-phase2-submission-receipt-v1",
        "subject_sha": subject,
        "slurm_job_id": job_id,
        "frozen_git_blobs": p1["frozen_git_blobs"],
        "grants_scientific_authority": False,
        "standalone_paper4_authorized": False,
    }
    if v2_submission:
        submission.update(
            {
                "transport_binding_version": 2,
                "transport_protocol_sha256": _sha256(TRANSPORT_V1),
                "transport_v2_protocol_sha256": _sha256(TRANSPORT_V2),
                "harvest_interpreter_git_blobs": {rel: _git("hash-object", rel) for rel in V2_IMPLEMENTATION_PATHS},
            }
        )
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission))
    (outdir / "EXECUTION_SUBJECT.json").write_text(json.dumps(execution))
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(final))
    (outdir / "DATA_MANIFEST.json").write_text("{}\n")
    (outdir / "LOCAL_RUNNER_CODE.txt").write_text("2\n")
    return outdir, submission_path, job_id


def test_strongest_parent_v1_accepts_harvest_without_local_head_binding(tmp_path):
    fake_subject = "f" * 40
    outdir, submission, job_id = _write_reduced_bundle(tmp_path, subject=fake_subject, v2_submission=False)
    assert _git("rev-parse", "HEAD") != fake_subject
    receipt = harvest_v1(
        outdir=outdir,
        submission_path=submission,
        transport_path=TRANSPORT_V1,
        subject_sha=fake_subject,
        job_id=job_id,
        scheduler_state="COMPLETED",
    )
    assert receipt["scientific_terminal"] == "RESOURCE_BLOCKED"
    assert receipt["standalone_paper4_authorized"] is False


def test_v2_rejects_that_exact_post_submission_interpreter_drift_shape(tmp_path):
    fake_subject = "f" * 40
    outdir, submission, job_id = _write_reduced_bundle(tmp_path, subject=fake_subject, v2_submission=True)
    with pytest.raises(ValueError, match="harvest_head_mismatch"):
        harvest_v2(
            repo_root=ROOT,
            outdir=outdir,
            submission_path=submission,
            transport_v1_path=TRANSPORT_V1,
            transport_v2_path=TRANSPORT_V2,
            subject_sha=fake_subject,
            job_id=job_id,
            scheduler_state="COMPLETED",
        )


def test_v2_accepts_reduced_terminal_only_on_exact_current_subject_and_keeps_authority_false(tmp_path):
    subject = _git("rev-parse", "HEAD")
    outdir, submission, job_id = _write_reduced_bundle(tmp_path, subject=subject, v2_submission=True)
    receipt = harvest_v2(
        repo_root=ROOT,
        outdir=outdir,
        submission_path=submission,
        transport_v1_path=TRANSPORT_V1,
        transport_v2_path=TRANSPORT_V2,
        subject_sha=subject,
        job_id=job_id,
        scheduler_state="COMPLETED",
    )
    assert receipt["schema_version"] == "paper4-phase2-harvest-receipt-v2"
    assert receipt["harvest_subject_binding_v2"] is True
    assert receipt["harvest_interpreter_subject_sha"] == subject
    assert receipt["scientific_terminal"] == "RESOURCE_BLOCKED"
    assert receipt["training_policy_mode_after_canonical_gate"] == "STATIC_STRUCTURAL"
    assert receipt["raw_paper4_standalone_authorized_field"] is True
    assert receipt["standalone_paper4_authorized"] is False
    assert receipt["grants_scientific_authority"] is False


def test_v2_rejects_interpreter_blob_drift_even_at_same_subject_argument(tmp_path):
    subject = _git("rev-parse", "HEAD")
    outdir, submission, job_id = _write_reduced_bundle(tmp_path, subject=subject, v2_submission=True)
    payload = json.loads(submission.read_text())
    rel = next(iter(payload["harvest_interpreter_git_blobs"]))
    payload["harvest_interpreter_git_blobs"][rel] = "0" * 40
    submission.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="harvest_interpreter_git_blob_mismatch"):
        harvest_v2(
            repo_root=ROOT,
            outdir=outdir,
            submission_path=submission,
            transport_v1_path=TRANSPORT_V1,
            transport_v2_path=TRANSPORT_V2,
            subject_sha=subject,
            job_id=job_id,
            scheduler_state="COMPLETED",
        )


def test_v2_rejects_transport_protocol_substitution(tmp_path):
    subject = _git("rev-parse", "HEAD")
    outdir, submission, job_id = _write_reduced_bundle(tmp_path, subject=subject, v2_submission=True)
    payload = json.loads(submission.read_text())
    payload["transport_v2_protocol_sha256"] = "0" * 64
    submission.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="submission_v2_transport_protocol_sha256_mismatch"):
        harvest_v2(
            repo_root=ROOT,
            outdir=outdir,
            submission_path=submission,
            transport_v1_path=TRANSPORT_V1,
            transport_v2_path=TRANSPORT_V2,
            subject_sha=subject,
            job_id=job_id,
            scheduler_state="COMPLETED",
        )
