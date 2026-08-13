#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

from rakl.unified_solver_registry import UNIFIED_SOLVER_MECHANICS


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "research" / "unified_problem_solving_v1" / "results" / "vtg_self_certification_audit.json"

# These field names previously acted as release/assurance gates with nothing
# stronger than a Boolean. They are forbidden in the proposal-side VTG modules.
FORBIDDEN_BOOL_FIELDS = {
    "passed",
    "accepted",
    "verifier_passed",
    "coverage_complete",
    "target_preserved",
    "forward_simulation_passed",
    "route_lifting_passed",
    "cost_relation_passed",
    "validated",
}

# A bare string such as `foo_receipt_id` is acceptable as a cross-reference,
# but not as the only load-bearing validation field. The hardened modules use
# actual evidence/receipt objects for those gates, so regressions are forbidden.
FORBIDDEN_LOAD_BEARING_ID_FIELDS = {
    "assurance_receipt_id",
    "rank_well_foundedness_receipt_id",
    "progress_action_verifier_id",
    "minima_goal_verifier_id",
    "parent_invariant_receipt_id",
    "final_verifier_receipt_id",
    "concretization_or_lifting_id",
    "transition_soundness_verifier_id",
    "target_preservation_verifier_id",
    "exact_two_way_verifier_id",
}

DANGEROUS_TRUE_PREFIXES = (
    "grants_",
    "establishes_",
    "supports_exact_",
    "supports_global_",
)


def _annotation_is_bool(annotation: ast.expr | None) -> bool:
    return isinstance(annotation, ast.Name) and annotation.id == "bool"


def _literal_true_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) and child.value.value is True:
            return True
    return False


def audit_file(path: Path) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name in FORBIDDEN_BOOL_FIELDS and _annotation_is_bool(node.annotation):
                problems.append(f"{path.relative_to(ROOT)}:{node.lineno}:forbidden_load_bearing_bool:{name}")
            if name in FORBIDDEN_LOAD_BEARING_ID_FIELDS:
                problems.append(f"{path.relative_to(ROOT)}:{node.lineno}:forbidden_string_only_validation_gate:{name}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith(DANGEROUS_TRUE_PREFIXES) and _literal_true_return(node):
                problems.append(f"{path.relative_to(ROOT)}:{node.lineno}:authority_or_global_claim_literal_true:{node.name}")
    return problems


def audited_paths() -> tuple[Path, ...]:
    paths = {ROOT / item.module_path for item in UNIFIED_SOLVER_MECHANICS}
    paths.update(
        {
            ROOT / "src/rakl/framework_closure.py",
            ROOT / "src/rakl/vtg_hardening.py",
        }
    )
    return tuple(sorted(paths))


def main() -> int:
    problems: list[str] = []
    paths = audited_paths()
    for path in paths:
        if not path.exists():
            problems.append(f"missing_registered_module:{path.relative_to(ROOT)}")
            continue
        problems.extend(audit_file(path))

    result = {
        "schema": "orion.vtg.self-certification-audit.v1",
        "audited_files": [str(path.relative_to(ROOT)) for path in paths],
        "problem_count": len(problems),
        "problems": problems,
        "valid": not problems,
        "global_hidden_issue_absence_claimed": False,
        "scientific_authority_granted": False,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VTG_SELF_CERTIFICATION_FILES={len(paths)}")
    print(f"VTG_SELF_CERTIFICATION_VALID={'true' if not problems else 'false'}")
    print("GLOBAL_HIDDEN_ISSUE_ABSENCE_CLAIMED=false")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    for problem in problems:
        print(problem, file=sys.stderr)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
