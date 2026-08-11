"""Proposal-only pre-action fibre receipt binding chronology before execution.

RAKL v3 freezes the *outcome* as a :class:`~rakl.experience_substrate.TaskEpisode`.
Application case studies show the recurring gap sits earlier: an agent can notice
and execute a useful discriminator before the exact problem fibre, the retrieval
authorities, the chosen operator and the predeclared falsifier are content-bound.
The later episode can be recorded honestly and still be *necessarily
retrospective*, because nothing in the record distinguishes a prediction from a
description written after the result was visible.

This module supplies the missing machine boundary between **action selection**
and **action execution**.  A :class:`PreActionFibreReceipt` binds the selection
context; :func:`audit_pre_action_chronology` derives whether a later episode has
a valid predecessor.  Retrospective status is *derived*, never declared: there is
no argument anywhere in this module by which a caller can assert that an episode
was prospective.  The only route to
:attr:`EpisodeChronologyStatus.PROSPECTIVELY_BOUND` is a receipt that verifies
its own content hash, binds this episode's exact fibre snapshot, precedes it, and
predeclared the outcome branch that was actually observed.

What this object does **not** do:

* It does not claim the fibre search universe was complete.  A receipt binds what
  *was* retrieved, not what *existed*; retrieval-universe coverage is a separate
  concern (cf. RAKL #119) and ``claims_fibre_search_universe_complete`` is
  permanently ``False``.  ``coverage_receipt_id`` exists only to point at that
  separate object when one is available.
* It does not establish wall-clock priority.  The timestamps in a receipt are
  strings an agent writes; a dishonest agent can write an early one.  Ordering
  here is *internal consistency*, and tamper-evidence comes from the append-only
  public trace anchor (``public_trace_event_id``), not from the string.
  ``establishes_wall_clock_priority`` is therefore permanently ``False``.
* It mints no proof, lesson, tool, gluing, theorem, review-independence or
  framework authority.

The module performs no network, git or filesystem access.  Every observation of
what an action actually did is supplied by an independent observer, exactly as in
:mod:`rakl.promotion_attestation`; nothing here infers effects from an episode's
own self-description.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Mapping, Tuple

from .experience_substrate import TaskEpisode


RECEIPT_SCHEMA_VERSION = "pre-action-fibre-receipt-v1"

_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ActionConsequence(str, Enum):
    """Whether an action can change governed state.

    ``UNCLASSIFIED`` is not a neutral third option.  It fails closed and is
    treated as ``CONSEQUENTIAL``, so declining to classify buys an agent nothing.

    ``NON_CONSEQUENTIAL_DECLARED`` carries ``DECLARED`` in its name because it is
    a claim, not a fact.  It is checked against independently observed effects;
    see :func:`audit_pre_action_chronology`.
    """

    CONSEQUENTIAL = "CONSEQUENTIAL"
    NON_CONSEQUENTIAL_DECLARED = "NON_CONSEQUENTIAL_DECLARED"
    UNCLASSIFIED = "UNCLASSIFIED"


class RetrievalAuthority(str, Enum):
    """Authority carried by one retrieved artifact.

    Only ``CANONICAL`` may back an action.  ``PENDING`` and ``NONCANONICAL``
    artifacts are legitimate to *read* — the failure this distinguishes is
    reading one and then treating it as support.
    """

    CANONICAL = "CANONICAL"
    PENDING = "PENDING"
    NONCANONICAL = "NONCANONICAL"
    UNVERIFIED = "UNVERIFIED"


class RetrievalDisposition(str, Enum):
    """What the agent did with a retrieved item.

    Recording relevant-but-rejected items is the point: a fibre that lists only
    what was used cannot distinguish "nothing else was relevant" from "nothing
    else was looked at".
    """

    SELECTED = "SELECTED"
    RELEVANT_BUT_REJECTED = "RELEVANT_BUT_REJECTED"


class EpisodeChronologyStatus(str, Enum):
    """Derived chronology conclusion for one episode.

    ``RETROSPECTIVE_ONLY`` is an honest, fully usable record: it feeds search
    priority and failure learning unchanged.  What it cannot do is satisfy a
    prospective promotion or preregistration gate.

    ``REFUTED_CLAIM`` is stronger and separate: the record positively contradicts
    itself — a tampered receipt, a receipt dated after the episode it claims to
    precede, a discriminator swapped after the result, or authority claimed for a
    noncanonical artifact.

    ``NON_CONSEQUENTIAL_NO_RECEIPT_REQUIRED`` is the no-alarm outcome.  A cheap
    action that mutated no governed state owes no ceremony at all.
    """

    PROSPECTIVELY_BOUND = "PROSPECTIVELY_BOUND"
    RETROSPECTIVE_ONLY = "RETROSPECTIVE_ONLY"
    NON_CONSEQUENTIAL_NO_RECEIPT_REQUIRED = "NON_CONSEQUENTIAL_NO_RECEIPT_REQUIRED"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


#: Steps a driver must perform before a consequential operator executes.  Listed
#: for workflow documentation; this module executes none of them.
REQUIRED_PRE_ACTION_STEPS: Tuple[str, ...] = (
    "classify_action_consequence",
    "freeze_exact_problem_fibre_snapshot",
    "bind_selected_and_relevant_but_rejected_retrievals_with_authority",
    "predeclare_discriminator_and_allowed_outcome_branches",
    "anchor_receipt_in_public_research_trace",
)


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


def _is_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.utcoffset() != timedelta(0):
        return None
    return parsed


@dataclass(frozen=True)
class RetrievalBinding:
    """One retrieval bound into the pre-action fibre.

    ``rejection_reason`` is mandatory for a rejected item and forbidden for a
    selected one — an unexplained rejection is indistinguishable from an
    omission, which is the failure this field exists to prevent.
    """

    retrieval_id: str
    disposition: RetrievalDisposition
    authority: RetrievalAuthority
    rejection_reason: str | None = None
    evidence_pointer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieval_id": self.retrieval_id,
            "disposition": self.disposition.value,
            "authority": self.authority.value,
            "rejection_reason": self.rejection_reason,
            "evidence_pointer": self.evidence_pointer,
        }


@dataclass(frozen=True)
class ObservedActionEffects:
    """Independently observed governed-state mutations caused by an action.

    These booleans must come from an observer of repository/ledger state, not
    from the acting agent's own narration and not from an episode's
    ``operator_ids`` or ``action_trace`` — a self-report that an action was
    harmless is precisely the claim under test.

    ``None`` means *not observed* and fails closed to
    :attr:`EpisodeChronologyStatus.CANNOT_CHECK`; it never reads as ``False``.
    """

    mutated_candidate_state: bool | None
    mutated_lesson_state: bool | None
    mutated_tool_state: bool | None
    mutated_route_state: bool | None

    @property
    def _values(self) -> Tuple[bool | None, ...]:
        return (
            self.mutated_candidate_state,
            self.mutated_lesson_state,
            self.mutated_tool_state,
            self.mutated_route_state,
        )

    @property
    def any_mutation_observed(self) -> bool:
        return any(value is True for value in self._values)

    @property
    def fully_observed(self) -> bool:
        return all(value is not None for value in self._values)

    @property
    def unobserved_surfaces(self) -> Tuple[str, ...]:
        names = (
            "candidate_state",
            "lesson_state",
            "tool_state",
            "route_state",
        )
        return tuple(
            name for name, value in zip(names, self._values) if value is None
        )


@dataclass(frozen=True)
class PreActionFibreReceipt:
    """Content-bound record of an action selection, frozen before execution.

    The receipt binds *what was chosen and why*, not *what was found*.  It is
    silent by construction about whether the fibre search universe was complete.

    ``sequence_index`` is a binding, not a comparator.  ``TaskEpisode`` carries
    no sequence number, so there is nothing to compare it against; its job is to
    freeze the agent's declared position in its own action sequence into the
    content hash, so that a later reordering of receipts is detectable.  Ordering
    against the episode is done on ``timestamp``.
    """

    framework_repository: str
    framework_commit: str
    application_repository: str
    application_revision: str
    task_id: str
    atom_id: str
    context_hash: str
    fibre_snapshot_hash: str
    operator_id: str
    predeclared_discriminator: str
    allowed_outcome_branches: Tuple[str, ...]
    timestamp: str
    sequence_index: int
    public_trace_event_id: str
    declared_consequence: ActionConsequence = ActionConsequence.UNCLASSIFIED
    retrieval_bindings: Tuple[RetrievalBinding, ...] = ()
    authority_bearing_retrieval_ids: Tuple[str, ...] = ()
    coverage_receipt_id: str | None = None
    evidence_pointers: Tuple[str, ...] = ()
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "framework_repository": self.framework_repository,
            "framework_commit": self.framework_commit,
            "application_repository": self.application_repository,
            "application_revision": self.application_revision,
            "task_id": self.task_id,
            "atom_id": self.atom_id,
            "context_hash": self.context_hash,
            "fibre_snapshot_hash": self.fibre_snapshot_hash,
            "operator_id": self.operator_id,
            "predeclared_discriminator": self.predeclared_discriminator,
            "allowed_outcome_branches": list(self.allowed_outcome_branches),
            "timestamp": self.timestamp,
            "sequence_index": self.sequence_index,
            "public_trace_event_id": self.public_trace_event_id,
            "declared_consequence": self.declared_consequence.value,
            "retrieval_bindings": [
                binding.to_dict() for binding in self.retrieval_bindings
            ],
            "authority_bearing_retrieval_ids": list(
                self.authority_bearing_retrieval_ids
            ),
            "coverage_receipt_id": self.coverage_receipt_id,
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "claims_fibre_search_universe_complete": False,
            "establishes_wall_clock_priority": False,
            "grants_proof_authority": False,
            "grants_lesson_authority": False,
            "grants_tool_authority": False,
            "grants_gluing_authority": False,
            "grants_theorem_authority": False,
            "grants_review_independence": False,
            "grants_framework_authority": False,
        }

    def with_content_hash(self) -> "PreActionFibreReceipt":
        """Return a copy carrying its own canonical content hash."""

        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )

    def selected_retrieval_ids(self) -> Tuple[str, ...]:
        return tuple(
            binding.retrieval_id
            for binding in self.retrieval_bindings
            if binding.disposition is RetrievalDisposition.SELECTED
        )

    def binding_for(self, retrieval_id: str) -> RetrievalBinding | None:
        for binding in self.retrieval_bindings:
            if binding.retrieval_id == retrieval_id:
                return binding
        return None


@dataclass(frozen=True)
class EpisodeChronologyReport:
    """Derived chronology conclusion.  No constructor argument sets the status."""

    status: EpisodeChronologyStatus
    reasons: Tuple[str, ...]
    receipt_required: bool
    non_authoritative_selected_retrieval_ids: Tuple[str, ...] = ()
    relevant_but_rejected_retrieval_ids: Tuple[str, ...] = ()

    @property
    def satisfies_prospective_gate(self) -> bool:
        """Only a fully bound predecessor receipt satisfies a prospective gate."""

        return self.status is EpisodeChronologyStatus.PROSPECTIVELY_BOUND

    @property
    def usable_for_search_priority(self) -> bool:
        """Always true.  Retrospective records still steer search."""

        return True

    @property
    def usable_for_failure_learning(self) -> bool:
        """Always true.  Retrospective records still teach failure modes."""

        return True

    @property
    def claims_fibre_search_universe_complete(self) -> bool:
        return False

    @property
    def establishes_wall_clock_priority(self) -> bool:
        return False

    @property
    def grants_proof_authority(self) -> bool:
        return False

    @property
    def grants_lesson_authority(self) -> bool:
        return False

    @property
    def grants_tool_authority(self) -> bool:
        return False

    @property
    def grants_gluing_authority(self) -> bool:
        return False

    @property
    def grants_theorem_authority(self) -> bool:
        return False

    @property
    def grants_review_independence(self) -> bool:
        return False

    @property
    def grants_framework_authority(self) -> bool:
        return False


def _structural_reasons(receipt: PreActionFibreReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    if not _GIT_OID_RE.match(receipt.framework_commit or ""):
        reasons.append("framework_commit_invalid")
    if not (receipt.application_revision or "").strip():
        reasons.append("application_revision_missing")
    for name, value in (
        ("framework_repository", receipt.framework_repository),
        ("application_repository", receipt.application_repository),
        ("task_id", receipt.task_id),
        ("atom_id", receipt.atom_id),
        ("context_hash", receipt.context_hash),
        ("fibre_snapshot_hash", receipt.fibre_snapshot_hash),
        ("operator_id", receipt.operator_id),
        ("predeclared_discriminator", receipt.predeclared_discriminator),
        ("public_trace_event_id", receipt.public_trace_event_id),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not receipt.allowed_outcome_branches:
        reasons.append("allowed_outcome_branches_missing")
    elif len(set(receipt.allowed_outcome_branches)) != len(
        receipt.allowed_outcome_branches
    ):
        reasons.append("allowed_outcome_branches_contain_duplicates")
    if not receipt.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    if receipt.sequence_index < 0:
        reasons.append("sequence_index_negative")
    if not _is_utc_timestamp(receipt.timestamp or ""):
        reasons.append("receipt_timestamp_not_utc_iso8601")

    seen: set[str] = set()
    for binding in receipt.retrieval_bindings:
        if not (binding.retrieval_id or "").strip():
            reasons.append("retrieval_id_missing")
            continue
        if binding.retrieval_id in seen:
            reasons.append("duplicate_retrieval_binding")
        seen.add(binding.retrieval_id)
        if binding.disposition is RetrievalDisposition.RELEVANT_BUT_REJECTED:
            if not (binding.rejection_reason or "").strip():
                reasons.append("relevant_but_rejected_retrieval_without_reason")
        elif binding.rejection_reason is not None:
            reasons.append("selected_retrieval_carries_rejection_reason")

    if len(set(receipt.authority_bearing_retrieval_ids)) != len(
        receipt.authority_bearing_retrieval_ids
    ):
        reasons.append("authority_bearing_retrieval_ids_contain_duplicates")

    if not receipt.receipt_canonical_sha256:
        reasons.append("receipt_canonical_sha256_missing")
    elif not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        reasons.append("receipt_canonical_sha256_malformed")
    return tuple(reasons)


def _retrieval_report_fields(
    receipt: PreActionFibreReceipt | None,
) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    if receipt is None:
        return ((), ())
    non_authoritative = tuple(
        binding.retrieval_id
        for binding in receipt.retrieval_bindings
        if binding.disposition is RetrievalDisposition.SELECTED
        and binding.authority is not RetrievalAuthority.CANONICAL
    )
    rejected = tuple(
        binding.retrieval_id
        for binding in receipt.retrieval_bindings
        if binding.disposition is RetrievalDisposition.RELEVANT_BUT_REJECTED
    )
    return non_authoritative, rejected


def audit_pre_action_chronology(
    receipt: PreActionFibreReceipt | None,
    episode: TaskEpisode,
    *,
    declared_consequence: ActionConsequence,
    observed_effects: ObservedActionEffects,
    observed_outcome_branch: str,
    observed_discriminator: str | None = None,
    observed_retrieval_authorities: Mapping[str, RetrievalAuthority] | None = None,
) -> EpisodeChronologyReport:
    """Derive whether ``episode`` had a valid pre-action predecessor.

    ``declared_consequence`` is the agent's classification and is *not* trusted.
    It is checked against ``observed_effects``, which an independent observer
    supplies.  A declared-cheap action that in fact mutated governed state is
    reported as :attr:`EpisodeChronologyStatus.REFUTED_CLAIM`; that check is what
    stops the classifier from becoming a bypass.

    A genuinely cheap action that mutated nothing requires no receipt and emits
    no reason demanding one — disproportionate ceremony for trivial actions is a
    design failure, not a safety margin.

    ``observed_discriminator`` and ``observed_outcome_branch`` describe what the
    agent reports *after* the result.  Divergence from the predeclared values is
    the discriminator-substitution failure and is refuted, not downgraded.
    """

    non_authoritative, rejected = _retrieval_report_fields(receipt)

    def report(
        status: EpisodeChronologyStatus,
        reasons: Tuple[str, ...],
        *,
        receipt_required: bool,
    ) -> EpisodeChronologyReport:
        return EpisodeChronologyReport(
            status,
            reasons,
            receipt_required,
            non_authoritative,
            rejected,
        )

    # --- classification trust surface -------------------------------------
    if declared_consequence is ActionConsequence.NON_CONSEQUENTIAL_DECLARED:
        if observed_effects.any_mutation_observed:
            return report(
                EpisodeChronologyStatus.REFUTED_CLAIM,
                (
                    "action_declared_non_consequential_mutated_governed_state",
                    f"episode={episode.episode_id}",
                ),
                receipt_required=True,
            )
        if not observed_effects.fully_observed:
            return report(
                EpisodeChronologyStatus.CANNOT_CHECK,
                (
                    "non_consequential_declaration_not_independently_observed",
                )
                + tuple(
                    f"unobserved:{surface}"
                    for surface in observed_effects.unobserved_surfaces
                ),
                receipt_required=True,
            )
        return report(
            EpisodeChronologyStatus.NON_CONSEQUENTIAL_NO_RECEIPT_REQUIRED,
            (
                "no_governed_state_mutation_observed",
                "cheap_action_owes_no_chronology_ceremony",
            ),
            receipt_required=False,
        )

    prefix: Tuple[str, ...] = ()
    if declared_consequence is ActionConsequence.UNCLASSIFIED:
        prefix = ("unclassified_action_treated_as_consequential",)

    # --- consequential path -----------------------------------------------
    if receipt is None:
        return report(
            EpisodeChronologyStatus.RETROSPECTIVE_ONLY,
            prefix
            + (
                "no_pre_action_fibre_receipt_precedes_this_episode",
                "record_remains_usable_for_search_priority_and_failure_learning",
            ),
            receipt_required=True,
        )

    structural = _structural_reasons(receipt)
    if structural:
        return report(
            EpisodeChronologyStatus.CANNOT_CHECK,
            prefix + structural,
            receipt_required=True,
        )

    recomputed = receipt_canonical_sha256(receipt.to_dict())
    if recomputed != receipt.receipt_canonical_sha256:
        return report(
            EpisodeChronologyStatus.REFUTED_CLAIM,
            prefix
            + (
                "receipt_content_hash_does_not_match_receipt_content",
                f"declared={receipt.receipt_canonical_sha256}",
                f"recomputed={recomputed}",
            ),
            receipt_required=True,
        )

    binding_reasons: list[str] = []
    if receipt.atom_id != episode.atom_id:
        binding_reasons.append("receipt_atom_id_does_not_match_episode")
    if receipt.context_hash != episode.context_hash:
        binding_reasons.append("receipt_context_hash_does_not_match_episode")
    if receipt.fibre_snapshot_hash != episode.fibre_snapshot_hash:
        binding_reasons.append("receipt_fibre_snapshot_hash_does_not_match_episode")
    if receipt.task_id != episode.task_id:
        binding_reasons.append("receipt_task_id_does_not_match_episode")
    if receipt.operator_id not in episode.operator_ids:
        binding_reasons.append("receipt_operator_not_among_episode_operators")
    if binding_reasons:
        return report(
            EpisodeChronologyStatus.RETROSPECTIVE_ONLY,
            prefix
            + tuple(binding_reasons)
            + ("no_receipt_binds_this_exact_episode",),
            receipt_required=True,
        )

    receipt_time = _parse_utc(receipt.timestamp)
    episode_time = _parse_utc(episode.timestamp)
    if receipt_time is None or episode_time is None:
        return report(
            EpisodeChronologyStatus.CANNOT_CHECK,
            prefix + ("episode_or_receipt_timestamp_not_utc_iso8601",),
            receipt_required=True,
        )
    if receipt_time > episode_time:
        return report(
            EpisodeChronologyStatus.REFUTED_CLAIM,
            prefix
            + (
                "pre_action_receipt_is_timestamped_after_the_episode_it_claims_to_precede",
            ),
            receipt_required=True,
        )
    if receipt_time == episode_time:
        return report(
            EpisodeChronologyStatus.RETROSPECTIVE_ONLY,
            prefix + ("receipt_is_not_strictly_earlier_than_the_episode",),
            receipt_required=True,
        )

    if (
        observed_discriminator is not None
        and observed_discriminator != receipt.predeclared_discriminator
    ):
        return report(
            EpisodeChronologyStatus.REFUTED_CLAIM,
            prefix
            + (
                "reported_discriminator_differs_from_the_predeclared_discriminator",
                f"predeclared={receipt.predeclared_discriminator}",
                f"reported={observed_discriminator}",
            ),
            receipt_required=True,
        )

    if observed_outcome_branch not in receipt.allowed_outcome_branches:
        return report(
            EpisodeChronologyStatus.REFUTED_CLAIM,
            prefix
            + (
                "observed_outcome_branch_was_not_predeclared",
                f"observed={observed_outcome_branch}",
            ),
            receipt_required=True,
        )

    selected = set(receipt.selected_retrieval_ids())
    for retrieval_id in receipt.authority_bearing_retrieval_ids:
        if retrieval_id not in selected:
            return report(
                EpisodeChronologyStatus.REFUTED_CLAIM,
                prefix
                + (
                    "authority_claimed_for_a_retrieval_that_was_not_selected",
                    f"retrieval={retrieval_id}",
                ),
                receipt_required=True,
            )
        binding = receipt.binding_for(retrieval_id)
        if binding is not None and binding.authority is not RetrievalAuthority.CANONICAL:
            return report(
                EpisodeChronologyStatus.REFUTED_CLAIM,
                prefix
                + (
                    "authority_claimed_for_a_noncanonical_or_pending_retrieval",
                    f"retrieval={retrieval_id}",
                    f"authority={binding.authority.value}",
                ),
                receipt_required=True,
            )

    if observed_retrieval_authorities is not None:
        for binding in receipt.retrieval_bindings:
            observed = observed_retrieval_authorities.get(binding.retrieval_id)
            if observed is None:
                continue
            if observed is not binding.authority:
                return report(
                    EpisodeChronologyStatus.REFUTED_CLAIM,
                    prefix
                    + (
                        "declared_retrieval_authority_contradicted_by_observation",
                        f"retrieval={binding.retrieval_id}",
                        f"declared={binding.authority.value}",
                        f"observed={observed.value}",
                    ),
                    receipt_required=True,
                )

    reasons = prefix + (
        "receipt_binds_this_episode_and_precedes_it",
        "discriminator_and_outcome_branch_were_predeclared",
        "fibre_search_universe_completeness_is_not_claimed_by_this_receipt",
    )
    if receipt.coverage_receipt_id is None:
        reasons = reasons + (
            "no_coverage_receipt_referenced_universe_completeness_remains_unbound",
        )
    return report(
        EpisodeChronologyStatus.PROSPECTIVELY_BOUND,
        reasons,
        receipt_required=True,
    )
