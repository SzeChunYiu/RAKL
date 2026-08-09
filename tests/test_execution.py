import json
import os
import sys
from pathlib import Path

import pytest

from rakl.execution import (
    ExecutionLedger,
    ExecutionManager,
    ExecutionSpec,
    ExecutionStatus,
    RunnerContract,
)
from rakl.project_runtime import RAKLProject


def _packet(label="one") -> bytes:
    return json.dumps(
        {
            "packet_version": "rakl-task-packet-v1",
            "question": label,
            "authority_boundary": {"llm_output_authority": "PROPOSAL_ONLY"},
        },
        sort_keys=True,
    ).encode()


def _write_script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / f"runner-{len(list(tmp_path.glob('runner-*.py')))}.py"
    path.write_text(body, encoding="utf-8")
    return path


def _contract(script: Path, *args: str, **kwargs) -> RunnerContract:
    return RunnerContract(
        runner_id=kwargs.pop("runner_id", "test-runner"),
        model_id=kwargs.pop("model_id", "test-model"),
        model_version=kwargs.pop("model_version", "v1"),
        argv=(sys.executable, str(script), *args),
        **kwargs,
    )


def test_successful_json_runner_receipt_binds_subjects_and_authority(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(
        tmp_path,
        "import json,sys\np=json.load(sys.stdin)\nprint(json.dumps({'proposal':'ok','question':p['question']}))\n",
    )
    manager = ExecutionManager(project)
    packet = _packet("science")
    result = manager.execute(
        packet_bytes=packet,
        runner=_contract(script),
        generation_config={"temperature": 0},
    )
    assert result.status == ExecutionStatus.COMPLETED
    assert not result.replayed
    receipt = result.receipt
    assert receipt is not None
    assert receipt.packet_sha256 == project.store.put_bytes(packet).sha256
    assert receipt.runner["shell"] is False
    assert receipt.runner["model_id"] == "test-model"
    assert receipt.output_authority == "PROPOSAL_ONLY"
    assert receipt.may_promote_canonical_knowledge is False
    assert receipt.stdout_sha256 is not None
    assert json.loads(manager.read_stdout(receipt))["proposal"] == "ok"


def test_completed_replay_does_not_execute_command_twice(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    counter = tmp_path / "counter.txt"
    script = _write_script(
        tmp_path,
        "import json,sys\nfrom pathlib import Path\nc=Path(sys.argv[1])\nn=int(c.read_text() if c.exists() else '0')+1\nc.write_text(str(n))\njson.load(sys.stdin)\nprint(json.dumps({'proposal':'ok','count':n}))\n",
    )
    contract = _contract(script, str(counter))
    manager = ExecutionManager(project)
    first = manager.execute(packet_bytes=_packet(), runner=contract)
    second = manager.execute(packet_bytes=_packet(), runner=contract)
    assert first.status == ExecutionStatus.COMPLETED
    assert second.status == ExecutionStatus.COMPLETED
    assert second.replayed
    assert counter.read_text() == "1"
    assert second.receipt == first.receipt


def test_changed_packet_changes_invocation_identity(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "import json,sys\njson.load(sys.stdin)\nprint('{}')\n")
    manager = ExecutionManager(project)
    contract = _contract(script)
    a = manager.build_spec(packet_bytes=_packet("a"), runner=contract)
    b = manager.build_spec(packet_bytes=_packet("b"), runner=contract)
    assert a.invocation_id != b.invocation_id


def test_changed_generation_config_changes_invocation_identity(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('{}')\n")
    manager = ExecutionManager(project)
    contract = _contract(script)
    a = manager.build_spec(packet_bytes=_packet(), runner=contract, generation_config={"temperature": 0})
    b = manager.build_spec(packet_bytes=_packet(), runner=contract, generation_config={"temperature": 1})
    assert a.invocation_id != b.invocation_id


def test_timeout_is_explicit_and_preserves_partial_output(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(
        tmp_path,
        "import sys,time\nsys.stdout.write('partial')\nsys.stdout.flush()\ntime.sleep(2)\n",
    )
    manager = ExecutionManager(project)
    result = manager.execute(
        packet_bytes=_packet(),
        runner=_contract(script, timeout_seconds=0.05, expects_json=False),
    )
    assert result.status == ExecutionStatus.TIMED_OUT
    assert result.receipt is not None
    assert result.receipt.exit_code is None
    assert manager.read_stdout(result.receipt).startswith(b"partial")


def test_nonzero_exit_is_explicit_failure_and_preserves_streams(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(
        tmp_path,
        "import sys\nsys.stdout.write('{\"proposal\":\"not-authoritative\"}')\nsys.stderr.write('failure')\nsys.exit(3)\n",
    )
    manager = ExecutionManager(project)
    result = manager.execute(packet_bytes=_packet(), runner=_contract(script))
    assert result.status == ExecutionStatus.FAILED_PROCESS
    assert result.receipt.exit_code == 3
    assert b"not-authoritative" in manager.read_stdout(result.receipt)
    assert manager.read_stderr(result.receipt) == b"failure"
    assert result.receipt.output_authority == "PROPOSAL_ONLY"


def test_malformed_json_is_protocol_failure_with_raw_output(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('not-json')\n")
    manager = ExecutionManager(project)
    result = manager.execute(packet_bytes=_packet(), runner=_contract(script))
    assert result.status == ExecutionStatus.FAILED_PROTOCOL
    assert result.receipt.protocol_valid is False
    assert manager.read_stdout(result.receipt).strip() == b"not-json"


def test_missing_executable_is_failed_start_without_fabricated_output(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    contract = RunnerContract(
        runner_id="missing",
        model_id="m",
        model_version="v",
        argv=(str(tmp_path / "definitely-missing-executable"),),
    )
    result = ExecutionManager(project).execute(packet_bytes=_packet(), runner=contract)
    assert result.status == ExecutionStatus.FAILED_START
    assert result.receipt.stdout_sha256 is None
    assert result.receipt.stderr_sha256 is None


def test_interrupted_non_idempotent_prepared_run_blocks_retry(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    counter = tmp_path / "counter.txt"
    script = _write_script(
        tmp_path,
        "import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text('ran')\nprint('{}')\n",
    )
    contract = _contract(script, str(counter), retry_safe=False)
    packet = _packet()
    spec = ExecutionSpec.build(packet_bytes=packet, runner=contract)
    ledger = ExecutionLedger(project, spec)
    ledger.ensure_spec()
    ledger.append(attempt=1, status=ExecutionStatus.PREPARED)

    result = ExecutionManager(project).execute(packet_bytes=packet, runner=contract)
    assert result.status == ExecutionStatus.RECOVERY_REQUIRED
    assert result.receipt is None
    assert not counter.exists()


def test_retry_safe_prepared_run_can_continue_with_new_attempt(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "import json,sys\njson.load(sys.stdin)\nprint('{}')\n")
    contract = _contract(script, retry_safe=True)
    packet = _packet()
    spec = ExecutionSpec.build(packet_bytes=packet, runner=contract)
    ledger = ExecutionLedger(project, spec)
    ledger.ensure_spec()
    ledger.append(attempt=1, status=ExecutionStatus.PREPARED)

    result = ExecutionManager(project).execute(packet_bytes=packet, runner=contract)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.receipt.attempt == 2
    attempts = [event.attempt for event, _ in ledger.events()]
    assert 1 in attempts and 2 in attempts


def test_running_state_never_auto_retries_even_when_retry_safe(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('{}')\n")
    contract = _contract(script, retry_safe=True)
    packet = _packet()
    spec = ExecutionSpec.build(packet_bytes=packet, runner=contract)
    ledger = ExecutionLedger(project, spec)
    ledger.ensure_spec()
    ledger.append(attempt=1, status=ExecutionStatus.PREPARED)
    ledger.append(attempt=1, status=ExecutionStatus.RUNNING)
    result = ExecutionManager(project).execute(packet_bytes=packet, runner=contract)
    assert result.status == ExecutionStatus.RECOVERY_REQUIRED
    assert result.reason == "prior_attempt_may_still_have_executed"


def test_secret_environment_value_is_not_logged(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(
        tmp_path,
        "import json,os,sys\njson.load(sys.stdin)\nassert os.environ['RAKL_TEST_SECRET']\nprint('{}')\n",
    )
    secret = "super-secret-value-that-must-not-be-in-receipts"
    contract = _contract(
        script,
        allowed_env_names=("RAKL_TEST_SECRET",),
        environment_revision="test-secret-v1",
    )
    result = ExecutionManager(project).execute(
        packet_bytes=_packet(),
        runner=contract,
        environment={"RAKL_TEST_SECRET": secret},
    )
    assert result.status == ExecutionStatus.COMPLETED
    receipt_text = json.dumps(result.receipt.to_dict(), sort_keys=True)
    assert secret not in receipt_text
    assert "RAKL_TEST_SECRET" in receipt_text
    for ref in (project.rakl_dir / "runs" / result.invocation_id).rglob("*.ref"):
        assert secret not in ref.read_text("utf-8")


def test_shell_metacharacters_are_passed_as_literal_argv(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    marker = tmp_path / "SHOULD_NOT_EXIST"
    literal = f";touch {marker}"
    script = _write_script(
        tmp_path,
        "import json,sys\njson.load(sys.stdin)\nprint(json.dumps({'arg':sys.argv[1]}))\n",
    )
    result = ExecutionManager(project).execute(
        packet_bytes=_packet(),
        runner=_contract(script, literal),
    )
    assert result.status == ExecutionStatus.COMPLETED
    assert json.loads(ExecutionManager(project).read_stdout(result.receipt))["arg"] == literal
    assert not marker.exists()


def test_receipt_reference_tamper_is_detected(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('{}')\n")
    manager = ExecutionManager(project)
    contract = _contract(script)
    result = manager.execute(packet_bytes=_packet(), runner=contract)
    assert result.receipt is not None
    spec = manager.build_spec(packet_bytes=_packet(), runner=contract)
    ledger = ExecutionLedger(project, spec)
    ledger.receipt_ref.write_text("0" * 64 + "\n", encoding="utf-8")
    with pytest.raises(KeyError):
        ledger.load_receipt()


def test_output_never_gains_authority_from_zero_exit(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('{\"claim\":\"I am true\"}')\n")
    result = ExecutionManager(project).execute(packet_bytes=_packet(), runner=_contract(script))
    assert result.status == ExecutionStatus.COMPLETED
    assert result.receipt.output_authority == "PROPOSAL_ONLY"
    assert result.receipt.may_promote_canonical_knowledge is False


def test_environment_not_allowlisted_is_rejected_before_execution(tmp_path):
    project = RAKLProject.create(tmp_path / "project", project_id="p")
    script = _write_script(tmp_path, "print('{}')\n")
    with pytest.raises(ValueError):
        ExecutionManager(project).execute(
            packet_bytes=_packet(),
            runner=_contract(script),
            environment={"UNDECLARED": "value"},
        )
