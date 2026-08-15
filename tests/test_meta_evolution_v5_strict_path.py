from __future__ import annotations

import hashlib
import pytest

from rakl.evolution import EvolutionVerdict
from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from rakl.meta_evolution import EvolutionLayer, SelfEvolutionAction
from rakl.meta_evolution_v2 import DiagnosisBoundEvolutionPortrait
from rakl.meta_evolution_v4 import CanonicalContextManifestV4, ContextTransportWitnessV4, FailureEpochV4, MutationFamilyManifestV4, content_digest
from rakl.meta_evolution_v5 import (
    StrictContextualMutationCreditV5,
    StrictContextualMutationPolicyV5,
    StrictDiscriminatorDecisionReceiptV5,
    StrictEvaluatorEpochIdentityV5,
    StrictEvolutionPortraitV5,
    StrictOuterAssuranceBindingV5,
    assess_mutation_governance_v5,
    plan_self_evolution_v5,
    transported_weight_v5,
    update_contextual_mutation_policy_v5,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def family(label: str, *, operator: str = "op", effect: str = "effect") -> MutationFamilyManifestV4:
    return MutationFamilyManifestV4(
        EvolutionLayer.REPRESENTATION,
        h(operator),
        (h("precondition"),),
        (h(effect),),
        (h("falsifier"),),
        label,
    )


def context(name: str, *, family_name: str = "family") -> CanonicalContextManifestV4:
    return CanonicalContextManifestV4(
        h("domain-manifest"),
        h(f"problem-family:{family_name}"),
        h("structural-substrate"),
        h("evaluator-epoch"),
        "domain-display",
        name,
    )


def evaluator(source: str = "target-source") -> StrictEvaluatorEpochIdentityV5:
    return StrictEvaluatorEpochIdentityV5(
        h(source),
        h("dependencies"),
        h("metric-semantics"),
        h("benchmark"),
        h("environment"),
        h("cutoff-manifest"),
        source,
    )


def test_historical_v2_portrait_is_not_a_valid_strict_v5_input() -> None:
    historical = DiagnosisBoundEvolutionPortrait(
        diagnosis_verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP,),
        discriminator_ids=(),
        stagnant=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        plan_self_evolution_v5(historical, current_diagnosis_digest=h("diagnosis"))  # type: ignore[arg-type]


def test_failure_family_renames_do_not_trigger_false_escalation_on_strict_path() -> None:
    same_a = family("first-name")
    same_b = family("renamed-family")
    portrait = StrictEvolutionPortraitV5(
        diagnosis_verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP,),
        discriminator_contract_digests=(),
        stagnant=True,
        failure_epochs=(
            FailureEpochV4(h("epoch-1"), same_a),
            FailureEpochV4(h("epoch-2"), same_b),
        ),
    )
    plan = plan_self_evolution_v5(portrait, current_diagnosis_digest=h("diagnosis"))
    assert plan.action is SelfEvolutionAction.PROPOSE_MUTATION
    assert plan.target_layers == (EvolutionLayer.REPRESENTATION,)


def test_three_content_distinct_failure_families_can_open_topology() -> None:
    portrait = StrictEvolutionPortraitV5(
        diagnosis_verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP,),
        discriminator_contract_digests=(),
        stagnant=True,
        failure_epochs=(
            FailureEpochV4(h("epoch-1"), family("one", effect="e1")),
            FailureEpochV4(h("epoch-2"), family("two", effect="e2")),
            FailureEpochV4(h("epoch-3"), family("three", effect="e3")),
        ),
    )
    plan = plan_self_evolution_v5(portrait, current_diagnosis_digest=h("diagnosis"))
    assert EvolutionLayer.REPRESENTATION in plan.target_layers
    assert EvolutionLayer.TOPOLOGY in plan.target_layers


def test_discriminator_receipt_uses_exact_content_digests_on_strict_path() -> None:
    disc = h("discriminator-contract")
    before = h("diagnosis-before")
    portrait = StrictEvolutionPortraitV5(
        diagnosis_verdict=MechanicDiagnosisVerdict.PARTIALLY_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP, MechanicCause.METRIC_FALSEHOOD),
        discriminator_contract_digests=(disc,),
        stagnant=True,
    )
    blocked = plan_self_evolution_v5(portrait, current_diagnosis_digest=before)
    assert blocked.action is SelfEvolutionAction.RUN_DISCRIMINATOR
    receipt = StrictDiscriminatorDecisionReceiptV5(
        h("receipt"),
        before,
        h("diagnosis-after"),
        disc,
        h("evidence-epoch"),
        1.0,
        EvolutionLayer.REPRESENTATION,
    )
    resolved = plan_self_evolution_v5(
        portrait,
        current_diagnosis_digest=before,
        discriminator_receipt=receipt,
    )
    assert resolved.action is SelfEvolutionAction.PROPOSE_MUTATION
    assert resolved.target_layers == (EvolutionLayer.REPRESENTATION,)


def test_free_scope_string_cannot_construct_strict_contextual_credit() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        StrictContextualMutationCreditV5(
            h("operator"), EvolutionLayer.REPRESENTATION, "paper4/state-reachability", 1.0
        )


def test_context_credit_updates_only_exact_manifest_context_and_transports_by_witness() -> None:
    op = h("operator-contract")
    source = context("source", family_name="A")
    destination = context("destination", family_name="B")
    policy = StrictContextualMutationPolicyV5(
        (StrictContextualMutationCreditV5(op, EvolutionLayer.REPRESENTATION, source.digest, 1.0),)
    )
    updated = update_contextual_mutation_policy_v5(
        policy,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        context=source,
        outcome=EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE,
    )
    assert updated.weight_for(operator_contract_digest=op, target_layer=EvolutionLayer.REPRESENTATION, context=source) == pytest.approx(1.25)
    assert transported_weight_v5(
        updated,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context=source,
        destination_context=destination,
        witness=None,
    ) is None
    witness = ContextTransportWitnessV4(
        h("transport-witness"),
        op,
        EvolutionLayer.REPRESENTATION,
        source.digest,
        destination.digest,
        h("transport-evidence"),
        "same registered transport",
    )
    assert transported_weight_v5(
        updated,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context=source,
        destination_context=destination,
        witness=witness,
    ) == pytest.approx(1.25)


def test_evaluator_governance_rejects_labels_and_accepts_content_addressed_outer_epoch_only() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        StrictEvaluatorEpochIdentityV5(
            "evaluator-v1", h("deps"), h("metric"), h("bench"), h("env"), h("cutoff")
        )

    target = evaluator("target-source")
    outer = evaluator("outer-independent-source")
    subject = "a" * 40
    assurance = StrictOuterAssuranceBindingV5(
        h("outer-assurance"), subject, outer, True, False
    )
    assessment = assess_mutation_governance_v5(
        target_layer=EvolutionLayer.EVALUATOR,
        target_evaluator=target,
        candidate_subject_sha=subject,
        candidate_benchmark_digest=h("benchmark"),
        outer_assurance=assurance,
    )
    assert assessment.eligible_for_auto_promotion is True
    assert assessment.grants_scientific_authority is False


def test_v5_objects_remain_nonsovereign() -> None:
    portrait = StrictEvolutionPortraitV5(
        diagnosis_verdict=MechanicDiagnosisVerdict.NO_GAP,
        causes=(),
        discriminator_contract_digests=(),
        stagnant=False,
    )
    assert portrait.grants_scientific_authority is False
    assert portrait.grants_method_promotion_authority is False
