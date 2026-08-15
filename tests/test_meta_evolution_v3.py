from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from rakl.meta_evolution import CandidateDelta, EvolutionLayer, SelfEvolutionAction
from rakl.meta_evolution_v2 import (
    BlockingValidity,
    ContextualMutationCredit,
    DiagnosisBoundEvolutionPortrait,
    ValidatedCandidateDelta,
)
from rakl.meta_evolution_v3 import (
    CanonicalContextIdentity,
    ContextTransportWitness,
    ContextualMutationPolicyV3,
    DiscriminatorDecisionReceipt,
    EvaluatorEpochIdentity,
    FailureEpochV3,
    MutationFamilyWitness,
    OuterAssuranceBindingV3,
    assess_mutation_governance_v3,
    distinct_failed_mutation_families_v3,
    plan_self_evolution_v3,
    transported_weight_v3,
    validity_gated_pareto_frontier_v3,
)


_BENCHMARK = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "self_rakl_p4_p6_question_saturation_v3"
    / "META_EVOLUTION_V3_FROZEN_BENCHMARK.json"
)


def test_v3_benchmark_was_frozen_before_implementation() -> None:
    data = json.loads(_BENCHMARK.read_text(encoding="utf-8"))
    assert data["status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    assert data["frozen_against_candidate_head"] == "0ddebfa03b18d5c34469c8ea62a4669b9c31da31"
    assert len(data["cases"]) >= 15


def _context(*, alias: str, evaluator: str = "epoch-a") -> CanonicalContextIdentity:
    return CanonicalContextIdentity(
        domain_id="paper4",
        problem_family_id="state_reachability",
        structural_substrate_digest="struct-sha",
        evaluator_epoch_digest=evaluator,
        alias=alias,
    )


def test_context_alias_does_not_manufacture_new_scope() -> None:
    assert _context(alias="pretty-name").digest == _context(alias="renamed-scope").digest
    assert _context(alias="same", evaluator="epoch-a").digest != _context(alias="same", evaluator="epoch-b").digest


def test_cross_context_credit_requires_exact_transport_witness() -> None:
    source = _context(alias="source", evaluator="epoch-a")
    destination = _context(alias="destination", evaluator="epoch-b")
    policy = ContextualMutationPolicyV3(
        (
            ContextualMutationCredit(
                operator_id="representation_reset",
                target_layer=EvolutionLayer.REPRESENTATION,
                scope_key=source.digest,
                weight=1.25,
            ),
        )
    )
    assert (
        transported_weight_v3(
            policy,
            operator_id="representation_reset",
            target_layer=EvolutionLayer.REPRESENTATION,
            source_context=source,
            destination_context=destination,
            witness=None,
        )
        is None
    )
    witness = ContextTransportWitness(
        witness_id="transport-1",
        operator_id="representation_reset",
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context_digest=source.digest,
        destination_context_digest=destination.digest,
        evidence_epoch_id="assurance-epoch-1",
        rationale="registered structural transport",
    )
    assert transported_weight_v3(
        policy,
        operator_id="representation_reset",
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context=source,
        destination_context=destination,
        witness=witness,
    ) == pytest.approx(1.25)
    assert witness.grants_scientific_authority is False
    assert witness.grants_method_promotion_authority is False


def _family(alias: str, *, effect: str = "new_representation") -> MutationFamilyWitness:
    return MutationFamilyWitness(
        target_layer=EvolutionLayer.REPRESENTATION,
        precondition_ids=("p2", "p1"),
        effect_ids=(effect,),
        falsifier_ids=("f1", "f2"),
        mechanism_class_id="representation_reset",
        alias=alias,
    )


def test_renamed_mutation_family_counts_once_but_real_difference_counts() -> None:
    left = _family("family-a")
    renamed = _family("totally-different-name")
    different = _family("family-b", effect="new_representation_plus_bridge")
    assert left.digest == renamed.digest
    assert left.digest != different.digest
    assert distinct_failed_mutation_families_v3(
        (
            FailureEpochV3("epoch-1", left),
            FailureEpochV3("epoch-2", renamed),
        )
    ) == 1
    assert distinct_failed_mutation_families_v3(
        (
            FailureEpochV3("epoch-1", left),
            FailureEpochV3("epoch-2", renamed),
            FailureEpochV3("epoch-3", different),
        )
    ) == 2


def _evaluator(display_id: str, *, source: str = "src-a", benchmark: str = "bench-a") -> EvaluatorEpochIdentity:
    return EvaluatorEpochIdentity(
        display_id=display_id,
        evaluator_source_digest=source,
        dependency_digest="deps-a",
        metric_semantics_digest="metrics-a",
        benchmark_digest=benchmark,
        environment_digest="env-a",
        cutoff_id="cutoff-1",
    )


def test_evaluator_rename_cannot_create_outer_independence() -> None:
    target = _evaluator("target")
    renamed = _evaluator("renamed-outer")
    assert target.evaluator_content_digest == renamed.evaluator_content_digest
    assessment = assess_mutation_governance_v3(
        target_layer=EvolutionLayer.EVALUATOR,
        target_evaluator=target,
        candidate_subject_sha="subject-1",
        candidate_benchmark_digest="bench-a",
        outer_assurance=OuterAssuranceBindingV3(
            assurance_id="outer-1",
            subject_sha="subject-1",
            outer_evaluator=renamed,
            frozen_before_candidate_outcome=True,
            candidate_outcomes_used_to_define_outer_evaluator=False,
        ),
    )
    assert assessment.eligible_for_auto_promotion is False
    assert "outer_evaluator_not_content_independent" in assessment.reasons


def test_same_evaluator_source_with_only_new_benchmark_is_not_independent() -> None:
    target = _evaluator("target", benchmark="bench-a")
    outer_epoch = _evaluator("outer", benchmark="bench-a")
    assessment = assess_mutation_governance_v3(
        target_layer=EvolutionLayer.META_POLICY,
        target_evaluator=target,
        candidate_subject_sha="subject-1",
        candidate_benchmark_digest="bench-a",
        outer_assurance=OuterAssuranceBindingV3(
            assurance_id="outer-2",
            subject_sha="subject-1",
            outer_evaluator=outer_epoch,
            frozen_before_candidate_outcome=True,
            candidate_outcomes_used_to_define_outer_evaluator=False,
        ),
    )
    assert assessment.eligible_for_auto_promotion is False


def test_independent_preoutcome_outer_assurance_can_only_enter_protected_gate() -> None:
    target = _evaluator("target", source="src-target")
    outer_epoch = _evaluator("outer", source="src-independent")
    assessment = assess_mutation_governance_v3(
        target_layer=EvolutionLayer.MUTATION_LANGUAGE,
        target_evaluator=target,
        candidate_subject_sha="subject-1",
        candidate_benchmark_digest="bench-a",
        outer_assurance=OuterAssuranceBindingV3(
            assurance_id="outer-3",
            subject_sha="subject-1",
            outer_evaluator=outer_epoch,
            frozen_before_candidate_outcome=True,
            candidate_outcomes_used_to_define_outer_evaluator=False,
        ),
    )
    assert assessment.eligible_for_auto_promotion is True
    assert assessment.requires_outer_assurance is True
    assert "entry_to_protected_gate" in assessment.reasons[0]


def test_postoutcome_outer_assurance_fails_closed_even_if_content_independent() -> None:
    target = _evaluator("target", source="src-target")
    outer_epoch = _evaluator("outer", source="src-independent")
    assessment = assess_mutation_governance_v3(
        target_layer=EvolutionLayer.EVALUATOR,
        target_evaluator=target,
        candidate_subject_sha="subject-1",
        candidate_benchmark_digest="bench-a",
        outer_assurance=OuterAssuranceBindingV3(
            assurance_id="outer-post",
            subject_sha="subject-1",
            outer_evaluator=outer_epoch,
            frozen_before_candidate_outcome=False,
            candidate_outcomes_used_to_define_outer_evaluator=False,
        ),
    )
    assert assessment.eligible_for_auto_promotion is False
    assert "outer_assurance_not_preoutcome" in assessment.reasons


def _underidentified_portrait() -> DiagnosisBoundEvolutionPortrait:
    return DiagnosisBoundEvolutionPortrait(
        diagnosis_verdict=MechanicDiagnosisVerdict.PARTIALLY_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP, MechanicCause.METRIC_FALSEHOOD),
        discriminator_ids=("probe-voi-1",),
        stagnant=True,
    )


def test_underidentified_multilayer_case_requires_decision_receipt() -> None:
    portrait = _underidentified_portrait()
    baseline = plan_self_evolution_v3(portrait, current_diagnosis_digest="diagnosis-a")
    assert baseline.action is SelfEvolutionAction.RUN_DISCRIMINATOR
    assert baseline.target_layers == ()

    receipt = DiscriminatorDecisionReceipt(
        receipt_id="receipt-1",
        diagnosis_before_digest="diagnosis-a",
        diagnosis_after_digest="diagnosis-b",
        discriminator_id="probe-voi-1",
        evidence_epoch_id="epoch-1",
        total_cost=2.5,
        resolved_target_layer=EvolutionLayer.REPRESENTATION,
    )
    resolved = plan_self_evolution_v3(
        portrait,
        current_diagnosis_digest="diagnosis-a",
        discriminator_receipt=receipt,
    )
    assert resolved.action is SelfEvolutionAction.PROPOSE_MUTATION
    assert resolved.target_layers == (EvolutionLayer.REPRESENTATION,)
    assert resolved.primary_layer is EvolutionLayer.REPRESENTATION
    assert receipt.grants_scientific_authority is False
    assert receipt.grants_method_promotion_authority is False


def test_discriminator_receipt_must_bind_current_diagnosis() -> None:
    receipt = DiscriminatorDecisionReceipt(
        receipt_id="receipt-wrong",
        diagnosis_before_digest="other-diagnosis",
        diagnosis_after_digest="diagnosis-b",
        discriminator_id="probe-voi-1",
        evidence_epoch_id="epoch-1",
        total_cost=1.0,
        resolved_target_layer=EvolutionLayer.REPRESENTATION,
    )
    with pytest.raises(ValueError, match="current diagnosis"):
        plan_self_evolution_v3(
            _underidentified_portrait(),
            current_diagnosis_digest="diagnosis-a",
            discriminator_receipt=receipt,
        )


def _candidate(cid: str, quality: float) -> CandidateDelta:
    return CandidateDelta(
        candidate_id=cid,
        quality=quality,
        cost=quality,
        latency=quality,
        robustness=quality,
        complexity=quality,
    )


def test_all_invalid_candidates_produce_empty_frontier() -> None:
    frontier = validity_gated_pareto_frontier_v3(
        (
            ValidatedCandidateDelta(_candidate("fail", 100.0), BlockingValidity.FAIL, ("harm",)),
            ValidatedCandidateDelta(_candidate("cc", 200.0), BlockingValidity.CANNOT_CHECK, ("missing",)),
        )
    )
    assert frontier == ()


def test_invalid_soft_dominator_never_compares_against_valid_candidate() -> None:
    frontier = validity_gated_pareto_frontier_v3(
        (
            ValidatedCandidateDelta(_candidate("valid", 1.0), BlockingValidity.PASS),
            ValidatedCandidateDelta(_candidate("invalid-superstar", 100.0), BlockingValidity.FAIL, ("unsafe",)),
        )
    )
    assert [entry.candidate.candidate_id for entry in frontier] == ["valid"]
