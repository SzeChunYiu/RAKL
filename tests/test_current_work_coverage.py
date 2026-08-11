"""Frozen hostile-world tests for the current work-state coverage receipt.

Fixtures are synthetic issues/PRs only. No problem-specific mathematics is
imported into framework authority.

The motivating failure is planted directly: open PR ``pr-118`` is in scope and
observed but never accounted for, while the remaining records stay locally
self-consistent. A consequential route must not claim ``CURRENT_WORK_BOUND``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from rakl.current_work_coverage import (
    CoverageSemantics,
    CurrentWorkBindingStatus,
    CurrentWorkCoverageReceipt,
    CurrentWorkGateVerdict,
    CurrentWorkVerdict,
    ObservedOpenWorkItem,
    WorkItemDisposition,
    WorkItemKind,
    WorkItemRecord,
    audit_current_work_coverage,
    gate_current_work_coverage,
    receipt_canonical_sha256,
    revalidation_required,
)


DEFAULT_HEAD = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
PR_118_HEAD = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
PR_118_BASE = "cccccccccccccccccccccccccccccccccccccccc"
PR_147_HEAD = "dddddddddddddddddddddddddddddddddddddddd"
PR_147_BASE = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
INDEX_HASH = "idx-open-work-millennium-rh-0007"
CLAIM_BOUNDARY = (
    "framework-process evidence only; binds the searched open-work universe and "
    "promotes no application evidence or mathematical authority"
)


def _observed(*ids: str) -> tuple[ObservedOpenWorkItem, ...]:
    items = {
        "pr-118": ObservedOpenWorkItem(
            "pr-118",
            WorkItemKind.PULL_REQUEST,
            head_sha=PR_118_HEAD,
            base_sha=PR_118_BASE,
        ),
        "pr-147": ObservedOpenWorkItem(
            "pr-147",
            WorkItemKind.PULL_REQUEST,
            head_sha=PR_147_HEAD,
            base_sha=PR_147_BASE,
        ),
        "issue-239": ObservedOpenWorkItem("issue-239", WorkItemKind.ISSUE),
    }
    selected = ids or tuple(items)
    return tuple(items[item_id] for item_id in selected)


def _included(
    work_item_id: str,
    *,
    kind: WorkItemKind = WorkItemKind.PULL_REQUEST,
    head_sha: str | None = None,
    base_sha: str | None = None,
    **overrides: Any,
) -> WorkItemRecord:
    heads = {
        "pr-118": (PR_118_HEAD, PR_118_BASE),
        "pr-147": (PR_147_HEAD, PR_147_BASE),
        "issue-239": (None, None),
    }
    default_head, default_base = heads[work_item_id]
    values: dict[str, Any] = {
        "work_item_id": work_item_id,
        "kind": kind if work_item_id != "issue-239" else WorkItemKind.ISSUE,
        "disposition": WorkItemDisposition.INCLUDED,
        "disposition_reason": None,
        "head_sha": default_head if head_sha is None else head_sha,
        "base_sha": default_base if base_sha is None else base_sha,
        "evidence_pointers": (f"index::{INDEX_HASH}::{work_item_id}",),
    }
    values.update(overrides)
    return WorkItemRecord(**values)


def _rejected(work_item_id: str, reason: str) -> WorkItemRecord:
    record = _included(work_item_id)
    return WorkItemRecord(
        work_item_id=record.work_item_id,
        kind=record.kind,
        disposition=WorkItemDisposition.REJECTED,
        disposition_reason=reason,
        head_sha=record.head_sha,
        base_sha=record.base_sha,
        evidence_pointers=record.evidence_pointers,
    )


def _receipt(**overrides: Any) -> CurrentWorkCoverageReceipt:
    values: dict[str, Any] = {
        "repository": "github.com/SzeChunYiu/RAKL_math",
        "observed_default_branch": "main",
        "observed_default_branch_head": DEFAULT_HEAD,
        "search_surface": (
            "is:open is:pr label:RH-ANA-003",
            "is:open is:issue RH-ANA-003",
        ),
        "open_work_index_hash": INDEX_HASH,
        "coverage_semantics": CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL,
        "bound_open_work_universe": ("pr-118", "pr-147", "issue-239"),
        "work_item_records": (
            _included("pr-118"),
            _included("pr-147"),
            _included("issue-239"),
        ),
        "route_id": "route::rh-ana-003::decomposition-0001",
        "public_trace_event_id": "trace::NEXT_STEP_PROPOSED::0011",
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_pointers": (f"index::{INDEX_HASH}",),
    }
    values.update(overrides)
    return CurrentWorkCoverageReceipt(**values).with_content_hash()


def _receipt_omitting_pr118(**overrides: Any) -> CurrentWorkCoverageReceipt:
    """Planted failure: PR 118 is bound/observed but has no accounting record."""

    values: dict[str, Any] = {
        "work_item_records": (
            _included("pr-147"),
            _included("issue-239"),
        ),
    }
    values.update(overrides)
    return _receipt(**values)


# --- clean baseline ----------------------------------------------------------


def test_fully_accounted_open_work_binds_cleanly() -> None:
    report = audit_current_work_coverage(
        _receipt(),
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.CURRENT_WORK_BOUND_PROPOSAL_ONLY
    assert report.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_BOUND
    assert report.is_bound is True
    assert report.unaccounted_work_item_ids == ()
    assert report.grants_mathematical_authority is False


def test_required_gate_allows_only_a_bound_receipt() -> None:
    gate = gate_current_work_coverage(
        _receipt(),
        observed_open_work=_observed(),
        require_current_work=True,
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert gate.verdict is CurrentWorkGateVerdict.ALLOWED
    assert gate.may_claim_current_work_bound is True
    assert gate.may_execute_under_current_work_contract is True


# --- motivating failure: silent omission of an in-scope open PR --------------


def test_omitted_in_scope_open_pr_cannot_claim_current_work_bound() -> None:
    report = audit_current_work_coverage(
        _receipt_omitting_pr118(),
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.CURRENT_WORK_INCOMPLETE
    assert report.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND
    assert report.is_bound is False
    assert report.unaccounted_work_item_ids == ("pr-118",)
    assert "unaccounted_work_item_in_bound_universe:pr-118" in report.reasons


def test_consequential_route_required_gate_blocks_omitted_open_pr() -> None:
    gate = gate_current_work_coverage(
        _receipt_omitting_pr118(),
        observed_open_work=_observed(),
        require_current_work=True,
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert gate.verdict is CurrentWorkGateVerdict.BLOCKED
    assert gate.may_claim_current_work_bound is False
    assert gate.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND
    assert "cannot_claim_current_work_bound_under_incomplete_or_stale_coverage" in (
        gate.reasons
    )


def test_observed_open_pr_absent_from_bound_universe_is_unaccounted() -> None:
    receipt = _receipt(
        bound_open_work_universe=("pr-147", "issue-239"),
        work_item_records=(_included("pr-147"), _included("issue-239")),
    )
    report = audit_current_work_coverage(
        receipt,
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.CURRENT_WORK_INCOMPLETE
    assert report.unaccounted_work_item_ids == ("pr-118",)
    assert "observed_open_work_absent_from_bound_universe:pr-118" in report.reasons


# --- declared exclusion remains searchable but non-authoritative ------------


def test_declared_rejection_with_reason_keeps_binding() -> None:
    receipt = _receipt(
        work_item_records=(
            _rejected("pr-118", "same-atom residual already opened as RH-ANA-004"),
            _included("pr-147"),
            _included("issue-239"),
        )
    )
    report = audit_current_work_coverage(
        receipt,
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.is_bound is True
    assert report.rejected_work_item_ids == ("pr-118",)
    assert report.included_work_item_ids == ("pr-147", "issue-239")


def test_rejection_without_reason_is_unverifiable() -> None:
    bad = _included("pr-118")
    receipt = _receipt(
        work_item_records=(
            WorkItemRecord(
                work_item_id=bad.work_item_id,
                kind=bad.kind,
                disposition=WorkItemDisposition.REJECTED,
                disposition_reason=None,
                head_sha=bad.head_sha,
                base_sha=bad.base_sha,
                evidence_pointers=bad.evidence_pointers,
            ),
            _included("pr-147"),
            _included("issue-239"),
        )
    )
    report = audit_current_work_coverage(
        receipt,
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.CANNOT_CHECK
    assert report.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND
    assert "disposition_without_declared_reason:pr-118" in report.reasons


# --- ordinary actions without a current-work requirement --------------------


def test_ordinary_action_without_requirement_is_unaffected_by_missing_receipt() -> None:
    gate = gate_current_work_coverage(
        None,
        observed_open_work=_observed(),
        require_current_work=False,
    )
    assert gate.verdict is CurrentWorkGateVerdict.NOT_REQUIRED
    assert gate.may_execute_under_current_work_contract is True
    assert gate.may_claim_current_work_bound is False


def test_ordinary_action_does_not_block_on_incomplete_supplied_receipt() -> None:
    gate = gate_current_work_coverage(
        _receipt_omitting_pr118(),
        observed_open_work=_observed(),
        require_current_work=False,
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert gate.verdict is CurrentWorkGateVerdict.NOT_REQUIRED
    assert gate.may_execute_under_current_work_contract is True
    assert gate.may_claim_current_work_bound is False


def test_required_contract_blocks_missing_receipt() -> None:
    gate = gate_current_work_coverage(
        None,
        observed_open_work=_observed(),
        require_current_work=True,
    )
    assert gate.verdict is CurrentWorkGateVerdict.CANNOT_CHECK
    assert gate.may_claim_current_work_bound is False
    assert "current_work_coverage_receipt_missing" in gate.reasons


# --- freshness / revalidation -----------------------------------------------


def test_default_branch_move_requires_revalidation() -> None:
    report = audit_current_work_coverage(
        _receipt(),
        observed_open_work=_observed(),
        observed_default_branch_head="ffffffffffffffffffffffffffffffffffffffff",
    )
    assert report.verdict is CurrentWorkVerdict.REVALIDATION_REQUIRED
    assert report.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND
    assert "default-branch" in report.stale_work_item_ids


def test_open_pr_head_move_requires_revalidation() -> None:
    moved = (
        ObservedOpenWorkItem(
            "pr-118",
            WorkItemKind.PULL_REQUEST,
            head_sha="1111111111111111111111111111111111111111",
            base_sha=PR_118_BASE,
        ),
        ObservedOpenWorkItem(
            "pr-147",
            WorkItemKind.PULL_REQUEST,
            head_sha=PR_147_HEAD,
            base_sha=PR_147_BASE,
        ),
        ObservedOpenWorkItem("issue-239", WorkItemKind.ISSUE),
    )
    report = audit_current_work_coverage(
        _receipt(),
        observed_open_work=moved,
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.REVALIDATION_REQUIRED
    assert report.stale_work_item_ids == ("pr-118",)
    assert revalidation_required(
        _receipt(),
        observed_open_work=moved,
        observed_default_branch_head=DEFAULT_HEAD,
    ) == ("pr-118",)


def test_sampled_semantics_cannot_support_bound_claim() -> None:
    receipt = _receipt(coverage_semantics=CoverageSemantics.SAMPLED_SUBSET)
    report = audit_current_work_coverage(
        receipt,
        observed_open_work=_observed(),
        observed_default_branch_head=DEFAULT_HEAD,
    )
    assert report.verdict is CurrentWorkVerdict.CURRENT_WORK_INCOMPLETE
    assert report.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND


def test_receipt_never_grants_authority_flags() -> None:
    document = _receipt().to_dict()
    assert document["grants_application_evidence_authority"] is False
    assert document["grants_mathematical_authority"] is False
    assert document["grants_novelty_authority"] is False
    assert document["grants_tool_authority"] is False
    assert document["grants_review_independence_authority"] is False
    assert document["grants_promotion_authority"] is False
    assert document["requires_full_pr_diff_enumeration"] is False


def test_content_hash_is_stable_and_excludes_itself() -> None:
    receipt = _receipt()
    document = receipt.to_dict()
    assert receipt.receipt_canonical_sha256 == receipt_canonical_sha256(document)
    mutated = dict(document)
    mutated["route_id"] = "route::mutated"
    assert receipt_canonical_sha256(mutated) != receipt.receipt_canonical_sha256


# --- schema ------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/current-work-coverage-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_schema_accepts_a_bound_receipt_document() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(_receipt().to_dict())


def test_schema_rejects_authority_true() -> None:
    document = _receipt().to_dict()
    document["grants_mathematical_authority"] = True
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []


@pytest.mark.parametrize(
    "missing_field",
    [
        "repository",
        "observed_default_branch_head",
        "search_surface",
        "bound_open_work_universe",
        "work_item_records",
        "claim_boundary",
    ],
)
def test_schema_requires_load_bearing_fields(missing_field: str) -> None:
    document = _receipt().to_dict()
    document.pop(missing_field)
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []
