from __future__ import annotations

from collections import defaultdict
from itertools import product
import json
from math import factorial
from pathlib import Path

from rakl.fieldability import amortization_break_even_queries
from rakl.mechanic_diagnosis import diagnose_mechanic_signals
from rakl.operational_map import MapEdgeStatus, OperationalEdge, OperationalMapReceipt, verified_reachability
from rakl.path_cost import PathAdmissibility, PathCostVector, PathOption, explicit_lexicographic_select
from rakl.solver_compilation import PreservationValidationReceipt, SolverCompilationCandidate, TransformationEffect, compilation_break_even_uses
from rakl.vtg_hardening import OperationalEdgeAssuranceClass


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "research" / "unified_problem_solving_v1" / "results"
RESULT_FILE = RESULT_DIR / "known_world_stress.json"
SEED_LABEL = "deterministic-enumeration-v1"


def field_amortization() -> dict:
    build = 100.0
    extract = 10.0
    baseline = 30.0
    points = []
    for q in range(1, 41):
        field_total = build + q * extract
        baseline_total = q * baseline
        points.append({
            "queries": q,
            "field_total": field_total,
            "baseline_total": baseline_total,
            "field_over_baseline": field_total / baseline_total,
        })
    return {
        "build_cost": build,
        "extraction_per_query": extract,
        "baseline_per_query": baseline,
        "break_even_queries_continuous": amortization_break_even_queries(
            build_cost=build,
            extraction_per_query_cost=extract,
            baseline_per_query_cost=baseline,
        ),
        "points": points,
    }


def local_navigation_trap() -> dict:
    graph: dict[str, tuple[str, ...]] = {}
    heuristic: dict[str, int] = {}
    optimal_successor: dict[str, str] = {}
    for i in range(8):
        node = f"s{i}"
        nxt = f"s{i+1}"
        graph[node] = (nxt,)
        heuristic[node] = 10 - i
        optimal_successor[node] = nxt
    graph["s8"] = ("trap", "bridge")
    heuristic["s8"] = 2
    heuristic["trap"] = 0
    heuristic["bridge"] = 3
    optimal_successor["s8"] = "bridge"
    graph["trap"] = ()
    graph["bridge"] = ("goal",)
    heuristic["goal"] = 0
    graph["goal"] = ()
    optimal_successor["bridge"] = "goal"

    current = "s0"
    greedy_route = [current]
    correct_local_choices = 0
    local_decisions = 0
    while current != "goal":
        successors = graph[current]
        if not successors:
            break
        chosen = min(successors, key=lambda item: (heuristic[item], item))
        if current in optimal_successor:
            local_decisions += 1
            if chosen == optimal_successor[current]:
                correct_local_choices += 1
        greedy_route.append(chosen)
        current = chosen
    greedy_success = current == "goal"

    frontier: list[tuple[int, str, tuple[str, ...]]] = [(heuristic["s0"], "s0", ("s0",))]
    expansions = 0
    best_route: tuple[str, ...] | None = None
    while frontier:
        frontier.sort(key=lambda item: (item[0], item[1], item[2]))
        _, node, route = frontier.pop(0)
        expansions += 1
        if node == "goal":
            best_route = route
            break
        for successor in graph[node]:
            if successor not in route:
                frontier.append((heuristic[successor], successor, route + (successor,)))

    return {
        "local_decisions": local_decisions,
        "correct_local_choices": correct_local_choices,
        "local_action_alignment": correct_local_choices / local_decisions,
        "strict_greedy_success": greedy_success,
        "strict_greedy_route": greedy_route,
        "bounded_best_first_success": best_route is not None,
        "bounded_best_first_route": list(best_route or ()),
        "bounded_best_first_expansions": expansions,
        "interpretation": "high local alignment does not imply closed-loop greedy completeness",
    }


def path_quotient_growth() -> dict:
    rows = []
    for m in range(2, 11):
        histories = factorial(m)
        rows.append({
            "independent_transformations": m,
            "sequential_histories": histories,
            "exact_partial_order_classes": 1,
            "duplication_factor": histories,
        })
    return {"points": rows}


def _pattern_probability(pattern: tuple[bool, ...], valid_probability: float) -> float:
    out = 1.0
    for valid in pattern:
        out *= valid_probability if valid else (1.0 - valid_probability)
    return out


def _sequential_checks(flag_probabilities: list[float], costs: list[float]) -> tuple[float, float]:
    survive = 1.0
    expected_cost = 0.0
    for flag_probability, cost in zip(flag_probabilities, costs):
        expected_cost += survive * cost
        survive *= 1.0 - flag_probability
    return survive, expected_cost


def verification_pareto() -> dict:
    valid_p = 0.96
    edge_sensitivity = 0.96
    edge_false_positive = 0.01
    group_sensitivity = 0.92
    group_false_positive = 0.008
    root_sensitivity = 0.88
    root_false_positive = 0.004
    edge_cost = 1.0
    group_cost = 2.0
    root_cost = 4.0
    interfaces = 15
    group_size = 4
    strategies = defaultdict(lambda: {"false_accept_mass": 0.0, "false_reject_mass": 0.0, "invalid_mass": 0.0, "valid_mass": 0.0, "cost": 0.0})

    for pattern in product((False, True), repeat=interfaces):
        probability = _pattern_probability(pattern, valid_p)
        globally_valid = all(pattern)
        invalid_mass = 0.0 if globally_valid else probability
        valid_mass = probability if globally_valid else 0.0

        root_flag = root_false_positive if globally_valid else root_sensitivity
        root_accept = 1.0 - root_flag
        root_expected_cost = root_cost

        edge_flags = [edge_false_positive if valid else edge_sensitivity for valid in pattern]
        edge_accept, edge_expected_cost = _sequential_checks(edge_flags, [edge_cost] * interfaces)

        group_flags: list[float] = []
        for start in range(0, interfaces, group_size):
            group = pattern[start:start + group_size]
            group_flags.append(group_false_positive if all(group) else group_sensitivity)
        group_survive, group_expected_cost = _sequential_checks(group_flags, [group_cost] * len(group_flags))
        group_root_accept = group_survive * root_accept
        group_root_expected_cost = group_expected_cost + group_survive * root_cost

        edge_root_accept = edge_accept * root_accept
        edge_root_expected_cost = edge_expected_cost + edge_accept * root_cost

        policy_rows = {
            "ROOT_ONLY": (root_accept, root_expected_cost),
            "ALL_EDGES": (edge_accept, edge_expected_cost),
            "GROUPS_PLUS_ROOT": (group_root_accept, group_root_expected_cost),
            "EDGES_PLUS_ROOT": (edge_root_accept, edge_root_expected_cost),
        }
        for name, (accept_probability, expected_cost) in policy_rows.items():
            row = strategies[name]
            row["invalid_mass"] += invalid_mass
            row["valid_mass"] += valid_mass
            if globally_valid:
                row["false_reject_mass"] += probability * (1.0 - accept_probability)
            else:
                row["false_accept_mass"] += probability * accept_probability
            row["cost"] += probability * expected_cost

    result_rows = []
    for name in ("ROOT_ONLY", "ALL_EDGES", "GROUPS_PLUS_ROOT", "EDGES_PLUS_ROOT"):
        row = strategies[name]
        result_rows.append({
            "strategy": name,
            "false_accept_given_invalid": row["false_accept_mass"] / row["invalid_mass"],
            "false_reject_given_valid": row["false_reject_mass"] / row["valid_mass"],
            "expected_cost": row["cost"],
        })
    return {
        "interface_valid_probability": valid_p,
        "interfaces": interfaces,
        "checker_parameters": {
            "edge_sensitivity": edge_sensitivity,
            "edge_false_positive": edge_false_positive,
            "group_sensitivity": group_sensitivity,
            "group_false_positive": group_false_positive,
            "root_sensitivity": root_sensitivity,
            "root_false_positive": root_false_positive,
        },
        "points": result_rows,
        "claim_boundary": "illustrative exact expectation under registered independent checker/interface toy assumptions",
    }


def map_and_cost_gates() -> dict:
    receipt = OperationalMapReceipt(
        "map", "problem", "ops-v1", "chart",
        edges=(
            OperationalEdge(
                "sa", "s", "a", MapEdgeStatus.VERIFIED_TRANSITION, "toy",
                verification_id="v1",
                assurance_class=OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
                assurance_receipt_id="replay-sa",
            ),
            OperationalEdge("ag?", "a", "g", MapEdgeStatus.UNKNOWN, "toy"),
        ),
        unknown_coordinates=("goal_bridge",),
    )
    map_report = verified_reachability(receipt, start_state_id="s", target_state_id="g")

    valid = PathAdmissibility(True, True, True, True, True)
    invalid = PathAdmissibility(False, True, True, True, True)
    options = (
        PathOption("short_unlicensed", PathCostVector(compute=1, verification=1), invalid),
        PathOption("verified", PathCostVector(compute=6, verification=2), valid),
    )
    selected = explicit_lexicographic_select(options, coordinate_order=("compute", "verification"))
    return {
        "partial_map_verdict": map_report.verdict.value,
        "partial_map_establishes_impossibility": map_report.establishes_mathematical_impossibility,
        "selected_path_after_hard_constraints": selected.path_id if selected else None,
    }


def diagnosis_and_compilation() -> dict:
    diagnosis = diagnose_mechanic_signals(
        diagnosis_id="diag",
        problem_state_id="p",
        atom_id="a",
        fibre_snapshot_hash="f",
        residual_ids=("r",),
        signals=("local_metric_descends_root_stalls",),
        discriminator_ids=("compare_same_map_best_first",),
    )
    candidate = SolverCompilationCandidate(
        compilation_id="compile",
        source_problem_hash="p",
        specification_hash="spec",
        root_qoi="target",
        representation_id="chart",
        transform_id="identity",
        solver_id="compiled_solver",
        decoder_id="decode",
        verifier_id="verifier",
        claimed_effects=(TransformationEffect.COMPILE_TO_FIELD,),
        preservation_receipt=PreservationValidationReceipt(
            "preserve", "p", "spec", "target", "chart", "identity", "quotient-checker", True
        ),
        build_cost=100,
        execution_cost=5,
        decode_cost=1,
        verification_cost=4,
        invalidation_hazard_per_use=0.1,
    )
    return {
        "diagnosis_verdict": diagnosis.verdict.value,
        "diagnosis_candidate_causes": [item.value for item in diagnosis.candidate_causes],
        "compilation_one_shot_cost": candidate.one_shot_cost,
        "compilation_break_even_uses_vs_30": compilation_break_even_uses(candidate, baseline_per_use_cost=30),
        "compilation_stability_adjusted_per_use": candidate.stability_adjusted_per_use_cost,
    }


def generate_results() -> dict:
    return {
        "schema_version": "orion-unified-solver-known-world-v1",
        "status": "DEVELOPMENT_KNOWN_WORLD_MECHANISM_EVIDENCE_ONLY",
        "seed": SEED_LABEL,
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        "field_amortization": field_amortization(),
        "local_navigation": local_navigation_trap(),
        "path_quotient": path_quotient_growth(),
        "verification_pareto": verification_pareto(),
        "hard_gates": map_and_cost_gates(),
        "diagnosis_and_compilation": diagnosis_and_compilation(),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = generate_results()
    RESULT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
