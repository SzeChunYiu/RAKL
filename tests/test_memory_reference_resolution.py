"""Hostile-world tests for fibre-time memory-reference resolution receipts.

Fixtures are synthetic memory IDs and payload hashes only. No problem-specific
mathematics is imported into framework authority.

Motivating failure (planted): a fibre names ``exp-missing`` while the approved
application state has no payload for it, and an issue/PR prose mention also
names the ID. Resolution must be ``MISSING_AT_SUBJECT``; the prose mention must
not mint payload or authority; selected/rejected/unresolved counts stay
separate from ``retrieved and rejected`` shadow rows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from rakl.memory_reference_resolution import (
    AuthorityEligibility,
    CanonicalMemoryConsumer,
    MemoryReferenceRecord,
    MemoryReferenceResolutionReceipt,
    MemoryResolutionStatus,
    ResolutionAuditVerdict,
    SubjectMemoryEntry,
    TransferApplicabilityStatus,
    audit_memory_reference,
    count_canonical_memory_references,
    resolve_memory_references,
)

FIBRE = "a" * 64
FRAMEWORK = "b" * 40
APP_STATE = "c" * 40
PAYLOAD_A = "1" * 64
PAYLOAD_B = "2" * 64
PAYLOAD_SHADOW = "3" * 64
RETRIEVED_AT = "2026-08-12T04:00:00Z"


def _canonical(memory_id: str, payload: str = PAYLOAD_A) -> SubjectMemoryEntry:
    return SubjectMemoryEntry(
        memory_id=memory_id,
        payload_hash=payload,
        source_pointer=f"canonical::{memory_id}",
        storage_class=MemoryResolutionStatus.CANONICAL_RESOLVED,
    )


def _shadow(memory_id: str, payload: str = PAYLOAD_SHADOW) -> SubjectMemoryEntry:
    return SubjectMemoryEntry(
        memory_id=memory_id,
        payload_hash=payload,
        source_pointer=f"shadow::{memory_id}",
        storage_class=MemoryResolutionStatus.PROPOSAL_SHADOW_RESOLVED,
    )


def _open_work(memory_id: str, payload: str = PAYLOAD_B) -> SubjectMemoryEntry:
    return SubjectMemoryEntry(
        memory_id=memory_id,
        payload_hash=payload,
        source_pointer=f"current-work::{memory_id}",
        storage_class=MemoryResolutionStatus.OPEN_CURRENT_WORK,
    )


def _receipt(**overrides: Any) -> MemoryReferenceResolutionReceipt:
    values: dict[str, Any] = {
        "receipt_id": "mrr::fibre-0001",
        "fibre_snapshot_hash": FIBRE,
        "framework_sha": FRAMEWORK,
        "application_state_sha": APP_STATE,
        "requested_memory_ids": ("exp-a", "exp-shadow", "exp-missing"),
        "subject_entries": (
            _canonical("exp-a"),
            _shadow("exp-shadow"),
        ),
        "retrieved_at_utc": RETRIEVED_AT,
        "prose_mentions_by_id": {
            "exp-missing": ("issue:#351", "pr:#999"),
        },
    }
    values.update(overrides)
    return resolve_memory_references(**values)


def test_canonical_and_shadow_and_missing_counts_are_separate() -> None:
    receipt = _receipt()
    selected, rejected, unresolved = receipt.derived_counts()
    assert selected == 1
    assert rejected == 1
    assert unresolved == 1
    assert receipt.document()["selected_count"] == 1
    assert receipt.document()["rejected_count"] == 1
    assert receipt.document()["unresolved_count"] == 1
    assert count_canonical_memory_references(receipt) == 1


def test_canonical_consumer_accepts_only_canonical_resolved() -> None:
    receipt = _receipt()
    ok = audit_memory_reference(
        receipt,
        "exp-a",
        expected_fibre_snapshot_hash=FIBRE,
        expected_framework_sha=FRAMEWORK,
        expected_application_state_sha=APP_STATE,
        protected_consumer=CanonicalMemoryConsumer.CANONICAL_MEMORY_GATE,
    )
    assert ok.verdict is ResolutionAuditVerdict.CANONICAL_CONSUMER_SATISFIED
    assert ok.satisfies_canonical_memory_consumer is True

    shadow = audit_memory_reference(
        receipt,
        "exp-shadow",
        protected_consumer=CanonicalMemoryConsumer.CANONICAL_MEMORY_GATE,
    )
    assert shadow.verdict is ResolutionAuditVerdict.PROTECTED_CONSUMER_REJECTED
    assert shadow.retained_for_search_guidance is True
    assert "retrieved_and_rejected_for_canonical_authority" in shadow.reasons


def test_missing_at_subject_is_unresolved_not_retrieved_and_rejected() -> None:
    receipt = _receipt()
    record = receipt.record_for("exp-missing")
    assert record is not None
    assert record.resolution_status is MemoryResolutionStatus.MISSING_AT_SUBJECT
    assert record.resolved_payload_hash is None
    assert record.prose_mention_sources == ("issue:#351", "pr:#999")

    report = audit_memory_reference(
        receipt,
        "exp-missing",
        protected_consumer=CanonicalMemoryConsumer.PROTECTED_EXPERIENCE_CONSUMER,
    )
    assert report.verdict is ResolutionAuditVerdict.UNRESOLVED_FAIL_CLOSED
    assert "referenced_but_unresolved" in report.reasons
    assert report.satisfies_canonical_memory_consumer is False


def test_prose_mention_cannot_mint_authority_even_when_caller_asks() -> None:
    receipt = _receipt()
    report = audit_memory_reference(
        receipt,
        "exp-missing",
        allow_prose_mention_authority=True,
    )
    assert report.verdict is ResolutionAuditVerdict.PROSE_MENTION_REJECTED
    assert report.prose_mentions_ignored_for_authority is True
    assert report.satisfies_canonical_memory_consumer is False


def test_ambiguous_distinct_payloads_fail_closed_without_inherited_hash() -> None:
    receipt = resolve_memory_references(
        receipt_id="mrr::ambig",
        fibre_snapshot_hash=FIBRE,
        framework_sha=FRAMEWORK,
        application_state_sha=APP_STATE,
        requested_memory_ids=("exp-dup",),
        subject_entries=(
            _canonical("exp-dup", PAYLOAD_A),
            _canonical("exp-dup", PAYLOAD_B),
        ),
        retrieved_at_utc=RETRIEVED_AT,
        prose_mentions_by_id={"exp-dup": ("issue:#1",)},
    )
    record = receipt.record_for("exp-dup")
    assert record is not None
    assert record.resolution_status is MemoryResolutionStatus.AMBIGUOUS
    assert record.resolved_payload_hash is None
    assert receipt.derived_counts() == (0, 0, 1)


def test_open_current_work_is_search_guidance_only() -> None:
    receipt = resolve_memory_references(
        receipt_id="mrr::open",
        fibre_snapshot_hash=FIBRE,
        framework_sha=FRAMEWORK,
        application_state_sha=APP_STATE,
        requested_memory_ids=("exp-open",),
        subject_entries=(_open_work("exp-open"),),
        retrieved_at_utc=RETRIEVED_AT,
    )
    record = receipt.record_for("exp-open")
    assert record is not None
    assert record.resolution_status is MemoryResolutionStatus.OPEN_CURRENT_WORK
    assert record.authority_eligibility is AuthorityEligibility.SEARCH_GUIDANCE_ONLY
    report = audit_memory_reference(receipt, "exp-open")
    assert report.verdict is ResolutionAuditVerdict.SEARCH_GUIDANCE_ONLY


def test_fibre_or_state_mismatch_makes_receipt_unverifiable() -> None:
    receipt = _receipt()
    report = audit_memory_reference(
        receipt,
        "exp-a",
        expected_fibre_snapshot_hash="d" * 64,
    )
    assert report.verdict is ResolutionAuditVerdict.RECEIPT_UNVERIFIABLE
    assert "fibre_snapshot_hash_mismatch" in report.reasons


def test_missing_receipt_rejects_protected_consumer() -> None:
    report = audit_memory_reference(
        None,
        "exp-a",
        protected_consumer=CanonicalMemoryConsumer.AUTHORITY_COUNT_DENOMINATOR,
    )
    assert report.verdict is ResolutionAuditVerdict.PROTECTED_CONSUMER_REJECTED
    assert report.fail_closed is True


def test_canonical_requires_payload_and_source() -> None:
    with pytest.raises(ValueError, match="resolved_payload_hash"):
        MemoryReferenceRecord(
            memory_id="exp-a",
            resolution_status=MemoryResolutionStatus.CANONICAL_RESOLVED,
            resolved_payload_hash=None,
            source_pointer="canonical::exp-a",
            authority_eligibility=AuthorityEligibility.CANONICAL_ELIGIBLE,
            retrieved_at_utc=RETRIEVED_AT,
        )


def test_missing_must_not_carry_payload_hash() -> None:
    with pytest.raises(ValueError, match="must not carry resolved_payload_hash"):
        MemoryReferenceRecord(
            memory_id="exp-missing",
            resolution_status=MemoryResolutionStatus.MISSING_AT_SUBJECT,
            resolved_payload_hash=PAYLOAD_A,
            source_pointer=None,
            authority_eligibility=AuthorityEligibility.NOT_ELIGIBLE,
            retrieved_at_utc=RETRIEVED_AT,
        )


def test_difference_witness_required_when_transfer_bound() -> None:
    with pytest.raises(ValueError, match="difference_witness_pointer"):
        MemoryReferenceRecord(
            memory_id="exp-a",
            resolution_status=MemoryResolutionStatus.CANONICAL_RESOLVED,
            resolved_payload_hash=PAYLOAD_A,
            source_pointer="canonical::exp-a",
            authority_eligibility=AuthorityEligibility.CANONICAL_ELIGIBLE,
            retrieved_at_utc=RETRIEVED_AT,
            transfer_applicability_status=TransferApplicabilityStatus.DIFFERENCE_WITNESS_BOUND,
        )


def test_document_matches_schema() -> None:
    receipt = _receipt()
    schema = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "schemas/memory-reference-resolution-receipt-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(receipt.document())


def test_authority_flags_cannot_be_true() -> None:
    with pytest.raises(ValueError, match="grants_mathematical_authority"):
        MemoryReferenceResolutionReceipt(
            receipt_id="mrr::bad",
            fibre_snapshot_hash=FIBRE,
            framework_sha=FRAMEWORK,
            application_state_sha=APP_STATE,
            requested_memory_ids=("exp-a",),
            resolutions=(
                MemoryReferenceRecord(
                    memory_id="exp-a",
                    resolution_status=MemoryResolutionStatus.CANONICAL_RESOLVED,
                    resolved_payload_hash=PAYLOAD_A,
                    source_pointer="canonical::exp-a",
                    authority_eligibility=AuthorityEligibility.CANONICAL_ELIGIBLE,
                    retrieved_at_utc=RETRIEVED_AT,
                ),
            ),
            grants_mathematical_authority=True,
        )
