"""Frozen hostile-world tests for the cross-problem memory coverage receipt.

Fixtures are synthetic lanes, tools and failure ids only.  No problem-specific
mathematics is imported into framework authority.

The motivating failure is planted directly: ``lane-gamma`` is registered and
inside the bound universe but is never inspected, while the remaining records
stay locally self-consistent.  A completeness/counting claim over that universe
must fail closed rather than read as correct.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from rakl.memory_coverage import (
    CompletenessClaim,
    CompletenessClaimKind,
    CompletenessClaimVerdict,
    CoverageQueryStatus,
    CoverageSemantics,
    CoverageVerdict,
    CrossProblemCoverageReceipt,
    LaneCoverageRecord,
    LaneInspectionStatus,
    RegisteredLane,
    RegisteredLane as Lane,
    audit_completeness_claim,
    audit_memory_coverage,
    receipt_canonical_sha256,
    revalidation_required,
)


REGISTRY_REVISION = "d8ac4102285c4ed1ba0fbd5d8818dc4c4731a8cc"
LANE_STATE = {
    "lane-alpha": ("head-alpha-07", "idx-alpha-07"),
    "lane-beta": ("head-beta-03", "idx-beta-03"),
    "lane-gamma": ("head-gamma-11", "idx-gamma-11"),
}
CLAIM_BOUNDARY = (
    "framework-process evidence only; binds the searched universe and promotes "
    "no application evidence or mathematical authority"
)


def _registry(*lane_ids: str) -> tuple[RegisteredLane, ...]:
    return tuple(
        Lane(lane_id, LANE_STATE[lane_id][0], LANE_STATE[lane_id][1])
        for lane_id in (lane_ids or tuple(LANE_STATE))
    )


def _inspected(
    lane_id: str,
    *,
    result_ids: tuple[str, ...] = (),
    semantics: CoverageSemantics = CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL,
    **overrides: Any,
) -> LaneCoverageRecord:
    head, index = LANE_STATE[lane_id]
    values: dict[str, Any] = {
        "lane_id": lane_id,
        "lane_head_revision": head,
        "index_manifest_hash": index,
        "inspection_status": LaneInspectionStatus.INSPECTED,
        "coverage_semantics": semantics,
        "result_ids": result_ids,
        "evidence_pointers": (f"index::{index}",),
    }
    values.update(overrides)
    return LaneCoverageRecord(**values)


def _deferred(lane_id: str, reason: str | None = "lane frozen pending calibration") -> LaneCoverageRecord:
    head, index = LANE_STATE[lane_id]
    return LaneCoverageRecord(
        lane_id=lane_id,
        lane_head_revision=head,
        index_manifest_hash=index,
        inspection_status=LaneInspectionStatus.DEFERRED_DECLARED,
        coverage_semantics=CoverageSemantics.UNSPECIFIED,
        deferral_reason=reason,
        evidence_pointers=(f"index::{index}",),
    )


def _receipt(**overrides: Any) -> CrossProblemCoverageReceipt:
    values: dict[str, Any] = {
        "registry_repository": "github.com/example/research-registry",
        "registry_revision": REGISTRY_REVISION,
        "synthesis_id": "synthesis::cross-lane-reuse-audit::0001",
        "public_trace_event_id": "trace::EXPERIENCE_MEMORY_REVIEW::0007",
        "bound_lane_universe": ("lane-alpha", "lane-beta", "lane-gamma"),
        "lane_records": (
            _inspected("lane-alpha", result_ids=("R-alpha-001",)),
            _inspected("lane-beta", result_ids=("R-beta-001",)),
            _inspected("lane-gamma", result_ids=("R-gamma-001",)),
        ),
        "query_status": CoverageQueryStatus.MATCHES_FOUND,
        "claim_boundary": CLAIM_BOUNDARY,
        "query_terms": ("bridge stability audit", "cross-lane reuse"),
        "structural_coordinates": ("shared invariant", "reuse-stable composition"),
        "desired_effects": ("locate prior reuse of T-SHARED-BRIDGE-AUDIT",),
        "result_ids": ("R-alpha-001", "R-beta-001", "R-gamma-001"),
        "evidence_pointers": ("registry::" + REGISTRY_REVISION,),
    }
    values.update(overrides)
    return CrossProblemCoverageReceipt(**values).with_content_hash()


def _receipt_missing_gamma(**overrides: Any) -> CrossProblemCoverageReceipt:
    """The planted failure: gamma is bound but never inspected.

    The remaining records stay internally consistent, which is exactly why the
    incompleteness is invisible without this object.
    """

    values: dict[str, Any] = {
        "lane_records": (
            _inspected("lane-alpha", result_ids=("R-alpha-001",)),
            _inspected("lane-beta", result_ids=("R-beta-001",)),
        ),
        "result_ids": ("R-alpha-001", "R-beta-001"),
    }
    values.update(overrides)
    return _receipt(**values)


def _no_match_receipt(**overrides: Any) -> CrossProblemCoverageReceipt:
    values: dict[str, Any] = {
        "lane_records": (
            _inspected("lane-alpha"),
            _inspected("lane-beta"),
            _inspected("lane-gamma"),
        ),
        "query_status": CoverageQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE,
        "result_ids": (),
    }
    values.update(overrides)
    return _receipt(**values)


def _claim(**overrides: Any) -> CompletenessClaim:
    values: dict[str, Any] = {
        "claim_id": "claim::0001",
        "kind": CompletenessClaimKind.REUSE_COUNT,
        "statement": "T-SHARED-BRIDGE-AUDIT has been reused in exactly three lanes",
        "asserted_count": 3,
    }
    values.update(overrides)
    return CompletenessClaim(**values)


# --- clean baseline ----------------------------------------------------------


def test_fully_covered_universe_binds_cleanly() -> None:
    report = audit_memory_coverage(_receipt(), registered_lane_universe=_registry())
    assert report.verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY
    assert report.uninspected_lane_ids == ()
    assert report.stale_lane_ids == ()
    assert set(report.inspected_lane_ids) == set(LANE_STATE)


def test_correct_count_claim_over_a_covered_universe_is_licensed() -> None:
    report = audit_completeness_claim(
        _receipt(), _claim(), registered_lane_universe=_registry()
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY
    assert report.licensed is True
    assert report.freshness_rechecked is True


# --- the motivating failure: bound but uninspected lane ----------------------


def test_lane_in_the_bound_universe_without_a_record_is_uninspected() -> None:
    report = audit_memory_coverage(
        _receipt_missing_gamma(), registered_lane_universe=_registry()
    )
    assert report.verdict is CoverageVerdict.COVERAGE_INCOMPLETE
    assert report.uninspected_lane_ids == ("lane-gamma",)
    assert "uninspected_lane_in_bound_universe:lane-gamma" in report.reasons


def test_locally_consistent_snapshot_cannot_carry_a_completeness_claim() -> None:
    """The count is self-consistent with what was searched and still fails closed."""

    report = audit_completeness_claim(
        _receipt_missing_gamma(),
        _claim(asserted_count=2, statement="this is the second reuse"),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE
    assert report.licensed is False
    assert "claim_ranges_over_uninspected_lane:lane-gamma" in report.reasons


def test_an_undercounted_claim_over_a_covered_universe_is_refuted_not_merely_rejected() -> None:
    report = audit_completeness_claim(
        _receipt(),
        _claim(asserted_count=2, statement="this is the second reuse"),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE
    assert "asserted_count_contradicts_bound_results" in report.reasons


def test_registered_lane_absent_from_the_bound_universe_is_uninspected() -> None:
    report = audit_memory_coverage(
        _receipt(
            bound_lane_universe=("lane-alpha", "lane-beta"),
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",)),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
            ),
            result_ids=("R-alpha-001", "R-beta-001"),
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.COVERAGE_INCOMPLETE
    assert "lane-gamma" in report.uninspected_lane_ids
    assert "registered_lane_absent_from_bound_universe:lane-gamma" in report.reasons


# --- unbounded narrative "no match" ------------------------------------------


def test_unbounded_no_match_has_no_valid_receipt() -> None:
    report = audit_memory_coverage(
        _receipt(bound_lane_universe=(), lane_records=(), result_ids=()),
        registered_lane_universe=(),
    )
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert "lane_universe_unbound" in report.reasons


def test_unbounded_no_match_claim_is_rejected_with_its_own_reason() -> None:
    report = audit_completeness_claim(
        _receipt(bound_lane_universe=(), lane_records=(), result_ids=()),
        _claim(
            kind=CompletenessClaimKind.NO_RELEVANT_CROSS_PROBLEM_MEMORY,
            asserted_count=None,
            statement="no relevant cross-problem memory exists",
        ),
        registered_lane_universe=(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_UNBOUND_UNIVERSE
    assert report.licensed is False


def test_bounded_no_match_claim_is_licensed() -> None:
    report = audit_completeness_claim(
        _no_match_receipt(),
        _claim(
            kind=CompletenessClaimKind.NO_RELEVANT_CROSS_PROBLEM_MEMORY,
            asserted_count=None,
            statement="no relevant cross-problem memory exists in the bound universe",
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY


def test_negative_claim_contradicted_by_a_bound_result_is_refuted() -> None:
    report = audit_completeness_claim(
        _receipt(),
        _claim(
            kind=CompletenessClaimKind.NO_OTHER_LANE_REUSED_ARTIFACT,
            asserted_count=None,
            statement="no other lane has reused this tool",
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE
    assert any("negative_claim_contradicted_by_bound_result" in r for r in report.reasons)


# --- declared deferral is allowed, but does not back a claim -----------------


def test_declared_deferral_is_allowed_and_recorded() -> None:
    report = audit_memory_coverage(
        _receipt(
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",)),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _deferred("lane-gamma"),
            ),
            result_ids=("R-alpha-001", "R-beta-001"),
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY
    assert report.deferred_lane_ids == ("lane-gamma",)
    assert report.uninspected_lane_ids == ()


def test_deferral_without_a_declared_reason_cannot_be_checked() -> None:
    report = audit_memory_coverage(
        _receipt(
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",)),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _deferred("lane-gamma", reason=None),
            ),
            result_ids=("R-alpha-001", "R-beta-001"),
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert "deferral_without_declared_reason:lane-gamma" in report.reasons


def test_completeness_claim_over_a_deferred_lane_is_rejected() -> None:
    receipt = _receipt(
        lane_records=(
            _inspected("lane-alpha", result_ids=("R-alpha-001",)),
            _inspected("lane-beta", result_ids=("R-beta-001",)),
            _deferred("lane-gamma"),
        ),
        result_ids=("R-alpha-001", "R-beta-001"),
    )
    report = audit_completeness_claim(
        receipt, _claim(asserted_count=2), registered_lane_universe=_registry()
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE
    assert "claim_ranges_over_deferred_lane:lane-gamma" in report.reasons


def test_claim_scoped_away_from_the_deferred_lane_is_licensed() -> None:
    receipt = _receipt(
        lane_records=(
            _inspected("lane-alpha", result_ids=("R-alpha-001",)),
            _inspected("lane-beta", result_ids=("R-beta-001",)),
            _deferred("lane-gamma"),
        ),
        result_ids=("R-alpha-001", "R-beta-001"),
    )
    report = audit_completeness_claim(
        receipt,
        _claim(asserted_count=2, subject_lane_ids=("lane-alpha", "lane-beta")),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY
    assert report.scope_lane_ids == ("lane-alpha", "lane-beta")


def test_claim_scoped_outside_the_bound_universe_is_rejected() -> None:
    report = audit_completeness_claim(
        _receipt(),
        _claim(subject_lane_ids=("lane-omega",)),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE
    assert "claim_ranges_outside_bound_universe:lane-omega" in report.reasons


# --- coverage semantics are typed and explicit -------------------------------


def test_hashed_index_targeted_retrieval_backs_completeness_without_full_enumeration() -> None:
    report = audit_memory_coverage(_receipt(), registered_lane_universe=_registry())
    assert (
        report.weakest_coverage_semantics
        is CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL
    )
    assert report.verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY
    assert _receipt().to_dict()["requires_full_artifact_enumeration"] is False


def test_hashed_index_semantics_without_an_index_hash_cannot_be_checked() -> None:
    report = audit_memory_coverage(
        _receipt(
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",), index_manifest_hash=""),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _inspected("lane-gamma", result_ids=("R-gamma-001",)),
            )
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert "index_manifest_hash_missing:lane-alpha" in report.reasons


def test_unspecified_coverage_semantics_cannot_be_checked() -> None:
    report = audit_memory_coverage(
        _receipt(
            lane_records=(
                _inspected(
                    "lane-alpha",
                    result_ids=("R-alpha-001",),
                    semantics=CoverageSemantics.UNSPECIFIED,
                ),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _inspected("lane-gamma", result_ids=("R-gamma-001",)),
            )
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert "coverage_semantics_unspecified:lane-alpha" in report.reasons


def test_sampled_lane_is_a_valid_search_that_cannot_back_a_claim() -> None:
    receipt = _receipt(
        lane_records=(
            _inspected("lane-alpha", result_ids=("R-alpha-001",)),
            _inspected("lane-beta", result_ids=("R-beta-001",)),
            _inspected(
                "lane-gamma",
                result_ids=("R-gamma-001",),
                semantics=CoverageSemantics.SAMPLED_SUBSET,
            ),
        )
    )
    coverage = audit_memory_coverage(receipt, registered_lane_universe=_registry())
    assert coverage.verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY
    assert coverage.weakest_coverage_semantics is CoverageSemantics.SAMPLED_SUBSET

    claim = audit_completeness_claim(
        receipt, _claim(), registered_lane_universe=_registry()
    )
    assert claim.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE
    assert "claim_ranges_over_sampled_lane:lane-gamma" in claim.reasons


# --- re-verification trigger -------------------------------------------------


def test_unchanged_registry_requires_no_revalidation() -> None:
    assert revalidation_required(_receipt(), registered_lane_universe=_registry()) == ()
    report = audit_memory_coverage(_receipt(), registered_lane_universe=_registry())
    assert report.verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY


@pytest.mark.parametrize("moved", ["head", "index"])
def test_changed_lane_head_or_index_triggers_revalidation(moved: str) -> None:
    head, index = LANE_STATE["lane-gamma"]
    current = _registry("lane-alpha", "lane-beta") + (
        Lane(
            "lane-gamma",
            head + "-moved" if moved == "head" else head,
            index + "-moved" if moved == "index" else index,
        ),
    )
    assert revalidation_required(_receipt(), registered_lane_universe=current) == (
        "lane-gamma",
    )
    report = audit_memory_coverage(_receipt(), registered_lane_universe=current)
    assert report.verdict is CoverageVerdict.REVALIDATION_REQUIRED
    assert report.stale_lane_ids == ("lane-gamma",)
    assert "covered_lane_state_changed_since_receipt:lane-gamma" in report.reasons


def test_claim_over_a_stale_lane_is_rejected() -> None:
    head, index = LANE_STATE["lane-gamma"]
    current = _registry("lane-alpha", "lane-beta") + (
        Lane("lane-gamma", head, index + "-moved"),
    )
    report = audit_completeness_claim(
        _receipt(), _claim(), registered_lane_universe=current
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE
    assert "claim_ranges_over_stale_lane:lane-gamma" in report.reasons


def test_newly_registered_lane_triggers_revalidation() -> None:
    extra = _registry() + (Lane("lane-delta", "head-delta-01", "idx-delta-01"),)
    assert "lane-delta" in revalidation_required(
        _receipt(), registered_lane_universe=extra
    )


def test_offline_mode_states_that_freshness_was_not_rechecked() -> None:
    head, index = LANE_STATE["lane-gamma"]
    current = _registry("lane-alpha", "lane-beta") + (
        Lane("lane-gamma", head, index + "-moved"),
    )
    report = audit_completeness_claim(
        _receipt(), _claim(), registered_lane_universe=current, recheck_freshness=False
    )
    assert report.verdict is CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY
    assert report.freshness_rechecked is False


# --- receipt integrity -------------------------------------------------------


def test_result_outside_the_bound_universe_is_refuted() -> None:
    report = audit_memory_coverage(
        _receipt(result_ids=("R-alpha-001", "R-beta-001", "R-gamma-001", "R-omega-001")),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.REFUTED_CLAIM
    assert "result_outside_bound_universe:R-omega-001" in report.reasons


def test_lane_record_outside_the_bound_universe_is_refuted() -> None:
    report = audit_memory_coverage(
        _receipt(
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",)),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _inspected("lane-gamma", result_ids=("R-gamma-001",)),
                LaneCoverageRecord(
                    lane_id="lane-omega",
                    lane_head_revision="head-omega",
                    index_manifest_hash="idx-omega",
                    inspection_status=LaneInspectionStatus.INSPECTED,
                    coverage_semantics=CoverageSemantics.FULL_ARTIFACT_ENUMERATION,
                ),
            )
        ),
        registered_lane_universe=_registry(),
    )
    assert report.verdict is CoverageVerdict.REFUTED_CLAIM
    assert "lane_record_outside_bound_universe:lane-omega" in report.reasons


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"query_status": CoverageQueryStatus.MATCHES_FOUND, "result_ids": ()}, "matches_found_status_without_result_ids"),
        (
            {"query_status": CoverageQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE},
            "no_match_status_with_result_ids",
        ),
    ],
)
def test_query_status_must_agree_with_bound_results(
    overrides: dict[str, Any], reason: str
) -> None:
    report = audit_memory_coverage(
        _receipt(**overrides), registered_lane_universe=_registry()
    )
    assert report.verdict is CoverageVerdict.REFUTED_CLAIM
    assert reason in report.reasons


def test_missing_receipt_fails_closed() -> None:
    report = audit_memory_coverage(None, registered_lane_universe=_registry())
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert report.universe_is_bound is False


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"registry_revision": "not a revision!"}, "registry_revision_invalid"),
        ({"synthesis_id": ""}, "synthesis_id_missing"),
        ({"public_trace_event_id": ""}, "public_trace_event_id_missing"),
        ({"claim_boundary": "  "}, "claim_boundary_missing"),
        ({"evidence_pointers": ()}, "evidence_pointers_missing"),
        (
            {"query_terms": (), "structural_coordinates": (), "desired_effects": ()},
            "search_specification_missing",
        ),
        (
            {"bound_lane_universe": ("lane-alpha", "lane-alpha", "lane-beta", "lane-gamma")},
            "bound_lane_universe_contains_duplicates",
        ),
    ],
)
def test_structurally_unbound_receipts_cannot_be_checked(
    overrides: dict[str, Any], reason: str
) -> None:
    report = audit_memory_coverage(
        _receipt(**overrides), registered_lane_universe=_registry()
    )
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert reason in report.reasons


def test_absent_content_hash_cannot_be_checked_but_present_hash_can() -> None:
    unhashed = replace(_receipt(), receipt_canonical_sha256="")
    report = audit_memory_coverage(unhashed, registered_lane_universe=_registry())
    assert report.verdict is CoverageVerdict.CANNOT_CHECK
    assert "receipt_canonical_sha256_missing" in report.reasons
    assert audit_memory_coverage(
        _receipt(), registered_lane_universe=_registry()
    ).verdict is CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY


def test_tampered_content_hash_is_refuted_not_merely_unchecked() -> None:
    tampered = replace(_receipt(), synthesis_id="synthesis::rewritten")
    report = audit_memory_coverage(tampered, registered_lane_universe=_registry())
    assert report.verdict is CoverageVerdict.REFUTED_CLAIM
    assert "receipt_canonical_sha256_mismatch" in report.reasons


def test_reuse_count_claim_without_an_asserted_count_cannot_be_checked() -> None:
    report = audit_completeness_claim(
        _receipt(), _claim(asserted_count=None), registered_lane_universe=_registry()
    )
    assert report.verdict is CompletenessClaimVerdict.CANNOT_CHECK
    assert "reuse_count_claim_without_asserted_count" in report.reasons


def test_receipt_promotes_no_authority() -> None:
    report = audit_memory_coverage(_receipt(), registered_lane_universe=_registry())
    assert report.grants_application_evidence_authority is False
    assert report.grants_mathematical_authority is False
    document = _receipt().to_dict()
    assert document["grants_application_evidence_authority"] is False
    assert document["grants_mathematical_authority"] is False


# --- schema ------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/research-memory-coverage-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_receipt_documents_validate_against_the_frozen_schema() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for receipt in (
        _receipt(),
        _receipt_missing_gamma(),
        _no_match_receipt(),
        _receipt(
            lane_records=(
                _inspected("lane-alpha", result_ids=("R-alpha-001",)),
                _inspected("lane-beta", result_ids=("R-beta-001",)),
                _deferred("lane-gamma"),
            ),
            result_ids=("R-alpha-001", "R-beta-001"),
        ),
    ):
        assert list(validator.iter_errors(receipt.to_dict())) == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d.update(grants_mathematical_authority=True),
        lambda d: d.update(requires_full_artifact_enumeration=True),
        lambda d: d.update(bound_lane_universe=[]),
        lambda d: d.update(query_status="NO_RELEVANT_MATCH"),
    ],
)
def test_schema_rejects_unbound_or_authority_claiming_documents(mutator: Any) -> None:
    document = _receipt().to_dict()
    mutator(document)
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []


def test_content_hash_excludes_only_itself() -> None:
    receipt = _receipt()
    document = receipt.to_dict()
    assert receipt.receipt_canonical_sha256 == receipt_canonical_sha256(document)
    document["synthesis_id"] = "synthesis::other"
    assert receipt_canonical_sha256(document) != receipt.receipt_canonical_sha256
