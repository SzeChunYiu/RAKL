"""Validation suite for the panel degeneracy auditor (issue #154).

Every check is exercised twice: once on a minimal fixture that *should* trip it
and once on a fixture that should not. A checker that only ever fires is a
false-positive generator and gets switched off; a checker that never fires is
decoration. Both failure modes are asserted against here.

The auditor is additionally validated against real data — the committed V1
panel, which it must find degenerate, and the V2 panel, which it must find
clean.
"""

from __future__ import annotations

import pytest

from rakl.authority_ledger import AuthorityAxis
from rakl.authority_leakage_audit import (
    AuditStatus,
    audit_panel,
    case_id_exploit_responder,
    check_case_id_opacity,
    check_label_blind_ceiling,
    check_label_pattern_diversity,
    check_positional_shortcut,
    check_role_order_shortcut,
    check_single_feature_separation,
    check_visible_disposition_leak,
    twin_polarity_responder,
)
from rakl.authority_leakage_benchmark import (
    CaseStratum,
    HiddenCaseLabels,
    LeakageSubtype,
    ScientificTransitionCase,
    TransitionDecision,
    VisibleCaseContext,
    frozen_case_panel,
    score_panel,
)
from rakl.authority_leakage_panel_v2 import HiddenCaseLabelsV2, frozen_case_panel_v2

_M = AuthorityAxis.MECHANISM
_R = AuthorityAxis.REPRESENTATION
_I = AuthorityAxis.IDENTIFICATION


def _case(
    case_id: str = "OPAQUE-001",
    *,
    observation: str = "held-out error fell to 0.08 on the registered map",
    claim_type: str = "representation",
    regime: str = "R1",
    roots: tuple[str, ...] = ("root-1",),
    candidates: tuple[str, ...] = ("read one", "read two", "read three"),
    allowed: frozenset[AuthorityAxis] = frozenset({_R}),
    disallowed: dict[AuthorityAxis, LeakageSubtype] | None = None,
    status: TransitionDecision = TransitionDecision.SUPPORTED,
    correct_index: int | None = None,
    roles: tuple[str, ...] = (),
) -> ScientificTransitionCase:
    labelled = correct_index is not None or bool(roles)
    label_cls = HiddenCaseLabelsV2 if labelled else HiddenCaseLabels
    extra: dict[str, object] = {}
    if correct_index is not None:
        extra["correct_interpretation_index"] = correct_index
    if roles:
        extra["candidate_roles"] = roles
    return ScientificTransitionCase(
        VisibleCaseContext(
            case_id=case_id,
            pre_state="claim K registered",
            registered_claims=("K",),
            claim_types=(claim_type,),
            context_regime=regime,
            existing_evidence_roots=roots,
            evidence_lineage=(),
            new_observation=observation,
            candidate_interpretations=candidates,
        ),
        label_cls(  # type: ignore[arg-type]
            allowed_authority_effects=allowed,
            disallowed_authority_effects=disallowed
            if disallowed is not None
            else {_M: LeakageSubtype.PREDICTION_TO_MECHANISM},
            required_terminal_status=status,
            **extra,
        ),
        CaseStratum.HOSTILE_NEAR_MISS,
    )


# --------------------------------------------------------------------------
# check 1: case id opacity
# --------------------------------------------------------------------------


def test_case_id_opacity_trips_on_semantic_identifier() -> None:
    result = check_case_id_opacity([_case("ALR-01-prediction-not-mechanism")])
    assert result.status is AuditStatus.DEGENERATE
    assert "mechanism" in result.detail["offending_case_ids"]["ALR-01-prediction-not-mechanism"]


def test_case_id_opacity_clean_on_opaque_identifier() -> None:
    assert check_case_id_opacity([_case("STA-V2-001A")]).status is AuditStatus.CLEAN


# --------------------------------------------------------------------------
# check 2: disposition asserted in setup text
# --------------------------------------------------------------------------


def test_disposition_leak_trips_when_setup_states_the_verdict() -> None:
    result = check_visible_disposition_leak(
        [_case(observation="the fit improved but mechanism authority must not increase")]
    )
    assert result.status is AuditStatus.DEGENERATE


@pytest.mark.parametrize(
    "observation",
    [
        # Regression: reporting which measurements exist is the *evidence*, not
        # the answer. An earlier revision flagged this and was wrong.
        "no intervention was performed and no mechanism witness was measured",
        # Regression: an unbounded "no" matched inside "nonetheless".
        "the instrument is offline; a decision is nonetheless requested now",
    ],
)
def test_disposition_leak_clean_on_legitimate_evidence_text(observation: str) -> None:
    assert check_visible_disposition_leak([_case(observation=observation)]).status is (
        AuditStatus.CLEAN
    )


# --------------------------------------------------------------------------
# check 3: single-feature separation
# --------------------------------------------------------------------------


def test_single_feature_separation_trips_on_perfect_value_shortcut() -> None:
    """Two roots always means an upgrade is licensed: a usable shortcut."""

    cases = [
        _case(f"OPAQUE-{i:03d}", roots=("a", "b"), allowed=frozenset({_R}))
        for i in range(6)
    ] + [
        _case(f"OPAQUE-1{i:02d}", roots=("a",), allowed=frozenset(), status=TransitionDecision.BLOCKED)
        for i in range(6)
    ]
    result = check_single_feature_separation(cases)
    assert result.status is AuditStatus.DEGENERATE
    shortcuts = {(s["feature"], s["predicts"]) for s in result.detail["value_shortcuts"]}
    assert ("n_evidence_roots", "licenses_an_upgrade") in shortcuts


def test_single_feature_separation_clean_when_purity_is_chance() -> None:
    """A pure group is not a finding when the facet's base rate is high.

    Regression: an earlier revision reported four such groups on the V2 panel.
    All were noise, and a checker that cries wolf on its first real run gets
    switched off.
    """

    cases = [
        _case(f"OPAQUE-{i:03d}", regime="R1" if i < 4 else "R2", allowed=frozenset({_R}))
        for i in range(12)
    ]
    # Break full-label uniformity so the facet has >1 observed value overall.
    cases.append(_case("OPAQUE-099", regime="R2", allowed=frozenset(), disallowed={}))
    result = check_single_feature_separation(cases)
    assert result.status is AuditStatus.CLEAN, result.message


def test_single_feature_separation_cannot_check_on_singleton_panel() -> None:
    assert check_single_feature_separation([_case()]).status is AuditStatus.CANNOT_CHECK


# --------------------------------------------------------------------------
# check 4: positional shortcut
# --------------------------------------------------------------------------


def test_positional_shortcut_cannot_check_without_index() -> None:
    """Absent labels are CANNOT_CHECK, never CLEAN."""

    result = check_positional_shortcut([_case(correct_index=None)])
    assert result.status is AuditStatus.CANNOT_CHECK
    assert result.detail["cases_missing_correct_interpretation_index"] == ["OPAQUE-001"]


def test_positional_shortcut_trips_when_one_position_always_correct() -> None:
    cases = [_case(f"OPAQUE-{i:03d}", correct_index=2) for i in range(8)]
    result = check_positional_shortcut(cases)
    assert result.status is AuditStatus.DEGENERATE


def test_positional_shortcut_clean_when_rotated() -> None:
    cases = [_case(f"OPAQUE-{i:03d}", correct_index=i % 3) for i in range(9)]
    assert check_positional_shortcut(cases).status is AuditStatus.CLEAN


# --------------------------------------------------------------------------
# check 4b: relative role order
# --------------------------------------------------------------------------


def test_role_order_cannot_check_without_roles() -> None:
    result = check_role_order_shortcut([_case(correct_index=0)])
    assert result.status is AuditStatus.CANNOT_CHECK


def test_role_order_trips_on_rotation_only_placement() -> None:
    """The defect a rotation scheme cannot avoid.

    Rotating ``(escalating, conservative, correct)`` spreads the correct answer
    evenly across absolute positions — ``check_positional_shortcut`` reports
    CLEAN — while leaving cyclic order invariant, so the correct reading always
    follows the conservative distractor.
    """

    canonical = ("escalating", "conservative", "correct")
    cases = [
        _case(f"OPAQUE-{i:03d}", correct_index=(2 - i % 3) % 3, roles=canonical[i % 3:] + canonical[: i % 3])
        for i in range(9)
    ]
    assert check_positional_shortcut(cases).status is AuditStatus.CLEAN
    result = check_role_order_shortcut(cases)
    assert result.status is AuditStatus.DEGENERATE
    assert result.detail["cyclic_adjacency_fraction"]["conservative->correct"] == 1.0


def test_role_order_clean_on_v2() -> None:
    assert check_role_order_shortcut(frozen_case_panel_v2()).status is AuditStatus.CLEAN


def test_twin_polarity_responder_does_not_clear_the_ceiling_on_v2() -> None:
    panel = frozen_case_panel_v2()
    score = score_panel(panel, tuple(twin_polarity_responder(c.visible) for c in panel))
    assert not (score.alr <= 0.25 and score.valid_upgrade_recall >= 0.50)


# --------------------------------------------------------------------------
# check 5: label balance
# --------------------------------------------------------------------------


def test_label_pattern_diversity_trips_when_few_cases_license_an_upgrade() -> None:
    """The defect that makes a panel blind to over-conservatism."""

    cases = [
        _case(f"OPAQUE-{i:03d}", allowed=frozenset(), status=TransitionDecision.BLOCKED)
        for i in range(7)
    ] + [_case("OPAQUE-100", allowed=frozenset({_R}))]
    result = check_label_pattern_diversity(cases)
    assert result.status is AuditStatus.DEGENERATE
    assert result.detail["cases_licensing_an_upgrade"] == 1


def test_label_pattern_diversity_clean_on_balanced_panel() -> None:
    assert check_label_pattern_diversity(frozen_case_panel_v2()).status is AuditStatus.CLEAN


# --------------------------------------------------------------------------
# check 6: label-blind ceiling
# --------------------------------------------------------------------------


def test_label_blind_ceiling_trips_on_v1_via_identifier_exploit() -> None:
    """The finding that invalidates V1's measured ALR.

    A responder reading nothing but ``case_id`` withholds unlicensed authority
    while granting licensed authority — indistinguishable from a disciplined
    reasoner, having done no reasoning.
    """

    panel = frozen_case_panel()
    score = score_panel(panel, tuple(case_id_exploit_responder(c.visible) for c in panel))
    assert score.alr <= 0.25
    assert score.valid_upgrade_recall >= 0.50

    result = check_label_blind_ceiling(panel)
    assert result.status is AuditStatus.DEGENERATE
    assert any("case_id_exploit" in breach for breach in result.detail["breaches"])


def test_label_blind_ceiling_clean_on_v2() -> None:
    result = check_label_blind_ceiling(frozen_case_panel_v2())
    assert result.status is AuditStatus.CLEAN, result.message


def test_identifier_exploit_is_powerless_against_opaque_ids() -> None:
    panel = frozen_case_panel_v2()
    score = score_panel(panel, tuple(case_id_exploit_responder(c.visible) for c in panel))
    assert score.valid_upgrade_recall == pytest.approx(0.0)


# --------------------------------------------------------------------------
# panel-level: real-data validation
# --------------------------------------------------------------------------


def test_v1_panel_is_degenerate() -> None:
    """Validation against real committed data, not a fixture."""

    report = audit_panel(frozen_case_panel(), "scientific-transition-authority-v1")
    assert report.status is AuditStatus.DEGENERATE
    assert set(report.degenerate_checks()) == {
        "case_id_opacity",
        "label_pattern_diversity",
        "label_blind_ceiling",
    }


def test_v2_panel_is_clean_on_every_check() -> None:
    report = audit_panel(frozen_case_panel_v2(), "scientific-transition-authority-v2")
    assert report.status is AuditStatus.CLEAN
    assert all(check.status is AuditStatus.CLEAN for check in report.checks), [
        (c.check_id, c.status.value, c.message) for c in report.checks
    ]


def test_degenerate_dominates_cannot_check_in_report_status() -> None:
    report = audit_panel(frozen_case_panel(), "v1")
    statuses = {check.status for check in report.checks}
    assert AuditStatus.CANNOT_CHECK in statuses
    assert report.status is AuditStatus.DEGENERATE


def test_audit_grants_no_authority_and_is_hash_bound() -> None:
    report = audit_panel(frozen_case_panel_v2(), "v2")
    assert report.grants_authority is False
    assert report.to_dict()["grants_scientific_authority"] is False
    assert len(report.artifact_hash()) == 64
