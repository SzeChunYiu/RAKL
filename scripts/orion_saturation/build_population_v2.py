"""Population construction, v2 — instrument repair.

v1 used `simp only [gold]` as the solve interface and as the gold-solvability
control. That control passed on 4 of 1406 well-posed candidates, because a
theorem's proof-term constants are not a simp set that reproduces its proof.
The control did its job: it caught a dead solve interface *before* any arm was
run. v1's interface is recorded as refuted rather than deleted.

v2 uses `simp [P]` and defines the population two-sidedly, so every retained
task has a real gap that premise selection has to close:

  1. well-posedness   — `exact <OriginalName>` is accepted (pp round-trip is faithful)
  2. GAP EXISTS       — `simp` with no extra premises FAILS
  3. GAP IS CLOSEABLE — `simp [gold]` SUCCEEDS

Filters 2 and 3 are two-sided controls on the interface: the floor is not
trivially solvable and the ceiling is reachable. Neither consults any arm.
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
MIN_GOLD, MAX_GOLD = 1, 8
POP_HEARTBEATS = 200000


def _batch(args):
    tasks, mathlib, work, tag = args
    return check(tasks, mathlib_dir=Path(mathlib), work_dir=Path(work), tag=tag,
                 max_heartbeats=POP_HEARTBEATS, timeout_s=3600)


def run(tasks, mathlib, work, prefix, workers):
    batches = [tasks[i:i + 120] for i in range(0, len(tasks), 120)]
    payload = [(b, str(mathlib), str(work), f"{prefix}_{i}") for i, b in enumerate(batches)]
    out = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(_batch, payload):
            out.update(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    for a in ("raw", "corpus", "mathlib", "work", "out"):
        ap.add_argument(f"--{a}", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    corpus_names = {json.loads(l)["name"]
                    for l in Path(args.corpus).read_text().splitlines() if l}
    raw = [json.loads(l) for l in Path(args.raw).read_text().splitlines() if l]

    cands = []
    for r in raw:
        stmt = " ".join(r["stmt"].split())
        if "✝" in stmt or "sorry" in stmt or len(stmt) > MAX_STMT_CHARS:
            continue
        gold = sorted({g for g in r["gold"] if g in corpus_names and g != r["name"]})
        if not (MIN_GOLD <= len(gold) <= MAX_GOLD):
            continue
        cands.append({"name": r["name"], "module": r["module"], "stmt": stmt, "gold": gold})
    print(f"raw={len(raw)} cheap={len(cands)}", flush=True)

    ids = {c["name"]: f"T{i}" for i, c in enumerate(cands)}
    mathlib, work = Path(args.mathlib), Path(args.work)

    wp = run([LeanTask(ids[c["name"]], c["stmt"], f"exact {c['name']}") for c in cands],
             mathlib, work, "v2wp", args.workers)
    cands = [c for c in cands if wp.get(ids[c["name"]])]
    print(f"well_posed={len(cands)}", flush=True)

    floor = run([LeanTask(ids[c["name"]], c["stmt"], "simp") for c in cands],
                mathlib, work, "v2floor", args.workers)
    cands = [c for c in cands if not floor.get(ids[c["name"]])]
    print(f"gap_exists (simp alone fails)={len(cands)}", flush=True)

    ceil = run([LeanTask(ids[c["name"]], c["stmt"], f"simp [{', '.join(c['gold'])}]")
                for c in cands], mathlib, work, "v2ceil", args.workers)
    keep = [c for c in cands if ceil.get(ids[c["name"]])]
    print(f"gap_closeable (simp [gold] succeeds)={len(keep)}", flush=True)

    with Path(args.out).open("w") as fh:
        for c in sorted(keep, key=lambda c: c["name"]):
            c["task_id"] = ids[c["name"]]
            fh.write(json.dumps(c) + "\n")


if __name__ == "__main__":
    main()
