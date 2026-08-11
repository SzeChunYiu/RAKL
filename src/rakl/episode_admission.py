"""Proposal-only TaskEpisode storage/admission separation.

The framework has a strict content/hash contract for ``TaskEpisode``, but until
this module nothing distinguished:

* **A.** valid proposal/shadow TaskEpisode evidence that may be stored immediately
* **B.** canonical episode-inventory admission that may satisfy protected
  discovery, promotion, lesson/tool, proof, or root gates

Application compatibility logic therefore had to infer admission intent from
path, filename extension, or the presence of a top-level ``episode_id``. That
conflation repeatedly turned valid proposal objects into exhaustive-inventory
failures (and the reverse risk: a shadow sidecar falsely treated as canonical).

This module freezes the missing authority/storage separation as an immutable,
content-hashed receipt bound to an episode's exact ``artifact_hash``. Path and
filename heuristics are deliberately not consulted: renaming a file or omitting
``episode_id`` never becomes an authority mechanism.

Scope, stated as narrowly as the artifact supports:

* **Not wired into any runtime path.** ``add_episode`` / ``record_task_episode``
  are unchanged. Automatic enforcement at protected consumers remains a separate
  change.
* **No authority.** A ``PROPOSAL_SHADOW_STORED`` receipt grants search/failure
  retention only. A ``CANONICAL_INVENTORY_ADMITTED`` receipt is a registration
  claim about inventory discoverability, never proof, lesson, tool, gluing,
  theorem, or review-independence authority.
* **Hard fail-closed rule.** Any protected consumer that treats an episode as
  canonical must require an explicit ``CANONICAL_INVENTORY_ADMITTED`` receipt
  whose ``episode_artifact_hash`` matches the episode. Shadow-only storage is
  rejected.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Tuple

from .experience_substrate import TaskEpisode, validate_episode

RECEIPT_SCHEMA_VERSION = "episode-admission-receipt-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")


class EpisodeStorageStatus(str, Enum):
    """Explicit storage/admission status bound to one TaskEpisode.

    ``PROPOSAL_SHADOW_STORED``
        episode may be retained and retrieved for search/failure learning; it
        must not satisfy canonical inventory, promotion, lesson/tool, proof, or
        root gates.
    ``CANONICAL_INVENTORY_ADMITTED``
        episode carries an explicit protected registration claim and is subject
        to exhaustive identity/hash/provenance discovery checks.
    """

    PROPOSAL_SHADOW_STORED = "PROPOSAL_SHADOW_STORED"
    CANONICAL_INVENTORY_ADMITTED = "CANONICAL_INVENTORY_ADMITTED"


class ProtectedConsumer(str, Enum):
    """Consumers that may only accept canonically admitted episodes.

    Path/name inference is not a consumer. Each enum value is an authority-
    bearing use the issue enumerates.
    """

    CANONICAL_INVENTORY = "CANONICAL_INVENTORY"
    PROMOTION = "PROMOTION"
    LESSON_OR_TOOL = "LESSON_OR_TOOL"
    PROOF = "PROOF"
    ROOT_GATE = "ROOT_GATE"


class AdmissionVerdict(str, Enum):
    """Outcome of auditing an episode against an admission receipt."""

    CANONICAL_ADMITTED = "CANONICAL_ADMITTED"
    SHADOW_RETAINED = "SHADOW_RETAINED"
    PROTECTED_CONSUMER_REJECTED = "PROTECTED_CONSUMER_REJECTED"
    RECEIPT_UNVERIFIABLE = "RECEIPT_UNVERIFIABLE"
    EPISODE_INVALID = "EPISODE_INVALID"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class EpisodeAdmissionReceipt:
    """Content-bound storage/admission status for one TaskEpisode.

    The receipt binds ``episode_id`` and ``episode_artifact_hash``. A receipt
    whose hash no longer matches the episode cannot admit anything.
    """

    receipt_id: str
    episode_id: str
    episode_artifact_hash: str
    storage_status: EpisodeStorageStatus
    inventory_registry_id: str
    registered_at_utc: str
    registration_evidence_pointers: Tuple[str, ...]
    reverification_triggers: Tuple[str, ...]
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise ValueError("admission receipt requires a receipt_id")
        if not self.episode_id:
            raise ValueError("admission receipt requires an episode_id")
        if not _SHA256_RE.match(self.episode_artifact_hash):
            raise ValueError("episode_artifact_hash must be sha256 hex")
        if not self.inventory_registry_id:
            raise ValueError("admission receipt requires an inventory_registry_id")
        if not _ISO_UTC_RE.match(self.registered_at_utc):
            raise ValueError("registered_at_utc must be ISO-8601 UTC ending in 'Z'")
        if not self.registration_evidence_pointers:
            raise ValueError("admission receipt requires registration_evidence_pointers")
        if not self.reverification_triggers:
            raise ValueError("admission receipt requires reverification_triggers")
        if (
            self.storage_status is EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
            and self.inventory_registry_id.startswith("shadow:")
        ):
            raise ValueError(
                "canonical admission cannot use a shadow: inventory_registry_id"
            )

    def content(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "episode_id": self.episode_id,
            "episode_artifact_hash": self.episode_artifact_hash,
            "storage_status": self.storage_status.value,
            "inventory_registry_id": self.inventory_registry_id,
            "registered_at_utc": self.registered_at_utc,
            "registration_evidence_pointers": list(self.registration_evidence_pointers),
            "reverification_triggers": list(self.reverification_triggers),
        }

    @property
    def receipt_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        document = dict(self.content())
        document["receipt_canonical_sha256"] = self.receipt_canonical_sha256
        return document

    @property
    def is_canonical(self) -> bool:
        return self.storage_status is EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED

    @property
    def is_shadow(self) -> bool:
        return self.storage_status is EpisodeStorageStatus.PROPOSAL_SHADOW_STORED


@dataclass(frozen=True)
class EpisodeAdmissionReport:
    """Audit result for one episode + receipt (+ optional protected consumer)."""

    episode_id: str
    receipt_id: str | None
    verdict: AdmissionVerdict
    reasons: Tuple[str, ...]
    storage_status: EpisodeStorageStatus | None
    retained_for_search_or_failure_learning: bool
    satisfies_canonical_inventory: bool
    path_or_name_heuristics_consulted: bool = False

    @property
    def fail_closed(self) -> bool:
        return self.verdict in {
            AdmissionVerdict.PROTECTED_CONSUMER_REJECTED,
            AdmissionVerdict.RECEIPT_UNVERIFIABLE,
            AdmissionVerdict.EPISODE_INVALID,
        }


def _receipt_binds_episode(
    episode: TaskEpisode, receipt: EpisodeAdmissionReceipt
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.episode_id != episode.episode_id:
        reasons.append("receipt_episode_id_mismatch")
    if receipt.episode_artifact_hash != episode.artifact_hash:
        reasons.append("receipt_episode_artifact_hash_mismatch")
    return tuple(reasons)


def retainable_for_search_and_failure_learning(
    episode: TaskEpisode,
    receipt: EpisodeAdmissionReceipt | None,
) -> bool:
    """Shadow and canonical receipts both retain episodes for learning uses.

    A missing or unbound receipt does not invent retention: the episode must
    still be content-valid, and a present receipt must bind the episode.
    """

    if validate_episode(episode):
        return False
    if receipt is None:
        return False
    if _receipt_binds_episode(episode, receipt):
        return False
    return receipt.storage_status in {
        EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
    }


def satisfies_canonical_inventory(
    episode: TaskEpisode,
    receipt: EpisodeAdmissionReceipt | None,
) -> bool:
    """True only for a valid episode with a binding canonical admission receipt."""

    if validate_episode(episode):
        return False
    if receipt is None or not receipt.is_canonical:
        return False
    return not _receipt_binds_episode(episode, receipt)


def audit_episode_admission(
    episode: TaskEpisode,
    receipt: EpisodeAdmissionReceipt | None,
    *,
    protected_consumer: ProtectedConsumer | None = None,
    claimed_path_or_name_hint: str | None = None,
) -> EpisodeAdmissionReport:
    """Audit storage/admission for one episode.

    ``claimed_path_or_name_hint`` is accepted only so callers can prove that
    path/extension heuristics are *ignored*: the auditor records that it was
    supplied and never uses it to decide authority.
    """

    episode_reasons = validate_episode(episode)
    if episode_reasons:
        return EpisodeAdmissionReport(
            episode_id=episode.episode_id,
            receipt_id=None if receipt is None else receipt.receipt_id,
            verdict=AdmissionVerdict.EPISODE_INVALID,
            reasons=episode_reasons,
            storage_status=None if receipt is None else receipt.storage_status,
            retained_for_search_or_failure_learning=False,
            satisfies_canonical_inventory=False,
            path_or_name_heuristics_consulted=False,
        )

    if receipt is None:
        reasons = ("admission_receipt_missing",)
        if protected_consumer is not None:
            return EpisodeAdmissionReport(
                episode_id=episode.episode_id,
                receipt_id=None,
                verdict=AdmissionVerdict.PROTECTED_CONSUMER_REJECTED,
                reasons=reasons + (f"protected_consumer={protected_consumer.value}",),
                storage_status=None,
                retained_for_search_or_failure_learning=False,
                satisfies_canonical_inventory=False,
                path_or_name_heuristics_consulted=False,
            )
        return EpisodeAdmissionReport(
            episode_id=episode.episode_id,
            receipt_id=None,
            verdict=AdmissionVerdict.RECEIPT_UNVERIFIABLE,
            reasons=reasons,
            storage_status=None,
            retained_for_search_or_failure_learning=False,
            satisfies_canonical_inventory=False,
            path_or_name_heuristics_consulted=False,
        )

    bind_reasons = _receipt_binds_episode(episode, receipt)
    # Re-derive the document hash so a round-tripped stale hash cannot pass.
    _ = receipt.receipt_canonical_sha256
    if bind_reasons:
        return EpisodeAdmissionReport(
            episode_id=episode.episode_id,
            receipt_id=receipt.receipt_id,
            verdict=AdmissionVerdict.RECEIPT_UNVERIFIABLE,
            reasons=bind_reasons,
            storage_status=receipt.storage_status,
            retained_for_search_or_failure_learning=False,
            satisfies_canonical_inventory=False,
            path_or_name_heuristics_consulted=False,
        )

    hint_supplied = claimed_path_or_name_hint is not None
    retained = retainable_for_search_and_failure_learning(episode, receipt)
    canonical = satisfies_canonical_inventory(episode, receipt)

    if protected_consumer is not None and not canonical:
        return EpisodeAdmissionReport(
            episode_id=episode.episode_id,
            receipt_id=receipt.receipt_id,
            verdict=AdmissionVerdict.PROTECTED_CONSUMER_REJECTED,
            reasons=(
                "shadow_or_noncanonical_rejected_by_protected_consumer",
                f"protected_consumer={protected_consumer.value}",
                f"storage_status={receipt.storage_status.value}",
                "path_or_name_hint_ignored",
            ),
            storage_status=receipt.storage_status,
            retained_for_search_or_failure_learning=retained,
            satisfies_canonical_inventory=False,
            path_or_name_heuristics_consulted=False,
        )

    if receipt.is_canonical:
        return EpisodeAdmissionReport(
            episode_id=episode.episode_id,
            receipt_id=receipt.receipt_id,
            verdict=AdmissionVerdict.CANONICAL_ADMITTED,
            reasons=(
                "canonical_inventory_admission_verified",
                "path_or_name_hint_ignored" if hint_supplied else "no_path_or_name_hint",
            ),
            storage_status=receipt.storage_status,
            retained_for_search_or_failure_learning=retained,
            satisfies_canonical_inventory=True,
            path_or_name_heuristics_consulted=False,
        )

    return EpisodeAdmissionReport(
        episode_id=episode.episode_id,
        receipt_id=receipt.receipt_id,
        verdict=AdmissionVerdict.SHADOW_RETAINED,
        reasons=(
            "proposal_shadow_retained_for_search_and_failure_learning",
            "excluded_from_canonical_authority_counts",
            "path_or_name_hint_ignored" if hint_supplied else "no_path_or_name_hint",
        ),
        storage_status=receipt.storage_status,
        retained_for_search_or_failure_learning=retained,
        satisfies_canonical_inventory=False,
        path_or_name_heuristics_consulted=False,
    )


def count_canonical_authority_episodes(
    pairs: Iterable[Tuple[TaskEpisode, EpisodeAdmissionReceipt | None]],
) -> int:
    """Count episodes that satisfy canonical inventory under explicit receipts.

    Shadow-only storage never increments this count, regardless of path/name.
    """

    total = 0
    for episode, receipt in pairs:
        report = audit_episode_admission(episode, receipt)
        if report.satisfies_canonical_inventory:
            total += 1
    return total
