"""Reference semantics for RAKL Observation Contract v1.

This module is deliberately small and non-sovereign.  It provides pursuit/audit
objects only; it has no scientific-authority or evaluator-mutation API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Tuple


class InformationRegime(str, Enum):
    SOURCE_GROUNDED = "SOURCE_GROUNDED"
    SEMANTIC_NORMALIZED = "SEMANTIC_NORMALIZED"
    EXTERNAL_COMPLETION = "EXTERNAL_COMPLETION"


class AuditVerdict(str, Enum):
    LICENSED_VISIBLE = "LICENSED_VISIBLE"
    LICENSED_SEMANTIC = "LICENSED_SEMANTIC"
    LICENSED_EXTERNAL = "LICENSED_EXTERNAL"
    REQUIRES_NORMALIZATION = "REQUIRES_NORMALIZATION"
    REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE = "REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE"
    EVALUATOR_CONTRACT_TENSION = "EVALUATOR_CONTRACT_TENSION"
    CANNOT_CHECK = "CANNOT_CHECK"


class QuestionTarget(str, Enum):
    VISIBLE_STRUCTURE = "VISIBLE_STRUCTURE"
    SEMANTIC_STRUCTURE = "SEMANTIC_STRUCTURE"
    EXTERNAL_COMPLETION = "EXTERNAL_COMPLETION"
    BENCHMARK_REPRODUCTION = "BENCHMARK_REPRODUCTION"


@dataclass(frozen=True)
class ObservationContract:
    contract_id: str
    version: str
    regime: InformationRegime
    input_sources: Tuple[str, ...]
    allowed_normalizers: Tuple[str, ...] = ()
    external_knowledge_policy: str = "FORBIDDEN"
    provenance_required: bool = True
    abstention_allowed: bool = True
    evaluator_policy: str = "FROZEN_GOLD"
    evaluator_epoch: str = "epoch-1"

    def validate(self) -> None:
        if not self.contract_id or not self.version:
            raise ValueError("contract identity/version must be non-empty")
        if not self.input_sources:
            raise ValueError("at least one input source is required")
        if len(set(self.input_sources)) != len(self.input_sources):
            raise ValueError("input sources must be unique")
        if len(set(self.allowed_normalizers)) != len(self.allowed_normalizers):
            raise ValueError("normalizers must be unique")
        if self.regime is InformationRegime.SOURCE_GROUNDED:
            if self.allowed_normalizers:
                raise ValueError("source-grounded regime forbids semantic normalizers")
            if self.external_knowledge_policy != "FORBIDDEN":
                raise ValueError("source-grounded regime forbids external knowledge")
        elif self.regime is InformationRegime.SEMANTIC_NORMALIZED:
            if not self.allowed_normalizers:
                raise ValueError("semantic-normalized regime requires a named normalizer")
            if self.external_knowledge_policy != "FORBIDDEN":
                raise ValueError("semantic-normalized regime forbids external completion")
        elif self.regime is InformationRegime.EXTERNAL_COMPLETION:
            if self.external_knowledge_policy == "FORBIDDEN":
                raise ValueError("external-completion regime requires an explicit policy")
            if not self.provenance_required:
                raise ValueError("external completion requires provenance")
        else:  # defensive for future enum changes
            raise ValueError(f"unsupported regime: {self.regime}")
        if not self.evaluator_policy or not self.evaluator_epoch:
            raise ValueError("evaluator policy/epoch must be non-empty")

    def canonical_dict(self) -> dict:
        self.validate()
        d = asdict(self)
        d["regime"] = self.regime.value
        d["input_sources"] = list(self.input_sources)
        d["allowed_normalizers"] = list(self.allowed_normalizers)
        return d

    def digest(self) -> str:
        payload = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PairEvidence:
    mapping_id: str
    left_source_licensed: bool
    right_source_licensed: bool
    semantic_normalizable: bool = False
    normalizer_id: str | None = None
    external_support_declared: bool = False
    source_explicitly_disclaims: bool = False


@dataclass(frozen=True)
class QuestionContractReceipt:
    contract_digest: str
    question_target: QuestionTarget
    mapping_id: str
    verdict: AuditVerdict
    no_authority: bool = True


def audit_pair(contract: ObservationContract, evidence: PairEvidence) -> AuditVerdict:
    """Classify a mapping under the frozen information contract."""
    contract.validate()

    if evidence.source_explicitly_disclaims:
        return AuditVerdict.EVALUATOR_CONTRACT_TENSION

    if evidence.left_source_licensed and evidence.right_source_licensed:
        return AuditVerdict.LICENSED_VISIBLE

    if evidence.semantic_normalizable:
        if contract.regime is InformationRegime.SOURCE_GROUNDED:
            return AuditVerdict.REQUIRES_NORMALIZATION
        if contract.regime is InformationRegime.SEMANTIC_NORMALIZED:
            if evidence.normalizer_id and evidence.normalizer_id in contract.allowed_normalizers:
                return AuditVerdict.LICENSED_SEMANTIC
            return AuditVerdict.CANNOT_CHECK
        # External completion may still use an explicitly registered normalizer.
        if evidence.normalizer_id and evidence.normalizer_id in contract.allowed_normalizers:
            return AuditVerdict.LICENSED_SEMANTIC
        if evidence.external_support_declared:
            return AuditVerdict.LICENSED_EXTERNAL
        return AuditVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE

    if evidence.external_support_declared:
        if contract.regime is InformationRegime.EXTERNAL_COMPLETION:
            return AuditVerdict.LICENSED_EXTERNAL
        return AuditVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE

    return AuditVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE


def recall_ceiling(licensed_gold: int, total_gold: int) -> float:
    if total_gold <= 0:
        raise ValueError("total_gold must be positive")
    if licensed_gold < 0 or licensed_gold > total_gold:
        raise ValueError("licensed_gold must lie in [0,total_gold]")
    return licensed_gold / total_gold


def issue_receipt(
    contract: ObservationContract,
    question_target: QuestionTarget,
    evidence: PairEvidence,
) -> QuestionContractReceipt:
    return QuestionContractReceipt(
        contract_digest=contract.digest(),
        question_target=question_target,
        mapping_id=evidence.mapping_id,
        verdict=audit_pair(contract, evidence),
        no_authority=True,
    )
