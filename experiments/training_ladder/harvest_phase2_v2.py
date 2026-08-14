#!/usr/bin/env python3
"""Subject-bound Paper-IV Phase-2 harvest successor.

V1 binds submission and compute-side scientific subjects, but its harvest
interpreter can be invoked from a later clean checkout.  V2 verifies that the
repository, transport protocols, harvester stack and authority imports are the
exact submission-bound Git objects before delegating the unchanged raw-bundle
scientific checks to the v1 harvester.

No scientific threshold is changed and no scientific/standalone-paper
authority is granted here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Mapping

from experiments.training_ladder.harvest_phase2_v1 import harvest as harvest_v1


V2_IMPLEMENTATION_PATHS = {
    "research/paper4_phase2_execution_transport_v1/PROTOCOL.json",
    "research/paper4_phase2_execution_transport_v2/PROTOCOL.json",
    "experiments/training_ladder/submit_and_harvest_phase2_v2_transport.sh",
    "experiments/training_ladder/harvest_phase2_v2.py",
    "experiments/training_ladder/harvest_phase2_v1.py",
    "experiments/training_ladder/validate_phase2_v1_terminal.py",
    "experiments/training_ladder/run_phase2_v1_lunarc_transport_v1.sbatch",
    "src/rakl/phase2_adaptive_receipt_admission.py",
    "src/rakl/training_policy_authority.py",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo_root), *args], text=True).strip()


def verify_harvest_subject(
    *,
    repo_root: Path,
    subject_sha: str,
    submission: Mapping[str, object],
    transport_v1_path: Path,
    transport_v2_path: Path,
) -> dict[str, str]:
    head = _git(repo_root, "rev-parse", "HEAD")
    if head != subject_sha:
        raise ValueError(f"harvest_head_mismatch:{head}:{subject_sha}")
    dirty = _git(repo_root, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise ValueError("harvest_tracked_checkout_dirty")

    if submission.get("schema_version") != "paper4-phase2-submission-receipt-v1":
        raise ValueError("submission_schema_mismatch")
    if submission.get("transport_binding_version") != 2:
        raise ValueError("submission_transport_binding_version_mismatch")
    if submission.get("subject_sha") != subject_sha:
        raise ValueError("submission_subject_mismatch")

    if submission.get("transport_protocol_sha256") != _sha256(transport_v1_path):
        raise ValueError("submission_v1_transport_protocol_sha256_mismatch")
    if submission.get("transport_v2_protocol_sha256") != _sha256(transport_v2_path):
        raise ValueError("submission_v2_transport_protocol_sha256_mismatch")

    v2 = _load(transport_v2_path)
    if v2.get("schema_version") != "paper4-phase2-execution-transport-v2":
        raise ValueError("transport_v2_schema_mismatch")
    if v2.get("grants_scientific_authority") is not False:
        raise ValueError("transport_v2_authority_boundary_invalid")

    bound = submission.get("harvest_interpreter_git_blobs")
    if not isinstance(bound, Mapping):
        raise ValueError("harvest_interpreter_git_blob_binding_missing")
    if set(bound) != V2_IMPLEMENTATION_PATHS:
        raise ValueError("harvest_interpreter_git_blob_binding_incomplete_or_extra")

    observed: dict[str, str] = {}
    for rel in sorted(V2_IMPLEMENTATION_PATHS):
        path = repo_root / rel
        if not path.is_file():
            raise ValueError(f"harvest_interpreter_path_missing:{rel}")
        actual = _git(repo_root, "hash-object", rel)
        expected = bound.get(rel)
        if actual != expected:
            raise ValueError(f"harvest_interpreter_git_blob_mismatch:{rel}:{actual}:{expected}")
        observed[rel] = actual
    return observed


def harvest_v2(
    *,
    repo_root: Path,
    outdir: Path,
    submission_path: Path,
    transport_v1_path: Path,
    transport_v2_path: Path,
    subject_sha: str,
    job_id: str,
    scheduler_state: str,
) -> dict:
    submission = _load(submission_path)
    observed = verify_harvest_subject(
        repo_root=repo_root,
        subject_sha=subject_sha,
        submission=submission,
        transport_v1_path=transport_v1_path,
        transport_v2_path=transport_v2_path,
    )

    receipt = harvest_v1(
        outdir=outdir,
        submission_path=submission_path,
        transport_path=transport_v1_path,
        subject_sha=subject_sha,
        job_id=job_id,
        scheduler_state=scheduler_state,
    )
    if receipt.get("grants_scientific_authority") is not False:
        raise ValueError("v1_harvest_authority_boundary_invalid")
    if receipt.get("standalone_paper4_authorized") is not False:
        raise ValueError("v1_harvest_standalone_boundary_invalid")

    out = dict(receipt)
    out["schema_version"] = "paper4-phase2-harvest-receipt-v2"
    out["harvest_subject_binding_v2"] = True
    out["harvest_interpreter_subject_sha"] = subject_sha
    out["harvest_interpreter_git_blobs"] = observed
    out["transport_v2_protocol_sha256"] = _sha256(transport_v2_path)
    out["standalone_paper4_authorized"] = False
    out["grants_scientific_authority"] = False
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--transport-v1", type=Path, required=True)
    parser.add_argument("--transport-v2", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--scheduler-state", required=True)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    try:
        receipt = harvest_v2(
            repo_root=args.repo_root,
            outdir=args.outdir,
            submission_path=args.submission,
            transport_v1_path=args.transport_v1,
            transport_v2_path=args.transport_v2,
            subject_sha=args.subject_sha,
            job_id=args.job_id,
            scheduler_state=args.scheduler_state,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"CANNOT_CHECK_EXECUTION_STATE: {exc}") from exc
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
