"""Observation Contract v1 — production tests.

Covers the ten behaviours the closure packet requires of a production port, plus
the frozen reference cases. The recursive audit's own 37-case conformance is
asserted in its own file and is untouched here: this module only *builds* the
residual type that chain already accepts.
"""

from __future__ import annotations

import dataclasses

import pytest

from rakl.observation_contract import (
    ContractVerdict,
    InformationRegime,
    ObservationContract,
    PairEvidence,
    QuestionTarget,
    audit_coordinates_for,
    audit_pair,
    decide_from_contract_verdict,
    issue_receipt,
    recall_ceiling,
    to_audit_residual,
)
from rakl.recursive_framework_audit import AuditAction, AuditCoordinate


def source_contract(**overrides: object) -> ObservationContract:
    fields: dict[str, object] = dict(
        contract_id="scar-source-v1",
        version="1.0.0",
        regime=InformationRegime.SOURCE_GROUNDED,
        input_sources=("system_a_background", "system_b_background"),
        evaluator_epoch="scar-gold-epoch-1",
    )
    fields.update(overrides)
    return ObservationContract(**fields)  # type: ignore[arg-type]


def semantic_contract(**overrides: object) -> ObservationContract:
    fields: dict[str, object] = dict(
        contract_id="scar-semantic-v1",
        version="1.0.0",
        regime=InformationRegime.SEMANTIC_NORMALIZED,
        input_sources=("system_a_background", "system_b_background"),
        allowed_normalizers=("synonym-v1",),
        evaluator_epoch="scar-gold-epoch-1",
    )
    fields.update(overrides)
    return ObservationContract(**fields)  # type: ignore[arg-type]


def external_contract(**overrides: object) -> ObservationContract:
    fields: dict[str, object] = dict(
        contract_id="scar-external-v1",
        version="1.0.0",
        regime=InformationRegime.EXTERNAL_COMPLETION,
        input_sources=("system_a_background",),
        external_knowledge_policy="DECLARED_WORLD_KNOWLEDGE",
        provenance_required=True,
        evaluator_epoch="scar-gold-epoch-1",
    )
    fields.update(overrides)
    return ObservationContract(**fields)  # type: ignore[arg-type]


# 1. a source-grounded contract rejects silent normalizer use ----------------


def test_source_grounded_rejects_silent_normalizer_and_external_knowledge() -> None:
    source_contract().validate()
    with pytest.raises(ValueError, match="forbids semantic normalizers"):
        source_contract(allowed_normalizers=("synonym-v1",))
    with pytest.raises(ValueError, match="forbids external knowledge"):
        source_contract(external_knowledge_policy="DECLARED_WORLD_KNOWLEDGE")


def test_paraphrase_under_a_source_contract_requires_normalization_not_a_pass() -> None:
    evidence = PairEvidence(
        "id14-sequence-parts",
        left_source_licensed=True,
        right_source_licensed=False,
        semantic_normalizable=True,
        normalizer_id="synonym-v1",
    )
    assert audit_pair(source_contract(), evidence) is ContractVerdict.REQUIRES_NORMALIZATION


# 2. a semantic contract requires a registered normalizer identity -----------


def test_semantic_regime_requires_a_named_normalizer() -> None:
    with pytest.raises(ValueError, match="requires a named normalizer"):
        semantic_contract(allowed_normalizers=())


def test_unregistered_normalizer_is_cannot_check_not_licensed() -> None:
    evidence = PairEvidence(
        "id14",
        left_source_licensed=True,
        right_source_licensed=False,
        semantic_normalizable=True,
        normalizer_id="unregistered-v9",
    )
    assert audit_pair(semantic_contract(), evidence) is ContractVerdict.CANNOT_CHECK
    registered = dataclasses.replace(evidence, normalizer_id="synonym-v1")
    assert audit_pair(semantic_contract(), registered) is ContractVerdict.LICENSED_SEMANTIC


# 3. external completion requires an external provenance policy --------------


def test_external_completion_requires_policy_and_provenance() -> None:
    with pytest.raises(ValueError, match="requires an explicit policy"):
        external_contract(external_knowledge_policy="FORBIDDEN")
    with pytest.raises(ValueError, match="requires provenance"):
        external_contract(provenance_required=False)


def test_external_support_is_never_licensed_by_omission() -> None:
    evidence = PairEvidence("external-needed", True, False, external_support_declared=True)
    assert audit_pair(source_contract(), evidence) is ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE
    assert audit_pair(semantic_contract(), evidence) is ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE
    assert audit_pair(external_contract(), evidence) is ContractVerdict.LICENSED_EXTERNAL


# 4. an evaluator epoch change alters the digest -----------------------------


def test_evaluator_epoch_change_changes_the_digest_and_closes_comparison() -> None:
    first = source_contract(evaluator_epoch="e1")
    second = first.successor(evaluator_epoch="e2")
    assert first.digest() != second.digest()
    assert second.supersedes(first)
    assert second.stales_results_of(first)
    assert first.comparable_to(second) is False
    assert first.comparable_to(source_contract(evaluator_epoch="e1")) is True


def test_regime_and_normalizer_changes_also_define_a_successor() -> None:
    base = semantic_contract()
    widened = base.successor(allowed_normalizers=("synonym-v1", "lemma-v2"))
    assert widened.digest() != base.digest()
    assert widened.supersedes(base)
    # A different lineage is not a supersession, even at a different digest.
    assert widened.supersedes(external_contract()) is False


# 5. an explicit source/gold contradiction routes to evaluator audit ---------


def test_explicit_source_disclaimer_outranks_everything_and_audits_the_evaluator() -> None:
    disclaimed = PairEvidence(
        "id24",
        left_source_licensed=True,
        right_source_licensed=True,
        semantic_normalizable=True,
        normalizer_id="synonym-v1",
        external_support_declared=True,
        source_explicitly_disclaims=True,
    )
    assert audit_pair(semantic_contract(), disclaimed) is ContractVerdict.EVALUATOR_CONTRACT_TENSION
    decision = decide_from_contract_verdict(ContractVerdict.EVALUATOR_CONTRACT_TENSION)
    assert decision.action is AuditAction.AUDIT_EVALUATOR


# 6. contract changes do not change authority --------------------------------


def test_nothing_in_this_module_grants_authority() -> None:
    contract = source_contract()
    receipt = issue_receipt(contract, QuestionTarget.VISIBLE_STRUCTURE, PairEvidence("v", True, True))
    for obj in (contract, contract.successor(evaluator_epoch="e9"), receipt):
        assert obj.grants_scientific_authority is False
        assert obj.grants_method_promotion_authority is False
    decision = decide_from_contract_verdict(ContractVerdict.REQUIRES_NORMALIZATION)
    assert decision.grants_scientific_authority is False
    assert decision.grants_method_promotion_authority is False


# 7. previous results are preserved, not deleted -----------------------------


def test_a_receipt_is_bound_to_the_contract_that_produced_it() -> None:
    first = source_contract(evaluator_epoch="e1")
    receipt = issue_receipt(first, QuestionTarget.VISIBLE_STRUCTURE, PairEvidence("v", True, True))
    second = first.successor(evaluator_epoch="e2")
    # The successor stales the earlier result but cannot rewrite it: the receipt
    # still names the predecessor's digest and epoch.
    assert second.stales_results_of(first)
    assert receipt.contract_digest == first.digest()
    assert receipt.contract_digest != second.digest()
    assert receipt.evaluator_epoch == "e1"


# 8. staled results cannot be relabelled as evidence for the successor -------


def test_staled_results_do_not_transfer_across_an_epoch_change() -> None:
    first = source_contract(evaluator_epoch="e1")
    second = first.successor(evaluator_epoch="e2")
    receipt = issue_receipt(first, QuestionTarget.VISIBLE_STRUCTURE, PairEvidence("v", True, True))
    assert receipt.contract_digest != second.digest()
    assert first.comparable_to(second) is False


# 9. a resource-bound audit is not a method failure --------------------------


def test_cannot_check_abstains_rather_than_attributing_a_cause() -> None:
    residual = to_audit_residual(ContractVerdict.CANNOT_CHECK)
    assert residual.plausible_causes == ()
    assert residual.resource_bound is True
    assert decide_from_contract_verdict(ContractVerdict.CANNOT_CHECK).action is AuditAction.CANNOT_CHECK


def test_licensed_verdicts_indicate_no_formulation_defect() -> None:
    for verdict in (
        ContractVerdict.LICENSED_VISIBLE,
        ContractVerdict.LICENSED_SEMANTIC,
        ContractVerdict.LICENSED_EXTERNAL,
    ):
        assert audit_coordinates_for(verdict) == ()
        assert decide_from_contract_verdict(verdict).action is AuditAction.SOLVE_CURRENT


# 10. the audit chain is inherited, not duplicated ---------------------------


def test_verdicts_route_through_the_frozen_chain() -> None:
    # Two plausible levels must discriminate before any revision.
    assert audit_coordinates_for(ContractVerdict.REQUIRES_NORMALIZATION) == (
        AuditCoordinate.QUESTION,
        AuditCoordinate.MEASUREMENT,
    )
    assert decide_from_contract_verdict(ContractVerdict.REQUIRES_NORMALIZATION).action is AuditAction.RUN_DISCRIMINATOR
    # Missing external knowledge is a capability/resource question.
    assert audit_coordinates_for(ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE) == (
        AuditCoordinate.EVIDENCE,
    )
    assert (
        decide_from_contract_verdict(ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE).action
        is AuditAction.SOLVE_CURRENT
    )
    # An evaluator invalidity outranks a resource bound, per the frozen order.
    assert (
        decide_from_contract_verdict(ContractVerdict.EVALUATOR_CONTRACT_TENSION, resource_bound=True).action
        is AuditAction.AUDIT_EVALUATOR
    )
    assert every_verdict_is_mapped()


def every_verdict_is_mapped() -> bool:
    return all(audit_coordinates_for(v) is not None for v in ContractVerdict)


# --- frozen reference cases from the closure packet --------------------------


def test_contract_is_immutable() -> None:
    contract = source_contract()
    with pytest.raises(dataclasses.FrozenInstanceError):
        contract.evaluator_epoch = "changed"  # type: ignore[misc]


def test_contract_relative_recall_ceiling() -> None:
    assert recall_ceiling(37, 42) == pytest.approx(0.8809523809523809)
    assert recall_ceiling(0, 42) == 0.0
    assert recall_ceiling(42, 42) == 1.0
    with pytest.raises(ValueError, match="must be positive"):
        recall_ceiling(1, 0)
    with pytest.raises(ValueError, match="within"):
        recall_ceiling(43, 42)


def test_question_targets_are_distinct() -> None:
    assert QuestionTarget.VISIBLE_STRUCTURE is not QuestionTarget.BENCHMARK_REPRODUCTION
    assert len(set(QuestionTarget)) == 4


def test_invalid_contracts_are_not_constructible() -> None:
    with pytest.raises(ValueError, match="at least one input source"):
        source_contract(input_sources=())
    with pytest.raises(ValueError, match="unique"):
        source_contract(input_sources=("a", "a"))
    with pytest.raises(ValueError, match="identity and version"):
        source_contract(contract_id="")
