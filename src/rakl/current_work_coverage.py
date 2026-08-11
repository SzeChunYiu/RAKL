"""Proposal-only current work-state coverage receipt.

A consequential application route can be locally self-consistent while omitting
relevant open issues, pull requests, or stacked branches.  This module binds the
open-work universe a route actually searched before it claims current-work
coverage.  It performs no network access, no registry writes, and promotes no
application evidence, mathematical, novelty, tool, review-independence, or
promotion authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Tuple


RECEIPT_SCHEMA_VERSION = "current-work-coverage-v1"

_REVISION_RE = re.compile(r"^[0-9A-Za-z._:+/-]{1,256}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CoverageSemantics(str, Enum):
    """How exhaustively the open-work index was searched."""

    FULL_ARTIFACT_ENUMERATION = "FULL_ARTIFACT_ENUMERATION"
    HASHED_INDEX_TARGETED_RETRIEVAL = "HASHED_INDEX_TARGETED_RETRIEVAL"
    SAMPLED_SUBSET = "SAMPLED_SUBSET"
    UNSPECIFIED = "UNSPECIFIED"


_BINDING_CAPABLE_SEMANTICS = frozenset(
    {
        CoverageSemantics.FULL_ARTIFACT_ENUMERATION,
        CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL,
    }
)


class WorkItemKind(str, Enum):
    ISSUE = "ISSUE"
    PULL_REQUEST = "PULL_REQUEST"


class WorkItemDisposition(str, Enum):
    INCLUDED = "INCLUDED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    STACKED = "STACKED"


class CurrentWorkVerdict(str, Enum):
    CURRENT_WORK_BOUND_PROPOSAL_ONLY = "CURRENT_WORK_BOUND_PROPOSAL_ONLY"
    CURRENT_WORK_INCOMPLETE = "CURRENT_WORK_INCOMPLETE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


class CurrentWorkBindingStatus(str, Enum):
    CURRENT_WORK_BOUND = "CURRENT_WORK_BOUND"
    CURRENT_WORK_NOT_BOUND = "CURRENT_WORK_NOT_BOUND"


class CurrentWorkGateVerdict(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    NOT_REQUIRED = "NOT_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def receipt_canonical_sha256(document: Mapping[str, Any]) -> str:
    subject = dict(document)
    subject.pop("receipt_canonical_sha256", None)
    return canonical_json_sha256(subject)


@dataclass(frozen=True)
class ObservedOpenWorkItem:
    work_item_id: str
    kind: WorkItemKind
    head_sha: str | None = None
    base_sha: str | None = None


@dataclass(frozen=True)
class WorkItemRecord:
    work_item_id: str
    kind: WorkItemKind
    disposition: WorkItemDisposition
    disposition_reason: str | None = None
    head_sha: str | None = None
    base_sha: str | None = None
    evidence_pointers: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_item_id": self.work_item_id,
            "kind": self.kind.value,
            "disposition": self.disposition.value,
            "disposition_reason": self.disposition_reason,
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class CurrentWorkCoverageReceipt:
    repository: str
    observed_default_branch: str
    observed_default_branch_head: str
    search_surface: Tuple[str, ...]
    bound_open_work_universe: Tuple[str, ...]
    work_item_records: Tuple[WorkItemRecord, ...]
    route_id: str
    public_trace_event_id: str
    claim_boundary: str
    evidence_pointers: Tuple[str, ...]
    open_work_index_hash: str = ""
    coverage_semantics: CoverageSemantics = CoverageSemantics.UNSPECIFIED
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "observed_default_branch": self.observed_default_branch,
            "observed_default_branch_head": self.observed_default_branch_head,
            "search_surface": list(self.search_surface),
            "open_work_index_hash": self.open_work_index_hash,
            "coverage_semantics": self.coverage_semantics.value,
            "bound_open_work_universe": list(self.bound_open_work_universe),
            "work_item_records": [record.to_dict() for record in self.work_item_records],
            "route_id": self.route_id,
            "public_trace_event_id": self.public_trace_event_id,
            "claim_boundary": self.claim_boundary,
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "grants_application_evidence_authority": False,
            "grants_mathematical_authority": False,
            "grants_novelty_authority": False,
            "grants_tool_authority": False,
            "grants_review_independence_authority": False,
            "grants_promotion_authority": False,
            "requires_full_pr_diff_enumeration": False,
        }

    def with_content_hash(self) -> "CurrentWorkCoverageReceipt":
        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )

    def record_for(self, work_item_id: str) -> WorkItemRecord | None:
        for record in self.work_item_records:
            if record.work_item_id == work_item_id:
                return record
        return None


@dataclass(frozen=True)
class CurrentWorkCoverageReport:
    verdict: CurrentWorkVerdict
    binding_status: CurrentWorkBindingStatus
    included_work_item_ids: Tuple[str, ...]
    rejected_work_item_ids: Tuple[str, ...]
    deferred_work_item_ids: Tuple[str, ...]
    stacked_work_item_ids: Tuple[str, ...]
    unaccounted_work_item_ids: Tuple[str, ...]
    stale_work_item_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def is_bound(self) -> bool:
        return self.binding_status is CurrentWorkBindingStatus.CURRENT_WORK_BOUND

    @property
    def grants_mathematical_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class CurrentWorkGateReport:
    verdict: CurrentWorkGateVerdict
    binding_status: CurrentWorkBindingStatus
    may_claim_current_work_bound: bool
    may_execute_under_current_work_contract: bool
    reasons: Tuple[str, ...]


def _structural_reasons(receipt: CurrentWorkCoverageReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    if not _REVISION_RE.match(receipt.observed_default_branch_head or ""):
        reasons.append("observed_default_branch_head_invalid")
    for name, value in (
        ("repository", receipt.repository),
        ("observed_default_branch", receipt.observed_default_branch),
        ("route_id", receipt.route_id),
        ("public_trace_event_id", receipt.public_trace_event_id),
        ("claim_boundary", receipt.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not receipt.search_surface:
        reasons.append("search_surface_missing")
    if not receipt.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    if not receipt.bound_open_work_universe:
        reasons.append("open_work_universe_unbound")
    if len(set(receipt.bound_open_work_universe)) != len(receipt.bound_open_work_universe):
        reasons.append("bound_open_work_universe_contains_duplicates")
    seen: set[str] = set()
    for record in receipt.work_item_records:
        if record.work_item_id in seen:
            reasons.append("duplicate_work_item_record")
            break
        seen.add(record.work_item_id)
    if not receipt.receipt_canonical_sha256:
        reasons.append("receipt_canonical_sha256_missing")
    elif not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        reasons.append("receipt_canonical_sha256_malformed")
    return tuple(reasons)


def _binding_status_for(verdict: CurrentWorkVerdict) -> CurrentWorkBindingStatus:
    if verdict is CurrentWorkVerdict.CURRENT_WORK_BOUND_PROPOSAL_ONLY:
        return CurrentWorkBindingStatus.CURRENT_WORK_BOUND
    return CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND


def audit_current_work_coverage(
    receipt: CurrentWorkCoverageReceipt | None,
    *,
    observed_open_work: Tuple[ObservedOpenWorkItem, ...],
    observed_default_branch_head: str | None = None,
    compare_work_state: bool = True,
) -> CurrentWorkCoverageReport:
    """Bind the open-work universe, failing closed on every gap."""

    empty: Tuple[str, ...] = ()
    if receipt is None:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.CANNOT_CHECK,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            empty,
            empty,
            empty,
            empty,
            empty,
            empty,
            ("current_work_coverage_receipt_missing",),
        )

    structural = _structural_reasons(receipt)
    if structural:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.CANNOT_CHECK,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            empty,
            empty,
            empty,
            empty,
            empty,
            empty,
            structural,
        )
    if receipt.receipt_canonical_sha256 != receipt_canonical_sha256(receipt.to_dict()):
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.REFUTED_CLAIM,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            empty,
            empty,
            empty,
            empty,
            empty,
            empty,
            ("receipt_canonical_sha256_mismatch",),
        )

    bound = tuple(receipt.bound_open_work_universe)
    bound_set = set(bound)
    observed = {item.work_item_id: item for item in observed_open_work}

    included: list[str] = []
    rejected: list[str] = []
    deferred: list[str] = []
    stacked: list[str] = []
    unaccounted: list[str] = []
    stale: list[str] = []
    reasons: list[str] = []
    unverifiable: list[str] = []
    refuting: list[str] = []

    if receipt.coverage_semantics is CoverageSemantics.UNSPECIFIED:
        unverifiable.append("coverage_semantics_unspecified")
    elif (
        receipt.coverage_semantics is CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL
        and not (receipt.open_work_index_hash or "").strip()
    ):
        unverifiable.append("open_work_index_hash_missing")
    elif receipt.coverage_semantics is CoverageSemantics.SAMPLED_SUBSET:
        reasons.append("sampled_subset_cannot_support_current_work_bound_claim")

    for work_item_id in sorted(observed):
        if work_item_id not in bound_set:
            unaccounted.append(work_item_id)
            reasons.append(f"observed_open_work_absent_from_bound_universe:{work_item_id}")

    for record in receipt.work_item_records:
        if record.work_item_id not in bound_set:
            refuting.append(f"work_item_record_outside_bound_universe:{record.work_item_id}")

    for work_item_id in bound:
        record = receipt.record_for(work_item_id)
        if record is None:
            unaccounted.append(work_item_id)
            reasons.append(f"unaccounted_work_item_in_bound_universe:{work_item_id}")
            continue
        if record.disposition is WorkItemDisposition.INCLUDED:
            included.append(work_item_id)
        elif record.disposition is WorkItemDisposition.REJECTED:
            rejected.append(work_item_id)
            if not (record.disposition_reason or "").strip():
                unverifiable.append(f"disposition_without_declared_reason:{work_item_id}")
        elif record.disposition is WorkItemDisposition.DEFERRED:
            deferred.append(work_item_id)
            if not (record.disposition_reason or "").strip():
                unverifiable.append(f"disposition_without_declared_reason:{work_item_id}")
        elif record.disposition is WorkItemDisposition.STACKED:
            stacked.append(work_item_id)
            if not (record.disposition_reason or "").strip():
                unverifiable.append(f"disposition_without_declared_reason:{work_item_id}")

        if compare_work_state and record.kind is WorkItemKind.PULL_REQUEST:
            current = observed.get(work_item_id)
            if current is not None and (
                (record.head_sha or "") != (current.head_sha or "")
                or (record.base_sha or "") != (current.base_sha or "")
            ):
                stale.append(work_item_id)

    if (
        compare_work_state
        and observed_default_branch_head is not None
        and observed_default_branch_head != receipt.observed_default_branch_head
    ):
        stale.append("default-branch")
        reasons.append("default_branch_head_changed_since_receipt")

    included_t = tuple(included)
    rejected_t = tuple(rejected)
    deferred_t = tuple(deferred)
    stacked_t = tuple(stacked)
    unaccounted_t = tuple(sorted(set(unaccounted)))
    stale_t = tuple(sorted(set(stale)))
    stale_reasons = tuple(
        f"covered_work_item_state_changed_since_receipt:{item_id}"
        for item_id in stale_t
        if item_id != "default-branch"
    )

    if unverifiable:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.CANNOT_CHECK,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            included_t,
            rejected_t,
            deferred_t,
            stacked_t,
            unaccounted_t,
            stale_t,
            tuple(unverifiable) + tuple(reasons) + stale_reasons,
        )
    if refuting:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.REFUTED_CLAIM,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            included_t,
            rejected_t,
            deferred_t,
            stacked_t,
            unaccounted_t,
            stale_t,
            tuple(refuting) + tuple(reasons) + stale_reasons,
        )
    if unaccounted_t or receipt.coverage_semantics is CoverageSemantics.SAMPLED_SUBSET:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.CURRENT_WORK_INCOMPLETE,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            included_t,
            rejected_t,
            deferred_t,
            stacked_t,
            unaccounted_t,
            stale_t,
            tuple(reasons) + stale_reasons,
        )
    if stale_t:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.REVALIDATION_REQUIRED,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            included_t,
            rejected_t,
            deferred_t,
            stacked_t,
            unaccounted_t,
            stale_t,
            tuple(reasons) + stale_reasons,
        )
    if receipt.coverage_semantics not in _BINDING_CAPABLE_SEMANTICS:
        return CurrentWorkCoverageReport(
            CurrentWorkVerdict.CURRENT_WORK_INCOMPLETE,
            CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND,
            included_t,
            rejected_t,
            deferred_t,
            stacked_t,
            unaccounted_t,
            stale_t,
            tuple(reasons) + ("coverage_semantics_not_binding_capable",),
        )
    return CurrentWorkCoverageReport(
        CurrentWorkVerdict.CURRENT_WORK_BOUND_PROPOSAL_ONLY,
        CurrentWorkBindingStatus.CURRENT_WORK_BOUND,
        included_t,
        rejected_t,
        deferred_t,
        stacked_t,
        unaccounted_t,
        stale_t,
        tuple(reasons)
        + (
            "every observed open work item is accounted for as included, rejected, deferred, or stacked",
            "current work coverage receipt is framework-process evidence and promotes no application or mathematical authority",
        ),
    )


def revalidation_required(
    receipt: CurrentWorkCoverageReceipt,
    *,
    observed_open_work: Tuple[ObservedOpenWorkItem, ...],
    observed_default_branch_head: str | None = None,
) -> Tuple[str, ...]:
    """Return work item ids whose head/base moved, plus default-branch when applicable."""

    observed = {item.work_item_id: item for item in observed_open_work}
    changed: list[str] = []
    if (
        observed_default_branch_head is not None
        and observed_default_branch_head != receipt.observed_default_branch_head
    ):
        changed.append("default-branch")
    for work_item_id in receipt.bound_open_work_universe:
        record = receipt.record_for(work_item_id)
        current = observed.get(work_item_id)
        if record is None or current is None:
            if work_item_id in observed:
                changed.append(work_item_id)
            continue
        if record.kind is WorkItemKind.PULL_REQUEST and (
            (record.head_sha or "") != (current.head_sha or "")
            or (record.base_sha or "") != (current.base_sha or "")
        ):
            changed.append(work_item_id)
    for work_item_id in sorted(observed):
        if work_item_id not in receipt.bound_open_work_universe:
            changed.append(work_item_id)
    return tuple(sorted(set(changed)))


def gate_current_work_coverage(
    receipt: CurrentWorkCoverageReceipt | None,
    *,
    observed_open_work: Tuple[ObservedOpenWorkItem, ...],
    require_current_work: bool,
    observed_default_branch_head: str | None = None,
) -> CurrentWorkGateReport:
    """Fail closed only when the contract explicitly requires current-work coverage."""

    not_bound = CurrentWorkBindingStatus.CURRENT_WORK_NOT_BOUND
    if not require_current_work:
        return CurrentWorkGateReport(
            CurrentWorkGateVerdict.NOT_REQUIRED,
            not_bound,
            False,
            True,
            ("current_work_coverage_not_required_by_contract",),
        )

    report = audit_current_work_coverage(
        receipt,
        observed_open_work=observed_open_work,
        observed_default_branch_head=observed_default_branch_head,
    )
    if report.verdict is CurrentWorkVerdict.CURRENT_WORK_BOUND_PROPOSAL_ONLY:
        return CurrentWorkGateReport(
            CurrentWorkGateVerdict.ALLOWED,
            report.binding_status,
            True,
            True,
            report.reasons,
        )
    if report.verdict is CurrentWorkVerdict.CANNOT_CHECK:
        return CurrentWorkGateReport(
            CurrentWorkGateVerdict.CANNOT_CHECK,
            report.binding_status,
            False,
            False,
            report.reasons,
        )
    return CurrentWorkGateReport(
        CurrentWorkGateVerdict.BLOCKED,
        report.binding_status,
        False,
        False,
        report.reasons
        + ("cannot_claim_current_work_bound_under_incomplete_or_stale_coverage",),
    )
