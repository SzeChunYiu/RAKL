from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "research" / "glm52_mechanism_suite_v1"


def test_v1_directory_unmodified_on_branch() -> None:
    result = subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", str(V1.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_v1_protocol_still_registered() -> None:
    text = (V1 / "PROTOCOL.json").read_text(encoding="utf-8")
    assert "GLM52-MECHANISM-SUITE-V1" in text
    assert "72bd139f" not in text
    assert "ANTHROPIC_AUTH_TOKEN" not in text
