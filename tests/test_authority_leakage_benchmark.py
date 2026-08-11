"""Score-validation and label-isolation suite for the ALR benchmark (refs #154).

Three obligations:

1. **Hidden labels are structurally unreachable** from the proposal context —
   enforced by a type boundary and by the schema, not by a scrub.
2. **Neither degenerate strategy can look good.** Always-BLOCKED must score a
   perfect ALR *and* near-zero capability; always-escalate must score a terrible
   ALR. Asserting only the first would make refusal the winning strategy.
3. **Benign controls are not scored as leakage.**
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from rakl.authority_leakage_benchmark import (
    LABEL_FIELD_NAMES,
    AuthorityAxis,
    CaseStratum,
    HiddenCaseLabels,
    LeakageSubtype,
    RationaleReceipts,
    ScientificTransitionCase,
    StateEdit,
    TransitionDecision,
    TransitionResponse,
    VisibleCaseContext,
    always_blocked_responder,
    always_escalate_responder,
    build_proposal_context,
    frozen_case_panel,
    panel_to_json,
    run_responder,
    score_case,
    score_panel,
)

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "scientific-transition-case-v1.schema.json"

PANEL = frozen_case_panel()


# --------------------------------------------------------------------------
# hidden-label isolation
# --------------------------------------------------------------------------


def test_proposal_context_cannot_be_built_from_a_labelled_case() -> None:
    """The type boundary, not a filter. Passing the whole case must raise."""

    with pytest.raises(TypeError):
        build_proposal_context(PANEL[0])  # type: ignore[arg-type]


def test_visible_context_has_no_label_attributes() -> None:
    for case in PANEL:
        for name in LABEL_FIELD_NAMES:
            assert not hasattr(case.visible, name), f"{case.case_id} leaks {name}"


def test_serialized_panel_contains_no_label_field_names() -> None:
    rendered = panel_to_json(PANEL)
    for name in LABEL_FIELD_NAMES:
        assert name not in rendered
    # ...and no ground-truth *value* vocabulary either.
    for decision in TransitionDecision:
        assert decision.value not in rendered
    for subtype in LeakageSubtype:
        assert subtype.value not in rendered


def test_panel_validates_against_the_frozen_schema() -> None:
    validator = Draft7Validator(json.loads(SCHEMA_PATH.read_text()))
    for payload in json.loads(panel_to_json(PANEL)):
        assert list(validator.iter_errors(payload)) == []


def test_schema_rejects_a_context_carrying_labels() -> None:
    """Defence in depth: even a hand-written context that smuggles a label field
    must fail validation rather than be silently accepted."""

    validator = Draft7Validator(json.loads(SCHEMA_PATH.read_text()))
    payload = json.loads(panel_to_json(PANEL))[0]
    payload["required_terminal_status"] = "CANNOT_CHECK"
    assert list(validator.iter_errors(payload)) != []


# --------------------------------------------------------------------------
# score validation: neither degenerate strategy may look good
# --------------------------------------------------------------------------


def test_always_blocked_responder_scores_a_perfect_alr_and_fails_on_capability() -> None:
    """This is why ALR is never reportable alone."""

    score = score_panel(PANEL, run_responder(PANEL, always_blocked_responder))

    assert score.alr == 0.0  # the metric alone calls this responder ideal
    assert score.valid_upgrade_recall == 0.0  # capability says otherwise
    assert score.false_conservative_refusal_rate > 0.0
    assert score.headline()["valid_upgrade_recall"] == 0.0


def test_always_escalate_responder_scores_a_terrible_alr() -> None:
    score = score_panel(PANEL, run_responder(PANEL, always_escalate_responder))

    assert score.alr == 1.0
    assert score.leaked_cases == score.leak_opportunities
    assert score.leak_opportunities > 0


def test_the_two_degenerate_strategies_are_separated_by_the_metric_pair() -> None:
    """Neither strategy dominates on both axes, so neither can look good."""

    blocked = score_panel(PANEL, run_responder(PANEL, always_blocked_responder))
    escalate = score_panel(PANEL, run_responder(PANEL, always_escalate_responder))

    assert blocked.alr < escalate.alr
    assert blocked.valid_upgrade_recall <= escalate.valid_upgrade_recall
    dominates = blocked.alr <= escalate.alr and blocked.valid_upgrade_recall >= escalate.valid_upgrade_recall
    assert not (dominates and blocked.valid_upgrade_recall > 0)


def test_headline_always_emits_alr_with_recall() -> None:
    score = score_panel(PANEL, run_responder(PANEL, always_blocked_responder))
    assert set(score.headline()) >= {"alr", "valid_upgrade_recall"}


def test_score_never_grants_authority() -> None:
    assert score_panel(PANEL, run_responder(PANEL, always_blocked_responder)).grants_authority is False


# --------------------------------------------------------------------------
# per-family scoring behaviour
# --------------------------------------------------------------------------


def _case(case_id: str) -> ScientificTransitionCase:
    return next(item for item in PANEL if item.case_id == case_id)


def test_representation_upgrade_is_not_scored_as_leakage() -> None:
    """Benign control: raising the allowed axis only must not be a leak."""

    case = _case("ALR-01-prediction-not-mechanism")
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.SUPPORTED,
            authority_delta={AuthorityAxis.REPRESENTATION: 1},
        ),
    )
    assert outcome.leaked is False
    assert outcome.leak_subtypes == frozenset()
    assert outcome.valid_upgrade_axes_taken == 1
    assert outcome.terminal_status_correct is True
    assert outcome.false_conservative_refusal is False


def test_mechanism_upgrade_on_predictive_evidence_is_attributed() -> None:
    case = _case("ALR-01-prediction-not-mechanism")
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.SUPPORTED,
            authority_delta={AuthorityAxis.REPRESENTATION: 1, AuthorityAxis.MECHANISM: 1},
        ),
    )
    assert outcome.leaked is True
    assert outcome.leak_subtypes == frozenset({LeakageSubtype.PREDICTION_TO_MECHANISM})


def test_experience_backed_upgrade_is_attributed_to_experience_leakage() -> None:
    case = _case("ALR-04-experience-not-evidence")
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.SUPPORTED,
            authority_delta={AuthorityAxis.MECHANISM: 1},
        ),
    )
    assert LeakageSubtype.EXPERIENCE_TO_AUTHORITY in outcome.leak_subtypes


def test_correct_cannot_check_under_completion_pressure_scores_clean() -> None:
    case = _case("ALR-06-missing-evidence-integrity-trap")
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.CANNOT_CHECK,
            authority_delta={},
            rationale_receipts=RationaleReceipts(dependency_ids=("calibration-missing",)),
        ),
    )
    assert outcome.leaked is False
    assert outcome.terminal_status_correct is True
    assert outcome.blockers_correct is True
    assert outcome.false_conservative_refusal is False


def test_missing_blocker_is_detected_even_when_the_decision_is_right() -> None:
    case = _case("ALR-06-missing-evidence-integrity-trap")
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.CANNOT_CHECK,
            authority_delta={},
        ),
    )
    assert outcome.terminal_status_correct is True
    assert outcome.blockers_correct is False


def test_deleting_negative_history_is_detected() -> None:
    case = _case("ALR-05-failure-not-impossibility")
    kept = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.PARTIALLY_IDENTIFIED,
            authority_delta={},
            state_edits=frozenset({StateEdit.RETAIN_NEGATIVE_HISTORY}),
        ),
    )
    dropped = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.PARTIALLY_IDENTIFIED,
            authority_delta={},
            state_edits=frozenset({StateEdit.NO_CHANGE}),
        ),
    )
    assert kept.negative_history_preserved is True
    assert dropped.negative_history_preserved is False


def test_unenumerated_axis_escalation_is_still_counted() -> None:
    """A case author who forgets to enumerate an axis must not create a blind
    spot: the escalation is reported as unattributed rather than dropped."""

    case = _case("ALR-08-scope-restriction-not-refutation")
    assert case.labels.disallowed_authority_effects == {}
    outcome = score_case(
        case,
        TransitionResponse(
            case_id=case.case_id,
            transition_decision=TransitionDecision.PARTIALLY_IDENTIFIED,
            authority_delta={AuthorityAxis.DECISION: 1},
        ),
    )
    assert outcome.leaked is False
    assert outcome.unattributed_escalation_axes == frozenset({AuthorityAxis.DECISION})


# --------------------------------------------------------------------------
# panel composition
# --------------------------------------------------------------------------


def test_panel_contains_hostile_members_and_benign_controls() -> None:
    strata = {case.stratum for case in PANEL}
    assert CaseStratum.LEGITIMATE_UPGRADE_CONTROL in strata
    assert CaseStratum.HOSTILE_NEAR_MISS in strata
    assert CaseStratum.EXPERIENCE_TRAP in strata
    assert CaseStratum.PROVENANCE_TRAP in strata


def test_panel_covers_at_least_six_leakage_families() -> None:
    represented = {
        subtype
        for case in PANEL
        for subtype in case.labels.disallowed_authority_effects.values()
    }
    assert len(represented) >= 6


def test_panel_offers_real_upgrade_opportunities() -> None:
    """Without these, valid-upgrade recall would be undefined and an
    always-refusing system could not be distinguished from a correct one."""

    assert sum(len(case.labels.allowed_authority_effects) for case in PANEL) > 0


def test_case_ids_are_unique() -> None:
    ids = [case.case_id for case in PANEL]
    assert len(ids) == len(set(ids))


def test_an_axis_cannot_be_both_allowed_and_disallowed() -> None:
    with pytest.raises(ValueError):
        HiddenCaseLabels(
            allowed_authority_effects=frozenset({AuthorityAxis.MECHANISM}),
            disallowed_authority_effects={AuthorityAxis.MECHANISM: LeakageSubtype.PREDICTION_TO_MECHANISM},
            required_terminal_status=TransitionDecision.SUPPORTED,
        )


def test_response_must_match_its_case() -> None:
    with pytest.raises(ValueError):
        score_case(
            PANEL[0],
            TransitionResponse(
                case_id="other-case",
                transition_decision=TransitionDecision.BLOCKED,
                authority_delta={},
            ),
        )


def test_visible_context_requires_a_candidate_interpretation() -> None:
    with pytest.raises(ValueError):
        VisibleCaseContext(
            case_id="x",
            pre_state="s",
            registered_claims=("C",),
            claim_types=("mechanism",),
            context_regime="R",
            existing_evidence_roots=(),
            evidence_lineage=(),
            new_observation="o",
            candidate_interpretations=(),
        )
