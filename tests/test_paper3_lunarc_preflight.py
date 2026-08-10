from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import canonical_sha256
from rakl.paper3_lunarc_preflight import validate_and_submit


SHA = "a" * 40
PROTOCOL = {"protocol_id": "paper3-confirmatory-gate-v2", "frozen": True}
PROTOCOL_SHA256 = canonical_sha256(PROTOCOL)
BENCHMARK = {
    "schema_version": "paper3-confirmatory-benchmark-v2",
    "benchmark_id": "paper3-confirmatory-test-v2",
    "subject_sha": SHA,
    "protocol_sha256": PROTOCOL_SHA256,
}
BENCHMARK_SHA256 = canonical_sha256(BENCHMARK)
IMPORT_RECEIPT = {
    "schema_version": "paper3-annotation-import-receipt-v2",
    "subject_sha": SHA,
    "protocol_id": "paper3-confirmatory-gate-v2",
    "protocol_sha256": PROTOCOL_SHA256,
    "source_set_sha256": "2" * 64,
    "packet_sha256": "3" * 64,
    "submission_sha256": ["4" * 64, "5" * 64],
    "adjudication_sha256": "6" * 64,
    "provenance_audit_sha256": "7" * 64,
    "negative_history_benchmark_sha256": [
        "831fa5804efca457f0c9763ec6efd4913c569068aa5ba3ae0b9b4f1f982e9db4"
    ],
    "benchmark_sha256": BENCHMARK_SHA256,
    "passed": True,
    "failures": [],
    "coordinate_exact_agreement": {},
    "coordinate_conflict_count": {},
    "training_authorized": False,
}


def _gate(*, authorized: bool) -> dict:
    return {
        "schema_version": "paper3-confirmatory-gate-result-v2",
        "experiment_id": "paper3-confirmatory-gate-lofo-v2",
        "subject_sha": SHA,
        "created_at_utc": "2026-08-10T22:00:00Z",
        "frozen_protocol_id": "paper3-confirmatory-gate-v2",
        "protocol_sha256": PROTOCOL_SHA256,
        "benchmark_id": BENCHMARK["benchmark_id"],
        "benchmark_sha256": BENCHMARK_SHA256,
        "claim_boundary": "Test-only full contract; no empirical authority.",
        "split": "leave_one_family_out",
        "family_count": 1,
        "case_count": 1,
        "arm_metrics": {},
        "predictions": [],
        "annotation_gate": {"passed": authorized},
        "diagnostic_signal_gate": {"passed": authorized},
        "overall_cheap_gate_passed": authorized,
        "expensive_training_authorized": authorized,
        "gate_verdict": "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE" if authorized else "FAIL_CLOSED_ANNOTATION_GATE",
        "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
        "negative_history": [] if authorized else ["test gate closed"],
    }


def _manifest(tmp_path: Path, gate: dict) -> dict:
    batch_script = tmp_path / "training.sbatch"
    shutil.copyfile(
        Path(__file__).resolve().parents[1]
        / "experiments/paper3/lunarc/allocated_preflight.sbatch",
        batch_script,
    )
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    artifact_paths = {}
    payloads = {
        "task_set": {"tasks": ["held-out-structural-transfer-v2"]},
        "environment": {
            "python_version": "3.11.9",
            "locked_environment_sha256": "8" * 64,
        },
        "seed_schedule": {"seeds": [11, 23, 47]},
        "model_artifact": {
            "model_revision": f"open-model@{'1' * 40}",
            "weights_artifact_sha256": "9" * 64,
            "source_uri": "https://example.invalid/immutable-model",
            "license": "test-only",
        },
    }
    for name, payload in payloads.items():
        path = tmp_path / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": f"paper3-{name.replace('_', '-')}-v1",
                    "artifact_id": f"paper3-test-{name}-v1",
                    "artifact_type": name,
                    "authority_status": "frozen_before_run",
                    "subject_sha": SHA,
                    "created_at_utc": "2026-08-10T22:00:00Z",
                    "payload": payload,
                }
            ),
            encoding="utf-8",
        )
        artifact_paths[name] = path
    manifest_path = tmp_path / "manifest.json"
    gate_receipt_path = tmp_path / "gate.json"
    gate_receipt_path.write_text(json.dumps(gate), encoding="utf-8")
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(PROTOCOL), encoding="utf-8")
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(json.dumps(BENCHMARK), encoding="utf-8")
    import_receipt_path = tmp_path / "annotation-import.json"
    import_receipt_path.write_text(json.dumps(IMPORT_RECEIPT), encoding="utf-8")
    manifest = {
        "schema_version": "paper3-lunarc-run-manifest-v1",
        "experiment_id": "paper3-training-pilot-v1",
        "workload": "training",
        "subject_sha": SHA,
        "gate_receipt_sha256": canonical_sha256(gate),
        "protocol_path": str(protocol_path),
        "protocol_sha256": PROTOCOL_SHA256,
        "benchmark_path": str(benchmark_path),
        "benchmark_sha256": BENCHMARK_SHA256,
        "annotation_import_receipt_path": str(import_receipt_path),
        "annotation_import_receipt_sha256": canonical_sha256(IMPORT_RECEIPT),
        "task_set_path": str(artifact_paths["task_set"]),
        "task_set_sha256": hashlib.sha256(artifact_paths["task_set"].read_bytes()).hexdigest(),
        "model_revision": f"open-model@{'1' * 40}",
        "model_artifact_path": str(artifact_paths["model_artifact"]),
        "model_artifact_sha256": hashlib.sha256(
            artifact_paths["model_artifact"].read_bytes()
        ).hexdigest(),
        "environment_path": str(artifact_paths["environment"]),
        "environment_sha256": hashlib.sha256(
            artifact_paths["environment"].read_bytes()
        ).hexdigest(),
        "seed_schedule_path": str(artifact_paths["seed_schedule"]),
        "seed_schedule_sha256": hashlib.sha256(
            artifact_paths["seed_schedule"].read_bytes()
        ).hexdigest(),
        "account": "lu2026-2-51",
        "partition": "gpua100",
        "fs9_output_dir": (
            "/projects/hep/fs9/users/scyiu/RAKL-paper3/paper3-training-pilot-v1"
        ),
        "batch_script": str(batch_script),
        "batch_script_sha256": hashlib.sha256(batch_script.read_bytes()).hexdigest(),
        "repo_path": str(repo_path),
        "manifest_path": str(manifest_path),
        "gate_receipt_path": str(gate_receipt_path),
    }
    _rewrite_manifest(manifest)
    return manifest


def _rewrite_manifest(manifest: dict) -> None:
    Path(manifest["manifest_path"]).write_text(json.dumps(manifest), encoding="utf-8")


class _Runner:
    def __init__(self, *, stdout: str = "3475000\n", error: Exception | None = None) -> None:
        self.calls: list[tuple[list[str], dict]] = []
        self.stdout = stdout
        self.error = error

    def __call__(self, argv: list[str], **kwargs: object) -> object:
        self.calls.append((argv, kwargs))
        if self.error is not None:
            raise self.error
        return type("Completed", (), {"stdout": self.stdout, "returncode": 0})()


def _validate(manifest: dict, gate: dict, runner: _Runner, **overrides: object) -> dict:
    arguments = {
        "manifest": manifest,
        "gate_receipt": gate,
        "observed_subject_sha": SHA,
        "checkout_clean": True,
        "output_exists": False,
        "execution_host": "cosmos3.int.lunarc",
        "observed_associations": {("lu2026-2-51", "gpua100")},
        "observed_repo_path": manifest["repo_path"],
        "runner": runner,
        "submit": True,
    }
    arguments.update(overrides)
    return validate_and_submit(**arguments)


def test_false_gate_never_invokes_sbatch(tmp_path: Path) -> None:
    gate = _gate(authorized=False)
    manifest = _manifest(tmp_path, gate)
    runner = _Runner()
    result = _validate(manifest, gate, runner)
    assert result["submitted"] is False
    assert result["verdict"] == "REFUSE_GATE_CLOSED"
    assert runner.calls == []


def test_truncated_self_hashed_gate_never_invokes_sbatch(tmp_path: Path) -> None:
    gate = {
        "schema_version": "paper3-confirmatory-gate-result-v2",
        "subject_sha": SHA,
        "annotation_gate": {"passed": True},
        "diagnostic_signal_gate": {"passed": True},
        "overall_cheap_gate_passed": True,
        "expensive_training_authorized": True,
        "gate_verdict": "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE",
    }
    manifest = _manifest(tmp_path, gate)
    runner = _Runner()
    result = _validate(manifest, gate, runner)
    assert "gate_receipt_schema_invalid" in result["failures"]
    assert result["submitted"] is False
    assert runner.calls == []


def test_wrong_subject_dirty_checkout_or_non_fs9_path_never_invokes_sbatch(
    tmp_path: Path,
) -> None:
    gate = _gate(authorized=True)
    manifest = _manifest(tmp_path, gate)
    manifest["fs9_output_dir"] = "/tmp/not-fs9"
    _rewrite_manifest(manifest)
    runner = _Runner()
    result = _validate(
        manifest,
        gate,
        runner,
        observed_subject_sha="0" * 40,
        checkout_clean=False,
    )
    assert result["submitted"] is False
    assert "subject_sha_mismatch" in result["failures"]
    assert "checkout_not_clean" in result["failures"]
    assert "fs9_output_outside_registered_root" in result["failures"]
    assert runner.calls == []


def test_authorized_exact_lunarc_manifest_submits_with_argv_and_records_job_id(
    tmp_path: Path,
) -> None:
    gate = _gate(authorized=True)
    manifest = _manifest(tmp_path, gate)
    runner = _Runner()
    result = _validate(manifest, gate, runner)
    assert result["submitted"] is True
    assert result["slurm_job_id"] == "3475000"
    assert result["verdict"] == "SUBMITTED_AFTER_EXACT_GATE_PASS"
    assert result["batch_script_sha256"] == manifest["batch_script_sha256"]
    assert result["repo_path"] == manifest["repo_path"]
    assert len(runner.calls) == 1
    argv, kwargs = runner.calls[0]
    assert argv[:4] == [
        "sbatch",
        "--parsable",
        "--account=lu2026-2-51",
        "--partition=gpua100",
    ]
    assert argv[-1] == manifest["batch_script"]
    assert kwargs["shell"] is False
    exported = next(value for value in argv if value.startswith("--export="))
    assert f"RAKL_EXPECTED_MANIFEST_SHA256={canonical_sha256(manifest)}" in exported
    assert f"RAKL_EXPECTED_GATE_SHA256={canonical_sha256(gate)}" in exported
    root = Path(__file__).resolve().parents[1]
    for name, instance in (
        ("paper3-lunarc-run-manifest.schema.json", manifest),
        ("paper3-lunarc-preflight-receipt.schema.json", result),
    ):
        schema = json.loads((root / "schemas" / name).read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


@pytest.mark.parametrize(
    ("runner", "expected_failure"),
    [
        (_Runner(stdout="not-a-job-id\n"), "sbatch_invalid_job_id"),
        (_Runner(error=RuntimeError("scheduler unavailable")), "sbatch_submission_failed"),
    ],
)
def test_submission_errors_return_machine_readable_receipt(
    tmp_path: Path, runner: _Runner, expected_failure: str
) -> None:
    gate = _gate(authorized=True)
    manifest = _manifest(tmp_path, gate)
    result = _validate(manifest, gate, runner)
    assert result["submitted"] is False
    assert result["verdict"] == "SUBMISSION_FAILED"
    assert expected_failure in result["failures"]
    assert result["slurm_job_id"] is None


@pytest.mark.parametrize(
    ("mutation", "expected_failure"),
    [
        ("protocol", "gate_protocol_hash_mismatch"),
        ("benchmark", "gate_benchmark_hash_mismatch"),
        ("batch_hash", "batch_script_hash_mismatch"),
        ("arbitrary_batch", "batch_script_not_allowlisted"),
        ("protocol_artifact", "lineage_hash_mismatch:protocol"),
        ("benchmark_artifact", "lineage_hash_mismatch:benchmark"),
        ("import_artifact", "lineage_hash_mismatch:annotation_import_receipt"),
        ("task_set", "artifact_hash_mismatch:task_set"),
        ("environment", "artifact_hash_mismatch:environment"),
        ("seed_schedule", "artifact_hash_mismatch:seed_schedule"),
        ("model_artifact", "artifact_hash_mismatch:model_artifact"),
        ("artifact_authority", "artifact_contract_invalid:task_set"),
        ("mutable_model_revision", "model_revision_not_immutable"),
        ("relative_task", "artifact_path_not_absolute:task_set"),
        ("repo", "repo_path_mismatch"),
        ("dotdot", "fs9_output_outside_registered_root"),
        ("grandchild", "fs9_output_not_exactly_one_new_child"),
    ],
)
def test_bound_manifest_mismatches_never_invoke_sbatch(
    tmp_path: Path, mutation: str, expected_failure: str
) -> None:
    gate = _gate(authorized=True)
    manifest = _manifest(tmp_path, gate)
    observed_repo_path = manifest["repo_path"]
    if mutation == "protocol":
        manifest["protocol_sha256"] = "0" * 64
    elif mutation == "benchmark":
        manifest["benchmark_sha256"] = "0" * 64
    elif mutation == "batch_hash":
        manifest["batch_script_sha256"] = "0" * 64
    elif mutation == "arbitrary_batch":
        Path(manifest["batch_script"]).write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
        manifest["batch_script_sha256"] = hashlib.sha256(
            Path(manifest["batch_script"]).read_bytes()
        ).hexdigest()
    elif mutation == "protocol_artifact":
        Path(manifest["protocol_path"]).write_text("{}\n", encoding="utf-8")
    elif mutation == "benchmark_artifact":
        Path(manifest["benchmark_path"]).write_text("{}\n", encoding="utf-8")
    elif mutation == "import_artifact":
        Path(manifest["annotation_import_receipt_path"]).write_text("{}\n", encoding="utf-8")
    elif mutation in {"task_set", "environment", "seed_schedule", "model_artifact"}:
        Path(manifest[f"{mutation}_path"]).write_text("changed\n", encoding="utf-8")
    elif mutation == "artifact_authority":
        path = Path(manifest["task_set_path"])
        value = json.loads(path.read_text())
        value["authority_status"] = "draft"
        path.write_text(json.dumps(value), encoding="utf-8")
        manifest["task_set_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation == "mutable_model_revision":
        manifest["model_revision"] = "open-model@latest"
    elif mutation == "relative_task":
        manifest["task_set_path"] = "relative-task-set.json"
    elif mutation == "repo":
        manifest["repo_path"] = str(tmp_path / "different-repo")
    elif mutation == "dotdot":
        manifest["fs9_output_dir"] = (
            "/projects/hep/fs9/users/scyiu/RAKL-paper3/../escape"
        )
    elif mutation == "grandchild":
        manifest["fs9_output_dir"] = (
            "/projects/hep/fs9/users/scyiu/RAKL-paper3/run/receipts"
        )
    _rewrite_manifest(manifest)
    runner = _Runner()
    result = _validate(
        manifest,
        gate,
        runner,
        observed_repo_path=observed_repo_path,
    )
    assert expected_failure in result["failures"]
    assert result["submitted"] is False
    assert runner.calls == []


@pytest.mark.parametrize("path_kind", ["manifest", "gate"])
def test_on_disk_binding_mismatch_never_invokes_sbatch(
    tmp_path: Path, path_kind: str
) -> None:
    gate = _gate(authorized=True)
    manifest = _manifest(tmp_path, gate)
    key = "manifest_path" if path_kind == "manifest" else "gate_receipt_path"
    Path(manifest[key]).write_text("{}\n", encoding="utf-8")
    runner = _Runner()
    result = _validate(manifest, gate, runner)
    assert f"{path_kind}_path_content_mismatch" in result["failures"]
    assert runner.calls == []


def test_allocated_batch_script_checks_exact_clean_repo_before_output_creation() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "experiments/paper3/lunarc/allocated_preflight.sbatch"
    ).read_text(encoding="utf-8")
    assert 'git -C "$repo_path" rev-parse HEAD' in script
    assert 'git -C "$repo_path" status --porcelain' in script
    assert 'observed_subject == manifest["subject_sha"]' in script
    assert 'canonical_hash(manifest) == os.environ["RAKL_EXPECTED_MANIFEST_SHA256"]' in script
    assert 'canonical_hash(gate) == os.environ["RAKL_EXPECTED_GATE_SHA256"]' in script
    assert 'gate["protocol_sha256"] == manifest["protocol_sha256"]' in script
    assert 'gate["benchmark_sha256"] == manifest["benchmark_sha256"]' in script
    assert 'gate["overall_cheap_gate_passed"] is True' in script
    assert 'for artifact in ("task_set", "environment", "seed_schedule", "model_artifact")' in script
    assert 'hashlib.sha256(artifact_path.read_bytes()).hexdigest()' in script
    assert 'for artifact in ("protocol", "benchmark", "annotation_import_receipt")' in script
    assert "output.parent == fs9_root" in script
    assert script.index("observed_subject =") < script.index("output.mkdir(")
