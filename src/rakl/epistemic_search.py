"""Proposal/routing-only Scientific / Epistemic Search Engine primitives (#433).

The module borrows mature search-engine ideas (typed query expansion, multiple
indexes, graph/navigation signals, diversification, interaction spaces, and
feedback) while enforcing a RAKL-specific boundary:

    rank / centrality / popularity / inspection frequency != scientific authority

It does not crawl the public internet itself and it does not replace
``ProblemFibre``.  Instead it defines a bounded layer that can compile a fibre's
research residual into typed search intents, fuse already-retrieved candidates,
and construct an immutable interaction-space snapshot for downstream tools.

All scores are routing/search scores only.  No object in this module grants
scientific or target authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable, Sequence, Tuple


class SearchVertical(str, Enum):
    LITERATURE = "LITERATURE"
    DATA = "DATA"
    CODE = "CODE"
    THEOREM_PROOF = "THEOREM_PROOF"
    EXPERIMENT = "EXPERIMENT"
    STANDARD = "STANDARD"
    FAILURE_NEGATIVE_RESULT = "FAILURE_NEGATIVE_RESULT"
    METHOD_TOOL = "METHOD_TOOL"
    CURRENT_WORK = "CURRENT_WORK"
    CROSS_DOMAIN_ANALOGY = "CROSS_DOMAIN_ANALOGY"


class SearchIndexKind(str, Enum):
    LEXICAL = "LEXICAL"
    SEMANTIC = "SEMANTIC"
    STRUCTURAL = "STRUCTURAL"
    CLAIM_EVIDENCE = "CLAIM_EVIDENCE"
    CITATION_DERIVATION = "CITATION_DERIVATION"
    FAILURE_NEGATIVE_HISTORY = "FAILURE_NEGATIVE_HISTORY"
    METHOD_OPERATOR = "METHOD_OPERATOR"
    TEMPORAL = "TEMPORAL"


class SearchIntentKind(str, Enum):
    EXACT_TERMINOLOGY = "EXACT_TERMINOLOGY"
    SOURCE_NATIVE_TERMINOLOGY = "SOURCE_NATIVE_TERMINOLOGY"
    SEMANTIC_EXPANSION = "SEMANTIC_EXPANSION"
    STRUCTURAL_MECHANISM = "STRUCTURAL_MECHANISM"
    COUNTEREXAMPLE_REFUTATION = "COUNTEREXAMPLE_REFUTATION"
    CONTRADICTION = "CONTRADICTION"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    METHOD_OPERATOR = "METHOD_OPERATOR"
    CROSS_DOMAIN_JUMP = "CROSS_DOMAIN_JUMP"
    CITATION_BACKWARD = "CITATION_BACKWARD"
    CITATION_FORWARD = "CITATION_FORWARD"
    INDEPENDENT_CORROBORATION = "INDEPENDENT_CORROBORATION"
    FRESHNESS_RETRACTION = "FRESHNESS_RETRACTION"


class EvidenceStance(str, Enum):
    SUPPORT = "SUPPORT"
    REFUTE = "REFUTE"
    CONTEXT = "CONTEXT"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    RETRACTION_CORRECTION = "RETRACTION_CORRECTION"
    NEUTRAL = "NEUTRAL"


class EpistemicSpamFlag(str, Enum):
    SAME_ROOT_ECHO = "SAME_ROOT_ECHO"
    RETRACTED_OR_SUPERSEDED = "RETRACTED_OR_SUPERSEDED"
    SYNTHETIC_CONSENSUS = "SYNTHETIC_CONSENSUS"
    SELF_CITATION_LOOP = "SELF_CITATION_LOOP"
    BENCHMARK_TARGET_LEAK = "BENCHMARK_TARGET_LEAK"
    KEYWORD_STUFFING_SUSPECTED = "KEYWORD_STUFFING_SUSPECTED"


@dataclass(frozen=True)
class ScientificSearchQuestion:
    question_id: str
    root_goal: str
    atom_id: str
    residual_terms: Tuple[str, ...]
    structural_coordinates: Tuple[str, ...]
    unresolved_obligations: Tuple[str, ...] = ()
    source_native_terms: Tuple[str, ...] = ()
    semantic_expansions: Tuple[str, ...] = ()
    candidate_mechanism: str | None = None

    def __post_init__(self) -> None:
        if not self.question_id.strip() or not self.root_goal.strip() or not self.atom_id.strip():
            raise ValueError("scientific search question requires question/root/atom ids")

    @property
    def root_goal_hash(self) -> str:
        return sha256(self.root_goal.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SearchIntent:
    intent_id: str
    kind: SearchIntentKind
    terms: Tuple[str, ...]
    purpose: str
    root_goal_hash: str
    atom_id: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SearchRankVector:
    query_relevance: float
    root_obligation_relevance: float
    expected_information_gain: float
    structural_fit: float
    context_alignment: float
    source_authenticity: float
    freshness: float
    independent_root_contribution: float
    contradiction_value: float
    negative_result_value: float
    novel_route_value: float
    graph_centrality: float
    retrieval_cost: float
    verification_cost: float
    failure_risk: float

    def __post_init__(self) -> None:
        for value in self.__dict__.values():
            if not isinstance(value, (int, float)):
                raise TypeError("search rank coordinates must be numeric")
        if self.retrieval_cost < 0 or self.verification_cost < 0 or self.failure_risk < 0:
            raise ValueError("search cost/risk coordinates cannot be negative")


@dataclass(frozen=True)
class SearchCandidate:
    candidate_id: str
    vertical: SearchVertical
    index_kinds: Tuple[SearchIndexKind, ...]
    rank: SearchRankVector
    evidence_root_id: str | None
    canonical_content_id: str
    mechanism_family: str | None
    stance: EvidenceStance
    negative_history: bool = False
    retracted_or_superseded: bool = False
    synthetic_or_generated_echo: bool = False
    self_citation_loop: bool = False
    benchmark_target_leak: bool = False
    keyword_overlap_ratio: float = 0.0
    substantive_match_score: float = 0.0

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.canonical_content_id.strip():
            raise ValueError("search candidate requires identity and canonical content id")
        if not 0.0 <= self.keyword_overlap_ratio <= 1.0:
            raise ValueError("keyword_overlap_ratio must be in [0,1]")
        if not 0.0 <= self.substantive_match_score <= 1.0:
            raise ValueError("substantive_match_score must be in [0,1]")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_evidence_independence(self) -> bool:
        return False


@dataclass(frozen=True)
class CandidateSpamAssessment:
    candidate_id: str
    flags: Tuple[EpistemicSpamFlag, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ResearchInteractionSpace:
    space_id: str
    question_id: str
    root_goal_hash: str
    atom_id: str
    problem_fibre_snapshot_hash: str | None
    intent_ids: Tuple[str, ...]
    candidate_ids: Tuple[str, ...]
    evidence_root_ids: Tuple[str, ...]
    negative_history_ids: Tuple[str, ...]
    allowed_tool_ids: Tuple[str, ...]
    unresolved_obligations: Tuple[str, ...]
    max_candidates: int
    snapshot_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SearchFeedback:
    question_id: str
    intent_id: str
    candidate_id: str
    rank_position: int
    exposure_probability: float
    inspected: bool
    changed_action: bool
    verified_downstream_success: bool | None
    cost: float

    def __post_init__(self) -> None:
        if self.rank_position < 1:
            raise ValueError("rank_position must be positive")
        if not 0.0 < self.exposure_probability <= 1.0:
            raise ValueError("exposure_probability must be in (0,1]")
        if self.cost < 0:
            raise ValueError("feedback cost cannot be negative")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def compile_search_intents(question: ScientificSearchQuestion) -> Tuple[SearchIntent, ...]:
    """Compile one scientific residual into purpose-bound search intents."""

    base = tuple(dict.fromkeys(term for term in question.residual_terms if term.strip()))
    structural = tuple(dict.fromkeys(term for term in question.structural_coordinates if term.strip()))
    intents: list[tuple[SearchIntentKind, Tuple[str, ...], str]] = []

    if base:
        intents.append((SearchIntentKind.EXACT_TERMINOLOGY, base, "exact terms for the current residual"))
    if question.source_native_terms:
        intents.append(
            (
                SearchIntentKind.SOURCE_NATIVE_TERMINOLOGY,
                tuple(dict.fromkeys(question.source_native_terms)),
                "recover source-native vocabulary without changing the root question",
            )
        )
    if question.semantic_expansions:
        intents.append(
            (
                SearchIntentKind.SEMANTIC_EXPANSION,
                tuple(dict.fromkeys(question.semantic_expansions)),
                "bounded synonym/paraphrase expansion for recall",
            )
        )
    if structural or question.candidate_mechanism:
        terms = structural + ((question.candidate_mechanism,) if question.candidate_mechanism else ())
        intents.append(
            (SearchIntentKind.STRUCTURAL_MECHANISM, tuple(dict.fromkeys(terms)), "search mechanism/structure rather than surface nouns")
        )
    if base:
        intents.extend(
            [
                (SearchIntentKind.COUNTEREXAMPLE_REFUTATION, base, "seek counterexamples/refutations to the active claim or route"),
                (SearchIntentKind.CONTRADICTION, base, "seek contradictory results and boundary mismatches"),
                (SearchIntentKind.NEGATIVE_RESULT, base, "seek null/negative results and failed routes"),
                (SearchIntentKind.CITATION_BACKWARD, base, "trace upstream sources/evidence roots"),
                (SearchIntentKind.CITATION_FORWARD, base, "trace downstream corrections, uses and challenges"),
                (SearchIntentKind.INDEPENDENT_CORROBORATION, base, "seek genuinely independent evidence roots"),
                (SearchIntentKind.FRESHNESS_RETRACTION, base, "seek recent versions, corrections, retractions and supersessions"),
            ]
        )
    if question.unresolved_obligations:
        intents.append(
            (
                SearchIntentKind.METHOD_OPERATOR,
                tuple(dict.fromkeys(question.unresolved_obligations)),
                "seek methods/tools that can discharge unresolved obligations",
            )
        )
    if structural:
        intents.append(
            (
                SearchIntentKind.CROSS_DOMAIN_JUMP,
                structural,
                "seek distant domains with preserved deep structure; proposal-only",
            )
        )

    return tuple(
        SearchIntent(
            intent_id=f"{question.question_id}:q{index:02d}:{kind.value}",
            kind=kind,
            terms=terms,
            purpose=purpose,
            root_goal_hash=question.root_goal_hash,
            atom_id=question.atom_id,
        )
        for index, (kind, terms, purpose) in enumerate(intents, start=1)
    )


def _benefit_coordinates(vector: SearchRankVector) -> tuple[float, ...]:
    return (
        vector.query_relevance,
        vector.root_obligation_relevance,
        vector.expected_information_gain,
        vector.structural_fit,
        vector.context_alignment,
        vector.source_authenticity,
        vector.freshness,
        vector.independent_root_contribution,
        vector.contradiction_value,
        vector.negative_result_value,
        vector.novel_route_value,
        vector.graph_centrality,
    )


def _burden_coordinates(vector: SearchRankVector) -> tuple[float, ...]:
    return (vector.retrieval_cost, vector.verification_cost, vector.failure_risk)


def dominates(left: SearchCandidate, right: SearchCandidate) -> bool:
    """Pareto dominance for routing utility; never a truth/authority relation."""

    left_benefit = _benefit_coordinates(left.rank)
    right_benefit = _benefit_coordinates(right.rank)
    left_burden = _burden_coordinates(left.rank)
    right_burden = _burden_coordinates(right.rank)
    weakly_better = all(a >= b for a, b in zip(left_benefit, right_benefit)) and all(
        a <= b for a, b in zip(left_burden, right_burden)
    )
    strictly_better = any(a > b for a, b in zip(left_benefit, right_benefit)) or any(
        a < b for a, b in zip(left_burden, right_burden)
    )
    return weakly_better and strictly_better


def pareto_front(candidates: Iterable[SearchCandidate]) -> Tuple[SearchCandidate, ...]:
    pool = tuple(candidates)
    front = [candidate for candidate in pool if not any(dominates(other, candidate) for other in pool if other is not candidate)]
    return tuple(sorted(front, key=lambda item: item.candidate_id))


def _routing_tiebreak(candidate: SearchCandidate) -> tuple[float, ... | str]:
    """Deterministic routing tiebreak *after* vector/Pareto reasoning.

    Centrality appears late and cannot compensate for poor root/context fit.
    """

    rank = candidate.rank
    return (
        -rank.root_obligation_relevance,
        -rank.expected_information_gain,
        -rank.context_alignment,
        -rank.structural_fit,
        -max(rank.contradiction_value, rank.negative_result_value),
        -rank.independent_root_contribution,
        -rank.query_relevance,
        rank.failure_risk,
        rank.verification_cost + rank.retrieval_cost,
        -rank.graph_centrality,
        candidate.candidate_id,
    )


def detect_epistemic_spam(candidates: Sequence[SearchCandidate]) -> Tuple[CandidateSpamAssessment, ...]:
    root_counts: dict[str, int] = {}
    for candidate in candidates:
        if candidate.evidence_root_id:
            root_counts[candidate.evidence_root_id] = root_counts.get(candidate.evidence_root_id, 0) + 1

    assessments: list[CandidateSpamAssessment] = []
    for candidate in candidates:
        flags: list[EpistemicSpamFlag] = []
        if candidate.evidence_root_id and root_counts.get(candidate.evidence_root_id, 0) > 1:
            flags.append(EpistemicSpamFlag.SAME_ROOT_ECHO)
        if candidate.retracted_or_superseded:
            flags.append(EpistemicSpamFlag.RETRACTED_OR_SUPERSEDED)
        if candidate.synthetic_or_generated_echo:
            flags.append(EpistemicSpamFlag.SYNTHETIC_CONSENSUS)
        if candidate.self_citation_loop:
            flags.append(EpistemicSpamFlag.SELF_CITATION_LOOP)
        if candidate.benchmark_target_leak:
            flags.append(EpistemicSpamFlag.BENCHMARK_TARGET_LEAK)
        if candidate.keyword_overlap_ratio >= 0.9 and candidate.substantive_match_score <= 0.2:
            flags.append(EpistemicSpamFlag.KEYWORD_STUFFING_SUSPECTED)
        assessments.append(CandidateSpamAssessment(candidate.candidate_id, tuple(flags)))
    return tuple(assessments)


def diversify_candidates(
    candidates: Sequence[SearchCandidate],
    *,
    limit: int,
    max_per_evidence_root: int = 1,
    max_per_mechanism_family: int = 2,
    preserve_counterevidence: bool = True,
) -> Tuple[SearchCandidate, ...]:
    """Select a bounded, epistemically diverse routing set."""

    if limit < 1 or max_per_evidence_root < 1 or max_per_mechanism_family < 1:
        raise ValueError("diversification limits must be positive")

    spam = {item.candidate_id: set(item.flags) for item in detect_epistemic_spam(candidates)}
    # Benchmark-target leakage is never an eligible evaluation/search input. Other
    # flags remain visible and may be useful for correction/retraction audits.
    eligible = [
        item
        for item in candidates
        if EpistemicSpamFlag.BENCHMARK_TARGET_LEAK not in spam[item.candidate_id]
    ]
    ordered = sorted(eligible, key=_routing_tiebreak)

    selected: list[SearchCandidate] = []
    root_counts: dict[str, int] = {}
    mechanism_counts: dict[str, int] = {}

    def admissible(candidate: SearchCandidate) -> bool:
        if candidate.evidence_root_id and root_counts.get(candidate.evidence_root_id, 0) >= max_per_evidence_root:
            return False
        if candidate.mechanism_family and mechanism_counts.get(candidate.mechanism_family, 0) >= max_per_mechanism_family:
            return False
        if any(existing.canonical_content_id == candidate.canonical_content_id for existing in selected):
            return False
        return True

    if preserve_counterevidence:
        counter = next(
            (
                item
                for item in ordered
                if item.stance in {EvidenceStance.REFUTE, EvidenceStance.NEGATIVE_RESULT, EvidenceStance.RETRACTION_CORRECTION}
                and admissible(item)
            ),
            None,
        )
        if counter is not None:
            selected.append(counter)
            if counter.evidence_root_id:
                root_counts[counter.evidence_root_id] = 1
            if counter.mechanism_family:
                mechanism_counts[counter.mechanism_family] = 1

    for candidate in ordered:
        if len(selected) >= limit:
            break
        if candidate in selected or not admissible(candidate):
            continue
        selected.append(candidate)
        if candidate.evidence_root_id:
            root_counts[candidate.evidence_root_id] = root_counts.get(candidate.evidence_root_id, 0) + 1
        if candidate.mechanism_family:
            mechanism_counts[candidate.mechanism_family] = mechanism_counts.get(candidate.mechanism_family, 0) + 1

    return tuple(selected)


def build_interaction_space(
    question: ScientificSearchQuestion,
    intents: Sequence[SearchIntent],
    candidates: Sequence[SearchCandidate],
    *,
    space_id: str,
    max_candidates: int,
    problem_fibre_snapshot_hash: str | None = None,
    allowed_tool_ids: Sequence[str] = (),
) -> ResearchInteractionSpace:
    """Build an immutable bounded search space that can compose with ProblemFibre."""

    if not space_id.strip() or max_candidates < 1:
        raise ValueError("interaction space requires id and positive candidate budget")
    if any(intent.root_goal_hash != question.root_goal_hash or intent.atom_id != question.atom_id for intent in intents):
        raise ValueError("query drift: intent is not bound to the same root goal/atom")

    selected = diversify_candidates(candidates, limit=max_candidates)
    evidence_roots = tuple(sorted({item.evidence_root_id for item in selected if item.evidence_root_id}))
    negative_ids = tuple(sorted(item.candidate_id for item in selected if item.negative_history or item.stance is EvidenceStance.NEGATIVE_RESULT))
    payload = repr(
        (
            space_id,
            question.question_id,
            question.root_goal_hash,
            question.atom_id,
            problem_fibre_snapshot_hash,
            tuple(intent.intent_id for intent in intents),
            tuple(item.candidate_id for item in selected),
            evidence_roots,
            negative_ids,
            tuple(sorted(set(allowed_tool_ids))),
            question.unresolved_obligations,
            max_candidates,
        )
    ).encode("utf-8")
    return ResearchInteractionSpace(
        space_id=space_id,
        question_id=question.question_id,
        root_goal_hash=question.root_goal_hash,
        atom_id=question.atom_id,
        problem_fibre_snapshot_hash=problem_fibre_snapshot_hash,
        intent_ids=tuple(intent.intent_id for intent in intents),
        candidate_ids=tuple(item.candidate_id for item in selected),
        evidence_root_ids=evidence_roots,
        negative_history_ids=negative_ids,
        allowed_tool_ids=tuple(sorted(set(allowed_tool_ids))),
        unresolved_obligations=question.unresolved_obligations,
        max_candidates=max_candidates,
        snapshot_hash=sha256(payload).hexdigest(),
    )


def bias_corrected_feedback_value(feedback: SearchFeedback, *, max_weight: float = 10.0) -> float:
    """Return an inverse-propensity routing signal, never an epistemic truth score."""

    if max_weight <= 0:
        raise ValueError("max_weight must be positive")
    if feedback.verified_downstream_success is None or not feedback.inspected:
        return 0.0
    outcome = 1.0 if feedback.verified_downstream_success else -1.0
    weight = min(max_weight, 1.0 / feedback.exposure_probability)
    return outcome * weight


__all__ = [
    "CandidateSpamAssessment",
    "EpistemicSpamFlag",
    "EvidenceStance",
    "ResearchInteractionSpace",
    "ScientificSearchQuestion",
    "SearchCandidate",
    "SearchFeedback",
    "SearchIndexKind",
    "SearchIntent",
    "SearchIntentKind",
    "SearchRankVector",
    "SearchVertical",
    "bias_corrected_feedback_value",
    "build_interaction_space",
    "compile_search_intents",
    "detect_epistemic_spam",
    "diversify_candidates",
    "dominates",
    "pareto_front",
]
