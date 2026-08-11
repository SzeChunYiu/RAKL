from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import argparse
from typing import Any

import pytest

import rakl.paper2_cpu_staging_v3_2 as frozen
import rakl.paper2_cpu_staging_v3_2_1 as repair


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json"
MANIFEST = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json"
WHEEL_LOCK = ROOT / "research/paper2_microtrial_v3/CP311_LINUX_X86_64_WHEEL_LOCK_AUDIT.json"
NATIVE_STAGE = (
    ROOT
    / "research/paper2_microtrial_v3/native_receipts/"
    "STAGING_PASS_NATIVE_V3_2_JOB_3475124.json"
)
REPAIR_CONTRACT = (
    ROOT
    / "research/paper2_microtrial_v3/CPU_STAGING_HARVEST_REPAIR_CONTRACT_V3_2_1.json"
)
SYNTHESIS = (
    ROOT
    / "research/paper2_microtrial_v3/"
    "PAPER2_NATIVE_V3_2_SUCCESS_HARVEST_REPAIR_READINESS_RECEIPT_20260811.json"
)
INTERNAL_REVIEW = (
    ROOT
    / "research/paper2_microtrial_v3/"
    "PAPER2_NATIVE_V3_2_SUCCESS_HARVEST_REPAIR_INTERNAL_REVIEW_20260811.json"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v3_2_contract_and_runtime_remain_immutable_negative_history() -> None:
    contract = _load(CONTRACT)
    assert frozen.validate_staging_contract(contract, repository_root=ROOT) == ()
    runtime_binding = next(
        item for item in contract["bindings"] if item["role"] == "staging_runtime"
    )
    assert runtime_binding["path"] == "src/rakl/paper2_cpu_staging_v3_2.py"
    assert _sha(ROOT / runtime_binding["path"]) == runtime_binding["sha256"]
    assert runtime_binding["sha256"] == (
        "98a5e28ab42a0f762d6e080bf5cdf22c9dc0946b187bf50eb8272dae6e6d6e01"
    )


def test_v3_2_1_repair_contract_is_self_bound_and_forbids_execution() -> None:
    contract = _load(REPAIR_CONTRACT)
    assert contract["authority_status"] == "repair_ready_not_reharvested"
    assert contract["source_job_ids"] == ["3475123", "3475124"]
    assert contract["job_submission_permitted"] is False
    assert contract["model_execution_permitted"] is False
    assert contract["evaluated_result_access_permitted"] is False
    roles = [item["role"] for item in contract["bindings"]]
    assert len(roles) == len(set(roles))
    for binding in contract["bindings"]:
        if binding["role"] == "contract_self":
            normalized = copy.deepcopy(contract)
            next(
                item for item in normalized["bindings"] if item["role"] == "contract_self"
            )["sha256"] = "0" * 64
            assert binding["sha256"] == frozen._canonical_sha256(normalized)
        else:
            assert _sha(ROOT / binding["path"]) == binding["sha256"]
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(
        ROOT / "schemas/paper2-cpu-staging-harvest-repair-contract-v3-2-1.schema.json"
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(contract)


def test_v3_2_1_accepts_only_exact_bundled_direct_references() -> None:
    stage = _load(NATIVE_STAGE)
    observed = repair._parse_pip_freeze(stage["pip_freeze_all"])
    assert observed == stage["installed_distributions"]
    assert observed is not None and len(observed) == 31
    assert observed["pip"] == "24.3.1"
    assert observed["setuptools"] == "75.6.0"

    for name in ("pip", "setuptools"):
        exact = repair._BUNDLED_FREEZE_DIRECT_REFERENCES[name]
        for mutation in (
            exact.replace("sha256=", "sha256=0", 1),
            exact.replace("file:///build/", "file:///other/", 1),
            exact.replace("file://", "FILE://", 1),
            exact.replace(" @ ", "@", 1),
            exact + "?download=1",
            exact.replace("#sha256=", "#SHA256=", 1),
            " " + exact,
            exact + " ",
            f"{name} @ https://example.invalid/{name}.whl",
            f"{name}=={'24.3.1' if name == 'pip' else '75.6.0'}",
        ):
            lines = [mutation if line == exact else line for line in stage["pip_freeze_all"]]
            assert repair._parse_pip_freeze(lines) is None or repair._parse_pip_freeze(
                lines
            ) != stage["installed_distributions"]

    exact_lines = stage["pip_freeze_all"]
    for mutation in (
        exact_lines[:-1],
        exact_lines + [exact_lines[0]],
        exact_lines + ["extra-package==1.0"],
        [exact_lines[0], *exact_lines],
    ):
        assert repair._parse_pip_freeze(mutation) is None


def test_native_sacct_and_bundle_are_semantically_source_derived() -> None:
    assert repair._native_evidence_failures(ROOT) == ()
    raw = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/"
        "SACCT_NATIVE_V3_2_JOBS_3475123_3475124.json"
    )
    assert repair._stage_max_rss_bytes(raw) == 2_156_756_992


def _positive_fixture(tmp_path: Path) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    jobs = ["3475123", "3475124"]
    expected_sha = repair.SOURCE_SUBJECT_SHA
    contract = _load(CONTRACT)
    contract_sha = frozen._canonical_sha256(contract)
    manifest = _load(MANIFEST)
    wheel_lock = _load(WHEEL_LOCK)
    installed = {
        str(item["name"]).lower().replace("_", "-"): str(item["version"])
        for item in wheel_lock["wheels"]
    }
    installed.update({"pip": "24.3.1", "setuptools": "75.6.0"})

    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text(
        json.dumps(
            {
                "schema_version": "paper2-repo-bootstrap-v3",
                "verdict": "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
                "exit_status": 0,
                "expected_repo_sha": expected_sha,
                "observed_repo_sha": expected_sha,
                "observed_repo_tree": repair.SOURCE_SUBJECT_TREE,
                "repo_path": str(ROOT),
                "github_remote": "https://github.com/SzeChunYiu/RAKL.git",
                "checkout_clean": True,
                "detached_head": True,
                "jobs_submitted": 0,
                "model_execution_performed": False,
                "evaluated_result_record_count": 0,
            }
        ),
        encoding="utf-8",
    )
    submission = {
        "schema_version": "paper2-cpu-staging-submission-receipt-v3.2",
        "verdict": "SUBMITTED_TWO_PHASE_STAGING",
        "submitted_job_ids": jobs,
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_sha,
        "observed_repo_sha": expected_sha,
        "failures": [],
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
        "bootstrap_receipt_path": str(bootstrap),
        "bootstrap_receipt_sha256": _sha(bootstrap),
    }
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    receipt_root = tmp_path / "receipts"
    failure_root = tmp_path / "failures"
    final_root = tmp_path / "assets/paper2-cpu-v3-2"
    receipt_root.mkdir()
    failure_root.mkdir()
    final_root.mkdir(parents=True)
    probe_path = receipt_root / f"network-probe-{jobs[0]}.json"
    probe_path.write_text(
        json.dumps(
            {
                "schema_version": "paper2-cpu-staging-network-probe-receipt-v3.2",
                "verdict": "NETWORK_PROBE_PASS",
                "contract_canonical_sha256": contract_sha,
                "expected_repo_sha": expected_sha,
                "observed_repo_sha": expected_sha,
                "slurm_job_id": jobs[0],
                "observations": [
                    {
                        "artifact_id": item["artifact_id"],
                        "http_status": 200,
                        "reachable": True,
                    }
                    for item in manifest["artifacts"]
                ],
                "failures": [],
                "model_execution_performed": False,
                "evaluated_result_record_count": 0,
            }
        ),
        encoding="utf-8",
    )
    candidate = final_root.parent / f".{final_root.name}-candidate-{jobs[1]}"
    equality_lines = [
        f"{name}=={version}"
        for name, version in installed.items()
        if name not in repair._BUNDLED_FREEZE_DIRECT_REFERENCES
    ]
    equality_lines.extend(repair._BUNDLED_FREEZE_DIRECT_REFERENCES.values())
    stage = {
        "schema_version": "paper2-cpu-staging-result-receipt-v3.2",
        "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_sha,
        "probe_receipt_path": str(probe_path),
        "probe_receipt_sha256": _sha(probe_path),
        "probe_slurm_job_id": jobs[0],
        "slurm_job_id": jobs[1],
        "repository_attestation": {
            "repo_sha": expected_sha,
            "repo_tree_sha": repair.SOURCE_SUBJECT_TREE,
            "checkout_clean": True,
            "construction_parent_sha": contract["construction_parent_sha"],
            "construction_parent_ancestor": True,
        },
        "failures": [],
        "candidate_path": str(candidate),
        "final_path": str(final_root),
        "artifact_count": 38,
        "observed_files": [
            {
                "artifact_id": item["artifact_id"],
                "path": item["destination"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }
            for item in manifest["artifacts"]
        ],
        "installed_versions": frozen._EXPECTED_RUNTIME,
        "installed_distributions": installed,
        "pip_check_returncode": 0,
        "pip_check_stdout": "No broken requirements found.",
        "pip_freeze_all": equality_lines,
        "torch_cpu_smoke": {"version": "2.8.0+cpu", "cuda": None, "device": "cpu"},
        "standalone_python_smoke": {
            "version": "3.11.13",
            "executable": str(candidate / "runtime/python/bin/python3.11"),
        },
        "platform_receipt": {"architecture": "x86_64"},
        "fs9_disk_usage_before_staging": {
            "total": 10_000_000_000,
            "used": 2_000_000_000,
            "free": 8_000_000_000,
        },
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    stage_path = final_root / "staging_receipt.json"
    stage_path.write_text(json.dumps(stage), encoding="utf-8")
    rows = [
        {
            "elapsed": "00:00:04",
            "exit_code": "0:0",
            "job_id": jobs[0],
            "max_rss": "",
            "node_list": "cn004",
            "state": "COMPLETED",
        },
        {
            "elapsed": "00:02:05",
            "exit_code": "0:0",
            "job_id": jobs[1],
            "max_rss": "",
            "node_list": "cn004",
            "state": "COMPLETED",
        },
    ]
    prior = {
        "schema_version": "paper2-cpu-staging-harvest-receipt-v3.2",
        "verdict": "HARVEST_CANNOT_CHECK",
        "failures": ["staging_job_or_receipt_failed"],
        "job_ids": jobs,
        "scheduler_rows": rows,
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_sha,
        "bootstrap_receipt_path": str(bootstrap),
        "bootstrap_receipt_sha256": _sha(bootstrap),
        "submission_receipt_sha256": _sha(submission_path),
        "probe_receipt_sha256": _sha(probe_path),
        "staging_receipt_sha256": _sha(stage_path),
        "failure_receipt_sha256": None,
        "negative_history_preserved": False,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    prior_path = tmp_path / "prior-harvest.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    return {
        "contract": contract,
        "submission": submission,
        "submission_path": submission_path,
        "prior": prior,
        "prior_path": prior_path,
        "bound_submission_sha": _sha(submission_path),
        "bound_prior_sha": _sha(prior_path),
        "receipt_root": receipt_root,
        "failure_root": failure_root,
        "final_root": final_root,
        "stage": stage,
        "stage_path": stage_path,
        "rows": rows,
        "runner_rows": "\n".join(
            "|".join(
                row[key]
                for key in ("job_id", "state", "exit_code", "elapsed", "max_rss", "node_list")
            )
            for row in rows
        )
        + "\n",
        "path_map": {
            str(contract["receipt_root"]): receipt_root,
            str(contract["failure_root"]): failure_root,
            str(contract["final_root"]): final_root,
        },
    }


def _harvest(case: dict[str, Any]) -> dict[str, Any]:
    def runner(_argv: list[str], **_: object) -> object:
        return type("Completed", (), {"stdout": case["runner_rows"]})()

    return repair.build_harvest_repair_receipt(
        repair_contract=_load(REPAIR_CONTRACT),
        repair_repository_root=ROOT,
        expected_repair_sha="d" * 40,
        source_contract=case["contract"],
        source_repository_root=ROOT,
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        prior_harvest_receipt_path=case["prior_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
        source_git_observer=lambda _root: (
            case["submission"]["expected_repo_sha"],
            True,
        ),
        repair_git_observer=lambda _root: ("d" * 40, True),
        path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
        binding_sha_observer=lambda _contract, role: {
            "native_submission": case["bound_submission_sha"],
            "native_harvest_cannot_check": case["bound_prior_sha"],
        }.get(role),
    )


def test_v3_2_1_reharvest_accepts_complete_known_answer_and_schema(tmp_path: Path) -> None:
    case = _positive_fixture(tmp_path)
    receipt = _harvest(case)
    assert receipt["verdict"] == "HARVEST_STAGING_PASS", receipt["failures"]
    assert receipt["failures"] == []
    assert receipt["repair_id"] == repair.REPAIR_ID
    assert receipt["prior_harvest_receipt_sha256"] == _sha(case["prior_path"])
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(
        ROOT / "schemas/paper2-cpu-staging-harvest-receipt-v3-2-1.schema.json"
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(receipt)

    repeat = _harvest(case)
    assert repeat["reproduced_v3_2_harvest_canonical_sha256"] == receipt[
        "reproduced_v3_2_harvest_canonical_sha256"
    ]


@pytest.mark.parametrize(
    "mutation",
    ["pip_hash", "setuptools_url", "generic_direct_reference", "prior_verdict"],
)
def test_v3_2_1_reharvest_rejects_mutated_direct_refs_or_prior_lineage(
    tmp_path: Path, mutation: str
) -> None:
    case = _positive_fixture(tmp_path)
    if mutation == "prior_verdict":
        case["prior"]["verdict"] = "HARVEST_STAGING_PASS"
        case["prior_path"].write_text(json.dumps(case["prior"]), encoding="utf-8")
    else:
        stage = copy.deepcopy(case["stage"])
        target = "pip" if mutation != "setuptools_url" else "setuptools"
        exact = repair._BUNDLED_FREEZE_DIRECT_REFERENCES[target]
        if mutation == "pip_hash":
            replacement = exact[:-1] + ("0" if exact[-1] != "0" else "1")
        elif mutation == "setuptools_url":
            replacement = exact.replace("file:///build/", "file:///other/", 1)
        else:
            replacement = "pip @ https://example.invalid/pip.whl"
        stage["pip_freeze_all"] = [
            replacement if line == exact else line for line in stage["pip_freeze_all"]
        ]
        case["stage_path"].write_text(json.dumps(stage), encoding="utf-8")
        case["prior"]["staging_receipt_sha256"] = _sha(case["stage_path"])
        case["prior_path"].write_text(json.dumps(case["prior"]), encoding="utf-8")
    receipt = _harvest(case)
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert receipt["model_execution_performed"] is False


def test_v3_2_1_rejects_wrong_subject_job_and_exact_prior_bytes(tmp_path: Path) -> None:
    for mutation in ("subject", "jobs", "prior_timestamp"):
        case = _positive_fixture(tmp_path / mutation)
        if mutation == "subject":
            case["submission"]["expected_repo_sha"] = "0" * 40
            case["submission_path"].write_text(json.dumps(case["submission"]), encoding="utf-8")
            case["bound_submission_sha"] = _sha(case["submission_path"])
        elif mutation == "jobs":
            case["submission"]["submitted_job_ids"] = ["3475124", "3475123"]
            case["submission_path"].write_text(json.dumps(case["submission"]), encoding="utf-8")
            case["bound_submission_sha"] = _sha(case["submission_path"])
        else:
            case["prior"]["created_at_utc"] = "2099-01-01T00:00:00Z"
            case["prior_path"].write_text(json.dumps(case["prior"]), encoding="utf-8")
        receipt = _harvest(case)
        assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
        assert receipt["failures"]


def test_v3_2_1_cannot_check_world_still_validates_schema(tmp_path: Path) -> None:
    case = _positive_fixture(tmp_path)
    case["stage_path"].unlink()
    receipt = _harvest(case)
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert receipt["staging_receipt_sha256"] is None
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(
        ROOT / "schemas/paper2-cpu-staging-harvest-receipt-v3-2-1.schema.json"
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(receipt)


def test_pre_reharvest_synthesis_derives_exact_cumulative_counts_and_schema() -> None:
    receipt = _load(SYNTHESIS)
    submissions = receipt["cumulative_source_submissions"]
    assert [item["generation"] for item in submissions] == ["v3", "v3.1", "v3.2"]
    assert sum(len(item["job_ids"]) for item in submissions) == 6
    assert sum(item["model_executions"] for item in submissions) == 0
    assert sum(item["evaluated_result_records"] for item in submissions) == 0
    assert receipt["cumulative_native_staging_counts"] == {
        "jobs_submitted": 6,
        "model_executions": 0,
        "evaluated_result_records": 0,
    }
    for item in [*receipt["native_evidence"], *submissions]:
        assert _sha(ROOT / item["path"]) == item["sha256"]
    schema_path = ROOT / receipt["schema_binding"]["path"]
    assert _sha(schema_path) == receipt["schema_binding"]["sha256"]
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(
        _load(schema_path), format_checker=jsonschema.FormatChecker()
    ).validate(receipt)


def test_main_refuses_output_inside_repair_checkout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    args = argparse.Namespace(
        repair_repo=ROOT,
        source_repo=source,
        receipt_output=ROOT / "protected-output.json",
        receipt_root=tmp_path / "receipts",
        final_root=tmp_path / "final",
        failure_root=tmp_path / "failures",
    )
    with pytest.raises(ValueError, match="outside every protected"):
        repair._main(args)


def test_internal_review_receipt_is_schema_valid_and_exactly_bound() -> None:
    review = _load(INTERNAL_REVIEW)
    assert review["blocking_concerns"] == []
    assert review["verdict"] == "PASS__HARVEST_REPAIR_READY_NOT_REHARVESTED"
    for item in review["reviewed_artifacts"]:
        assert _sha(ROOT / item["path"]) == item["sha256"]
    schema_path = ROOT / review["schema_binding"]["path"]
    assert _sha(schema_path) == review["schema_binding"]["sha256"]
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(
        _load(schema_path), format_checker=jsonschema.FormatChecker()
    ).validate(review)
