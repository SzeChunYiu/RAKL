"""Experiment-epoch composition surface binding the section-B residuals.

This module is the honest integration entry point for one experiment/integration
epoch.  It composes the canonical state commitment (V3 dual-write), the exact
structural identity reuse receipt across external/training/inference stages, and
the unified mechanics manifest, then runs the readiness assessment.

It grants NO scientific, proof, transfer, model-promotion or capability
authority.  ``READY_FOR_INTEGRATION_TEST`` means only that the identities and
resolved external receipts for the epoch are bound well enough to *run* the
next experiment, not that the experiment will succeed or that any coordinate is
scientifically supported.

The residual wirings exercised here:
  * dual-write V3 canonical commitments (state_fingerprint_v3)
  * bind the exact StructuralIdentityBundle through external/training/inference
    (build_epoch_identity_reuse_receipt)
  * create a UnifiedMechanicsManifest for the integrated epoch
    (build_unified_mechanics_manifest + assess_unified_integration)
"""
from __future__ import annotations

from typing import Any


def assemble_integration_epoch(
    *,
    epoch_id: str,
    base_commit_hash: str,
    state: Any,
    structural_object: Any,
    context_hash: str,
    boundary_contract: Any,
    external_consumer_artifact_hash: str,
    training_consumer_artifact_hash: str,
    training_model_checkpoint_hash: str,
    inference_consumer_artifact_hash: str,
    inference_model_checkpoint_hash: str,
    train_example_ids: tuple[str, ...],
    fresh_inference_example_ids: tuple[str, ...],
    resolved_receipt_ids: tuple[str, ...],
    operational_subject_digest: str | None = None,
    quotient_validation_receipt_id: str | None = None,
    structural_transfer_use_receipt_id: str | None = None,
    training_assurance_id: str | None = None,
    geometry_id: str | None = None,
    geometry_learning_receipt_id: str | None = None,
    compilation_proposal_id: str | None = None,
    fresh_compilation_assurance_id: str | None = None,
    exact_base_guard_receipt_id: str | None = None,
    quotient_view: Any | None = None,
    witness: Any | None = None,
    require_geometry: bool = False,
    require_training: bool = False,
    require_shared_identity_reuse: bool = True,
    require_cognitive_compilation: bool = False,
    require_quotient_assurance: bool = False,
    require_transfer_use_assurance: bool = False,
    require_exact_base_guards: bool = True,
) -> tuple[Any, Any]:
    """Assemble one integration epoch and report readiness without coercing authority.

    Returns ``(manifest, report)``.  The manifest binds the V3 state commitment
    digest, the structural identity reuse receipt and every supplied component
    receipt; the report is the fail-closed readiness verdict for the epoch.
    """
    from .structural_identity_bridge import build_epoch_identity_reuse_receipt
    from .unified_integration_contract import (
        assess_unified_integration,
        build_unified_mechanics_manifest,
    )
    from .v3_commitment import state_commitment_v3

    state_commitment = state_commitment_v3(state)
    reuse_receipt = build_epoch_identity_reuse_receipt(
        receipt_id=f"{epoch_id}:identity-reuse",
        structural_object=structural_object,
        context_hash=context_hash,
        boundary_contract=boundary_contract,
        external_consumer_artifact_hash=external_consumer_artifact_hash,
        training_consumer_artifact_hash=training_consumer_artifact_hash,
        training_model_checkpoint_hash=training_model_checkpoint_hash,
        inference_consumer_artifact_hash=inference_consumer_artifact_hash,
        inference_model_checkpoint_hash=inference_model_checkpoint_hash,
        train_example_ids=train_example_ids,
        fresh_inference_example_ids=fresh_inference_example_ids,
        quotient_view=quotient_view,
        witness=witness,
    )
    manifest = build_unified_mechanics_manifest(
        manifest_id=f"{epoch_id}:manifest",
        base_commit_hash=base_commit_hash,
        state_commitment_digest=state_commitment.digest,
        structural_identity_digest=reuse_receipt.bundle.digest,
        operational_subject_digest=operational_subject_digest,
        geometry_id=geometry_id,
        geometry_learning_receipt_id=geometry_learning_receipt_id,
        quotient_validation_receipt_id=quotient_validation_receipt_id,
        structural_transfer_use_receipt_id=structural_transfer_use_receipt_id,
        training_assurance_id=training_assurance_id,
        shared_identity_reuse_receipt_id=reuse_receipt.receipt_id,
        compilation_proposal_id=compilation_proposal_id,
        fresh_compilation_assurance_id=fresh_compilation_assurance_id,
        exact_base_guard_receipt_id=exact_base_guard_receipt_id,
    )
    report = assess_unified_integration(
        manifest,
        expected_base_commit_hash=base_commit_hash,
        resolved_receipt_ids=resolved_receipt_ids,
        require_geometry=require_geometry,
        require_training=require_training,
        require_shared_identity_reuse=require_shared_identity_reuse,
        require_cognitive_compilation=require_cognitive_compilation,
        require_quotient_assurance=require_quotient_assurance,
        require_transfer_use_assurance=require_transfer_use_assurance,
        require_exact_base_guards=require_exact_base_guards,
    )
    return manifest, report
