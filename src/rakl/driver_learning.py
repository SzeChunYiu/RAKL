from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Protocol, Tuple

from .breakthrough_learning import ExpertiseChunk
from .experience_substrate import EpisodeOutcome, TaskEpisode
from .problem_fibre import FibreKnowledgeItem, ProblemAtom, ProblemFibre
from .problem_solving_algebra import ProblemState, ResearchOperator
from .strategy_motifs import StrategyMotif
from .v3_runtime import FailureProjectionSpec, RAKLV3State, compile_state_fibre, record_task_episode


@dataclass(frozen=True)
class DriverTask:
    task_id: str
    atom: ProblemAtom
    problem_signature: Tuple[str, ...]
    timestamp: str

    def __post_init__(self) -> None:
        if not self.task_id or not self.problem_signature or not self.timestamp:
            raise ValueError("driver task requires task_id, problem_signature, and timestamp")


@dataclass(frozen=True)
class DriverRequest:
    task: DriverTask
    fibre: ProblemFibre


@dataclass(frozen=True)
class DriverResult:
    operator_ids: Tuple[str, ...]
    action_trace: Tuple[str, ...]
    observation_ids: Tuple[str, ...]
    verification_ids: Tuple[str, ...]
    outcome: EpisodeOutcome
    residual_signature: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str
    cost: float = 0.0

    def __post_init__(self) -> None:
        if not self.action_trace:
            raise ValueError("driver result requires an action trace")
        if not self.evidence_pointers or not self.artifact_hash:
            raise ValueError("driver result requires evidence pointers and artifact hash")
        if self.cost < 0:
            raise ValueError("driver result cost cannot be negative")
        if self.outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.PARTIAL_SUCCESS, EpisodeOutcome.BLOCKED} and not self.residual_signature:
            raise ValueError("non-success driver result requires a residual signature")


class LearningDriver(Protocol):
    def __call__(self, request: DriverRequest) -> DriverResult: ...


@dataclass(frozen=True)
class LearningTurnReport:
    state: RAKLV3State
    fibre: ProblemFibre
    episode: TaskEpisode
    driver_result: DriverResult


def run_learning_turn(
    state: RAKLV3State,
    task: DriverTask,
    driver: LearningDriver,
    *,
    episode_id: str,
    knowledge_items: Iterable[FibreKnowledgeItem] = (),
    strategy_motifs: Iterable[StrategyMotif] = (),
    operators: Iterable[ResearchOperator] = (),
    problem_state: ProblemState | None = None,
    expertise_chunks: Iterable[ExpertiseChunk] = (),
    candidate_method_families: Tuple[str, ...] = (),
    failure_spec_factory: Callable[[DriverResult], FailureProjectionSpec | None] | None = None,
    top_k_each: int = 12,
) -> LearningTurnReport:
    """Execute one LLM/agent turn against RAKL and persist its experience.

    The driver is replaceable and receives only a derived fibre.  Its output is
    frozen into a TaskEpisode before any consolidation.  Optional failure
    projection occurs only after the observed result exists.
    """

    if not episode_id:
        raise ValueError("episode_id is required")
    fibre = compile_state_fibre(
        state,
        task.atom,
        knowledge_items=knowledge_items,
        strategy_motifs=strategy_motifs,
        operators=operators,
        problem_state=problem_state,
        expertise_chunks=expertise_chunks,
        candidate_method_families=candidate_method_families,
        top_k_each=top_k_each,
    )
    result = driver(DriverRequest(task=task, fibre=fibre))
    episode = TaskEpisode(
        episode_id=episode_id,
        task_id=task.task_id,
        atom_id=task.atom.atom_id,
        context_hash=task.atom.context_hash,
        problem_signature=task.problem_signature,
        fibre_snapshot_hash=fibre.snapshot_hash,
        operator_ids=result.operator_ids,
        action_trace=result.action_trace,
        observation_ids=result.observation_ids,
        verification_ids=result.verification_ids,
        outcome=result.outcome,
        residual_signature=result.residual_signature,
        evidence_pointers=result.evidence_pointers,
        artifact_hash=result.artifact_hash,
        timestamp=task.timestamp,
        cost=result.cost,
    )
    failure_spec = failure_spec_factory(result) if failure_spec_factory is not None else None
    if failure_spec is not None and result.outcome is EpisodeOutcome.SUCCESS:
        raise ValueError("failure_spec_factory returned a failure projection for a successful result")
    next_state = record_task_episode(state, episode, failure_spec=failure_spec)
    return LearningTurnReport(next_state, fibre, episode, result)
