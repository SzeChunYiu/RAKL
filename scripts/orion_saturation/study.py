"""Matched-budget ablation: ORION's bounded-saturation stopping rule vs a
uniform fixed-round stop, scored by Lean.

Arm A  saturating   — run retrieval rounds until ``SaturationTracker`` reports
                      SATURATED_SCOPED (or the round schedule is exhausted).
Arm B  uniform      — run exactly ``k`` rounds of the identical schedule, where
                      ``k`` is the population mean of Arm A's round count. Total
                      retrieval spend is therefore matched at the population
                      level; per-task spend differs, which *is* the mechanism.

Both arms fuse the rankings they actually retrieved and hand the tactic exactly
``M_PREMISES`` premises, so the solve interface is budget-identical and a larger
pool cannot win by simply passing more lemmas. Solver effort (maxHeartbeats) is
identical across arms.

The stopping rule is ``rakl.saturation.SaturationTracker`` used unmodified. The
outcome is the Lean kernel's verdict, which no part of RAKL defines.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import json
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_check import LeanTask, check  # noqa: E402
from retrieval import ROUTES, Premise, PremiseIndex, rrf_fuse, run_route  # noqa: E402

# ---- frozen parameters -------------------------------------------------
K_PER_ROUND = 40
M_PREMISES = 16
MAX_HEARTBEATS = 400000
#: Saturation may not be declared before the goal's own vocabulary has been
#: swept. The extended routes are expansions and are optional.
REQUIRED_ROUTES = frozenset({"jaccard", "idf", "rarest"})
SAME_CONTEXT_FLAT_REQUIRED = 2
INDEPENDENT_FLAT_REQUIRED = 1
#: Deepening sweeps per route, after the primary sweep.
DEEPEN_SWEEPS = 3


def load_corpus(path: Path) -> PremiseIndex:
    premises = []
    for line in path.read_text().splitlines():
        if not line:
            continue
        rec = json.loads(line)
        premises.append(Premise(rec["name"], frozenset(rec["ty"])))
    return PremiseIndex(premises)


def _norm(name: str) -> str:
    """Strip decoration that distinguishes a lemma from its trivial variants."""
    base = name.rstrip("'")
    for suffix in ("_iff", "_eq", "_def", "_symm", "_comm", "_self"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base


def forbidden_premises(index: PremiseIndex, name: str) -> frozenset[str]:
    """Self-retrieval guard.

    The task's own theorem lives in the same corpus the retriever searches, and
    every route would rank it first (its type is identical to the goal), so
    ``simp [self]`` would close every goal in both arms and the comparison would
    measure nothing. Trivial restatements of the same lemma leak the same way,
    so near-name variants are excluded too. This is deliberately conservative:
    over-excluding costs recall symmetrically in every arm, whereas
    under-excluding silently manufactures a 100% tie.
    """
    base = _norm(name)
    out = {name}
    for other in index.by_name:
        if other == name:
            continue
        if _norm(other) == base:
            out.add(other)
        elif other.startswith(name + "_") or name.startswith(other + "_"):
            out.add(other)
    return frozenset(out)


def round_schedule(
    index: PremiseIndex, goal: frozenset[str], banned: frozenset[str]
) -> list[dict]:
    """The frozen round schedule: per route, a primary sweep then a deepening
    sweep over the next slice of the same ranking."""
    depth = (1 + DEEPEN_SWEEPS) * K_PER_ROUND
    schedule = []
    for route in ROUTES:
        ranked = [p for p in run_route(index, route, goal, depth + K_PER_ROUND)
                  if p not in banned][:depth]
        schedule.append(
            {"route": route, "ranking": ranked[:K_PER_ROUND], "independent": True,
             "round_id": f"{route}-primary"}
        )
        for s in range(1, DEEPEN_SWEEPS + 1):
            schedule.append(
                {"route": route,
                 "ranking": ranked[s * K_PER_ROUND : (s + 1) * K_PER_ROUND],
                 "independent": False,
                 "round_id": f"{route}-deepen{s}"}
            )
    return schedule


def saturating_rounds(schedule: list[dict]) -> int:
    """Number of rounds ORION's rule consumes. Retrieval only — no outcome."""
    from rakl.saturation import ResearchRound, SaturationState, SaturationTracker

    tracker = SaturationTracker(
        required_routes=REQUIRED_ROUTES,
        same_context_flat_required=SAME_CONTEXT_FLAT_REQUIRED,
        independent_flat_required=INDEPENDENT_FLAT_REQUIRED,
    )
    for i, step in enumerate(schedule, start=1):
        tracker.record(
            ResearchRound.from_objects(
                round_id=step["round_id"],
                route=step["route"],
                context_id=step["route"],
                semantic_objects=step["ranking"],
                independent=step["independent"],
                evidence_lineage=(step["route"],) if step["independent"] else (),
                lineage_complete=step["independent"],
            )
        )
        if tracker.state is SaturationState.SATURATED_SCOPED:
            return i
    return len(schedule)


def select(schedule: list[dict], n_rounds: int) -> list[str]:
    return rrf_fuse([s["ranking"] for s in schedule[:n_rounds]], M_PREMISES)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar (binomial on the discordant pairs).

    Pre-declared as the primary test. Written out rather than pulled from scipy
    so the frozen protocol does not depend on a library version.
    """
    n = b + c
    if n == 0:
        return 1.0
    from math import comb

    tail = sum(comb(n, i) for i in range(0, min(b, c) + 1))
    return min(1.0, 2.0 * tail / (2.0**n))


def _batch(args) -> dict[str, bool]:
    tasks, mathlib_dir, work_dir, tag = args
    return check(tasks, mathlib_dir=Path(mathlib_dir), work_dir=Path(work_dir),
                 tag=tag, max_heartbeats=MAX_HEARTBEATS, timeout_s=5400)


def run_arm(tasks: list[LeanTask], mathlib: Path, work: Path, prefix: str, workers: int):
    batches = [tasks[i:i + 100] for i in range(0, len(tasks), 100)]
    payload = [(b, str(mathlib), str(work), f"{prefix}_{i}") for i, b in enumerate(batches)]
    out: dict[str, bool] = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(_batch, payload):
            out.update(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--population", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--mathlib", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stop-after-design-check", action="store_true")
    args = ap.parse_args()

    index = load_corpus(Path(args.corpus))
    pop = [json.loads(l) for l in Path(args.population).read_text().splitlines() if l]
    print(f"population={len(pop)} corpus={len(index.premises)}", flush=True)

    t0 = time.time()
    schedules, rounds_a, banned_counts = {}, {}, {}
    for task in pop:
        goal = frozenset(index.by_name[task["name"]].consts) if task["name"] in index.by_name \
            else frozenset()
        banned = forbidden_premises(index, task["name"])
        banned_counts[task["task_id"]] = len(banned)
        sched = round_schedule(index, goal, banned)
        schedules[task["task_id"]] = sched
        rounds_a[task["task_id"]] = saturating_rounds(sched)
    print(f"retrieval+saturation done in {time.time() - t0:.1f}s", flush=True)

    counts = list(rounds_a.values())
    dist = {r: counts.count(r) for r in sorted(set(counts))}
    k = round(statistics.mean(counts))
    censored = sum(1 for c in counts if c == len(next(iter(schedules.values()))))
    # A gold premise caught by the self-retrieval guard lowers the reachable
    # ceiling for BOTH arms. Report it rather than let it sit as a silent floor.
    gold_banned_any = 0
    gold_banned_all = 0
    for task in pop:
        banned = forbidden_premises(index, task["name"])
        gold = set(task["gold"])
        if gold & banned:
            gold_banned_any += 1
        if gold and gold <= banned:
            gold_banned_all += 1

    design = {
        "rounds_A_distribution": dist,
        "rounds_A_mean": statistics.mean(counts),
        "rounds_A_stdev": statistics.pstdev(counts),
        "k_uniform": k,
        "censored_at_schedule_end": censored,
        "degenerate_single_valued": len(dist) == 1,
        "mean_banned_per_task": statistics.mean(banned_counts.values()),
        "tasks_with_some_gold_banned": gold_banned_any,
        "tasks_with_all_gold_banned": gold_banned_all,
    }
    print("DESIGN CHECK:", json.dumps(design), flush=True)
    if args.stop_after_design_check:
        Path(args.out).write_text(json.dumps({"design_check": design}, indent=2))
        return

    arm_a_tasks, arm_b_tasks, sel = [], [], {}
    for task in pop:
        tid = task["task_id"]
        a = select(schedules[tid], rounds_a[tid])
        b = select(schedules[tid], k)
        sel[tid] = {"A": a, "B": b}
        arm_a_tasks.append(LeanTask(tid, task["stmt"], f"simp [{', '.join(a)}]" if a else "simp"))
        arm_b_tasks.append(LeanTask(tid, task["stmt"], f"simp [{', '.join(b)}]" if b else "simp"))

    mathlib, work = Path(args.mathlib), Path(args.work)
    res_a = run_arm(arm_a_tasks, mathlib, work, "armA", args.workers)
    print("arm A done", flush=True)
    res_b = run_arm(arm_b_tasks, mathlib, work, "armB", args.workers)
    print("arm B done", flush=True)

    rows = []
    for task in pop:
        tid = task["task_id"]
        gold = set(task["gold"])
        rows.append({
            "task_id": tid, "name": task["name"], "module": task["module"],
            "rounds_A": rounds_a[tid], "rounds_B": k,
            "solved_A": bool(res_a.get(tid, False)), "solved_B": bool(res_b.get(tid, False)),
            "gold_cov_A": len(set(sel[tid]["A"]) & gold) / len(gold),
            "gold_cov_B": len(set(sel[tid]["B"]) & gold) / len(gold),
            "n_premises_A": len(sel[tid]["A"]), "n_premises_B": len(sel[tid]["B"]),
        })

    n = len(rows)
    a_only = sum(1 for r in rows if r["solved_A"] and not r["solved_B"])
    b_only = sum(1 for r in rows if r["solved_B"] and not r["solved_A"])
    summary = {
        "n_tasks": n,
        "solve_rate_A": sum(r["solved_A"] for r in rows) / n,
        "solve_rate_B": sum(r["solved_B"] for r in rows) / n,
        "discordant_A_only": a_only, "discordant_B_only": b_only,
        "mcnemar_exact_p_two_sided": mcnemar_exact(a_only, b_only),
        "total_rounds_A": sum(r["rounds_A"] for r in rows),
        "total_rounds_B": sum(r["rounds_B"] for r in rows),
        "mean_gold_cov_A": statistics.mean(r["gold_cov_A"] for r in rows),
        "mean_gold_cov_B": statistics.mean(r["gold_cov_B"] for r in rows),
        "design_check": design,
    }
    print("SUMMARY:", json.dumps(summary, indent=2), flush=True)
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
