"""Fail-closed evaluator primitives for the Paper-II external scientific-analogy lane.

The evaluator is deliberately model-agnostic.  Gold labels/mappings live in the
case object supplied by the protected evaluation harness; candidate code only
sees the source/target text and must return a grounded witness.  Invalid or
partial structured output remains in hard denominators rather than disappearing
from safety/abstention metrics.

This module grants no scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable, Tuple


class AnalogyDecision(str, Enum):
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class GroundedMapping:
    source_term: str
    target_term: str
    source_span: str
    target_span: str


@dataclass(frozen=True)
class GroundedWitness:
    decision: AnalogyDecision
    mappings: Tuple[GroundedMapping, ...] = ()
    boundary_qoi: str = ""


@dataclass(frozen=True)
class ExternalAnalogyCase:
    case_id: str
    source_text: str
    target_text: str
    gold_decision: AnalogyDecision
    gold_mappings: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True)
class GroundedEvaluation:
    decision_correct: bool
    unsafe_false_accept: bool
    mapping_precision: float
    mapping_recall: float
    mapping_f1: float
    grounded_mapping_rate: float
    structured_valid: bool
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_SPACE = re.compile(r"\s+")


def _norm(value: str) -> str:
    return _SPACE.sub(" ", value.strip().casefold())


def _term_in_span(term: str, span: str) -> bool:
    return bool(_norm(term)) and _norm(term) in _norm(span)


def _exact_span(text: str, span: str) -> bool:
    return bool(span) and span in text


def _mapping_set(items: Iterable[Tuple[str, str]]) -> set[Tuple[str, str]]:
    return {(_norm(source), _norm(target)) for source, target in items}


def evaluate_grounded_witness(
    case: ExternalAnalogyCase, witness: GroundedWitness
) -> GroundedEvaluation:
    """Evaluate one protected case without compensatory omission semantics.

    A LICENSED witness is structurally valid only when every declared mapping is
    source/target-span bound and every mapped term is present in its declared
    exact span.  Duplicate normalized mappings are invalid.  REJECTED and
    CANNOT_CHECK outputs must not carry positive mappings; this prevents a
    malformed answer from being counted as an abstention while simultaneously
    smuggling a positive mapping.
    """

    reasons: list[str] = []
    predicted_pairs = [
        (_norm(item.source_term), _norm(item.target_term)) for item in witness.mappings
    ]
    if len(set(predicted_pairs)) != len(predicted_pairs):
        reasons.append("duplicate_mapping")

    grounded_flags: list[bool] = []
    for item in witness.mappings:
        grounded = (
            _exact_span(case.source_text, item.source_span)
            and _exact_span(case.target_text, item.target_span)
            and _term_in_span(item.source_term, item.source_span)
            and _term_in_span(item.target_term, item.target_span)
        )
        grounded_flags.append(grounded)
        if not grounded:
            reasons.append("mapping_not_exactly_source_span_grounded")

    if witness.decision is AnalogyDecision.LICENSED:
        if not witness.mappings:
            reasons.append("licensed_without_mapping")
        if not witness.boundary_qoi.strip():
            reasons.append("licensed_without_boundary_qoi")
    elif witness.mappings:
        reasons.append("nonlicensed_output_carries_positive_mapping")

    structured_valid = not reasons
    gold = _mapping_set(case.gold_mappings)
    predicted = set(predicted_pairs) if structured_valid else set()
    tp = len(gold & predicted)
    precision = tp / len(predicted) if predicted else (1.0 if not gold else 0.0)
    recall = tp / len(gold) if gold else (1.0 if not predicted else 0.0)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    grounded_rate = (
        sum(grounded_flags) / len(grounded_flags) if grounded_flags else (1.0 if not predicted else 0.0)
    )

    decision_correct = structured_valid and witness.decision is case.gold_decision
    unsafe_false_accept = (
        witness.decision is AnalogyDecision.LICENSED
        and case.gold_decision is not AnalogyDecision.LICENSED
    )
    return GroundedEvaluation(
        decision_correct=decision_correct,
        unsafe_false_accept=unsafe_false_accept,
        mapping_precision=precision,
        mapping_recall=recall,
        mapping_f1=f1,
        grounded_mapping_rate=grounded_rate,
        structured_valid=structured_valid,
        reasons=tuple(sorted(set(reasons))),
    )
