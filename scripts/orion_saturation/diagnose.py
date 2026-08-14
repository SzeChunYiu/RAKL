"""Attribute the null to a single stage.

The question this answers: did the two arms actually differ in what they handed
the tactic? If the frozen premise budget makes the selections mostly identical,
the effective paired-contrast size is far below n=112 and the study had almost
no power regardless of the mechanism's merit — a design-stage failure, not a
mechanism-stage one. That distinction decides which lever a revival should pull.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "/home/billy/orion-lean/scripts")
from retrieval import ROUTES, Premise, PremiseIndex, rrf_fuse, run_route  # noqa: E402
from study import (  # noqa: E402
    K_PER_ROUND, DEEPEN_SWEEPS, M_PREMISES, forbidden_premises, round_schedule,
    saturating_rounds, mcnemar_exact,
)

res = json.loads(Path("/home/billy/orion-lean/results.json").read_text())
rows = {r["task_id"]: r for r in res["rows"]}
k = res["summary"]["design_check"]["k_uniform"]

premises = [
    Premise(json.loads(l)["name"], frozenset(json.loads(l)["ty"]))
    for l in open("/home/billy/orion-lean/corpus.jsonl") if l.strip()
]
index = PremiseIndex(premises)
pop = [json.loads(l) for l in open("/home/billy/orion-lean/population_v2.jsonl") if l.strip()]

identical, differing, jac = 0, [], []
for task in pop:
    tid = task["task_id"]
    goal = frozenset(index.by_name[task["name"]].consts)
    sched = round_schedule(index, goal, forbidden_premises(index, task["name"]))
    ra = saturating_rounds(sched)
    a = set(rrf_fuse([s["ranking"] for s in sched[:ra]], M_PREMISES))
    b = set(rrf_fuse([s["ranking"] for s in sched[:k]], M_PREMISES))
    if a == b:
        identical += 1
    else:
        differing.append(tid)
    jac.append(len(a & b) / max(len(a | b), 1))

print(f"n_tasks                      : {len(pop)}")
print(f"identical top-{M_PREMISES} selections    : {identical}")
print(f"differing selections         : {len(differing)}")
print(f"mean Jaccard(A_sel, B_sel)   : {statistics.mean(jac):.4f}")

sub = [rows[t] for t in differing]
if sub:
    a_only = sum(1 for r in sub if r["solved_A"] and not r["solved_B"])
    b_only = sum(1 for r in sub if r["solved_B"] and not r["solved_A"])
    print("\n-- restricted to tasks where the arms actually differ --")
    print(f"  n                          : {len(sub)}")
    print(f"  solve_rate_A               : {sum(r['solved_A'] for r in sub) / len(sub):.4f}")
    print(f"  solve_rate_B               : {sum(r['solved_B'] for r in sub) / len(sub):.4f}")
    print(f"  discordant A-only / B-only : {a_only} / {b_only}")
    print(f"  McNemar exact p            : {mcnemar_exact(a_only, b_only):.4f}")
    print("  NOTE: diagnostic only. This subpopulation was identified after outcome")
    print("        access and is NOT a confirmatory test.")

allr = list(rows.values())
disc = [r for r in allr if r["solved_A"] != r["solved_B"]]
print(f"\ndiscordant pairs overall     : {len(disc)}  (all n={len(allr)})")
print(f"  of which selections differ : {sum(1 for r in disc if r['task_id'] in set(differing))}")
early = [r for r in allr if r["rounds_A"] < k]
late = [r for r in allr if r["rounds_A"] > k]
for label, grp in (("A stopped EARLIER than B", early), ("A stopped LATER than B", late)):
    if grp:
        print(f"\n{label}: n={len(grp)}")
        print(f"  solve A={sum(r['solved_A'] for r in grp) / len(grp):.4f} "
              f"B={sum(r['solved_B'] for r in grp) / len(grp):.4f}")
        print(f"  gold_cov A={statistics.mean(r['gold_cov_A'] for r in grp):.4f} "
              f"B={statistics.mean(r['gold_cov_B'] for r in grp):.4f}")
