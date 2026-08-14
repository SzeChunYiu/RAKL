from rakl.epistemic_projection_benchmark_v2 import (
    Architecture,
    REGISTERED_AUTHORITY_BASIS,
    assert_gold_is_state_function,
    assert_no_family_label_visibility,
    audit_all,
    authority_basis_certificate,
)


def test_gold_is_coherent_without_family_id():
    assert_gold_is_state_function()


def test_no_answer_semantic_family_label_visible():
    assert_no_family_label_visibility()


def test_registered_authority_basis_is_minimal_on_twins():
    cert = authority_basis_certificate()
    assert cert["sufficient"] is True
    assert cert["minimal_by_registered_twin_witnesses"] is True
    assert cert["size"] == 10
    assert set(cert["basis"]) == set(REGISTERED_AUTHORITY_BASIS)


def test_strong_parent_is_stronger_than_simple_controls_but_not_sufficient():
    result = audit_all()["architectures"]
    strong = result[Architecture.ATMS_PROV_REVISION.value]
    simple = result[Architecture.SIMPLE_TRANSACTIONAL_STATE.value]
    typed = result[Architecture.RAKL_TYPED_AUTHORITY.value]
    assert strong["identifiable_accuracy_upper_bound"] > simple["identifiable_accuracy_upper_bound"]
    assert strong["identifiable_accuracy_upper_bound"] < 1.0
    assert typed["identifiable_accuracy_upper_bound"] == 1.0
    assert typed["ambiguous_projected_states"] == 0
