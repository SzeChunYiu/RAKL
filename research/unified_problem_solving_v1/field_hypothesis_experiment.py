#!/usr/bin/env python3
"""Empirical test of the solvability-field hypothesis on random known worlds.

The unified framework's field/reuse economics rest on a falsifiable claim: a *cheap*
local field signal predicts *verified* global progress often enough to replace a
meaningful fraction of search. This experiment tests that claim directly, on a
distribution of random grid worlds where ground truth is exactly computable, rather
than on a single hand-built toy.

Setup (deterministic from seed):
  * M random grid worlds with random obstacles, start and goal (goal reachable).
  * True cost-to-go Psi(v): exact BFS distance to goal through free cells (the oracle).
  * Cheap field Phi(v): Manhattan distance to goal -- O(1), ignores obstacles.

Measured:
  1. field-descent predictiveness = P(the neighbour that most decreases the CHEAP field
     Phi also decreases the TRUE cost-to-go Psi | state on some shortest path region).
     This is the operational content of  <d(a), -grad Phi> > 0  =>  E[Delta R] > 0.
  2. search reduction = 1 - (nodes expanded by a Phi-guided best-first search) /
     (nodes expanded by uninformed BFS) to first reach the goal.

Honesty: development/known-world evidence only. Grants NO scientific or method-promotion
authority. Reports whatever the distribution shows, with bootstrap CIs.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "field_hypothesis.json"

MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _make_world(rng: random.Random, n: int, obstacle_p: float):
    grid = [[rng.random() < obstacle_p for _ in range(n)] for _ in range(n)]  # True = obstacle
    free = [(r, c) for r in range(n) for c in range(n) if not grid[r][c]]
    if len(free) < 2:
        return None
    start = rng.choice(free)
    goal = rng.choice(free)
    if start == goal:
        return None
    return grid, start, goal


def _true_costs(grid, goal, n):
    """Exact BFS cost-to-go from every free cell to goal (None if unreachable)."""
    dist = {goal: 0}
    q = deque([goal])
    while q:
        r, c = q.popleft()
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and not grid[nr][nc] and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return dist


def _phi(cell, goal):
    return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])  # cheap Manhattan field


def _neighbours(cell, grid, n):
    out = []
    for dr, dc in MOVES:
        nr, nc = cell[0] + dr, cell[1] + dc
        if 0 <= nr < n and 0 <= nc < n and not grid[nr][nc]:
            out.append((nr, nc))
    return out


def _predictiveness(grid, goal, n, true_cost):
    """Fraction of free cells where descending the cheap field == real progress."""
    hits = total = 0
    for cell, tc in true_cost.items():
        if cell == goal:
            continue
        nbrs = _neighbours(cell, grid, n)
        if not nbrs:
            continue
        # neighbour that most decreases the cheap field Phi
        best = min(nbrs, key=lambda x: _phi(x, goal))
        # does it also decrease the TRUE cost-to-go? (verified progress)
        if best in true_cost and true_cost[best] < tc:
            hits += 1
        total += 1
    return (hits / total) if total else None


def _bfs_expanded(grid, start, goal, n):
    seen = {start}
    q = deque([start])
    expanded = 0
    while q:
        cell = q.popleft()
        expanded += 1
        if cell == goal:
            return expanded
        for nb in _neighbours(cell, grid, n):
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return expanded


def _field_guided_expanded(grid, start, goal, n):
    """Greedy best-first by the cheap field Phi (with a bounded frontier, not pure greedy)."""
    import heapq
    seen = {start}
    heap = [(_phi(start, goal), 0, start)]
    expanded = 0
    tie = 1
    while heap:
        _, _, cell = heapq.heappop(heap)
        expanded += 1
        if cell == goal:
            return expanded
        for nb in _neighbours(cell, grid, n):
            if nb not in seen:
                seen.add(nb)
                heapq.heappush(heap, (_phi(nb, goal), tie, nb))
                tie += 1
    return expanded


def _boot(vals, rng, B=5000):
    if not vals:
        return None
    m = sum(vals) / len(vals)
    samples = []
    for _ in range(B):
        s = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
        samples.append(sum(s) / len(s))
    samples.sort()
    return {"mean": round(m, 4), "lo": round(samples[int(0.025 * B)], 4), "hi": round(samples[int(0.975 * B)], 4), "n": len(vals)}


def run(seed=461, m=400, n=12, obstacle_p=0.25):
    rng = random.Random(seed)
    pred, redu = [], []
    per = []
    made = 0
    while made < m:
        w = _make_world(rng, n, obstacle_p)
        if not w:
            continue
        grid, start, goal = w
        tc = _true_costs(grid, goal, n)
        if start not in tc:  # goal unreachable from start -> skip (need a solvable world)
            continue
        made += 1
        p = _predictiveness(grid, goal, n, tc)
        eb = _bfs_expanded(grid, start, goal, n)
        ef = _field_guided_expanded(grid, start, goal, n)
        r = 1.0 - ef / eb if eb else 0.0
        if p is not None:
            pred.append(p)
        redu.append(r)
        per.append({"predictiveness": p, "bfs_expanded": eb, "field_expanded": ef, "reduction": round(r, 4)})
    bs = random.Random(seed + 1)
    return {
        "schema_version": "orion-field-hypothesis-v1",
        "seed": seed, "worlds": m, "grid_n": n, "obstacle_p": obstacle_p,
        "claim_boundary": "development known-world evidence; tests the field hypothesis on random solvable grids; "
                          "cheap field = Manhattan (obstacle-blind); grants no scientific or method-promotion authority.",
        "grants_scientific_authority": False, "grants_method_promotion": False,
        "field_descent_predicts_true_progress": _boot(pred, bs),
        "search_reduction_vs_bfs": _boot(redu, bs),
        "fraction_worlds_field_reduces_search": round(sum(1 for r in redu if r > 0) / len(redu), 4),
        "per_world": per,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=461)
    ap.add_argument("--worlds", type=int, default=400)
    ap.add_argument("--grid", type=int, default=12)
    ap.add_argument("--obstacle-p", type=float, default=0.25)
    a = ap.parse_args()
    res = run(seed=a.seed, m=a.worlds, n=a.grid, obstacle_p=a.obstacle_p)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(res, indent=2))
    print(f"WROTE={RESULT.relative_to(HERE.parents[1])}")
    print("field_descent_predicts_true_progress:", res["field_descent_predicts_true_progress"])
    print("search_reduction_vs_bfs:", res["search_reduction_vs_bfs"])
    print("fraction_worlds_field_reduces_search:", res["fraction_worlds_field_reduces_search"])
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
