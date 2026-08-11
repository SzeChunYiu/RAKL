"""Proposal-only cross-problem research-memory coverage receipt.

A cross-problem synthesis routinely makes completeness and counting claims —
"no other domain has reused this tool", "this is the second reuse", "no relevant
cross-problem memory exists", "that lane remains uncalibrated".  Each of those is
a statement about a *search universe*, but a narrative "no match" carries no
universe with it.  A locally self-consistent snapshot can therefore coexist with
a lane that was registered, was in scope, and was simply never inspected.

This module makes that universe explicit and binds it before the claim.  Full
artifact enumeration is deliberately not required: a hashed index/manifest plus
targeted retrieval is sufficient, provided the coverage semantics are stated as a
typed field rather than assumed.  The module performs no network access, no
registry access and no writes, and promotes no application evidence or
mathematical authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Tuple


RECEIPT_SCHEMA_VERSION = "research-memory-coverage-v1"

_REVISION_RE = re.compile(r"^[0-9A-Za-z._:+/-]{1,256}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CoverageSemantics(str, Enum):
    """How exhaustively a lane was actually searched.

    ``FULL_ARTIFACT_ENUMERATION`` and ``HASHED_INDEX_TARGETED_RETRIEVAL`` can
    support a completeness claim; the latter is the cheap path the motivating
    issue explicitly permits, and it requires a bound index/manifest hash.
    ``SAMPLED_SUBSET`` is a legitimate search that cannot support completeness.
    ``UNSPECIFIED`` fails closed: unstated coverage semantics are not coverage.
    """

    FULL_ARTIFACT_ENUMERATION = "FULL_ARTIFACT_ENUMERATION"
    HASHED_INDEX_TARGETED_RETRIEVAL = "HASHED_INDEX_TARGETED_RETRIEVAL"
    SAMPLED_SUBSET = "SAMPLED_SUBSET"
    UNSPECIFIED = "UNSPECIFIED"


#: Semantics under which a lane may back a completeness/counting claim.
_COMPLETENESS_CAPABLE_SEMANTICS = frozenset(
    {
        CoverageSemantics.FULL_ARTIFACT_ENUMERATION,
        CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL,
    }
)

#: Weakest-first ordering used only to report the weakest semantics across the
#: inspected lanes.  It is a presentation order, never a score or threshold.
_SEMANTICS_STRENGTH: Mapping[CoverageSemantics, int] = {
    CoverageSemantics.UNSPECIFIED: 0,
    CoverageSemantics.SAMPLED_SUBSET: 1,
    CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL: 2,
    CoverageSemantics.FULL_ARTIFACT_ENUMERATION: 3,
}


class LaneInspectionStatus(str, Enum):
    """A lane in the bound universe was either searched or explicitly deferred.

    There is no third value.  A lane that is neither is an uninspected lane and
    is reported as such; silence is never inspection.
    """

    INSPECTED = "INSPECTED"
    DEFERRED_DECLARED = "DEFERRED_DECLARED"


class CoverageQueryStatus(str, Enum):
    """Outcome of the cross-problem query.

    ``NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE`` is the only representable way to say
    "no match".  An unbounded narrative "no match" has no value in this type and
    cannot be encoded, which is the point of the object.
    """

    MATCHES_FOUND = "MATCHES_FOUND"
    NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE = "NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE"


class CoverageVerdict(str, Enum):
    COVERAGE_BOUND_PROPOSAL_ONLY = "COVERAGE_BOUND_PROPOSAL_ONLY"
    COVERAGE_INCOMPLETE = "COVERAGE_INCOMPLETE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


class CompletenessClaimKind(str, Enum):
    NO_OTHER_LANE_REUSED_ARTIFACT = "NO_OTHER_LANE_REUSED_ARTIFACT"
    REUSE_COUNT = "REUSE_COUNT"
    NO_RELEVANT_CROSS_PROBLEM_MEMORY = "NO_RELEVANT_CROSS_PROBLEM_MEMORY"
    LANE_STATE_ASSERTION = "LANE_STATE_ASSERTION"


#: Claim kinds whose truth requires that nothing was found anywhere in scope.
_NEGATIVE_CLAIM_KINDS = frozenset(
    {
        CompletenessClaimKind.NO_OTHER_LANE_REUSED_ARTIFACT,
        CompletenessClaimKind.NO_RELEVANT_CROSS_PROBLEM_MEMORY,
    }
)


class CompletenessClaimVerdict(str, Enum):
    """Why a completeness/counting claim is or is not licensed.

    The rejection reasons are deliberately not interchangeable:
    ``CLAIM_REJECTED_UNBOUND_UNIVERSE`` is the narrative "no match";
    ``CLAIM_REJECTED_INCOMPLETE_COVERAGE`` is a bound universe that was not fully
    searched; ``CLAIM_REFUTED_BY_BOUND_EVIDENCE`` is a claim the receipt's own
    bound evidence contradicts; ``CANNOT_CHECK`` is an unverifiable receipt.
    """

    CLAIM_BOUND_PROPOSAL_ONLY = "CLAIM_BOUND_PROPOSAL_ONLY"
    CLAIM_REJECTED_UNBOUND_UNIVERSE = "CLAIM_REJECTED_UNBOUND_UNIVERSE"
    CLAIM_REJECTED_INCOMPLETE_COVERAGE = "CLAIM_REJECTED_INCOMPLETE_COVERAGE"
    CLAIM_REFUTED_BY_BOUND_EVIDENCE = "CLAIM_REFUTED_BY_BOUND_EVIDENCE"
    CANNOT_CHECK = "CANNOT_CHECK"


def canonical_json_bytes(value: object) -> bytes:
    """Return the UTF-8 RFC-8259-compatible representation used for hashing."""

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
    """Hash a receipt document excluding its own content-hash field."""

    subject = dict(document)
    subject.pop("receipt_canonical_sha256", None)
    return canonical_json_sha256(subject)


@dataclass(frozen=True)
class RegisteredLane:
    """Current registry state for one problem/lane.

    Supplied by an independent registry observer, not read by this module.
    """

    lane_id: str
    lane_head_revision: str
    index_manifest_hash: str


@dataclass(frozen=True)
class LaneCoverageRecord:
    """What the synthesis actually did with one lane of the bound universe."""

    lane_id: str
    lane_head_revision: str
    index_manifest_hash: str
    inspection_status: LaneInspectionStatus
    coverage_semantics: CoverageSemantics = CoverageSemantics.UNSPECIFIED
    deferral_reason: str | None = None
    result_ids: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "lane_head_revision": self.lane_head_revision,
            "index_manifest_hash": self.index_manifest_hash,
            "inspection_status": self.inspection_status.value,
            "coverage_semantics": self.coverage_semantics.value,
            "deferral_reason": self.deferral_reason,
            "result_ids": list(self.result_ids),
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class CompletenessClaim:
    """A completeness or counting claim awaiting a bound coverage receipt.

    An empty ``subject_lane_ids`` means the claim ranges over the whole bound
    universe, which is the common and most dangerous case.
    """

    claim_id: str
    kind: CompletenessClaimKind
    statement: str
    asserted_count: int | None = None
    subject_lane_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CrossProblemCoverageReceipt:
    """Frozen record of the universe a cross-problem synthesis actually searched."""

    registry_repository: str
    registry_revision: str
    synthesis_id: str
    public_trace_event_id: str
    bound_lane_universe: Tuple[str, ...]
    lane_records: Tuple[LaneCoverageRecord, ...]
    query_status: CoverageQueryStatus
    claim_boundary: str
    query_terms: Tuple[str, ...] = ()
    structural_coordinates: Tuple[str, ...] = ()
    desired_effects: Tuple[str, ...] = ()
    result_ids: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "registry_repository": self.registry_repository,
            "registry_revision": self.registry_revision,
            "synthesis_id": self.synthesis_id,
            "public_trace_event_id": self.public_trace_event_id,
            "bound_lane_universe": list(self.bound_lane_universe),
            "lane_records": [record.to_dict() for record in self.lane_records],
            "query_status": self.query_status.value,
            "claim_boundary": self.claim_boundary,
            "query_terms": list(self.query_terms),
            "structural_coordinates": list(self.structural_coordinates),
            "desired_effects": list(self.desired_effects),
            "result_ids": list(self.result_ids),
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "grants_application_evidence_authority": False,
            "grants_mathematical_authority": False,
            "requires_full_artifact_enumeration": False,
        }

    def with_content_hash(self) -> "CrossProblemCoverageReceipt":
        """Return a copy carrying its own canonical content hash."""

        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )

    def record_for(self, lane_id: str) -> LaneCoverageRecord | None:
        for record in self.lane_records:
            if record.lane_id == lane_id:
                return record
        return None


@dataclass(frozen=True)
class CoverageReport:
    verdict: CoverageVerdict
    inspected_lane_ids: Tuple[str, ...]
    deferred_lane_ids: Tuple[str, ...]
    uninspected_lane_ids: Tuple[str, ...]
    stale_lane_ids: Tuple[str, ...]
    weakest_coverage_semantics: CoverageSemantics
    reasons: Tuple[str, ...]

    @property
    def universe_is_bound(self) -> bool:
        return self.verdict is not CoverageVerdict.CANNOT_CHECK

    @property
    def grants_application_evidence_authority(self) -> bool:
        return False

    @property
    def grants_mathematical_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class CompletenessClaimReport:
    verdict: CompletenessClaimVerdict
    claim_id: str
    scope_lane_ids: Tuple[str, ...]
    freshness_rechecked: bool
    reasons: Tuple[str, ...]

    @property
    def licensed(self) -> bool:
        return self.verdict is CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY


def _structural_reasons(receipt: CrossProblemCoverageReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    if not _REVISION_RE.match(receipt.registry_revision or ""):
        reasons.append("registry_revision_invalid")
    for name, value in (
        ("registry_repository", receipt.registry_repository),
        ("synthesis_id", receipt.synthesis_id),
        ("public_trace_event_id", receipt.public_trace_event_id),
        ("claim_boundary", receipt.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not receipt.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    if not (
        receipt.query_terms or receipt.structural_coordinates or receipt.desired_effects
    ):
        reasons.append("search_specification_missing")
    if not receipt.bound_lane_universe:
        reasons.append("lane_universe_unbound")
    if len(set(receipt.bound_lane_universe)) != len(receipt.bound_lane_universe):
        reasons.append("bound_lane_universe_contains_duplicates")
    seen: set[str] = set()
    for record in receipt.lane_records:
        if record.lane_id in seen:
            reasons.append("duplicate_lane_record")
            break
        seen.add(record.lane_id)
    if not receipt.receipt_canonical_sha256:
        reasons.append("receipt_canonical_sha256_missing")
    elif not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        reasons.append("receipt_canonical_sha256_malformed")
    return tuple(reasons)


def audit_memory_coverage(
    receipt: CrossProblemCoverageReceipt | None,
    *,
    registered_lane_universe: Tuple[RegisteredLane, ...],
) -> CoverageReport:
    """Bind a cross-problem search universe, failing closed on every gap.

    ``registered_lane_universe`` is the *current* registry state, supplied by an
    independent observer.  A lane that is registered but absent from the receipt's
    bound universe, and a lane that is in the bound universe but has no record at
    all, are both reported as uninspected — that second case is the exact failure
    this object exists to catch.
    """

    empty: Tuple[str, ...] = ()
    if receipt is None:
        return CoverageReport(
            CoverageVerdict.CANNOT_CHECK,
            empty,
            empty,
            empty,
            empty,
            CoverageSemantics.UNSPECIFIED,
            ("cross_problem_coverage_receipt_missing",),
        )

    structural = _structural_reasons(receipt)
    if structural:
        return CoverageReport(
            CoverageVerdict.CANNOT_CHECK,
            empty,
            empty,
            empty,
            empty,
            CoverageSemantics.UNSPECIFIED,
            structural,
        )
    if receipt.receipt_canonical_sha256 != receipt_canonical_sha256(receipt.to_dict()):
        return CoverageReport(
            CoverageVerdict.REFUTED_CLAIM,
            empty,
            empty,
            empty,
            empty,
            CoverageSemantics.UNSPECIFIED,
            ("receipt_canonical_sha256_mismatch",),
        )

    bound = tuple(receipt.bound_lane_universe)
    bound_set = set(bound)
    registered = {lane.lane_id: lane for lane in registered_lane_universe}

    inspected: list[str] = []
    deferred: list[str] = []
    uninspected: list[str] = []
    stale: list[str] = []
    reasons: list[str] = []
    unverifiable: list[str] = []

    for lane_id in sorted(registered):
        if lane_id not in bound_set:
            uninspected.append(lane_id)
            reasons.append(f"registered_lane_absent_from_bound_universe:{lane_id}")

    for record in receipt.lane_records:
        if record.lane_id not in bound_set:
            reasons.append(f"lane_record_outside_bound_universe:{record.lane_id}")

    for lane_id in bound:
        record = receipt.record_for(lane_id)
        if record is None:
            uninspected.append(lane_id)
            reasons.append(f"uninspected_lane_in_bound_universe:{lane_id}")
            continue
        if record.inspection_status is LaneInspectionStatus.DEFERRED_DECLARED:
            deferred.append(lane_id)
            if not (record.deferral_reason or "").strip():
                unverifiable.append(f"deferral_without_declared_reason:{lane_id}")
            continue
        inspected.append(lane_id)
        if record.coverage_semantics is CoverageSemantics.UNSPECIFIED:
            unverifiable.append(f"coverage_semantics_unspecified:{lane_id}")
        elif (
            record.coverage_semantics is CoverageSemantics.HASHED_INDEX_TARGETED_RETRIEVAL
            and not (record.index_manifest_hash or "").strip()
        ):
            unverifiable.append(f"index_manifest_hash_missing:{lane_id}")
        current = registered.get(lane_id)
        if current is not None and (
            current.lane_head_revision != record.lane_head_revision
            or current.index_manifest_hash != record.index_manifest_hash
        ):
            stale.append(lane_id)

    covered_results = {
        result for record in receipt.lane_records for result in record.result_ids
    }
    orphan_results = tuple(sorted(set(receipt.result_ids) - covered_results))
    if orphan_results:
        reasons.extend(
            f"result_outside_bound_universe:{result}" for result in orphan_results
        )
    if receipt.query_status is CoverageQueryStatus.MATCHES_FOUND and not receipt.result_ids:
        reasons.append("matches_found_status_without_result_ids")
    if (
        receipt.query_status is CoverageQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE
        and receipt.result_ids
    ):
        reasons.append("no_match_status_with_result_ids")

    weakest = CoverageSemantics.FULL_ARTIFACT_ENUMERATION
    for lane_id in inspected:
        record = receipt.record_for(lane_id)
        if record is None:  # pragma: no cover - inspected implies a record
            continue
        if _SEMANTICS_STRENGTH[record.coverage_semantics] < _SEMANTICS_STRENGTH[weakest]:
            weakest = record.coverage_semantics
    if not inspected:
        weakest = CoverageSemantics.UNSPECIFIED

    inspected_t = tuple(inspected)
    deferred_t = tuple(deferred)
    uninspected_t = tuple(sorted(set(uninspected)))
    stale_t = tuple(stale)

    if unverifiable:
        return CoverageReport(
            CoverageVerdict.CANNOT_CHECK,
            inspected_t,
            deferred_t,
            uninspected_t,
            stale_t,
            weakest,
            tuple(unverifiable) + tuple(reasons),
        )
    if orphan_results or any(
        reason.startswith(("lane_record_outside_bound_universe", "matches_found_status", "no_match_status"))
        for reason in reasons
    ):
        return CoverageReport(
            CoverageVerdict.REFUTED_CLAIM,
            inspected_t,
            deferred_t,
            uninspected_t,
            stale_t,
            weakest,
            tuple(reasons),
        )
    if uninspected_t:
        return CoverageReport(
            CoverageVerdict.COVERAGE_INCOMPLETE,
            inspected_t,
            deferred_t,
            uninspected_t,
            stale_t,
            weakest,
            tuple(reasons),
        )
    if stale_t:
        return CoverageReport(
            CoverageVerdict.REVALIDATION_REQUIRED,
            inspected_t,
            deferred_t,
            uninspected_t,
            stale_t,
            weakest,
            tuple(reasons)
            + tuple(f"covered_lane_state_changed_since_receipt:{lane}" for lane in stale_t),
        )
    return CoverageReport(
        CoverageVerdict.COVERAGE_BOUND_PROPOSAL_ONLY,
        inspected_t,
        deferred_t,
        uninspected_t,
        stale_t,
        weakest,
        tuple(reasons)
        + (
            "every registered lane is accounted for as inspected or explicitly deferred",
            "coverage receipt is framework-process evidence and promotes no application or mathematical authority",
        ),
    )


def revalidation_required(
    receipt: CrossProblemCoverageReceipt,
    *,
    registered_lane_universe: Tuple[RegisteredLane, ...],
) -> Tuple[str, ...]:
    """Return the lane ids whose head or index moved, or could not be re-observed."""

    registered = {lane.lane_id: lane for lane in registered_lane_universe}
    changed: list[str] = []
    for lane_id in receipt.bound_lane_universe:
        record = receipt.record_for(lane_id)
        current = registered.get(lane_id)
        if record is None or current is None:
            changed.append(lane_id)
            continue
        if (
            current.lane_head_revision != record.lane_head_revision
            or current.index_manifest_hash != record.index_manifest_hash
        ):
            changed.append(lane_id)
    for lane_id in sorted(registered):
        if lane_id not in receipt.bound_lane_universe:
            changed.append(lane_id)
    return tuple(sorted(set(changed)))


def audit_completeness_claim(
    receipt: CrossProblemCoverageReceipt | None,
    claim: CompletenessClaim,
    *,
    registered_lane_universe: Tuple[RegisteredLane, ...],
    recheck_freshness: bool = True,
) -> CompletenessClaimReport:
    """Decide whether a bound receipt licenses a completeness/counting claim.

    ``recheck_freshness=False`` evaluates the claim against the receipt exactly
    as of its own binding.  That is a legitimate offline mode, and the report says
    so via ``freshness_rechecked`` rather than implying the world was re-observed.
    """

    coverage = audit_memory_coverage(
        receipt,
        registered_lane_universe=registered_lane_universe if recheck_freshness else (),
    )
    if receipt is None or coverage.verdict is CoverageVerdict.CANNOT_CHECK:
        verdict = (
            CompletenessClaimVerdict.CLAIM_REJECTED_UNBOUND_UNIVERSE
            if "lane_universe_unbound" in coverage.reasons
            else CompletenessClaimVerdict.CANNOT_CHECK
        )
        return CompletenessClaimReport(
            verdict, claim.claim_id, (), recheck_freshness, coverage.reasons
        )
    if coverage.verdict is CoverageVerdict.REFUTED_CLAIM:
        return CompletenessClaimReport(
            CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE,
            claim.claim_id,
            (),
            recheck_freshness,
            coverage.reasons,
        )

    scope = tuple(claim.subject_lane_ids) or tuple(receipt.bound_lane_universe)
    reasons: list[str] = []

    outside = tuple(
        lane for lane in scope if lane not in set(receipt.bound_lane_universe)
    )
    if outside:
        reasons.extend(f"claim_ranges_outside_bound_universe:{lane}" for lane in outside)
    if coverage.verdict is CoverageVerdict.COVERAGE_INCOMPLETE:
        reasons.extend(
            f"claim_ranges_over_uninspected_lane:{lane}"
            for lane in coverage.uninspected_lane_ids
            if lane in scope or not claim.subject_lane_ids
        )
    if coverage.verdict is CoverageVerdict.REVALIDATION_REQUIRED:
        reasons.extend(
            f"claim_ranges_over_stale_lane:{lane}"
            for lane in coverage.stale_lane_ids
            if lane in scope
        )
    for lane in scope:
        record = receipt.record_for(lane)
        if record is None:
            continue
        if record.inspection_status is LaneInspectionStatus.DEFERRED_DECLARED:
            reasons.append(f"claim_ranges_over_deferred_lane:{lane}")
        elif record.coverage_semantics not in _COMPLETENESS_CAPABLE_SEMANTICS:
            reasons.append(f"claim_ranges_over_sampled_lane:{lane}")
    if reasons:
        return CompletenessClaimReport(
            CompletenessClaimVerdict.CLAIM_REJECTED_INCOMPLETE_COVERAGE,
            claim.claim_id,
            scope,
            recheck_freshness,
            tuple(reasons),
        )

    # Every lane in scope has an inspected record here: an unbound, uninspected,
    # deferred or sampled lane already returned above.
    in_scope_results = tuple(
        sorted(
            {
                result
                for lane in scope
                for record in (receipt.record_for(lane),)
                if record is not None
                for result in record.result_ids
            }
        )
    )

    if claim.kind in _NEGATIVE_CLAIM_KINDS:
        if in_scope_results:
            return CompletenessClaimReport(
                CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE,
                claim.claim_id,
                scope,
                recheck_freshness,
                tuple(
                    f"negative_claim_contradicted_by_bound_result:{result}"
                    for result in in_scope_results
                ),
            )
        if receipt.query_status is not CoverageQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE:
            return CompletenessClaimReport(
                CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE,
                claim.claim_id,
                scope,
                recheck_freshness,
                ("negative_claim_without_no_match_in_bound_universe_status",),
            )

    if claim.kind is CompletenessClaimKind.REUSE_COUNT:
        if claim.asserted_count is None:
            return CompletenessClaimReport(
                CompletenessClaimVerdict.CANNOT_CHECK,
                claim.claim_id,
                scope,
                recheck_freshness,
                ("reuse_count_claim_without_asserted_count",),
            )
        if claim.asserted_count != len(in_scope_results):
            return CompletenessClaimReport(
                CompletenessClaimVerdict.CLAIM_REFUTED_BY_BOUND_EVIDENCE,
                claim.claim_id,
                scope,
                recheck_freshness,
                (
                    "asserted_count_contradicts_bound_results",
                    f"asserted={claim.asserted_count}",
                    f"bound={len(in_scope_results)}",
                ),
            )

    return CompletenessClaimReport(
        CompletenessClaimVerdict.CLAIM_BOUND_PROPOSAL_ONLY,
        claim.claim_id,
        scope,
        recheck_freshness,
        (
            "claim ranges only over lanes inspected under completeness-capable semantics",
            "claim is proposal-only telemetry and promotes no application or mathematical authority",
        ),
    )
