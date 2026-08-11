"""Proposal-only TaskEpisode storage / inventory-admission separation.

A content-valid :class:`~rakl.experience_substrate.TaskEpisode` can be retained
for search and failure learning without being admitted into a canonical episode
inventory that protected discovery, promotion, lesson/tool, proof or root gates
may count. Application compatibility layers that infer that distinction from
path, file extension or the presence of a top-level ``episode_id`` repeatedly
collide valid proposal/shadow objects with exhaustive inventory governance.

This module emits an explicit, content-bound admission receipt and derives
whether a given consumer may treat the episode as canonical. Storage status is
never inferred from representation tricks: it is declared inside a hashed
receipt that binds the exact episode identity.

Scope, stated as narrowly as the artifact supports:

* **Not wired into any runtime path.** ``record_task_episode``, ledger discovery
  and application inventory gates are unchanged. Automatic enforcement remains a
  separate, separately reviewable change.
* **No path/name authority.** Renaming a file extension or omitting
  ``episode_id`` cannot satisfy canonical admission here; only a verified
  ``CANONICAL_INVENTORY_ADMITTED`` receipt can.
* **No authority minting.** Emits no proof, lesson, tool, gluing, theorem,
  review-independence or framework authority. ``grants_*`` fields are literal
  ``false`` and schema-pinned.
* Shadow episodes remain fully usable for search priority and failure learning.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Mapping, Tuple

from .experience_substrate import TaskEpisode, validate_episode

RECEIPT_SCHEMA_VERSION = "episode-inventory-admission-receipt-v1"

#: Prefix used to reference an admission receipt from an episode's evidence
#: pointers. The episode dataclass is deliberately not modified: binding travels
#: as data.
EPISODE_ADMISSION_POINTER_PREFIX = "episode_inventory_admission:"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EpisodeStorageStatus(str, Enum):
    """Content-bound storage / admission intent for one TaskEpisode.

    ``PROPOSAL_SHADOW_STORED``
        may be retained and retrieved for search/failure learning; must not
        satisfy canonical inventory, promotion, lesson/tool, proof or root gates.
    ``CANONICAL_INVENTORY_ADMITTED``
        requires an explicit protected admission attestation id inside the
        receipt; is exhaustively discoverable under identity/hash/provenance
        checks once verified.
    """

    PROPOSAL_SHADOW_STORED = "PROPOSAL_SHADOW_STORED"
    CANONICAL_INVENTORY_ADMITTED = "CANONICAL_INVENTORY_ADMITTED"


class ProtectedConsumerKind(str, Enum):
    """How a caller intends to use the episode.

    Only ``SEARCH_OR_FAILURE_LEARNING`` is admissible for shadow-only storage.
    Every other value is a protected consumer that requires verified canonical
    admission. Path heuristics are not a consumer kind.
    """

    SEARCH_OR_FAILURE_LEARNING = "SEARCH_OR_FAILURE_LEARNING"
    CANONICAL_INVENTORY = "CANONICAL_INVENTORY"
    PROMOTION_GATE = "PROMOTION_GATE"
    LESSON_TOOL_PROOF_OR_ROOT_GATE = "LESSON_TOOL_PROOF_OR_ROOT_GATE"


class AdmissionVerdict(str, Enum):
    """Integrity of the storage/admission claim for a consumer.

    The non-verified values are deliberately distinct so that "shadow retained
    for learning" is never conflated with "shadow treated as canonical", and
    neither is conflated with "could not check":

    ``CANONICAL_ADMISSION_VERIFIED``
        episode + receipt bind, status is canonical, consumer is protected.
    ``SHADOW_RETAINED_NONCANONICAL``
        episode + receipt bind, status is shadow, consumer is search/learning.
    ``REJECTED_SHADOW_AS_CANONICAL``
        checked and defective — a shadow receipt was offered to a protected
        consumer.
    ``REJECTED_STATUS_MISMATCH``
        checked and defective — declared status disagrees with attestation
        evidence (e.g. canonical without admission attestation).
    ``CANNOT_CHECK``
        not checked — missing/malformed receipt, invalid episode or stale hash.
    """

    CANONICAL_ADMISSION_VERIFIED = "CANONICAL_ADMISSION_VERIFIED"
    SHADOW_RETAINED_NONCANONICAL = "SHADOW_RETAINED_NONCANONICAL"
    REJECTED_SHADOW_AS_CANONICAL = "REJECTED_SHADOW_AS_CANONICAL"
    REJECTED_STATUS_MISMATCH = "REJECTED_STATUS_MISMATCH"
    CANNOT_CHECK = "CANNOT_CHECK"


_PROTECTED_CONSUMERS = frozenset(
    {
        ProtectedConsumerKind.CANONICAL_INVENTORY,
        ProtectedConsumerKind.PROMOTION_GATE,
        ProtectedConsumerKind.LESSON_TOOL_PROOF_OR_ROOT_GATE,
    }
)


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


def _is_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


@dataclass(frozen=True)
class EpisodeInventoryAdmissionReceipt:
    """Immutable receipt separating shadow storage from canonical admission.

    ``episode_artifact_hash`` binds the receipt to one exact TaskEpisode identity.
    Declared ``storage_status`` is re-checked against attestation evidence: a
    canonical claim without a nonempty ``admission_attestation_id`` is always
    rejected, so a shadow object cannot silently escalate by renaming itself.
    """

    receipt_id: str
    episode_id: str
    episode_artifact_hash: str
    storage_status: EpisodeStorageStatus
    claim_boundary: str
    evidence_pointers: Tuple[str, ...]
    frozen_at_utc: str
    admission_attestation_id: str | None = None
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise ValueError("receipt_id is required")
        if not self.episode_id:
            raise ValueError("episode_id is required")
        if not self.episode_artifact_hash:
            raise ValueError("episode_artifact_hash is required")
        if not self.claim_boundary:
            raise ValueError("claim_boundary is required")
        if not self.evidence_pointers:
            raise ValueError("evidence_pointers are required")
        if not self.frozen_at_utc:
            raise ValueError("frozen_at_utc is required")

    def content(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "episode_id": self.episode_id,
            "episode_artifact_hash": self.episode_artifact_hash,
            "storage_status": self.storage_status.value,
            "claim_boundary": self.claim_boundary,
            "admission_attestation_id": self.admission_attestation_id,
            "evidence_pointers": list(self.evidence_pointers),
            "frozen_at_utc": self.frozen_at_utc,
            "grants_proof_authority": False,
            "grants_lesson_tool_authority": False,
            "grants_framework_authority": False,
            "path_or_extension_is_not_authority": True,
        }

    @property
    def receipt_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        """Serializable receipt conforming to the frozen schema.

        The hash is derived, never supplied, so a document cannot carry a hash
        that disagrees with its own content.
        """

        document = dict(self.content())
        document["receipt_canonical_sha256"] = self.receipt_canonical_sha256
        return document

    @property
    def episode_pointer(self) -> str:
        """Evidence pointer an episode may carry to reference this receipt."""

        return f"{EPISODE_ADMISSION_POINTER_PREFIX}{self.receipt_canonical_sha256}"


@dataclass(frozen=True)
class EpisodeInventoryAdmissionReport:
    """Result of auditing storage/admission for one consumer kind."""

    verdict: AdmissionVerdict
    storage_status: EpisodeStorageStatus | None
    reasons: Tuple[str, ...]
    consumer: ProtectedConsumerKind

    @property
    def canonical_inventory_admissible(self) -> bool:
        """Only a verified canonical admission may satisfy inventory/promotion."""

        return self.verdict is AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED

    @property
    def retained_for_search_or_failure_learning(self) -> bool:
        """Shadow storage remains usable for search priority and failure learning."""

        return self.verdict in {
            AdmissionVerdict.SHADOW_RETAINED_NONCANONICAL,
            AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED,
        }

    @property
    def counts_toward_canonical_inventory(self) -> bool:
        """Shadow-only storage is excluded from canonical authority counts."""

        return self.verdict is AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED


def _structural_reasons(receipt: EpisodeInventoryAdmissionReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append(f"unknown_schema_version:{receipt.schema_version}")
    if not _SHA256_RE.match(receipt.episode_artifact_hash):
        reasons.append("episode_artifact_hash_invalid")
    if not _is_utc_timestamp(receipt.frozen_at_utc):
        reasons.append("frozen_at_utc_not_tz_aware_iso8601")
    if receipt.storage_status is EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED:
        if not receipt.admission_attestation_id:
            reasons.append("canonical_admission_attestation_missing")
    elif receipt.storage_status is EpisodeStorageStatus.PROPOSAL_SHADOW_STORED:
        if receipt.admission_attestation_id:
            reasons.append("shadow_storage_must_not_carry_admission_attestation")
    return tuple(reasons)


def audit_episode_inventory_admission(
    receipt: EpisodeInventoryAdmissionReceipt | None,
    episode: TaskEpisode,
    *,
    consumer: ProtectedConsumerKind,
) -> EpisodeInventoryAdmissionReport:
    """Derive whether ``consumer`` may treat ``episode`` as canonical.

    Missing receipt, malformed receipt, episode/receipt identity mismatch, stale
    episode hash, and shadow-as-canonical all fail closed. There is no flag that
    yields ``CANONICAL_ADMISSION_VERIFIED`` without a verified canonical receipt.
    """

    episode_reasons = validate_episode(episode)
    if episode_reasons:
        return EpisodeInventoryAdmissionReport(
            verdict=AdmissionVerdict.CANNOT_CHECK,
            storage_status=None,
            reasons=("episode_invalid:" + ",".join(episode_reasons),),
            consumer=consumer,
        )

    if receipt is None:
        if consumer is ProtectedConsumerKind.SEARCH_OR_FAILURE_LEARNING:
            # A naked episode may still inform search/learning locally; it cannot
            # satisfy canonical inventory without an explicit receipt. Callers that
            # need an explicit shadow declaration should supply one.
            return EpisodeInventoryAdmissionReport(
                verdict=AdmissionVerdict.CANNOT_CHECK,
                storage_status=None,
                reasons=("no_admission_receipt_supplied",),
                consumer=consumer,
            )
        return EpisodeInventoryAdmissionReport(
            verdict=AdmissionVerdict.CANNOT_CHECK,
            storage_status=None,
            reasons=("no_admission_receipt_supplied_for_protected_consumer",),
            consumer=consumer,
        )

    structural = _structural_reasons(receipt)
    if structural:
        mismatch_only = set(structural) <= {
            "canonical_admission_attestation_missing",
            "shadow_storage_must_not_carry_admission_attestation",
        }
        verdict = (
            AdmissionVerdict.REJECTED_STATUS_MISMATCH
            if mismatch_only
            else AdmissionVerdict.CANNOT_CHECK
        )
        return EpisodeInventoryAdmissionReport(
            verdict=verdict,
            storage_status=receipt.storage_status,
            reasons=structural,
            consumer=consumer,
        )

    reasons: list[str] = []
    if receipt.episode_id != episode.episode_id:
        reasons.append("episode_id_mismatch")
    if receipt.episode_artifact_hash != episode.artifact_hash:
        reasons.append("episode_artifact_hash_mismatch")
    if reasons:
        return EpisodeInventoryAdmissionReport(
            verdict=AdmissionVerdict.CANNOT_CHECK,
            storage_status=receipt.storage_status,
            reasons=tuple(reasons),
            consumer=consumer,
        )

    if receipt.storage_status is EpisodeStorageStatus.PROPOSAL_SHADOW_STORED:
        if consumer in _PROTECTED_CONSUMERS:
            return EpisodeInventoryAdmissionReport(
                verdict=AdmissionVerdict.REJECTED_SHADOW_AS_CANONICAL,
                storage_status=receipt.storage_status,
                reasons=("shadow_storage_cannot_satisfy_protected_consumer",),
                consumer=consumer,
            )
        return EpisodeInventoryAdmissionReport(
            verdict=AdmissionVerdict.SHADOW_RETAINED_NONCANONICAL,
            storage_status=receipt.storage_status,
            reasons=(),
            consumer=consumer,
        )

    # Canonical status with attestation already structurally checked.
    if consumer is ProtectedConsumerKind.SEARCH_OR_FAILURE_LEARNING:
        # Canonical episodes remain usable for search/learning.
        return EpisodeInventoryAdmissionReport(
            verdict=AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED,
            storage_status=receipt.storage_status,
            reasons=(),
            consumer=consumer,
        )
    return EpisodeInventoryAdmissionReport(
        verdict=AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED,
        storage_status=receipt.storage_status,
        reasons=(),
        consumer=consumer,
    )
