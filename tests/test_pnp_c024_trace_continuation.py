from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/p_vs_np/09_trace"


def _load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_c024_trace_continues_strict_pre_candidate_trace_without_backfill() -> None:
    parent = _load("O9d12a2a1_PRE_CANDIDATE_TRACE_20260811.json")
    continuation = _load("O9d12a2a1_C024_TRACE_CONTINUATION_20260811.json")

    terminal = parent["entries"][-1]["artifact_hash"]
    assert continuation["parent_trace_id"] == parent["trace_id"]
    assert continuation["parent_terminal_hash"] == terminal

    previous = terminal
    expected_types = [
        "CANDIDATE_PROPOSED",
        "FALSIFIER_RUN",
        "RESULT_RECORDED",
        "RESIDUAL_OPENED",
    ]
    assert [entry["event_type"] for entry in continuation["entries"]] == expected_types

    for entry in continuation["entries"]:
        assert entry["previous_event_hash"] == previous
        payload = copy.deepcopy(entry)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash
