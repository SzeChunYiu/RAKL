"""Fibre-time memory-reference resolution receipt.

Case-study metrology exposed a referential-integrity gap: a frozen fibre or
current-work pointer can name an experience ID while the canonical payload is
absent from the exact approved application state. Safe behavior is to fail
closed and treat the pointer as non-authoritative. Without a typed receipt,
metrology cannot cleanly distinguish ``retrieved and rejected`` from
``referenced but unresolved``.

This module emits an immutable, content-hashed
:class:`MemoryReferenceResolutionReceipt` bound to the exact fibre snapshot,
framework SHA, and application-state/base SHA. For each requested memory ID it
records a closed resolution status, optional payload hash/source pointer,
authority eligibility, retrieval timestamp, and transfer/DifferenceWitness
status when a transfer is attempted.

Fail-closed invariants (machine-checked here):

* Only ``CANONICAL_RESOLVED`` with ``CANONICAL_ELIGIBLE`` may satisfy a
  canonical-memory consumer/gate.
* ``PROPOSAL_SHADOW_RESOLVED`` and ``OPEN_CURRENT_WORK`` may guide search only.
* ``MISSING_AT_SUBJECT`` and ``AMBIGUOUS`` never silently inherit payload or
  authority from issue, PR, or prose mentions.
* Counts for selected / rejected / unresolved are reported separately.

Scope: framework metrology only. No application-domain mathematical evidence or
theorem authority. Performs no network access, no git access, and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Tuple

RECEIPT_SCHEMA_VERSION = "memory-reference-resolution-receipt-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OR_SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")

CLAIM_BOUNDARY_DEFAULT = (
    "framework-process metrology only; binds memory-reference resolution at an "
    "exact fibre/application-state snapshot and promotes no application "
    "evidence or mathematical authority"
)


class MemoryResolutionStatus(str, Enum):
    """Closed resolution outcomes for one requested memory ID."""

    CANONICAL_RESOLVED = "CANONICAL_RESOLVED"
    PROPOSAL_SHADOW_RESOLVED = "PROPOSAL_SHADOW_RESOLVED"
    OPEN_CURRENT_WORK = "OPEN_CURRENT_WORK"
    MISSING_AT_SUBJECT = "MISSING_AT_SUBJECT"
    AMBIGUOUS = "AMBIGUOUS"


class AuthorityEligibility(str, Enum):
    """Whether a resolved reference may satisfy a canonical-memory consumer."""

    CANONICAL_ELIGIBLE = "CANONICAL_ELIGIBLE"
    SEARCH_GUIDANCE_ONLY = "SEARCH_GUIDANCE_ONLY"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class TransferApplicabilityStatus(str, Enum):
    """Transfer attempt status relative to an optional DifferenceWitness."""

    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    DIFFERENCE_WITNESS_BOUND = "DIFFERENCE_WITNESS_BOUND"
    TRANSFER_REJECTED = "TRANSFER_REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class CanonicalMemoryConsumer(str, Enum):
    """Consumers that may only accept CANONICAL_RESOLVED references."""

    CANONICAL_MEMORY_GATE = "CANONICAL_MEMORY_GATE"
    PROTECTED_EXPERIENCE_CONSUMER = "PROTECTED_EXPERIENCE_CONSUMER"
    AUTHORITY_COUNT_DENOMINATOR = "AUTHORITY_COUNT_DENOMINATOR"


class ResolutionAuditVerdict(str, Enum):
    CANONICAL_CONSUMER_SATISFIED = "CANONICAL_CONSUMER_SATISFIED"
    SEARCH_GUIDANCE_ONLY = "SEARCH_GUIDANCE_ONLY"
    UNRESOLVED_FAIL_CLOSED = "UNRESOLVED_FAIL_CLOSED"
    PROTECTED_CONSUMER_REJECTED = "PROTECTED_CONSUMER_REJECTED"
    RECEIPT_UNVERIFIABLE = "RECEIPT_UNVERIFIABLE"
    PROSE_MENTION_REJECTED = "PROSE_MENTION_REJECTED"


_SEARCH_ONLY_STATUSES = frozenset(
    {
        MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED,
        MemoryResolutionStatus.OPEN_CURRENT_WORK,
    }
)

_UNRESOLVED_STATUSES = frozenset(
    {
        MemoryResolutionStatus.MISSING_AT_SUBJECT,
        MemoryResolutionStatus.AMBIGUOUS,
    }
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_RE.match(value):
        raise ValueError(f"{field_name} must be sha256 hex")


def _require_subject_sha(value: str, field_name: str) -> None:
    if not _GIT_OR_SHA_RE.match(value):
        raise ValueError(f"{field_name} must be a 40-char git OID or 64-char sha256 hex")


def _require_utc(value: str, field_name: str) -> None:
    if not _ISO_UTC_RE.match(value):
        raise ValueError(f"{field_name} must be ISO-8601 UTC ending in 'Z'")


@dataclass(frozen=True)
class MemoryReferenceRecord:
    """One requested memory ID resolved against the bound application state."""

    memory_id: str
    resolution_status: MemoryResolutionStatus
    resolved_payload_hash: str | None
    source_pointer: str | None
    authority_eligibility: AuthorityEligibility
    retrieved_at_utc: str
    transfer_applicability_status: TransferApplicabilityStatus = (
        TransferApplicabilityStatus.NOT_ATTEMPTED
    )
    difference_witness_pointer: str | None = None
    prose_mention_sources: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.memory_id:
            raise ValueError("memory reference requires memory_id")
        _require_utc(self.retrieved_at_utc, "retrieved_at_utc")
        if self.resolved_payload_hash is not None:
            _require_sha256(self.resolved_payload_hash, "resolved_payload_hash")

        status = self.resolution_status
        eligibility = self.authority_eligibility

        if status is MemoryResolutionStatus.CANONICAL_RESOLVED:
            if self.resolved_payload_hash is None:
                raise ValueError("CANONICAL_RESOLVED requires resolved_payload_hash")
            if not self.source_pointer:
                raise ValueError("CANONICAL_RESOLVED requires source_pointer")
            if eligibility is not AuthorityEligibility.CANONICAL_ELIGIBLE:
                raise ValueError(
                    "CANONICAL_RESOLVED requires authority_eligibility=CANONICAL_ELIGIBLE"
                )
        elif status in _SEARCH_ONLY_STATUSES:
            if eligibility is not AuthorityEligibility.SEARCH_GUIDANCE_ONLY:
                raise ValueError(
                    f"{status.value} requires authority_eligibility=SEARCH_GUIDANCE_ONLY"
                )
            if status is MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED:
                if self.resolved_payload_hash is None:
                    raise ValueError(
                        "PROPOSAL_SHADOW_RESOLVED requires resolved_payload_hash"
                    )
        elif status in _UNRESOLVED_STATUSES:
            if eligibility is not AuthorityEligibility.NOT_ELIGIBLE:
                raise ValueError(
                    f"{status.value} requires authority_eligibility=NOT_ELIGIBLE"
                )
            if self.resolved_payload_hash is not None:
                raise ValueError(
                    f"{status.value} must not carry resolved_payload_hash "
                    "(no silent inheritance from prose/issue/PR mentions)"
                )

        if (
            self.transfer_applicability_status
            is TransferApplicabilityStatus.DIFFERENCE_WITNESS_BOUND
            and not self.difference_witness_pointer
        ):
            raise ValueError(
                "DIFFERENCE_WITNESS_BOUND requires difference_witness_pointer"
            )
        if (
            self.transfer_applicability_status
            is TransferApplicabilityStatus.NOT_ATTEMPTED
            and self.difference_witness_pointer
        ):
            raise ValueError(
                "difference_witness_pointer forbidden when transfer NOT_ATTEMPTED"
            )

    def content(self) -> Mapping[str, Any]:
        return {
            "memory_id": self.memory_id,
            "resolution_status": self.resolution_status.value,
            "resolved_payload_hash": self.resolved_payload_hash,
            "source_pointer": self.source_pointer,
            "authority_eligibility": self.authority_eligibility.value,
            "retrieved_at_utc": self.retrieved_at_utc,
            "transfer_applicability_status": self.transfer_applicability_status.value,
            "difference_witness_pointer": self.difference_witness_pointer,
            "prose_mention_sources": list(self.prose_mention_sources),
        }

    @property
    def is_canonical(self) -> bool:
        return (
            self.resolution_status is MemoryResolutionStatus.CANONICAL_RESOLVED
            and self.authority_eligibility is AuthorityEligibility.CANONICAL_ELIGIBLE
        )

    @property
    def is_unresolved(self) -> bool:
        return self.resolution_status in _UNRESOLVED_STATUSES

    @property
    def is_search_guidance_only(self) -> bool:
        return self.resolution_status in _SEARCH_ONLY_STATUSES


@dataclass(frozen=True)
class MemoryReferenceResolutionReceipt:
    """Fibre-time binding of requested memory IDs to closed resolution outcomes."""

    receipt_id: str
    fibre_snapshot_hash: str
    framework_sha: str
    application_state_sha: str
    requested_memory_ids: Tuple[str, ...]
    resolutions: Tuple[MemoryReferenceRecord, ...]
    claim_boundary: str = CLAIM_BOUNDARY_DEFAULT
    schema_version: str = RECEIPT_SCHEMA_VERSION
    grants_application_evidence_authority: bool = False
    grants_mathematical_authority: bool = False

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise ValueError("receipt requires receipt_id")
        _require_sha256(self.fibre_snapshot_hash, "fibre_snapshot_hash")
        _require_subject_sha(self.framework_sha, "framework_sha")
        _require_subject_sha(self.application_state_sha, "application_state_sha")
        if not self.requested_memory_ids:
            raise ValueError("receipt requires at least one requested_memory_id")
        if len(set(self.requested_memory_ids)) != len(self.requested_memory_ids):
            raise ValueError("requested_memory_ids must be unique")
        if not self.resolutions:
            raise ValueError("receipt requires at least one resolution record")
        if not self.claim_boundary:
            raise ValueError("receipt requires claim_boundary")
        if self.grants_application_evidence_authority:
            raise ValueError("grants_application_evidence_authority must be false")
        if self.grants_mathematical_authority:
            raise ValueError("grants_mathematical_authority must be false")

        by_id = {record.memory_id: record for record in self.resolutions}
        if len(by_id) != len(self.resolutions):
            raise ValueError("resolution records must be unique by memory_id")
        missing = [mid for mid in self.requested_memory_ids if mid not in by_id]
        if missing:
            raise ValueError(
                f"requested memory ids lack resolution records: {missing}"
            )
        extras = [mid for mid in by_id if mid not in set(self.requested_memory_ids)]
        if extras:
            raise ValueError(
                f"resolution records for unrequested memory ids: {extras}"
            )

    def derived_counts(self) -> Tuple[int, int, int]:
        """Return ``(selected_count, rejected_count, unresolved_count)``."""

        selected = sum(1 for record in self.resolutions if record.is_canonical)
        rejected = sum(1 for record in self.resolutions if record.is_search_guidance_only)
        unresolved = sum(1 for record in self.resolutions if record.is_unresolved)
        return selected, rejected, unresolved

    def content(self) -> Mapping[str, Any]:
        selected, rejected, unresolved = self.derived_counts()
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "fibre_snapshot_hash": self.fibre_snapshot_hash,
            "framework_sha": self.framework_sha,
            "application_state_sha": self.application_state_sha,
            "requested_memory_ids": list(self.requested_memory_ids),
            "resolutions": [record.content() for record in self.resolutions],
            "selected_count": selected,
            "rejected_count": rejected,
            "unresolved_count": unresolved,
            "claim_boundary": self.claim_boundary,
            "grants_application_evidence_authority": False,
            "grants_mathematical_authority": False,
        }

    @property
    def receipt_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        document = dict(self.content())
        document["receipt_canonical_sha256"] = self.receipt_canonical_sha256
        return document

    def record_for(self, memory_id: str) -> MemoryReferenceRecord | None:
        for record in self.resolutions:
            if record.memory_id == memory_id:
                return record
        return None


@dataclass(frozen=True)
class MemoryReferenceAuditReport:
    """Audit outcome for one memory ID against a fibre-time receipt."""

    memory_id: str
    receipt_id: str | None
    verdict: ResolutionAuditVerdict
    reasons: Tuple[str, ...]
    resolution_status: MemoryResolutionStatus | None
    authority_eligibility: AuthorityEligibility | None
    satisfies_canonical_memory_consumer: bool
    retained_for_search_guidance: bool
    prose_mentions_ignored_for_authority: bool

    @property
    def fail_closed(self) -> bool:
        return self.verdict in {
            ResolutionAuditVerdict.UNRESOLVED_FAIL_CLOSED,
            ResolutionAuditVerdict.PROTECTED_CONSUMER_REJECTED,
            ResolutionAuditVerdict.RECEIPT_UNVERIFIABLE,
            ResolutionAuditVerdict.PROSE_MENTION_REJECTED,
        }


@dataclass(frozen=True)
class SubjectMemoryEntry:
    """One memory payload observed at the bound application-state subject."""

    memory_id: str
    payload_hash: str
    source_pointer: str
    storage_class: MemoryResolutionStatus

    def __post_init__(self) -> None:
        if not self.memory_id:
            raise ValueError("subject entry requires memory_id")
        _require_sha256(self.payload_hash, "payload_hash")
        if not self.source_pointer:
            raise ValueError("subject entry requires source_pointer")
        if self.storage_class not in {
            MemoryResolutionStatus.CANONICAL_RESOLVED,
            MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED,
            MemoryResolutionStatus.OPEN_CURRENT_WORK,
        }:
            raise ValueError(
                "subject storage_class must be CANONICAL_RESOLVED, "
                "PROPOSAL_SHADOW_RESOLVED, or OPEN_CURRENT_WORK"
            )


def resolve_memory_references(
    *,
    receipt_id: str,
    fibre_snapshot_hash: str,
    framework_sha: str,
    application_state_sha: str,
    requested_memory_ids: Iterable[str],
    subject_entries: Iterable[SubjectMemoryEntry],
    retrieved_at_utc: str,
    prose_mentions_by_id: Mapping[str, Tuple[str, ...]] | None = None,
    claim_boundary: str = CLAIM_BOUNDARY_DEFAULT,
) -> MemoryReferenceResolutionReceipt:
    """Build a fibre-time resolution receipt from an exact subject inventory.

    Prose/issue/PR mentions may be recorded on unresolved rows for audit, but
    never mint a payload hash or authority eligibility.
    """

    requested = tuple(requested_memory_ids)
    mentions = prose_mentions_by_id or {}
    by_id: dict[str, list[SubjectMemoryEntry]] = {}
    for entry in subject_entries:
        by_id.setdefault(entry.memory_id, []).append(entry)

    resolutions: list[MemoryReferenceRecord] = []
    for memory_id in requested:
        mention_sources = tuple(mentions.get(memory_id, ()))
        entries = by_id.get(memory_id, [])
        if not entries:
            resolutions.append(
                MemoryReferenceRecord(
                    memory_id=memory_id,
                    resolution_status=MemoryResolutionStatus.MISSING_AT_SUBJECT,
                    resolved_payload_hash=None,
                    source_pointer=None,
                    authority_eligibility=AuthorityEligibility.NOT_ELIGIBLE,
                    retrieved_at_utc=retrieved_at_utc,
                    prose_mention_sources=mention_sources,
                )
            )
            continue

        distinct_payloads = {entry.payload_hash for entry in entries}
        canonical_entries = [
            e
            for e in entries
            if e.storage_class is MemoryResolutionStatus.CANONICAL_RESOLVED
        ]
        if len(distinct_payloads) > 1 or len(canonical_entries) > 1:
            resolutions.append(
                MemoryReferenceRecord(
                    memory_id=memory_id,
                    resolution_status=MemoryResolutionStatus.AMBIGUOUS,
                    resolved_payload_hash=None,
                    source_pointer=None,
                    authority_eligibility=AuthorityEligibility.NOT_ELIGIBLE,
                    retrieved_at_utc=retrieved_at_utc,
                    prose_mention_sources=mention_sources,
                )
            )
            continue

        chosen = canonical_entries[0] if canonical_entries else entries[0]
        if chosen.storage_class is MemoryResolutionStatus.CANONICAL_RESOLVED:
            resolutions.append(
                MemoryReferenceRecord(
                    memory_id=memory_id,
                    resolution_status=MemoryResolutionStatus.CANONICAL_RESOLVED,
                    resolved_payload_hash=chosen.payload_hash,
                    source_pointer=chosen.source_pointer,
                    authority_eligibility=AuthorityEligibility.CANONICAL_ELIGIBLE,
                    retrieved_at_utc=retrieved_at_utc,
                    prose_mention_sources=mention_sources,
                )
            )
        elif chosen.storage_class is MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED:
            resolutions.append(
                MemoryReferenceRecord(
                    memory_id=memory_id,
                    resolution_status=MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED,
                    resolved_payload_hash=chosen.payload_hash,
                    source_pointer=chosen.source_pointer,
                    authority_eligibility=AuthorityEligibility.SEARCH_GUIDANCE_ONLY,
                    retrieved_at_utc=retrieved_at_utc,
                    prose_mention_sources=mention_sources,
                )
            )
        else:
            resolutions.append(
                MemoryReferenceRecord(
                    memory_id=memory_id,
                    resolution_status=MemoryResolutionStatus.OPEN_CURRENT_WORK,
                    resolved_payload_hash=chosen.payload_hash,
                    source_pointer=chosen.source_pointer,
                    authority_eligibility=AuthorityEligibility.SEARCH_GUIDANCE_ONLY,
                    retrieved_at_utc=retrieved_at_utc,
                    prose_mention_sources=mention_sources,
                )
            )

    return MemoryReferenceResolutionReceipt(
        receipt_id=receipt_id,
        fibre_snapshot_hash=fibre_snapshot_hash,
        framework_sha=framework_sha,
        application_state_sha=application_state_sha,
        requested_memory_ids=requested,
        resolutions=tuple(resolutions),
        claim_boundary=claim_boundary,
    )


def audit_memory_reference(
    receipt: MemoryReferenceResolutionReceipt | None,
    memory_id: str,
    *,
    expected_fibre_snapshot_hash: str | None = None,
    expected_framework_sha: str | None = None,
    expected_application_state_sha: str | None = None,
    protected_consumer: CanonicalMemoryConsumer | None = None,
    allow_prose_mention_authority: bool = False,
) -> MemoryReferenceAuditReport:
    """Audit one memory ID against a fibre-time resolution receipt.

    ``allow_prose_mention_authority`` is accepted only so callers can prove the
    hostile path is rejected: prose/issue/PR mentions never mint authority.
    """

    if allow_prose_mention_authority:
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=None if receipt is None else receipt.receipt_id,
            verdict=ResolutionAuditVerdict.PROSE_MENTION_REJECTED,
            reasons=(
                "prose_issue_or_pr_mention_cannot_mint_memory_authority",
                "fail_closed_no_silent_payload_inheritance",
            ),
            resolution_status=None,
            authority_eligibility=None,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=False,
            prose_mentions_ignored_for_authority=True,
        )

    if receipt is None:
        reasons = ("memory_reference_resolution_receipt_missing",)
        verdict = (
            ResolutionAuditVerdict.PROTECTED_CONSUMER_REJECTED
            if protected_consumer is not None
            else ResolutionAuditVerdict.RECEIPT_UNVERIFIABLE
        )
        if protected_consumer is not None:
            reasons = reasons + (f"protected_consumer={protected_consumer.value}",)
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=None,
            verdict=verdict,
            reasons=reasons,
            resolution_status=None,
            authority_eligibility=None,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=False,
            prose_mentions_ignored_for_authority=True,
        )

    bind_reasons: list[str] = []
    if (
        expected_fibre_snapshot_hash is not None
        and expected_fibre_snapshot_hash != receipt.fibre_snapshot_hash
    ):
        bind_reasons.append("fibre_snapshot_hash_mismatch")
    if (
        expected_framework_sha is not None
        and expected_framework_sha != receipt.framework_sha
    ):
        bind_reasons.append("framework_sha_mismatch")
    if (
        expected_application_state_sha is not None
        and expected_application_state_sha != receipt.application_state_sha
    ):
        bind_reasons.append("application_state_sha_mismatch")
    _ = receipt.receipt_canonical_sha256
    if bind_reasons:
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=receipt.receipt_id,
            verdict=ResolutionAuditVerdict.RECEIPT_UNVERIFIABLE,
            reasons=tuple(bind_reasons),
            resolution_status=None,
            authority_eligibility=None,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=False,
            prose_mentions_ignored_for_authority=True,
        )

    record = receipt.record_for(memory_id)
    if record is None:
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=receipt.receipt_id,
            verdict=ResolutionAuditVerdict.UNRESOLVED_FAIL_CLOSED,
            reasons=("memory_id_absent_from_receipt",),
            resolution_status=None,
            authority_eligibility=None,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=False,
            prose_mentions_ignored_for_authority=True,
        )

    if record.is_unresolved:
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=receipt.receipt_id,
            verdict=ResolutionAuditVerdict.UNRESOLVED_FAIL_CLOSED,
            reasons=(
                f"resolution_status={record.resolution_status.value}",
                "referenced_but_unresolved",
                "prose_mentions_do_not_supply_payload",
            ),
            resolution_status=record.resolution_status,
            authority_eligibility=record.authority_eligibility,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=False,
            prose_mentions_ignored_for_authority=True,
        )

    if record.is_search_guidance_only:
        if protected_consumer is not None:
            return MemoryReferenceAuditReport(
                memory_id=memory_id,
                receipt_id=receipt.receipt_id,
                verdict=ResolutionAuditVerdict.PROTECTED_CONSUMER_REJECTED,
                reasons=(
                    "retrieved_and_rejected_for_canonical_authority",
                    f"resolution_status={record.resolution_status.value}",
                    f"protected_consumer={protected_consumer.value}",
                ),
                resolution_status=record.resolution_status,
                authority_eligibility=record.authority_eligibility,
                satisfies_canonical_memory_consumer=False,
                retained_for_search_guidance=True,
                prose_mentions_ignored_for_authority=True,
            )
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=receipt.receipt_id,
            verdict=ResolutionAuditVerdict.SEARCH_GUIDANCE_ONLY,
            reasons=(
                "retrieved_and_rejected_for_canonical_authority",
                f"resolution_status={record.resolution_status.value}",
            ),
            resolution_status=record.resolution_status,
            authority_eligibility=record.authority_eligibility,
            satisfies_canonical_memory_consumer=False,
            retained_for_search_guidance=True,
            prose_mentions_ignored_for_authority=True,
        )

    if protected_consumer is None:
        return MemoryReferenceAuditReport(
            memory_id=memory_id,
            receipt_id=receipt.receipt_id,
            verdict=ResolutionAuditVerdict.CANONICAL_CONSUMER_SATISFIED,
            reasons=("canonical_resolved_and_eligible",),
            resolution_status=record.resolution_status,
            authority_eligibility=record.authority_eligibility,
            satisfies_canonical_memory_consumer=True,
            retained_for_search_guidance=True,
            prose_mentions_ignored_for_authority=True,
        )

    return MemoryReferenceAuditReport(
        memory_id=memory_id,
        receipt_id=receipt.receipt_id,
        verdict=ResolutionAuditVerdict.CANONICAL_CONSUMER_SATISFIED,
        reasons=(
            "canonical_resolved_and_eligible",
            f"protected_consumer={protected_consumer.value}",
        ),
        resolution_status=record.resolution_status,
        authority_eligibility=record.authority_eligibility,
        satisfies_canonical_memory_consumer=True,
        retained_for_search_guidance=True,
        prose_mentions_ignored_for_authority=True,
    )


def count_canonical_memory_references(
    receipt: MemoryReferenceResolutionReceipt,
) -> int:
    """Count references that may enter a bounded canonical-memory denominator."""

    return sum(1 for record in receipt.resolutions if record.is_canonical)
