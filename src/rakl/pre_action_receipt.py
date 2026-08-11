"""Proposal-only pre-action fibre receipt (two-phase episode binding).

RAKL v3 freezes the *outcome* as a :class:`~rakl.experience_substrate.TaskEpisode`,
but nothing binds the stage before it. An agent can notice and execute a useful
discriminator before the exact problem fibre, the retrieval authorities, the
chosen operator and the predeclared falsifier are content-bound. The later
episode can be recorded honestly and still be, unavoidably, retrospective.

This module emits the missing pre-action half as an immutable, content-hashed
shell, and derives the chronology status of an episode by *comparing* the two
halves. The status is never declared: it is re-derived from the pair, so nothing
an agent asserts after the fact can promote a retrospective episode.

Scope, stated as narrowly as the artifact supports:

* **Not wired into any runtime path.** ``record_task_episode`` is unchanged.
  Nothing in RAKL calls this module. The issue asks for receipts generated
  *automatically*; this lands the object and its guard, and automatic
  enforcement remains a separate, separately reviewable change.
* **No completeness claim.** A verified binding says what was selected and
  rejected, never that the fibre search universe was complete. Retrieval-universe
  coverage is a different object, tracked by RAKL issue #119. (Unrelated to
  :mod:`rakl.discovery_coverage`, which covers a different question again.)
* **Detection, not prevention.** A post-hoc discriminator substitution is
  detected because the predeclared discriminator is inside the hashed receipt and
  the episode references that hash. An actor able to rewrite *both* the receipt
  and the episode's reference is outside what a pure value module can witness;
  that guarantee belongs to an append-only store.
* **No authority.** Emits no proof, lesson, tool, gluing, theorem or
  review-independence authority, and grants none by being present.

Retrospective episodes remain fully usable for search priority and failure
learning. That half of the acceptance boundary is a machine-checked invariant
here, not a promise: admissibility for those two uses is derived from episode
well-formedness and is never a function of chronology status.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Tuple

from .experience_substrate import EpisodeOutcome, TaskEpisode

RECEIPT_SCHEMA_VERSION = "pre-action-fibre-receipt-v1"

#: Prefix used to reference a receipt from an episode's evidence pointers. The
#: episode dataclass is deliberately not modified: binding travels as data.
EPISODE_RECEIPT_POINTER_PREFIX = "pre_action_receipt:"

_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RetrievalAuthority(str, Enum):
    """Authority of one retrieved artifact at the moment it was selected.

    ``PENDING`` and ``NONCANONICAL`` artifacts may legitimately *inform* an
    action; they may never *bear authority* for it. ``UNSPECIFIED`` fails closed
    into the same non-authority-bearing class: an unstated authority is not an
    authority.
    """

    CANONICAL = "CANONICAL"
    PENDING = "PENDING"
    NONCANONICAL = "NONCANONICAL"
    UNSPECIFIED = "UNSPECIFIED"


#: The only authority that a selected retrieval may carry into an action.
_AUTHORITY_BEARING = frozenset({RetrievalAuthority.CANONICAL})


class BindingVerdict(str, Enum):
    """What was established about the pre-action/outcome pair.

    The three non-verified values are deliberately distinct, so that "no receipt
    was claimed" is never conflated with "a receipt was claimed and refuted", and
    neither is conflated with "could not check":

    ``PROSPECTIVE_BINDING_VERIFIED``
        a receipt exists, is self-consistent, is referenced by the episode, binds
        the same fibre/atom/context/operators, and strictly precedes it.
    ``RETROSPECTIVE_NO_RECEIPT``
        no receipt was supplied. Not a defect: an action that never claimed
        prospective credit incurs no ceremony and is not flagged.
    ``RETROSPECTIVE_BINDING_REFUTED``
        checked, and defective — a receipt was supplied but does not bind.
    ``CANNOT_CHECK``
        not checked — receipt or episode is malformed or unverifiable.
    """

    PROSPECTIVE_BINDING_VERIFIED = "PROSPECTIVE_BINDING_VERIFIED"
    RETROSPECTIVE_NO_RECEIPT = "RETROSPECTIVE_NO_RECEIPT"
    RETROSPECTIVE_BINDING_REFUTED = "RETROSPECTIVE_BINDING_REFUTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class ChronologyStatus(str, Enum):
    """Whether an episode may carry prospective credit.

    Derived from :class:`BindingVerdict`, never declared. Exactly one verdict
    yields ``PROSPECTIVE_BOUND``; every other path — including every failure to
    check — yields ``RETROSPECTIVE_ONLY``. That asymmetry is what makes
    retrospective status unavoidable rather than opt-in.
    """

    PROSPECTIVE_BOUND = "PROSPECTIVE_BOUND"
    RETROSPECTIVE_ONLY = "RETROSPECTIVE_ONLY"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


@dataclass(frozen=True)
class SelectedRetrieval:
    """One artifact retrieved into the fibre before the action was chosen."""

    retrieval_id: str
    authority: RetrievalAuthority
    payload_hash: str

    def __post_init__(self) -> None:
        if not self.retrieval_id:
            raise ValueError("selected retrieval requires a retrieval_id")
        if not _SHA256_RE.match(self.payload_hash):
            raise ValueError("selected retrieval payload_hash must be sha256 hex")

    @property
    def bears_authority(self) -> bool:
        return self.authority in _AUTHORITY_BEARING


@dataclass(frozen=True)
class RejectedRetrieval:
    """One artifact judged relevant and then deliberately not used.

    Recording rejections is what distinguishes "considered and set aside" from
    "never seen". It does not make the search universe complete; see #119.
    """

    retrieval_id: str
    rejection_reason: str

    def __post_init__(self) -> None:
        if not self.retrieval_id or not self.rejection_reason:
            raise ValueError("rejected retrieval requires a retrieval_id and rejection_reason")


@dataclass(frozen=True)
class PreActionFibreReceipt:
    """Immutable pre-action shell, hashed over its own content.

    The predeclared discriminator and its allowed outcome branches are inside the
    hashed content on purpose: substituting them after seeing a result changes
    the content hash and therefore breaks the episode's reference.
    """

    receipt_id: str
    framework_repository: str
    framework_commit: str
    application_repository: str
    application_commit: str
    task_id: str
    atom_id: str
    context_hash: str
    fibre_snapshot_hash: str
    operator_ids: Tuple[str, ...]
    selected_retrievals: Tuple[SelectedRetrieval, ...]
    rejected_retrievals: Tuple[RejectedRetrieval, ...]
    predeclared_discriminator: str
    allowed_outcome_branches: Tuple[str, ...]
    frozen_at_utc: str
    sequence_index: int
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise ValueError("pre-action receipt requires a receipt_id")
        if self.sequence_index < 0:
            raise ValueError("pre-action receipt sequence_index cannot be negative")
        valid_outcomes = {e.value for e in EpisodeOutcome}
        for branch in self.allowed_outcome_branches:
            if branch not in valid_outcomes:
                raise ValueError(
                    f"invalid allowed_outcome_branch: {branch!r}; "
                    f"must be one of {sorted(valid_outcomes)}"
                )

    def content(self) -> Mapping[str, Any]:
        """Canonical hashed content. Every field that could be swapped is inside."""

        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "framework_repository": self.framework_repository,
            "framework_commit": self.framework_commit,
            "application_repository": self.application_repository,
            "application_commit": self.application_commit,
            "task_id": self.task_id,
            "atom_id": self.atom_id,
            "context_hash": self.context_hash,
            "fibre_snapshot_hash": self.fibre_snapshot_hash,
            "operator_ids": list(self.operator_ids),
            "selected_retrievals": [
                {
                    "retrieval_id": item.retrieval_id,
                    "authority": item.authority.value,
                    "payload_hash": item.payload_hash,
                }
                for item in self.selected_retrievals
            ],
            "rejected_retrievals": [
                {
                    "retrieval_id": item.retrieval_id,
                    "rejection_reason": item.rejection_reason,
                }
                for item in self.rejected_retrievals
            ],
            "predeclared_discriminator": self.predeclared_discriminator,
            "allowed_outcome_branches": list(self.allowed_outcome_branches),
            "frozen_at_utc": self.frozen_at_utc,
            "sequence_index": self.sequence_index,
        }

    @property
    def receipt_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        """Serializable receipt: hashed content plus the hash it commits to.

        Conforms to ``schemas/pre-action-fibre-receipt-v1.schema.json``. The hash
        is derived, never supplied, so a document cannot carry a hash that
        disagrees with its own content.
        """

        document = dict(self.content())
        document["receipt_canonical_sha256"] = self.receipt_canonical_sha256
        return document

    @property
    def episode_pointer(self) -> str:
        """The evidence pointer an episode must carry to reference this receipt."""

        return f"{EPISODE_RECEIPT_POINTER_PREFIX}{self.receipt_canonical_sha256}"

    @property
    def authority_bearing_retrieval_ids(self) -> Tuple[str, ...]:
        """Selected retrievals that may carry authority into the action.

        Pending, noncanonical and unspecified-authority artifacts are excluded
        here while remaining recorded above: they informed the action, and that
        is all the receipt lets them do.
        """

        return tuple(item.retrieval_id for item in self.selected_retrievals if item.bears_authority)


@dataclass(frozen=True)
class PreActionBindingReport:
    """Result of comparing a pre-action receipt with the episode that followed."""

    verdict: BindingVerdict
    chronology_status: ChronologyStatus
    reasons: Tuple[str, ...]
    authority_bearing_retrieval_ids: Tuple[str, ...]
    non_authority_bearing_retrieval_ids: Tuple[str, ...]

    @property
    def prospective_gate_admissible(self) -> bool:
        """Only a verified binding may satisfy a prospective promotion gate."""

        return self.chronology_status is ChronologyStatus.PROSPECTIVE_BOUND

    #: A receipt binds chronology. It never asserts that the fibre search
    #: universe was complete; that claim belongs to RAKL issue #119 and no value
    #: of this report can be read as making it.
    @property
    def implies_fibre_search_universe_complete(self) -> bool:
        return False


def episode_is_well_formed(episode: TaskEpisode) -> bool:
    """Minimal structural admissibility, deliberately independent of chronology."""

    return bool(episode.episode_id and episode.atom_id and episode.artifact_hash)


def admissible_for_search_priority(episode: TaskEpisode) -> bool:
    """Retrospective episodes still guide search. Chronology is not consulted."""

    return episode_is_well_formed(episode)


def admissible_for_failure_learning(episode: TaskEpisode) -> bool:
    """Retrospective episodes still teach. Chronology is not consulted."""

    return episode_is_well_formed(episode)


def _structural_reasons(receipt: PreActionFibreReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append(f"unknown_schema_version:{receipt.schema_version}")
    if not _GIT_OID_RE.match(receipt.framework_commit):
        reasons.append("framework_commit_not_a_git_oid")
    if not _GIT_OID_RE.match(receipt.application_commit):
        reasons.append("application_commit_not_a_git_oid")
    if not receipt.fibre_snapshot_hash:
        reasons.append("fibre_snapshot_hash_missing")
    if not receipt.operator_ids:
        reasons.append("operator_ids_missing")
    if not receipt.predeclared_discriminator:
        reasons.append("predeclared_discriminator_missing")
    if not receipt.allowed_outcome_branches:
        reasons.append("allowed_outcome_branches_missing")
    if _parse_utc(receipt.frozen_at_utc) is None:
        reasons.append("frozen_at_utc_not_tz_aware_iso8601")
    return tuple(reasons)


def audit_pre_action_binding(
    receipt: PreActionFibreReceipt | None,
    episode: TaskEpisode,
) -> PreActionBindingReport:
    """Derive an episode's chronology status by comparing it with its receipt.

    The status is a function of the pair. A missing receipt, a mismatched
    receipt, a receipt not referenced by the episode, a receipt that does not
    strictly precede the episode, and an outcome outside the predeclared
    branches all yield ``RETROSPECTIVE_ONLY``. There is no argument, flag or
    declared field that yields ``PROSPECTIVE_BOUND`` without a verified binding.
    """

    if receipt is None:
        return PreActionBindingReport(
            verdict=BindingVerdict.RETROSPECTIVE_NO_RECEIPT,
            chronology_status=ChronologyStatus.RETROSPECTIVE_ONLY,
            reasons=("no_pre_action_receipt_supplied",),
            authority_bearing_retrieval_ids=(),
            non_authority_bearing_retrieval_ids=(),
        )

    bearing = receipt.authority_bearing_retrieval_ids
    non_bearing = tuple(
        item.retrieval_id for item in receipt.selected_retrievals if not item.bears_authority
    )

    def _report(verdict: BindingVerdict, reasons: Tuple[str, ...]) -> PreActionBindingReport:
        status = (
            ChronologyStatus.PROSPECTIVE_BOUND
            if verdict is BindingVerdict.PROSPECTIVE_BINDING_VERIFIED
            else ChronologyStatus.RETROSPECTIVE_ONLY
        )
        return PreActionBindingReport(
            verdict=verdict,
            chronology_status=status,
            reasons=reasons,
            authority_bearing_retrieval_ids=bearing,
            non_authority_bearing_retrieval_ids=non_bearing,
        )

    structural = _structural_reasons(receipt)
    if structural:
        return _report(BindingVerdict.CANNOT_CHECK, structural)

    if not episode_is_well_formed(episode):
        return _report(BindingVerdict.CANNOT_CHECK, ("episode_not_well_formed",))

    episode_time = _parse_utc(episode.timestamp)
    receipt_time = _parse_utc(receipt.frozen_at_utc)
    if episode_time is None:
        return _report(BindingVerdict.CANNOT_CHECK, ("episode_timestamp_not_tz_aware_iso8601",))

    reasons: list[str] = []

    if receipt.episode_pointer not in episode.evidence_pointers:
        # Either the episode never referenced this receipt, or the receipt's
        # hashed content changed after the episode was written — a post-hoc
        # discriminator or fibre substitution presents exactly here.
        reasons.append("episode_does_not_reference_this_receipt_content_hash")

    if episode.atom_id != receipt.atom_id:
        reasons.append("atom_id_mismatch")
    if episode.context_hash != receipt.context_hash:
        reasons.append("context_hash_mismatch")
    if episode.fibre_snapshot_hash != receipt.fibre_snapshot_hash:
        reasons.append("fibre_snapshot_hash_mismatch")
    if tuple(episode.operator_ids) != tuple(receipt.operator_ids):
        reasons.append("operator_ids_mismatch")
    if episode.task_id != receipt.task_id:
        reasons.append("task_id_mismatch")

    if receipt_time is not None and not receipt_time < episode_time:
        reasons.append("receipt_does_not_strictly_precede_episode")

    if episode.outcome.value not in receipt.allowed_outcome_branches:
        reasons.append(f"outcome_outside_predeclared_branches:{episode.outcome.value}")

    if reasons:
        return _report(BindingVerdict.RETROSPECTIVE_BINDING_REFUTED, tuple(reasons))

    return _report(BindingVerdict.PROSPECTIVE_BINDING_VERIFIED, ())
