import pytest

from rakl.authority_assurance import *
from rakl.cognitive_compilation import *
from rakl.neural_structural_contract import *
from rakl.structural_identity_bridge import *


def bundle():
    return StructuralIdentityBundle("v1", "s", "sh", "q", "ctx", "quot", "qh", "wit", "wh", "bound")


def test_exact_identity_reuse_requires_all_three_stages_and_disjoint_fresh_panel():
    b = bundle()
    bindings = (
        StructuralUseBinding("e", StructuralUseStage.EXTERNAL_REASONING, b.digest, "external"),
        StructuralUseBinding("t", StructuralUseStage.TRAINING, b.digest, "trainer", "m0"),
        StructuralUseBinding("i", StructuralUseStage.INFERENCE, b.digest, "infer", "m1"),
    )
    r = SharedIdentityReuseReceipt("r", b, bindings, "train", "fresh", False)
    assert r.exact_identity_reuse_established and not r.grants_scientific_authority
    with pytest.raises(ValueError):
        SharedIdentityReuseReceipt("r", b, bindings, "same", "same", False)


def test_neural_witness_objective_must_be_asymmetric_when_panel_is():
    panel = DirectionalPairPanel(100, 40)
    assert panel.symmetric_classifier_accuracy_ceiling == .8
    with pytest.raises(ValueError):
        NeuralStructuralPreregistration(
            "p", "quotient", "witness", True, panel, "protected", "nonpreserve", "traps", "fresh", "compute",
            ("conditional-metric", "iit", "abstractor"), "matched-augmentation",
        )
    ok = NeuralStructuralPreregistration(
        "p", "quotient", "witness", False, panel, "protected", "nonpreserve", "traps", "fresh", "compute",
        ("conditional-metric", "iit", "abstractor"), "matched-augmentation",
    )
    assert not ok.grants_scientific_authority


def proposal():
    return CompilationProposal("p", "base", ("failure",), "diag", "bundle", "train", "recipe", "code", "proposer", True)


def test_cognitive_compilation_training_cannot_move_epistemic_projection():
    p = proposal()
    with pytest.raises(ValueError):
        ChallengerTrainingReceipt("t", p.digest, "challenger", "env", "log", "epi-before", "epi-after")
    t = ChallengerTrainingReceipt("t", p.digest, "challenger", "env", "log", "epi", "epi")
    assert compilation_decision(p, t, None) is CompilationVerdict.FRESH_ASSURANCE_REQUIRED
    assurance = FreshCompilationAssurance(
        "a", p.digest, "challenger", "fresh", "train", False, "evaluator", "proposer",
        "eval-artifact", ("static-baseline",), True
    )
    assert compilation_decision(p, t, assurance) is CompilationVerdict.CANNOT_CHECK
    assert compilation_decision(
        p, t, assurance, resolved_fresh_assurance_ids=frozenset({"a"})
    ) is CompilationVerdict.MODEL_PROMOTION_ELIGIBLE
    assert not assurance.grants_scientific_authority


def test_fresh_assurance_requires_separate_evaluator_and_disjoint_split():
    with pytest.raises(ValueError):
        FreshCompilationAssurance("a", "proposal", "c", "fresh", "train", False, "same", "same", "art", ("b",), True)
    with pytest.raises(ValueError):
        FreshCompilationAssurance("a", "proposal", "c", "train", "train", False, "e", "p", "art", ("b",), True)


def test_derived_authority_is_provenance_only_unless_reverified():
    ref = DerivedAuthorityBinding("v", "vh", ("cert",), DerivedAuthoritySemantics.PROVENANCE_REFERENCE_ONLY)
    assert not ref.grants_derived_authority
    with pytest.raises(ValueError):
        DerivedAuthorityBinding("v", "vh", ("cert",), DerivedAuthoritySemantics.EXACT_SCOPE_PRESERVING_REVERIFIED)
    real = DerivedAuthorityBinding("v", "vh", ("cert",), DerivedAuthoritySemantics.EXACT_SCOPE_PRESERVING_REVERIFIED, "reverify")
    assert not real.grants_derived_authority
    assert not derived_view_eligible_for_authority_gate(real, resolved_revalidation_receipt_ids=frozenset())
    assert derived_view_eligible_for_authority_gate(
        real, resolved_revalidation_receipt_ids=frozenset({"reverify"})
    )


def test_internal_hmac_fixture_is_not_called_production_grade():
    b = CertificateAssuranceBinding(
        "b", "cert", "ch", "att", "subj", "eval", ("evidence",), "backend", TrustBackendClass.INTERNAL_RELEASE_FIXTURE
    )
    assert not b.production_grade_trust_root


def test_identity_bundle_builder_hashes_actual_content():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class S:
        structure_id: str
        qoi: str
        payload: int

    a = build_structural_identity_bundle(S("s", "q", 1), context_hash="ctx", boundary_contract={"b": 1})
    b = build_structural_identity_bundle(S("s", "q", 2), context_hash="ctx", boundary_contract={"b": 1})
    assert a.structure_content_hash != b.structure_content_hash
    assert a.digest != b.digest


def test_shared_identity_builder_computes_example_overlap_instead_of_trusting_flag():
    b = bundle()
    bindings = (
        StructuralUseBinding("e", StructuralUseStage.EXTERNAL_REASONING, b.digest, "external"),
        StructuralUseBinding("t", StructuralUseStage.TRAINING, b.digest, "trainer", "m0"),
        StructuralUseBinding("i", StructuralUseStage.INFERENCE, b.digest, "infer", "m1"),
    )
    ok = build_shared_identity_reuse_receipt(
        receipt_id="r2", bundle=b, bindings=bindings,
        train_example_ids=("a", "b"), fresh_inference_example_ids=("c", "d"),
    )
    assert ok.exact_identity_reuse_established
    with pytest.raises(ValueError):
        build_shared_identity_reuse_receipt(
            receipt_id="r3", bundle=b, bindings=bindings,
            train_example_ids=("a", "b"), fresh_inference_example_ids=("b", "c"),
        )


def test_fresh_compilation_builder_computes_split_overlap():
    p = proposal()
    a = build_fresh_compilation_assurance(
        p, assurance_id="fa", challenger_checkpoint_hash="c",
        training_example_ids=("t1",), fresh_example_ids=("f1",), evaluator_id="e",
        evaluator_artifact_hash="art", comparator_ids=("base",), passed=True,
    )
    assert a.proposal_digest == p.digest
    with pytest.raises(ValueError):
        build_fresh_compilation_assurance(
            p, assurance_id="fa2", challenger_checkpoint_hash="c",
            training_example_ids=("same",), fresh_example_ids=("same",), evaluator_id="e",
            evaluator_artifact_hash="art", comparator_ids=("base",), passed=True,
        )
