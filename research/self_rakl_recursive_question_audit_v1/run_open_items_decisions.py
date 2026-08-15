"""Drive the merged controller over the programme's open items.

Answers one question with a run instead of an opinion: given what is actually
open, what does the recursive framework audit select, and which selections can
this session act on?

Every item is sourced from a committed artifact -- the negative frontier's own
levers, the question audit's licensed-next list, or the observation-contract
promotion receipt's open gates. Nothing is invented here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from rakl.recursive_framework_audit import (  # noqa: E402
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    decide,
)

OUT = Path("research/self_rakl_recursive_question_audit_v1/OPEN_ITEMS_DECISIONS.json")

# (id, source, causes, flags, actionable_by_this_session, blocker)
ITEMS = [
    (
        "construct-independence-admission-gate",
        "NEG_CLUSTER_CONSTRUCT_DEPENDENCE.md §3 (candidate mechanic, unbuilt)",
        (AuditCoordinate.MEASUREMENT,),
        {},
        True,
        None,
    ),
    (
        "arn-local-vs-parent-discriminator",
        "AUDIT_RESULT.json arn_lineage_ascent_test.blocking_gap",
        (AuditCoordinate.MEASUREMENT,),
        {"parent_challenge_supported": True, "distinct_local_repair_families_failed": 3},
        True,
        None,
    ),
    (
        "question-level-instrument",
        "CORE.md §2 CANNOT_CHECK__SOURCE_VOCABULARY_CANNOT_EXPRESS_THE_COORDINATE",
        (AuditCoordinate.QUESTION, AuditCoordinate.MEASUREMENT),
        {},
        True,
        None,
    ),
    (
        "manuscript-claim-vs-receipt-audit",
        "unverified class fixed by #711; no check covers it",
        (AuditCoordinate.EVALUATOR,),
        {},
        True,
        None,
    ),
    (
        "rfa-fresh-utility-assurance-epoch-a-b",
        "PROMOTION_RECEIPT.json open_gates[0]; RFC-v1 arms A-G over F0-F10",
        (AuditCoordinate.EVIDENCE,),
        {"resource_bound": True},
        False,
        "executed empirical epochs with hidden independently-validated defect labels",
    ),
    (
        "semantic-parent-execution",
        "PROMOTION_RECEIPT.json open_gates[1] CANNOT_CHECK_RESOURCE_BOUND",
        (AuditCoordinate.EVIDENCE,),
        {"resource_bound": True},
        False,
        "A100 / hosted model outside the sanctioned local envelope",
    ),
    (
        "a3a4-receipt-destruction-fix",
        "src/rakl/ablation_a3_a4_matched_empirical.py overwrites a harvested receipt",
        (AuditCoordinate.EVALUATOR,),
        {},
        False,
        "protected tests/ input; needs a pre-declared migration and operator authorization (#710)",
    ),
    (
        "evidence-cluster-17-records",
        "AUDIT_RESULT.json coordinate_counts.EVIDENCE",
        (AuditCoordinate.EVIDENCE,),
        {"resource_bound": True},
        False,
        "mostly STRUCTURALLY_BLOCKED / REVIVABLE_EXTERNAL in the frontier's own classification",
    ),
    (
        "rfa-production-caller",
        "no pipeline invokes the controller outside conformance and tests",
        (AuditCoordinate.METHOD,),
        {},
        False,
        "roadmap position, not a defect: Phase 3 asks for entrypoints, which exist",
    ),
]


def main() -> int:
    rows = []
    for item_id, source, causes, flags, actionable, blocker in ITEMS:
        residual = AuditResidual(plausible_causes=causes, **flags)
        decision = decide(
            AuditNode(closure_coordinates_pass=False, material_open_residual=True),
            residual,
        )
        rows.append(
            {
                "item": item_id,
                "source": source,
                "coordinates": [c.value for c in causes],
                "selected_action": decision.action.value,
                "reasons": list(decision.reasons),
                "actionable_without_new_authority_or_resource": actionable,
                "blocker": blocker,
            }
        )

    # The ARN item is the one place where the frozen chain and the completeness
    # check disagree, and the stricter one governs. decide() returns ASCEND on
    # two failed local repair families; the challenge packet is nonetheless
    # inadmissible because no local-vs-parent discriminator is registered.
    for row in rows:
        if row["item"] == "arn-local-vs-parent-discriminator":
            row["admissibility_tension"] = (
                "frozen chain selects ASCEND; AncestorChallenge.escalation_admissible is False "
                "because the packet has no registered local-vs-parent discriminator. The "
                "stricter check governs: ascending here would promote repeated raw failure "
                "into a parent-level verdict."
            )

    actionable = [r for r in rows if r["actionable_without_new_authority_or_resource"]]
    result = {
        "schema_version": "rakl-open-items-controller-run-v1",
        "status": "PURSUIT_SELECTION_ONLY_NO_AUTHORITY",
        "grants_scientific_authority": False,
        "question": "What does the merged controller select for each open item, and which can be acted on now?",
        "note": (
            "The controller selects a pursuit action; it does not execute research. A selection "
            "of SOLVE_CURRENT on a resource-bound item is not a claim that the item is easy -- it "
            "is the chain reporting no formulation-level defect, with the blocker recorded "
            "separately."
        ),
        "items": len(rows),
        "actionable_now": len(actionable),
        "blocked": len(rows) - len(actionable),
        "decisions": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    width = max(len(r["item"]) for r in rows)
    for row in rows:
        mark = "ACT " if row["actionable_without_new_authority_or_resource"] else "BLOCK"
        print(f"{mark} {row['item']:<{width}}  {row['selected_action']}")
        if row["blocker"]:
            print(f"      blocker: {row['blocker']}")
    print(f"\nactionable now: {len(actionable)}/{len(rows)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
