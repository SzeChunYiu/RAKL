from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READINESS = (
    ROOT
    / "research/paper2_microtrial_v3/PAPER2_NATIVE_STAGING_PREFLIGHT_READINESS_RECEIPT_20260811.json"
)
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3.json"
SUBJECT_SHA = "8184ed2960078102a6b5c25221dd26fc01f03a7a"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def test_native_preflight_readiness_binds_exact_receipts_and_contract() -> None:
    readiness = _load(READINESS)
    expected = {
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_8184ED2.json": (
            "fa6fe7b716da221419005001dd26d75a5ecf11f335168282c501e2bd81f0db02",
            "BOOTSTRAP_PASS_ATOMICALLY_PROMOTED",
        ),
        "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_8184ED2.json": (
            "b5120b4ff2179a962ab41c6a81861fcc6867b10176a7a97f594f346702065c09",
            "READY_NOT_SUBMITTED",
        ),
        "research/paper2_microtrial_v3/native_receipts/QUARANTINE_OBSERVATION_NATIVE_8184ED2.json": (
            "8635afd77787b809f1ea356479e38d8f103a0dc88154938b4971442761944efe",
            "PRIOR_DIRTY_CHECKOUT_QUARANTINED__ACTIVE_CHECKOUT_CLEAN_READ_ONLY",
        ),
    }
    observed = {item["path"]: item for item in readiness["native_receipts"]}
    assert set(observed) == set(expected)
    for relative, (digest, verdict) in expected.items():
        path = ROOT / relative
        assert _sha256(path) == digest
        assert observed[relative]["sha256"] == digest
        assert observed[relative]["verdict"] == verdict == _load(path)["verdict"]

    contract = _load(CONTRACT)
    binding = readiness["contract_binding"]
    assert binding["path"] == str(CONTRACT.relative_to(ROOT))
    assert binding["file_sha256"] == _sha256(CONTRACT)
    assert binding["canonical_sha256"] == _canonical_sha256(contract)
    dry_run = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_8184ED2.json"
    )
    assert binding["dry_run_bound_canonical_sha256"] == dry_run[
        "contract_canonical_sha256"
    ] == binding["canonical_sha256"]
    assert binding["matches_dry_run"] is True


def test_native_preflight_is_exact_clean_and_strictly_not_submitted() -> None:
    readiness = _load(READINESS)
    bootstrap = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_8184ED2.json"
    )
    dry_run = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_8184ED2.json"
    )
    assert readiness["subject_sha"] == SUBJECT_SHA
    assert readiness["subject_tree"] == bootstrap["observed_repo_tree"]
    assert bootstrap["expected_repo_sha"] == bootstrap["observed_repo_sha"] == SUBJECT_SHA
    assert bootstrap["checkout_clean"] is True
    assert bootstrap["detached_head"] is True
    assert dry_run["expected_repo_sha"] == dry_run["observed_repo_sha"] == SUBJECT_SHA
    assert dry_run["failures"] == []
    assert dry_run["submitted_job_ids"] == []
    assert dry_run["model_execution_performed"] is False
    assert dry_run["evaluated_result_record_count"] == 0
    assert readiness["execution_counts"] == {
        "evaluated_result_records": 0,
        "jobs_submitted": 0,
        "model_executions": 0,
    }
    assert readiness["native_result"]["active_checkout_status_entry_count"] == 0
    planned = readiness["native_result"]["planned_sbatch_argv"]
    assert planned == dry_run["planned_sbatch_argv"]
    assert len(planned) == 2
    assert all(argv[0] == "sbatch" for argv in planned)
    assert "executed_sbatch_argv" not in dry_run
    assert "not native asset staging success" in readiness["claim_boundary"].lower()
    assert readiness["verdict"] == (
        "NATIVE_PREFLIGHT_READY_NOT_SUBMITTED__PRIOR_FALSIFIER_PRESERVED"
    )


def test_prior_refusal_and_quarantined_checkout_remain_bound_negative_history() -> None:
    readiness = _load(READINESS)
    history = readiness["negative_history"]
    prior = ROOT / history["prior_dry_run_refusal_path"]
    repair = ROOT / history["prior_repair_receipt_path"]
    assert _sha256(prior) == history["prior_dry_run_refusal_sha256"] == (
        "5e102ec6e1d0f6145e4c19d5e45f989c30fd236a4d7975d0de05c2aa84b1f445"
    )
    assert _load(prior)["verdict"] == history["prior_dry_run_verdict"] == (
        "REFUSE_PREFLIGHT_VALIDATION"
    )
    assert _sha256(repair) == history["prior_repair_receipt_sha256"]
    assert history["superseded_or_deleted"] is False

    quarantine = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/QUARANTINE_OBSERVATION_NATIVE_8184ED2.json"
    )
    assert quarantine["observation_mode"] == "read_only"
    assert quarantine["remote_mutation_performed_by_observation"] is False
    assert quarantine["quarantined_checkout"]["repo_sha"] == history["prior_subject_sha"]
    assert quarantine["quarantined_checkout"]["git_status_entry_count"] == 24
    prior_observation = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/REMOTE_DIRTY_CHECKOUT_OBSERVATION_NATIVE_2FC6457B.json"
    )
    quarantined = quarantine["quarantined_checkout"]
    assert quarantined["git_status_porcelain_v1"] == prior_observation[
        "git_status_porcelain_v1"
    ]
    assert quarantined["git_status_porcelain_v1_sha256"] == prior_observation[
        "git_status_porcelain_v1_sha256"
    ]
    assert quarantined["untracked_pyc_files"] == prior_observation["untracked_pyc_files"]
    assert quarantined["matches_prior_exact_status_receipt"] is True
    assert quarantined["matches_prior_exact_file_hashes"] is True
    assert quarantine["active_checkout"]["repo_sha"] == SUBJECT_SHA
    assert quarantine["active_checkout"]["repo_tree"] == readiness["subject_tree"]
    assert quarantine["active_checkout"]["git_status_entry_count"] == 0
    assert quarantine["slurm_job_submission_performed"] is False
    bootstrap = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_8184ED2.json"
    )
    dry_run = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_8184ED2.json"
    )
    assert (
        bootstrap["observed_at_utc"]
        < dry_run["created_at_utc"]
        < readiness["created_at_utc"]
        < quarantine["observed_at_utc"]
        < readiness["finalized_at_utc"]
    )
