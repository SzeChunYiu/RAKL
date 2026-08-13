"""EXACT structural-identity reuse across external reasoning, training, inference.

This primitive extends structural_identity_bridge with the distinction between:
1. EXACT shared content identity - the same bytes/content are reused across stages
2. Semantically-equivalent but independently-reconstructed identity - same semantics,
   different bytes (e.g., two separately constructed but equivalent quotients)

The primitive binds one structural object through external/training/inference and
produces a receipt that establishes exact identity reuse. This receipt grants no
scientific authority and does not assert that reuse is mechanistically beneficial.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from rakl.canonical_commitment import sha256_digest


class IdentityReuseMode(str, Enum):
    """The mode of identity reuse being tested."""

    EXACT_SHARED_CONTENT = "EXACT_SHARED_CONTENT"
    SEMANTIC_EQUIVALENT_RECONSTRUCTED = "SEMANTIC_EQUIVALENT_RECONSTRUCTED"
    STRUCTURE_AWARE_TRAIN_ONLY = "STRUCTURE_AWARE_TRAIN_ONLY"
    STRUCTURE_AWARE_INFERENCE_ONLY = "STRUCTURE_AWARE_INFERENCE_ONLY"
    GENERIC_RETRIEVAL = "GENERIC_RETRIEVAL"


@dataclass(frozen=True)
class StructuralContentSpec:
    """The exact content specification for a structural object.

    This captures the byte-level identity that distinguishes EXACT shared content
    from semantically-equivalent reconstructions.
    """
    structure_id: str
    content_bytes: bytes
    semantic_hash: str  # Hash of the semantic structure (ignoring byte-level details)

    def __post_init__(self) -> None:
        if not self.structure_id:
            raise ValueError("structure_id required")
        if not self.content_bytes:
            raise ValueError("content_bytes required")
        if not self.semantic_hash:
            raise ValueError("semantic_hash required")

    @property
    def content_hash(self) -> str:
        return sha256_digest(self.content_bytes, domain="rakl-structural-content-bytes/v1")

    @property
    def exact_content_identity_key(self) -> str:
        """Key that uniquely identifies this EXACT content."""
        return f"{self.structure_id}:{self.content_hash}"

    @property
    def semantic_identity_key(self) -> str:
        """Key that identifies semantically-equivalent content."""
        return f"{self.structure_id}:{self.semantic_hash}"


@dataclass(frozen=True)
class StageBinding:
    """Binding of structural identity to a specific use stage."""

    stage: Literal["EXTERNAL_REASONING", "TRAINING", "INFERENCE"]
    content_spec: StructuralContentSpec
    consumer_artifact_hash: str
    model_checkpoint_hash: str | None = None
    reconstruction_cost: float = 0.0

    def __post_init__(self) -> None:
        if self.stage in {"TRAINING", "INFERENCE"} and not self.model_checkpoint_hash:
            raise ValueError(f"{self.stage} requires model_checkpoint_hash")
        if self.stage == "EXTERNAL_REASONING" and self.model_checkpoint_hash:
            raise ValueError("EXTERNAL_REASONING must not have model_checkpoint_hash")

    @property
    def binding_key(self) -> str:
        return f"{self.stage}:{self.content_spec.exact_content_identity_key}"


@dataclass(frozen=True)
class IdentityReuseReceipt:
    """Receipt documenting the identity reuse pattern tested."""

    receipt_id: str
    mode: IdentityReuseMode
    external_binding: StageBinding
    training_binding: StageBinding
    inference_binding: StageBinding
    train_example_hashes: tuple[str, ...]
    inference_example_hashes: tuple[str, ...]
    any_example_overlap: bool

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise ValueError("receipt_id required")
        if self.external_binding.stage != "EXTERNAL_REASONING":
            raise ValueError("external_binding must be EXTERNAL_REASONING stage")
        if self.training_binding.stage != "TRAINING":
            raise ValueError("training_binding must be TRAINING stage")
        if self.inference_binding.stage != "INFERENCE":
            raise ValueError("inference_binding must be INFERENCE stage")
        if not self.train_example_hashes or not self.inference_example_hashes:
            raise ValueError("train and inference example panels must be nonempty")
        train_set = set(self.train_example_hashes)
        inference_set = set(self.inference_example_hashes)
        if len(train_set) != len(self.train_example_hashes):
            raise ValueError("train example hashes must be unique")
        if len(inference_set) != len(self.inference_example_hashes):
            raise ValueError("inference example hashes must be unique")
        overlap = bool(train_set & inference_set)
        if overlap != self.any_example_overlap:
            raise ValueError("any_example_overlap must match actual overlap")

    @property
    def exact_identity_reuse_established(self) -> bool:
        """True if all three stages bind the exact same content bytes."""
        return (
            self.external_binding.content_spec.exact_content_identity_key
            == self.training_binding.content_spec.exact_content_identity_key
            == self.inference_binding.content_spec.exact_content_identity_key
        )

    @property
    def semantic_identity_reuse_established(self) -> bool:
        """True if all three stages bind semantically-equivalent content."""
        return (
            self.external_binding.content_spec.semantic_identity_key
            == self.training_binding.content_spec.semantic_identity_key
            == self.inference_binding.content_spec.semantic_identity_key
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def total_reconstruction_cost(self) -> float:
        return (
            self.external_binding.reconstruction_cost
            + self.training_binding.reconstruction_cost
            + self.inference_binding.reconstruction_cost
        )


def build_exact_content_reuse_receipt(
    *,
    receipt_id: str,
    structure_id: str,
    content_bytes: bytes,
    semantic_hash: str,
    external_consumer_hash: str,
    training_consumer_hash: str,
    training_checkpoint_hash: str,
    inference_consumer_hash: str,
    inference_checkpoint_hash: str,
    train_example_hashes: tuple[str, ...],
    inference_example_hashes: tuple[str, ...],
) -> IdentityReuseReceipt:
    """Build a receipt for EXACT shared content reuse across all stages.

    All three stages bind the EXACT same content bytes. This is the primitive
    for testing whether exact identity reuse provides measurable benefit over
    semantic equivalence or independent reconstruction.
    """
    spec = StructuralContentSpec(
        structure_id=structure_id,
        content_bytes=content_bytes,
        semantic_hash=semantic_hash,
    )
    return IdentityReuseReceipt(
        receipt_id=receipt_id,
        mode=IdentityReuseMode.EXACT_SHARED_CONTENT,
        external_binding=StageBinding(
            stage="EXTERNAL_REASONING",
            content_spec=spec,
            consumer_artifact_hash=external_consumer_hash,
            reconstruction_cost=0.0,  # No reconstruction cost for exact reuse
        ),
        training_binding=StageBinding(
            stage="TRAINING",
            content_spec=spec,
            consumer_artifact_hash=training_consumer_hash,
            model_checkpoint_hash=training_checkpoint_hash,
            reconstruction_cost=0.0,  # No reconstruction cost for exact reuse
        ),
        inference_binding=StageBinding(
            stage="INFERENCE",
            content_spec=spec,
            consumer_artifact_hash=inference_consumer_hash,
            model_checkpoint_hash=inference_checkpoint_hash,
            reconstruction_cost=0.0,  # No reconstruction cost for exact reuse
        ),
        train_example_hashes=train_example_hashes,
        inference_example_hashes=inference_example_hashes,
        any_example_overlap=bool(set(train_example_hashes) & set(inference_example_hashes)),
    )


def build_semantic_equivalent_reuse_receipt(
    *,
    receipt_id: str,
    structure_id: str,
    semantic_hash: str,
    external_content_bytes: bytes,
    training_content_bytes: bytes,
    inference_content_bytes: bytes,
    external_consumer_hash: str,
    training_consumer_hash: str,
    training_checkpoint_hash: str,
    inference_consumer_hash: str,
    inference_checkpoint_hash: str,
    train_example_hashes: tuple[str, ...],
    inference_example_hashes: tuple[str, ...],
    reconstruction_costs: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> IdentityReuseReceipt:
    """Build a receipt for SEMANTICALLY-EQUIVALENT but independently-reconstructed content.

    Each stage has content that is semantically equivalent (same semantic_hash) but
    reconstructed independently (different content_bytes). This tests whether exact
    byte-level identity matters beyond semantic equivalence.
    """
    external_cost, training_cost, inference_cost = reconstruction_costs
    return IdentityReuseReceipt(
        receipt_id=receipt_id,
        mode=IdentityReuseMode.SEMANTIC_EQUIVALENT_RECONSTRUCTED,
        external_binding=StageBinding(
            stage="EXTERNAL_REASONING",
            content_spec=StructuralContentSpec(
                structure_id=structure_id,
                content_bytes=external_content_bytes,
                semantic_hash=semantic_hash,
            ),
            consumer_artifact_hash=external_consumer_hash,
            reconstruction_cost=external_cost,
        ),
        training_binding=StageBinding(
            stage="TRAINING",
            content_spec=StructuralContentSpec(
                structure_id=structure_id,
                content_bytes=training_content_bytes,
                semantic_hash=semantic_hash,
            ),
            consumer_artifact_hash=training_consumer_hash,
            model_checkpoint_hash=training_checkpoint_hash,
            reconstruction_cost=training_cost,
        ),
        inference_binding=StageBinding(
            stage="INFERENCE",
            content_spec=StructuralContentSpec(
                structure_id=structure_id,
                content_bytes=inference_content_bytes,
                semantic_hash=semantic_hash,
            ),
            consumer_artifact_hash=inference_consumer_hash,
            model_checkpoint_hash=inference_checkpoint_hash,
            reconstruction_cost=inference_cost,
        ),
        train_example_hashes=train_example_hashes,
        inference_example_hashes=inference_example_hashes,
        any_example_overlap=bool(set(train_example_hashes) & set(inference_example_hashes)),
    )


def build_structure_aware_receipt(
    *,
    receipt_id: str,
    structure_id: str,
    content_bytes: bytes,
    semantic_hash: str,
    which_aware: Literal["train_only", "inference_only"],
    external_consumer_hash: str,
    training_consumer_hash: str,
    training_checkpoint_hash: str,
    inference_consumer_hash: str,
    inference_checkpoint_hash: str,
    train_example_hashes: tuple[str, ...],
    inference_example_hashes: tuple[str, ...],
) -> IdentityReuseReceipt:
    """Build a receipt where structure awareness is only applied to one stage.

    This tests whether structure-aware reuse in only training or only inference
    provides benefit, compared to full three-stage reuse.
    """
    spec = StructuralContentSpec(
        structure_id=structure_id,
        content_bytes=content_bytes,
        semantic_hash=semantic_hash,
    )
    if which_aware == "train_only":
        mode = IdentityReuseMode.STRUCTURE_AWARE_TRAIN_ONLY
        # External and inference use generic retrieval (higher cost)
        external_cost = 1.0
        inference_cost = 1.0
        training_cost = 0.0  # Structure-aware reuse
    else:  # inference_only
        mode = IdentityReuseMode.STRUCTURE_AWARE_INFERENCE_ONLY
        external_cost = 1.0
        training_cost = 1.0
        inference_cost = 0.0  # Structure-aware reuse

    return IdentityReuseReceipt(
        receipt_id=receipt_id,
        mode=mode,
        external_binding=StageBinding(
            stage="EXTERNAL_REASONING",
            content_spec=spec,
            consumer_artifact_hash=external_consumer_hash,
            reconstruction_cost=external_cost,
        ),
        training_binding=StageBinding(
            stage="TRAINING",
            content_spec=spec,
            consumer_artifact_hash=training_consumer_hash,
            model_checkpoint_hash=training_checkpoint_hash,
            reconstruction_cost=training_cost,
        ),
        inference_binding=StageBinding(
            stage="INFERENCE",
            content_spec=spec,
            consumer_artifact_hash=inference_consumer_hash,
            model_checkpoint_hash=inference_checkpoint_hash,
            reconstruction_cost=inference_cost,
        ),
        train_example_hashes=train_example_hashes,
        inference_example_hashes=inference_example_hashes,
        any_example_overlap=bool(set(train_example_hashes) & set(inference_example_hashes)),
    )


def build_generic_retrieval_receipt(
    *,
    receipt_id: str,
    structure_id: str,
    content_bytes: bytes,
    semantic_hash: str,
    external_consumer_hash: str,
    training_consumer_hash: str,
    training_checkpoint_hash: str,
    inference_consumer_hash: str,
    inference_checkpoint_hash: str,
    train_example_hashes: tuple[str, ...],
    inference_example_hashes: tuple[str, ...],
    generic_retrieval_cost: float = 1.0,
) -> IdentityReuseReceipt:
    """Build a receipt where all stages use generic retrieval (no structure awareness).

    This is the baseline control: all three stages pay the cost of generic retrieval
    without exploiting structural identity.
    """
    spec = StructuralContentSpec(
        structure_id=structure_id,
        content_bytes=content_bytes,
        semantic_hash=semantic_hash,
    )
    return IdentityReuseReceipt(
        receipt_id=receipt_id,
        mode=IdentityReuseMode.GENERIC_RETRIEVAL,
        external_binding=StageBinding(
            stage="EXTERNAL_REASONING",
            content_spec=spec,
            consumer_artifact_hash=external_consumer_hash,
            reconstruction_cost=generic_retrieval_cost,
        ),
        training_binding=StageBinding(
            stage="TRAINING",
            content_spec=spec,
            consumer_artifact_hash=training_consumer_hash,
            model_checkpoint_hash=training_checkpoint_hash,
            reconstruction_cost=generic_retrieval_cost,
        ),
        inference_binding=StageBinding(
            stage="INFERENCE",
            content_spec=spec,
            consumer_artifact_hash=inference_consumer_hash,
            model_checkpoint_hash=inference_checkpoint_hash,
            reconstruction_cost=generic_retrieval_cost,
        ),
        train_example_hashes=train_example_hashes,
        inference_example_hashes=inference_example_hashes,
        any_example_overlap=bool(set(train_example_hashes) & set(inference_example_hashes)),
    )
