"""Proposal-only typed research-method telemetry linked to a ``TaskEpisode``.

``TaskEpisode`` is an immutable evidence root: it records what RAKL attempted and
observed.  Several load-bearing *decision* variables of a research cycle are
currently recoverable only by reading the free-text ``action_trace`` — which
fibre items were actually consulted, which retrieved candidates were rejected and
why, which alternatives lost, which policy selected the next action, what kind of
failure occurred, whether a local result glued globally, which saturation axes
reopened, and what the next atom is.

This module emits those variables as one bound, machine-readable record that is
**separate from** the episode and points at it, rather than enlarging the episode.
Two reasons, both from this repository:

* ``TaskEpisode`` documents itself as an evidence root that derived abstractions
  must reference rather than absorb.  Rejection reasons, failure classification,
  routing attribution and novelty metrology are *interpretation* of the episode's
  observations, so folding them into the evidence root would erase exactly the
  raw-observation/interpretation separation the substrate exists to keep.
* Every field added to ``TaskEpisode`` changes ``artifact_hash`` for every
  historical episode.  Historical objects must be migrated by versioned successors
  rather than by rewriting evidence.

This module performs no network access, no git access and no writes.  Every value
must be supplied by the recording cycle, in the same spirit as
:mod:`rakl.promotion_attestation` and :mod:`rakl.framework_freshness`.

Disclosure boundary
-------------------
The record is an auditable decision record, never a private chain-of-thought
transcript.  It carries ids, content hashes, enumerated reason codes, bounded
single-line notes, evidence pointers, outcomes and residuals.  It carries no
free-form reasoning narrative, and :func:`audit_method_telemetry` refutes a
record whose notes are unbounded or multi-line rather than silently storing them.

Relation to issue #119
----------------------
Coverage of the *search universe* is owned by the cross-problem coverage receipt.
This record references such a receipt by id and content hash through
:class:`CoverageReceiptRef` and deliberately re-derives none of its semantics: a
consulted-items list is a subset claim about what was used, never a claim about
what was searched.  The two objects compose; they are not conflated.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Mapping, Tuple


RECORD_SCHEMA_VERSION = "method-telemetry-record-v1"

#: Maximum length of any bounded rationale note.  The bound is a disclosure
#: control, not a style preference: a decision record states *which* reason code
#: applied and adds at most one short clarifying line.  Anything longer is
#: treated as an attempted reasoning transcript.
MAX_NOTE_CHARS = 240

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RecordedSetStatus(str, Enum):
    """Whether a set of decision records was recorded, empty, or never captured.

    An ordinary episode with nothing rejected declares ``NONE_OCCURRED``.  That is
    a positive statement, distinguishable from ``UNRECORDED`` — silence is not a
    search, in the same sense as ``NO_RELEVANT_MATCH`` in
    :mod:`rakl.research_memory`.
    """

    ITEMS_RECORDED = "ITEMS_RECORDED"
    NONE_OCCURRED = "NONE_OCCURRED"
    UNRECORDED = "UNRECORDED"


class FibreItemRole(str, Enum):
    """Why a consulted fibre item was pulled into the episode."""

    DEFINITION = "DEFINITION"
    THEOREM = "THEOREM"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    METHOD = "METHOD"
    REPRESENTATION = "REPRESENTATION"
    SOURCE = "SOURCE"
    DATA = "DATA"


class RoutingInfluenceKind(str, Enum):
    """Kind of prior experience that is claimed to have changed routing."""

    PRIOR_TOOL = "PRIOR_TOOL"
    PRIOR_FAILURE = "PRIOR_FAILURE"
    PRIOR_EPISODE = "PRIOR_EPISODE"
    PRIOR_LESSON = "PRIOR_LESSON"


class RejectionReason(str, Enum):
    """Enumerated, bounded grounds for discarding a retrieved or considered item.

    Reason codes rather than prose keep the record auditable and keep it from
    becoming a place to paste reasoning.
    """

    PRECONDITION_MISMATCH = "PRECONDITION_MISMATCH"
    STRUCTURAL_COORDINATE_MISMATCH = "STRUCTURAL_COORDINATE_MISMATCH"
    KNOWN_FAILURE_SCOPE_MATCH = "KNOWN_FAILURE_SCOPE_MATCH"
    SUPERSEDED_BY_SELECTED = "SUPERSEDED_BY_SELECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    COST_EXCEEDS_BUDGET = "COST_EXCEEDS_BUDGET"
    OUT_OF_SCOPE_AUTHORITY = "OUT_OF_SCOPE_AUTHORITY"
    DUPLICATE_OF_RETAINED = "DUPLICATE_OF_RETAINED"
    UNVERIFIABLE_PROVENANCE = "UNVERIFIABLE_PROVENANCE"


class AlternativeKind(str, Enum):
    """What sort of alternative was weighed against the selected action."""

    OPERATOR = "OPERATOR"
    MOTIF = "MOTIF"
    REPRESENTATION = "REPRESENTATION"
    DECOMPOSITION = "DECOMPOSITION"
    FALSIFIER = "FALSIFIER"


class SearchPolicyKind(str, Enum):
    """The control decision that selected the next action.

    ``DEFAULT_SEQUENTIAL`` is the ordinary case and is not a defect.
    ``UNRECORDED`` is fail-closed: it never collapses into a default policy.
    """

    EXPERIENCE_MEMORY_ROUTED = "EXPERIENCE_MEMORY_ROUTED"
    FAILURE_LATTICE_AVOIDANCE = "FAILURE_LATTICE_AVOIDANCE"
    EXPERT_REVIEW_RECOMMENDATION = "EXPERT_REVIEW_RECOMMENDATION"
    SATURATION_AXIS_REOPENED = "SATURATION_AXIS_REOPENED"
    CHEAPEST_FALSIFIER_FIRST = "CHEAPEST_FALSIFIER_FIRST"
    OPERATOR_DIRECTED = "OPERATOR_DIRECTED"
    DEFAULT_SEQUENTIAL = "DEFAULT_SEQUENTIAL"
    UNRECORDED = "UNRECORDED"


class FailureCategory(str, Enum):
    """Typed failure taxonomy for the episode.

    ``NONE`` and ``UNCLASSIFIED`` are deliberately distinct.  ``NONE`` means the
    episode did not fail; ``UNCLASSIFIED`` means it failed and the category was
    not established, which is a routing signal towards an ontology/method-basis
    gap rather than a licence to keep guessing.
    """

    NONE = "NONE"
    MATHEMATICAL = "MATHEMATICAL"
    DECOMPOSITION = "DECOMPOSITION"
    RETRIEVAL = "RETRIEVAL"
    REPRESENTATION = "REPRESENTATION"
    BRIDGE_GLUING = "BRIDGE_GLUING"
    SOURCE_PROVENANCE = "SOURCE_PROVENANCE"
    VERIFICATION = "VERIFICATION"
    TOOLING_CI = "TOOLING_CI"
    META_POLICY = "META_POLICY"
    UNCLASSIFIED = "UNCLASSIFIED"


class GluingStatus(str, Enum):
    """Local-versus-global status of whatever the episode established.

    ``NOT_APPLICABLE`` covers episodes with no local/global distinction to make.
    ``UNOBSERVED`` is fail-closed and never means "glued".
    """

    NOT_APPLICABLE = "NOT_APPLICABLE"
    LOCAL_ONLY = "LOCAL_ONLY"
    LOCAL_CONSISTENT_GLOBAL_UNTESTED = "LOCAL_CONSISTENT_GLOBAL_UNTESTED"
    GLOBAL_OBSTRUCTION_FOUND = "GLOBAL_OBSTRUCTION_FOUND"
    GLOBALLY_GLUED = "GLOBALLY_GLUED"
    UNOBSERVED = "UNOBSERVED"


class SaturationDelta(str, Enum):
    """Movement of one saturation axis across the episode."""

    ADVANCED = "ADVANCED"
    UNCHANGED = "UNCHANGED"
    REOPENED = "REOPENED"
    REGRESSED = "REGRESSED"


class NoveltyClass(str, Enum):
    """Structural-novelty metrology for the locally solved task.

    ``NOT_ASSESSED`` is explicitly available so that an ordinary episode is not
    forced to manufacture a novelty claim.
    """

    NOT_ASSESSED = "NOT_ASSESSED"
    NO_STRUCTURAL_NOVELTY = "NO_STRUCTURAL_NOVELTY"
    RECOMBINATION_OF_KNOWN = "RECOMBINATION_OF_KNOWN"
    NEW_STRUCTURAL_COORDINATE = "NEW_STRUCTURAL_COORDINATE"


class DisclosureStatus(str, Enum):
    """Derived judgement about what kind of content the record actually carries.

    This is the enforced form of the chain-of-thought boundary.  It is derived
    from the record's own bounded-note discipline, not declared by the recorder.
    """

    BOUNDED_DECISION_RECORD = "BOUNDED_DECISION_RECORD"
    REASONING_TRANSCRIPT_SUSPECTED = "REASONING_TRANSCRIPT_SUSPECTED"
    UNCHECKED = "UNCHECKED"


class TelemetryVerdict(str, Enum):
    """Integrity of the record, separate from what the record reports.

    A well-formed record that honestly reports a failed, unclassified episode is
    ``RECORDED_PROPOSAL_ONLY``; the failure travels in the payload, not in the
    verdict.
    """

    RECORDED_PROPOSAL_ONLY = "RECORDED_PROPOSAL_ONLY"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


#: Novelty classes that assert something about structure and therefore require a
#: named comparison basis.  ``NOT_ASSESSED`` and ``NO_STRUCTURAL_NOVELTY`` assert
#: nothing positive and need none.
_NOVELTY_CLAIM_CLASSES = frozenset(
    {NoveltyClass.RECOMBINATION_OF_KNOWN, NoveltyClass.NEW_STRUCTURAL_COORDINATE}
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


def record_canonical_sha256(document: Mapping[str, Any]) -> str:
    """Hash a record document excluding its own content-hash field."""

    subject = dict(document)
    subject.pop("record_canonical_sha256", None)
    return canonical_json_sha256(subject)


def _note_violation(field: str, note: str) -> str | None:
    """Return a disclosure-boundary reason code for a bounded note, if violated.

    Two independent tripwires.  Length catches a pasted block; the newline check
    catches a transcript that happens to be short.  A genuine bounded rationale is
    one line.
    """

    if len(note) > MAX_NOTE_CHARS:
        return f"{field}_exceeds_bounded_length"
    if "\n" in note or "\r" in note:
        return f"{field}_is_multiline_narrative"
    return None


@dataclass(frozen=True)
class CoverageReceiptRef:
    """Pointer to a cross-problem coverage receipt owned by issue #119.

    Held by id and content hash only.  This record re-derives no coverage
    semantics and makes no completeness claim on the strength of holding a
    pointer.
    """

    synthesis_id: str
    receipt_canonical_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "synthesis_id": self.synthesis_id,
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
        }


@dataclass(frozen=True)
class ConsultedFibreItem:
    """One fibre item the episode actually consulted.

    The episode's ``fibre_snapshot_hash`` binds the fibre as a whole; this binds
    the individual items that were used, which the aggregate hash cannot express.
    """

    item_id: str
    item_content_hash: str
    role: FibreItemRole

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "item_content_hash": self.item_content_hash,
            "role": self.role.value,
        }


@dataclass(frozen=True)
class RoutingInfluence:
    """A prior tool, failure, episode or lesson that changed this episode's route.

    ``changed_action`` is the load-bearing bit: consulting prior experience and
    being *redirected* by it are different events, and only the second supports a
    later claim that accumulated experience is doing work.
    """

    kind: RoutingInfluenceKind
    reference_id: str
    changed_action: bool
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "reference_id": self.reference_id,
            "changed_action": self.changed_action,
            "note": self.note,
        }


@dataclass(frozen=True)
class RejectedCandidate:
    """A candidate that retrieval surfaced and the episode discarded."""

    candidate_id: str
    retrieval_source: str
    reason_code: RejectionReason
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "retrieval_source": self.retrieval_source,
            "reason_code": self.reason_code.value,
            "note": self.note,
        }


@dataclass(frozen=True)
class AlternativeConsidered:
    """An operator/motif/representation weighed against the selected action.

    A non-selected alternative must carry a reason code; otherwise the record
    would assert deliberation it cannot evidence.
    """

    alternative_id: str
    kind: AlternativeKind
    selected: bool
    reason_code: RejectionReason | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alternative_id": self.alternative_id,
            "kind": self.kind.value,
            "selected": self.selected,
            "reason_code": None if self.reason_code is None else self.reason_code.value,
            "note": self.note,
        }


@dataclass(frozen=True)
class SearchPolicyDecision:
    """The control decision that selected the next action."""

    policy_kind: SearchPolicyKind
    selected_action_id: str
    decision_note: str = ""
    considered_alternative_ids: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_kind": self.policy_kind.value,
            "selected_action_id": self.selected_action_id,
            "decision_note": self.decision_note,
            "considered_alternative_ids": list(self.considered_alternative_ids),
        }


@dataclass(frozen=True)
class SaturationAxisDelta:
    """Movement of one saturation axis attributable to this episode."""

    axis_id: str
    delta: SaturationDelta
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis_id": self.axis_id,
            "delta": self.delta.value,
            "note": self.note,
        }


@dataclass(frozen=True)
class GluingRecord:
    """Local-versus-global status of what the episode established."""

    status: GluingStatus
    local_scope_id: str = ""
    global_scope_id: str | None = None
    obstruction_ids: Tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "local_scope_id": self.local_scope_id,
            "global_scope_id": self.global_scope_id,
            "obstruction_ids": list(self.obstruction_ids),
            "note": self.note,
        }


@dataclass(frozen=True)
class StructuralNoveltyMetrology:
    """Structural novelty of the locally solved task, against a named basis."""

    novelty_class: NoveltyClass
    comparison_basis_ids: Tuple[str, ...] = ()
    changed_structural_coordinates: Tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "novelty_class": self.novelty_class.value,
            "comparison_basis_ids": list(self.comparison_basis_ids),
            "changed_structural_coordinates": list(self.changed_structural_coordinates),
            "note": self.note,
        }


@dataclass(frozen=True)
class NextActionPointer:
    """The exact next action and child atom this episode hands forward."""

    next_action_id: str
    child_atom_id: str | None = None
    rationale_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "next_action_id": self.next_action_id,
            "child_atom_id": self.child_atom_id,
            "rationale_note": self.rationale_note,
        }


@dataclass(frozen=True)
class MethodTelemetryRecord:
    """Typed method telemetry bound to one immutable ``TaskEpisode``.

    The record is interpretation of an evidence root, not a second evidence root.
    ``episode_id`` plus ``episode_artifact_hash`` bind it to the exact episode
    content; rebinding it to a different episode is detectable rather than silent.

    The ``*_status`` declarations exist so that an ordinary episode is fully
    representable: nothing rejected and nothing reconsidered is stated as
    ``NONE_OCCURRED``, which is a different fact from ``UNRECORDED``.
    """

    episode_id: str
    episode_artifact_hash: str
    task_id: str
    atom_id: str
    public_trace_event_id: str
    claim_boundary: str
    consulted_items_status: RecordedSetStatus
    routing_influence_status: RecordedSetStatus
    rejected_candidates_status: RecordedSetStatus
    alternatives_status: RecordedSetStatus
    failure_category: FailureCategory
    search_policy_decision: SearchPolicyDecision
    gluing: GluingRecord
    novelty: StructuralNoveltyMetrology
    next_action: NextActionPointer
    schema_version: str = RECORD_SCHEMA_VERSION
    consulted_fibre_items: Tuple[ConsultedFibreItem, ...] = ()
    routing_influences: Tuple[RoutingInfluence, ...] = ()
    rejected_candidates: Tuple[RejectedCandidate, ...] = ()
    alternatives_considered: Tuple[AlternativeConsidered, ...] = ()
    saturation_axis_deltas: Tuple[SaturationAxisDelta, ...] = ()
    reopened_saturation_axis_ids: Tuple[str, ...] = ()
    coverage_receipt_ref: CoverageReceiptRef | None = None
    failure_note: str = ""
    evidence_pointers: Tuple[str, ...] = ()
    record_canonical_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "episode_artifact_hash": self.episode_artifact_hash,
            "task_id": self.task_id,
            "atom_id": self.atom_id,
            "public_trace_event_id": self.public_trace_event_id,
            "claim_boundary": self.claim_boundary,
            "consulted_items_status": self.consulted_items_status.value,
            "routing_influence_status": self.routing_influence_status.value,
            "rejected_candidates_status": self.rejected_candidates_status.value,
            "alternatives_status": self.alternatives_status.value,
            "failure_category": self.failure_category.value,
            "search_policy_decision": self.search_policy_decision.to_dict(),
            "gluing": self.gluing.to_dict(),
            "novelty": self.novelty.to_dict(),
            "next_action": self.next_action.to_dict(),
            "consulted_fibre_items": [i.to_dict() for i in self.consulted_fibre_items],
            "routing_influences": [i.to_dict() for i in self.routing_influences],
            "rejected_candidates": [i.to_dict() for i in self.rejected_candidates],
            "alternatives_considered": [
                i.to_dict() for i in self.alternatives_considered
            ],
            "saturation_axis_deltas": [
                i.to_dict() for i in self.saturation_axis_deltas
            ],
            "reopened_saturation_axis_ids": list(self.reopened_saturation_axis_ids),
            "coverage_receipt_ref": (
                None
                if self.coverage_receipt_ref is None
                else self.coverage_receipt_ref.to_dict()
            ),
            "failure_note": self.failure_note,
            "evidence_pointers": list(self.evidence_pointers),
            "record_canonical_sha256": self.record_canonical_sha256,
            "is_episode_evidence_root": self.is_episode_evidence_root,
            "grants_method_authority": self.grants_method_authority,
            "discloses_private_chain_of_thought": (
                self.discloses_private_chain_of_thought
            ),
        }

    def with_content_hash(self) -> "MethodTelemetryRecord":
        """Return a copy carrying its own canonical content hash."""

        return replace(
            self,
            record_canonical_sha256=record_canonical_sha256(self.to_dict()),
        )

    @property
    def is_episode_evidence_root(self) -> bool:
        """Always false: this record interprets an episode, it does not replace it."""

        return False

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def discloses_private_chain_of_thought(self) -> bool:
        """Always false by construction.

        The record has a fixed field set with no free-form narrative slot, and
        every note is length- and line-bounded by
        :func:`audit_method_telemetry`.  This property states the contract; the
        audit enforces it.
        """

        return False


@dataclass(frozen=True)
class MethodTelemetryReport:
    verdict: TelemetryVerdict
    disclosure_status: DisclosureStatus
    reasons: Tuple[str, ...]

    @property
    def recorded(self) -> bool:
        return self.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def grants_search_completeness_claim(self) -> bool:
        """Coverage of the search universe is owned by the #119 receipt."""

        return False


def _disclosure_reasons(record: MethodTelemetryRecord) -> Tuple[str, ...]:
    """Collect bounded-note violations across every free-text slot."""

    reasons: list[str] = []
    checks: list[tuple[str, str]] = [
        ("claim_boundary", record.claim_boundary),
        ("failure_note", record.failure_note),
        ("search_policy_decision_note", record.search_policy_decision.decision_note),
        ("gluing_note", record.gluing.note),
        ("novelty_note", record.novelty.note),
        ("next_action_rationale_note", record.next_action.rationale_note),
    ]
    for influence in record.routing_influences:
        checks.append(("routing_influence_note", influence.note))
    for candidate in record.rejected_candidates:
        checks.append(("rejected_candidate_note", candidate.note))
    for alternative in record.alternatives_considered:
        checks.append(("alternative_note", alternative.note))
    for delta in record.saturation_axis_deltas:
        checks.append(("saturation_axis_note", delta.note))
    for field, note in checks:
        violation = _note_violation(field, note)
        if violation is not None and violation not in reasons:
            reasons.append(violation)
    return tuple(reasons)


def _structural_reasons(record: MethodTelemetryRecord) -> Tuple[str, ...]:
    reasons: list[str] = []
    if record.schema_version != RECORD_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    for name, value in (
        ("episode_id", record.episode_id),
        ("task_id", record.task_id),
        ("atom_id", record.atom_id),
        ("public_trace_event_id", record.public_trace_event_id),
        ("claim_boundary", record.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not _SHA256_RE.match(record.episode_artifact_hash or ""):
        reasons.append("episode_artifact_hash_invalid")
    if not record.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    if not (record.search_policy_decision.selected_action_id or "").strip():
        reasons.append("selected_action_id_missing")
    if not (record.next_action.next_action_id or "").strip():
        reasons.append("next_action_id_missing")
    for item in record.consulted_fibre_items:
        if not item.item_id.strip() or not _SHA256_RE.match(item.item_content_hash or ""):
            reasons.append("consulted_fibre_item_binding_invalid")
            break
    ref = record.coverage_receipt_ref
    if ref is not None and (
        not ref.synthesis_id.strip()
        or not _SHA256_RE.match(ref.receipt_canonical_sha256 or "")
    ):
        reasons.append("coverage_receipt_ref_binding_invalid")
    return tuple(reasons)


def _set_declaration_reasons(record: MethodTelemetryRecord) -> Tuple[str, ...]:
    """Contradictions between a declared set status and the recorded set."""

    reasons: list[str] = []
    declarations: tuple[tuple[str, RecordedSetStatus, int], ...] = (
        (
            "consulted_items",
            record.consulted_items_status,
            len(record.consulted_fibre_items),
        ),
        (
            "routing_influence",
            record.routing_influence_status,
            len(record.routing_influences),
        ),
        (
            "rejected_candidates",
            record.rejected_candidates_status,
            len(record.rejected_candidates),
        ),
        (
            "alternatives",
            record.alternatives_status,
            len(record.alternatives_considered),
        ),
    )
    for name, status, count in declarations:
        if status is RecordedSetStatus.ITEMS_RECORDED and count == 0:
            reasons.append(f"{name}_declared_recorded_but_empty")
        if status is RecordedSetStatus.NONE_OCCURRED and count > 0:
            reasons.append(f"{name}_declared_none_but_present")
    return tuple(reasons)


def _payload_consistency_reasons(record: MethodTelemetryRecord) -> Tuple[str, ...]:
    """Internal contradictions in what the record asserts about itself."""

    reasons: list[str] = []

    for alternative in record.alternatives_considered:
        if not alternative.selected and alternative.reason_code is None:
            reasons.append("non_selected_alternative_missing_reason_code")
            break

    gluing = record.gluing
    if gluing.status is GluingStatus.GLOBAL_OBSTRUCTION_FOUND and not gluing.obstruction_ids:
        reasons.append("global_obstruction_claimed_without_obstruction_ids")
    if gluing.status is GluingStatus.GLOBALLY_GLUED and not (gluing.global_scope_id or ""):
        reasons.append("global_gluing_claimed_without_global_scope")

    novelty = record.novelty
    if novelty.novelty_class in _NOVELTY_CLAIM_CLASSES and not novelty.comparison_basis_ids:
        reasons.append("novelty_claimed_without_comparison_basis")
    if (
        novelty.novelty_class is NoveltyClass.NEW_STRUCTURAL_COORDINATE
        and not novelty.changed_structural_coordinates
    ):
        reasons.append("new_structural_coordinate_claimed_without_named_coordinate")

    declared_reopened = set(record.reopened_saturation_axis_ids)
    delta_reopened = {
        delta.axis_id
        for delta in record.saturation_axis_deltas
        if delta.delta is SaturationDelta.REOPENED
    }
    if declared_reopened - delta_reopened:
        reasons.append("reopened_axis_declared_without_matching_delta")
    if delta_reopened - declared_reopened:
        reasons.append("reopened_axis_delta_not_declared")

    if record.failure_category is FailureCategory.NONE and record.failure_note.strip():
        reasons.append("failure_note_present_without_failure_category")

    return tuple(reasons)


def audit_method_telemetry(
    record: MethodTelemetryRecord | None,
    *,
    episode_id: str | None = None,
    episode_artifact_hash: str | None = None,
) -> MethodTelemetryReport:
    """Classify a method-telemetry record's integrity and disclosure posture.

    Fails closed.  A missing record, a malformed binding and an unverifiable
    content hash each yield ``CANNOT_CHECK`` with a distinct reason rather than a
    default of "recorded".  A record that contradicts its own declarations, that
    is bound to a different episode, or that carries an unbounded note is
    ``REFUTED_CLAIM``.

    An episode that simply had nothing to reject and nothing to reconsider is
    ``RECORDED_PROPOSAL_ONLY`` with no reasons: this audit reports contradictions,
    not activity levels.
    """

    if record is None:
        return MethodTelemetryReport(
            TelemetryVerdict.CANNOT_CHECK,
            DisclosureStatus.UNCHECKED,
            ("method_telemetry_record_missing",),
        )

    structural = _structural_reasons(record)
    if structural:
        return MethodTelemetryReport(
            TelemetryVerdict.CANNOT_CHECK,
            DisclosureStatus.UNCHECKED,
            structural,
        )

    if not record.record_canonical_sha256:
        return MethodTelemetryReport(
            TelemetryVerdict.CANNOT_CHECK,
            DisclosureStatus.UNCHECKED,
            ("record_canonical_sha256_missing",),
        )
    if not _SHA256_RE.match(record.record_canonical_sha256):
        return MethodTelemetryReport(
            TelemetryVerdict.CANNOT_CHECK,
            DisclosureStatus.UNCHECKED,
            ("record_canonical_sha256_malformed",),
        )
    if record.record_canonical_sha256 != record_canonical_sha256(record.to_dict()):
        return MethodTelemetryReport(
            TelemetryVerdict.REFUTED_CLAIM,
            DisclosureStatus.UNCHECKED,
            ("record_canonical_sha256_mismatch",),
        )

    disclosure = _disclosure_reasons(record)
    if disclosure:
        return MethodTelemetryReport(
            TelemetryVerdict.REFUTED_CLAIM,
            DisclosureStatus.REASONING_TRANSCRIPT_SUSPECTED,
            disclosure,
        )

    binding: list[str] = []
    if episode_id is not None and episode_id != record.episode_id:
        binding.append("telemetry_bound_to_other_episode")
    if (
        episode_artifact_hash is not None
        and episode_artifact_hash != record.episode_artifact_hash
    ):
        binding.append("telemetry_bound_to_other_episode_content")

    contradictions = (
        tuple(binding)
        + _set_declaration_reasons(record)
        + _payload_consistency_reasons(record)
    )
    if contradictions:
        return MethodTelemetryReport(
            TelemetryVerdict.REFUTED_CLAIM,
            DisclosureStatus.BOUNDED_DECISION_RECORD,
            contradictions,
        )

    notes: list[str] = []
    if record.search_policy_decision.policy_kind is SearchPolicyKind.UNRECORDED:
        notes.append("search_policy_decision_unrecorded")
    for name, status in (
        ("consulted_items", record.consulted_items_status),
        ("routing_influence", record.routing_influence_status),
        ("rejected_candidates", record.rejected_candidates_status),
        ("alternatives", record.alternatives_status),
    ):
        if status is RecordedSetStatus.UNRECORDED:
            notes.append(f"{name}_unrecorded")
    if record.failure_category is FailureCategory.UNCLASSIFIED:
        notes.append("failure_category_unclassified_route_to_metacognitive_auditor")

    return MethodTelemetryReport(
        TelemetryVerdict.RECORDED_PROPOSAL_ONLY,
        DisclosureStatus.BOUNDED_DECISION_RECORD,
        tuple(notes),
    )
