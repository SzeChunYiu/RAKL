import json
import os
import subprocess
import sys
from pathlib import Path

from rakl.cli import main


def test_python_module_entrypoint_lists_profiles():
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root / "src") + (os.pathsep + existing if existing else "")
    completed = subprocess.run(
        [sys.executable, "-m", "rakl", "profiles"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert any(profile["profile_id"] == "ordinary-8k" for profile in payload["profiles"])


def test_cli_reference_workflow_end_to_end(tmp_path, capsys):
    root = tmp_path / "project"
    source = tmp_path / "source.txt"
    refutation = tmp_path / "refutation.txt"
    packet_file = tmp_path / "packet.json"
    source.write_text("Observation A supports representation R.", encoding="utf-8")
    refutation.write_text("Prior experiment refuted mechanism M.", encoding="utf-8")

    assert main(["init", str(root), "--project-id", "demo", "--profile", "ordinary-8k"]) == 0
    capsys.readouterr()

    assert main([
        "ingest",
        str(root),
        str(source),
        "--record-id",
        "source-A",
        "--tokens",
        "20",
        "--fiber",
        "mechanism",
        "--coverage",
        "representation_R",
    ]) == 0
    capsys.readouterr()

    assert main([
        "ingest",
        str(root),
        str(refutation),
        "--record-id",
        "negative-M",
        "--tokens",
        "20",
        "--kind",
        "FAILURE",
        "--coverage",
        "negative_history",
        "--mandatory",
    ]) == 0
    capsys.readouterr()

    assert main(["doctor", str(root)]) == 0
    doctor = json.loads(capsys.readouterr().out)
    assert doctor["healthy"] is True
    assert doctor["record_count"] == 2

    assert main([
        "packet",
        str(root),
        "--operation",
        "contradiction_diagnosis",
        "--question",
        "Does representation R identify mechanism M?",
        "--budget",
        "100",
        "--fiber",
        "mechanism",
        "--require",
        "negative_history",
        "--output",
        str(packet_file),
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "READY"
    packet = json.loads(packet_file.read_text("utf-8"))
    assert packet["authority_boundary"]["llm_output_authority"] == "PROPOSAL_ONLY"
    assert {record["record_id"] for record in packet["selected_records"]} == {
        "source-A",
        "negative-M",
    }

    assert main(["status", str(root)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["healthy"] is True
    assert status["record_count"] == 2
    assert status["reference_profile"] == "ordinary-8k"


def test_cli_check_profile_is_honest_about_unknowns(capsys):
    code = main([
        "check-profile",
        "--profile",
        "ordinary-8k",
        "--model-id",
        "unknown",
        "--instruction-following",
        "yes",
        "--json-output",
        "yes",
        "--native-tool-calls",
        "no",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert code == 3
    assert payload["verdict"] == "CANNOT_CHECK"
    assert "context_window_tokens" in payload["unknown_requirements"]
