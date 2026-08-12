"""Tests for local Paper III semantic descriptor builder CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "experiments" / "paper3" / "build_semantic_descriptor.py"


def _run_builder(model_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--model-dir",
            str(model_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_local_builder_fails_closed_without_model_assets(tmp_path: Path) -> None:
    proc = _run_builder(tmp_path)
    assert proc.returncode == 0
    receipt = json.loads(proc.stdout)
    assert receipt["status"] == "CANNOT_CHECK_MODEL_ASSET_MISSING"
    assert receipt["descriptors"] == []
    assert receipt["training_authorized"] is False
    assert receipt["label_access"]["evaluated_result_accessed"] is False


def test_local_builder_writes_out_file(tmp_path: Path) -> None:
    out = tmp_path / "descriptor.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--model-dir",
            str(tmp_path / "empty"),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert out.is_file()
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert receipt["status"] == "CANNOT_CHECK_MODEL_ASSET_MISSING"
