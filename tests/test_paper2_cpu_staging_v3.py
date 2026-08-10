from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import rakl.paper2_cpu_staging as staging

from rakl.paper2_cpu_staging import (
    SubmissionObservation,
    _commit_staging_candidate,
    _safe_extract,
    build_harvest_receipt,
    build_submission_receipt,
    validate_staging_contract,
    validate_staging_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
ASSET_MANIFEST = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json"
WHEEL_LOCK = ROOT / "research/paper2_microtrial_v3/CP311_LINUX_X86_64_WHEEL_LOCK_AUDIT.json"
REQUIREMENTS = ROOT / "research/paper2_microtrial_v3/requirements-cp311-linux-x86_64-v3.lock"
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3.json"
SCRIPT_ROOT = ROOT / "experiments/paper2/lunarc"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_asset_manifest_freezes_exact_python_cpu_torch_wheels_and_model_bytes() -> None:
    manifest = _load(ASSET_MANIFEST)
    wheel_lock = _load(WHEEL_LOCK)

    assert validate_staging_manifest(manifest, repository_root=ROOT) == ()
    assert hashlib.sha256(WHEEL_LOCK.read_bytes()).hexdigest() == (
        "e06c27464d15b46617b1b8c8f79544f6173267b080189257b2d0e28d006afff3"
    )
    assert hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest() == (
        "291752036b264369795967b2599ca401a1707750a213b0992c2ef4a3b55c87b0"
    )
    assert wheel_lock["wheel_count"] == 29
    assert wheel_lock["total_bytes"] == 233304796
    torch = next(wheel for wheel in wheel_lock["wheels"] if wheel["name"] == "torch")
    assert torch["requirement"] == "torch==2.8.0+cpu"
    assert manifest["required_runtime_versions"]["torch"] == "2.8.0+cpu"
    python = next(item for item in manifest["artifacts"] if item["role"] == "python_archive")
    assert python["bytes"] == 48610589
    assert python["sha256"] == "13f898a7ac7a54e97d3efd6a958ef5e16e9329bd9639b03fc95146227d18706c"
    assert sum(item["role"] == "model_snapshot" for item in manifest["artifacts"]) == 8
    assert manifest["model_execution_performed"] is False


def test_manifest_rejects_weakened_torch_equality_duplicate_or_unlocked_artifact() -> None:
    manifest = _load(ASSET_MANIFEST)
    for mutation, expected in (
        ("torch", "runtime_version_mismatch:torch"),
        ("duplicate", "artifact_destination_duplicate"),
        ("hash", "artifact_sha256_invalid"),
    ):
        candidate = copy.deepcopy(manifest)
        if mutation == "torch":
            candidate["required_runtime_versions"]["torch"] = "2.8.0"
        elif mutation == "duplicate":
            candidate["artifacts"][1]["destination"] = candidate["artifacts"][0]["destination"]
        else:
            candidate["artifacts"][0]["sha256"] = "0"
        assert expected in validate_staging_manifest(candidate, repository_root=ROOT)


def test_contract_binds_all_scripts_and_inputs_and_forbids_model_execution() -> None:
    contract = _load(CONTRACT)
    assert validate_staging_contract(contract, repository_root=ROOT) == ()
    assert contract["model_execution_permitted"] is False
    assert contract["submission_policy"]["exact_repo_sha_required"] is True
    assert contract["submission_policy"]["network_probe_must_precede_staging"] is True
    assert contract["promotion_policy"]["atomic_rename_required"] is True
    assert contract["failure_policy"]["preserve_failed_candidate_and_receipt"] is True
    assert {item["role"] for item in contract["bindings"]} >= {
        "asset_manifest",
        "wheel_lock",
        "requirements_lock",
        "network_probe_batch",
        "staging_batch",
        "submission_script",
        "harvest_script",
    }


def test_wrong_sha_dirty_checkout_or_unobserved_association_never_submits() -> None:
    contract = _load(CONTRACT)
    calls: list[list[str]] = []

    def forbidden(argv: list[str], **_: object) -> object:
        calls.append(argv)
        raise AssertionError("sbatch must not be called")

    receipt = build_submission_receipt(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha="a" * 40,
        observation=SubmissionObservation(
            observed_repo_sha="b" * 40,
            checkout_clean=False,
            execution_host="cosmos3.int.lunarc",
            observed_associations=frozenset({("lu2026-2-51", "shared")}),
        ),
        account="lu2026-2-51",
        partition="other",
        submit=True,
        runner=forbidden,
    )
    assert receipt["verdict"] == "REFUSE_PREFLIGHT_VALIDATION"
    assert receipt["submitted_job_ids"] == []
    assert {
        "repo_sha_mismatch",
        "checkout_not_clean",
        "account_partition_association_missing",
    } <= set(receipt["failures"])
    assert calls == []


class Runner:
    def __init__(self, outputs: list[str], failure_at: int | None = None) -> None:
        self.outputs = outputs
        self.failure_at = failure_at
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **kwargs: object) -> object:
        assert kwargs["shell"] is False
        self.calls.append(argv)
        if self.failure_at == len(self.calls):
            raise RuntimeError("scheduler unavailable")
        return type("Completed", (), {"stdout": self.outputs[len(self.calls) - 1]})()


def _observation(sha: str) -> SubmissionObservation:
    return SubmissionObservation(
        observed_repo_sha=sha,
        checkout_clean=True,
        execution_host="cosmos3.int.lunarc",
        observed_associations=frozenset({("lu2026-2-51", "shared")}),
    )


def _bootstrap_receipt(tmp_path: Path, sha: str, repo: Path = ROOT) -> Path:
    path = tmp_path / "bootstrap.json"
    path.write_text(
        json.dumps(
            {
                "verdict": "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT",
                "exit_status": 0,
                "expected_repo_sha": sha,
                "observed_repo_sha": sha,
                "repo_path": str(repo),
                "checkout_clean": True,
                "detached_head": True,
                "jobs_submitted": 0,
                "model_execution_performed": False,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_submission_is_probe_then_afterok_staging_and_carries_exact_repo_sha(tmp_path: Path) -> None:
    contract = _load(CONTRACT)
    sha = "c" * 40
    runner = Runner(["41001\n", "41002\n"])
    receipt = build_submission_receipt(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha=sha,
        observation=_observation(sha),
        account="lu2026-2-51",
        partition="shared",
        submit=True,
        bootstrap_receipt_path=_bootstrap_receipt(tmp_path, sha),
        runner=runner,
    )
    assert receipt["verdict"] == "SUBMITTED_TWO_PHASE_STAGING"
    assert receipt["submitted_job_ids"] == ["41001", "41002"]
    assert len(runner.calls) == 2
    assert any(value == "--dependency=afterok:41001" for value in runner.calls[1])
    assert all(any(f"RAKL_EXPECTED_REPO_SHA={sha}" in value for value in call) for call in runner.calls)
    assert runner.calls[0][-1].endswith("network_probe.sbatch")
    assert runner.calls[1][-1].endswith("stage_cpu_assets.sbatch")


def test_partial_submission_failure_preserves_first_job_id_in_receipt(tmp_path: Path) -> None:
    contract = _load(CONTRACT)
    sha = "c" * 40
    runner = Runner(["41001\n", "41002\n"], failure_at=2)
    receipt = build_submission_receipt(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha=sha,
        observation=_observation(sha),
        account="lu2026-2-51",
        partition="shared",
        submit=True,
        bootstrap_receipt_path=_bootstrap_receipt(tmp_path, sha),
        runner=runner,
    )
    assert receipt["verdict"] == "PARTIAL_SUBMISSION_FAILURE"
    assert receipt["submitted_job_ids"] == ["41001"]
    assert receipt["failures"] == ["staging_submission_failed"]
    assert receipt["failure_history_preserved"] is True


def test_batch_and_operator_scripts_encode_no_execution_atomic_and_harvest_boundaries() -> None:
    probe = (SCRIPT_ROOT / "network_probe.sbatch").read_text(encoding="utf-8")
    stage = (SCRIPT_ROOT / "stage_cpu_assets.sbatch").read_text(encoding="utf-8")
    submit = (SCRIPT_ROOT / "submit_cpu_staging_v3.sh").read_text(encoding="utf-8")
    harvest = (SCRIPT_ROOT / "harvest_cpu_staging_v3.sh").read_text(encoding="utf-8")

    assert "network-probe" in probe
    assert "stage-assets" in stage
    assert "RAKL_EXPECTED_REPO_SHA" in probe and "RAKL_EXPECTED_REPO_SHA" in stage
    assert "--expected-repo-sha" in submit
    assert "--dependency=afterok" not in submit  # dependency is constructed by validated Python
    assert "harvest" in harvest
    forbidden = ("AutoModel", "generate(", "execute_microtrial", "paper2_pendulum_microtrial run")
    assert not any(token in probe + stage + submit + harvest for token in forbidden)


def _make_existing_bootstrap_repo(fs9_root: Path) -> str:
    import subprocess

    repo = fs9_root / "repo"
    repo.mkdir(parents=True)
    for argv in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Paper 2 bootstrap test"],
        ["git", "config", "user.email", "paper2-bootstrap@example.invalid"],
    ):
        subprocess.run(argv, cwd=repo, check=True, shell=False)
    (repo / "tracked.txt").write_text("frozen\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True, shell=False)
    subprocess.run(["git", "commit", "-qm", "frozen"], cwd=repo, check=True, shell=False)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/SzeChunYiu/RAKL.git"],
        cwd=repo,
        check=True,
        shell=False,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        shell=False,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    subprocess.run(["git", "checkout", "-q", "--detach", sha], cwd=repo, check=True, shell=False)
    return sha


def test_repo_bootstrap_accepts_only_exact_clean_detached_existing_checkout(tmp_path: Path) -> None:
    import stat
    import subprocess

    fs9_root = tmp_path / "fs9"
    sha = _make_existing_bootstrap_repo(fs9_root)
    receipt_path = fs9_root / "receipts/v3/bootstrap.json"
    subprocess.run(
        [
            str(SCRIPT_ROOT / "bootstrap_repo_v3.sh"),
            "--fs9-root",
            str(fs9_root),
            "--expected-repo-sha",
            sha,
            "--receipt-output",
            str(receipt_path),
        ],
        check=True,
        shell=False,
    )
    receipt = _load(receipt_path)
    assert receipt["verdict"] == "BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT"
    assert receipt["github_remote"] == "https://github.com/SzeChunYiu/RAKL.git"
    assert receipt["expected_repo_sha"] == receipt["observed_repo_sha"] == sha
    assert receipt["observed_repo_tree"]
    assert receipt["checkout_clean"] is True
    assert receipt["detached_head"] is True
    assert receipt["jobs_submitted"] == 0
    assert receipt["model_execution_performed"] is False
    for governed in (fs9_root, fs9_root / "logs", fs9_root / "receipts", fs9_root / "failures", fs9_root / "assets"):
        assert stat.S_IMODE(governed.stat().st_mode) == 0o700
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600


def test_repo_bootstrap_preserves_machine_readable_failure_for_dirty_existing_repo(tmp_path: Path) -> None:
    import subprocess

    fs9_root = tmp_path / "fs9"
    sha = _make_existing_bootstrap_repo(fs9_root)
    (fs9_root / "repo/tracked.txt").write_text("dirty\n", encoding="utf-8")
    receipt_path = fs9_root / "receipts/v3/bootstrap-failure.json"
    completed = subprocess.run(
        [
            str(SCRIPT_ROOT / "bootstrap_repo_v3.sh"),
            "--fs9-root",
            str(fs9_root),
            "--expected-repo-sha",
            sha,
            "--receipt-output",
            str(receipt_path),
        ],
        check=False,
        shell=False,
    )
    assert completed.returncode == 2
    receipt = _load(receipt_path)
    assert receipt["verdict"] == "BOOTSTRAP_FAILURE"
    assert receipt["failure"] == "repository_checkout_not_clean"
    assert receipt["exit_status"] == 2
    assert receipt["jobs_submitted"] == 0
    assert receipt["model_execution_performed"] is False


def test_submission_wrapper_requires_matching_successful_bootstrap_receipt_before_scheduler() -> None:
    bootstrap = (SCRIPT_ROOT / "bootstrap_repo_v3.sh").read_text(encoding="utf-8")
    submit = (SCRIPT_ROOT / "submit_cpu_staging_v3.sh").read_text(encoding="utf-8")
    assert "--expected-repo-sha" in bootstrap
    assert "https://github.com/SzeChunYiu/RAKL.git" in bootstrap
    assert "mv --no-target-directory" in bootstrap
    assert '"jobs_submitted": 0' in bootstrap
    assert '"model_execution_performed": False' in bootstrap
    assert "--bootstrap-receipt" in submit
    assert submit.index("bootstrap receipt validation failed") < submit.index("sacctmgr")


def test_contract_and_construction_receipt_validate_against_bound_schemas() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    contract = _load(CONTRACT)
    receipt_path = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONSTRUCTION_RECEIPT_V3.json"
    receipt = _load(receipt_path)
    for schema_name, value in (
        ("paper2-cpu-staging-contract-v3.schema.json", contract),
        ("paper2-cpu-staging-construction-receipt-v3.schema.json", receipt),
    ):
        schema = _load(ROOT / "schemas" / schema_name)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)
    assert receipt["verdict"] == "READY_NOT_SUBMITTED"
    assert receipt["jobs_submitted"] == 0
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    assert receipt["contract_file_sha256"] == hashlib.sha256(CONTRACT.read_bytes()).hexdigest()


def test_every_operator_script_has_valid_bash_syntax() -> None:
    import subprocess

    for path in sorted(SCRIPT_ROOT.iterdir()):
        if path.suffix in {".sh", ".sbatch"}:
            subprocess.run(["bash", "-n", str(path)], check=True, shell=False)


def test_harvest_binds_terminal_scheduler_rows_and_both_native_receipts(tmp_path: Path) -> None:
    submission_path = tmp_path / "submission.json"
    bootstrap_path = _bootstrap_receipt(tmp_path, "c" * 40)
    submission = {
        "verdict": "SUBMITTED_TWO_PHASE_STAGING",
        "submitted_job_ids": ["41001", "41002"],
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "bootstrap_receipt_path": str(bootstrap_path),
        "bootstrap_receipt_sha256": hashlib.sha256(bootstrap_path.read_bytes()).hexdigest(),
    }
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    receipt_root = tmp_path / "receipts"
    receipt_root.mkdir()
    probe = {
        "verdict": "NETWORK_PROBE_PASS",
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
    }
    (receipt_root / "network-probe-41001.json").write_text(json.dumps(probe), encoding="utf-8")
    final_root = tmp_path / "assets"
    final_root.mkdir()
    stage = {
        "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "model_execution_performed": False,
    }
    (final_root / "staging_receipt.json").write_text(json.dumps(stage), encoding="utf-8")

    def sacct(argv: list[str], **kwargs: object) -> object:
        assert argv[0] == "sacct" and kwargs["shell"] is False
        return type(
            "Completed",
            (),
            {"stdout": "41001|COMPLETED|0:0|00:00:05|10M|cn1\n41002|COMPLETED|0:0|00:02:00|2G|cn2\n"},
        )()

    receipt = build_harvest_receipt(
        submission_receipt=submission,
        submission_receipt_path=submission_path,
        receipt_root=receipt_root,
        final_root=final_root,
        failure_root=tmp_path / "failures",
        runner=sacct,
    )
    assert receipt["verdict"] == "HARVEST_STAGING_PASS"
    assert receipt["probe_receipt_sha256"] == hashlib.sha256(
        (receipt_root / "network-probe-41001.json").read_bytes()
    ).hexdigest()
    assert receipt["staging_receipt_sha256"] == hashlib.sha256(
        (final_root / "staging_receipt.json").read_bytes()
    ).hexdigest()
    assert receipt["model_execution_performed"] is False


@pytest.mark.parametrize(
    ("failure_name", "failure_verdict"),
    (
        ("staging-failed-41002.json", "STAGING_FAILED_PRESERVED"),
        ("staging-refused-41002.json", "STAGING_REFUSED"),
    ),
)
def test_harvest_preserves_terminal_failed_stage_as_negative_not_success(
    tmp_path: Path, failure_name: str, failure_verdict: str
) -> None:
    submission_path = tmp_path / "submission.json"
    bootstrap_path = _bootstrap_receipt(tmp_path, "c" * 40)
    submission = {
        "verdict": "SUBMITTED_TWO_PHASE_STAGING",
        "submitted_job_ids": ["41001", "41002"],
        "contract_canonical_sha256": "d" * 64,
        "expected_repo_sha": "c" * 40,
        "bootstrap_receipt_path": str(bootstrap_path),
        "bootstrap_receipt_sha256": hashlib.sha256(bootstrap_path.read_bytes()).hexdigest(),
    }
    submission_path.write_text(json.dumps(submission), encoding="utf-8")
    receipt_root = tmp_path / "receipts"; receipt_root.mkdir()
    (receipt_root / "network-probe-41001.json").write_text(json.dumps({"verdict":"NETWORK_PROBE_PASS","contract_canonical_sha256":"d"*64,"expected_repo_sha":"c"*40}), encoding="utf-8")
    failure_root = tmp_path / "failures"; failure_root.mkdir()
    (failure_root / failure_name).write_text(json.dumps({"verdict":failure_verdict,"contract_canonical_sha256":"d"*64,"expected_repo_sha":"c"*40,"model_execution_performed":False}), encoding="utf-8")

    def sacct(argv: list[str], **_: object) -> object:
        return type("Completed", (), {"stdout": "41001|COMPLETED|0:0|00:00:05|10M|cn1\n41002|FAILED|1:0|00:00:12|20M|cn2\n"})()

    receipt = build_harvest_receipt(
        submission_receipt=submission,
        submission_receipt_path=submission_path,
        receipt_root=receipt_root,
        final_root=tmp_path / "assets",
        failure_root=failure_root,
        runner=sacct,
    )
    assert receipt["verdict"] == "HARVEST_STAGING_NEGATIVE_PRESERVED"
    assert receipt["failures"] == ["staging_job_or_receipt_failed"]
    assert receipt["negative_history_preserved"] is True


@pytest.mark.parametrize(("probe_job_id", "drop_last"), (("99999", False), ("41001", True)))
def test_stage_refuses_replayed_or_incomplete_network_probe_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probe_job_id: str, drop_last: bool
) -> None:
    contract = _load(CONTRACT)
    manifest = _load(ASSET_MANIFEST)
    observations = [
        {"artifact_id": item["artifact_id"], "http_status": 200, "reachable": True}
        for item in manifest["artifacts"]
    ]
    if drop_last:
        observations.pop()
    canonical = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    probe_path = tmp_path / "probe.json"
    probe_path.write_text(
        json.dumps(
            {
                "verdict": "NETWORK_PROBE_PASS",
                "contract_canonical_sha256": canonical,
                "expected_repo_sha": "c" * 40,
                "observed_repo_sha": "c" * 40,
                "slurm_job_id": probe_job_id,
                "observations": observations,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SLURM_JOB_ID", "41002")
    monkeypatch.setenv("RAKL_PROBE_JOB_ID", "41001")
    monkeypatch.setattr(
        staging,
        "_git_attestation",
        lambda *_: {
            "repo_sha": "c" * 40,
            "repo_tree_sha": "d" * 40,
            "checkout_clean": True,
            "construction_parent_sha": contract["construction_parent_sha"],
            "construction_parent_ancestor": True,
        },
    )
    monkeypatch.setattr(
        staging.shutil,
        "disk_usage",
        lambda *_: type("Usage", (), {"total": 10_000_000_000, "used": 1, "free": 9_000_000_000})(),
    )
    written: list[dict] = []
    monkeypatch.setattr(staging, "_atomic_json", lambda _path, value: written.append(value))
    receipt = staging.stage_assets(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha="c" * 40,
        probe_receipt_path=probe_path,
    )
    assert receipt["verdict"] == "STAGING_REFUSED"
    assert "network_probe_receipt_invalid" in receipt["failures"]
    assert receipt["probe_slurm_job_id"] == "41001"
    assert receipt["slurm_job_id"] == "41002"
    assert written == [receipt]


def test_stage_setup_exception_is_caught_and_machine_receipted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load(CONTRACT)
    probe_path = tmp_path / "probe.json"
    probe_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SLURM_JOB_ID", "41002")
    monkeypatch.setenv("RAKL_PROBE_JOB_ID", "41001")
    monkeypatch.setattr(staging, "_git_attestation", lambda *_: (_ for _ in ()).throw(OSError("git unavailable")))
    written: list[dict] = []
    monkeypatch.setattr(staging, "_atomic_json", lambda _path, value: written.append(value))

    receipt = staging.stage_assets(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha="c" * 40,
        probe_receipt_path=probe_path,
    )

    assert receipt["verdict"] == "STAGING_FAILED_PRESERVED"
    assert receipt["failures"] == ["staging_setup_or_promotion_exception"]
    assert receipt["error_type"] == "OSError"
    assert receipt["slurm_job_id"] == "41002"
    assert receipt["probe_slurm_job_id"] == "41001"
    assert receipt["candidate_preserved"] is False
    assert written == [receipt]


def test_atomic_promotion_commit_record_is_terminal_and_failed_rename_preserves_candidate(
    tmp_path: Path,
) -> None:
    receipt = {
        "verdict": "STAGING_PASS_ATOMICALLY_PROMOTED",
        "authority_condition": "authoritative only at final path",
    }
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    final = tmp_path / "final"

    _commit_staging_candidate(candidate, final, receipt)

    assert not candidate.exists()
    assert json.loads((final / "staging_receipt.json").read_text()) == receipt

    second_candidate = tmp_path / "second-candidate"
    second_candidate.mkdir()
    occupied_final = tmp_path / "occupied-final"
    occupied_final.mkdir()
    (occupied_final / "sentinel").write_text("preserve", encoding="utf-8")
    with pytest.raises(OSError):
        _commit_staging_candidate(second_candidate, occupied_final, receipt)
    assert second_candidate.is_dir()
    assert (second_candidate / "staging_receipt.json").is_file()
    assert (occupied_final / "sentinel").read_text(encoding="utf-8") == "preserve"


def test_contract_rejects_missing_runtime_or_cross_filesystem_promotion_paths() -> None:
    contract = _load(CONTRACT)
    missing_runtime = copy.deepcopy(contract)
    missing_runtime["bindings"] = [
        item for item in missing_runtime["bindings"] if item["role"] != "staging_runtime"
    ]
    assert "contract_required_binding_missing" in validate_staging_contract(
        missing_runtime, repository_root=ROOT
    )

    split_parent = copy.deepcopy(contract)
    split_parent["final_root"] = "/projects/hep/fs9/users/scyiu/RAKL-paper2/elsewhere/paper2-cpu-v3"
    assert "promotion_paths_not_same_parent" in validate_staging_contract(
        split_parent, repository_root=ROOT
    )


def test_safe_python_archive_extraction_rejects_links_devices_and_absolute_names(tmp_path: Path) -> None:
    import io
    import tarfile

    for kind in ("symlink", "hardlink", "device", "absolute"):
        archive = tmp_path / f"{kind}.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("/escape" if kind == "absolute" else "python/bad")
            if kind == "symlink":
                member.type = tarfile.SYMTYPE; member.linkname = "../../escape"
            elif kind == "hardlink":
                member.type = tarfile.LNKTYPE; member.linkname = "python/other"
            elif kind == "device":
                member.type = tarfile.CHRTYPE
            else:
                member.size = 1; bundle.addfile(member, io.BytesIO(b"x")); continue
            bundle.addfile(member)
        with pytest.raises(ValueError, match="archive unsafe member"):
            _safe_extract(archive, tmp_path / f"out-{kind}")


def test_stage_receipt_contract_includes_environment_smoke_and_repo_attestation() -> None:
    source = (ROOT / "src/rakl/paper2_cpu_staging.py").read_text(encoding="utf-8")
    for token in (
        '"pip", "check"',
        "torch.version.cuda",
        "importlib.metadata",
        "pip_freeze_all",
        "shutil.disk_usage",
        '"rev-parse", "HEAD^{tree}"',
        '"merge-base", "--is-ancestor"',
    ):
        assert token in source
    contract = _load(CONTRACT)
    assert contract["bootstrap_policy"]["exact_repo_sha_required"] is True
    assert contract["staging_attestation_policy"]["torch_cuda_must_be_null"] is True
    assert any(binding["role"] == "repo_bootstrap_script" for binding in contract["bindings"])
