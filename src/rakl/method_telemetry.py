"""Proposal-only typed method telemetry linked to a task episode.

``TaskEpisode`` is the immutable evidence root: what was attempted and observed.
The decision variables needed to study *how* an agent researches — which fibre
items were actually opened, which prior experience changed routing, what was
retrieved and rejected, what was considered and not selected, which policy chose
the next action — are interpretation of that record, and today they survive only
as free text in ``action_trace``.

This module records them as a **separate linked object** rather than as extra
fields on the episode, so that raw observation and interpretation stay
separable and the evidence root keeps a stable content hash.  The link is
immutable: telemetry binds the episode id, the episode artifact hash and the
fibre snapshot hash, and fails closed the moment any of the three stops matching.

The episode is supplied as an observed :class:`EpisodeBinding` rather than
imported, for the same reason :mod:`rakl.promotion_attestation` takes an
observation packet: a proposal-only object must not acquire a runtime edge into
the evidence-root module.

Chain-of-thought is out of scope by construction, not by promise.  Every
rationale field is a single-line bounded decision record; a multi-line or
oversized value is rejected, so the object has no field a reasoning transcript
can occupy.  See :func:`bounded_rationale_reasons`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Sequence, Tuple


RECEIPT_SCHEMA_VERSION = "method-telemetry-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
#: Any line break or control whitespace disqualifies a bounded rationale.
_LINE_BREAK_RE = re.compile(r"[\r\n\v\f\t\x1c-\x1e\u2028\u2029]")

#: Maximum characters in one bounded rationale.  This is a smuggling guard, not
#: a tuned parameter: combined with the single-line rule below it leaves the
#: object no field large enough to hold a multi-step reasoning narrative, while
#: sitting above the size of any single decision record.  It is deliberately at
#: or below the ``maxLength`` this repository already uses for bounded strings.
_MAX_RATIONALE_CHARS = 512

#: Maximum entries in any one decision collection.  Also a smuggling guard: it
#: stops a transcript being split across many short single-line rationales.  It
#: is set well above the structural size of an episode's decision record and is
#: not a threshold on research behaviour.
_MAX_DECISION_ENTRIES = 64


class MethodFailureClass(str, Enum):
    """Typed failure taxonomy for a research step.

    ``NO_FAILURE_OBSERVED`` and ``UNCLASSIFIED_FAILURE`` are not
    interchangeable: the first is checked and clean, the second records that a
    failure occurred and was *not* attributed.  Repeated unclassified failures
    are an ontology/method-basis signal, so they must remain visible rather than
    be absorbed into a neighbouring category.
    """

    MATHEMATICAL = "MATHEMATICAL"
    DECOMPOSITION = "DECOMPOSITION"
    RETRIEVAL = "RETRIEVAL"
    REPRESENTATION = "REPRESENTATION"
    BRIDGE_GLUING = "BRIDGE_GLUING"
    SOURCE_PROVENANCE = "SOURCE_PROVENANCE"
    VERIFICATION = "VERIFICATION"
    TOOLING_CI = "TOOLING_CI"
    META_POLICY = "META_POLICY"
    NO_FAILURE_OBSERVED = "NO_FAILURE_OBSERVED"
    UNCLASSIFIED_FAILURE = "UNCLASSIFIED_FAILURE"


#: Classes that attribute an observed failure to a cause.
_ATTRIBUTED_FAILURE_CLASSES = frozenset(
    {
        MethodFailureClass.MATHEMATICAL,
        MethodFailureClass.DECOMPOSITION,
        MethodFailureClass.RETRIEVAL,
        MethodFailureClass.REPRESENTATION,
        MethodFailureClass.BRIDGE_GLUING,
        MethodFailureClass.SOURCE_PROVENANCE,
        MethodFailureClass.VERIFICATION,
        MethodFailureClass.TOOLING_CI,
        MethodFailureClass.META_POLICY,
    }
)


class GluingStatus(str, Enum):
    """Whether a local result was glued to the global object.

    ``GLUING_NOT_ASSESSED`` fails closed: an unassessed gluing is never reported
    as a local-only result, because those are different observations.
    """

    LOCAL_ONLY = "LOCAL_ONLY"
    GLUED_TO_GLOBAL = "GLUED_TO_GLOBAL"
    GLUING_OBSTRUCTED = "GLUING_OBSTRUCTED"
    GLUING_NOT_ASSESSED = "GLUING_NOT_ASSESSED"


class RoutingInfluenceKind(str, Enum):
    PRIOR_TOOL = "PRIOR_TOOL"
    PRIOR_FAILURE = "PRIOR_FAILURE"
    PRIOR_EPISODE = "PRIOR_EPISODE"


class MethodTelemetryVerdict(str, Enum):
    """Integrity of the telemetry record, separate from what it reports.

    A record that honestly reports an unattributed failure or an unassessed
    gluing is ``RECORDED_PROPOSAL_ONLY``; the gap travels in the typed field.
    """

    RECORDED_PROPOSAL_ONLY = "RECORDED_PROPOSAL_ONLY"
    REFUTED_CLAIM = "REFUTED_CLAIM"
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


def artifact_canonical_sha256(document: Mapping[str, Any]) -> str:
    """Hash a telemetry document excluding its own content-hash field."""

    subject = dict(document)
    subject.pop("artifact_hash", None)
    return canonical_json_sha256(subject)


def bounded_rationale_reasons(label: str, text: str) -> Tuple[str, ...]:
    """Reject anything that is not a single-line bounded decision record.

    The single-line rule is the load-bearing one.  A chain-of-thought transcript
    is inherently multi-line; a decision record is one statement.  Together with
    the character cap this leaves no field in the object that a reasoning
    transcript can be written into.
    """

    if not text.strip():
        return (f"{label}_missing",)
    reasons: list[str] = []
    if _LINE_BREAK_RE.search(text):
        reasons.append(f"{label}_is_not_a_single_line_decision_record")
    if len(text) > _MAX_RATIONALE_CHARS:
        reasons.append(f"{label}_exceeds_bounded_rationale_length")
    return tuple(reasons)


@dataclass(frozen=True)
class EpisodeBinding:
    """Observed identity of the task episode this telemetry interprets.

    Supplied by whoever read the episode, never read from the substrate by this
    module.  ``artifact_hash`` is treated as an opaque bound identifier: its
    format is the episode object's contract, not this object's, so it is
    compared for equality and never reinterpreted here.
    """

    episode_id: str
    artifact_hash: str
    fibre_snapshot_hash: str
    outcome_is_failure: bool


@dataclass(frozen=True)
class ConsultedFibreItem:
    """One fibre item actually opened, not just the aggregate snapshot hash."""

    item_id: str
    item_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "item_hash": self.item_hash}


@dataclass(frozen=True)
class RoutingInfluence:
    """Prior experience that materially changed where the search went next."""

    kind: RoutingInfluenceKind
    reference_id: str
    effect_on_routing: str
    evidence_pointer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "reference_id": self.reference_id,
            "effect_on_routing": self.effect_on_routing,
            "evidence_pointer": self.evidence_pointer,
        }


@dataclass(frozen=True)
class RejectedCandidate:
    """A candidate that retrieval surfaced and the agent did not carry forward."""

    candidate_id: str
    rejection_reason: str
    evidence_pointer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "rejection_reason": self.rejection_reason,
            "evidence_pointer": self.evidence_pointer,
        }


@dataclass(frozen=True)
class ConsideredAlternative:
    """An operator or motif weighed and not selected."""

    alternative_id: str
    kind: str
    not_selected_because: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "alternative_id": self.alternative_id,
            "kind": self.kind,
            "not_selected_because": self.not_selected_because,
        }


@dataclass(frozen=True)
class SearchPolicyDecision:
    """The control decision that selected the next action."""

    policy_id: str
    policy_version: str
    selected_action_id: str
    selection_rule: str
    expected_discriminator: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "selected_action_id": self.selected_action_id,
            "selection_rule": self.selection_rule,
            "expected_discriminator": self.expected_discriminator,
        }


@dataclass(frozen=True)
class SaturationAxisDelta:
    """Movement on one saturation axis, with reopening recorded explicitly."""

    axis_id: str
    before: float
    after: float
    reopened: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis_id": self.axis_id,
            "before": self.before,
            "after": self.after,
            "reopened": self.reopened,
        }


@dataclass(frozen=True)
class StructuralNoveltyMetrology:
    """A named novelty measure against a named baseline.

    Every component must be supplied: there is no default score, because a
    novelty number with no stated measure or baseline is not a measurement.
    """

    measure_id: str
    score: float
    baseline_reference: str
    method_reference: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "measure_id": self.measure_id,
            "score": self.score,
            "baseline_reference": self.baseline_reference,
            "method_reference": self.method_reference,
        }


@dataclass(frozen=True)
class MethodTelemetry:
    """Typed decision record for one episode, bound immutably to that episode."""

    telemetry_id: str
    episode_id: str
    episode_artifact_hash: str
    fibre_snapshot_hash: str
    public_trace_event_id: str
    failure_class: MethodFailureClass
    gluing_status: GluingStatus
    next_action_id: str
    claim_boundary: str
    consulted_fibre_items: Tuple[ConsultedFibreItem, ...] = ()
    routing_influences: Tuple[RoutingInfluence, ...] = ()
    rejected_candidates: Tuple[RejectedCandidate, ...] = ()
    considered_alternatives: Tuple[ConsideredAlternative, ...] = ()
    search_policy_decision: SearchPolicyDecision | None = None
    saturation_axis_deltas: Tuple[SaturationAxisDelta, ...] = ()
    reopened_axis_ids: Tuple[str, ...] = ()
    structural_novelty: StructuralNoveltyMetrology | None = None
    child_atom_id: str | None = None
    coverage_receipt_id: str | None = None
    coverage_receipt_hash: str | None = None
    failure_evidence_pointers: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    artifact_hash: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "telemetry_id": self.telemetry_id,
            "episode_id": self.episode_id,
            "episode_artifact_hash": self.episode_artifact_hash,
            "fibre_snapshot_hash": self.fibre_snapshot_hash,
            "public_trace_event_id": self.public_trace_event_id,
            "failure_class": self.failure_class.value,
            "gluing_status": self.gluing_status.value,
            "next_action_id": self.next_action_id,
            "claim_boundary": self.claim_boundary,
            "consulted_fibre_items": [i.to_dict() for i in self.consulted_fibre_items],
            "routing_influences": [i.to_dict() for i in self.routing_influences],
            "rejected_candidates": [i.to_dict() for i in self.rejected_candidates],
            "considered_alternatives": [
                i.to_dict() for i in self.considered_alternatives
            ],
            "search_policy_decision": (
                self.search_policy_decision.to_dict()
                if self.search_policy_decision is not None
                else None
            ),
            "saturation_axis_deltas": [
                i.to_dict() for i in self.saturation_axis_deltas
            ],
            "reopened_axis_ids": list(self.reopened_axis_ids),
            "structural_novelty": (
                self.structural_novelty.to_dict()
                if self.structural_novelty is not None
                else None
            ),
            "child_atom_id": self.child_atom_id,
            "coverage_receipt_id": self.coverage_receipt_id,
            "coverage_receipt_hash": self.coverage_receipt_hash,
            "failure_evidence_pointers": list(self.failure_evidence_pointers),
            "evidence_pointers": list(self.evidence_pointers),
            "artifact_hash": self.artifact_hash,
            "contains_private_reasoning_transcript": False,
            "grants_chain_of_thought_disclosure": False,
            "grants_theorem_authority": False,
            "grants_tool_promotion": False,
            "grants_gluing_authority": False,
            "grants_review_independence": False,
        }

    def with_content_hash(self) -> "MethodTelemetry":
        """Return a copy carrying its own canonical content hash."""

        return replace(self, artifact_hash=artifact_canonical_sha256(self.to_dict()))


@dataclass(frozen=True)
class MethodTelemetryReport:
    verdict: MethodTelemetryVerdict
    reasons: Tuple[str, ...]

    @property
    def permits_failure_attribution_study(self) -> bool:
        """A record only supports failure attribution once a cause is named."""

        return (
            self.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
            and "failure_observed_but_not_attributed" not in self.reasons
        )

    @property
    def grants_theorem_authority(self) -> bool:
        return False

    @property
    def grants_tool_promotion(self) -> bool:
        return False

    @property
    def grants_gluing_authority(self) -> bool:
        return False

    @property
    def discloses_private_reasoning(self) -> bool:
        return False


def _rationale_reasons(telemetry: MethodTelemetry) -> Tuple[str, ...]:
    reasons: list[str] = []
    for influence in telemetry.routing_influences:
        reasons.extend(
            bounded_rationale_reasons(
                f"routing_influence:{influence.reference_id}:effect_on_routing",
                influence.effect_on_routing,
            )
        )
    for candidate in telemetry.rejected_candidates:
        reasons.extend(
            bounded_rationale_reasons(
                f"rejected_candidate:{candidate.candidate_id}:rejection_reason",
                candidate.rejection_reason,
            )
        )
    for alternative in telemetry.considered_alternatives:
        reasons.extend(
            bounded_rationale_reasons(
                f"considered_alternative:{alternative.alternative_id}:not_selected_because",
                alternative.not_selected_because,
            )
        )
    # claim_boundary is prose the author writes, so it is guarded too: it is the
    # only other free-text field, and leaving it unbounded would make the
    # object's no-transcript property false.
    reasons.extend(
        bounded_rationale_reasons("claim_boundary", telemetry.claim_boundary)
    )
    decision = telemetry.search_policy_decision
    if decision is not None:
        reasons.extend(
            bounded_rationale_reasons(
                "search_policy_decision:selection_rule", decision.selection_rule
            )
        )
        reasons.extend(
            bounded_rationale_reasons(
                "search_policy_decision:expected_discriminator",
                decision.expected_discriminator,
            )
        )
    return tuple(reasons)


def _size_reasons(telemetry: MethodTelemetry) -> Tuple[str, ...]:
    collections: Sequence[tuple[str, Sequence[object]]] = (
        ("consulted_fibre_items", telemetry.consulted_fibre_items),
        ("routing_influences", telemetry.routing_influences),
        ("rejected_candidates", telemetry.rejected_candidates),
        ("considered_alternatives", telemetry.considered_alternatives),
        ("saturation_axis_deltas", telemetry.saturation_axis_deltas),
    )
    return tuple(
        f"{name}_exceeds_decision_record_bound"
        for name, items in collections
        if len(items) > _MAX_DECISION_ENTRIES
    )


def _structural_reasons(telemetry: MethodTelemetry) -> Tuple[str, ...]:
    reasons: list[str] = []
    if telemetry.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    for name, value in (
        ("telemetry_id", telemetry.telemetry_id),
        ("episode_id", telemetry.episode_id),
        ("episode_artifact_hash", telemetry.episode_artifact_hash),
        ("fibre_snapshot_hash", telemetry.fibre_snapshot_hash),
        ("public_trace_event_id", telemetry.public_trace_event_id),
        ("next_action_id", telemetry.next_action_id),
        ("claim_boundary", telemetry.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not telemetry.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    if (telemetry.coverage_receipt_id is None) != (
        telemetry.coverage_receipt_hash is None
    ):
        reasons.append("coverage_receipt_reference_incompletely_bound")
    duplicate_axes = len({d.axis_id for d in telemetry.saturation_axis_deltas}) != len(
        telemetry.saturation_axis_deltas
    )
    if duplicate_axes:
        reasons.append("duplicate_saturation_axis_delta")
    if not telemetry.artifact_hash:
        reasons.append("artifact_hash_missing")
    elif not _SHA256_RE.match(telemetry.artifact_hash):
        reasons.append("artifact_hash_malformed")
    return tuple(reasons)


def audit_method_telemetry(
    telemetry: MethodTelemetry | None,
    *,
    episode: EpisodeBinding | None,
) -> MethodTelemetryReport:
    """Verify the episode link, the rationale bound and internal consistency.

    Deliberately not a richness gate: an ordinary episode with nothing notable
    produces a small, valid record.  The checks are consistency checks — a
    telemetry that contradicts its own fields or its bound episode fails; a
    telemetry that simply has little to report does not.
    """

    if telemetry is None:
        return MethodTelemetryReport(
            MethodTelemetryVerdict.CANNOT_CHECK, ("method_telemetry_missing",)
        )
    if episode is None:
        return MethodTelemetryReport(
            MethodTelemetryVerdict.CANNOT_CHECK, ("bound_episode_not_observed",)
        )

    unverifiable = (
        _structural_reasons(telemetry)
        + _rationale_reasons(telemetry)
        + _size_reasons(telemetry)
    )
    if unverifiable:
        return MethodTelemetryReport(
            MethodTelemetryVerdict.CANNOT_CHECK, unverifiable
        )

    if telemetry.artifact_hash != artifact_canonical_sha256(telemetry.to_dict()):
        return MethodTelemetryReport(
            MethodTelemetryVerdict.REFUTED_CLAIM, ("artifact_hash_mismatch",)
        )

    refuting: list[str] = []
    if telemetry.episode_id != episode.episode_id:
        refuting.append("telemetry_bound_to_a_different_episode")
    if telemetry.episode_artifact_hash != episode.artifact_hash:
        refuting.append("episode_artifact_hash_changed_since_telemetry")
    if telemetry.fibre_snapshot_hash != episode.fibre_snapshot_hash:
        refuting.append("fibre_snapshot_hash_does_not_match_bound_episode")

    declared_reopened = set(telemetry.reopened_axis_ids)
    observed_reopened = {d.axis_id for d in telemetry.saturation_axis_deltas if d.reopened}
    if declared_reopened != observed_reopened:
        refuting.append("reopened_axis_ids_contradict_saturation_axis_deltas")

    # Only one direction is a contradiction.  A failed episode reported as
    # NO_FAILURE_OBSERVED denies the evidence root.  The converse — an episode
    # that succeeded while telemetry attributes a failure class — is a normal
    # recovered sub-step, so it is recorded as scope, never refuted.
    if (
        episode.outcome_is_failure
        and telemetry.failure_class is MethodFailureClass.NO_FAILURE_OBSERVED
    ):
        refuting.append("failure_class_contradicts_bound_episode_outcome")

    if refuting:
        return MethodTelemetryReport(
            MethodTelemetryVerdict.REFUTED_CLAIM, tuple(refuting)
        )

    notes: list[str] = []
    # Not gated on the episode outcome.  Because a successful episode may
    # legitimately attribute a recovered sub-step failure, an *unclassified*
    # sub-step failure is equally reachable there.  Being unattributed is a
    # property of the failure class alone.
    if telemetry.failure_class is MethodFailureClass.UNCLASSIFIED_FAILURE:
        notes.append("failure_observed_but_not_attributed")
    if telemetry.gluing_status is GluingStatus.GLUING_NOT_ASSESSED:
        notes.append("gluing_status_not_assessed")
    if (
        telemetry.failure_class in _ATTRIBUTED_FAILURE_CLASSES
        and not telemetry.failure_evidence_pointers
    ):
        notes.append("failure_attributed_without_evidence_pointers")

    return MethodTelemetryReport(
        MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY,
        tuple(notes)
        + (
            "telemetry is immutably bound to the observed episode identity",
            "records reproducible decision variables only; no private reasoning transcript",
            "mints no theorem, tool, gluing, review-independence or framework authority",
        ),
    )
