from __future__ import annotations
import pytest
from rakl.meta_evolution import EvolutionLayer
from rakl.meta_evolution_v4 import CanonicalContextManifestV4, FailureEpochV4, MutationFamilyManifestV4, content_digest, distinct_failed_mutation_families_v4

def h(x): return content_digest({"content":x})

def _ctx(domain=h("domain"),problem=h("problem"),domain_label="A",problem_label="P"):
    return CanonicalContextManifestV4(domain,problem,h("structure"),h("evaluator-epoch"),domain_label,problem_label)

def test_domain_and_problem_labels_cannot_change_context_identity():
    assert _ctx(domain_label="paper4",problem_label="state_reachability").digest == _ctx(domain_label="renamed-domain",problem_label="renamed-family").digest

def test_content_change_under_same_label_changes_context_identity():
    assert _ctx(domain=h("domain-v1"),domain_label="same").digest != _ctx(domain=h("domain-v2"),domain_label="same").digest

def _fam(label="m",operator=h("operator"),effect=h("effect")):
    return MutationFamilyManifestV4(EvolutionLayer.REPRESENTATION,operator,(h("pre"),),(effect,),(h("falsifier"),),label)

def test_mechanic_class_rename_cannot_fake_distinct_failure_family():
    a=_fam("representation_reset"); b=_fam("magic_new_name")
    assert a.digest==b.digest
    assert distinct_failed_mutation_families_v4((FailureEpochV4(h("epoch1"),a),FailureEpochV4(h("epoch2"),b)))==1

def test_operator_contract_change_is_a_real_family_difference():
    a=_fam(operator=h("operator-v1")); b=_fam(operator=h("operator-v2"))
    assert a.digest!=b.digest
    assert distinct_failed_mutation_families_v4((FailureEpochV4(h("epoch1"),a),FailureEpochV4(h("epoch2"),b)))==2

def test_non_digest_human_label_is_rejected_as_content_identity():
    with pytest.raises(ValueError,match="SHA-256"):
        CanonicalContextManifestV4("paper4",h("problem"),h("structure"),h("epoch"))
    with pytest.raises(ValueError,match="SHA-256"):
        MutationFamilyManifestV4(EvolutionLayer.REPRESENTATION,"representation_reset",(h("p"),),(h("e"),),(h("f"),))

def test_v4_objects_remain_nonsovereign():
    assert _ctx().grants_scientific_authority is False
    assert _fam().grants_scientific_authority is False
