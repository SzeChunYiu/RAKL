"""Frozen planted-world tests for the proposal-only method telemetry record.

Every fail-closed assertion is paired with a no-alarm assertion, so a checker that
always fires would fail here.  The mandatory no-alarm control is explicit: an
ordinary episode with nothing rejected and nothing reconsidered must produce a
valid, small record with no reasons at all.

The disclosure-boundary tests are deliberately not "assert no reasoning field
exists" — that passes trivially.  They plant an actual pasted transcript in a
bounded note and require the audit to refute it, and they smuggle a narrative key
past the dataclass into the serialized document and require the schema to reject
it.

All identifiers are synthetic.  No application mathematics is imported.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from rakl.method_telemetry import (
    MAX_NOTE_CHARS,
    RECORD_SCHEMA_VERSION,
    AlternativeConsidered,
    AlternativeKind,
    ConsultedFibreItem,
    CoverageReceiptRef,
    DisclosureStatus,
    FailureCategory,
    FibreItemRole,
    GluingRecord,
    GluingStatus,
    MethodTelemetryRecord,
    NextActionPointer,
    NoveltyClass,
    RecordedSetStatus,
    RejectedCandidate,
    RejectionReason,
    RoutingInfluence,
    RoutingInfluenceKind,
    SaturationAxisDelta,
    SaturationDelta,
    SearchPolicyDecision,
    SearchPolicyKind,
    StructuralNoveltyMetrology,
    TelemetryVerdict,
    audit_method_telemetry,
    record_canonical_sha256,
)


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "method-telemetry-record-v1.schema.json"
)

EPISODE_ID = "episode::synthetic-cycle::0007"
EPISODE_HASH = "3f2b1c0d4e5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0"
ITEM_HASH_A = "11a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80"
ITEM_HASH_B = "22b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091"
COVERAGE_HASH = "9c8b7a695847362514f3e2d1c0b9a8978695847362514f3e2d1c0b9a89786958"

CLAIM_BOUNDARY = (
    "method-process telemetry only; interprets one immutable episode, mints no "
    "method authority, and makes no search-completeness claim"
)


def _plain_record(**overrides: Any) -> MethodTelemetryRecord:
    """No-alarm control: an ordinary episode with nothing notable to report."""

    values: dict[str, Any] = {
        "episode_id": EPISODE_ID,
        "episode_artifact_hash": EPISODE_HASH,
        "task_id": "task::synthetic::routine-check",
        "atom_id": "atom::synthetic::0007",
        "public_trace_event_id": "trace::RESULT_RECORDED::0007",
        "claim_boundary": CLAIM_BOUNDARY,
        "consulted_items_status": RecordedSetStatus.ITEMS_RECORDED,
        "routing_influence_status": RecordedSetStatus.NONE_OCCURRED,
        "rejected_candidates_status": RecordedSetStatus.NONE_OCCURRED,
        "alternatives_status": RecordedSetStatus.NONE_OCCURRED,
        "failure_category": FailureCategory.NONE,
        "search_policy_decision": SearchPolicyDecision(
            policy_kind=SearchPolicyKind.DEFAULT_SEQUENTIAL,
            selected_action_id="action::synthetic::rerun-verification",
        ),
        "gluing": GluingRecord(status=GluingStatus.NOT_APPLICABLE),
        "novelty": StructuralNoveltyMetrology(
            novelty_class=NoveltyClass.NOT_ASSESSED
        ),
        "next_action": NextActionPointer(
            next_action_id="action::synthetic::close-atom"
        ),
        "consulted_fibre_items": (
            ConsultedFibreItem(
                item_id="fibre::synthetic::definition-a",
                item_content_hash=ITEM_HASH_A,
                role=FibreItemRole.DEFINITION,
            ),
        ),
        "evidence_pointers": ("trace::0007",),
    }
    values.update(overrides)
    return MethodTelemetryRecord(**values).with_content_hash()


def _rich_record(**overrides: Any) -> MethodTelemetryRecord:
    """A consequential episode exercising every decision variable named by #125."""

    values: dict[str, Any] = {
        "episode_id": EPISODE_ID,
        "episode_artifact_hash": EPISODE_HASH,
        "task_id": "task::synthetic::representation-prune",
        "atom_id": "atom::synthetic::0011",
        "public_trace_event_id": "trace::NEXT_STEP_PROPOSED::0011",
        "claim_boundary": CLAIM_BOUNDARY,
        "consulted_items_status": RecordedSetStatus.ITEMS_RECORDED,
        "routing_influence_status": RecordedSetStatus.ITEMS_RECORDED,
        "rejected_candidates_status": RecordedSetStatus.ITEMS_RECORDED,
        "alternatives_status": RecordedSetStatus.ITEMS_RECORDED,
        "failure_category": FailureCategory.REPRESENTATION,
        "failure_note": "richer representation collapsed to the coarser invariant",
        "search_policy_decision": SearchPolicyDecision(
            policy_kind=SearchPolicyKind.CHEAPEST_FALSIFIER_FIRST,
            selected_action_id="action::synthetic::congruence-audit",
            decision_note="cheapest audit discriminates the two representations",
            considered_alternative_ids=("alt::synthetic::enumerate-candidates",),
        ),
        "gluing": GluingRecord(
            status=GluingStatus.LOCAL_CONSISTENT_GLOBAL_UNTESTED,
            local_scope_id="scope::synthetic::fixed-parameter",
            global_scope_id=None,
            note="local result not yet tested outside the fixed parameter",
        ),
        "novelty": StructuralNoveltyMetrology(
            novelty_class=NoveltyClass.RECOMBINATION_OF_KNOWN,
            comparison_basis_ids=("tool::synthetic::projection-audit",),
            changed_structural_coordinates=("coordinate::synthetic::rank",),
            note="known projection composed with a known congruence test",
        ),
        "next_action": NextActionPointer(
            next_action_id="action::synthetic::refine-projection",
            child_atom_id="atom::synthetic::0011-a",
            rationale_note="prune the representation before inventing candidates",
        ),
        "consulted_fibre_items": (
            ConsultedFibreItem(
                item_id="fibre::synthetic::definition-a",
                item_content_hash=ITEM_HASH_A,
                role=FibreItemRole.DEFINITION,
            ),
            ConsultedFibreItem(
                item_id="fibre::synthetic::counterexample-b",
                item_content_hash=ITEM_HASH_B,
                role=FibreItemRole.COUNTEREXAMPLE,
            ),
        ),
        "routing_influences": (
            RoutingInfluence(
                kind=RoutingInfluenceKind.PRIOR_FAILURE,
                reference_id="failure::synthetic::0003",
                changed_action=True,
                note="prior failure ruled out the direct enumeration route",
            ),
            RoutingInfluence(
                kind=RoutingInfluenceKind.PRIOR_TOOL,
                reference_id="tool::synthetic::projection-audit",
                changed_action=False,
                note="consulted but did not redirect",
            ),
        ),
        "rejected_candidates": (
            RejectedCandidate(
                candidate_id="candidate::synthetic::source-native-closure",
                retrieval_source="inventory::synthetic::tools",
                reason_code=RejectionReason.STRUCTURAL_COORDINATE_MISMATCH,
                note="collapses under the fixed-parameter congruence test",
            ),
            RejectedCandidate(
                candidate_id="candidate::synthetic::wide-enumeration",
                retrieval_source="inventory::synthetic::tools",
                reason_code=RejectionReason.COST_EXCEEDS_BUDGET,
            ),
        ),
        "alternatives_considered": (
            AlternativeConsidered(
                alternative_id="alt::synthetic::congruence-audit",
                kind=AlternativeKind.FALSIFIER,
                selected=True,
            ),
            AlternativeConsidered(
                alternative_id="alt::synthetic::enumerate-candidates",
                kind=AlternativeKind.OPERATOR,
                selected=False,
                reason_code=RejectionReason.COST_EXCEEDS_BUDGET,
                note="deferred until the representation is pruned",
            ),
        ),
        "saturation_axis_deltas": (
            SaturationAxisDelta(
                axis_id="axis::synthetic::representation",
                delta=SaturationDelta.REOPENED,
                note="coarser invariant reopened the representation axis",
            ),
            SaturationAxisDelta(
                axis_id="axis::synthetic::verification",
                delta=SaturationDelta.ADVANCED,
            ),
        ),
        "reopened_saturation_axis_ids": ("axis::synthetic::representation",),
        "coverage_receipt_ref": CoverageReceiptRef(
            synthesis_id="synthesis::synthetic::0002",
            receipt_canonical_sha256=COVERAGE_HASH,
        ),
        "evidence_pointers": ("trace::0011", "artifact::synthetic::audit-log"),
    }
    values.update(overrides)
    return MethodTelemetryRecord(**values).with_content_hash()


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


# --------------------------------------------------------------------------
# Mandatory no-alarm control
# --------------------------------------------------------------------------


def test_ordinary_episode_records_cleanly_and_is_not_flagged(
    validator: Draft202012Validator,
) -> None:
    """An episode with nothing notable must record without any reason at all."""

    record = _plain_record()
    report = audit_method_telemetry(
        record,
        episode_id=EPISODE_ID,
        episode_artifact_hash=EPISODE_HASH,
    )

    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert report.disclosure_status is DisclosureStatus.BOUNDED_DECISION_RECORD
    assert report.reasons == ()
    assert report.recorded is True
    validator.validate(record.to_dict())


def test_ordinary_episode_record_stays_small() -> None:
    """The no-alarm record must not impose a large bookkeeping payload.

    #125's own evaluation contract measures log overhead and performative
    bookkeeping, so an ordinary episode that costs kilobytes would be a defect.
    """

    plain = len(
        json.dumps(_plain_record().to_dict(), separators=(",", ":")).encode("utf-8")
    )
    rich = len(
        json.dumps(_rich_record().to_dict(), separators=(",", ":")).encode("utf-8")
    )
    assert plain < 2048
    assert plain * 2 < rich


def test_nothing_rejected_is_expressible_without_inventing_records() -> None:
    """``NONE_OCCURRED`` is a positive statement, distinct from ``UNRECORDED``."""

    record = _plain_record()
    assert record.rejected_candidates_status is RecordedSetStatus.NONE_OCCURRED
    assert record.rejected_candidates == ()
    assert audit_method_telemetry(record).reasons == ()

    unrecorded = _plain_record(
        rejected_candidates_status=RecordedSetStatus.UNRECORDED
    )
    report = audit_method_telemetry(unrecorded)
    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "rejected_candidates_unrecorded" in report.reasons


# --------------------------------------------------------------------------
# Disclosure boundary: no private chain-of-thought
# --------------------------------------------------------------------------


def test_pasted_reasoning_transcript_in_a_bounded_note_is_refuted() -> None:
    """Planted world: a long reasoning transcript pasted into a rationale slot."""

    transcript = "first I considered the projection, then I realised " * 100
    assert len(transcript) > MAX_NOTE_CHARS
    record = _rich_record(
        next_action=NextActionPointer(
            next_action_id="action::synthetic::refine-projection",
            rationale_note=transcript,
        )
    )

    report = audit_method_telemetry(record)
    assert report.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert report.disclosure_status is DisclosureStatus.REASONING_TRANSCRIPT_SUSPECTED
    assert "next_action_rationale_note_exceeds_bounded_length" in report.reasons


def test_short_multiline_narrative_is_refuted() -> None:
    """A transcript that is short still fails: a decision note is one line."""

    record = _rich_record(
        gluing=GluingRecord(
            status=GluingStatus.LOCAL_ONLY,
            local_scope_id="scope::synthetic::fixed-parameter",
            note="step 1: try X\nstep 2: X failed\nstep 3: try Y",
        )
    )

    report = audit_method_telemetry(record)
    assert report.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert report.disclosure_status is DisclosureStatus.REASONING_TRANSCRIPT_SUSPECTED
    assert "gluing_note_is_multiline_narrative" in report.reasons


def test_every_bounded_note_slot_is_covered_by_the_disclosure_check() -> None:
    """No rationale slot may be an unbounded back door."""

    overlong = "x" * (MAX_NOTE_CHARS + 1)
    planted: tuple[tuple[str, dict[str, Any]], ...] = (
        ("claim_boundary_exceeds_bounded_length", {"claim_boundary": overlong}),
        ("failure_note_exceeds_bounded_length", {"failure_note": overlong}),
        (
            "search_policy_decision_note_exceeds_bounded_length",
            {
                "search_policy_decision": SearchPolicyDecision(
                    policy_kind=SearchPolicyKind.CHEAPEST_FALSIFIER_FIRST,
                    selected_action_id="action::synthetic::congruence-audit",
                    decision_note=overlong,
                )
            },
        ),
        (
            "novelty_note_exceeds_bounded_length",
            {
                "novelty": StructuralNoveltyMetrology(
                    novelty_class=NoveltyClass.NOT_ASSESSED, note=overlong
                )
            },
        ),
        (
            "routing_influence_note_exceeds_bounded_length",
            {
                "routing_influences": (
                    RoutingInfluence(
                        kind=RoutingInfluenceKind.PRIOR_TOOL,
                        reference_id="tool::synthetic::projection-audit",
                        changed_action=False,
                        note=overlong,
                    ),
                )
            },
        ),
        (
            "rejected_candidate_note_exceeds_bounded_length",
            {
                "rejected_candidates": (
                    RejectedCandidate(
                        candidate_id="candidate::synthetic::wide-enumeration",
                        retrieval_source="inventory::synthetic::tools",
                        reason_code=RejectionReason.COST_EXCEEDS_BUDGET,
                        note=overlong,
                    ),
                )
            },
        ),
        (
            "alternative_note_exceeds_bounded_length",
            {
                "alternatives_considered": (
                    AlternativeConsidered(
                        alternative_id="alt::synthetic::enumerate-candidates",
                        kind=AlternativeKind.OPERATOR,
                        selected=True,
                        note=overlong,
                    ),
                )
            },
        ),
        (
            "saturation_axis_note_exceeds_bounded_length",
            {
                "saturation_axis_deltas": (
                    SaturationAxisDelta(
                        axis_id="axis::synthetic::verification",
                        delta=SaturationDelta.ADVANCED,
                        note=overlong,
                    ),
                ),
                "reopened_saturation_axis_ids": (),
            },
        ),
    )

    for expected_reason, override in planted:
        report = audit_method_telemetry(_rich_record(**override))
        assert report.verdict is TelemetryVerdict.REFUTED_CLAIM, expected_reason
        assert (
            report.disclosure_status is DisclosureStatus.REASONING_TRANSCRIPT_SUSPECTED
        ), expected_reason
        assert expected_reason in report.reasons


def test_schema_rejects_a_smuggled_reasoning_field(
    validator: Draft202012Validator,
) -> None:
    """The serialized document has no slot for a free-form reasoning transcript."""

    document = _rich_record().to_dict()
    validator.validate(document)

    for smuggled_key in ("reasoning", "thoughts", "chain_of_thought", "scratchpad"):
        polluted = dict(document)
        polluted[smuggled_key] = "long internal deliberation text"
        with pytest.raises(ValidationError):
            validator.validate(polluted)


def test_schema_rejects_unbounded_and_multiline_notes(
    validator: Draft202012Validator,
) -> None:
    """The schema enforces the same boundary as the runtime, independently."""

    document = _rich_record().to_dict()
    validator.validate(document)

    overlong = dict(document)
    overlong["failure_note"] = "x" * (MAX_NOTE_CHARS + 1)
    with pytest.raises(ValidationError):
        validator.validate(overlong)

    for narrative in ("line one\nline two", "trailing newline\n", "carriage\rreturn"):
        multiline = dict(document)
        multiline["failure_note"] = narrative
        with pytest.raises(ValidationError):
            validator.validate(multiline)


def test_record_never_claims_to_expose_hidden_reasoning() -> None:
    record = _rich_record()
    assert record.discloses_private_chain_of_thought is False
    assert record.grants_method_authority is False
    assert record.to_dict()["discloses_private_chain_of_thought"] is False


# --------------------------------------------------------------------------
# Separation from the immutable evidence root
# --------------------------------------------------------------------------


def test_record_is_not_an_evidence_root() -> None:
    """The record interprets an episode; it never becomes a second evidence root."""

    record = _rich_record()
    assert record.is_episode_evidence_root is False
    assert record.episode_id == EPISODE_ID
    assert record.episode_artifact_hash == EPISODE_HASH


def test_rebinding_to_another_episode_is_detected() -> None:
    """Planted world: telemetry reattached to a different episode."""

    record = _rich_record()

    other_id = audit_method_telemetry(
        record,
        episode_id="episode::synthetic-cycle::9999",
        episode_artifact_hash=EPISODE_HASH,
    )
    assert other_id.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert "telemetry_bound_to_other_episode" in other_id.reasons

    other_content = audit_method_telemetry(
        record,
        episode_id=EPISODE_ID,
        episode_artifact_hash="0" * 64,
    )
    assert other_content.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert "telemetry_bound_to_other_episode_content" in other_content.reasons

    # No-alarm: the correct binding is accepted.
    assert audit_method_telemetry(
        record, episode_id=EPISODE_ID, episode_artifact_hash=EPISODE_HASH
    ).verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY


# --------------------------------------------------------------------------
# Fail-closed integrity
# --------------------------------------------------------------------------


def test_missing_record_cannot_check() -> None:
    report = audit_method_telemetry(None)
    assert report.verdict is TelemetryVerdict.CANNOT_CHECK
    assert report.disclosure_status is DisclosureStatus.UNCHECKED
    assert report.reasons == ("method_telemetry_record_missing",)


@pytest.mark.parametrize(
    ("override", "expected_reason"),
    [
        ({"episode_artifact_hash": "not-a-hash"}, "episode_artifact_hash_invalid"),
        ({"episode_artifact_hash": "A" * 64}, "episode_artifact_hash_invalid"),
        ({"evidence_pointers": ()}, "evidence_pointers_missing"),
        ({"atom_id": "  "}, "atom_id_missing"),
        ({"schema_version": "method-telemetry-record-v0"}, "schema_version_unsupported"),
        (
            {
                "coverage_receipt_ref": CoverageReceiptRef(
                    synthesis_id="synthesis::synthetic::0002",
                    receipt_canonical_sha256="short",
                )
            },
            "coverage_receipt_ref_binding_invalid",
        ),
        (
            {
                "consulted_fibre_items": (
                    ConsultedFibreItem(
                        item_id="fibre::synthetic::definition-a",
                        item_content_hash="nope",
                        role=FibreItemRole.DEFINITION,
                    ),
                )
            },
            "consulted_fibre_item_binding_invalid",
        ),
    ],
)
def test_malformed_bindings_cannot_check(
    override: dict[str, Any], expected_reason: str
) -> None:
    report = audit_method_telemetry(_rich_record(**override))
    assert report.verdict is TelemetryVerdict.CANNOT_CHECK
    assert report.disclosure_status is DisclosureStatus.UNCHECKED
    assert expected_reason in report.reasons


def test_content_hash_states_are_distinguished() -> None:
    record = _rich_record()

    missing = replace(record, record_canonical_sha256="")
    assert audit_method_telemetry(missing).reasons == (
        "record_canonical_sha256_missing",
    )
    assert audit_method_telemetry(missing).verdict is TelemetryVerdict.CANNOT_CHECK

    malformed = replace(record, record_canonical_sha256="zz")
    assert audit_method_telemetry(malformed).verdict is TelemetryVerdict.CANNOT_CHECK
    assert "record_canonical_sha256_malformed" in audit_method_telemetry(
        malformed
    ).reasons

    # A silent payload edit after hashing is a refuted claim, not a soft warning.
    tampered = replace(record, task_id="task::synthetic::rewritten")
    report = audit_method_telemetry(tampered)
    assert report.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert report.reasons == ("record_canonical_sha256_mismatch",)


def test_content_hash_is_derived_and_stable() -> None:
    record = _rich_record()
    assert record.record_canonical_sha256 == record_canonical_sha256(record.to_dict())
    assert record.with_content_hash() == record
    assert record.schema_version == RECORD_SCHEMA_VERSION


# --------------------------------------------------------------------------
# Declared-set and payload contradictions
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("override", "expected_reason"),
    [
        (
            {"rejected_candidates_status": RecordedSetStatus.NONE_OCCURRED},
            "rejected_candidates_declared_none_but_present",
        ),
        (
            {"alternatives_status": RecordedSetStatus.NONE_OCCURRED},
            "alternatives_declared_none_but_present",
        ),
        (
            {
                "routing_influence_status": RecordedSetStatus.ITEMS_RECORDED,
                "routing_influences": (),
            },
            "routing_influence_declared_recorded_but_empty",
        ),
        (
            {
                "consulted_items_status": RecordedSetStatus.ITEMS_RECORDED,
                "consulted_fibre_items": (),
            },
            "consulted_items_declared_recorded_but_empty",
        ),
    ],
)
def test_declared_set_status_must_match_the_recorded_set(
    override: dict[str, Any], expected_reason: str
) -> None:
    report = audit_method_telemetry(_rich_record(**override))
    assert report.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert expected_reason in report.reasons
    # The contradiction is a bookkeeping conflict, not a disclosure problem.
    assert report.disclosure_status is DisclosureStatus.BOUNDED_DECISION_RECORD


@pytest.mark.parametrize(
    ("override", "expected_reason"),
    [
        (
            {
                "alternatives_considered": (
                    AlternativeConsidered(
                        alternative_id="alt::synthetic::enumerate-candidates",
                        kind=AlternativeKind.OPERATOR,
                        selected=False,
                    ),
                )
            },
            "non_selected_alternative_missing_reason_code",
        ),
        (
            {
                "gluing": GluingRecord(
                    status=GluingStatus.GLOBAL_OBSTRUCTION_FOUND,
                    local_scope_id="scope::synthetic::fixed-parameter",
                )
            },
            "global_obstruction_claimed_without_obstruction_ids",
        ),
        (
            {
                "gluing": GluingRecord(
                    status=GluingStatus.GLOBALLY_GLUED,
                    local_scope_id="scope::synthetic::fixed-parameter",
                )
            },
            "global_gluing_claimed_without_global_scope",
        ),
        (
            {
                "novelty": StructuralNoveltyMetrology(
                    novelty_class=NoveltyClass.NEW_STRUCTURAL_COORDINATE,
                    changed_structural_coordinates=("coordinate::synthetic::rank",),
                )
            },
            "novelty_claimed_without_comparison_basis",
        ),
        (
            {
                "novelty": StructuralNoveltyMetrology(
                    novelty_class=NoveltyClass.NEW_STRUCTURAL_COORDINATE,
                    comparison_basis_ids=("tool::synthetic::projection-audit",),
                )
            },
            "new_structural_coordinate_claimed_without_named_coordinate",
        ),
        (
            {"reopened_saturation_axis_ids": ()},
            "reopened_axis_delta_not_declared",
        ),
        (
            {
                "reopened_saturation_axis_ids": (
                    "axis::synthetic::representation",
                    "axis::synthetic::ghost",
                )
            },
            "reopened_axis_declared_without_matching_delta",
        ),
        (
            {"failure_category": FailureCategory.NONE},
            "failure_note_present_without_failure_category",
        ),
    ],
)
def test_internal_contradictions_are_refuted(
    override: dict[str, Any], expected_reason: str
) -> None:
    report = audit_method_telemetry(_rich_record(**override))
    assert report.verdict is TelemetryVerdict.REFUTED_CLAIM
    assert expected_reason in report.reasons


def test_consistent_rich_record_is_not_flagged(
    validator: Draft202012Validator,
) -> None:
    """No-alarm control for the contradiction checks above."""

    report = audit_method_telemetry(
        _rich_record(),
        episode_id=EPISODE_ID,
        episode_artifact_hash=EPISODE_HASH,
    )
    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert report.disclosure_status is DisclosureStatus.BOUNDED_DECISION_RECORD
    assert report.reasons == ()
    validator.validate(_rich_record().to_dict())


# --------------------------------------------------------------------------
# Honest defects travel in the payload, not in the verdict
# --------------------------------------------------------------------------


def test_unclassified_failure_is_recorded_and_routed_not_refuted() -> None:
    """An honestly unclassified failure is a valid record with a routing note."""

    record = _rich_record(
        failure_category=FailureCategory.UNCLASSIFIED,
        failure_note="residual did not match any registered category",
    )
    report = audit_method_telemetry(record)

    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert (
        "failure_category_unclassified_route_to_metacognitive_auditor"
        in report.reasons
    )


def test_unrecorded_search_policy_is_reported_without_defaulting() -> None:
    record = _rich_record(
        search_policy_decision=SearchPolicyDecision(
            policy_kind=SearchPolicyKind.UNRECORDED,
            selected_action_id="action::synthetic::congruence-audit",
        )
    )
    report = audit_method_telemetry(record)

    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "search_policy_decision_unrecorded" in report.reasons
    # No-alarm: the ordinary default policy is not reported as a defect.
    assert "search_policy_decision_unrecorded" not in audit_method_telemetry(
        _plain_record()
    ).reasons


# --------------------------------------------------------------------------
# Composition with the cross-problem coverage receipt (#119)
# --------------------------------------------------------------------------


def test_coverage_receipt_is_referenced_not_reimplemented() -> None:
    """Telemetry points at a coverage receipt and mints no completeness claim."""

    record = _rich_record()
    assert record.coverage_receipt_ref is not None
    assert record.coverage_receipt_ref.receipt_canonical_sha256 == COVERAGE_HASH

    report = audit_method_telemetry(record)
    assert report.grants_search_completeness_claim is False
    assert report.grants_method_authority is False


def test_absent_coverage_reference_is_not_an_error() -> None:
    """#125 is composable with #119, not dependent on it."""

    report = audit_method_telemetry(_rich_record(coverage_receipt_ref=None))
    assert report.verdict is TelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert report.reasons == ()
