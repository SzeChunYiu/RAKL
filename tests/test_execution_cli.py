import json
import sys
from pathlib import Path

from rakl.cli import main
from rakl.project_runtime import RAKLProject


def test_cli_run_roundtrip_and_replay(tmp_path, capsys):
    root = tmp_path / "project"
    project = RAKLProject.create(root, project_id="p")
    packet = tmp_path / "packet.json"
    packet.write_text(
        project.canonical_packet_json(
            {
                "packet_version": "rakl-task-packet-v1",
                "question": "test question",
                "authority_boundary": {"llm_output_authority": "PROPOSAL_ONLY"},
            }
        ),
        encoding="utf-8",
    )
    counter = tmp_path / "counter.txt"
    output = tmp_path / "output.json"
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json,sys\n"
        "from pathlib import Path\n"
        "c=Path(sys.argv[1])\n"
        "n=int(c.read_text() if c.exists() else '0')+1\n"
        "c.write_text(str(n))\n"
        "e=json.load(sys.stdin)\n"
        "p=e['task_packet']\n"
        "print(json.dumps({'proposal':'ok','question':p['question'],'count':n,'temperature':e['generation_config']['temperature']}))\n",
        encoding="utf-8",
    )

    argv = [
        "run",
        str(root),
        str(packet),
        "--runner-id",
        "local-test",
        "--model-id",
        "fake-model",
        "--model-version",
        "v1",
        "--exec",
        sys.executable,
        "--arg",
        str(runner),
        "--arg",
        str(counter),
        "--config-json",
        '{"temperature":0}',
        "--output",
        str(output),
    ]
    assert main(argv) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "COMPLETED"
    assert first["replayed"] is False
    assert first["receipt"]["output_authority"] == "PROPOSAL_ONLY"
    assert first["receipt"]["generation_config_authority"] == "DELIVERED_TO_RUNNER_PROTOCOL"
    result = json.loads(output.read_text("utf-8"))
    assert result["proposal"] == "ok"
    assert result["temperature"] == 0

    assert main(argv) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "COMPLETED"
    assert second["replayed"] is True
    assert second["invocation_id"] == first["invocation_id"]
    assert counter.read_text() == "1"
