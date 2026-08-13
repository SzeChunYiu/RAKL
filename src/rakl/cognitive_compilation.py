"""Governed cognitive-compilation state machine (proposal/assurance only).

No optimizer is implemented here.  The contract exists to prevent the future
loop "failure -> weight update -> better metric -> scientific promotion" from
collapsing authority domains.  Training-only steps must preserve the epistemic
projection hash, and model-incumbent promotion requires fresh assurance by a
separate evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .canonical_commitment import sha256_digest


class CompilationVerdict(str, Enum):
    CHALLENGER_ONLY = "CHALLENGER_ONLY"
    FRESH_ASSURANCE_REQUIRED = "FRESH_ASSURANCE_REQUIRED"
    MODEL_PROMOTION_ELIGIBLE = "MODEL_PROMOTION_ELIGIBLE"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CompilationProposal:
    proposal_id: str
    base_model_checkpoint_hash: str
    source_failure_receipt_ids: tuple[str, ...]
    diagnosis_receipt_hash: str
    structural_identity_bundle_digest: str
    training_data_hash: str
    training_recipe_hash: str
    code_hash: str
    proposer_id: str
    frozen_before_training: bool

    def __post_init__(self) -> None:
        required = (
            self.proposal_id, self.base_model_checkpoint_hash, self.source_failure_receipt_ids,
            self.diagnosis_receipt_hash, self.structural_identity_bundle_digest,
            self.training_data_hash, self.training_recipe_hash, self.code_hash, self.proposer_id,
        )
        if any(not x for x in required):
            raise ValueError("compilation proposal requires frozen causal/provenance identities")
        if not self.frozen_before_training:
            raise ValueError("compilation hypothesis must be frozen before training")

    @property
    def digest(self) -> str:
        return sha256_digest(self, domain="rakl-cognitive-compilation-proposal/v1")


@dataclass(frozen=True)
class ChallengerTrainingReceipt:
    receipt_id: str
    proposal_digest: str
    challenger_checkpoint_hash: str
    execution_environment_hash: str
    training_log_hash: str
    epistemic_projection_before_hash: str
    epistemic_projection_after_hash: str

    def __post_init__(self) -> None:
        if any(not x for x in (
            self.receipt_id, self.proposal_digest, self.challenger_checkpoint_hash,
            self.execution_environment_hash, self.training_log_hash,
            self.epistemic_projection_before_hash, self.epistemic_projection_after_hash,
        )):
            raise ValueError("challenger receipt requires full subject binding")
        if self.epistemic_projection_before_hash != self.epistemic_projection_after_hash:
            raise ValueError("training-only cognitive compilation violated epistemic noninterference")


@dataclass(frozen=True)
class FreshCompilationAssurance:
    assurance_id: str
    proposal_digest: str
    challenger_checkpoint_hash: str
    fresh_split_hash: str
    training_data_hash: str
    split_overlap_detected: bool
    evaluator_id: str
    proposer_id: str
    evaluator_artifact_hash: str
    comparator_ids: tuple[str, ...]
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            self.assurance_id, self.proposal_digest, self.challenger_checkpoint_hash, self.fresh_split_hash,
            self.training_data_hash, self.evaluator_id, self.proposer_id, self.evaluator_artifact_hash,
        )
        if any(not x for x in required):
            raise ValueError("fresh assurance requires bound challenger/split/evaluator")
        if self.evaluator_id == self.proposer_id:
            raise ValueError("fresh assurance evaluator must be separate from proposer")
        if self.fresh_split_hash == self.training_data_hash or self.split_overlap_detected:
            raise ValueError("fresh assurance set must be disjoint from training data")
        if self.passed and self.failure_reasons:
            raise ValueError("passing assurance cannot carry failure reasons")
        if not self.passed and not self.failure_reasons:
            raise ValueError("failed assurance requires reasons")
        if len(self.comparator_ids) < 1:
            raise ValueError("fresh assurance requires at least one frozen comparator")
        if len(self.comparator_ids) != len(set(self.comparator_ids)) or any(not item for item in self.comparator_ids):
            raise ValueError("frozen comparator identities must be unique and nonempty")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def compilation_decision(
    proposal: CompilationProposal,
    training: ChallengerTrainingReceipt | None,
    assurance: FreshCompilationAssurance | None,
    *,
    resolved_fresh_assurance_ids: frozenset[str] = frozenset(),
) -> CompilationVerdict:
    if training is None:
        return CompilationVerdict.CHALLENGER_ONLY
    if training.proposal_digest != proposal.digest:
        return CompilationVerdict.REJECT
    if assurance is None:
        return CompilationVerdict.FRESH_ASSURANCE_REQUIRED
    if assurance.proposal_digest != proposal.digest or assurance.training_data_hash != proposal.training_data_hash:
        return CompilationVerdict.REJECT
    if assurance.challenger_checkpoint_hash != training.challenger_checkpoint_hash:
        return CompilationVerdict.REJECT
    if not assurance.passed:
        return CompilationVerdict.REJECT
    # A caller-declared ``passed=True`` is not a promotion root. The assurance
    # must first be resolved by the protected evaluator/replay layer.
    if assurance.assurance_id not in resolved_fresh_assurance_ids:
        return CompilationVerdict.CANNOT_CHECK
    return CompilationVerdict.MODEL_PROMOTION_ELIGIBLE


def build_fresh_compilation_assurance(
    proposal: CompilationProposal,
    *,
    assurance_id: str,
    challenger_checkpoint_hash: str,
    training_example_ids: tuple[str, ...],
    fresh_example_ids: tuple[str, ...],
    evaluator_id: str,
    evaluator_artifact_hash: str,
    comparator_ids: tuple[str, ...],
    passed: bool,
    failure_reasons: tuple[str, ...] = (),
) -> FreshCompilationAssurance:
    if not training_example_ids or not fresh_example_ids:
        raise ValueError("training/fresh assurance example panels must be nonempty")
    if len(training_example_ids) != len(set(training_example_ids)) or len(fresh_example_ids) != len(set(fresh_example_ids)):
        raise ValueError("training/fresh example identities must be unique within split")
    overlap = bool(set(training_example_ids) & set(fresh_example_ids))
    fresh_hash = sha256_digest(tuple(sorted(fresh_example_ids)), domain="rakl-cognitive-compilation-fresh-examples/v1")
    return FreshCompilationAssurance(
        assurance_id=assurance_id,
        proposal_digest=proposal.digest,
        challenger_checkpoint_hash=challenger_checkpoint_hash,
        fresh_split_hash=fresh_hash,
        training_data_hash=proposal.training_data_hash,
        split_overlap_detected=overlap,
        evaluator_id=evaluator_id,
        proposer_id=proposal.proposer_id,
        evaluator_artifact_hash=evaluator_artifact_hash,
        comparator_ids=comparator_ids,
        passed=passed,
        failure_reasons=failure_reasons,
    )
