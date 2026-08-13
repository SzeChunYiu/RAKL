from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_vtg_terminology import audit


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "unified_problem_solving_v1" / "VTG_TERMINOLOGY_LEDGER.json"


def test_vtg_terminology_ledger_has_no_false_merge_or_owner_problem():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert audit(data) == []


def test_vtg_terminology_ledger_explicitly_separates_load_bearing_false_friends():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = {row["concept_id"]: row for row in data["entries"]}
    assert "verified transition" in rows["VERIFIED_APPLICABILITY"]["must_not_conflate_with"]
    assert "kernel derivation edge" in rows["REPLAY_OPERATIONAL_EDGE"]["must_not_conflate_with"]
    assert "sound over-approximating abstraction" in rows["EXACT_NAVIGATION_QUOTIENT"]["must_not_conflate_with"]
    assert "budget-conditioned value" in rows["INTRINSIC_GEOMETRY"]["must_not_conflate_with"]
    assert "solution certificate" in rows["SEARCH_TRAJECTORY"]["must_not_conflate_with"]
    assert "global amalgamation" in rows["LOCAL_COMPATIBILITY"]["must_not_conflate_with"]
    assert "nontrivial geometry improvement" in rows["GEOMETRY_EXISTENCE"]["must_not_conflate_with"]
    assert "Grothendieck fibration" in rows["PROBLEM_FIBRE"]["must_not_conflate_with"]
