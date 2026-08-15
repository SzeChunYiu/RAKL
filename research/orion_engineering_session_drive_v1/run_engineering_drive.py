"""Drive Orion's own open engineering fibers through Orion's session loop.

Workstream: use the framework on the framework. The thirteen open fibers come
from the engineering package's own CLOSURE_ASSESSMENT_V2; each is scored for
whether this session can supply support for it, which for engineering means
"is the residual local wiring, or does it need infrastructure we do not have?"
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

ASSESSMENT = Path("research/orion_engineering_closure_v1/CLOSURE_ASSESSMENT_V2.json")
OUT = Path("research/orion_engineering_session_drive_v1/RESULT.json")

# Residuals whose fix is local wiring inside this repository. Support is
# declarable for these because the population is the codebase itself and the
# ceiling is "the call exists or it does not" — binary and observable.
LOCAL_WIRING = {
    "E3": "atomic persistence of the chart/transition/obstruction plane, all in-repo",
    "E4": "wire the incumbent metric-saturation decision heads into project_runtime",
    "E9": "have the problem-solving runtime call the EpistemicStatus gate",
}

# Residuals that need infrastructure this session does not have. Support is
# genuinely undeclarable: no population, no ceiling, nothing to measure against.
NEEDS_INFRASTRUCTURE = {
    "E6": "production multi-worker history backend",
    "E10": "network transport, authn and rate-limit adapter",
    "E11": "production observatory UI",
    "E12": "OpenTelemetry export adapter",
    "E13": "real identity provider, secret manager, policy enforcement",
    "E15": "PostgreSQL PITR and object-store restore drill",
    "E17": "measured release load and SLO envelope",
    "E18": "fresh hostile assurance on an exact production release",
    "E19": "real build-attestation verifier",
    "E20": "production runbook and a live operator drill",
}


def main() -> int:
    assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
    open_fibers = set(assessment["open_fibers"])
    by_id = {a["fiber_id"]: a for a in assessment["assessments"]}

    rows = []
    ledgers = []
    for fid in assessment["open_fibers"]:
        a = by_id[fid]
        residual_text = "; ".join(str(r) for r in (a.get("residuals") or []))

        if fid in LOCAL_WIRING:
            support = SupportDeclaration(
                population="this repository at the current head",
                predicate_in_domain=True,
                conditioning_variables=("module_boundary",),
                reachable_ceiling=1.0,
                ceiling_basis="the call site either exists or it does not; observable by import "
                "and by test, with no external dependency",
            )
            # A missing call is an interface defect, not a measurement defect.
            residual = AuditResidual(plausible_causes=(AuditCoordinate.INTERFACE,))
        else:
            support = None  # genuinely undeclarable
            residual = AuditResidual(
                plausible_causes=(AuditCoordinate.EVIDENCE,), resource_bound=True
            )

        step = next_step(
            target_id=fid,
            node=AuditNode(closure_coordinates_pass=False, material_open_residual=True),
            residual=residual,
            support=support,
        )
        ledgers.append(SessionLedger(fid).with_step(step))
        rows.append(
            {
                "fiber": fid,
                "level": a.get("level"),
                "residual": residual_text,
                "class": "LOCAL_WIRING" if fid in LOCAL_WIRING else "NEEDS_INFRASTRUCTURE",
                "proposed": step.proposed_action.value,
                "licensed": step.licensed_action.value,
                "blocked": step.blocked,
                "digest": step.digest(),
            }
        )

    counts = Counter(r["licensed"] for r in rows)
    actionable = [r for r in rows if not r["blocked"] and r["class"] == "LOCAL_WIRING"]

    result = {
        "schema_version": "rakl-orion-engineering-session-drive-v1",
        "status": "FRAMEWORK_DRIVEN_AT_ITS_OWN_ENGINEERING",
        "grants_scientific_authority": False,
        "question": "Which of Orion's own open engineering fibers can this session close?",
        "source": str(ASSESSMENT),
        "open_fibers": len(open_fibers),
        "licensed_action_counts": dict(counts.most_common()),
        "actionable_now": [r["fiber"] for r in actionable],
        "needs_infrastructure": sorted(NEEDS_INFRASTRUCTURE),
        "reading": (
            "The two fibers that matter most for an operable framework name the same gap in "
            "Orion's own words: E4, the incumbent metric-saturation decision heads are not wired "
            "into the project runtime, and E9, the problem-solving runtime does not call the "
            "EpistemicStatus gate. Both are local wiring. The remaining ten need infrastructure "
            "this session does not have, and the loop refuses them rather than pretending "
            "otherwise."
        ),
        "per_fiber": rows,
        "ledgers": [l.to_dict() for l in ledgers],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for r in rows:
        mark = "ABSTAIN" if r["licensed"] == "CANNOT_CHECK" else "ACT    "
        print(f"{mark} {r['fiber']:<4} {r['licensed']:<20} {r['residual'][:66]}")
    print()
    print(f"actionable local wiring: {[r['fiber'] for r in actionable]}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
