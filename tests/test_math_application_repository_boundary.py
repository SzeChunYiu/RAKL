from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_APPLICATION_PREFIX = "research/real_math/millennium/"


def _tracked_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(completed.stdout.splitlines())


def test_millennium_application_artifacts_live_only_in_rakl_math() -> None:
    leaked = sorted(
        path
        for path in _tracked_paths()
        if path.startswith(FORBIDDEN_APPLICATION_PREFIX)
    )

    assert leaked == [], (
        "Millennium application artifacts belong in SzeChunYiu/RAKL_math, "
        f"not the reusable RAKL framework repository: {leaked}"
    )
