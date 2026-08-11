from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research" / "paper2_experience_benchmark_v1"
FREEZE = ROOT / "experiments" / "paper2" / "freeze_experience_benchmark_protocol.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_experience_benchmark_protocol_freeze_check_only() -> None:
    result = run(str(FREEZE), "--check-only")
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "PROTOCOL_FREEZE_CHECK_PASS"
    assert len(payload["protocol_subject_hash"]) == 64

    packet = json.loads((PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    receipt = json.loads((PACKET_DIR / "PROTOCOL_FREEZE_RECEIPT.json").read_text(encoding="utf-8"))
    assert packet["arms"] == ["RESET_BASELINE", "LEARNING_ENABLED"]
    assert packet["development_task_ids"] == ["D1", "D2", "D3"]
    assert packet["transfer_task_ids"] == ["T1", "T2", "T3"]
    assert set(packet["development_task_ids"]).isdisjoint(packet["transfer_task_ids"])
    assert packet["runs"] == []
    assert packet["frozen_before_runs"] is True
    assert packet["learned_state_after_development_hash"].startswith("PENDING_")
    assert packet["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert packet["v4_1_pendulum_compatibility"]["score_reuse_allowed"] is False
    assert receipt["verdict"] == "PROTOCOL_FREEZE_PASS"
    assert receipt["empirical_section_b_status"] == "NOT_DONE"
    assert receipt["protocol_subject_hash"] == packet["protocol_subject_hash"]
    assert receipt["runs_present"] is False
    assert "3476520" in str(packet["v4_1_pendulum_compatibility"]["jobs_explicitly_not_experience_evidence"])


def test_experience_benchmark_protocol_freeze_refuses_result_jsonl(tmp_path: Path) -> None:
    # Copy minimal packet tree into tmp and plant a forbidden runs.jsonl.
    import shutil

    staging = tmp_path / "packet"
    shutil.copytree(PACKET_DIR, staging)
    (staging / "runs.jsonl").write_text("{}\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(FREEZE), "--packet-dir", str(staging)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode != 0
    assert "REFUSED" in (proc.stderr + proc.stdout)
