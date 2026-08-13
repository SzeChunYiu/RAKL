#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

from rakl.formal_contracts import METHOD_SURFACES


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "unified_problem_solving_v1" / "VTG_FORMALIZATION_LEDGER.json"
RESULT = ROOT / "research" / "unified_problem_solving_v1" / "results" / "vtg_formalization_audit.json"

VALID_STATUS = {"OPEN_FORMALIZATION", "MECHANIZED"}
FORBIDDEN_TOKENS = ("sorry", "admit", "axiom ", "opaque unsafe")


def audit(data: dict) -> list[str]:
    problems: list[str] = []
    if data.get("schema") != "orion.vtg.formalization-ledger.v1":
        problems.append("schema_mismatch")
    obligations = data.get("obligations") or []
    if not obligations:
        problems.append("obligations_missing")
        return problems
    ids = [str(row.get("obligation_id", "")).strip() for row in obligations]
    if len(ids) != len(set(ids)):
        problems.append("duplicate_obligation_id")

    for row in obligations:
        oid = str(row.get("obligation_id", "")).strip()
        owner = str(row.get("owner_surface", "")).strip()
        status = str(row.get("status", "")).strip()
        statement = str(row.get("statement", "")).strip()
        sources = tuple(str(item).strip() for item in row.get("statement_sources", ()))
        artifact = str(row.get("required_completion_artifact", "")).strip()
        next_cut = str(row.get("next_epistemic_cut", "")).strip()
        if not oid or not statement or not artifact:
            problems.append(f"{oid or '<missing>'}:missing_identity_statement_or_artifact")
        if owner not in METHOD_SURFACES:
            problems.append(f"{oid}:owner_surface_not_canonical:{owner}")
        if status not in VALID_STATUS:
            problems.append(f"{oid}:invalid_status:{status}")
        if not sources:
            problems.append(f"{oid}:statement_sources_missing")
        for source in sources:
            if not (ROOT / source).exists():
                problems.append(f"{oid}:missing_statement_source:{source}")
        if status == "OPEN_FORMALIZATION":
            if not next_cut:
                problems.append(f"{oid}:open_formalization_missing_next_cut")
        elif status == "MECHANIZED":
            path = ROOT / artifact
            if not path.exists():
                problems.append(f"{oid}:mechanized_artifact_missing:{artifact}")
            else:
                text = path.read_text(encoding="utf-8").lower()
                for token in FORBIDDEN_TOKENS:
                    if token in text:
                        problems.append(f"{oid}:mechanized_artifact_contains_escape_hatch:{token.strip()}")
    return problems


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    problems = audit(data)
    open_ids = [row["obligation_id"] for row in data.get("obligations", ()) if row.get("status") == "OPEN_FORMALIZATION"]
    mechanized_ids = [row["obligation_id"] for row in data.get("obligations", ()) if row.get("status") == "MECHANIZED"]
    result = {
        "schema": "orion.vtg.formalization-audit.v1",
        "ledger_id": data.get("ledger_id"),
        "obligation_count": len(data.get("obligations") or []),
        "open_formalization_ids": open_ids,
        "mechanized_ids": mechanized_ids,
        "valid": not problems,
        "problems": problems,
        "mathematical_theory_complete_claimed": False,
        "scientific_authority_granted": False,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VTG_FORMALIZATION_OBLIGATIONS={result['obligation_count']}")
    print(f"VTG_FORMALIZATION_OPEN={len(open_ids)}")
    print(f"VTG_FORMALIZATION_VALID={'true' if not problems else 'false'}")
    print("MATHEMATICAL_THEORY_COMPLETE_CLAIMED=false")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    for problem in problems:
        print(problem, file=sys.stderr)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
