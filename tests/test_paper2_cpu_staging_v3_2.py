from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
from typing import Any

import pytest

import rakl.paper2_cpu_staging_v3_2 as staging


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3_2.json"
OBSERVATION = (
    ROOT
    / "research/paper2_microtrial_v3/native_receipts/"
    "ARCHIVE_OBSERVATION_NATIVE_V3_1_JOB_3475099.json"
)
SCRIPTS = ROOT / "experiments/paper2/lunarc"
SCHEMAS = ROOT / "schemas"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tar(path: Path, members: list[dict[str, Any]]) -> None:
    with tarfile.open(path, "w:gz") as bundle:
        for spec in members:
            info = tarfile.TarInfo(spec["name"])
            info.type = spec.get("type", tarfile.REGTYPE)
            info.mode = spec.get("mode", 0o755)
            info.linkname = spec.get("linkname", "")
            payload = spec.get("payload", b"")
            info.size = len(payload) if info.type in {tarfile.REGTYPE, tarfile.AREGTYPE} else 0
            bundle.addfile(info, io.BytesIO(payload) if info.size else None)


def test_v3_2_contract_is_self_bound_and_binds_exact_v3_1_archive_observation() -> None:
    contract = _load(CONTRACT)
    assert staging.validate_staging_contract(contract, repository_root=ROOT) == ()
    assert contract["contract_id"] == "PAPER2_CPU_STAGING_V3_2"
    assert contract["supersedes_contract_id"] == "PAPER2_CPU_STAGING_V3_1"
    assert contract["predecessor_failure"] == {
        "contract_id": "PAPER2_CPU_STAGING_V3_1",
        "probe_job_id": "3475098",
        "staging_job_id": "3475099",
        "staging_verdict": "STAGING_FAILED_PRESERVED",
        "error_type": "ValueError",
        "error_detail": "archive unsafe member:python/bin/2to3",
        "preserved_candidate_path": "/projects/hep/fs9/users/scyiu/RAKL-paper2/assets/.paper2-cpu-v3-1-candidate-3475099",
        "archive_observation_verdict": "ALL_38_ARTIFACTS_EXACT__ARCHIVE_RELATIVE_LINK_POLICY_MISMATCH_LOCALIZED",
    }
    observation_binding = next(
        item for item in contract["bindings"] if item["role"] == "archive_observation"
    )
    assert observation_binding["path"] == str(OBSERVATION.relative_to(ROOT))
    assert observation_binding["sha256"] == hashlib.sha256(OBSERVATION.read_bytes()).hexdigest()
    observation = _load(OBSERVATION)
    assert observation["staging_job_id"] == "3475099"
    assert observation["archive_sha256"] == staging._EXPECTED_PYTHON["sha256"]
    assert observation["symlink_count"] == 1048
    assert observation["parent_relative_link_count"] == 300
    assert observation["hardlink_count"] == 0
    assert observation["special_member_count"] == 0
    self_binding = next(item for item in contract["bindings"] if item["role"] == "contract_self")
    assert self_binding["path"] == str(CONTRACT.relative_to(ROOT))
    assert self_binding["sha256"] == staging._contract_self_sha256(contract)
    for field in ("candidate_root", "final_root", "receipt_root", "failure_root"):
        assert "v3-2" in contract[field] or "v3_2" in contract[field]
    assert contract["model_execution_permitted"] is False
    assert contract["submission_policy"]["default_operator_mode"] == "READY_NOT_SUBMITTED"


def test_v3_2_contract_and_all_bound_bytes_fail_closed() -> None:
    contract = _load(CONTRACT)
    changed = copy.deepcopy(contract)
    changed["repair_boundary"] += " mutation"
    assert "contract_binding_hash_mismatch:contract_self" in staging.validate_staging_contract(
        changed, repository_root=ROOT
    )
    changed = copy.deepcopy(contract)
    next(item for item in changed["bindings"] if item["role"] == "archive_observation")[
        "sha256"
    ] = "0" * 64
    assert "contract_binding_hash_mismatch:archive_observation" in staging.validate_staging_contract(
        changed, repository_root=ROOT
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("artifact_count", 37),
        ("identity_matching_artifact_count", 37),
        ("candidate_exists", False),
        ("final_exists", True),
        ("all_link_targets_resolve_inside_archive_root", False),
        ("all_link_targets_exist", False),
        ("all_link_targets_are_regular_files", False),
        ("candidate_mutation_performed", True),
        ("jobs_submitted_by_observation", 1),
    ],
)
def test_v3_2_archive_observation_semantic_mutations_fail_closed(
    tmp_path: Path, field: str, value: object
) -> None:
    contract = copy.deepcopy(_load(CONTRACT))
    for binding in contract["bindings"]:
        source = ROOT / binding["path"]
        target = tmp_path / binding["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    observation_binding = next(
        item for item in contract["bindings"] if item["role"] == "archive_observation"
    )
    observation_path = tmp_path / observation_binding["path"]
    observation = _load(observation_path)
    observation[field] = value
    observation_path.write_text(json.dumps(observation, sort_keys=True) + "\n", encoding="utf-8")
    observation_binding["sha256"] = hashlib.sha256(observation_path.read_bytes()).hexdigest()
    self_binding = next(item for item in contract["bindings"] if item["role"] == "contract_self")
    self_binding["sha256"] = staging._contract_self_sha256(contract)
    assert "archive_observation_lineage_invalid" in staging.validate_staging_contract(
        contract, repository_root=tmp_path
    )


def test_v3_2_contract_and_receipt_schemas_are_valid() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema_names = [
        "paper2-cpu-staging-contract-v3-2.schema.json",
        "paper2-cpu-staging-construction-receipt-v3-2.schema.json",
        "paper2-cpu-staging-submission-receipt-v3-2.schema.json",
        "paper2-cpu-staging-network-probe-receipt-v3-2.schema.json",
        "paper2-cpu-staging-result-receipt-v3-2.schema.json",
        "paper2-cpu-staging-harvest-receipt-v3-2.schema.json",
        "paper2-cpu-staging-archive-observation-v3-1.schema.json",
        "paper2-repo-bootstrap-v3.schema.json",
        "paper2-native-v3-1-failure-v3-2-repair-receipt.schema.json",
    ]
    for name in schema_names:
        jsonschema.Draft202012Validator.check_schema(_load(SCHEMAS / name))
    contract = _load(CONTRACT)
    jsonschema.Draft202012Validator(
        _load(SCHEMAS / schema_names[0]), format_checker=jsonschema.FormatChecker()
    ).validate(contract)
    for binding in contract["bindings"]:
        if binding["role"] != "contract_self":
            assert hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest() == binding[
                "sha256"
            ]
    schema_instances = [
        (
            "paper2-cpu-staging-archive-observation-v3-1.schema.json",
            OBSERVATION,
        ),
        (
            "paper2-repo-bootstrap-v3.schema.json",
            ROOT
            / "research/paper2_microtrial_v3/native_receipts/"
            "BOOTSTRAP_NATIVE_V3_1_9D6EE25.json",
        ),
        (
            "paper2-native-v3-1-failure-v3-2-repair-receipt.schema.json",
            ROOT
            / "research/paper2_microtrial_v3/"
            "PAPER2_NATIVE_V3_1_FAILURE_V3_2_REPAIR_RECEIPT_20260811.json",
        ),
    ]
    for schema_name, instance_path in schema_instances:
        jsonschema.Draft202012Validator(
            _load(SCHEMAS / schema_name), format_checker=jsonschema.FormatChecker()
        ).validate(_load(instance_path))


def test_v3_2_positive_receipt_schemas_reject_empty_or_contradictory_claims() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    common = {
        "created_at_utc": "2026-08-11T01:00:00Z",
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    counterexamples = [
        (
            "paper2-cpu-staging-network-probe-receipt-v3-2.schema.json",
            {
                **common,
                "schema_version": "paper2-cpu-staging-network-probe-receipt-v3.2",
                "observed_repo_sha": "c" * 40,
                "slurm_job_id": "51001",
                "observations": [],
                "failures": ["fabricated"],
                "verdict": "NETWORK_PROBE_PASS",
            },
        ),
        (
            "paper2-cpu-staging-submission-receipt-v3-2.schema.json",
            {
                **common,
                "schema_version": "paper2-cpu-staging-submission-receipt-v3.2",
                "observed_repo_sha": "c" * 40,
                "submitted_job_ids": [],
                "failures": [],
                "verdict": "SUBMITTED_TWO_PHASE_STAGING",
            },
        ),
        (
            "paper2-cpu-staging-result-receipt-v3-2.schema.json",
            {
                **common,
                "schema_version": "paper2-cpu-staging-result-receipt-v3.2",
                "slurm_job_id": "51002",
                "failures": ["no artifacts or attestations"],
                "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
            },
        ),
        (
            "paper2-cpu-staging-harvest-receipt-v3-2.schema.json",
            {
                **common,
                "schema_version": "paper2-cpu-staging-harvest-receipt-v3.2",
                "submission_receipt_sha256": "a" * 64,
                "job_ids": [],
                "scheduler_rows": [],
                "probe_receipt_sha256": None,
                "staging_receipt_sha256": None,
                "failure_receipt_sha256": None,
                "failures": [],
                "negative_history_preserved": False,
                "verdict": "HARVEST_STAGING_PASS",
            },
        ),
    ]
    for schema_name, counterexample in counterexamples:
        validator = jsonschema.Draft202012Validator(
            _load(SCHEMAS / schema_name), format_checker=jsonschema.FormatChecker()
        )
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(counterexample)


def test_v3_2_operator_scripts_are_distinct_staging_only_and_default_dry_run() -> None:
    names = [
        "network_probe_v3_2.sbatch",
        "stage_cpu_assets_v3_2.sbatch",
        "submit_cpu_staging_v3_2.sh",
        "harvest_cpu_staging_v3_2.sh",
    ]
    texts = {name: (SCRIPTS / name).read_text(encoding="utf-8") for name in names}
    combined = "\n".join(texts.values())
    assert "rakl.paper2_cpu_staging_v3_2" in combined
    assert "CPU_STAGING_CONTRACT_V3_2.json" in combined
    assert "/receipts/v3_2" in combined
    assert "/failures/v3_2" in combined
    assert "paper2-cpu-v3-2" in combined
    assert "--dependency=afterok" not in texts["submit_cpu_staging_v3_2.sh"]
    assert not any(
        token in combined
        for token in ("AutoModel", "generate(", "execute_microtrial", "paper2_pendulum_microtrial run")
    )


def test_v3_2_default_submission_records_zero_jobs_models_and_results(tmp_path: Path) -> None:
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
                "github_remote": "https://github.com/SzeChunYiu/RAKL.git",
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
    jsonschema.Draft202012Validator(
        _load(SCHEMAS / "paper2-cpu-staging-submission-receipt-v3-2.schema.json"),
        format_checker=jsonschema.FormatChecker(),
    ).validate(receipt)


def test_safe_extract_accepts_exact_archive_style_link_chains_and_hardlink(tmp_path: Path) -> None:
    archive = tmp_path / "safe.tar.gz"
    destination = tmp_path / "runtime"
    _tar(
        archive,
        [
            {"name": "python/share/terminfo/i/ibmpc", "payload": b"terminal"},
            {
                "name": "python/share/terminfo/w/wyse60-PC",
                "type": tarfile.SYMTYPE,
                "linkname": "../i/ibmpc",
            },
            {
                "name": "python/share/terminfo/w/wyse60-PC-alias",
                "type": tarfile.SYMTYPE,
                "linkname": "wyse60-PC",
            },
            {
                "name": "python/share/terminfo/w/wyse60-PC-hard",
                "type": tarfile.LNKTYPE,
                "linkname": "python/share/terminfo/i/ibmpc",
            },
            {
                "name": "python/share/terminfo/w/wyse60-PC-hard-chain",
                "type": tarfile.LNKTYPE,
                "linkname": "python/share/terminfo/w/wyse60-PC-alias",
            },
        ],
    )
    staging._safe_extract(archive, destination)
    target = destination / "python/share/terminfo/i/ibmpc"
    first = destination / "python/share/terminfo/w/wyse60-PC"
    second = destination / "python/share/terminfo/w/wyse60-PC-alias"
    hard = destination / "python/share/terminfo/w/wyse60-PC-hard"
    hard_chain = destination / "python/share/terminfo/w/wyse60-PC-hard-chain"
    assert first.is_symlink() and os.readlink(first) == "../i/ibmpc"
    assert second.is_symlink() and os.readlink(second) == "wyse60-PC"
    assert second.read_bytes() == b"terminal"
    assert hard.read_bytes() == b"terminal"
    assert hard.stat().st_ino == target.stat().st_ino
    assert hard_chain.read_bytes() == b"terminal"
    assert hard_chain.stat().st_ino == target.stat().st_ino


def test_safe_extract_accepts_parent_relative_symlink_only_when_it_stays_in_root(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "parent-relative.tar.gz"
    destination = tmp_path / "runtime"
    _tar(
        archive,
        [
            {"name": "root/data/value", "payload": b"ok"},
            {"name": "root/bin/value", "type": tarfile.SYMTYPE, "linkname": "../data/value"},
        ],
    )
    staging._safe_extract(archive, destination)
    link = destination / "root/bin/value"
    assert link.is_symlink()
    assert os.readlink(link) == "../data/value"
    assert link.read_bytes() == b"ok"


def test_safe_extract_preserves_v3_1_write_bit_hardening(tmp_path: Path) -> None:
    archive = tmp_path / "mode.tar.gz"
    destination = tmp_path / "runtime"
    _tar(archive, [{"name": "python/bin/tool", "payload": b"tool", "mode": 0o777}])
    staging._safe_extract(archive, destination)
    assert (destination / "python/bin/tool").stat().st_mode & 0o777 == 0o755


@pytest.mark.parametrize(
    "members",
    [
        [{"name": "/absolute", "payload": b"x"}],
        [{"name": "../../escape", "payload": b"x"}],
        [
            {"name": "target", "payload": b"x"},
            {"name": "link", "type": tarfile.SYMTYPE, "linkname": "/target"},
        ],
        [{"name": "nested/link", "type": tarfile.SYMTYPE, "linkname": "../../escape"}],
        [{"name": "link", "type": tarfile.SYMTYPE, "linkname": "missing"}],
        [
            {"name": "a", "type": tarfile.SYMTYPE, "linkname": "b"},
            {"name": "b", "type": tarfile.SYMTYPE, "linkname": "a"},
        ],
        [
            {"name": "a", "type": tarfile.LNKTYPE, "linkname": "b"},
            {"name": "b", "type": tarfile.LNKTYPE, "linkname": "a"},
        ],
        [
            {"name": "dir/../same", "payload": b"one"},
            {"name": "same", "payload": b"two"},
        ],
        [
            {"name": "ancestor", "type": tarfile.SYMTYPE, "linkname": "target"},
            {"name": "target", "payload": b"safe"},
            {"name": "ancestor/child", "payload": b"unsafe"},
        ],
        [{"name": "device", "type": tarfile.CHRTYPE}],
        [{"name": "fifo", "type": tarfile.FIFOTYPE}],
        [{"name": "unknown", "type": tarfile.CONTTYPE}],
    ],
    ids=[
        "absolute-member",
        "escaping-member",
        "absolute-link",
        "escaping-link",
        "missing-target",
        "link-cycle",
        "hardlink-cycle",
        "duplicate-normalized-name",
        "link-ancestor-collision",
        "device",
        "fifo",
        "unknown-type",
    ],
)
def test_safe_extract_hostile_archive_is_rejected_before_any_write(
    tmp_path: Path, members: list[dict[str, Any]]
) -> None:
    archive = tmp_path / "hostile.tar.gz"
    destination = tmp_path / "runtime"
    _tar(archive, members)
    with pytest.raises(ValueError, match="archive unsafe"):
        staging._safe_extract(archive, destination)
    assert not destination.exists() or list(destination.iterdir()) == []


def _negative_harvest_fixture(tmp_path: Path) -> dict[str, Any]:
    jobs = ["51001", "51002"]
    contract = _load(CONTRACT)
    contract_sha = staging._canonical_sha256(contract)
    expected_sha = "c" * 40
    manifest = _load(ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json")
    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text(
        json.dumps(
            {
                "schema_version": "paper2-repo-bootstrap-v3",
                "verdict": "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
                "exit_status": 0,
                "expected_repo_sha": expected_sha,
                "observed_repo_sha": expected_sha,
                "observed_repo_tree": "b" * 40,
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
        "bootstrap_receipt_sha256": hashlib.sha256(bootstrap.read_bytes()).hexdigest(),
    }
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    receipt_root = tmp_path / "receipts"
    failure_root = tmp_path / "failures"
    final_root = tmp_path / "assets/paper2-cpu-v3-2"
    receipt_root.mkdir()
    failure_root.mkdir()
    final_root.parent.mkdir()
    candidate = final_root.parent / ".paper2-cpu-v3-2-candidate-51002"
    candidate.mkdir()
    probe_path = receipt_root / "network-probe-51001.json"
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
                    {"artifact_id": item["artifact_id"], "http_status": 200, "reachable": True}
                    for item in manifest["artifacts"]
                ],
                "failures": [],
                "model_execution_performed": False,
                "evaluated_result_record_count": 0,
            }
        ),
        encoding="utf-8",
    )
    failed = {
        "schema_version": "paper2-cpu-staging-result-receipt-v3.2",
        "verdict": "STAGING_FAILED_PRESERVED",
        "contract_canonical_sha256": contract_sha,
        "expected_repo_sha": expected_sha,
        "probe_receipt_path": str(probe_path),
        "probe_receipt_sha256": hashlib.sha256(probe_path.read_bytes()).hexdigest(),
        "probe_slurm_job_id": jobs[0],
        "slurm_job_id": jobs[1],
        "failures": ["staging_exception"],
        "error_type": "ValueError",
        "error_detail": "planted failure",
        "candidate_path": str(candidate),
        "candidate_preserved": True,
        "final_path": str(final_root),
        "final_exists": False,
        "model_execution_performed": False,
        "evaluated_result_record_count": 0,
    }
    failure_path = failure_root / "staging-failed-51002.json"
    failure_path.write_text(json.dumps(failed), encoding="utf-8")
    return {
        "submission": submission,
        "contract": contract,
        "submission_path": submission_path,
        "receipt_root": receipt_root,
        "failure_root": failure_root,
        "final_root": final_root,
        "failure_path": failure_path,
        "failed": failed,
        "rows": "51001|COMPLETED|0:0|00:00:06||cn004\n51002|FAILED|2:0|00:00:04||cn004\n",
        "path_map": {
            str(contract["receipt_root"]): receipt_root,
            str(contract["final_root"]): final_root,
            str(contract["failure_root"]): failure_root,
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_job",
        "candidate_not_preserved",
        "candidate_missing",
        "final_exists_mismatch",
        "final_unexpectedly_exists",
        "duplicate_scheduler_row",
    ],
)
def test_v3_2_harvest_preserves_v3_1_cannot_check_hardening(
    tmp_path: Path, mutation: str
) -> None:
    case = _negative_harvest_fixture(tmp_path)
    rows = case["rows"]
    if mutation == "wrong_job":
        case["failed"]["slurm_job_id"] = "99999"
    elif mutation == "candidate_not_preserved":
        case["failed"]["candidate_preserved"] = False
    elif mutation == "candidate_missing":
        Path(case["failed"]["candidate_path"]).rmdir()
    elif mutation == "final_exists_mismatch":
        case["failed"]["final_exists"] = True
    elif mutation == "final_unexpectedly_exists":
        case["final_root"].mkdir()
    elif mutation == "duplicate_scheduler_row":
        rows = "51001|COMPLETED|0:0|00:00:06||cn004\n51001|COMPLETED|0:0|00:00:07||cn005\n"
    case["failure_path"].write_text(json.dumps(case["failed"]), encoding="utf-8")

    def runner(_argv: list[str], **_: object) -> object:
        return type("Completed", (), {"stdout": rows})()

    receipt = staging.build_harvest_receipt(
        contract=case["contract"],
        repository_root=ROOT,
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
        git_observer=lambda _root: (case["submission"]["expected_repo_sha"], True),
        path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
    )
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert receipt["negative_history_preserved"] is False


def test_v3_2_harvest_rejects_fabricated_semantically_empty_pass(tmp_path: Path) -> None:
    case = _negative_harvest_fixture(tmp_path)
    jobs = case["submission"]["submitted_job_ids"]
    probe_path = case["receipt_root"] / f"network-probe-{jobs[0]}.json"
    probe = _load(probe_path)
    probe["observations"] = []
    probe["failures"] = ["fabricated"]
    probe_path.write_text(json.dumps(probe), encoding="utf-8")
    case["final_root"].mkdir()
    (case["final_root"] / "staging_receipt.json").write_text(
        json.dumps(
            {
                "schema_version": "paper2-cpu-staging-result-receipt-v3.2",
                "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
                "contract_canonical_sha256": case["submission"]["contract_canonical_sha256"],
                "expected_repo_sha": case["submission"]["expected_repo_sha"],
                "slurm_job_id": jobs[1],
                "final_path": str(case["final_root"]),
                "failures": ["no artifacts or attestations"],
                "model_execution_performed": False,
                "evaluated_result_record_count": 0,
            }
        ),
        encoding="utf-8",
    )

    def runner(_argv: list[str], **_: object) -> object:
        rows = (
            f"{jobs[0]}|COMPLETED|0:0|00:00:01||cn004\n"
            f"{jobs[1]}|COMPLETED|0:0|00:00:01||cn004\n"
        )
        return type("Completed", (), {"stdout": rows})()

    receipt = staging.build_harvest_receipt(
        contract=case["contract"],
        repository_root=ROOT,
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
        git_observer=lambda _root: (case["submission"]["expected_repo_sha"], True),
        path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
    )
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    assert "network_probe_receipt_invalid" in receipt["failures"]


def test_v3_2_harvest_accepts_only_complete_semantic_pass(tmp_path: Path) -> None:
    case = _negative_harvest_fixture(tmp_path)
    jobs = case["submission"]["submitted_job_ids"]
    case["failure_path"].unlink()
    Path(case["failed"]["candidate_path"]).rmdir()
    case["final_root"].mkdir()
    manifest = _load(ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json")
    wheel_lock = _load(ROOT / "research/paper2_microtrial_v3/CP311_LINUX_X86_64_WHEEL_LOCK_AUDIT.json")
    installed_distributions = {
        str(item["name"]).lower().replace("_", "-"): str(item["version"])
        for item in wheel_lock["wheels"]
    }
    installed_distributions.update({"pip": "24.3.1", "setuptools": "75.6.0"})
    probe_path = case["receipt_root"] / f"network-probe-{jobs[0]}.json"
    expected_candidate = case["final_root"].parent / f".{case['final_root'].name}-candidate-{jobs[1]}"
    stage = {
        "schema_version": "paper2-cpu-staging-result-receipt-v3.2",
        "created_at_utc": "2026-08-11T01:00:00Z",
        "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
        "contract_canonical_sha256": case["submission"]["contract_canonical_sha256"],
        "expected_repo_sha": case["submission"]["expected_repo_sha"],
        "probe_receipt_path": str(probe_path),
        "probe_receipt_sha256": hashlib.sha256(probe_path.read_bytes()).hexdigest(),
        "probe_slurm_job_id": jobs[0],
        "slurm_job_id": jobs[1],
        "repository_attestation": {
            "repo_sha": case["submission"]["expected_repo_sha"],
            "repo_tree_sha": "b" * 40,
            "checkout_clean": True,
            "construction_parent_sha": case["contract"]["construction_parent_sha"],
            "construction_parent_ancestor": True,
        },
        "failures": [],
        "candidate_path": str(expected_candidate),
        "final_path": str(case["final_root"]),
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
        "installed_versions": staging._EXPECTED_RUNTIME,
        "installed_distributions": installed_distributions,
        "pip_check_returncode": 0,
        "pip_check_stdout": "No broken requirements found.",
        "pip_freeze_all": [f"{name}=={version}" for name, version in installed_distributions.items()],
        "torch_cpu_smoke": {"version": "2.8.0+cpu", "cuda": None, "device": "cpu"},
        "standalone_python_smoke": {
            "version": "3.11.13",
            "executable": str(expected_candidate / "runtime/python/bin/python3.11"),
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
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(
        _load(SCHEMAS / "paper2-cpu-staging-result-receipt-v3-2.schema.json"),
        format_checker=jsonschema.FormatChecker(),
    ).validate(stage)
    (case["final_root"] / "staging_receipt.json").write_text(json.dumps(stage), encoding="utf-8")

    def runner(_argv: list[str], **_: object) -> object:
        rows = (
            f"{jobs[0]}|COMPLETED|0:0|00:00:01||cn004\n"
            f"{jobs[1]}|COMPLETED|0:0|00:00:01||cn004\n"
        )
        return type("Completed", (), {"stdout": rows})()

    receipt = staging.build_harvest_receipt(
        contract=case["contract"],
        repository_root=ROOT,
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
        git_observer=lambda _root: (case["submission"]["expected_repo_sha"], True),
        path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
    )
    assert receipt["verdict"] == "HARVEST_STAGING_PASS"
    assert receipt["failures"] == []
    jsonschema.Draft202012Validator(
        _load(SCHEMAS / "paper2-cpu-staging-harvest-receipt-v3-2.schema.json"),
        format_checker=jsonschema.FormatChecker(),
    ).validate(receipt)

    for mutation in ("empty_freeze", "insufficient_free_space"):
        mutated = copy.deepcopy(stage)
        if mutation == "empty_freeze":
            mutated["pip_freeze_all"] = []
        else:
            mutated["fs9_disk_usage_before_staging"] = {
                "total": 10_000_000_000,
                "used": 9_999_999_999,
                "free": 1,
            }
        (case["final_root"] / "staging_receipt.json").write_text(
            json.dumps(mutated), encoding="utf-8"
        )
        rejected = staging.build_harvest_receipt(
            contract=case["contract"],
            repository_root=ROOT,
            submission_receipt=case["submission"],
            submission_receipt_path=case["submission_path"],
            receipt_root=case["receipt_root"],
            final_root=case["final_root"],
            failure_root=case["failure_root"],
            runner=runner,
            git_observer=lambda _root: (case["submission"]["expected_repo_sha"], True),
            path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
        )
        assert rejected["verdict"] == "HARVEST_CANNOT_CHECK"


@pytest.mark.parametrize(
    "mutation", ["contract_hash", "bootstrap_repo_sha", "bootstrap_verdict"]
)
def test_v3_2_harvest_rejects_mismatched_contract_or_bootstrap(
    tmp_path: Path, mutation: str
) -> None:
    case = _negative_harvest_fixture(tmp_path)
    if mutation == "contract_hash":
        case["submission"]["contract_canonical_sha256"] = "f" * 64
    else:
        bootstrap_path = Path(case["submission"]["bootstrap_receipt_path"])
        bootstrap = _load(bootstrap_path)
        if mutation == "bootstrap_repo_sha":
            bootstrap["observed_repo_sha"] = "e" * 40
        else:
            bootstrap["verdict"] = "BOOTSTRAP_PASS_FABRICATED"
        bootstrap_path.write_text(json.dumps(bootstrap), encoding="utf-8")
        case["submission"]["bootstrap_receipt_sha256"] = hashlib.sha256(
            bootstrap_path.read_bytes()
        ).hexdigest()
    case["submission_path"].write_text(json.dumps(case["submission"]), encoding="utf-8")

    def runner(_argv: list[str], **_: object) -> object:
        return type("Completed", (), {"stdout": case["rows"]})()

    receipt = staging.build_harvest_receipt(
        contract=case["contract"],
        repository_root=ROOT,
        submission_receipt=case["submission"],
        submission_receipt_path=case["submission_path"],
        receipt_root=case["receipt_root"],
        final_root=case["final_root"],
        failure_root=case["failure_root"],
        runner=runner,
        git_observer=lambda _root: (case["submission"]["expected_repo_sha"], True),
        path_mapper=lambda raw: case["path_map"].get(raw, Path(raw)),
    )
    assert receipt["verdict"] == "HARVEST_CANNOT_CHECK"
    expected_failure = (
        "submission_receipt_semantics_invalid"
        if mutation == "contract_hash"
        else "bootstrap_receipt_semantics_invalid"
    )
    assert expected_failure in receipt["failures"]
