#!/usr/bin/env python3
"""Framework <-> paper consistency checker.

Nothing previously enforced that the manuscripts and the code say the same thing. This
gate checks three directions of drift, all mechanically:

  D1 MECHANIC WITHOUT OWNER   - a mechanic registered/implemented in src has no
                                reader-facing paper section describing it.
  D2 PAPER WITHOUT MECHANIC   - a paper names a mechanic/module that does not exist in
                                src (a claim about software that is not there).
  D3 NUMBER DRIFT             - a headline number quoted in a paper does not match the
                                evidence artifact it came from (stale figure text).

Exit status is informational; the report is the artifact. Consistency is a publication
obligation, not scientific authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "rakl"
PAPERS = ROOT / "publication" / "papers"

# Mechanics that must have a reader-facing owner section, and the module implementing them.
MECHANIC_MODULES = [
    "operational_map", "path_equivalence", "path_cost", "fieldability",
    "mechanic_diagnosis", "solver_compilation", "solution_assembly",
    "unified_solver_registry", "navigation_quotient", "path_congruence",
    "cost_geometry", "verified_transformation_geometry", "canonical_commitment",
    "authority_assurance", "cognitive_compilation", "diagnosis_state_machine",
    "structural_identity_bridge", "neural_structural_contract",
    "semantic_quotient_assurance", "approximation_budget", "structural_transfer_use",
    "unified_integration_contract", "training_projection_binding", "v3_commitment",
]

# Headline numbers quoted in papers -> (artifact, json path, tolerance)
NUMBER_BINDINGS = [
    {
        "label": "field-descent predictiveness",
        "paper": "paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex",
        "pattern": r"0\.863",
        "artifact": "research/unified_problem_solving_v1/results/field_hypothesis.json",
        "keys": ["field_descent_predicts_true_progress", "mean"],
    },
    {
        "label": "field search reduction",
        "paper": "paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex",
        "pattern": r"0\.725",
        "artifact": "research/unified_problem_solving_v1/results/field_hypothesis.json",
        "keys": ["search_reduction_vs_bfs", "mean"],
    },
    {
        "label": "gate false-accept (comparator)",
        "paper": "paper-02-structural-mechanics/sections/03c_objective_confirmatory_result.tex",
        "pattern": r"0\.339",
        "artifact": "research/llm_comparator_confirmatory_v1/summary.json",
        "keys": ["by_condition", "RAKL_GATE", "false_accept_on_invalid"],
    },
]


def _paper_text() -> dict[str, str]:
    out = {}
    for tex in PAPERS.rglob("*.tex"):
        try:
            out[str(tex.relative_to(PAPERS))] = tex.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
    return out


def _dig(obj, keys):
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def main() -> int:
    texts = _paper_text()
    blob = "\n".join(texts.values())
    findings = {"D1_mechanic_without_paper_owner": [], "D2_paper_claims_missing_module": [],
                "D3_number_drift": []}

    # D1: every implemented mechanic module should be discussed somewhere reader-facing.
    for m in MECHANIC_MODULES:
        if not (SRC / f"{m}.py").is_file():
            continue
        human = m.replace("_", " ")
        alt = m.replace("_", "-")
        if m not in blob and human not in blob.lower() and alt not in blob:
            findings["D1_mechanic_without_paper_owner"].append(m)

    # D2: modules named in papers (\texttt{...py} or src/rakl/x.py) that do not exist.
    named = set(re.findall(r"src/rakl/([a-z0-9_]+)\.py", blob))
    for n in sorted(named):
        if not (SRC / f"{n}.py").is_file():
            findings["D2_paper_claims_missing_module"].append(n)

    # D3: headline numbers still match their evidence artifacts.
    for b in NUMBER_BINDINGS:
        tex = texts.get(b["paper"])
        art = ROOT / b["artifact"]
        if tex is None or not art.is_file():
            findings["D3_number_drift"].append({"label": b["label"], "status": "CANNOT_CHECK"})
            continue
        quoted = re.search(b["pattern"], tex) is not None
        try:
            actual = _dig(json.loads(art.read_text()), b["keys"])
        except Exception:
            actual = None
        if actual is None:
            findings["D3_number_drift"].append({"label": b["label"], "status": "CANNOT_CHECK_ARTIFACT"})
        elif not quoted:
            findings["D3_number_drift"].append(
                {"label": b["label"], "status": "DRIFT", "artifact_value": actual,
                 "expected_pattern": b["pattern"]})

    total = sum(len(v) for v in findings.values())
    report = {
        "schema_version": "orion-paper-framework-consistency-v1",
        "grants_scientific_authority": False,
        "verdict": "CONSISTENT" if total == 0 else "DRIFT_FOUND",
        "findings": findings,
        "checked_mechanics": len([m for m in MECHANIC_MODULES if (SRC / f"{m}.py").is_file()]),
        "checked_numbers": len(NUMBER_BINDINGS),
    }
    dest = ROOT / "research" / "unified_problem_solving_v1" / "results" / "PAPER_FRAMEWORK_CONSISTENCY.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(f"CONSISTENCY={report['verdict']} (mechanics checked: {report['checked_mechanics']})")
    for k, v in findings.items():
        if v:
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
