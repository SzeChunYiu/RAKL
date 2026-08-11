from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import rakl.paper2_cpu_staging_v3_1 as staging


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_1.json"
SCRIPTS = ROOT / "experiments/paper2/lunarc"
SCHEMAS = ROOT / "schemas"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v3_1_contract_is_self_bound_versioned_and_preserves_v3_failure() -> None:
    contract = _load(CONTRACT)
    assert staging.validate_staging_contract(contract, repository_root=ROOT) == ()
    self_binding = next(item for item in contract["bindings"] if item["role"] == "contract_self")
    assert self_binding["path"] == "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_1.json"
    assert self_binding["sha256_mode"] == "canonical_contract_with_self_sha256_zeroed"
    assert self_binding["sha256"] == staging._contract_self_sha256(contract)
    assert contract["candidate_root"].endswith("/.paper2-cpu-v3-1-candidate")
    assert contract["final_root"].endswith("/paper2-cpu-v3-1")
    assert contract["receipt_root"].endswith("/v3_1")
    assert contract["failure_root"].endswith("/v3_1")
    assert contract["predecessor_failure"] == {
        "contract_id": "PAPER2_CPU_STAGING_V3",
        "probe_job_id": "3475080",
        "staging_job_id": "3475081",
        "staging_verdict": "STAGING_FAILED_PRESERVED",
        "http_status": 403,
        "preserved_candidate_path": "/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/.paper2-cpu-v3-candidate-3475081",
        "first_missing_artifact": "wheel:torch==2.8.0+cpu",
        "localization_authority": "bounded_inference_from_first_missing_manifest_artifact_not_direct_failure-receipt_proof",
    }
    assert contract["model_execution_permitted"] is False
    assert contract["submission_policy"]["default_operator_mode"] == "READY_NOT_SUBMITTED"
    assert contract["submission_policy"]["retry_requires_new_explicit_operator_action"] is True


def test_v3_1_contract_self_hash_and_every_bound_byte_fail_closed() -> None:
    contract = _load(CONTRACT)
    changed = copy.deepcopy(contract)
    changed["repair_boundary"] += " mutation"
    assert "contract_binding_hash_mismatch:contract_self" in staging.validate_staging_contract(
        changed, repository_root=ROOT
    )
    changed = copy.deepcopy(contract)
    self_binding = next(item for item in changed["bindings"] if item["role"] == "contract_self")
    self_binding["sha256_mode"] = "ordinary_file_sha256"
    failures = staging.validate_staging_contract(changed, repository_root=ROOT)
    assert "contract_self_hash_mode_invalid" in failures


def test_v3_1_contract_and_all_receipt_schemas_are_valid() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    contract = _load(CONTRACT)
    schema_names = [
        "paper2-cpu-staging-contract-v3-1.schema.json",
        "paper2-cpu-staging-construction-receipt-v3-1.schema.json",
        "paper2-cpu-staging-submission-receipt-v3-1.schema.json",
        "paper2-cpu-staging-network-probe-receipt-v3-1.schema.json",
        "paper2-cpu-staging-result-receipt-v3-1.schema.json",
        "paper2-cpu-staging-harvest-receipt-v3-1.schema.json",
    ]
    for name in schema_names:
        schema = _load(SCHEMAS / name)
        jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        _load(SCHEMAS / schema_names[0]), format_checker=jsonschema.FormatChecker()
    ).validate(contract)
    for binding in contract["bindings"]:
        if binding["role"] == "contract_self":
            continue
        assert hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest() == binding["sha256"]


def test_v3_1_operator_scripts_use_versioned_runtime_and_paths_without_model_execution() -> None:
    names = [
        "network_probe_v3_1.sbatch",
        "stage_cpu_assets_v3_1.sbatch",
        "submit_cpu_staging_v3_1.sh",
        "harvest_cpu_staging_v3_1.sh",
    ]
    combined = "\n".join((SCRIPTS / name).read_text(encoding="utf-8") for name in names)
    assert "rakl.paper2_cpu_staging_v3_1" in combined
    assert "CPU_STAGING_CONTRACT_V3_1.json" in combined
    assert "/receipts/v3_1" in combined
    assert "/failures/v3_1" in combined
    assert "paper2-cpu-v3-1" in combined
    assert "--dependency=afterok" not in (SCRIPTS / "submit_cpu_staging_v3_1.sh").read_text()
    forbidden = ("AutoModel", "generate(", "execute_microtrial", "paper2_pendulum_microtrial run")
    assert not any(token in combined for token in forbidden)


def test_v3_1_default_submission_is_schema_valid_ready_not_submitted(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    contract = _load(CONTRACT)
    sha = "c" * 40
    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text(
        json.dumps(
            {
                "verdict": "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
                "exit_status": 0,
                "expected_repo_sha": sha,
                "observed_repo_sha": sha,
                "repo_path": str(ROOT),
                "checkout_clean": True,
                "detached_head": True,
                "jobs_submitted": 0,
                "model_execution_performed": False,
            }
        ),
        encoding="utf-8",
    )
    receipt = staging.build_submission_receipt(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha=sha,
        observation=staging.SubmissionObservation(
            observed_repo_sha=sha,
            checkout_clean=True,
            execution_host="cosmos3.int.lunarc",
            observed_associations=frozenset({("lu2026-2-51", "shared")}),
        ),
        account="lu2026-2-51",
        partition="shared",
        submit=False,
        bootstrap_receipt_path=bootstrap,
    )
    assert receipt["verdict"] == "READY_NOT_SUBMITTED"
    assert receipt["submitted_job_ids"] == []
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    schema = _load(SCHEMAS / "paper2-cpu-staging-submission-receipt-v3-1.schema.json")
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(receipt)


def _negative_harvest_fixture(tmp_path: Path) -> dict[str, Any]:
    jobs = ["41001", "41002"]
    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text("{}", encoding="utf-8")
    submission = {
        "verdict": "SUBMITTED_TWO_PHASE_STAGING",
        "submitted_job_ids": jobs,
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "bootstrap_receipt_path": str(bootstrap),
        "bootstrap_receipt_sha256": hashlib.sha256(bootstrap.read_bytes()).hexdigest(),
    }
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    receipt_root = tmp_path / "receipts"
    failure_root = tmp_path / "failures"
    final_root = tmp_path / "assets/paper2-cpu-v3-1"
    receipt_root.mkdir()
    failure_root.mkdir()
    final_root.parent.mkdir()
    candidate = final_root.parent / ".paper2-cpu-v3-1-candidate-41002"
    candidate.mkdir()
    probe = {
        "verdict": "NETWORK_PROBE_PASS",
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "slurm_job_id": jobs[0],
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    (receipt_root / "network-probe-41001.json").write_text(
        json.dumps(probe), encoding="utf-8"
    )
    failed = {
        "verdict": "STAGING_FAILED_PRESERVED",
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "slurm_job_id": jobs[1],
        "failures": ["staging_exception"],
        "error_type": "ArtifactDownloadError",
        "candidate_path": str(candidate),
        "candidate_preserved": True,
        "final_path": str(final_root),
        "final_exists": False,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    failure_path = failure_root / "staging-failed-41002.json"
    failure_path.write_text(json.dumps(failed), encoding="utf-8")
    return {
        "submission": submission,
        "submission_path": submission_path,
        "receipt_root": receipt_root,
        "failure_root": failure_root,
        "final_root": final_root,
        "failure_path": failure_path,
        "failed": failed,
        "rows": "41001|COMPLETED|0:0|00:00:06||cn004\n41002|FAILED|2:0|00:00:04||cn004\n",
    }


def _harvest(case: dict[str, Any], rows: str | None = None) -> dict[str, Any]:
    def runner(_argv: list[str], **_: object) -> object:
        return type("Completed", (), {"stdout": case["rows"] if rows is None else rows})()

    return staging.build_harvest_receipt(
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
    )


def test_v3_1_harvest_accepts_exact_scheduler_and_preserved_failure_lineage(
    tmp_path: Path,
) -> None:
    receipt = _harvest(_negative_harvest_fixture(tmp_path))
    assert receipt["verdict"] == "HARVEST_STAGING_NEGATIVE_PRESERVED"
    assert receipt["failures"] == ["staging_job_or_receipt_failed"]
    assert receipt["negative_history_preserved"] is True


@pytest.mark.parametrize(
    ("mutation", "rows"),
    [
        ("wrong_slurm_job", None),
        ("missing_slurm_job", None),
        ("candidate_not_preserved", None),
        ("candidate_missing_on_disk", None),
        ("final_exists_mismatch", None),
        ("final_unexpectedly_exists", None),
        ("missing_scheduler_row", "41001|COMPLETED|0:0|00:00:06||cn004\n"),
        (
            "duplicate_scheduler_row",
            "41001|COMPLETED|0:0|00:00:06||cn004\n41001|COMPLETED|0:0|00:00:07||cn005\n",
        ),
    ],
)
def test_v3_1_harvest_hostile_negative_evidence_fails_closed(
    tmp_path: Path, mutation: str, rows: str | None
) -> None:
    case = _negative_harvest_fixture(tmp_path)
    failed = case["failed"]
    if mutation == "wrong_slurm_job":
        failed["slurm_job_id"] = "99999"
    elif mutation == "missing_slurm_job":
        failed.pop("slurm_job_id")
    elif mutation == "candidate_not_preserved":
        failed["candidate_preserved"] = False
    elif mutation == "candidate_missing_on_disk":
        Path(failed["candidate_path"]).rmdir()
    elif mutation == "final_exists_mismatch":
        failed["final_exists"] = True
    elif mutation == "final_unexpectedly_exists":
        case["final_root"].mkdir()
    case["failure_path"].write_text(json.dumps(failed), encoding="utf-8")
    receipt = _harvest(case, rows)
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert receipt["negative_history_preserved"] is False


def test_v3_1_harvest_refused_receipt_requires_explicit_presence_observations(
    tmp_path: Path,
) -> None:
    case = _negative_harvest_fixture(tmp_path)
    case["failure_path"].unlink()
    refused = copy.deepcopy(case["failed"])
    refused["verdict"] = "STAGING_REFUSED"
    refused.pop("candidate_preserved")
    refused.pop("final_exists")
    (case["failure_root"] / "staging-refused-41002.json").write_text(
        json.dumps(refused), encoding="utf-8"
    )
    receipt = _harvest(case)
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert receipt["negative_history_preserved"] is False
