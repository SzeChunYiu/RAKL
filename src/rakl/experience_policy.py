from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Iterable, Tuple

from .experience_substrate import EpisodeOutcome, ExperienceLedger, TaskEpisode
from .problem_solving_algebra import (
    PathCandidate,
    ProblemState,
    ResearchOperator,
    operator_applicable,
    search_operator_paths,
)
from .saturation_vector import SaturationAxis, SaturationVectorReport
from .strategy_motifs import StrategyMotif


@dataclass(frozen=True)
class OperatorExperienceStatistic:
    operator_id: str
    matched_episode_ids: Tuple[str, ...]
    successes: int
    partial_successes: int
    failures: int
    blocked: int
    mean_cost: float
    empirical_success_rate: float


@dataclass(frozen=True)
class OperatorPolicyScore:
    operator: ResearchOperator
    statistic: OperatorExperienceStatistic
    score: float
    exploration_bonus: float
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class ExperienceConditionedPath:
    path: PathCandidate
    experience_adjustment: float
    adjusted_score: float
    operator_statistics: Tuple[OperatorExperienceStatistic, ...]


@dataclass(frozen=True)
class LearnedStrategyMotif:
    motif: StrategyMotif
    supporting_episode_ids: Tuple[str, ...]
    contradicting_episode_ids: Tuple[str, ...]
    observed_context_hashes: Tuple[str, ...]
    support_count: int
    contradiction_count: int


@dataclass(frozen=True)
class InventionReadinessReport:
    ready: bool
    target: str
    reasons: Tuple[str, ...]

    @property
    def grants_invention_authority(self) -> bool:
        return False


def _structural_match(episode: TaskEpisode, target_signature: Tuple[str, ...], context_hash: str) -> bool:
    if context_hash and episode.context_hash == context_hash:
        return True
    if not target_signature:
        return True
    target = set(target_signature)
    return bool(target & set(episode.problem_signature)) or bool(target & set(episode.residual_signature))


def operator_experience_statistic(
    operator_id: str,
    ledger: ExperienceLedger,
    *,
    target_signature: Tuple[str, ...] = (),
    context_hash: str = "",
) -> OperatorExperienceStatistic:
    matched = tuple(
        episode
        for episode in ledger.episodes
        if operator_id in episode.operator_ids and _structural_match(episode, target_signature, context_hash)
    )
    successes = sum(episode.outcome is EpisodeOutcome.SUCCESS for episode in matched)
    partials = sum(episode.outcome is EpisodeOutcome.PARTIAL_SUCCESS for episode in matched)
    failures = sum(episode.outcome is EpisodeOutcome.FAILURE for episode in matched)
    blocked = sum(episode.outcome is EpisodeOutcome.BLOCKED for episode in matched)
    mean_cost = sum(episode.cost for episode in matched) / len(matched) if matched else 0.0
    # Beta-style smoothing plus half credit for partial success prevents one early
    # episode from becoming an irreversible routing rule.
    success_rate = (successes + 0.5 * partials + 1.0) / (len(matched) + 2.0)
    return OperatorExperienceStatistic(
        operator_id=operator_id,
        matched_episode_ids=tuple(episode.episode_id for episode in matched),
        successes=successes,
        partial_successes=partials,
        failures=failures,
        blocked=blocked,
        mean_cost=mean_cost,
        empirical_success_rate=success_rate,
    )


def rank_operators_with_experience(
    state: ProblemState,
    operators: Iterable[ResearchOperator],
    ledger: ExperienceLedger,
    *,
    target_signature: Tuple[str, ...] = (),
    context_hash: str = "",
) -> Tuple[OperatorPolicyScore, ...]:
    """Rank applicable operators using history as a routing prior, not authority."""

    scored: list[OperatorPolicyScore] = []
    for operator in operators:
        if not operator_applicable(operator, state):
            continue
        stat = operator_experience_statistic(
            operator.operator_id,
            ledger,
            target_signature=target_signature,
            context_hash=context_hash,
        )
        matched = len(stat.matched_episode_ids)
        failure_rate = (stat.failures + stat.blocked + 1.0) / (matched + 2.0)
        exploration_bonus = 0.25 / sqrt(matched + 1.0)
        score = (
            operator.cost
            + 2.0 * operator.verification_debt
            + 2.0 * operator.boundary_risk
            - 3.0 * stat.empirical_success_rate
            + 2.0 * failure_rate
            - exploration_bonus
        )
        reasons = (
            f"matched_episodes:{matched}",
            f"smoothed_success_rate:{stat.empirical_success_rate:.6f}",
            f"smoothed_failure_rate:{failure_rate:.6f}",
            "experience_affects_search_priority_only",
        )
        scored.append(OperatorPolicyScore(operator, stat, score, exploration_bonus, reasons))
    scored.sort(key=lambda item: (item.score, item.operator.operator_id))
    return tuple(scored)


def rank_paths_with_experience(
    state: ProblemState,
    operators: Iterable[ResearchOperator],
    ledger: ExperienceLedger,
    *,
    target_signature: Tuple[str, ...] = (),
    context_hash: str = "",
    max_depth: int = 4,
    top_k: int = 8,
) -> Tuple[ExperienceConditionedPath, ...]:
    operator_tuple = tuple(operators)
    paths = search_operator_paths(state, operator_tuple, max_depth=max_depth, top_k=max(top_k * 3, top_k))
    stats = {
        operator.operator_id: operator_experience_statistic(
            operator.operator_id,
            ledger,
            target_signature=target_signature,
            context_hash=context_hash,
        )
        for operator in operator_tuple
    }
    ranked: list[ExperienceConditionedPath] = []
    for path in paths:
        path_stats = tuple(stats[operator_id] for operator_id in path.operators if operator_id in stats)
        adjustment = 0.0
        for stat in path_stats:
            matched = len(stat.matched_episode_ids)
            failure_rate = (stat.failures + stat.blocked + 1.0) / (matched + 2.0)
            adjustment += -1.5 * stat.empirical_success_rate + 1.0 * failure_rate
        ranked.append(
            ExperienceConditionedPath(
                path=path,
                experience_adjustment=adjustment,
                adjusted_score=path.score + adjustment,
                operator_statistics=path_stats,
            )
        )
    ranked.sort(key=lambda item: (item.adjusted_score, item.path.operators))
    return tuple(ranked[:top_k])


def _contains_contiguous(sequence: Tuple[str, ...], motif: Tuple[str, ...]) -> bool:
    if len(motif) > len(sequence):
        return False
    return any(sequence[index : index + len(motif)] == motif for index in range(len(sequence) - len(motif) + 1))


def induce_strategy_motifs(
    ledger: ExperienceLedger,
    *,
    min_support: int = 2,
    min_length: int = 2,
    max_length: int = 4,
) -> Tuple[LearnedStrategyMotif, ...]:
    """Mine repeated successful operator sequences while retaining near-miss history."""

    if min_support < 1 or min_length < 1 or max_length < min_length:
        raise ValueError("invalid motif induction parameters")
    successes = tuple(episode for episode in ledger.episodes if episode.outcome is EpisodeOutcome.SUCCESS)
    failures = tuple(episode for episode in ledger.episodes if episode.outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.BLOCKED})
    support: dict[Tuple[str, ...], list[TaskEpisode]] = {}
    for episode in successes:
        operators = episode.operator_ids
        for length in range(min_length, min(max_length, len(operators)) + 1):
            seen_in_episode: set[Tuple[str, ...]] = set()
            for index in range(len(operators) - length + 1):
                sequence = operators[index : index + length]
                if sequence in seen_in_episode:
                    continue
                support.setdefault(sequence, []).append(episode)
                seen_in_episode.add(sequence)

    learned: list[LearnedStrategyMotif] = []
    for sequence, episodes in support.items():
        if len(episodes) < min_support:
            continue
        contradicted = tuple(episode for episode in failures if _contains_contiguous(episode.operator_ids, sequence))
        digest = sha256("|".join(sequence).encode("utf-8")).hexdigest()[:12]
        failure_modes = tuple(
            dict.fromkeys(
                residual
                for episode in contradicted
                for residual in episode.residual_signature
            )
        )
        motif = StrategyMotif(
            motif_id=f"learned_{digest}",
            operator_ids=sequence,
            description="Experience-induced reusable operator sequence; promotion still requires scoped validation.",
            failure_modes=failure_modes,
        )
        learned.append(
            LearnedStrategyMotif(
                motif=motif,
                supporting_episode_ids=tuple(episode.episode_id for episode in episodes),
                contradicting_episode_ids=tuple(episode.episode_id for episode in contradicted),
                observed_context_hashes=tuple(sorted({episode.context_hash for episode in episodes})),
                support_count=len(episodes),
                contradiction_count=len(contradicted),
            )
        )
    learned.sort(
        key=lambda item: (
            -item.support_count,
            item.contradiction_count,
            -len(item.motif.operator_ids),
            item.motif.motif_id,
        )
    )
    return tuple(learned)


def assess_invention_readiness(
    saturation: SaturationVectorReport,
    *,
    stable_residual_count: int,
    ordinary_causes_excluded: bool,
    cross_domain_routes_exhausted: bool,
    representation_gap_supported: bool,
    method_basis_gap_supported: bool,
) -> InventionReadinessReport:
    if stable_residual_count < 0:
        raise ValueError("stable_residual_count cannot be negative")
    required = (SaturationAxis.KNOWLEDGE, SaturationAxis.OPERATOR, SaturationAxis.PATH)
    missing = tuple(axis.value for axis in required if not saturation.flat(axis))
    reasons: list[str] = []
    if missing:
        reasons.append("unsaturated_axes:" + ",".join(missing))
    if stable_residual_count < 2:
        reasons.append("residual_not_yet_stable_across_repeated_attempts")
    if not ordinary_causes_excluded:
        reasons.append("ordinary_failure_causes_not_excluded")
    if not cross_domain_routes_exhausted:
        reasons.append("cross_domain_transfer_search_not_bounded_flat")
    if reasons:
        return InventionReadinessReport(False, "NONE", tuple(reasons))
    if method_basis_gap_supported:
        return InventionReadinessReport(
            True,
            "OPERATOR",
            ("bounded relevant search is flat and evidence supports a missing method basis",),
        )
    if representation_gap_supported:
        return InventionReadinessReport(
            True,
            "REPRESENTATION",
            ("bounded relevant search is flat and evidence supports a missing representation",),
        )
    return InventionReadinessReport(
        False,
        "NONE",
        ("saturation is compatible with being stuck but no missing representation/operator has been identified",),
    )
