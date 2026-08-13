from __future__ import annotations

import json
from pathlib import Path

from rakl.unified_solver_registry import UNIFIED_SOLVER_MECHANICS, validate_unified_solver_registry


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "unified_problem_solving_v1" / "VERIFICATION_LEDGER.json"
DOC = ROOT / "docs" / "ORION_UNIFIED_FRAMEWORK_VERIFICATION_LEDGER.md"


def main() -> int:
    problems: list[str] = []
    report = validate_unified_solver_registry()
    if not report.valid:
        problems.append(f"registry_invalid:{report.problems}")
    if report.grants_scientific_authority:
        problems.append("registry_illegally_grants_scientific_authority")
    if report.establishes_global_framework_completeness:
        problems.append("registry_illegally_claims_global_completeness")

    for spec in UNIFIED_SOLVER_MECHANICS:
        for rel in (spec.module_path,) + spec.test_paths:
            if not (ROOT / rel).is_file():
                problems.append(f"registered_path_missing:{spec.mechanic_id}:{rel}")

    if not LEDGER.is_file():
        problems.append("verification_ledger_missing")
    else:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
        ledger_ids = {item["id"] for item in data.get("mechanics", ())}
        registry_ids = {item.mechanic_id for item in UNIFIED_SOLVER_MECHANICS}
        if ledger_ids != registry_ids:
            problems.append(f"ledger_registry_id_mismatch:{sorted(registry_ids-ledger_ids)}:{sorted(ledger_ids-registry_ids)}")
        boundary = data.get("claim_boundary", {})
        forbidden_true = (
            "global_no_bug_proof",
            "global_logic_completeness_proof",
            "global_bibliographic_completeness",
            "scientific_authority_granted",
            "method_promotion_granted",
        )
        for key in forbidden_true:
            if boundary.get(key) is not False:
                problems.append(f"claim_boundary_not_fail_closed:{key}")
        if not data.get("remaining_cannot_prove"):
            problems.append("remaining_cannot_prove_missing")

    if not DOC.is_file():
        problems.append("verification_document_missing")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in (
            "UNKNOWN != BLOCKED",
            "Hard legality",
            "READY_FOR_EXTERNAL_AUTHORITY_GATE",
            "absence of every undiscovered software bug",
        ):
            if needle not in text:
                problems.append(f"verification_document_missing_invariant:{needle}")

    if problems:
        print("UNIFIED_FRAMEWORK_AUDIT=FAIL")
        for problem in problems:
            print(problem)
        return 1

    print("UNIFIED_FRAMEWORK_AUDIT=PASS")
    print(f"REGISTERED_MECHANICS={len(UNIFIED_SOLVER_MECHANICS)}")
    print("GLOBAL_COMPLETENESS_CLAIMED=false")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
