from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping


class TrialCondition(str, Enum):
    DIRECT_CORPUS = "DIRECT_CORPUS"
    RAKL_CONTEXT = "RAKL_CONTEXT"


@dataclass(frozen=True)
class MatchedModelConfig:
    model_id: str
    model_revision: str
    temperature: float
    max_output_tokens: int
    seed: int
    system_prompt: str

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_revision:
            raise ValueError("model identity and revision are required")
        if self.temperature < 0:
            raise ValueError("temperature cannot be negative")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")

    @property
    def system_prompt_hash(self) -> str:
        return hashlib.sha256(self.system_prompt.encode("utf-8")).hexdigest()

    @property
    def matching_tuple(self) -> tuple[object, ...]:
        return (
            self.model_id,
            self.model_revision,
            self.temperature,
            self.max_output_tokens,
            self.seed,
            self.system_prompt_hash,
        )


@dataclass(frozen=True)
class TrialResourceCeiling:
    """Matched *ceiling*, not matched usage, for a fair workflow comparison.

    RAKL is allowed to spend its budget differently from the direct arm because the
    preprocessing is the intervention.  The arms must nevertheless face the same
    externally registered resource envelope.  Actual usage is reported separately.
    """

    max_model_input_tokens: int
    max_model_output_tokens: int
    max_preprocessing_model_tokens: int
    max_preprocessing_tool_calls: int
    max_external_retrieval_calls: int
    max_wall_time_ms: int

    def __post_init__(self) -> None:
        if min(
            self.max_model_input_tokens,
            self.max_model_output_tokens,
            self.max_preprocessing_model_tokens,
            self.max_preprocessing_tool_calls,
            self.max_external_retrieval_calls,
            self.max_wall_time_ms,
        ) < 0:
            raise ValueError("resource ceilings cannot be negative")
        if self.max_model_input_tokens < 1 or self.max_model_output_tokens < 1 or self.max_wall_time_ms < 1:
            raise ValueError("model token and wall-time ceilings must be positive")


@dataclass(frozen=True)
class TrialResourceUsage:
    model_input_tokens: int
    model_output_tokens: int
    preprocessing_model_tokens: int
    preprocessing_tool_calls: int
    external_retrieval_calls: int
    wall_time_ms: int

    def __post_init__(self) -> None:
        if min(
            self.model_input_tokens,
            self.model_output_tokens,
            self.preprocessing_model_tokens,
            self.preprocessing_tool_calls,
            self.external_retrieval_calls,
            self.wall_time_ms,
        ) < 0:
            raise ValueError("resource usage cannot be negative")


@dataclass(frozen=True)
class ResourceUsageValidation:
    within_ceiling: bool
    problems: tuple[str, ...]


def validate_resource_usage(
    usage: TrialResourceUsage,
    ceiling: TrialResourceCeiling,
) -> ResourceUsageValidation:
    checks = (
        ("model_input_tokens", usage.model_input_tokens, ceiling.max_model_input_tokens),
        ("model_output_tokens", usage.model_output_tokens, ceiling.max_model_output_tokens),
        ("preprocessing_model_tokens", usage.preprocessing_model_tokens, ceiling.max_preprocessing_model_tokens),
        ("preprocessing_tool_calls", usage.preprocessing_tool_calls, ceiling.max_preprocessing_tool_calls),
        ("external_retrieval_calls", usage.external_retrieval_calls, ceiling.max_external_retrieval_calls),
        ("wall_time_ms", usage.wall_time_ms, ceiling.max_wall_time_ms),
    )
    problems = tuple(
        f"resource_ceiling_exceeded:{name}:{actual}>{maximum}"
        for name, actual, maximum in checks
        if actual > maximum
    )
    return ResourceUsageValidation(not problems, problems)


@dataclass(frozen=True)
class EvidenceCorpusFingerprint:
    source_ids: tuple[str, ...]
    source_hashes: tuple[str, ...]
    corpus_hash: str
    raw_bytes: int

    @classmethod
    def from_payloads(
        cls,
        payloads: Mapping[str, bytes] | Iterable[tuple[str, bytes]],
    ) -> "EvidenceCorpusFingerprint":
        items = tuple(payloads.items()) if isinstance(payloads, Mapping) else tuple(payloads)
        if not items:
            raise ValueError("at least one source payload is required")
        if len({source_id for source_id, _ in items}) != len(items):
            raise ValueError("source ids must be unique")
        if any(not source_id for source_id, _ in items):
            raise ValueError("source ids cannot be empty")
        if any(not isinstance(payload, bytes) for _, payload in items):
            raise TypeError("source payloads must be bytes")

        ordered = tuple(sorted(items, key=lambda item: item[0]))
        source_ids = tuple(source_id for source_id, _ in ordered)
        source_hashes = tuple(hashlib.sha256(payload).hexdigest() for _, payload in ordered)
        aggregate = bytearray()
        for (source_id, payload), payload_hash in zip(ordered, source_hashes, strict=True):
            source_id_bytes = source_id.encode("utf-8")
            aggregate.extend(len(source_id_bytes).to_bytes(4, "big"))
            aggregate.extend(source_id_bytes)
            aggregate.extend(len(payload).to_bytes(8, "big"))
            aggregate.extend(payload)
            aggregate.extend(bytes.fromhex(payload_hash))
        return cls(
            source_ids=source_ids,
            source_hashes=source_hashes,
            corpus_hash=hashlib.sha256(bytes(aggregate)).hexdigest(),
            raw_bytes=sum(len(payload) for _, payload in ordered),
        )


@dataclass(frozen=True)
class MatchedTrialArm:
    condition: TrialCondition
    model: MatchedModelConfig
    evidence: EvidenceCorpusFingerprint
    resource_ceiling: TrialResourceCeiling
    tool_policy_id: str
    output_schema_id: str
    question_set_hash: str
    evaluator_protocol_hash: str

    def __post_init__(self) -> None:
        required = (
            self.tool_policy_id,
            self.output_schema_id,
            self.question_set_hash,
            self.evaluator_protocol_hash,
        )
        if any(not item for item in required):
            raise ValueError("trial arm protocol identifiers cannot be empty")
        if self.resource_ceiling.max_model_output_tokens != self.model.max_output_tokens:
            raise ValueError("model output-token setting must equal the registered workflow ceiling")


@dataclass(frozen=True)
class MatchedTrialValidation:
    matched: bool
    problems: tuple[str, ...]


def validate_matched_arms(
    direct: MatchedTrialArm,
    rakl: MatchedTrialArm,
) -> MatchedTrialValidation:
    problems: list[str] = []
    if direct.condition is not TrialCondition.DIRECT_CORPUS:
        problems.append("direct_arm_condition_invalid")
    if rakl.condition is not TrialCondition.RAKL_CONTEXT:
        problems.append("rakl_arm_condition_invalid")
    if direct.model.matching_tuple != rakl.model.matching_tuple:
        problems.append("model_configuration_mismatch")
    if direct.evidence != rakl.evidence:
        problems.append("evidence_corpus_mismatch")
    if direct.resource_ceiling != rakl.resource_ceiling:
        problems.append("resource_ceiling_mismatch")
    if direct.tool_policy_id != rakl.tool_policy_id:
        problems.append("tool_policy_mismatch")
    if direct.output_schema_id != rakl.output_schema_id:
        problems.append("output_schema_mismatch")
    if direct.question_set_hash != rakl.question_set_hash:
        problems.append("question_set_mismatch")
    if direct.evaluator_protocol_hash != rakl.evaluator_protocol_hash:
        problems.append("evaluator_protocol_mismatch")
    return MatchedTrialValidation(not problems, tuple(problems))


@dataclass(frozen=True)
class PendulumStructuredAnswer:
    """Sealed machine-scoreable answer schema for the known-answer microtrial.

    The LLM may explain its reasoning in a separate text field at execution time,
    but authority-bearing scores are computed only from these registered fields and
    source ids. The schema intentionally asks about the contextual distinctions that
    the deterministic pendulum world was built to test.
    """

    small_angle_is_asymptotic: bool
    finite_amplitude_increases_period: bool
    period_differs_from_time_to_angle: bool
    context_alignment_required_before_contradiction: bool
    supporting_source_ids: tuple[str, ...]
    rejected_as_misaligned_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class PendulumKnownAnswerScore:
    conceptual_correct: int
    conceptual_total: int
    required_support_recall: float
    support_precision: float
    misalignment_recall: float
    unsupported_source_count: int
    exact_conceptual_pass: bool


_PENDULUM_REQUIRED_SUPPORT = frozenset({"S2", "S3", "S7"})
_PENDULUM_MISALIGNED = frozenset({"S4", "S5"})
_PENDULUM_ALLOWED_SUPPORT = frozenset({"S1", "S2", "S3", "S6", "S7", "S8"})


def score_pendulum_answer(answer: PendulumStructuredAnswer) -> PendulumKnownAnswerScore:
    conceptual_vector = (
        answer.small_angle_is_asymptotic,
        answer.finite_amplitude_increases_period,
        answer.period_differs_from_time_to_angle,
        answer.context_alignment_required_before_contradiction,
    )
    conceptual_correct = sum(bool(item) for item in conceptual_vector)
    support = frozenset(answer.supporting_source_ids)
    misaligned = frozenset(answer.rejected_as_misaligned_source_ids)
    required_hits = support & _PENDULUM_REQUIRED_SUPPORT
    supported_hits = support & _PENDULUM_ALLOWED_SUPPORT
    unsupported = support - _PENDULUM_ALLOWED_SUPPORT
    return PendulumKnownAnswerScore(
        conceptual_correct=conceptual_correct,
        conceptual_total=len(conceptual_vector),
        required_support_recall=len(required_hits) / len(_PENDULUM_REQUIRED_SUPPORT),
        support_precision=(len(supported_hits) / len(support) if support else 0.0),
        misalignment_recall=len(misaligned & _PENDULUM_MISALIGNED) / len(_PENDULUM_MISALIGNED),
        unsupported_source_count=len(unsupported),
        exact_conceptual_pass=conceptual_correct == len(conceptual_vector),
    )


def canonical_protocol_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
