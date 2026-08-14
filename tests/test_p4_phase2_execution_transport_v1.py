from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from experiments.training_ladder.harvest_phase2_v1 import COMPUTE_BOUND_PATHS, harvest
from experiments.training_ladder.validate_phase2_v1_terminal import RC_TERMINALS, validate_terminal_pair


ROOT = Path(__file__).resolve().parents[1]
TRANSPORT = ROOT / "research" / "paper4_phase2_execution_transport_v1" / "PROTOCOL.json"


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def _transport() -> dict:
    return json.loads(TRANSPORT.read_text())


def _write_reduced_bundle(tmp_path: Path, *, terminal: str, runner_code: int, raw_standalone: bool | None = None):
    transport = _transport()
    subject = "subject-sha"
    job_id = "12345"
    outdir = tmp_path / job_id
    outdir.mkdir(parents=True)
    frozen = transport["frozen_git_blobs"]
    compute_blobs = {path: frozen[path] for path in COMPUTE_BOUND_PATHS}
    execution = {
        "schema_version": "paper4-phase2-compute-subject-v1",
        "subject_sha": subject,
        "slurm_job_id": job_id,
        "model_id": transport["scientific_subject_unchanged"]["model_id"],
        "model_revision": transport["scientific_subject_unchanged"]["model_revision"],
        "git_blobs": compute_blobs,
        "grants_scientific_authority": False,
        "standalone_paper4_authorized": False,
    }
    final = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "terminal": terminal,
        "grants_scientific_authority": False,
    }
    if raw_standalone is not None:
        final["paper4_standalone_authorized"] = raw_standalone
    submission = {
        "schema_version": "paper4-phase2-submission-receipt-v1",
        "subject_sha": subject,
        "slurm_job_id": job_id,
        "frozen_git_blobs": frozen,
        "grants_scientific_authority": False,
        "standalone_paper4_authorized": False,
    }
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission))
    (outdir / "EXECUTION_SUBJECT.json").write_text(json.dumps(execution))
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(final))
    (outdir / "DATA_MANIFEST.json").write_text("{}\n")
    (outdir / "LOCAL_RUNNER_CODE.txt").write_text(str(runner_code) + "\n")
    return transport, outdir, submission_path, subject, job_id


def test_transport_freeze_preserves_exact_scientific_subject_blobs():
    transport = _transport()
    assert transport["chronology"]["phase2_model_outputs_accessed_before_freeze"] is False
    assert transport["scientific_subject_unchanged"]["scientific_settings_changed"] is False
    for path, expected in transport["frozen_git_blobs"].items():
        assert _git_blob_sha((ROOT / path).read_bytes()) == expected
    assert transport["grants_scientific_authority"] is False


def test_every_registered_runner_code_terminal_pair_is_explicit_and_mismatches_fail():
    base = {"schema_version": "rakl-paper4-phase2-result-v1", "grants_scientific_authority": False}
    for code, terminals in RC_TERMINALS.items():
        for terminal in terminals:
            assert validate_terminal_pair({**base, "terminal": terminal}, code) == (True, terminal)
    ok, reason = validate_terminal_pair({**base, "terminal": "RESOURCE_BLOCKED"}, 0)
    assert ok is False and "mismatch" in reason
    ok, reason = validate_terminal_pair({**base, "terminal": "ADAPTIVE_RESIDUAL_SUPPORTED"}, 1)
    assert ok is False and "mismatch" in reason


def test_complete_early_harm_scientific_negative_is_not_relabelled_scheduler_failure(tmp_path):
    _, outdir, submission, subject, job_id = _write_reduced_bundle(
        tmp_path,
        terminal="ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
        runner_code=1,
    )
    receipt = harvest(
        outdir=outdir,
        submission_path=submission,
        transport_path=TRANSPORT,
        subject_sha=subject,
        job_id=job_id,
        scheduler_state="COMPLETED",
    )
    assert receipt["scientific_terminal"] == "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION"
    assert receipt["training_policy_mode_after_canonical_gate"] == "STATIC_STRUCTURAL"
    assert receipt["standalone_paper4_authorized"] is False
    assert receipt["grants_scientific_authority"] is False


def test_resource_block_is_preserved_as_scientific_resource_terminal(tmp_path):
    _, outdir, submission, subject, job_id = _write_reduced_bundle(
        tmp_path,
        terminal="RESOURCE_BLOCKED",
        runner_code=2,
    )
    receipt = harvest(
        outdir=outdir,
        submission_path=submission,
        transport_path=TRANSPORT,
        subject_sha=subject,
        job_id=job_id,
        scheduler_state="COMPLETED",
    )
    assert receipt["scientific_terminal"] == "RESOURCE_BLOCKED"
    assert receipt["training_policy_mode_after_canonical_gate"] == "STATIC_STRUCTURAL"


def test_raw_phase2_standalone_flag_is_explicitly_non_authoritative(tmp_path):
    _, outdir, submission, subject, job_id = _write_reduced_bundle(
        tmp_path,
        terminal="ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
        runner_code=1,
        raw_standalone=True,
    )
    receipt = harvest(
        outdir=outdir,
        submission_path=submission,
        transport_path=TRANSPORT,
        subject_sha=subject,
        job_id=job_id,
        scheduler_state="COMPLETED",
    )
    assert receipt["raw_paper4_standalone_authorized_field"] is True
    assert receipt["raw_standalone_field_is_non_authoritative"] is True
    assert receipt["standalone_paper4_authorized"] is False
    assert receipt["standalone_requires_issue_462_and_fresh_467_468_evidence"] is True


def test_scheduler_noncompletion_cannot_be_interpreted_as_scientific_terminal(tmp_path):
    _, outdir, submission, subject, job_id = _write_reduced_bundle(
        tmp_path,
        terminal="RESOURCE_BLOCKED",
        runner_code=2,
    )
    with pytest.raises(ValueError, match="scheduler_not_completed"):
        harvest(
            outdir=outdir,
            submission_path=submission,
            transport_path=TRANSPORT,
            subject_sha=subject,
            job_id=job_id,
            scheduler_state="FAILED",
        )


def test_compute_subject_must_bind_every_load_bearing_scientific_blob(tmp_path):
    _, outdir, submission, subject, job_id = _write_reduced_bundle(
        tmp_path,
        terminal="RESOURCE_BLOCKED",
        runner_code=2,
    )
    path = outdir / "EXECUTION_SUBJECT.json"
    execution = json.loads(path.read_text())
    execution["git_blobs"].pop(next(iter(execution["git_blobs"])))
    path.write_text(json.dumps(execution))
    with pytest.raises(ValueError, match="compute_git_blob_binding_incomplete_or_extra"):
        harvest(
            outdir=outdir,
            submission_path=submission,
            transport_path=TRANSPORT,
            subject_sha=subject,
            job_id=job_id,
            scheduler_state="COMPLETED",
        )
