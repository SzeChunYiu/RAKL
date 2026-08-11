"""Frozen tests for proposal-only method telemetry.

Fixtures are synthetic atoms, tools and failure ids.  No application-side
mathematics enters framework authority.

Two properties carry most of the weight: the object cannot hold a private
reasoning transcript, and it is not a richness gate — an ordinary episode with
nothing notable must produce a small, valid record without being flagged.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from rakl.method_telemetry import (
    ConsideredAlternative,
    ConsultedFibreItem,
    EpisodeBinding,
    GluingStatus,
    MethodFailureClass,
    MethodTelemetry,
    MethodTelemetryVerdict,
    RejectedCandidate,
    RoutingInfluence,
    RoutingInfluenceKind,
    SaturationAxisDelta,
    SearchPolicyDecision,
    StructuralNoveltyMetrology,
    artifact_canonical_sha256,
    audit_method_telemetry,
    bounded_rationale_reasons,
)


EPISODE_ID = "episode::atom-A7::0003"
EPISODE_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
FIBRE_HASH = "9f2c1e0b7a4d5c6e8f0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f506"
CLAIM_BOUNDARY = (
    "framework-process observation only; reproducible decision records, no "
    "private reasoning transcript, no theorem/tool/gluing/review authority"
)
assert "\n" not in CLAIM_BOUNDARY


def _episode(**overrides: Any) -> EpisodeBinding:
    values: dict[str, Any] = {
        "episode_id": EPISODE_ID,
        "artifact_hash": EPISODE_HASH,
        "fibre_snapshot_hash": FIBRE_HASH,
        "outcome_is_failure": True,
    }
    values.update(overrides)
    return EpisodeBinding(**values)


def _telemetry(**overrides: Any) -> MethodTelemetry:
    """A rich episode: prior experience routed it, candidates were pruned."""

    values: dict[str, Any] = {
        "telemetry_id": "telemetry::atom-A7::0003",
        "episode_id": EPISODE_ID,
        "episode_artifact_hash": EPISODE_HASH,
        "fibre_snapshot_hash": FIBRE_HASH,
        "public_trace_event_id": "trace::NEXT_STEP_PROPOSED::0012",
        "failure_class": MethodFailureClass.REPRESENTATION,
        "gluing_status": GluingStatus.LOCAL_ONLY,
        "next_action_id": "action::refine-projection::0004",
        "claim_boundary": CLAIM_BOUNDARY,
        "consulted_fibre_items": (
            ConsultedFibreItem("fibre::analogy-scan::11", "hash-fibre-11"),
            ConsultedFibreItem("fibre::method-transfer::12", "hash-fibre-12"),
        ),
        "routing_influences": (
            RoutingInfluence(
                RoutingInfluenceKind.PRIOR_FAILURE,
                "F-projection-collapse",
                "prior collapse warning redirected search to a congruence test first",
                "failure::F-projection-collapse",
            ),
            RoutingInfluence(
                RoutingInfluenceKind.PRIOR_TOOL,
                "T-SOURCE-DEFINED-PROJECTION",
                "reused the source-defined projection but demanded target validation",
                "tool::T-SOURCE-DEFINED-PROJECTION",
            ),
        ),
        "rejected_candidates": (
            RejectedCandidate(
                "candidate::signature-representation",
                "congruence audit compressed rule activation to antecedent bits",
                "result::congruence-audit::0002",
            ),
        ),
        "considered_alternatives": (
            ConsideredAlternative(
                "operator::widen-basis",
                "operator",
                "widening the basis reopens an axis already refuted in this context",
            ),
        ),
        "search_policy_decision": SearchPolicyDecision(
            policy_id="policy::prune-before-invent",
            policy_version="v1",
            selected_action_id="action::refine-projection::0004",
            selection_rule="prune the representation before inventing a candidate",
            expected_discriminator="a hostile counterexample survives the refined projection",
        ),
        "saturation_axis_deltas": (
            SaturationAxisDelta("axis::representation", 0.7, 0.4, reopened=True),
            SaturationAxisDelta("axis::verification", 0.5, 0.6),
        ),
        "reopened_axis_ids": ("axis::representation",),
        "structural_novelty": StructuralNoveltyMetrology(
            measure_id="measure::motif-distance",
            score=0.31,
            baseline_reference="baseline::prior-motif-corpus",
            method_reference="method::structural-signature-distance",
        ),
        "child_atom_id": "atom::A7.1",
        "coverage_receipt_id": "synthesis::cross-lane-reuse-audit::0001",
        "coverage_receipt_hash": "a" * 64,
        "failure_evidence_pointers": ("result::congruence-audit::0002",),
        "evidence_pointers": ("episode::atom-A7::0003", "trace::0012"),
    }
    values.update(overrides)
    return MethodTelemetry(**values).with_content_hash()


def _ordinary_telemetry(**overrides: Any) -> MethodTelemetry:
    """The no-alarm control: an unremarkable episode, nothing notable to report."""

    values: dict[str, Any] = {
        "telemetry_id": "telemetry::atom-B2::0001",
        "episode_id": EPISODE_ID,
        "episode_artifact_hash": EPISODE_HASH,
        "fibre_snapshot_hash": FIBRE_HASH,
        "public_trace_event_id": "trace::RESULT_RECORDED::0001",
        "failure_class": MethodFailureClass.NO_FAILURE_OBSERVED,
        "gluing_status": GluingStatus.LOCAL_ONLY,
        "next_action_id": "action::continue::0002",
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_pointers": ("episode::atom-A7::0003",),
    }
    values.update(overrides)
    return MethodTelemetry(**values).with_content_hash()


# --- no-alarm controls -------------------------------------------------------


def test_ordinary_episode_produces_a_small_valid_record() -> None:
    """A checker that demands richness would fire here.  It must not."""

    report = audit_method_telemetry(
        _ordinary_telemetry(), episode=_episode(outcome_is_failure=False)
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert report.permits_failure_attribution_study is True

    document = _ordinary_telemetry().to_dict()
    assert document["routing_influences"] == []
    assert document["rejected_candidates"] == []
    assert document["search_policy_decision"] is None
    assert document["structural_novelty"] is None


def test_rich_episode_records_cleanly() -> None:
    report = audit_method_telemetry(_telemetry(), episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert report.permits_failure_attribution_study is True


# --- chain-of-thought is structurally excluded -------------------------------

_TRANSCRIPT = (
    "First I considered whether the projection was faithful.\n"
    "Then I worried the congruence might not be well defined.\n"
    "On reflection I decided to test antecedent membership instead."
)


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "routing_influences": (
                RoutingInfluence(
                    RoutingInfluenceKind.PRIOR_FAILURE,
                    "F-1",
                    _TRANSCRIPT,
                    "failure::F-1",
                ),
            )
        },
        {
            "rejected_candidates": (
                RejectedCandidate("candidate::x", _TRANSCRIPT, "result::1"),
            )
        },
        {
            "considered_alternatives": (
                ConsideredAlternative("operator::y", "operator", _TRANSCRIPT),
            )
        },
    ],
)
def test_no_field_can_hold_a_reasoning_transcript(overrides: dict[str, Any]) -> None:
    report = audit_method_telemetry(_telemetry(**overrides), episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert any(
        "is_not_a_single_line_decision_record" in reason for reason in report.reasons
    )


def test_policy_rationales_are_bounded_too() -> None:
    base = _telemetry()
    assert base.search_policy_decision is not None
    report = audit_method_telemetry(
        _telemetry(
            search_policy_decision=replace(
                base.search_policy_decision, selection_rule=_TRANSCRIPT
            )
        ),
        episode=_episode(),
    )
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert any("selection_rule" in reason for reason in report.reasons)


def test_an_oversized_single_line_rationale_is_still_rejected() -> None:
    report = audit_method_telemetry(
        _telemetry(
            rejected_candidates=(
                RejectedCandidate("candidate::x", "y" * 600, "result::1"),
            )
        ),
        episode=_episode(),
    )
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert any("exceeds_bounded_rationale_length" in r for r in report.reasons)


def test_a_transcript_cannot_be_smuggled_as_many_short_lines() -> None:
    report = audit_method_telemetry(
        _telemetry(
            rejected_candidates=tuple(
                RejectedCandidate(f"candidate::{i}", f"line {i} of narrative", "result::1")
                for i in range(65)
            )
        ),
        episode=_episode(),
    )
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert "rejected_candidates_exceeds_decision_record_bound" in report.reasons


def test_a_normal_rationale_with_spaces_and_punctuation_passes() -> None:
    """The guard must not fire on ordinary prose-free decision records."""

    assert (
        bounded_rationale_reasons(
            "x", "prior failure F-12 warned the projection collapses; rerouted."
        )
        == ()
    )


def test_object_declares_no_reasoning_disclosure() -> None:
    report = audit_method_telemetry(_telemetry(), episode=_episode())
    assert report.discloses_private_reasoning is False
    document = _telemetry().to_dict()
    assert document["contains_private_reasoning_transcript"] is False
    assert document["grants_chain_of_thought_disclosure"] is False


# --- immutable link to the episode -------------------------------------------


def test_missing_episode_observation_fails_closed() -> None:
    report = audit_method_telemetry(_telemetry(), episode=None)
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert "bound_episode_not_observed" in report.reasons


def test_missing_telemetry_fails_closed() -> None:
    report = audit_method_telemetry(None, episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK


@pytest.mark.parametrize(
    ("episode_overrides", "reason"),
    [
        ({"episode_id": "episode::other"}, "telemetry_bound_to_a_different_episode"),
        ({"artifact_hash": "f" * 64}, "episode_artifact_hash_changed_since_telemetry"),
        (
            {"fibre_snapshot_hash": "0" * 64},
            "fibre_snapshot_hash_does_not_match_bound_episode",
        ),
    ],
)
def test_broken_episode_link_is_refuted(
    episode_overrides: dict[str, Any], reason: str
) -> None:
    report = audit_method_telemetry(
        _telemetry(), episode=_episode(**episode_overrides)
    )
    assert report.verdict is MethodTelemetryVerdict.REFUTED_CLAIM
    assert reason in report.reasons


def test_intact_episode_link_is_not_reported_as_broken() -> None:
    report = audit_method_telemetry(_telemetry(), episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY


# --- typed fields must agree with each other and with the evidence root ------


def test_reopened_axis_ids_must_match_the_deltas_they_summarize() -> None:
    report = audit_method_telemetry(
        _telemetry(reopened_axis_ids=("axis::verification",)), episode=_episode()
    )
    assert report.verdict is MethodTelemetryVerdict.REFUTED_CLAIM
    assert "reopened_axis_ids_contradict_saturation_axis_deltas" in report.reasons


def test_a_failed_episode_cannot_be_reported_as_no_failure_observed() -> None:
    report = audit_method_telemetry(
        _telemetry(
            failure_class=MethodFailureClass.NO_FAILURE_OBSERVED,
            failure_evidence_pointers=(),
        ),
        episode=_episode(outcome_is_failure=True),
    )
    assert report.verdict is MethodTelemetryVerdict.REFUTED_CLAIM
    assert "failure_class_contradicts_bound_episode_outcome" in report.reasons


def test_a_recovered_substep_failure_on_a_successful_episode_is_recorded() -> None:
    """A succeeded episode may still attribute a sub-step failure; not a defect."""

    report = audit_method_telemetry(
        _telemetry(), episode=_episode(outcome_is_failure=False)
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY


def test_unattributed_failure_is_recorded_but_does_not_support_attribution() -> None:
    report = audit_method_telemetry(
        _telemetry(
            failure_class=MethodFailureClass.UNCLASSIFIED_FAILURE,
            failure_evidence_pointers=(),
        ),
        episode=_episode(outcome_is_failure=True),
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "failure_observed_but_not_attributed" in report.reasons
    assert report.permits_failure_attribution_study is False


def test_unattributed_failure_on_a_successful_episode_also_blocks_attribution() -> None:
    """Being unattributed is a property of the failure class, not the outcome.

    A successful episode may attribute a recovered sub-step failure, so an
    *unclassified* sub-step failure is equally reachable there.  Gating this note
    on the episode outcome let such a record license attribution study.
    """

    report = audit_method_telemetry(
        _telemetry(
            failure_class=MethodFailureClass.UNCLASSIFIED_FAILURE,
            failure_evidence_pointers=(),
        ),
        episode=_episode(outcome_is_failure=False),
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "failure_observed_but_not_attributed" in report.reasons
    assert report.permits_failure_attribution_study is False


def test_a_claim_boundary_cannot_hold_a_narrative_either() -> None:
    """The no-transcript property must cover every free-text field, not most."""

    report = audit_method_telemetry(
        _telemetry(claim_boundary=_TRANSCRIPT), episode=_episode()
    )
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert any("claim_boundary" in reason for reason in report.reasons)


def test_unassessed_gluing_is_recorded_as_such() -> None:
    report = audit_method_telemetry(
        _telemetry(gluing_status=GluingStatus.GLUING_NOT_ASSESSED), episode=_episode()
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "gluing_status_not_assessed" in report.reasons


def test_assessed_gluing_is_not_flagged() -> None:
    report = audit_method_telemetry(
        _telemetry(gluing_status=GluingStatus.GLUED_TO_GLOBAL), episode=_episode()
    )
    assert "gluing_status_not_assessed" not in report.reasons


def test_attributed_failure_without_evidence_is_recorded_as_a_gap() -> None:
    report = audit_method_telemetry(
        _telemetry(failure_evidence_pointers=()), episode=_episode()
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    assert "failure_attributed_without_evidence_pointers" in report.reasons


# --- composition with the coverage receipt (#119), never re-implementation ---


@pytest.mark.parametrize(
    "overrides",
    [{"coverage_receipt_hash": None}, {"coverage_receipt_id": None}],
)
def test_half_bound_coverage_reference_fails_closed(overrides: dict[str, Any]) -> None:
    report = audit_method_telemetry(_telemetry(**overrides), episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert "coverage_receipt_reference_incompletely_bound" in report.reasons


def test_no_coverage_reference_at_all_is_allowed() -> None:
    report = audit_method_telemetry(
        _telemetry(coverage_receipt_id=None, coverage_receipt_hash=None),
        episode=_episode(),
    )
    assert report.verdict is MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY


# --- receipt integrity -------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"telemetry_id": ""}, "telemetry_id_missing"),
        ({"next_action_id": "  "}, "next_action_id_missing"),
        ({"claim_boundary": ""}, "claim_boundary_missing"),
        ({"public_trace_event_id": ""}, "public_trace_event_id_missing"),
        ({"evidence_pointers": ()}, "evidence_pointers_missing"),
        (
            {
                "saturation_axis_deltas": (
                    SaturationAxisDelta("axis::a", 0.1, 0.2),
                    SaturationAxisDelta("axis::a", 0.2, 0.3),
                ),
                "reopened_axis_ids": (),
            },
            "duplicate_saturation_axis_delta",
        ),
    ],
)
def test_structurally_unbound_records_cannot_be_checked(
    overrides: dict[str, Any], reason: str
) -> None:
    report = audit_method_telemetry(_telemetry(**overrides), episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert reason in report.reasons


def test_absent_content_hash_cannot_be_checked_but_present_hash_can() -> None:
    unhashed = replace(_telemetry(), artifact_hash="")
    report = audit_method_telemetry(unhashed, episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.CANNOT_CHECK
    assert "artifact_hash_missing" in report.reasons
    assert audit_method_telemetry(_telemetry(), episode=_episode()).verdict is (
        MethodTelemetryVerdict.RECORDED_PROPOSAL_ONLY
    )


def test_tampered_content_hash_is_refuted() -> None:
    tampered = replace(_telemetry(), next_action_id="action::rewritten")
    report = audit_method_telemetry(tampered, episode=_episode())
    assert report.verdict is MethodTelemetryVerdict.REFUTED_CLAIM
    assert "artifact_hash_mismatch" in report.reasons


def test_content_hash_excludes_only_itself() -> None:
    telemetry = _telemetry()
    document = telemetry.to_dict()
    assert telemetry.artifact_hash == artifact_canonical_sha256(document)
    document["next_action_id"] = "action::other"
    assert artifact_canonical_sha256(document) != telemetry.artifact_hash


def test_record_mints_no_authority() -> None:
    report = audit_method_telemetry(_telemetry(), episode=_episode())
    assert report.grants_theorem_authority is False
    assert report.grants_tool_promotion is False
    assert report.grants_gluing_authority is False
    document = _telemetry().to_dict()
    for key in (
        "grants_theorem_authority",
        "grants_tool_promotion",
        "grants_gluing_authority",
        "grants_review_independence",
    ):
        assert document[key] is False


# --- schema ------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/method-telemetry-v1.schema.json").read_text(encoding="utf-8")
    )


def test_documents_validate_against_the_frozen_schema() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for telemetry in (
        _telemetry(),
        _ordinary_telemetry(),
        _telemetry(coverage_receipt_id=None, coverage_receipt_hash=None),
    ):
        assert list(validator.iter_errors(telemetry.to_dict())) == []


def test_schema_itself_forbids_a_multiline_rationale() -> None:
    """The transcript guard is in the schema too, not only the runtime."""

    document = _telemetry().to_dict()
    document["rejected_candidates"][0]["rejection_reason"] = _TRANSCRIPT
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d.update(grants_theorem_authority=True),
        lambda d: d.update(contains_private_reasoning_transcript=True),
        lambda d: d.update(grants_chain_of_thought_disclosure=True),
    ],
)
def test_schema_rejects_authority_or_disclosure_claims(mutator: Any) -> None:
    document = _telemetry().to_dict()
    mutator(document)
    assert list(Draft202012Validator(_schema()).iter_errors(document)) != []
