#!/usr/bin/env python3
"""Deterministic development-only conformance harness for operator absorption v1.

No external performance or novelty claim is made here.  The harness asks whether
the proposal-only Orion wrappers correctly absorb the semantics of failure
minimization and minimal conflict/correction analysis while preserving the
stronger-oracle distinctions frozen in PROTOCOL.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from rakl.failure_analysis import (
    FailureAnalysisVerdict,
    OracleVerdict,
    exhaustive_global_minimum_failure,
    exhaustive_minimal_conflicts,
    exhaustive_minimal_corrections,
    find_minimal_conflict,
    find_minimal_correction,
    minimize_failure_conditions,
)


SCHEMA_VERSION = "p5-p6-failure-analysis-development-v1"


def _meta(prefix: str) -> dict[str, str]:
    return {
        "analysis_id": f"dev:{prefix}",
        "oracle_id": f"known-world:{prefix}",
        "context_hash": "known-world-dev-context-v1",
        "revision_id": "operator-absorption-v1",
    }


def _failure_oracle(required_sets: tuple[frozenset[str], ...], *, cannot_check: frozenset[str] | None = None):
    def oracle(items):
        values = frozenset(items)
        if cannot_check is not None and values == cannot_check:
            return OracleVerdict.CANNOT_CHECK
        return OracleVerdict.FAIL if any(required <= values for required in required_sets) else OracleVerdict.PASS
    return oracle


def _consistency_oracle(conflicts: tuple[frozenset[str], ...], *, cannot_check: frozenset[str] | None = None):
    def oracle(items):
        values = frozenset(items)
        if cannot_check is not None and values == cannot_check:
            return OracleVerdict.CANNOT_CHECK
        return OracleVerdict.FAIL if any(conflict <= values for conflict in conflicts) else OracleVerdict.PASS
    return oracle


def _size_gap(result: tuple[str, ...], oracle_sets: tuple[tuple[str, ...], ...]) -> int:
    minimum = min(len(item) for item in oracle_sets)
    return len(result) - minimum


def run_development() -> dict:
    cases: list[dict] = []
    blockers: list[str] = []

    # D1: simple conjunctive failure with irrelevant conditions.
    fail_simple = _failure_oracle((frozenset({"A", "B"}),))
    dd_simple = minimize_failure_conditions(
        ("A", "B", "C", "D", "E"), fail_simple, failure_id="D1", **_meta("D1-ddmin")
    )
    oracle_simple = exhaustive_global_minimum_failure(
        ("A", "B", "C", "D", "E"), fail_simple, failure_id="D1", **_meta("D1-oracle")
    )
    d1_ok = (
        dd_simple.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and oracle_simple.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and dd_simple.receipt is not None
        and oracle_simple.receipt is not None
        and set(dd_simple.receipt.result_sets[0]) == {"A", "B"}
        and _size_gap(dd_simple.receipt.result_sets[0], oracle_simple.receipt.result_sets) == 0
    )
    if not d1_ok:
        blockers.append("D1_failure_minimization_semantics")
    cases.append({
        "case_id": "D1_FAIL_IRRELEVANT",
        "hard_gate_pass": d1_ok,
        "one_minimal": None if dd_simple.receipt is None else list(dd_simple.receipt.result_sets[0]),
        "global_minimum_sets": [] if oracle_simple.receipt is None else [list(x) for x in oracle_simple.receipt.result_sets],
        "minimality_gap": None if dd_simple.receipt is None or oracle_simple.receipt is None else _size_gap(dd_simple.receipt.result_sets[0], oracle_simple.receipt.result_sets),
        "candidate_oracle_calls": dd_simple.oracle_calls,
        "exhaustive_oracle_calls": oracle_simple.oracle_calls,
    })

    # D2: deliberate trap where one-minimal need not be globally minimum.
    # Ordering biases the deterministic ddmin parent toward the CDE core first.
    fail_multi = _failure_oracle((frozenset({"A", "B"}), frozenset({"C", "D", "E"})))
    dd_multi = minimize_failure_conditions(
        ("C", "D", "E", "A", "B"), fail_multi, failure_id="D2", **_meta("D2-ddmin")
    )
    oracle_multi = exhaustive_global_minimum_failure(
        ("C", "D", "E", "A", "B"), fail_multi, failure_id="D2", **_meta("D2-oracle")
    )
    d2_gap = None
    if dd_multi.receipt is not None and oracle_multi.receipt is not None:
        d2_gap = _size_gap(dd_multi.receipt.result_sets[0], oracle_multi.receipt.result_sets)
    d2_ok = (
        dd_multi.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and oracle_multi.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and dd_multi.receipt is not None
        and oracle_multi.receipt is not None
        and d2_gap is not None
        and d2_gap >= 0
        and "one_minimal_not_global_minimum" in dd_multi.receipt.notes
    )
    if not d2_ok:
        blockers.append("D2_one_minimal_vs_minimum_boundary")
    cases.append({
        "case_id": "D2_MINIMALITY_TRAP",
        "hard_gate_pass": d2_ok,
        "one_minimal": None if dd_multi.receipt is None else list(dd_multi.receipt.result_sets[0]),
        "global_minimum_sets": [] if oracle_multi.receipt is None else [list(x) for x in oracle_multi.receipt.result_sets],
        "minimality_gap": d2_gap,
        "candidate_oracle_calls": dd_multi.oracle_calls,
        "exhaustive_oracle_calls": oracle_multi.oracle_calls,
    })

    # D3: multiple MUSes; deletion-based treatment is required to return a real
    # inclusion-minimal conflict but is not required to enumerate or minimize cardinality.
    consistency_multi = _consistency_oracle((frozenset({"A", "B"}), frozenset({"C", "D", "E"})))
    conflict = find_minimal_conflict(
        ("A", "B", "C", "D", "E"), consistency_multi, conflict_id="D3", **_meta("D3-delete")
    )
    all_conflicts = exhaustive_minimal_conflicts(
        ("A", "B", "C", "D", "E"), consistency_multi, conflict_id="D3", **_meta("D3-oracle")
    )
    d3_gap = None
    if conflict.receipt is not None and all_conflicts.receipt is not None:
        d3_gap = _size_gap(conflict.receipt.result_sets[0], all_conflicts.receipt.result_sets)
    d3_ok = (
        conflict.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and all_conflicts.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and conflict.receipt is not None
        and all_conflicts.receipt is not None
        and tuple(sorted(all_conflicts.receipt.result_sets)) == (("A", "B"), ("C", "D", "E"))
        and d3_gap is not None
        and d3_gap >= 0
    )
    if not d3_ok:
        blockers.append("D3_conflict_semantics")
    cases.append({
        "case_id": "D3_MULTIPLE_MUS",
        "hard_gate_pass": d3_ok,
        "selected_inclusion_minimal_conflict": None if conflict.receipt is None else list(conflict.receipt.result_sets[0]),
        "all_mus": [] if all_conflicts.receipt is None else [list(x) for x in all_conflicts.receipt.result_sets],
        "cardinality_gap_to_smallest_mus": d3_gap,
        "candidate_oracle_calls": conflict.oracle_calls,
        "exhaustive_oracle_calls": all_conflicts.oracle_calls,
    })

    # D4: multiple correction choices; treatment must restore consistency and be
    # inclusion-minimal, while exhaustive oracle records the full MCS set.
    consistency_correction = _consistency_oracle((frozenset({"A", "B"}), frozenset({"C", "D"})))
    correction = find_minimal_correction(
        ("A", "B", "C", "D"), consistency_correction, correction_id="D4", **_meta("D4-delete")
    )
    all_corrections = exhaustive_minimal_corrections(
        ("A", "B", "C", "D"), consistency_correction, correction_id="D4", **_meta("D4-oracle")
    )
    expected_mcs = {("A", "C"), ("A", "D"), ("B", "C"), ("B", "D")}
    d4_ok = (
        correction.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and all_corrections.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
        and correction.receipt is not None
        and all_corrections.receipt is not None
        and set(all_corrections.receipt.result_sets) == expected_mcs
        and correction.receipt.result_sets[0] in expected_mcs
    )
    if not d4_ok:
        blockers.append("D4_correction_semantics")
    cases.append({
        "case_id": "D4_MULTIPLE_MCS",
        "hard_gate_pass": d4_ok,
        "selected_inclusion_minimal_correction": None if correction.receipt is None else list(correction.receipt.result_sets[0]),
        "all_mcs": [] if all_corrections.receipt is None else [list(x) for x in all_corrections.receipt.result_sets],
        "candidate_oracle_calls": correction.oracle_calls,
        "exhaustive_oracle_calls": all_corrections.oracle_calls,
    })

    # D5: CANNOT_CHECK is load-bearing and must never be treated as FAIL.
    fail_cc = _failure_oracle((frozenset({"A", "B"}),), cannot_check=frozenset({"A"}))
    dd_cc = minimize_failure_conditions(
        ("A", "B", "C"), fail_cc, failure_id="D5", **_meta("D5-cc")
    )
    consistency_cc = _consistency_oracle((frozenset({"A", "B"}),), cannot_check=frozenset({"B"}))
    conflict_cc = find_minimal_conflict(
        ("A", "B", "C"), consistency_cc, conflict_id="D5c", **_meta("D5-conflict-cc")
    )
    d5_ok = (
        dd_cc.verdict is FailureAnalysisVerdict.CANNOT_CHECK
        and dd_cc.receipt is None
        and conflict_cc.verdict is FailureAnalysisVerdict.CANNOT_CHECK
        and conflict_cc.receipt is None
    )
    if not d5_ok:
        blockers.append("D5_cannot_check_fail_closed")
    cases.append({
        "case_id": "D5_CANNOT_CHECK",
        "hard_gate_pass": d5_ok,
        "failure_minimizer_verdict": dd_cc.verdict.value,
        "conflict_analyzer_verdict": conflict_cc.verdict.value,
        "failure_cannot_check_calls": dd_cc.cannot_check_calls,
        "conflict_cannot_check_calls": conflict_cc.cannot_check_calls,
    })

    all_hard_gates_pass = not blockers and all(case["hard_gate_pass"] for case in cases)
    terminal = "PARENT_SEMANTICS_ABSORBED" if all_hard_gates_pass else "IMPLEMENTATION_DEFECT"

    return {
        "schema_version": SCHEMA_VERSION,
        "study": "P5_P6_FAILURE_ANALYSIS_OPERATOR_ABSORPTION_V1",
        "development_only": True,
        "grants_scientific_authority": False,
        "grants_promotion_authority": False,
        "performance_claim_against_quickxplain_or_marco": False,
        "terminal": terminal,
        "hard_gates_pass": all_hard_gates_pass,
        "blocking_failures": blockers,
        "cases": cases,
        "interpretation": (
            "If green, Orion has absorbed established failure-minimization and "
            "conflict/correction semantics with stronger authority/minimality "
            "boundaries. This does not establish a RAKL-specific performance residual."
        ),
        "next_step": (
            "Implement faithful QuickXplain/MARCO parent adapters and a disjoint "
            "comparative benchmark only if a RAKL-specific residual is claimed; "
            "otherwise keep PARENT_SEMANTICS_ABSORBED."
        ),
    }


def main() -> int:
    result = run_development()
    destination = Path(__file__).with_name("DEVELOPMENT_RESULT.json")
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["hard_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
