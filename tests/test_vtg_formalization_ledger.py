from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_vtg_formalization import audit


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "unified_problem_solving_v1" / "VTG_FORMALIZATION_LEDGER.json"


def test_vtg_formalization_obligations_are_owned_and_well_formed():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert audit(data) == []


def test_vtg_formalization_ledger_does_not_pretend_open_theorems_are_mechanized():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    obligations = data["obligations"]
    assert obligations
    assert all(row["status"] in {"OPEN_FORMALIZATION", "MECHANIZED"} for row in obligations)
    assert any(row["status"] == "OPEN_FORMALIZATION" for row in obligations)
