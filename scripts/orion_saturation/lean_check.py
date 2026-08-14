"""Batch Lean adjudication.

The only thing that decides whether a goal is solved is the Lean kernel. This
module emits a file of independent ``example`` declarations and reports, per
declaration, whether Lean accepted it. Nothing in RAKL participates in that
judgement.

Declarations are separated by sentinel comment lines so an error can be mapped
back to the declaration whose line range contains it. Lean recovers at
declaration boundaries, so one failing example does not mask its neighbours.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

# `sorry` must be treated as a failure, not a warning; the linters are noise.
_ERROR_RE = re.compile(r"^(?P<file>[^\n:]+):(?P<line>\d+):(?P<col>\d+): error:", re.MULTILINE)
_SORRY_RE = re.compile(
    r"^(?P<file>[^\n:]+):(?P<line>\d+):(?P<col>\d+): warning: declaration uses 'sorry'",
    re.MULTILINE,
)

HEADER = """import Mathlib.Data.List.Basic
import Mathlib.Data.Nat.Defs
import Mathlib.Data.Set.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Group.Basic
import Mathlib.Logic.Basic

set_option linter.all false
set_option maxRecDepth 4000
"""


@dataclass(frozen=True)
class LeanTask:
    task_id: str
    statement: str
    tactic: str


def _render(tasks: list[LeanTask], max_heartbeats: int) -> tuple[str, dict[str, tuple[int, int]]]:
    lines = HEADER.split("\n")
    spans: dict[str, tuple[int, int]] = {}
    for task in tasks:
        start = len(lines) + 1
        lines.append(f"-- BEGIN {task.task_id}")
        lines.append(f"set_option maxHeartbeats {max_heartbeats} in")
        lines.append(f"example : {task.statement} := by")
        lines.append(f"  {task.tactic}")
        lines.append(f"-- END {task.task_id}")
        spans[task.task_id] = (start, len(lines))
    return "\n".join(lines) + "\n", spans


def check(
    tasks: list[LeanTask],
    *,
    mathlib_dir: Path,
    work_dir: Path,
    max_heartbeats: int = 400000,
    timeout_s: int = 3600,
    tag: str = "batch",
) -> dict[str, bool]:
    """Return ``{task_id: solved}``. A task is solved iff Lean reports no error
    and no ``sorry`` inside its line span."""
    if not tasks:
        return {}
    source, spans = _render(tasks, max_heartbeats)
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / f"probe_{tag}.lean"
    path.write_text(source)

    proc = subprocess.run(
        ["lake", "env", "lean", str(path)],
        cwd=mathlib_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    output = proc.stdout + proc.stderr

    bad_lines: set[int] = set()
    for match in list(_ERROR_RE.finditer(output)) + list(_SORRY_RE.finditer(output)):
        bad_lines.add(int(match.group("line")))

    results: dict[str, bool] = {}
    for task_id, (start, end) in spans.items():
        results[task_id] = not any(start <= line <= end for line in bad_lines)

    # A whole-file failure (e.g. the process was killed) must never be reported
    # as "everything solved".
    if proc.returncode != 0 and not bad_lines:
        raise RuntimeError(
            f"lean exited {proc.returncode} with no locatable errors; refusing to "
            f"score this batch. tail={output[-2000:]}"
        )
    return results
