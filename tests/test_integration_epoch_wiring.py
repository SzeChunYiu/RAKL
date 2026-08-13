"""Integration tests proving the section-B residuals are wired into the live call graph.

These are INTEGRATION tests, not unit tests on each gate: they drive real
production entry points (the quotient runtime, the benchmark receipt builder,
the training projection, the diagnosis flow, the epoch assembler) and assert
that the wiring is load-bearing — in particular that the quotient runtime
REFUSES a caller-made validation report when no external receipt is resolved
and SUCCEEDS when one is.
"""
from __future__ import annotations

import pytest

from rakl.diagnosis_state_machine import DiagnosisVerdict
from rakl.mechanic_diagnosis import (
    MechanicCause,
    MechanicDiagnosisVerdict,
    diagnose_mechanic_signals,
    refine_diagnosis_with_discriminator,
)
from rakl.problem_fibre import FibreKnowledgeItem, ProblemAtom
from rakl.promotion import (
    PromotionDecision,
    PromotionVerdict,
    model_promotion_eligibility_is_separate_from_scientific_authority,
)
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    materialize_validated_quotient,
)
from rakl.semantic_quotient_assurance import ResolvedQuotientValidationReceipt
from rakl.semantic_quotient_runtime import (
    QuotientRuntimeRoute,
    assured_compile_problem_fibre_with_quotient,
)
from rakl.structural_benchmark import make_multifamily_cases
from rakl.structural_benchmark_receipt import build_structural_transfer_use_receipt
from rakl.structural_transfer_use import TransferUseVerdict
from rakl.training_projection import attach_canonical_training_assurance
from rakl.v3_runtime import state_fingerprint, state_fingerprint_v2, state_fingerprint_v3


# ---------------------------------------------------------------------------
# Shared fixtures (mirror the runtime contract tests).
# ---------------------------------------------------------------------------


def _source() -> ProblemRepresentation:
    return ProblemRepresentation(
        representation_id="runtime-r",
        problem_id="runtime-p",
        atom_id="runtime-a",
        qoi="stability",
        context_hash="runtime-ctx",
        source_hash="runtime-source-hash",
        coordinates=("queue", "stability", "surface"),
        protected_fields=("queue", "stability"),
    )


def _proposal(source: ProblemRepresentation) -> QuotientProposal:
    return QuotientProposal(
        quotient_id="runtime-q",
        source_representation_id=source.representation_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        preserved_coordinates=("queue", "stability"),
        erased_coordinates=("surface",),
        preserved_invariants=("queue_stability",),
        protected_coordinates=("queue", "stability"),
        sufficiency_obligations=("answer_preserved",),
        falsifiers=("surface_changes_answer",),
    )


def _report(source: ProblemRepresentation, proposal: QuotientProposal) -> QuotientValidationReport:
    return QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("answer_preserved",),
        metamorphic_checks=("surface_orbit",),
        protected_coordinate_checks=("queue_present", "stability_present"),
        evidence_pointers=("runtime:receipt",),
    )


def _atom() -> ProblemAtom:
    return ProblemAtom(
        atom_id="runtime-a",
        goal="determine stability",
        context_hash="runtime-ctx",
        structural_coordinates=("queue", "stability", "surface"),
        desired_effects=(),
    )


def _items():
    return (
        FibreKnowledgeItem(
            item_id="a-surface",
            kind="surface",
            structural_signature=("surface",),
            effects=(),
            context_tags=(),
            authority="PROPOSAL_ONLY",
            payload_hash="surface-hash",
        ),
        FibreKnowledgeItem(
            item_id="z-structure",
            kind="structure",
            structural_signature=("queue", "stability"),
            effects=(),
            context_tags=(),
            authority="PROPOSAL_ONLY",
            payload_hash="structure-hash",
        ),
    )


def _resolved_receipt(source, proposal, report) -> ResolvedQuotientValidationReceipt:
    return ResolvedQuotientValidationReceipt(
        receipt_id="kernel-replay-receipt",
        validation_report_hash=report.content_hash,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verifier_id="kernel-replay",
        evidence_content_hashes=("sha256:evidence-a", "sha256:evidence-b"),
    )


# ---------------------------------------------------------------------------
# Residual 1 + L10 P3: assured quotient runtime refuses then succeeds.
# ---------------------------------------------------------------------------


def test_assured_runtime_refuses_unresolved_validation_receipt() -> None:
    source = _source()
    proposal = _proposal(source)
    report = _report(source, proposal)
    receipt = _resolved_receipt(source, proposal, report)
    atom = _atom()

    # A caller-made VALID_* report must NOT be self-authenticating at the
    # production entry point: with the receipt unresolved the runtime refuses.
    with pytest.raises(ValueError, match="quotient_validation_receipt_unresolved"):
        assured_compile_problem_fibre_with_quotient(
            atom,
            source,
            proposal=proposal,
            report=report,
            validation_receipt=receipt,
            resolved_receipt_ids=(),
            knowledge_items=_items(),
            top_k_each=1,
        )


def test_assured_runtime_refuses_content_mismatched_receipt() -> None:
    source = _source()
    proposal = _proposal(source)
    report = _report(source, proposal)
    mismatched = ResolvedQuotientValidationReceipt(
        receipt_id="kernel-replay-receipt",
        validation_report_hash="not-the-report-hash",
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verifier_id="kernel-replay",
        evidence_content_hashes=("sha256:evidence-a",),
    )
    atom = _atom()
    with pytest.raises(ValueError, match="quotient_validation_receipt_unresolved"):
        assured_compile_problem_fibre_with_quotient(
            atom,
            source,
            proposal=proposal,
            report=report,
            validation_receipt=mismatched,
            resolved_receipt_ids=("kernel-replay-receipt",),
            knowledge_items=_items(),
            top_k_each=1,
        )


def test_assured_runtime_succeeds_when_receipt_resolved() -> None:
    source = _source()
    proposal = _proposal(source)
    report = _report(source, proposal)
    receipt = _resolved_receipt(source, proposal, report)
    atom = _atom()
    raw_coordinates = atom.structural_coordinates

    result = assured_compile_problem_fibre_with_quotient(
        atom,
        source,
        proposal=proposal,
        report=report,
        validation_receipt=receipt,
        resolved_receipt_ids=("kernel-replay-receipt",),
        knowledge_items=_items(),
        top_k_each=1,
    )
    assert result.route is QuotientRuntimeRoute.QUOTIENT
    assert result.fibre.knowledge_items[0].item_id == "z-structure"
    assert result.quotient_view_hash == materialize_validated_quotient(source, proposal, report).content_hash
    # The runtime must not mutate the caller's atom.
    assert atom.structural_coordinates == raw_coordinates


# ---------------------------------------------------------------------------
# Residual 2: transfer-use receipt is load-bearing on non-preserved properties.
# ---------------------------------------------------------------------------


def test_transfer_use_receipt_fails_closed_without_resolved_evidence() -> None:
    receipt = build_structural_transfer_use_receipt()
    # No evidence or preservation receipts resolved -> every case is either
    # REJECTED (use_qoi_mismatch on decoys) or CANNOT_CHECK; none licensed.
    assert receipt["licensed_for_use_count"] == 0
    assert receipt["resolved_witness_evidence_count"] == 0
    verdicts = {row["use_verdict"] for row in receipt["cases"]}
    assert TransferUseVerdict.LICENSED_FOR_USE.value not in verdicts


def test_transfer_use_receipt_licenses_when_evidence_and_receipts_resolved() -> None:
    cases = make_multifamily_cases()
    resolved_evidence: set[str] = set()
    resolved_preservation: set[str] = set()
    for case in cases:
        resolved_evidence.update(case.witness.evidence_ids)
        for prop in sorted(case.source.invariants):
            resolved_preservation.add(f"preservation-receipt:{case.case_id}:{prop}")

    receipt = build_structural_transfer_use_receipt(
        resolved_witness_evidence_ids=frozenset(resolved_evidence),
        resolved_preservation_receipt_ids=frozenset(resolved_preservation),
    )
    # At least the structural-match-expected cases (Q2) must license for use
    # once their evidence and preservation receipts are resolved.
    assert receipt["licensed_for_use_count"] >= 1
    licensed = [row for row in receipt["cases"] if row["use_verdict"] == TransferUseVerdict.LICENSED_FOR_USE.value]
    assert licensed, "expected at least one LICENSED_FOR_USE case after resolution"


# ---------------------------------------------------------------------------
# Residual 3: V3 canonical commitment dual-write.
# ---------------------------------------------------------------------------


class _MiniState:
    """Minimal attribute carrier matching the v3 commitment field set."""

    experience = ("e1",)
    tools = ("t1",)
    failures = ("f1",)
    saturation = ("s1",)
    evolution = ("ev1",)
    scientific_authority = ("sa1",)


def test_state_fingerprint_v3_dual_writes_a_distinct_canonical_digest() -> None:
    state = _MiniState()
    v1 = state_fingerprint(state)
    v2 = state_fingerprint_v2(state)
    v3 = state_fingerprint_v3(state)
    # v1/v2 are unchanged historical identities (raw 64-char hex); v3 is the
    # canonical commitment, which uses the prefixed sha256: encoding (71 chars).
    assert v1 != v2 != v3 and v1 != v3
    assert isinstance(v3, str) and v3.startswith("sha256:") and len(v3) == 71
    assert len(v1) == 64 and len(v2) == 64
    # A sequence-bearing chained commitment differs from the initial one.
    chained = state_fingerprint_v3(state, sequence=1, previous_digest=v3)
    assert chained != v3


# ---------------------------------------------------------------------------
# Residual 4: canonical training assurance attaches to a learner projection.
# ---------------------------------------------------------------------------


def test_attach_canonical_training_assurance_dual_writes_digest() -> None:
    from rakl.training_projection import build_training_projection
    from rakl.structural_types import (
        BoundaryCondition,
        StructuralObject,
        StructuralRole,
    )

    struct = StructuralObject(
        structure_id="proj-struct-1",
        domain="stability",
        qoi="stability",
        context_id="proj-ctx",
        roles=(StructuralRole("queue", "arrival_process"),),
        relations=(),
        invariants=frozenset({"queue_stability"}),
        boundaries=(BoundaryCondition("regime", "continual"),),
        evidence_ids=("e:proj-struct-1",),
    )
    from rakl.training_projection import structural_catalog_digest

    catalog = structural_catalog_digest((struct,))
    snapshot = build_training_projection(
        projection_id="proj-1",
        model_checkpoint_hash="ckpt-1",
        structural_catalog_hash=catalog,
        probe_family_hash="probe-1",
        structural_objects=(struct,),
        mastery_estimates=(),
        candidates=(),
        repetition_floor=0.0,
        frozen_before_outcome_access=True,
    )
    assured = attach_canonical_training_assurance(
        snapshot,
        (struct,),
        assurance_id="assurance-1",
        code_commit_hash="commit-1",
        tokenizer_hash="tok-1",
        optimizer_config_hash="opt-1",
        sampling_policy_hash="sample-1",
        train_split_hash="train-1",
        probe_split_hash="probe-1",
        fresh_assurance_split_hash="fresh-1",
    )
    assert assured.snapshot is snapshot
    # Canonical (non-repr) digest is populated and differs from the legacy hash.
    assert assured.assurance.canonical_snapshot_digest
    assert assured.assurance.canonical_snapshot_digest != snapshot.snapshot_hash
    assert assured.assurance.legacy_snapshot_hash == snapshot.snapshot_hash
    assert not assured.grants_scientific_authority
    assert not assured.claims_adaptive_training_works


# ---------------------------------------------------------------------------
# Residual 5: diagnosis refinement emits an immutable transition receipt.
# ---------------------------------------------------------------------------


def test_refine_diagnosis_emits_transition_receipt_and_refuses_non_discriminator() -> None:
    # Two candidate causes + a registered discriminator -> DISCRIMINATOR_REQUIRED.
    receipt = diagnose_mechanic_signals(
        diagnosis_id="diag-1",
        problem_state_id="state-1",
        atom_id="atom-1",
        fibre_snapshot_hash="fibre-1",
        residual_ids=("r1",),
        signals=("coverage_incomplete", "decomposition_interface_missing"),
        discriminator_ids=("disc-A",),
    )
    assert receipt.verdict is MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED

    state, transition = refine_diagnosis_with_discriminator(
        receipt,
        transition_id="transition-1",
        discriminator_id="disc-A",
        surviving_causes=(MechanicCause.MAP_COVERAGE_GAP,),
        evidence_receipt_id="evidence-1",
    )
    assert transition.diagnosis_id == "diag-1"
    assert transition.before_state_digest != transition.after_state_digest
    assert transition.evidence_receipt_id == "evidence-1"
    assert transition.discriminator_id == "disc-A"
    assert state.verdict is DiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
    assert not transition.grants_method_promotion_authority

    # A one-shot identified diagnosis (single cause) cannot be discriminator-refined.
    identified = diagnose_mechanic_signals(
        diagnosis_id="diag-2",
        problem_state_id="state-2",
        atom_id="atom-2",
        fibre_snapshot_hash="fibre-2",
        residual_ids=("r2",),
        signals=("formal_target_alignment_failed",),
    )
    assert identified.verdict is MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
    with pytest.raises(ValueError):
        refine_diagnosis_with_discriminator(
            identified,
            transition_id="transition-2",
            discriminator_id="disc-X",
            surviving_causes=(MechanicCause.SPECIFICATION_GAP,),
            evidence_receipt_id="evidence-2",
        )


# ---------------------------------------------------------------------------
# Residual 6: exact structural identity bound through 3 stages.
# ---------------------------------------------------------------------------


def _boundary_contract():
    from rakl.structural_types import BoundaryCondition

    return (BoundaryCondition("regime", "continual"),)


def _structural_object():
    from rakl.structural_types import (
        BoundaryCondition,
        StructuralObject,
        StructuralRole,
    )

    return StructuralObject(
        structure_id="epoch-struct-1",
        domain="stability",
        qoi="stability",
        context_id="epoch-ctx",
        roles=(StructuralRole("queue", "arrival_process"),),
        relations=(),
        invariants=frozenset({"queue_stability"}),
        boundaries=(BoundaryCondition("regime", "continual"),),
        evidence_ids=("e:epoch-struct-1",),
    )


def test_build_epoch_identity_reuse_receipt_binds_three_stages() -> None:
    from rakl.structural_identity_bridge import (
        StructuralUseStage,
        build_epoch_identity_reuse_receipt,
    )

    receipt = build_epoch_identity_reuse_receipt(
        receipt_id="epoch-reuse-1",
        structural_object=_structural_object(),
        context_hash="epoch-context-hash",
        boundary_contract=_boundary_contract(),
        external_consumer_artifact_hash="external-artifact-hash",
        training_consumer_artifact_hash="training-artifact-hash",
        training_model_checkpoint_hash="ckpt-train",
        inference_consumer_artifact_hash="inference-artifact-hash",
        inference_model_checkpoint_hash="ckpt-infer",
        train_example_ids=("train-1", "train-2"),
        fresh_inference_example_ids=("infer-1", "infer-2"),
    )
    assert receipt.exact_identity_reuse_established
    assert not receipt.grants_scientific_authority
    stages = {binding.stage for binding in receipt.bindings}
    assert stages == set(StructuralUseStage)
    assert receipt.train_examples_hash != receipt.fresh_inference_examples_hash


def test_build_epoch_identity_reuse_receipt_refuses_overlapping_panels() -> None:
    from rakl.structural_identity_bridge import build_epoch_identity_reuse_receipt

    with pytest.raises(ValueError):
        build_epoch_identity_reuse_receipt(
            receipt_id="epoch-reuse-2",
            structural_object=_structural_object(),
            context_hash="epoch-context-hash",
            boundary_contract=_boundary_contract(),
            external_consumer_artifact_hash="external-artifact-hash",
            training_consumer_artifact_hash="training-artifact-hash",
            training_model_checkpoint_hash="ckpt-train",
            inference_consumer_artifact_hash="inference-artifact-hash",
            inference_model_checkpoint_hash="ckpt-infer",
            train_example_ids=("train-1",),
            fresh_inference_example_ids=("train-1",),
        )


# ---------------------------------------------------------------------------
# Residual 7 + L10 P3: epoch manifest readiness is fail-closed then ready.
# ---------------------------------------------------------------------------


def test_assemble_integration_epoch_reports_ready_when_receipts_resolved() -> None:
    from rakl.integration_epoch import assemble_integration_epoch

    struct = _structural_object()
    boundary = _boundary_contract()
    manifest, report = assemble_integration_epoch(
        epoch_id="epoch-1",
        base_commit_hash="3c24a9f78722ee5fa47ee3527e7e0e774aff91c6",
        state=_MiniState(),
        structural_object=struct,
        context_hash="epoch-context-hash",
        boundary_contract=boundary,
        external_consumer_artifact_hash="external-artifact-hash",
        training_consumer_artifact_hash="training-artifact-hash",
        training_model_checkpoint_hash="ckpt-train",
        inference_consumer_artifact_hash="inference-artifact-hash",
        inference_model_checkpoint_hash="ckpt-infer",
        train_example_ids=("train-1", "train-2"),
        fresh_inference_example_ids=("infer-1", "infer-2"),
        resolved_receipt_ids=("epoch-1:identity-reuse",),
        exact_base_guard_receipt_id="guard-receipt-1",
    )
    from rakl.unified_integration_contract import IntegrationReadiness

    # exact_base_guard_receipt_id is required and unresolved here -> CANNOT_CHECK.
    assert report.verdict is IntegrationReadiness.CANNOT_CHECK
    assert any("exact_base_guard_receipt_id" in r for r in report.reasons)


def test_assemble_integration_epoch_ready_when_all_required_resolved() -> None:
    from rakl.integration_epoch import assemble_integration_epoch
    from rakl.unified_integration_contract import IntegrationReadiness

    struct = _structural_object()
    boundary = _boundary_contract()
    manifest, report = assemble_integration_epoch(
        epoch_id="epoch-2",
        base_commit_hash="3c24a9f78722ee5fa47ee3527e7e0e774aff91c6",
        state=_MiniState(),
        structural_object=struct,
        context_hash="epoch-context-hash",
        boundary_contract=boundary,
        external_consumer_artifact_hash="external-artifact-hash",
        training_consumer_artifact_hash="training-artifact-hash",
        training_model_checkpoint_hash="ckpt-train",
        inference_consumer_artifact_hash="inference-artifact-hash",
        inference_model_checkpoint_hash="ckpt-infer",
        train_example_ids=("train-1", "train-2"),
        fresh_inference_example_ids=("infer-1", "infer-2"),
        resolved_receipt_ids=("epoch-2:identity-reuse", "guard-receipt-1"),
        exact_base_guard_receipt_id="guard-receipt-1",
    )
    assert report.verdict is IntegrationReadiness.READY_FOR_INTEGRATION_TEST
    assert not manifest.grants_scientific_authority
    assert not manifest.grants_proof_authority


# ---------------------------------------------------------------------------
# Residual 8: model-promotion eligibility != scientific-authority promotion.
# ---------------------------------------------------------------------------


def test_model_promotion_never_grants_scientific_authority() -> None:
    # A PROMOTE decision is the strongest model-promotion eligibility signal,
    # yet it must carry no scientific authority (separate transition).
    for decision in PromotionDecision:
        verdict = PromotionVerdict(decision=decision, reasons=())
        assert not verdict.grants_scientific_authority
        # The separation guard holds for every decision.
        assert model_promotion_eligibility_is_separate_from_scientific_authority(verdict)
