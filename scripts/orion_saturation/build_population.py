"""Construct the task population, Lean-verified, before any arm is run.

Two filters, both adjudicated by Lean rather than by us:

  1. well-posedness — the pretty-printed statement must re-elaborate and be
     closed by ``exact <OriginalName>``. This proves the round-trip through the
     pretty-printer did not change the goal.
  2. gold-solvability — ``simp only [<gold premises>]`` must close the goal.
     This is the *control*: it establishes that the solve interface can succeed
     at all, so a later null cannot be dismissed as a dead harness.

Both filters are deterministic given the frozen module list, so the population
is not cherry-picked. Neither filter consults the two comparison arms.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_check import LeanTask, check  # noqa: E402

MAX_STMT_CHARS = 400
MIN_GOLD = 1
MAX_GOLD = 8


def _batch_check(args) -> dict[str, bool]:
    tasks, mathlib_dir, work_dir, tag = args
    return check(
        tasks,
        mathlib_dir=Path(mathlib_dir),
        work_dir=Path(work_dir),
        tag=tag,
        timeout_s=3600,
    )


def run_checks(
    tasks: list[LeanTask], mathlib_dir: Path, work_dir: Path, prefix: str, workers: int
) -> dict[str, bool]:
    batches = [tasks[i : i + 120] for i in range(0, len(tasks), 120)]
    payload = [
        (b, str(mathlib_dir), str(work_dir), f"{prefix}_{i}") for i, b in enumerate(batches)
    ]
    out: dict[str, bool] = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(_batch_check, payload):
            out.update(result)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--mathlib", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    corpus_names = {
        json.loads(line)["name"] for line in Path(args.corpus).read_text().splitlines() if line
    }

    raw = [json.loads(l) for l in Path(args.raw).read_text().splitlines() if l]
    cands = []
    for r in raw:
        stmt = r["stmt"]
        if "✝" in stmt or "sorry" in stmt or len(stmt) > MAX_STMT_CHARS:
            continue
        if "\n" in stmt:
            stmt = " ".join(stmt.split())
        gold = sorted({g for g in r["gold"] if g in corpus_names and g != r["name"]})
        if not (MIN_GOLD <= len(gold) <= MAX_GOLD):
            continue
        cands.append({"name": r["name"], "module": r["module"], "stmt": stmt, "gold": gold})

    print(f"raw={len(raw)} after_cheap_filters={len(cands)}", flush=True)

    ids = {c["name"]: f"T{i}" for i, c in enumerate(cands)}
    mathlib_dir, work_dir = Path(args.mathlib), Path(args.work)

    wp = run_checks(
        [LeanTask(ids[c["name"]], c["stmt"], f"exact {c['name']}") for c in cands],
        mathlib_dir, work_dir, "wellposed", args.workers,
    )
    cands = [c for c in cands if wp.get(ids[c["name"]], False)]
    print(f"well_posed={len(cands)}", flush=True)

    gs = run_checks(
        [
            LeanTask(ids[c["name"]], c["stmt"], f"simp only [{', '.join(c['gold'])}]")
            for c in cands
        ],
        mathlib_dir, work_dir, "goldsolve", args.workers,
    )
    solvable = [c for c in cands if gs.get(ids[c["name"]], False)]
    print(f"gold_solvable={len(solvable)}", flush=True)

    with Path(args.out).open("w") as fh:
        for c in sorted(solvable, key=lambda c: c["name"]):
            c["task_id"] = ids[c["name"]]
            fh.write(json.dumps(c) + "\n")


if __name__ == "__main__":
    main()
