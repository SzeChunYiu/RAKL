#!/usr/bin/env python3
"""Emit the degeneracy-audit artifact for the authority-leakage panels (#154).

Runs :mod:`rakl.authority_leakage_audit` over both the frozen V1 panel and the
V2 twin-pair panel and writes the result to
``research/AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json``.

Numbers in that artifact are produced here, never hand-written. Run:

    python3 scripts/audit_authority_leakage_panels.py

Exit codes are distinct so CI can tell the cases apart:

    0  V1 degenerate and V2 clean — the expected, recorded state
    1  V2 is degenerate: the replacement panel has a defect, fix the panel
    2  V1 audited clean: the auditor has lost the ability to fire, fix the
       auditor (a checker that cannot reproduce a known defect is decoration)
    3  a panel could not be audited at all
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rakl.authority_leakage_audit import (  # noqa: E402
    AUDIT_THRESHOLDS_FROZEN_AT,
    AuditStatus,
    audit_panel,
)
from rakl.authority_leakage_benchmark import frozen_case_panel  # noqa: E402
from rakl.authority_leakage_panel_v2 import (  # noqa: E402
    PANEL_V2_ID,
    frozen_case_panel_v2,
)

ARTIFACT_PATH = REPO_ROOT / "research" / "AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json"

V1_ID = "scientific-transition-authority-v1"


def main() -> int:
    v1 = audit_panel(frozen_case_panel(), V1_ID)
    v2 = audit_panel(frozen_case_panel_v2(), PANEL_V2_ID)

    artifact = {
        "schema_version": "authority-leakage-panel-audit-v1",
        "issue": 154,
        "status": "PROPOSAL_ONLY / NO_MODEL_EVALUATION / NEGATIVE_RESULT_PRESERVED",
        "thresholds_frozen_at": AUDIT_THRESHOLDS_FROZEN_AT,
        "claim_boundary": (
            "Records panel construction defects and their repair. Evaluates no "
            "model, reports no ALR for any system, and mints no scientific "
            "authority or benchmark-novelty claim."
        ),
        "summary": {
            "v1_status": v1.status.value,
            "v1_degenerate_checks": list(v1.degenerate_checks()),
            "v2_status": v2.status.value,
            "v2_degenerate_checks": list(v2.degenerate_checks()),
        },
        "negative_history": {
            "note": (
                "V1 is preserved verbatim in rakl.authority_leakage_benchmark."
                "frozen_case_panel and is not edited. Its freeze receipt stays "
                "valid: the V1 scorer source is byte-identical, which is why the "
                "V2-only correct_interpretation_index field lives on a subclass "
                "in rakl.authority_leakage_panel_v2 rather than on HiddenCaseLabels."
            ),
            "v1_defects_found": [
                "every case id restated its own answer, e.g. "
                "ALR-07-legitimate-mechanism-upgrade",
                "a responder reading only the case id cleared the joint competence "
                "ceiling without performing any scientific reasoning",
                "only 2 of 8 cases licensed any upgrade and the panel offered 3 "
                "allowed axes in total, leaving no power to detect over-conservatism",
            ],
            "auditor_self_corrections": [
                "an unbounded negation pattern matched 'no' inside 'nonetheless', "
                "producing a false positive on ALR-06",
                "flagging any negated axis mention treated 'no mechanism witness was "
                "measured' (legitimate evidence) as a leak; narrowed to negations "
                "bound to an authority noun",
                "single-feature separation tested only the full label signature and "
                "so could not fire on a panel of distinct labels; extended to label "
                "facets, which then surfaced a real n_evidence_roots shortcut in an "
                "early V2 draft",
                "facet purity without a base-rate test reported four chance groups "
                "as findings; gated on the probability of purity under the panel "
                "base rate",
            ],
        },
        "panels": {V1_ID: v1.to_dict(), PANEL_V2_ID: v2.to_dict()},
        "artifact_hashes": {V1_ID: v1.artifact_hash(), PANEL_V2_ID: v2.artifact_hash()},
        "grants_scientific_authority": False,
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print(f"  V1 {v1.status.value}: {', '.join(v1.degenerate_checks()) or 'no degenerate checks'}")
    print(f"  V2 {v2.status.value}: {', '.join(v2.degenerate_checks()) or 'no degenerate checks'}")

    if not v1.checks or not v2.checks:
        return 3
    if v1.status is not AuditStatus.DEGENERATE:
        print("FAIL: the auditor no longer reproduces V1's known defects", file=sys.stderr)
        return 2
    if v2.status is not AuditStatus.CLEAN:
        print("FAIL: V2 is degenerate; fix the panel, not the thresholds", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
