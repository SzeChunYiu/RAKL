from dataclasses import FrozenInstanceError
import pytest

from implementation.observation_contract_reference import (
    AuditVerdict,
    InformationRegime,
    ObservationContract,
    PairEvidence,
    QuestionTarget,
    audit_pair,
    issue_receipt,
    recall_ceiling,
)


def source_contract(**kw):
    base = dict(
        contract_id="scar-source-v1",
        version="1.0.0",
        regime=InformationRegime.SOURCE_GROUNDED,
        input_sources=("system_a_background", "system_b_background"),
        evaluator_epoch="scar-gold-epoch-1",
    )
    base.update(kw)
    return ObservationContract(**base)


def test_source_contract_validates():
    source_contract().validate()


def test_source_rejects_silent_normalizer():
    with pytest.raises(ValueError):
        source_contract(allowed_normalizers=("synonym-v1",)).validate()


def test_semantic_requires_registered_normalizer():
    c = ObservationContract(
        "sem", "1", InformationRegime.SEMANTIC_NORMALIZED,
        ("backgrounds",), (), evaluator_epoch="e1"
    )
    with pytest.raises(ValueError):
        c.validate()


def test_external_requires_explicit_policy_and_provenance():
    c = ObservationContract(
        "ext", "1", InformationRegime.EXTERNAL_COMPLETION,
        ("backgrounds",), external_knowledge_policy="DECLARED_WORLD_KNOWLEDGE",
        provenance_required=False, evaluator_epoch="e1"
    )
    with pytest.raises(ValueError):
        c.validate()


def test_contract_digest_changes_when_evaluator_epoch_changes():
    assert source_contract(evaluator_epoch="e1").digest() != source_contract(evaluator_epoch="e2").digest()


def test_source_paraphrase_requires_normalization():
    e = PairEvidence("id14-sequence-parts", True, False, semantic_normalizable=True, normalizer_id="synonym-v1")
    assert audit_pair(source_contract(), e) is AuditVerdict.REQUIRES_NORMALIZATION


def test_registered_semantic_normalizer_licenses_semantic_pair():
    c = ObservationContract(
        "sem", "1", InformationRegime.SEMANTIC_NORMALIZED,
        ("backgrounds",), ("synonym-v1",), evaluator_epoch="e1"
    )
    e = PairEvidence("id14-sequence-parts", True, False, semantic_normalizable=True, normalizer_id="synonym-v1")
    assert audit_pair(c, e) is AuditVerdict.LICENSED_SEMANTIC


def test_external_support_is_not_silently_licensed_in_source_regime():
    e = PairEvidence("external-needed", True, False, external_support_declared=True)
    assert audit_pair(source_contract(), e) is AuditVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE


def test_external_completion_can_license_declared_support():
    c = ObservationContract(
        "ext", "1", InformationRegime.EXTERNAL_COMPLETION,
        ("backgrounds",), external_knowledge_policy="DECLARED_WORLD_KNOWLEDGE",
        provenance_required=True, evaluator_epoch="e1"
    )
    e = PairEvidence("external-needed", True, False, external_support_declared=True)
    assert audit_pair(c, e) is AuditVerdict.LICENSED_EXTERNAL


def test_explicit_source_disclaimer_routes_to_evaluator_audit():
    e = PairEvidence("id24", False, False, source_explicitly_disclaims=True)
    assert audit_pair(source_contract(), e) is AuditVerdict.EVALUATOR_CONTRACT_TENSION


def test_fresh_block_contract_ceiling():
    assert recall_ceiling(37, 42) == pytest.approx(0.8809523809523809)


def test_contract_is_immutable():
    c = source_contract()
    with pytest.raises(FrozenInstanceError):
        c.evaluator_epoch = "changed"


def test_receipt_is_explicitly_non_authoritative():
    e = PairEvidence("visible", True, True)
    r = issue_receipt(source_contract(), QuestionTarget.VISIBLE_STRUCTURE, e)
    assert r.verdict is AuditVerdict.LICENSED_VISIBLE
    assert r.no_authority is True


def test_question_targets_are_distinct():
    assert QuestionTarget.VISIBLE_STRUCTURE != QuestionTarget.BENCHMARK_REPRODUCTION
