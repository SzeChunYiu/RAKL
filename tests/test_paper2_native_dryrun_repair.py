from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONTRACT_V3.json"
CONSTRUCTION_RECEIPT = (
    ROOT / "research/paper2_microtrial_v3/CPU_STAGING_CONSTRUCTION_RECEIPT_V3.json"
)
NATIVE_DRYRUN_REPAIR_RECEIPT = (
    ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_DRYRUN_REPAIR_RECEIPT_20260811.json"
)
REMOTE_DIRTY_CHECKOUT_OBSERVATION = (
    ROOT
    / "research/paper2_microtrial_v3/native_receipts/REMOTE_DIRTY_CHECKOUT_OBSERVATION_NATIVE_2FC6457B.json"
)
SCRIPT_ROOT = ROOT / "experiments/paper2/lunarc"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_repository_module_invocation_disables_python_bytecode() -> None:
    module_command = re.compile(r"\bpython(?:3)?\s+-m\s+rakl(?:\.|\b)")
    array_declaration = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=\([^\n]*$")
    guarded_module_commands: list[tuple[Path, str]] = []

    for path in sorted(SCRIPT_ROOT.iterdir()):
        if path.suffix not in {".sh", ".sbatch"}:
            continue
        source = path.read_text(encoding="utf-8")
        # Continuations form one shell command and must be inspected together.
        logical_source = re.sub(r"\\\n[ \t]*", " ", source)
        logical_lines = logical_source.splitlines()
        for line_number, line in enumerate(logical_lines, start=1):
            match = module_command.search(line)
            if match is None:
                continue
            command_prefix = line[: match.start()]
            if "PYTHONDONTWRITEBYTECODE=1" in command_prefix:
                guarded_module_commands.append((path, line))
                continue

            declaration = array_declaration.search(command_prefix)
            assert declaration is not None, (
                f"{path}:{line_number}: repository module invocation is not protected by "
                "PYTHONDONTWRITEBYTECODE=1"
            )
            array_name = declaration.group(1)
            guarded_expansion = re.compile(
                rf"(?m)^[^\n]*\bPYTHONDONTWRITEBYTECODE=1\b[^\n]*"
                rf'\"?\$\{{{re.escape(array_name)}\[@\]\}}\"?[^\n]*$'
            )
            assert guarded_expansion.search(logical_source), (
                f"{path}:{line_number}: command array {array_name!r} contains a repository "
                "module invocation but is not executed with PYTHONDONTWRITEBYTECODE=1"
            )
            guarded_module_commands.append((path, line))

    assert guarded_module_commands, "no repository module invocations were inspected"


def test_repository_module_invocation_does_not_mutate_copied_source_tree(
    tmp_path: Path,
) -> None:
    copied_src = tmp_path / "src"
    shutil.copytree(
        ROOT / "src",
        copied_src,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(copied_src)

    completed = subprocess.run(
        [sys.executable, "-m", "rakl.paper2_cpu_staging", "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Paper 2 CPU staging V3" in completed.stdout
    assert not list(copied_src.rglob("__pycache__"))
    assert not list(copied_src.rglob("*.py[co]"))


def test_native_dryrun_repair_receipt_binds_negative_history_and_current_repair() -> None:
    repair_receipt = _load(NATIVE_DRYRUN_REPAIR_RECEIPT)
    expected_native = {
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_2FC6457B.json": (
            "6c76c22ecc36f36c7b42ed998b819d5c91d8306de1095597069d234092453fdf",
            "BOOTSTRAP_PASS_ATOMICALLY_PROMOTED",
        ),
        "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_2FC6457B.json": (
            "5e102ec6e1d0f6145e4c19d5e45f989c30fd236a4d7975d0de05c2aa84b1f445",
            "REFUSE_PREFLIGHT_VALIDATION",
        ),
        "research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_REPEAT_REFUSAL_NATIVE_2FC6457B.json": (
            "1d0db23b1426fbcb32e6ec9b3b9638ad21825cb95596a7c7fda8f2b117e4a2dc",
            "BOOTSTRAP_FAILURE",
        ),
    }
    observed_native = {item["path"]: item for item in repair_receipt["native_receipts"]}
    assert set(observed_native) == set(expected_native)
    for relative_path, (expected_hash, expected_verdict) in expected_native.items():
        native_path = ROOT / relative_path
        native_item = observed_native[relative_path]
        assert native_item["sha256"] == expected_hash
        assert hashlib.sha256(native_path.read_bytes()).hexdigest() == expected_hash
        assert native_item["verdict"] == expected_verdict
        assert _load(native_path)["verdict"] == expected_verdict

    assert repair_receipt["old_contract_canonical_sha256"] == (
        "3ba31a201a5574cf4a8f2ec96424e19d31656ebd68705bb8d27bc589a72c0057"
    )
    preserved_submission = _load(
        ROOT
        / "research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_2FC6457B.json"
    )
    assert preserved_submission["contract_canonical_sha256"] == repair_receipt[
        "old_contract_canonical_sha256"
    ]
    contract = _load(CONTRACT)
    contract_canonical_hash = hashlib.sha256(
        json.dumps(
            contract,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    refreshed = repair_receipt["refreshed_contract"]
    assert refreshed["path"] == str(CONTRACT.relative_to(ROOT))
    assert refreshed["file_sha256"] == hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    assert refreshed["canonical_sha256"] == contract_canonical_hash
    assert refreshed["construction_receipt_path"] == str(CONSTRUCTION_RECEIPT.relative_to(ROOT))
    assert refreshed["construction_receipt_sha256"] == hashlib.sha256(
        CONSTRUCTION_RECEIPT.read_bytes()
    ).hexdigest()

    construction_receipt = _load(CONSTRUCTION_RECEIPT)
    assert construction_receipt["contract_file_sha256"] == refreshed["file_sha256"]
    assert construction_receipt["contract_canonical_sha256"] == refreshed["canonical_sha256"]
    assert repair_receipt["execution_counts"] == {
        "evaluated_result_records": 0,
        "jobs_submitted": 0,
        "model_executions": 0,
    }
    assert construction_receipt["jobs_submitted"] == 0
    assert construction_receipt["model_execution_performed"] is False
    assert construction_receipt["evaluated_result_record_count"] == 0

    fixed_artifacts = repair_receipt["repair"]["fixed_artifacts"]
    assert {item["path"] for item in fixed_artifacts} == {
        "experiments/paper2/lunarc/submit_cpu_staging_v3.sh",
        "experiments/paper2/lunarc/network_probe.sbatch",
        "experiments/paper2/lunarc/stage_cpu_assets.sbatch",
        "experiments/paper2/lunarc/harvest_cpu_staging_v3.sh",
    }
    for artifact in fixed_artifacts:
        assert artifact["sha256"] == hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()

    assert repair_receipt["verdict"] == (
        "NATIVE_DRYRUN_FALSIFIER_PRESERVED__REPAIR_READY_NOT_SUBMITTED"
    )
    assert "not native staging success" in repair_receipt["claim_boundary"].lower()
    assert "not submitted" in construction_receipt["verdict"].lower().replace("_", " ")
    assert contract["authority_status"] == "frozen_ready_not_submitted"

    remote_observation = _load(REMOTE_DIRTY_CHECKOUT_OBSERVATION)
    remote_boundary = repair_receipt["remote_state_boundary"]
    assert remote_boundary["observation_receipt_path"] == str(
        REMOTE_DIRTY_CHECKOUT_OBSERVATION.relative_to(ROOT)
    )
    assert remote_boundary["observation_receipt_sha256"] == hashlib.sha256(
        REMOTE_DIRTY_CHECKOUT_OBSERVATION.read_bytes()
    ).hexdigest()
    assert remote_observation["observation_mode"] == "read_only"
    assert remote_observation["remote_mutation_performed"] is False
    assert remote_observation["repo_sha"] == repair_receipt["subject_base_sha"]
    assert remote_observation["tracked_change_count"] == 0
    assert remote_observation["untracked_change_count"] == 24
    assert remote_observation["untracked_pyc_count"] == 24
    assert remote_observation["only_observed_checkout_changes_are_untracked_pyc"] is True
    assert len(remote_observation["untracked_pyc_files"]) == 24
    assert {item["path"] for item in remote_observation["untracked_pyc_files"]} == {
        line.removeprefix("?? ") for line in remote_observation["git_status_porcelain_v1"]
    }
    assert all(re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) for item in remote_observation["untracked_pyc_files"])
    status_bytes = (
        "\n".join(remote_observation["git_status_porcelain_v1"]) + "\n"
    ).encode()
    assert remote_observation["git_status_porcelain_v1_sha256"] == hashlib.sha256(
        status_bytes
    ).hexdigest()
    root_cause_basis = repair_receipt["native_observation"]["root_cause_basis"]
    assert root_cause_basis["read_only_remote_observation_sha256"] == remote_boundary[
        "observation_receipt_sha256"
    ]
    assert root_cause_basis["sole_cause_claimed"] is False
    assert (
        repair_receipt["created_at_utc"]
        < remote_observation["observed_at_utc"]
        < repair_receipt["finalized_at_utc"]
    )


