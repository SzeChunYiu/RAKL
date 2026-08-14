"""Audit the scoring path with ``rakl.gate_falsifiability.audit_gate``.

The gate under audit is the thing that will license the benefit claim: "the
Lean-adjudicated solve check reports success on this evidence". If that gate
cannot fail, every downstream number is decoration.

Note the short-circuit in ``audit_gate``: a gate that fails on unperturbed
evidence is reported FALSIFIABLE without probing. So a dead harness that solves
nothing would score FALSIFIABLE. The audit is therefore only meaningful when
``baseline_pass`` is also True, and this script asserts both.

Perturbations are domain-appropriate:
  * corrupt_premises  — premise names replaced by nonexistent identifiers. Must flip.
  * false_goal        — the goal replaced by a false proposition. Must flip.
  * drop_premises     — the premise set emptied. Must flip.
  * shuffle_premises  — premise order permuted. Expected INSENSITIVE; `simp only`
                        is order-tolerant here, so this is a control on the probe
                        itself, not a defect if it does not move.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_check import LeanTask, check  # noqa: E402

from rakl.gate_falsifiability import GateFalsifiability, audit_gate  # noqa: E402

PASS_FRACTION = 0.90
MATHLIB = Path("/home/billy/orion-lean/mathlib4")
WORK = Path("/home/billy/orion-lean/work")
_counter = {"n": 0}


def solve_gate(evidence) -> bool:
    """Pass iff Lean closes at least PASS_FRACTION of the evidence items."""
    _counter["n"] += 1
    tasks = [
        LeanTask(
            e["task_id"],
            e["stmt"],
            f"simp [{', '.join(e['premises'])}]" if e["premises"] else "simp",
        )
        for e in evidence
    ]
    res = check(tasks, mathlib_dir=MATHLIB, work_dir=WORK, tag=f"audit{_counter['n']}")
    solved = sum(1 for t in tasks if res.get(t.task_id, False))
    return solved >= PASS_FRACTION * len(tasks)


def corrupt_premises(evidence, rng: random.Random):
    return [
        {**e, "premises": [f"ORION_Absent_{rng.randrange(10**9)}" for _ in e["premises"]]}
        for e in evidence
    ]


def false_goal(evidence, rng: random.Random):
    return [{**e, "stmt": "(1 : Nat) = 2"} for e in evidence]


def drop_premises(evidence, rng: random.Random):
    return [{**e, "premises": []} for e in evidence]


def shuffle_premises(evidence, rng: random.Random):
    out = []
    for e in evidence:
        p = list(e["premises"])
        rng.shuffle(p)
        out.append({**e, "premises": p})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--population", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pop = [json.loads(l) for l in Path(args.population).read_text().splitlines() if l]
    evidence = [
        {"task_id": t["task_id"], "stmt": t["stmt"], "premises": list(t["gold"])}
        for t in pop[: args.n]
    ]

    report = audit_gate(
        solve_gate,
        evidence,
        gate_id="LEAN-SOLVE-GATE-V1",
        perturbations={
            "corrupt_premises": corrupt_premises,
            "false_goal": false_goal,
            "drop_premises": drop_premises,
            "shuffle_premises": shuffle_premises,
        },
        trials=2,
    )

    payload = {
        "gate_id": report.gate_id,
        "baseline_pass": report.baseline_pass,
        "verdict": report.verdict.value,
        "sensitive_probes": list(report.sensitive_probes),
        "supports_confirmatory_use": report.supports_confirmatory_use,
        "reasons": list(report.reasons),
        "probes": [
            {"probe_id": p.probe_id, "outcome": p.outcome.value,
             "trials": p.trials, "flips": p.flips, "detail": p.detail}
            for p in report.probes
        ],
        "control_asserted_first": True,
        "n_evidence": len(evidence),
    }
    print(json.dumps(payload, indent=2))
    Path(args.out).write_text(json.dumps(payload, indent=2))

    if not report.baseline_pass:
        raise SystemExit("BLOCKED: gate does not pass on real evidence; probe would be vacuous")
    if report.verdict is not GateFalsifiability.FALSIFIABLE:
        raise SystemExit(f"BLOCKED: gate verdict {report.verdict.value}; fix instrument before spending")
    print("\nGATE OK: baseline_pass=True and verdict=FALSIFIABLE")


if __name__ == "__main__":
    main()
