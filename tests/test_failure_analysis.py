from __future__ import annotations

import pytest

from rakl.failure_analysis import (
    FailureAnalysisKind,
    FailureAnalysisVerdict,
    MinimalityKind,
    OracleVerdict,
    exhaustive_global_minimum_failure,
    exhaustive_minimal_conflicts,
    exhaustive_minimal_corrections,
    find_minimal_conflict,
    find_minimal_correction,
    minimize_failure_conditions,
)


def _meta() -> dict[str, str]:
    return {
        "analysis_id": "analysis-1",
        "oracle_id": "oracle-1",
        "context_hash": "ctx-1",
        "revision_id": "rev-1",
    }


def _failure_report(ids, oracle):
    return minimize_failure_conditions(ids, oracle, failure_id="failure-1", **_meta())


def _conflict_report(ids, oracle):
    return find_minimal_conflict(ids, oracle, conflict_id="conflict-1", **_meta())


def _correction_report(ids, oracle):
    return find_minimal_correction(ids, oracle, correction_id="correction-1", **_meta())


def test_ddmin_finds_one_minimal_conjunctive_failure_and_preserves_authority_boundary() -> None:
    def oracle(items):
        return OracleVerdict.FAIL if {"A", "B"} <= set(items) else OracleVerdict.PASS

    report = _failure_report(("A", "B", "C", "D", "E"), oracle)
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert report.receipt.kind is FailureAnalysisKind.FAILURE_CONDITION_MINIMIZATION
    assert report.receipt.result_sets == (("A", "B"),)
    assert report.receipt.minimality_kind is MinimalityKind.ONE_MINIMAL
    assert report.receipt.grants_causal_authority is False
    assert report.receipt.grants_scientific_authority is False
    assert report.receipt.grants_method_promotion_authority is False
    assert "one_minimal_not_global_minimum" in report.receipt.notes


def test_ddmin_can_find_failure_independent_of_registered_conditions() -> None:
    def oracle(items):
        return OracleVerdict.FAIL

    report = _failure_report(("A", "B"), oracle)
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert report.receipt.result_sets == ((),)


def test_ddmin_refuses_cannot_check_instead_of_using_it_as_failure() -> None:
    def oracle(items):
        values = set(items)
        if values == {"A"}:
            return OracleVerdict.CANNOT_CHECK
        return OracleVerdict.FAIL if {"A", "B"} <= values else OracleVerdict.PASS

    report = _failure_report(("A", "B", "C"), oracle)
    assert report.verdict is FailureAnalysisVerdict.CANNOT_CHECK
    assert report.receipt is None
    assert report.cannot_check_calls >= 1


def test_ddmin_requires_initial_registered_failure() -> None:
    report = _failure_report(("A", "B"), lambda _: OracleVerdict.PASS)
    assert report.verdict is FailureAnalysisVerdict.NO_TARGET_PHENOMENON
    assert "initial_conditions_do_not_reproduce_registered_failure" in report.reasons


def test_exhaustive_failure_oracle_finds_all_minimum_cardinality_cores() -> None:
    def oracle(items):
        values = set(items)
        return OracleVerdict.FAIL if ({"A"} <= values or {"B"} <= values) else OracleVerdict.PASS

    report = exhaustive_global_minimum_failure(
        ("A", "B", "C"),
        oracle,
        failure_id="failure-min",
        **_meta(),
    )
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert report.receipt.minimality_kind is MinimalityKind.GLOBAL_MINIMUM_CARDINALITY
    assert report.receipt.result_sets == (("A",), ("B",))


def test_deletion_conflict_is_inclusion_minimal_but_not_claimed_minimum() -> None:
    # Two MUSes exist: {A,B} (size 2) and {C,D,E} (size 3). The deterministic
    # deletion order lands on the larger inclusion-minimal conflict on purpose.
    def consistent(items):
        values = set(items)
        bad = ({"A", "B"} <= values) or ({"C", "D", "E"} <= values)
        return OracleVerdict.FAIL if bad else OracleVerdict.PASS

    report = _conflict_report(("A", "B", "C", "D", "E"), consistent)
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert report.receipt.result_sets == (("C", "D", "E"),)
    assert report.receipt.minimality_kind is MinimalityKind.INCLUSION_MINIMAL
    assert "inclusion_minimal_not_minimum_cardinality" in report.receipt.notes
    assert report.receipt.grants_causal_authority is False


def test_exhaustive_conflict_oracle_returns_all_muses() -> None:
    def consistent(items):
        values = set(items)
        bad = ({"A", "B"} <= values) or ({"C", "D", "E"} <= values)
        return OracleVerdict.FAIL if bad else OracleVerdict.PASS

    report = exhaustive_minimal_conflicts(
        ("A", "B", "C", "D", "E"),
        consistent,
        conflict_id="all-mus",
        **_meta(),
    )
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert report.receipt.result_sets == (("A", "B"), ("C", "D", "E"))
    assert report.receipt.minimality_kind is MinimalityKind.COMPLETE_ENUMERATION_OF_INCLUSION_MINIMAL_SETS


def test_conflict_analysis_refuses_inconsistent_background() -> None:
    report = _conflict_report(("A", "B"), lambda _: OracleVerdict.FAIL)
    assert report.verdict is FailureAnalysisVerdict.NO_TARGET_PHENOMENON
    assert "background_itself_inconsistent_no_condition_conflict" in report.reasons


def test_conflict_analysis_refuses_cannot_check_minimality_probe() -> None:
    def consistent(items):
        values = set(items)
        if values == {"B"}:
            return OracleVerdict.CANNOT_CHECK
        return OracleVerdict.FAIL if {"A", "B"} <= values else OracleVerdict.PASS

    report = _conflict_report(("A", "B", "C"), consistent)
    assert report.verdict is FailureAnalysisVerdict.CANNOT_CHECK
    assert report.receipt is None


def test_minimal_correction_restores_consistency_and_is_inclusion_minimal() -> None:
    def consistent(items):
        values = set(items)
        bad = ({"A", "B"} <= values) or ({"C", "D"} <= values)
        return OracleVerdict.FAIL if bad else OracleVerdict.PASS

    report = _correction_report(("A", "B", "C", "D"), consistent)
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    removed = set(report.receipt.result_sets[0])
    assert len(removed) == 2
    assert removed & {"A", "B"}
    assert removed & {"C", "D"}
    assert report.receipt.minimality_kind is MinimalityKind.INCLUSION_MINIMAL
    assert "minimal_correction_is_removal_set_not_conflict" in report.receipt.notes


def test_exhaustive_correction_oracle_returns_all_mcses() -> None:
    def consistent(items):
        values = set(items)
        bad = ({"A", "B"} <= values) or ({"C", "D"} <= values)
        return OracleVerdict.FAIL if bad else OracleVerdict.PASS

    report = exhaustive_minimal_corrections(
        ("A", "B", "C", "D"),
        consistent,
        correction_id="all-mcs",
        **_meta(),
    )
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.receipt is not None
    assert set(report.receipt.result_sets) == {
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
    }


def test_correction_analysis_refuses_cannot_check() -> None:
    def consistent(items):
        values = set(items)
        if values == {"A"}:
            return OracleVerdict.CANNOT_CHECK
        return OracleVerdict.FAIL if {"A", "B"} <= values else OracleVerdict.PASS

    report = _correction_report(("A", "B"), consistent)
    assert report.verdict is FailureAnalysisVerdict.CANNOT_CHECK
    assert report.receipt is None


def test_duplicate_or_blank_condition_ids_fail_input_validation() -> None:
    with pytest.raises(ValueError, match="unique"):
        _failure_report(("A", "A"), lambda _: OracleVerdict.FAIL)
    with pytest.raises(ValueError, match="nonempty"):
        _failure_report(("A", ""), lambda _: OracleVerdict.FAIL)


def test_oracle_must_return_typed_verdict() -> None:
    with pytest.raises(TypeError, match="OracleVerdict"):
        _failure_report(("A",), lambda _: "FAIL")  # type: ignore[return-value]


def test_receipt_hash_is_deterministic_and_subject_bound() -> None:
    def oracle(items):
        return OracleVerdict.FAIL if "A" in items else OracleVerdict.PASS

    left = _failure_report(("A", "B"), oracle)
    right = _failure_report(("A", "B"), oracle)
    assert left.receipt is not None and right.receipt is not None
    assert left.receipt.content_hash == right.receipt.content_hash

    changed = minimize_failure_conditions(
        ("A", "B"),
        oracle,
        analysis_id="analysis-1",
        oracle_id="oracle-1",
        context_hash="different-context",
        revision_id="rev-1",
        failure_id="failure-1",
    )
    assert changed.receipt is not None
    assert changed.receipt.content_hash != left.receipt.content_hash


def test_reports_never_grant_authority_even_on_verified_result() -> None:
    report = _failure_report(("A",), lambda _: OracleVerdict.FAIL)
    assert report.verdict is FailureAnalysisVerdict.VERIFIED_RESULT
    assert report.grants_causal_authority is False
    assert report.grants_scientific_authority is False
    assert report.grants_method_promotion_authority is False
