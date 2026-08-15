"""Drive the negative frontier through the session loop.

First real use of `rakl.research_session`. Support declarations are not invented:
each is taken from evidence established and committed this session, or left
undeclared where nothing established it — which is the honest majority.

The point is not to license action on everything. It is that the loop refuses
where support is absent, and says exactly what is missing.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")

from rakl.recursive_framework_audit import (  # noqa: E402
    AuditCoordinate,
    AuditNode,
    AuditResidual,
)
from rakl.research_session import (  # noqa: E402
    SessionLedger,
    SupportDeclaration,
    next_step,
)

INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = Path("research/frontier_session_drive_v1/RESULT.json")

# Support established this session, with the artifact that established it.
# Anything absent from this map is genuinely undeclared and must come back
# CANNOT_CHECK — that is the loop working, not a gap in the driver.
SUPPORT = {
    "p1-bounded-saturation-null": SupportDeclaration(
        population="112 held-out Mathlib tasks, 11 discordant pairs",
        predicate_in_domain=True,
        conditioning_variables=(),
        reachable_ceiling=0.154,
        ceiling_basis="power at the observed effect; 37 discordant pairs needed for 0.80 "
        "(research/orion_saturation_power_reanalysis_v1)",
    ),
    "p1-l4-tight-resource-floor": SupportDeclaration(
        population="60 tight-budget worlds at 2*S*",
        predicate_in_domain=False,  # protocol declares the stratum outside PROMOTE scope
        conditioning_variables=("budget_class",),
        reachable_ceiling=0.0,
        ceiling_basis="budget exactly funds a zero-waste solution; protocol marks the class "
        "outside PROMOTE scope (research/l4_tight_floor_scope_v1)",
    ),
    "p4-adaptive-lost-to-static": SupportDeclaration(
        population="12 worlds, adaptive vs static allocator",
        predicate_in_domain=True,
        conditioning_variables=("world_family",),
        reachable_ceiling=0.024570935346802252,
        ceiling_basis="tier-3 rigorous harm-free upper bound against a 0.05 hard gate "
        "(research/p4_adaptive_lever_admissibility_v1)",
        registered_gate=0.05,
    ),
    "p2-template-inversion": SupportDeclaration(
        population="576 held-out confirmatory pairs, prose-transfer instrument",
        predicate_in_domain=True,
        # The failure concentrated in exactly one of seven registered ambiguity
        # classes, so the class is the conditioning variable a successor must block on.
        conditioning_variables=("ambiguity_class",),
        reachable_ceiling=0.9722222222222222,
        ceiling_basis="G2 full_exact on the executed confirmatory run; the lever requires the "
        "successor's ceiling not to rise (research/paper2_prose_transfer_v1/results)",
    ),
    "p1-source-monitoring-repetition-attack": SupportDeclaration(
        population="source-identity repair v1 case set",
        predicate_in_domain=True,
        conditioning_variables=("identifier_form",),
        reachable_ceiling=1.0,
        ceiling_basis="repair executed and landed via #728; RECEIPT.json terminal "
        "ATTACK_DETECTED_CONTROLS_PASSING (research/paper1_source_identity_repair_v1)",
    ),
    "p2-arn-v4-battery-failed": SupportDeclaration(
        population="ARN corpus, 2190 pairs, CONFIRM split",
        predicate_in_domain=True,
        conditioning_variables=("distractor_similarity",),
        reachable_ceiling=0.0,
        ceiling_basis="removing role_boost moves the shuffled-gold leak by 0.000623; the probe "
        "measures abstention (research/arn_v4r_role_boost_repair_v1)",
    ),
}

RULES = (
    ("licence/abstention (independence)", AuditCoordinate.EVIDENCE),
    ("licence/abstention", AuditCoordinate.EVALUATOR),
    ("licence", AuditCoordinate.EVALUATOR),
    ("instrument-construct (admissibility", AuditCoordinate.EVALUATOR),
    ("instrument-construct (comparator admissibility)", AuditCoordinate.EVALUATOR),
    ("instrument-construct", AuditCoordinate.MEASUREMENT),
    ("capability/benefit", AuditCoordinate.EVIDENCE),
    ("capability (feature adequacy)", AuditCoordinate.MEASUREMENT),
    ("capability", AuditCoordinate.EVIDENCE),
    ("hardware", AuditCoordinate.EVIDENCE),
    ("power", AuditCoordinate.EVIDENCE),
    ("extraction/provenance", AuditCoordinate.EVIDENCE),
    ("extraction/integration", AuditCoordinate.INTERFACE),
    ("extraction", AuditCoordinate.MEASUREMENT),
    ("mapping / allocation-policy", AuditCoordinate.DECOMPOSITION),
    ("mapping", AuditCoordinate.FRAMEWORK),
)


def coordinate_for(attribution: str) -> AuditCoordinate | None:
    low = attribution.lower()
    for needle, coord in RULES:
        if needle.lower() in low:
            return coord
    return None


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    local = [r for r in inventory["records"] if r["class"] == "REVIVABLE_LOCAL"]

    ledgers = []
    rows = []
    for record in local:
        slug = record["slug"]
        coord = coordinate_for(record.get("one_stage_attribution", ""))
        residual = AuditResidual(plausible_causes=(coord,) if coord else ())
        step = next_step(
            target_id=slug,
            node=AuditNode(closure_coordinates_pass=False, material_open_residual=True),
            residual=residual,
            support=SUPPORT.get(slug),
        )
        ledgers.append(SessionLedger(slug).with_step(step))
        rows.append(
            {
                "slug": slug,
                "coordinate": coord.value if coord else None,
                "proposed": step.proposed_action.value,
                "licensed": step.licensed_action.value,
                "blocked": step.blocked,
                "support": step.support.value,
                "support_gaps": list(step.support_gaps),
                "digest": step.digest(),
                "reasons": list(step.reasons),
            }
        )

    licensed = [r for r in rows if not r["blocked"]]
    counts = Counter(r["licensed"] for r in rows)

    result = {
        "schema_version": "rakl-frontier-session-drive-v1",
        "status": "FIRST_REAL_USE_OF_THE_SESSION_LOOP",
        "grants_scientific_authority": False,
        "question": "Which frontier targets does the governed loop license action on, and what is missing on the rest?",
        "targets": len(rows),
        "licensed_to_act": len(licensed),
        "blocked": len(rows) - len(licensed),
        "licensed_action_counts": dict(counts.most_common()),
        "support_declared_for": sorted(SUPPORT),
        "records_discharged_since_the_inventory": {
            "p1-source-monitoring-repetition-attack": {
                "receipt_on_main": "research/paper1_source_identity_repair_v1/RECEIPT.json",
                "terminal": "ATTACK_DETECTED_CONTROLS_PASSING",
                "landed_by": "#728",
                "frontier_defect": (
                    "the record cites research/p1_source_identity_repair_v1, a path that has "
                    "never existed; the artifact is at research/paper1_source_identity_repair_v1"
                ),
            }
        },
        "support_undeclarable": {
            "p1-atms-parent-boundary": (
                "both cited receipts are absent from main, so no population, domain or ceiling "
                "can be read. The loop still licenses AUDIT_EVALUATOR, which is correct: "
                "auditing a comparator's admissibility asks whether the ruler is fair and needs "
                "no population. Any measurement against that comparator would block on the same "
                "missing support, and the provenance gap stands independently of this verdict."
            )
        },
        "note": (
            "Support declarations are taken from evidence committed this session, never "
            "invented. Targets absent from that map are genuinely undeclared and come back "
            "CANNOT_CHECK, which is the loop working rather than a gap in the driver."
        ),
        "per_target": rows,
        "ledgers": [l.to_dict() for l in ledgers],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    width = max(len(r["slug"]) for r in rows)
    for r in rows:
        mark = "ACT  " if not r["blocked"] else "BLOCK"
        print(f"{mark} {r['slug']:<{width}}  {r['proposed']:<20} -> {r['licensed']}")
    print()
    print(f"licensed to act: {len(licensed)}/{len(rows)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
