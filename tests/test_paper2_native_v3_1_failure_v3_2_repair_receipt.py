from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tarfile

import rakl.paper2_cpu_staging_v3_2 as staging


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "research/paper2_microtrial_v3/"
    "PAPER2_NATIVE_V3_1_FAILURE_V3_2_REPAIR_RECEIPT_20260811.json"
)
CONTRACT_V3_1 = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_1.json"
CONTRACT_V3_2 = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json"
SUBJECT = "9d6ee25c9526cdf604bfeb727eeb6e1870cae16f"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def test_v3_1_failure_receipt_binds_all_native_bytes_and_chronology() -> None:
    receipt = _load(RECEIPT)
    expected = {
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_V3_1_9D6EE25.json": "94badee3fca190c3f208a7ca36ccfb16b56082e8a35c294e3c6472b584e305e6",
        "research/paper2_microtrial_v3/native_receipts/SUBMISSION_NATIVE_V3_1_9D6EE25.json": "156921b1624923208dfa3f0499a1dcaff3b274e80fe52e6deb4b864599935527",
        "research/paper2_microtrial_v3/native_receipts/NETWORK_PROBE_NATIVE_V3_1_JOB_3475098.json": "7f833e74ce1765fa516d80f3260341605ba9a04eb792803e39f0bc9c6738e151",
        "research/paper2_microtrial_v3/native_receipts/STAGING_FAILURE_NATIVE_V3_1_JOB_3475099.json": "29ff6fd6c0a1da2f4034fe141b012b5a4ce350e7974ca42c43b808175a5b3908",
        "research/paper2_microtrial_v3/native_receipts/HARVEST_NATIVE_V3_1_JOBS_3475098_3475099.json": "3945f8100096df4d97792645885dedb5ad8a258faf28bf852df3c23197f895d7",
        "research/paper2_microtrial_v3/native_receipts/SACCT_NATIVE_V3_1_JOBS_3475098_3475099.json": "604aa811ccbccd82e49183f1e16552cece5abf8d2bf9bba6d5a0160dada192b3",
        "research/paper2_microtrial_v3/native_receipts/ARCHIVE_OBSERVATION_NATIVE_V3_1_JOB_3475099.json": "6ee12c477c47c800f56625056ebcc72a3178e0cbe5dfae5e344df441711a35fc",
        "research/paper2_microtrial_v3/native_logs/NETWORK_PROBE_V3_1_JOB_3475098.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "research/paper2_microtrial_v3/native_logs/STAGE_CPU_V3_1_JOB_3475099.out": "9ee9666b49ddfa07894332aef352b24ae514718639edb17135a3af22e4ace1ae",
        "research/paper2_microtrial_v3/native_bundles/PAPER2_STAGE_NEGATIVE_V3_1_JOBS_3475098_3475099.tar.gz": "346931ebdc60036afc727707664776845187c306b2d5aedd99f88d96e2d82994",
    }
    bound = {item["path"]: item["sha256"] for item in receipt["native_receipts_and_raw_evidence"]}
    assert bound == expected
    for relative, digest in expected.items():
        assert _sha256(ROOT / relative) == digest

    chronology = receipt["chronology"]
    times = [datetime.fromisoformat(item["created_or_observed_at_utc"].replace("Z", "+00:00")) for item in chronology]
    assert times == sorted(times)
    assert [item["event"] for item in chronology] == [
        "bootstrap",
        "submission",
        "network_probe",
        "staging_failure",
        "harvest",
        "read_only_archive_observation",
        "v3_2_contract_freeze",
    ]


def test_v3_1_native_scheduler_failure_and_archive_observation_are_exact() -> None:
    receipt = _load(RECEIPT)
    source_dir = ROOT / "research/paper2_microtrial_v3/native_receipts"
    submission = _load(source_dir / "SUBMISSION_NATIVE_V3_1_9D6EE25.json")
    probe = _load(source_dir / "NETWORK_PROBE_NATIVE_V3_1_JOB_3475098.json")
    failure = _load(source_dir / "STAGING_FAILURE_NATIVE_V3_1_JOB_3475099.json")
    harvest = _load(source_dir / "HARVEST_NATIVE_V3_1_JOBS_3475098_3475099.json")
    raw_sacct = _load(source_dir / "SACCT_NATIVE_V3_1_JOBS_3475098_3475099.json")
    archive_source = _load(source_dir / "ARCHIVE_OBSERVATION_NATIVE_V3_1_JOB_3475099.json")
    assert receipt["subject_sha"] == SUBJECT
    assert submission["submitted_job_ids"] == ["3475098", "3475099"]
    assert probe["slurm_job_id"] == submission["submitted_job_ids"][0]
    assert failure["slurm_job_id"] == submission["submitted_job_ids"][1]
    assert harvest["job_ids"] == submission["submitted_job_ids"]
    assert receipt["scheduler_result"] == {
        "account": "lu2026-2-51",
        "partition": "lu48",
        "rows": [
            {"elapsed": "00:00:05", "exit_code": "0:0", "job_id": "3475098", "max_rss": "", "node_list": "cn004", "state": "COMPLETED"},
            {"elapsed": "00:00:18", "exit_code": "2:0", "job_id": "3475099", "max_rss": "", "node_list": "cn004", "state": "FAILED"},
        ],
    }
    native = receipt["native_result"]
    assert native["probe_job_id"] == "3475098"
    assert native["probe_observation_count"] == 38
    assert native["probe_all_reachable"] is True
    assert native["staging_job_id"] == "3475099"
    assert native["staging_verdict"] == "STAGING_FAILED_PRESERVED"
    assert native["error_detail"] == "archive unsafe member:python/bin/2to3"
    assert native["candidate_preserved"] is True
    assert native["final_exists"] is False
    assert native["error_type"] == failure["error_type"]
    assert native["error_detail"] == failure["error_detail"]
    assert native["candidate_path"] == failure["candidate_path"]
    assert native["candidate_preserved"] == failure["candidate_preserved"]
    assert native["final_path"] == failure["final_path"]
    assert native["final_exists"] == failure["final_exists"]
    assert native["harvest_verdict"] == harvest["verdict"]
    assert len(probe["observations"]) == 38
    assert len({item["artifact_id"] for item in probe["observations"]}) == 38
    assert all(item["reachable"] is True and item["http_status"] == 200 for item in probe["observations"])

    root_jobs = {str(item["job_id"]): item for item in raw_sacct["jobs"]}
    assert set(root_jobs) == {"3475098", "3475099"}
    derived_rows = []
    for job_id in submission["submitted_job_ids"]:
        job = root_jobs[job_id]
        code = job["exit_code"]["return_code"]["number"]
        signal = job["exit_code"]["signal"]["id"]["number"]
        derived_rows.append(
            {
                "elapsed": f"00:00:{job['time']['elapsed']:02d}",
                "exit_code": f"{code}:{signal}",
                "job_id": job_id,
                "max_rss": "",
                "node_list": job["nodes"],
                "state": job["state"]["current"][0],
            }
        )
    assert receipt["scheduler_result"]["rows"] == harvest["scheduler_rows"] == derived_rows
    assert receipt["scheduler_result"]["account"] == root_jobs["3475098"]["association"]["account"]
    assert receipt["scheduler_result"]["partition"] == root_jobs["3475098"]["association"]["partition"]

    observation = receipt["archive_observation"]
    for key, value in observation.items():
        assert archive_source[key] == value
    assert observation["artifact_count"] == observation["identity_matching_artifact_count"] == 38
    assert observation["archive_member_count"] == 5400
    assert observation["regular_file_count"] == 4352
    assert observation["symlink_count"] == 1048
    assert observation["parent_relative_link_count"] == 300
    assert observation["hardlink_count"] == observation["special_member_count"] == 0
    assert observation["all_link_targets_exist"] is True
    assert observation["all_link_targets_are_regular_files"] is True
    assert observation["all_link_targets_resolve_inside_archive_root"] is True
    assert observation["candidate_mutation_performed"] is False
    assert observation["jobs_submitted_by_observation"] == 0
    manifest = _load(ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json")
    expected_artifacts = {
        item["artifact_id"]: (item["bytes"], item["sha256"])
        for item in manifest["artifacts"]
    }
    observed_artifacts = {
        item["artifact_id"]: (item["observed_bytes"], item["observed_sha256"])
        for item in archive_source["artifact_observations"]
    }
    assert observed_artifacts == expected_artifacts


def test_v3_1_chronology_and_bundle_are_derived_from_exact_source_bytes() -> None:
    receipt = _load(RECEIPT)
    source_dir = ROOT / "research/paper2_microtrial_v3/native_receipts"
    sources = [
        (_load(source_dir / "BOOTSTRAP_NATIVE_V3_1_9D6EE25.json"), "observed_at_utc"),
        (_load(source_dir / "SUBMISSION_NATIVE_V3_1_9D6EE25.json"), "created_at_utc"),
        (_load(source_dir / "NETWORK_PROBE_NATIVE_V3_1_JOB_3475098.json"), "created_at_utc"),
        (_load(source_dir / "STAGING_FAILURE_NATIVE_V3_1_JOB_3475099.json"), "created_at_utc"),
        (_load(source_dir / "HARVEST_NATIVE_V3_1_JOBS_3475098_3475099.json"), "created_at_utc"),
        (_load(source_dir / "ARCHIVE_OBSERVATION_NATIVE_V3_1_JOB_3475099.json"), "created_at_utc"),
        (_load(CONTRACT_V3_2), "created_at_utc"),
    ]
    assert [item["created_or_observed_at_utc"] for item in receipt["chronology"]] == [
        source[field] for source, field in sources
    ]

    bundle = ROOT / "research/paper2_microtrial_v3/native_bundles/PAPER2_STAGE_NEGATIVE_V3_1_JOBS_3475098_3475099.tar.gz"
    members = {
        "receipts/v3_1/bootstrap-9d6ee25c9526cdf604bfeb727eeb6e1870cae16f.json": source_dir / "BOOTSTRAP_NATIVE_V3_1_9D6EE25.json",
        "receipts/v3_1/submission-9d6ee25c9526cdf604bfeb727eeb6e1870cae16f.json": source_dir / "SUBMISSION_NATIVE_V3_1_9D6EE25.json",
        "receipts/v3_1/network-probe-3475098.json": source_dir / "NETWORK_PROBE_NATIVE_V3_1_JOB_3475098.json",
        "failures/v3_1/staging-failed-3475099.json": source_dir / "STAGING_FAILURE_NATIVE_V3_1_JOB_3475099.json",
        "receipts/v3_1/harvest-3475098-3475099.json": source_dir / "HARVEST_NATIVE_V3_1_JOBS_3475098_3475099.json",
        "logs/network_probe_v3_1_3475098.out": ROOT / "research/paper2_microtrial_v3/native_logs/NETWORK_PROBE_V3_1_JOB_3475098.out",
        "logs/stage_cpu_v3_1_3475099.out": ROOT / "research/paper2_microtrial_v3/native_logs/STAGE_CPU_V3_1_JOB_3475099.out",
    }
    with tarfile.open(bundle, "r:gz") as archive:
        assert set(archive.getnames()) == set(members)
        for member_name, source_path in members.items():
            extracted = archive.extractfile(member_name)
            assert extracted is not None
            assert extracted.read() == source_path.read_bytes()


def test_v3_1_negative_history_is_immutable_and_v3_2_is_exactly_bound() -> None:
    receipt = _load(RECEIPT)
    v3_1 = _load(CONTRACT_V3_1)
    protected = receipt["protected_v3_1_negative_history"]
    assert protected["contract_file_sha256"] == _sha256(CONTRACT_V3_1)
    assert protected["contract_canonical_sha256"] == _canonical(v3_1)
    assert protected["runtime_sha256"] == _sha256(ROOT / protected["runtime_path"])
    assert protected["v3_1_contract_mutated_for_repair"] is False
    assert protected["failed_candidate_superseded_or_deleted"] is False

    repair = receipt["v3_2_repair"]
    contract = _load(CONTRACT_V3_2)
    assert staging.validate_staging_contract(contract, repository_root=ROOT) == ()
    assert repair["contract_file_sha256"] == _sha256(CONTRACT_V3_2)
    assert repair["contract_canonical_sha256"] == _canonical(contract)
    assert repair["contract_self_canonical_zeroed_sha256"] == staging._contract_self_sha256(contract)
    assert repair["bindings"] == contract["bindings"]
    for binding in contract["bindings"]:
        if binding["role"] != "contract_self":
            assert _sha256(ROOT / binding["path"]) == binding["sha256"]
    changed = copy.deepcopy(contract)
    next(item for item in changed["bindings"] if item["role"] == "contract_self")["sha256"] = "0" * 64
    assert "contract_binding_hash_mismatch:contract_self" in staging.validate_staging_contract(
        changed, repository_root=ROOT
    )


def test_v3_2_zero_submission_result_boundary_and_claim_narrowing() -> None:
    receipt = _load(RECEIPT)
    assert _sha256(ROOT / receipt["schema_binding"]["path"]) == receipt["schema_binding"]["sha256"]
    assert receipt["execution_counts_this_retry"] == {
        "evaluated_result_records": 0,
        "jobs_submitted": 2,
        "model_executions": 0,
    }
    assert receipt["cumulative_native_staging_counts"] == {
        "evaluated_result_records": 0,
        "jobs_submitted": 4,
        "model_executions": 0,
    }
    repair = receipt["v3_2_repair"]
    assert repair["operator_state"] == "REPAIR_READY_NOT_SUBMITTED"
    assert repair["native_submission_performed"] is False
    assert repair["native_result_available"] is False
    assert receipt["manuscript_status"]["quantitative_figure_generated"] is False
    assert _sha256(ROOT / receipt["manuscript_status"]["path"]) == receipt["manuscript_status"]["sha256"]
    assert receipt["verdict"] == "NATIVE_V3_1_STAGING_FAILURE_PRESERVED__V3_2_REPAIR_READY_NOT_SUBMITTED"
    boundary = receipt["claim_boundary"].lower()
    assert "not v3.2 native staging success" in boundary
    for forbidden_promotion in (
        "execution packet",
        "independent review",
        "peer review",
        "acceptance",
        "publication",
    ):
        assert forbidden_promotion in boundary
