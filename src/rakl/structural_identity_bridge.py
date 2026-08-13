"""Exact structural identity reuse across external reasoning, training, inference."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .canonical_commitment import sha256_digest


class StructuralUseStage(str, Enum):
    EXTERNAL_REASONING = "EXTERNAL_REASONING"
    TRAINING = "TRAINING"
    INFERENCE = "INFERENCE"


@dataclass(frozen=True)
class StructuralIdentityBundle:
    schema_version: str
    structure_id: str
    structure_content_hash: str
    qoi: str
    context_hash: str
    quotient_id: str | None
    quotient_view_hash: str | None
    witness_id: str | None
    witness_content_hash: str | None
    boundary_contract_hash: str

    def __post_init__(self) -> None:
        required = (self.schema_version, self.structure_id, self.structure_content_hash, self.qoi, self.context_hash, self.boundary_contract_hash)
        if any(not x for x in required):
            raise ValueError("structural identity bundle requires exact structure/QoI/context/boundary identity")
        if (self.quotient_id is None) != (self.quotient_view_hash is None):
            raise ValueError("quotient id/hash must be both present or absent")
        if (self.witness_id is None) != (self.witness_content_hash is None):
            raise ValueError("witness id/hash must be both present or absent")

    @property
    def digest(self) -> str:
        return sha256_digest(self, domain="rakl-structural-identity-bundle/v1")


def build_structural_identity_bundle(
    structural_object: object,
    *,
    context_hash: str,
    boundary_contract: object,
    quotient_view: object | None = None,
    witness: object | None = None,
) -> StructuralIdentityBundle:
    """Derive the bundle from actual content rather than caller-named hashes.

    This is the preferred experiment-construction surface. Existing native hashes
    may still be stored inside the objects, but the cross-stage identity is the
    typed canonical digest of the exact object presented here.
    """
    structure_id = str(getattr(structural_object, "structure_id"))
    qoi = str(getattr(structural_object, "qoi"))
    if not structure_id or not qoi or not context_hash:
        raise ValueError("structural object/QoI/context identity required")
    quotient_id = None
    quotient_hash = None
    if quotient_view is not None:
        quotient_id = str(getattr(quotient_view, "quotient_id"))
        if not quotient_id:
            raise ValueError("quotient view requires quotient_id")
        quotient_hash = sha256_digest(quotient_view, domain="rakl-shared-structural-quotient/v1")
    witness_id = None
    witness_hash = None
    if witness is not None:
        witness_id = str(getattr(witness, "witness_id"))
        if not witness_id:
            raise ValueError("structural witness requires witness_id")
        witness_hash = sha256_digest(witness, domain="rakl-shared-structural-witness/v1")
    return StructuralIdentityBundle(
        schema_version="rakl.structural-identity-bundle/v1",
        structure_id=structure_id,
        structure_content_hash=sha256_digest(structural_object, domain="rakl-shared-structural-object/v1"),
        qoi=qoi,
        context_hash=context_hash,
        quotient_id=quotient_id,
        quotient_view_hash=quotient_hash,
        witness_id=witness_id,
        witness_content_hash=witness_hash,
        boundary_contract_hash=sha256_digest(boundary_contract, domain="rakl-shared-boundary-contract/v1"),
    )


@dataclass(frozen=True)
class StructuralUseBinding:
    binding_id: str
    stage: StructuralUseStage
    structural_bundle_digest: str
    consumer_artifact_hash: str
    model_checkpoint_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.binding_id or not self.structural_bundle_digest or not self.consumer_artifact_hash:
            raise ValueError("structural use binding identity required")
        if self.stage in {StructuralUseStage.TRAINING, StructuralUseStage.INFERENCE} and not self.model_checkpoint_hash:
            raise ValueError("training/inference structural use must bind model checkpoint")
        if self.stage is StructuralUseStage.EXTERNAL_REASONING and self.model_checkpoint_hash is not None:
            raise ValueError("external structural substrate identity must not be redefined by a model checkpoint")


@dataclass(frozen=True)
class SharedIdentityReuseReceipt:
    receipt_id: str
    bundle: StructuralIdentityBundle
    bindings: tuple[StructuralUseBinding, ...]
    train_examples_hash: str
    fresh_inference_examples_hash: str
    any_example_overlap: bool

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.train_examples_hash or not self.fresh_inference_examples_hash:
            raise ValueError("identity reuse receipt requires frozen split identities")
        stages = [b.stage for b in self.bindings]
        if set(stages) != set(StructuralUseStage) or len(stages) != 3:
            raise ValueError("exactly one external/training/inference binding required")
        expected = self.bundle.digest
        if any(b.structural_bundle_digest != expected for b in self.bindings):
            raise ValueError("all stages must consume the exact same structural identity bundle")
        if self.train_examples_hash == self.fresh_inference_examples_hash or self.any_example_overlap:
            raise ValueError("fresh inference panel must be identity-disjoint from training examples")

    @property
    def exact_identity_reuse_established(self) -> bool:
        return True

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def build_shared_identity_reuse_receipt(
    *,
    receipt_id: str,
    bundle: StructuralIdentityBundle,
    bindings: tuple[StructuralUseBinding, ...],
    train_example_ids: tuple[str, ...],
    fresh_inference_example_ids: tuple[str, ...],
) -> SharedIdentityReuseReceipt:
    if not train_example_ids or not fresh_inference_example_ids:
        raise ValueError("train and fresh inference panels must be nonempty")
    if len(train_example_ids) != len(set(train_example_ids)) or len(fresh_inference_example_ids) != len(set(fresh_inference_example_ids)):
        raise ValueError("example identities must be unique within each split")
    overlap = bool(set(train_example_ids) & set(fresh_inference_example_ids))
    return SharedIdentityReuseReceipt(
        receipt_id=receipt_id,
        bundle=bundle,
        bindings=bindings,
        train_examples_hash=sha256_digest(tuple(sorted(train_example_ids)), domain="rakl-shared-identity-train-examples/v1"),
        fresh_inference_examples_hash=sha256_digest(tuple(sorted(fresh_inference_example_ids)), domain="rakl-shared-identity-fresh-examples/v1"),
        any_example_overlap=overlap,
    )
