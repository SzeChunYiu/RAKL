"""Which of this session's additions are verifiable, and against what?

The programme's own distinction: conformance is instrument evidence, never
utility evidence. That was applied to the RFA controller and not to the
mechanics added on top of it. This applies it.

Five questions per mechanic:

  T   has tests
  R   tested against REAL recorded data, not fixtures
  F   carries a registered falsifier
  X   that falsifier has been EXECUTED
  C   has any caller outside tests and its own scripts

A mechanic with T only is internally consistent: the tests show the code does
what its docstring says. That is not evidence that it measures anything.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path("research/self_rakl_verifiability_audit_v1/RESULT.json")

MECHANICS = [
    {
        "id": "recursive_framework_audit.decide",
        "added": "prior session (#722); extended here",
        "tests": True,
        "real_data": True,
        "real_data_note": "run over 38 recorded frontier terminals in the question audit",
        "falsifier": True,
        "falsifier_note": "RFC-v1 utility benchmark, arms A-G over F0-F10",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: interface ten bindings",
        "added": "#723",
        "tests": True,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "none registered; the bindings are asserted as required, never tested against an interface that failed for want of one",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: atomicity five conditions",
        "added": "#723",
        "tests": True,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "none; no recorded atomicity claim was re-checked against them",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: bounded node closure (8 conditions)",
        "added": "#723",
        "tests": True,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "none; no node has ever been assessed with it",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: value-of-audit selection",
        "added": "#723",
        "tests": True,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "none; no audit has been selected by it",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: question/framework adequacy vectors",
        "added": "#723",
        "tests": True,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "none. The 9 and 10 coordinates were transcribed from the packet; nothing tests that they are the right coordinates, or that scoring a question on them predicts anything",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "recursive_framework_audit: ancestor challenge packet",
        "added": "#723",
        "tests": True,
        "real_data": True,
        "real_data_note": "applied to the ARN lineage; returned escalation_admissible=False, which held up",
        "falsifier": False,
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "observation_contract",
        "added": "#726",
        "tests": True,
        "real_data": True,
        "real_data_note": "the ARN discriminator ran under a source-grounded contract",
        "falsifier": False,
        "falsifier_note": "none registered. No evidence that declaring a regime changes any outcome; the question-level probe found zero designs declare one",
        "falsifier_executed": False,
        "callers_outside_tests": True,
        "callers_note": "research/arn_local_vs_parent_discriminator_v1/run_discriminator.py",
    },
    {
        "id": "construct_independence gate",
        "added": "#731",
        "tests": True,
        "real_data": True,
        "real_data_note": "validated against 3 recorded instruments: 2 agree with the record, 1 clean miss",
        "falsifier": True,
        "falsifier_note": "frozen: over the next 12 instrument closures, defect rate must be lower among designs declaring all four obligations",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
    {
        "id": "SUPPORT_DECLARED precondition",
        "added": "named in #734, not implemented",
        "tests": False,
        "real_data": False,
        "falsifier": False,
        "falsifier_note": "named after three failures it would have caught; no code, no test, no falsifier",
        "falsifier_executed": False,
        "callers_outside_tests": False,
    },
]


def main() -> int:
    rows = []
    for m in MECHANICS:
        score = {
            "T_has_tests": m["tests"],
            "R_tested_on_real_data": m["real_data"],
            "F_has_registered_falsifier": m["falsifier"],
            "X_falsifier_executed": m["falsifier_executed"],
            "C_caller_outside_tests": m["callers_outside_tests"],
        }
        n = sum(1 for v in score.values() if v)
        if not m["tests"]:
            grade = "UNIMPLEMENTED"
        elif not m["real_data"]:
            grade = "INTERNALLY_CONSISTENT_ONLY"
        elif not m["falsifier"]:
            grade = "EXERCISED_BUT_UNFALSIFIABLE_AS_BUILT"
        elif not m["falsifier_executed"]:
            grade = "FALSIFIER_REGISTERED_UNRUN"
        else:
            grade = "FALSIFIED_OR_SURVIVED"
        rows.append({**m, "score": score, "criteria_met": n, "grade": grade})

    from collections import Counter

    grades = Counter(r["grade"] for r in rows)

    result = {
        "schema_version": "rakl-self-verifiability-audit-v1",
        "status": "SELF_AUDIT__PROPOSAL_ONLY",
        "grants_scientific_authority": False,
        "question": "Which mechanics added this session are verifiable, and against what?",
        "criteria": {
            "T": "has tests",
            "R": "tested against real recorded data, not fixtures",
            "F": "carries a registered falsifier",
            "X": "that falsifier has been executed",
            "C": "has a caller outside tests and its own scripts",
        },
        "headline": (
            "Of the mechanics added, the majority are INTERNALLY_CONSISTENT_ONLY: their tests show "
            "the code does what its docstring says, which is not evidence that they measure "
            "anything. Exactly one carries a registered falsifier and it has not been run."
        ),
        "grades": dict(grades),
        "mechanics": len(rows),
        "with_a_registered_falsifier": sum(1 for r in rows if r["falsifier"]),
        "with_an_executed_falsifier": sum(1 for r in rows if r["falsifier_executed"]),
        "with_a_production_caller": sum(1 for r in rows if r["callers_outside_tests"]),
        "the_honest_reading": (
            "The programme's own rule is that conformance is instrument evidence and never utility "
            "evidence. That rule was applied to the RFA controller and not to the mechanics built "
            "on top of it. Applied here, most of this session's formalism is a hypothesis written "
            "in type declarations: it constrains what can be expressed, and nothing yet shows that "
            "constraining it improves any research outcome."
        ),
        "what_would_change_each_grade": {
            "INTERNALLY_CONSISTENT_ONLY": "run it against recorded instruments whose outcomes are known, as the construct gate was",
            "EXERCISED_BUT_UNFALSIFIABLE_AS_BUILT": "register a falsifier before the next use, stating what result would retire the mechanic",
            "FALSIFIER_REGISTERED_UNRUN": "execute it; for the construct gate that means 12 instrument closures",
            "UNIMPLEMENTED": "implement, or delete the name so it stops looking like a mechanic",
        },
        "per_mechanic": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    width = max(len(r["id"]) for r in rows)
    for r in rows:
        flags = "".join(
            k[0] if v else "-" for k, v in r["score"].items()
        )
        print(f"  {r['id']:<{width}}  {flags}  {r['grade']}")
    print()
    print(f"mechanics: {len(rows)}")
    print(f"  with a registered falsifier : {result['with_a_registered_falsifier']}")
    print(f"  with an EXECUTED falsifier  : {result['with_an_executed_falsifier']}")
    print(f"  with a production caller    : {result['with_a_production_caller']}")
    print(f"  grades: {dict(grades)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
