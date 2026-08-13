#!/usr/bin/env python3
"""Framework closure ledger: bounded method-saturation check.

"Closure" in Orion's own vocabulary is NOT absolute completeness (which is
non-certifiable in an open world); it is *bounded method-saturation at a cutoff*:
every registered mechanic must have
  (1) an executable implementation,
  (2) tests,
  (3) an evidence artifact (known-world/empirical, honestly labelled),
  (4) a reader-facing paper owner,
  (5) a registered open question (what would extend or falsify it).
A mechanic missing any coordinate is OPEN, not closed. The ledger prints per-mechanic
status and an overall verdict, and deliberately reports
GLOBAL_COMPLETENESS_CLAIMED=false: closure is at-cutoff saturation, not a proof
that no further mechanic exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "publication" / "papers"

# mechanic -> (implementation, tests, evidence artifact, paper owner file, open question note)
MECHANICS: dict[str, dict[str, list[str]]] = {
    # --- epistemic / structural / method cores (Papers I-III, V) ---
    "epistemic_authority_state": {
        "impl": ["src/rakl/authority_ledger.py", "src/rakl/epistemic_noninterference.py", "src/rakl/epistemic_evolution.py"],
        "tests": ["tests/test_formalism.py"],
        "evidence": ["research/empirical_10_of_10_v1"],
        "paper": ["paper-01-epistemic-mechanics/main.tex"],
        "open": ["independent external review (#216) remains a human-open coordinate"],
    },
    "directional_structural_witness": {
        "impl": ["src/rakl/structural_types.py"],
        "tests": ["tests/test_formalism.py", "tests/test_atlas_gluing.py"],
        "evidence": ["research/empirical_10_of_10_v1/PAPER3/OBJECTIVE", "research/llm_comparator_confirmatory_v1"],
        "paper": ["paper-02-structural-mechanics/main.tex"],
        "open": ["six-family robustness extension; cross-model comparator replication"],
    },
    "method_evolution": {
        "impl": ["src/rakl/driver_learning.py", "src/rakl/experience_learning.py", "src/rakl/failure_learning.py"],
        "tests": ["tests/test_rakl_v3_driver_learning.py"],
        "evidence": ["research/paper2_experience_benchmark_v1_3_2"],
        "paper": ["paper-03-method-evolution-mechanics/main.tex"],
        "open": ["four-arm causal attribution remains preregistered, unexecuted (capable model gated)"],
    },
    "training_ladder_phase1": {
        "impl": ["experiments/training_ladder/exposure_executor.py", "experiments/training_ladder/generator_v2.py", "experiments/training_ladder/phase1_v2.py"],
        "tests": ["tests/test_exposure_executor.py", "tests/test_training_ladder_phase0_1.py"],
        "evidence": ["research/paper4_phase1_results/ROOT_CAUSE.md"],
        "paper": ["paper-04-structural-learning-mechanics/main.tex"],
        "open": ["v2 ladder re-run pending; Phase-2 gated on learnability + #462"],
    },
    "math_assurance": {
        "impl": ["src/rakl/proof_dag.py", "src/rakl/invention_api.py"],
        "tests": ["tests/test_proof_dag.py", "tests/test_invention_api.py"],
        "evidence": ["research/unified_problem_solving_v1/VERIFICATION_LEDGER.json"],
        "paper": ["paper-05-verified-discovery-in-mathematics/main.tex"],
        "open": ["verified-transformation-geometry falsifier preregistered, unexecuted"],
    },
    # --- unified problem-solving mechanics (Paper VI 10c) ---
    "operational_map": {
        "impl": ["src/rakl/operational_map.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/known_world_stress.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["map discovery on natural (non-constructed) domains"],
    },
    "path_equivalence_quotient": {
        "impl": ["src/rakl/path_equivalence.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/path_quotient_savings.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["net saving after witness cost on natural domains"],
    },
    "path_cost_admissibility": {
        "impl": ["src/rakl/path_cost.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/known_world_stress.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["cost-vector calibration against real solver telemetry"],
    },
    "fieldability": {
        "impl": ["src/rakl/fieldability.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/field_hypothesis.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["field CONSTRUCTION (not given metric) on non-metric domains -- preregistered in Paper V lane"],
    },
    "mechanic_diagnosis": {
        "impl": ["src/rakl/mechanic_diagnosis.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/diagnosis_accuracy.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["diagnosis accuracy on real (non-injected) research failures"],
    },
    "solver_compilation": {
        "impl": ["src/rakl/solver_compilation.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/known_world_stress.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["compilation vs strong algorithm-selection parents"],
    },
    "solution_assembly": {
        "impl": ["src/rakl/solution_assembly.py"],
        "tests": ["tests/test_unified_solver_framework.py"],
        "evidence": ["research/unified_problem_solving_v1/results/known_world_stress.json"],
        "paper": ["paper-06-rakl-scientific-research-engine/source/sections/10c_unified_problem_solving.tex"],
        "open": ["assembly on long real proof/experiment DAGs"],
    },
    "unified_registry_ownership": {
        "impl": ["src/rakl/unified_solver_registry.py"],
        "tests": ["tests/test_unified_solver_registry.py"],
        "evidence": ["research/unified_problem_solving_v1/VERIFICATION_LEDGER.json"],
        "paper": ["publication/UNIFIED_PROBLEM_SOLVING_CROSS_PAPER_INTEGRATION.md"],
        "open": ["registry as live routing surface (currently audit-only)"],
    },
}


def _exists(rel: str) -> bool:
    p = ROOT / rel
    if p.exists():
        return True
    # paper paths may be given relative to publication/papers
    return (P / rel).exists()


def main() -> int:
    rows = {}
    all_closed = True
    for name, spec in MECHANICS.items():
        status = {}
        for coord in ("impl", "tests", "evidence", "paper"):
            ok = all(_exists(r) for r in spec[coord])
            status[coord] = {"ok": ok, "paths": spec[coord]}
            if not ok:
                all_closed = False
        status["open_question"] = spec["open"]
        status["closed_at_cutoff"] = all(status[c]["ok"] for c in ("impl", "tests", "evidence", "paper"))
        rows[name] = status
    ledger = {
        "schema_version": "orion-closure-ledger-v1",
        "definition": "closure = bounded method-saturation at cutoff: impl+tests+evidence+paper owner+registered open question per mechanic",
        "GLOBAL_COMPLETENESS_CLAIMED": False,
        "grants_scientific_authority": False,
        "mechanics": rows,
        "closed": sum(1 for r in rows.values() if r["closed_at_cutoff"]),
        "total": len(rows),
        "verdict": "CLOSED_AT_CUTOFF" if all_closed else "OPEN_COORDINATES_REMAIN",
    }
    out = ROOT / "research" / "unified_problem_solving_v1" / "results" / "CLOSURE_LEDGER.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2, sort_keys=True))
    print(f"CLOSURE={ledger['verdict']} ({ledger['closed']}/{ledger['total']} mechanics closed at cutoff)")
    for name, r in sorted(rows.items()):
        missing = [c for c in ("impl", "tests", "evidence", "paper") if not r[c]["ok"]]
        print(f"  {'CLOSED' if r['closed_at_cutoff'] else 'OPEN  '}  {name}" + (f"  missing: {missing}" if missing else ""))
    print("GLOBAL_COMPLETENESS_CLAIMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
