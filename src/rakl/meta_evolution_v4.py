"""Manifest-digest identity successor for recursive RAKL self-evolution.

V3 removed display aliases from several digests but still accepted opaque domain,
problem-family and mechanic-class identifiers as if they were content identities.
V4 requires SHA-256 manifest digests for all load-bearing scope/family identity.
Human-readable labels are metadata only.

Frozen attacks:
``research/self_rakl_p4_p6_question_saturation_v4/META_EVOLUTION_V4_FROZEN_BENCHMARK.json``.
Research-only; no scientific or method-promotion authority.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re
from typing import Iterable
from .meta_evolution import EvolutionLayer

_HEX64=re.compile(r"^[0-9a-f]{64}$")

def content_digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def _sha(value: str, name: str) -> str:
    if not _HEX64.fullmatch(value): raise ValueError(f"{name} must be a lowercase SHA-256 content digest")
    return value

def _digests(values: tuple[str,...], name: str) -> tuple[str,...]:
    if not values: raise ValueError(f"{name} cannot be empty")
    checked=tuple(_sha(x,name) for x in values)
    if len(set(checked))!=len(checked): raise ValueError(f"{name} contains duplicate content digests")
    return tuple(sorted(checked))

@dataclass(frozen=True)
class CanonicalContextManifestV4:
    domain_manifest_digest: str
    problem_family_manifest_digest: str
    structural_substrate_digest: str
    evaluator_epoch_digest: str
    domain_label: str=""
    problem_family_label: str=""
    def __post_init__(self):
        for n in ("domain_manifest_digest","problem_family_manifest_digest","structural_substrate_digest","evaluator_epoch_digest"):
            _sha(getattr(self,n),n)
    @property
    def digest(self):
        return content_digest({"domain_manifest_digest":self.domain_manifest_digest,"problem_family_manifest_digest":self.problem_family_manifest_digest,"structural_substrate_digest":self.structural_substrate_digest,"evaluator_epoch_digest":self.evaluator_epoch_digest})
    @property
    def grants_scientific_authority(self): return False

@dataclass(frozen=True)
class MutationFamilyManifestV4:
    target_layer: EvolutionLayer
    operator_contract_digest: str
    precondition_digests: tuple[str,...]
    effect_digests: tuple[str,...]
    falsifier_digests: tuple[str,...]
    display_label: str=""
    def __post_init__(self):
        _sha(self.operator_contract_digest,"operator_contract_digest")
        _digests(self.precondition_digests,"precondition_digests")
        _digests(self.effect_digests,"effect_digests")
        _digests(self.falsifier_digests,"falsifier_digests")
    @property
    def digest(self):
        return content_digest({"target_layer":self.target_layer.value,"operator_contract_digest":self.operator_contract_digest,"precondition_digests":_digests(self.precondition_digests,"precondition_digests"),"effect_digests":_digests(self.effect_digests,"effect_digests"),"falsifier_digests":_digests(self.falsifier_digests,"falsifier_digests")})
    @property
    def grants_scientific_authority(self): return False

@dataclass(frozen=True)
class FailureEpochV4:
    evidence_epoch_digest: str
    family: MutationFamilyManifestV4
    def __post_init__(self): _sha(self.evidence_epoch_digest,"evidence_epoch_digest")

def distinct_failed_mutation_families_v4(epochs: Iterable[FailureEpochV4]) -> int:
    items=tuple(epochs); ids=[x.evidence_epoch_digest for x in items]
    if len(ids)!=len(set(ids)): raise ValueError("failure evidence epochs must be content-distinct")
    return len({x.family.digest for x in items})

@dataclass(frozen=True)
class ContextTransportWitnessV4:
    witness_digest: str
    operator_contract_digest: str
    target_layer: EvolutionLayer
    source_context_digest: str
    destination_context_digest: str
    evidence_receipt_digest: str
    display_label: str=""
    def __post_init__(self):
        for n in ("witness_digest","operator_contract_digest","source_context_digest","destination_context_digest","evidence_receipt_digest"):
            _sha(getattr(self,n),n)
        if self.source_context_digest==self.destination_context_digest: raise ValueError("transport requires distinct contexts")
    @property
    def grants_scientific_authority(self): return False
    @property
    def grants_method_promotion_authority(self): return False
