from __future__ import annotations

import hashlib
import pytest

from rakl.evolution import EvolutionVerdict
from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from rakl.meta_evolution import CandidateDelta, EvolutionLayer, SelfEvolutionAction
from rakl.meta_evolution_v2 import BlockingValidity, ContextualMutationCredit, ContextualMutationPolicy, DiagnosisBoundEvolutionPortrait, ValidatedCandidateDelta
from rakl.meta_evolution_v3 import EvaluatorEpochIdentity
from rakl.meta_evolution_v4 import CanonicalContextManifestV4, ContextTransportWitnessV4, content_digest
from rakl.meta_evolution_v5 import StrictContextualMutationCreditV5, StrictContextualMutationPolicyV5, StrictEvaluatorEpochIdentityV5, StrictEvolutionPortraitV5, StrictOuterAssuranceBindingV5
from rakl.self_evolution_controller import CURRENT_SELF_EVOLUTION_CONTROLLER, SelfEvolutionController


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def context(label: str, family: str = "A") -> CanonicalContextManifestV4:
    return CanonicalContextManifestV4(h("domain"), h("family:" + family), h("substrate"), h("eval-epoch"), "domain", label)


def evaluator(source: str) -> StrictEvaluatorEpochIdentityV5:
    return StrictEvaluatorEpochIdentityV5(h(source), h("deps"), h("metric"), h("benchmark"), h("environment"), h("cutoff"), source)


def test_current_controller_rejects_historical_v2_portrait_explicitly() -> None:
    historical = DiagnosisBoundEvolutionPortrait(
        diagnosis_verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP,),
        discriminator_ids=(),
        stagnant=True,
    )
    with pytest.raises(TypeError, match="StrictEvolutionPortraitV5"):
        CURRENT_SELF_EVOLUTION_CONTROLLER.plan(historical, current_diagnosis_digest=h("diagnosis"))  # type: ignore[arg-type]


def test_current_controller_delegates_strict_plan_to_v5() -> None:
    portrait = StrictEvolutionPortraitV5(
        diagnosis_verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        causes=(MechanicCause.REPRESENTATION_GAP,),
        discriminator_contract_digests=(),
        stagnant=True,
    )
    plan = CURRENT_SELF_EVOLUTION_CONTROLLER.plan(portrait, current_diagnosis_digest=h("diagnosis"))
    assert plan.action is SelfEvolutionAction.PROPOSE_MUTATION
    assert plan.primary_layer is EvolutionLayer.REPRESENTATION


def test_current_controller_rejects_historical_free_scope_credit_policy() -> None:
    source = context("source")
    historical = ContextualMutationPolicy((ContextualMutationCredit("op", EvolutionLayer.REPRESENTATION, "paper4/free-scope", 1.0),))
    with pytest.raises(TypeError, match="StrictContextualMutationPolicyV5"):
        CURRENT_SELF_EVOLUTION_CONTROLLER.update_credit(
            historical,  # type: ignore[arg-type]
            operator_contract_digest=h("op"),
            target_layer=EvolutionLayer.REPRESENTATION,
            context=source,
            outcome=EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE,
        )


def test_current_controller_updates_and_transports_only_strict_context_credit() -> None:
    op = h("operator-contract")
    source = context("source", "A")
    destination = context("destination", "B")
    policy = StrictContextualMutationPolicyV5((StrictContextualMutationCreditV5(op, EvolutionLayer.REPRESENTATION, source.digest, 1.0),))
    updated = CURRENT_SELF_EVOLUTION_CONTROLLER.update_credit(
        policy,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        context=source,
        outcome=EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE,
    )
    assert updated.weight_for(operator_contract_digest=op, target_layer=EvolutionLayer.REPRESENTATION, context=source) == pytest.approx(1.25)
    assert CURRENT_SELF_EVOLUTION_CONTROLLER.transported_credit(
        updated,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context=source,
        destination_context=destination,
        witness=None,
    ) is None
    witness = ContextTransportWitnessV4(h("witness"), op, EvolutionLayer.REPRESENTATION, source.digest, destination.digest, h("evidence"), "registered")
    assert CURRENT_SELF_EVOLUTION_CONTROLLER.transported_credit(
        updated,
        operator_contract_digest=op,
        target_layer=EvolutionLayer.REPRESENTATION,
        source_context=source,
        destination_context=destination,
        witness=witness,
    ) == pytest.approx(1.25)


def test_current_controller_rejects_historical_evaluator_identity() -> None:
    historical = EvaluatorEpochIdentity("old", h("source"), h("deps"), h("metric"), h("benchmark"), h("env"), h("cutoff"))
    with pytest.raises(TypeError, match="StrictEvaluatorEpochIdentityV5"):
        CURRENT_SELF_EVOLUTION_CONTROLLER.assess_governance(
            target_layer=EvolutionLayer.EVALUATOR,
            target_evaluator=historical,  # type: ignore[arg-type]
            candidate_subject_sha="a" * 40,
            candidate_benchmark_digest=h("benchmark"),
            outer_assurance=None,
        )


def test_current_controller_delegates_strict_evaluator_governance() -> None:
    target = evaluator("target")
    outer = evaluator("outer")
    subject = "a" * 40
    assurance = StrictOuterAssuranceBindingV5(h("assurance"), subject, outer, True, False)
    result = CURRENT_SELF_EVOLUTION_CONTROLLER.assess_governance(
        target_layer=EvolutionLayer.EVALUATOR,
        target_evaluator=target,
        candidate_subject_sha=subject,
        candidate_benchmark_digest=h("benchmark"),
        outer_assurance=assurance,
    )
    assert result.eligible_for_auto_promotion is True
    assert result.grants_scientific_authority is False


def _candidate(cid: str, q: float) -> CandidateDelta:
    return CandidateDelta(cid, q, q, q, q, q)


def test_current_controller_filters_invalid_candidates_before_soft_frontier() -> None:
    frontier = CURRENT_SELF_EVOLUTION_CONTROLLER.select_frontier((
        ValidatedCandidateDelta(_candidate("valid", 1.0), BlockingValidity.PASS),
        ValidatedCandidateDelta(_candidate("invalid-superstar", 100.0), BlockingValidity.FAIL, ("unsafe",)),
        ValidatedCandidateDelta(_candidate("unknown-superstar", 200.0), BlockingValidity.CANNOT_CHECK, ("missing",)),
    ))
    assert [entry.candidate.candidate_id for entry in frontier] == ["valid"]


def test_controller_is_explicitly_nonsovereign_and_has_no_auto_promotion() -> None:
    controller = SelfEvolutionController()
    assert controller.version == "SELF_EVOLUTION_CONTROLLER_STRICT_V5"
    assert controller.grants_scientific_authority is False
    assert controller.grants_method_promotion_authority is False
    assert controller.auto_promotes_methods is False
