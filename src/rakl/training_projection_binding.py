"""Assurance sidecars for the proposal-only training projection.

The current training projection intentionally has no scheduler, but its v1 hashes
use ``repr``.  This sidecar adds canonical content binding, code/data environment
identity, uncertainty intervals, and split/leakage declarations without changing
legacy v1 snapshot identities.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

from .canonical_commitment import sha256_digest


@dataclass(frozen=True)
class IntervalEstimate:
    estimate: float
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not all(isfinite(x) for x in (self.estimate, self.lower, self.upper)):
            raise ValueError("interval values must be finite")
        if not self.lower <= self.estimate <= self.upper:
            raise ValueError("estimate must lie inside interval")


@dataclass(frozen=True)
class TrainingProjectionAssurance:
    assurance_id: str
    legacy_snapshot_hash: str
    canonical_snapshot_digest: str
    model_checkpoint_hash: str
    structural_catalog_hash: str
    canonical_structural_catalog_digest: str
    probe_family_hash: str
    code_commit_hash: str
    tokenizer_hash: str
    optimizer_config_hash: str
    sampling_policy_hash: str
    train_split_hash: str
    probe_split_hash: str
    fresh_assurance_split_hash: str
    effect_intervals: tuple[tuple[str, IntervalEstimate], ...]
    target_leak_detected: bool
    posthoc_selection_detected: bool

    def __post_init__(self) -> None:
        fields = (
            self.assurance_id,
            self.legacy_snapshot_hash,
            self.canonical_snapshot_digest,
            self.model_checkpoint_hash,
            self.structural_catalog_hash,
            self.canonical_structural_catalog_digest,
            self.probe_family_hash,
            self.code_commit_hash,
            self.tokenizer_hash,
            self.optimizer_config_hash,
            self.sampling_policy_hash,
            self.train_split_hash,
            self.probe_split_hash,
            self.fresh_assurance_split_hash,
        )
        if any(not str(x).strip() for x in fields):
            raise ValueError("training assurance requires complete identity bindings")
        if len({self.train_split_hash, self.probe_split_hash, self.fresh_assurance_split_hash}) != 3:
            raise ValueError("train/probe/fresh assurance splits must be distinct")
        keys = [k for k, _ in self.effect_intervals]
        if len(keys) != len(set(keys)) or any(not k for k in keys):
            raise ValueError("effect interval coordinates must be unique and nonempty")

    @property
    def ready_for_fresh_experiment(self) -> bool:
        return not self.target_leak_detected and not self.posthoc_selection_detected

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def canonical_training_snapshot_digest(snapshot: object) -> str:
    return sha256_digest(snapshot, domain="rakl-training-projection/v2")


def canonical_structural_catalog_digest(structural_objects: Sequence[object]) -> str:
    if not structural_objects:
        raise ValueError("canonical structural catalog cannot be empty")
    ids = [str(getattr(item, "structure_id")) for item in structural_objects]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("structural catalog identities must be nonempty and unique")
    # Sort by stable structural identity before typed canonicalization; object field
    # order remains intact inside each dataclass. This repairs the legacy catalog
    # digest dependency on Python repr without redefining the legacy digest.
    ordered = tuple(sorted(structural_objects, key=lambda item: str(getattr(item, "structure_id"))))
    return sha256_digest(ordered, domain="rakl-training-structural-catalog/v2")


def build_training_projection_assurance(
    snapshot: object,
    structural_objects: Sequence[object],
    *,
    assurance_id: str,
    code_commit_hash: str,
    tokenizer_hash: str,
    optimizer_config_hash: str,
    sampling_policy_hash: str,
    train_split_hash: str,
    probe_split_hash: str,
    fresh_assurance_split_hash: str,
    effect_intervals: Mapping[str, IntervalEstimate] | None = None,
    target_leak_detected: bool = False,
    posthoc_selection_detected: bool = False,
) -> TrainingProjectionAssurance:
    return TrainingProjectionAssurance(
        assurance_id=assurance_id,
        legacy_snapshot_hash=str(getattr(snapshot, "snapshot_hash")),
        canonical_snapshot_digest=canonical_training_snapshot_digest(snapshot),
        model_checkpoint_hash=str(getattr(snapshot, "model_checkpoint_hash")),
        structural_catalog_hash=str(getattr(snapshot, "structural_catalog_hash")),
        canonical_structural_catalog_digest=canonical_structural_catalog_digest(structural_objects),
        probe_family_hash=str(getattr(snapshot, "probe_family_hash")),
        code_commit_hash=code_commit_hash,
        tokenizer_hash=tokenizer_hash,
        optimizer_config_hash=optimizer_config_hash,
        sampling_policy_hash=sampling_policy_hash,
        train_split_hash=train_split_hash,
        probe_split_hash=probe_split_hash,
        fresh_assurance_split_hash=fresh_assurance_split_hash,
        effect_intervals=tuple(sorted((effect_intervals or {}).items())),
        target_leak_detected=target_leak_detected,
        posthoc_selection_detected=posthoc_selection_detected,
    )
