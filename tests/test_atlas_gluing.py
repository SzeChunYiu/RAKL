from dataclasses import FrozenInstanceError

import pytest

from rakl.atlas_gluing import (
    AtlasChart,
    AtlasGluingTrial,
    AtlasGluingVerdict,
    CycleConsistencyWitness,
    GluingLayer,
    ObstructionType,
    OverlapTransition,
    TransitionVerdict,
    evaluate_atlas_gluing,
    validate_overlap_transition,
)
from rakl.generator_transport import AbstractionLevel


def _chart(chart_id: str) -> AtlasChart:
    return AtlasChart(
        chart_id=chart_id,
        atlas_object_id="apple-object",
        question_or_qoi="what global theory describes q?",
        abstraction_level=AbstractionLevel.L4,
        context_id=f"context-{chart_id}",
        assumptions=("registered-assumption",),
        regime=("shared-regime",),
        evidence_ids=(f"evidence-{chart_id}",),
    )


def _transition(
    source: str,
    target: str,
    *,
    transition_id: str | None = None,
    certified_layers: tuple[GluingLayer, ...] = (
        GluingLayer.OBSERVATIONAL,
        GluingLayer.MECHANISTIC,
    ),
    context_alignment_passed: bool | None = True,
    assumption_compatibility_passed: bool | None = True,
    regime_overlap: tuple[str, ...] = ("shared-regime",),
    transition_map_passed: bool | None = True,
    preserved: tuple[str, ...] = ("shared-relation",),
    not_preserved: tuple[str, ...] = ("local-coordinate",),
    declared_before_outcomes: bool | None = True,
) -> OverlapTransition:
    tid = transition_id or f"{source}-{target}"
    return OverlapTransition(
        transition_id=tid,
        source_chart_id=source,
        target_chart_id=target,
        overlap_id=f"overlap-{source}-{target}",
        mapping_pairs=(("role-a", "role-a"), ("role-b", "role-b")),
        preserved=preserved,
        not_preserved=not_preserved,
        certified_layers=certified_layers,
        context_alignment_passed=context_alignment_passed,
        assumption_compatibility_passed=assumption_compatibility_passed,
        regime_overlap=regime_overlap,
        transition_map_passed=transition_map_passed,
        evidence_ids=(f"evidence-{tid}",),
        declared_before_outcomes=declared_before_outcomes,
    )


def _cycle(*, consistent: bool | None = True) -> CycleConsistencyWitness:
    return CycleConsistencyWitness(
        cycle_id="cycle-abc",
        chart_path=("A", "B", "C", "A"),
        composition_consistent=consistent,
        evidence_ids=("cycle-evidence",),
    )


def _trial(**overrides) -> AtlasGluingTrial:
    values = dict(
        trial_id="trial-018",
        atlas_object_id="apple-object",
        question_or_qoi="what global theory describes q?",
        abstraction_level=AbstractionLevel.L4,
        requested_layer=GluingLayer.MECHANISTIC,
        charts=(_chart("A"), _chart("B"), _chart("C")),
        transitions=(
            _transition("A", "B"),
            _transition("B", "C"),
            _transition("C", "A"),
        ),
        cover_connected=True,
        cover_has_cycles=True,
        cycle_basis_complete=True,
        cycle_witnesses=(_cycle(),),
        global_existence_checked=True,
        global_exists=True,
        uniqueness_checked=True,
        unique_global=True,
        hidden_labels_exposed=False,
        transition_family_frozen_before_outcomes=True,
        target_tested=False,
        target_passed=None,
    )
    values.update(overrides)
    return AtlasGluingTrial(**values)


def _has_obstruction(report, kind: ObstructionType) -> bool:
    return any(obstruction.obstruction is kind for obstruction in report.obstructions)


def test_consistent_triangle_can_form_only_a_global_proposal():
    report = evaluate_atlas_gluing(_trial())
    assert report.verdict is AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY
    assert report.activates_canonical_knowledge is False
    assert report.establishes_mechanism_beyond_requested_layer is False


def test_pairwise_compatible_cycle_inconsistency_blocks_global_glue():
    report = evaluate_atlas_gluing(_trial(cycle_witnesses=(_cycle(consistent=False),)))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.CYCLE_OR_PATH_INCONSISTENCY)


def test_cyclic_cover_requires_complete_cycle_basis_checks():
    report = evaluate_atlas_gluing(_trial(cycle_basis_complete=False))
    assert report.verdict is AtlasGluingVerdict.CANNOT_CHECK


def test_pairwise_compatibility_does_not_imply_global_existence():
    report = evaluate_atlas_gluing(_trial(global_existence_checked=False))
    assert report.verdict is AtlasGluingVerdict.PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN


def test_global_existence_without_uniqueness_check_stays_unproven():
    report = evaluate_atlas_gluing(_trial(uniqueness_checked=False))
    assert report.verdict is AtlasGluingVerdict.GLOBAL_EXISTS_UNIQUENESS_UNPROVEN


def test_nonunique_global_state_is_retained_as_identified_set():
    report = evaluate_atlas_gluing(_trial(unique_global=False))
    assert report.verdict is AtlasGluingVerdict.IDENTIFIED_SET_ONLY


def test_disconnected_cover_remains_partial_atlas():
    report = evaluate_atlas_gluing(_trial(cover_connected=False))
    assert report.verdict is AtlasGluingVerdict.PARTIAL_ATLAS_ONLY


def test_context_mismatch_is_localized_as_obstruction():
    transitions = (
        _transition("A", "B", context_alignment_passed=False),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.CONTEXT_MISMATCH)


def test_assumption_conflict_is_localized_as_obstruction():
    transitions = (
        _transition("A", "B", assumption_compatibility_passed=False),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.ASSUMPTION_CONFLICT)


def test_disjoint_regime_is_not_glued():
    transitions = (
        _transition("A", "B", regime_overlap=()),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.REGIME_DISJOINT)


def test_observational_overlap_cannot_be_promoted_to_mechanistic_glue():
    transitions = (
        _transition("A", "B", certified_layers=(GluingLayer.OBSERVATIONAL,)),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.RELATION_LAYER_NOT_CERTIFIED)


def test_unknown_overlap_evidence_is_cannot_check():
    transitions = (
        _transition("A", "B", transition_map_passed=None),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.CANNOT_CHECK


def test_failed_transition_map_is_obstruction():
    transitions = (
        _transition("A", "B", transition_map_passed=False),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.TRANSITION_MAP_FAILURE)


def test_preserved_and_not_preserved_self_contradiction_is_obstruction():
    transitions = (
        _transition(
            "A",
            "B",
            preserved=("shared-relation",),
            not_preserved=("shared-relation",),
        ),
        _transition("B", "C"),
        _transition("C", "A"),
    )
    report = evaluate_atlas_gluing(_trial(transitions=transitions))
    assert report.verdict is AtlasGluingVerdict.OBSTRUCTED_ATLAS
    assert _has_obstruction(report, ObstructionType.MAPPING_WITNESS_CONTRADICTION)


def test_hidden_global_answer_exposure_invalidates_trial():
    report = evaluate_atlas_gluing(_trial(hidden_labels_exposed=True))
    assert report.verdict is AtlasGluingVerdict.TRIAL_INVALID


def test_posthoc_transition_family_adaptation_invalidates_trial():
    report = evaluate_atlas_gluing(
        _trial(transition_family_frozen_before_outcomes=False)
    )
    assert report.verdict is AtlasGluingVerdict.TRIAL_INVALID


def test_acyclic_pairwise_checks_still_need_explicit_global_evidence():
    report = evaluate_atlas_gluing(
        _trial(
            transitions=(_transition("A", "B"), _transition("B", "C")),
            cover_has_cycles=False,
            cycle_basis_complete=False,
            cycle_witnesses=(),
            global_existence_checked=False,
        )
    )
    assert report.verdict is AtlasGluingVerdict.PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN


def test_requested_layer_can_glue_while_allowed_coordinates_remain_not_preserved():
    report = evaluate_atlas_gluing(_trial())
    assert report.verdict is AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY
    assert all(
        transition.not_preserved == ("local-coordinate",)
        for transition in _trial().transitions
    )


def test_native_target_refutation_preserves_valid_gluing_history():
    report = evaluate_atlas_gluing(
        _trial(target_tested=True, target_passed=False)
    )
    assert (
        report.verdict
        is AtlasGluingVerdict.GLOBAL_PROPOSAL_REFUTED_OBSTRUCTION_HISTORY_PRESERVED
    )
    assert all(
        transition_report.verdict is TransitionVerdict.VALID
        for transition_report in report.transition_reports
    )


def test_transition_contract_is_immutable():
    transition = _transition("A", "B")
    with pytest.raises(FrozenInstanceError):
        transition.transition_id = "changed"  # type: ignore[misc]


def test_unknown_transition_freeze_chronology_is_cannot_check():
    transition = _transition("A", "B", declared_before_outcomes=None)
    report = validate_overlap_transition(
        transition,
        requested_layer=GluingLayer.MECHANISTIC,
        chart_ids=("A", "B"),
    )
    assert report.verdict is TransitionVerdict.CANNOT_CHECK
