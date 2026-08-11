from __future__ import annotations

from dataclasses import replace

from rakl.breakthrough_learning import (
    BreakthroughMode,
    ExpertiseChunk,
    LearningControlSignals,
    LearningControlVerdict,
    NaivePriorProbe,
    recommend_breakthrough_modes,
    validate_expertise_chunk,
    validate_naive_prior_probe,
)


def _prior() -> NaivePriorProbe:
    return NaivePriorProbe(
        probe_id="P1",
        atom_id="A1",
        frozen_at="2026-08-11T04:00:00+00:00",
        source_exposure_at="2026-08-11T04:01:00+00:00",
        provisional_representations=("graph separation view",),
        provisional_assumptions=("reuse may be the obstruction",),
        predicted_obstacles=("tree-style measures may double-count shared work",),
        artifact_hash="sha256:prior",
    )


def _chunk() -> ExpertiseChunk:
    return ExpertiseChunk(
        chunk_id="chunk-1",
        cue_signature=("DAG reuse", "shared subcomputation"),
        deep_structure=("reuse defeats recomputation charging",),
        tool_ids=("tool-reuse-audit",),
        failure_warning_ids=("failure-depth3-transfer",),
        applicability_conditions=("target representation permits explicit DAG reuse audit",),
        non_applicability_conditions=("tree-only model",),
        contrastive_near_misses=("same sign matrix but formula rather than unrestricted DAG",),
        retrieval_probes=("new surface vocabulary with identical reuse structure",),
        evidence_pointers=("receipt:tool", "failure:depth3"),
        artifact_hash="sha256:chunk",
    )


def test_naive_prior_requires_pre_source_isolation() -> None:
    assert validate_naive_prior_probe(_prior()) == ()
    bad = replace(_prior(), source_exposure_at="2026-08-11T03:59:00+00:00")
    assert "naive_prior:not_frozen_before_source_exposure" in validate_naive_prior_probe(bad)
    leaked = replace(_prior(), isolated_from_candidate_generation=False)
    assert "naive_prior:not_isolated_from_candidate_generation" in validate_naive_prior_probe(leaked)


def test_expertise_chunk_requires_scope_contrasts_and_retrieval_probes() -> None:
    assert validate_expertise_chunk(_chunk()) == ()
    bad = replace(_chunk(), non_applicability_conditions=(), contrastive_near_misses=())
    reasons = validate_expertise_chunk(bad)
    assert "expertise_chunk:non_applicability_conditions_missing" in reasons
    assert "expertise_chunk:contrastive_near_misses_missing" in reasons


def test_safe_familiar_case_prefers_routine_reuse() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            familiar_context_match=True,
            applicability_witness_passed=True,
            mature_tool_available=True,
        )
    )
    assert report.verdict is LearningControlVerdict.PROPOSE
    assert report.modes[0] is BreakthroughMode.ROUTINE_REUSE
    assert not report.authority_created


def test_scope_conflict_triggers_reflection_and_contrast() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            familiar_context_match=True,
            applicability_witness_passed=False,
            conflicting_cues=True,
        )
    )
    assert BreakthroughMode.ROUTINE_REUSE not in report.modes
    assert BreakthroughMode.REFLECTIVE_RESTRUCTURE in report.modes
    assert BreakthroughMode.CONTRASTIVE_DISCRIMINATION in report.modes


def test_flat_repeated_search_triggers_fixation_reset() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            repeated_failure_count=3,
            epistemic_gain_flat=True,
            fixation_risk=True,
        )
    )
    assert BreakthroughMode.FIXATION_RESET in report.modes
    assert BreakthroughMode.INCUBATION_CONTEXT_ROTATION in report.modes


def test_mature_but_brittle_tool_triggers_deliberate_practice() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            mature_tool_available=True,
            transfer_boundary_unstable=True,
            familiar_context_match=True,
            applicability_witness_passed=True,
        )
    )
    assert BreakthroughMode.DELIBERATE_PRACTICE in report.modes


def test_effectual_probe_selected_when_global_search_is_flat() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            epistemic_gain_flat=True,
            controllable_probe_available=True,
        )
    )
    assert BreakthroughMode.EFFECTUAL_PROBE in report.modes


def test_method_basis_audit_requires_strong_stagnation_pattern() -> None:
    report = recommend_breakthrough_modes(
        LearningControlSignals(
            repeated_failure_count=4,
            failure_redundancy_high=True,
            epistemic_gain_flat=True,
            search_diversity_high=True,
            context_coverage_high=True,
        )
    )
    assert BreakthroughMode.META_METHOD_BASIS_AUDIT in report.modes
    assert BreakthroughMode.EXPLORATORY_RECOMBINATION in report.modes


def test_insufficient_signals_fail_closed() -> None:
    report = recommend_breakthrough_modes(LearningControlSignals())
    assert report.verdict is LearningControlVerdict.CANNOT_CHECK
    assert report.modes == ()
