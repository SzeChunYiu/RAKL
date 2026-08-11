from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper3_annotation import canonical_sha256
from rakl.paper3_lunarc_workload import WORKLOAD_SCRIPTS, validate_and_submit_workload


SHA = "1" * 40


class Runner:
    def __init__(self, stdout: str = "48151623\n") -> None:
        self.stdout = stdout
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv: list[str], **kwargs: object) -> object:
        self.calls.append((argv, kwargs))
        return type("Completed", (), {"stdout": self.stdout, "returncode": 0})()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_world(tmp_path: Path, workload: str, authorized: bool = True) -> tuple[dict, dict]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "runner.py").write_text("raise SystemExit('not executed by wrapper test')\n")
    (repo / "result.schema.json").write_text('{"type":"object"}\n')
    weights = tmp_path / "weights.bin"
    weights.write_bytes(b"frozen-input-weights")
    protocol = {"protocol_id": "paper3-confirmatory-gate-v2"}
    benchmark = {"subject_sha": SHA, "protocol_sha256": canonical_sha256(protocol)}
    annotation_import = {
        "passed": authorized,
        "failures": [] if authorized else ["missing_external_annotations"],
        "subject_sha": SHA,
        "protocol_sha256": canonical_sha256(protocol),
        "benchmark_sha256": canonical_sha256(benchmark),
    }
    gate = {
        "schema_version": "paper3-confirmatory-gate-result-v2",
        "subject_sha": SHA,
        "protocol_sha256": canonical_sha256(protocol),
        "benchmark_sha256": canonical_sha256(benchmark),
        "annotation_gate": {"passed": authorized},
        "diagnostic_signal_gate": {"passed": authorized},
        "overall_cheap_gate_passed": authorized,
        "expensive_training_authorized": authorized,
        "gate_verdict": "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE" if authorized else "FAIL_CLOSED_ANNOTATION_GATE",
    }
    paths: dict[str, Path] = {}
    for name, value in (
        ("protocol", protocol),
        ("benchmark", benchmark),
        ("annotation_import_receipt", annotation_import),
    ):
        paths[name] = tmp_path / f"{name}.json"
        paths[name].write_text(json.dumps(value))
    for name in ("task_set", "environment", "seed_schedule", "model_artifact"):
        paths[name] = tmp_path / f"{name}.json"
        payload = {}
        if name == "model_artifact":
            payload = {
                "model_revision": f"open-model@{'2' * 40}",
                "weights_artifact_sha256": file_sha(weights),
            }
        paths[name].write_text(
            json.dumps({"artifact_type": name, "subject_sha": SHA, "payload": payload})
        )

    script_name, script_hash, mode = WORKLOAD_SCRIPTS[workload]
    source_script = Path(__file__).resolve().parents[1] / "experiments/paper3/lunarc" / script_name
    script = tmp_path / script_name
    shutil.copyfile(source_script, script)
    assert file_sha(script) == script_hash
    gate_path = tmp_path / "gate.json"
    gate_path.write_text(json.dumps(gate))
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "schema_version": "paper3-lunarc-workload-manifest-v1",
        "experiment_id": f"paper3-{workload}-pilot-v1",
        "workload": workload,
        "model_mode": mode,
        "resource_profile": "single_gpu_training_v1" if workload == "training" else "single_gpu_frozen_inference_v1",
        "subject_sha": SHA,
        "gate_receipt_path": str(gate_path),
        "gate_receipt_sha256": canonical_sha256(gate),
        "protocol_path": str(paths["protocol"]),
        "protocol_sha256": canonical_sha256(protocol),
        "benchmark_path": str(paths["benchmark"]),
        "benchmark_sha256": canonical_sha256(benchmark),
        "annotation_import_receipt_path": str(paths["annotation_import_receipt"]),
        "annotation_import_receipt_sha256": canonical_sha256(annotation_import),
        "task_set_path": str(paths["task_set"]),
        "task_set_sha256": file_sha(paths["task_set"]),
        "environment_path": str(paths["environment"]),
        "environment_sha256": file_sha(paths["environment"]),
        "seed_schedule_path": str(paths["seed_schedule"]),
        "seed_schedule_sha256": file_sha(paths["seed_schedule"]),
        "model_revision": f"open-model@{'2' * 40}",
        "model_artifact_path": str(paths["model_artifact"]),
        "model_artifact_sha256": file_sha(paths["model_artifact"]),
        "input_weights_path": str(weights),
        "input_weights_sha256": file_sha(weights),
        "python_executable": sys.executable,
        "runner_path": str(repo / "runner.py"),
        "runner_sha256": file_sha(repo / "runner.py"),
        "result_schema_path": str(repo / "result.schema.json"),
        "result_schema_sha256": file_sha(repo / "result.schema.json"),
        "result_receipt_relpath": f"receipts/{workload}_result.json",
        "account": "lu2026-2-51",
        "partition": "gpua100",
        "fs9_output_dir": f"/projects/hep/fs9/users/scyiu/RAKL-paper3/paper3-{workload}-pilot-v1",
        "batch_script": str(script),
        "batch_script_sha256": file_sha(script),
        "repo_path": str(repo),
        "manifest_path": str(manifest_path),
    }
    manifest_path.write_text(json.dumps(manifest))
    return manifest, gate


def invoke(manifest: dict, gate: dict, runner: Runner, **kwargs: object) -> dict:
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
        "schema_checker": lambda _value, _name: True,
    }
    arguments.update(kwargs)
    return validate_and_submit_workload(**arguments)


@pytest.mark.parametrize("workload", ["training", "inference"])
def test_authorized_workloads_use_distinct_allowlisted_scripts(tmp_path: Path, workload: str) -> None:
    manifest, gate = build_world(tmp_path, workload)
    runner = Runner()
    receipt = invoke(manifest, gate, runner)
    assert receipt["verdict"] == "SUBMITTED_AFTER_EXACT_GATE_PASS"
    assert receipt["submitted"] is True
    assert len(runner.calls) == 1
    argv, kwargs = runner.calls[0]
    assert argv[0] == "sbatch"
    assert argv[-1] == manifest["batch_script"]
    assert "--export=NONE," in next(value for value in argv if value.startswith("--export="))
    assert kwargs["shell"] is False


@pytest.mark.parametrize("workload", ["training", "inference"])
def test_closed_gate_never_invokes_sbatch(tmp_path: Path, workload: str) -> None:
    manifest, gate = build_world(tmp_path, workload, authorized=False)
    runner = Runner()
    receipt = invoke(manifest, gate, runner)
    assert receipt["verdict"] == "REFUSE_GATE_CLOSED"
    assert receipt["submitted"] is False
    assert "gate_receipt_not_authorized" in receipt["failures"]
    assert runner.calls == []


def test_training_script_cannot_be_used_for_frozen_inference(tmp_path: Path) -> None:
    manifest, gate = build_world(tmp_path, "inference")
    training_name, training_hash, _ = WORKLOAD_SCRIPTS["training"]
    source = Path(__file__).resolve().parents[1] / "experiments/paper3/lunarc" / training_name
    replacement = Path(manifest["batch_script"]).with_name(training_name)
    shutil.copyfile(source, replacement)
    manifest["batch_script"] = str(replacement)
    manifest["batch_script_sha256"] = training_hash
    Path(manifest["manifest_path"]).write_text(json.dumps(manifest))
    runner = Runner()
    receipt = invoke(manifest, gate, runner)
    assert "workload_batch_script_mismatch" in receipt["failures"]
    assert runner.calls == []


def test_unsafe_slurm_export_path_never_invokes_sbatch(tmp_path: Path) -> None:
    manifest, gate = build_world(tmp_path, "training")
    manifest["python_executable"] = "/safe/python,RAKL_EXPECTED_GATE_SHA256=forged"
    Path(manifest["manifest_path"]).write_text(json.dumps(manifest))
    runner = Runner()
    receipt = invoke(manifest, gate, runner)
    assert "unsafe_sbatch_export_value:python_executable" in receipt["failures"]
    assert runner.calls == []


def test_batch_runtime_rechecks_gate_before_creating_output() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = (root / "experiments/paper3/lunarc/gated_workload_runtime.py").read_text()
    assert runtime.index('require(gate["annotation_gate"]["passed"] is True') < runtime.index("output.mkdir(")
    assert runtime.index('require(gate["diagnostic_signal_gate"]["passed"] is True') < runtime.index("output.mkdir(")
    assert "def require(" in runtime
    assert "assert " not in runtime
    assert "shell=False" in runtime
    assert "weights_after = file_sha256(weights)" in runtime
    for script_name, _, _ in WORKLOAD_SCRIPTS.values():
        script = (root / "experiments/paper3/lunarc" / script_name).read_text()
        assert not any(line.lstrip().startswith("sbatch ") for line in script.splitlines())
        assert "gated_workload_runtime.py" in script


def test_new_schemas_are_valid_and_submission_receipt_validates(tmp_path: Path) -> None:
    manifest, gate = build_world(tmp_path, "training")
    receipt = invoke(manifest, gate, Runner(), submit=False)
    root = Path(__file__).resolve().parents[1]
    for name in (
        "paper3-lunarc-workload-manifest.schema.json",
        "paper3-lunarc-workload-receipt.schema.json",
        "paper3-lunarc-workload-submission-receipt.schema.json",
    ):
        schema = json.loads((root / "schemas" / name).read_text())
        Draft202012Validator.check_schema(schema)
    receipt_schema = json.loads((root / "schemas/paper3-lunarc-workload-submission-receipt.schema.json").read_text())
    Draft202012Validator(receipt_schema, format_checker=FormatChecker()).validate(receipt)


def test_gate_lunarc_audit_is_fail_closed_and_file_bound() -> None:
    root = Path(__file__).resolve().parents[1]
    audit = json.loads(
        (root / "research/receipts/PAPER3_GATE_LUNARC_AUDIT_20260811.json").read_text()
    )
    assert audit["annotation_gate"]["registered_external_annotation_count"] == 0
    assert audit["annotation_gate"]["solicitation"]["comment_count"] == 0
    assert audit["workload_design"]["current_authorization"] is False
    assert audit["lunarc_observation"]["jobs_submitted_by_this_iteration"] == 0
    for key in ("training_template", "inference_template", "allocated_node_runtime", "submission_wrapper"):
        binding = audit["workload_design"][key]
        assert file_sha(root / binding["path"]) == binding["sha256"]
