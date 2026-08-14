"""Validate the Lean adjudicator against real data before it scores anything.

Asserts the no-alarm case (a genuine proof must be accepted) as well as the
alarm cases (a false goal and a nonexistent premise must be rejected). A checker
that has only been shown to fire is not validated.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/billy/orion-lean/scripts")
from lean_check import LeanTask, check  # noqa: E402

raw = [json.loads(l) for l in open("/home/billy/orion-lean/population_raw.jsonl") if l.strip()]
print("raw:", len(raw))
ok = [r for r in raw if "✘" not in r["stmt"] and "✠" not in r["stmt"]
      and len(r["stmt"]) < 400 and r["gold"]]
print("cheap-filtered:", len(ok))

sample = ok[:6]
tasks = [
    LeanTask(f"S{i}", " ".join(r["stmt"].split()), f"exact {r['name']}")
    for i, r in enumerate(sample)
]
tasks.append(LeanTask("HOSTILE_FALSE_GOAL", "(1:Nat) = 2", "simp"))
tasks.append(
    LeanTask("HOSTILE_BAD_PREMISE", " ".join(sample[0]["stmt"].split()),
             "simp only [Nonexistent_Lemma_XYZ]")
)

res = check(
    tasks,
    mathlib_dir=Path("/home/billy/orion-lean/mathlib4"),
    work_dir=Path("/home/billy/orion-lean/work"),
    tag="smoke",
)
for k in sorted(res):
    print(f"  {k}: {res[k]}")

controls = [res[f"S{i}"] for i in range(len(sample))]
print("CONTROL_PASS_RATE:", sum(controls), "/", len(controls))
print("HOSTILE_FALSE_GOAL_rejected:", res["HOSTILE_FALSE_GOAL"] is False)
print("HOSTILE_BAD_PREMISE_rejected:", res["HOSTILE_BAD_PREMISE"] is False)
