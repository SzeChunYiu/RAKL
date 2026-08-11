from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Callable, Iterable, Protocol, Tuple

from .breakthrough_learning import ExpertiseChunk
from .core import KnowledgeFiber
from .experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes
from .pre_action_receipt import (
    OperatorExecutionGateReport,
    PreActionBindingReport,
    PreActionFibreReceipt,
    audit_pre_action_binding,
    gate_consequential_operator_execution,
)
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
    chronology_binding: PreActionBindingReport
    execution_gate: OperatorExecutionGateReport | None = None


def _resolve_intended_operator_id(
    receipt: PreActionFibreReceipt | None,
    intended_operator_id: str | None,
) -> str:
    if intended_operator_id is not None and intended_operator_id.strip():
        return intended_operator_id
    if receipt is not None and len(receipt.operator_ids) == 1:
        return receipt.operator_ids[0]
    return ""


def _resolve_intended_falsifier(
    receipt: PreActionFibreReceipt | None,
    intended_falsifier: str | None,
) -> str:
    if intended_falsifier is not None and intended_falsifier.strip():
        return intended_falsifier
    if receipt is not None:
        return receipt.predeclared_discriminator
    return ""


def run_learning_turn(
    state: RAKLV3State,
    task: DriverTask,
    driver: LearningDriver,
    *,
    episode_id: str,
    knowledge_items: Iterable[FibreKnowledgeItem] = (),
    legacy_knowledge_fibers: Iterable[KnowledgeFiber] = (),
    strategy_motifs: Iterable[StrategyMotif] = (),
    operators: Iterable[ResearchOperator] = (),
    problem_state: ProblemState | None = None,
    expertise_chunks: Iterable[ExpertiseChunk] = (),
    candidate_method_families: Tuple[str, ...] = (),
    failure_spec_factory: Callable[[DriverResult], FailureProjectionSpec | None] | None = None,
    top_k_each: int = 12,
    pre_action_receipt: PreActionFibreReceipt | None = None,
    require_pre_action_receipt: bool = False,
    intended_operator_id: str | None = None,
    intended_falsifier: str | None = None,
) -> LearningTurnReport:
    """Execute one LLM/agent turn against RAKL and persist its experience.

    The driver is replaceable and receives only a derived fibre.  Its output is
    frozen into a TaskEpisode before any consolidation.  Optional failure
    projection occurs only after the observed result exists.  Existing RAKL
    `KnowledgeFiber` objects can be supplied directly and are adapted read-only.

    Pre-action fibre / consequential-operator gate (issue #123)
    ----------------------------------------------------------
    ``compile_state_fibre`` → action execution → ``record_task_episode`` is the
    consequential learning path named by the issue. When
    ``require_pre_action_receipt`` is set, or a ``pre_action_receipt`` is
    supplied, the fail-closed pre-execution gate runs *before* the driver is
    invoked. Cheap/proposal turns that neither require nor supply a receipt
    leave the gate inactive (same shape as the #124 preservation gate).

    Chronology status is always derived after the episode is frozen via
    :func:`audit_pre_action_binding`. A missing receipt yields
    ``RETROSPECTIVE_ONLY`` automatically; prospective credit is never declared.
    ``record_task_episode`` itself stays ungated so symbolic/cheap recording is
    not ceremonially taxed.
    """

    if not episode_id:
        raise ValueError("episode_id is required")
    fibre = compile_state_fibre(
        state,
        task.atom,
        knowledge_items=knowledge_items,
        legacy_knowledge_fibers=legacy_knowledge_fibers,
        strategy_motifs=strategy_motifs,
        operators=operators,
        problem_state=problem_state,
        expertise_chunks=expertise_chunks,
        candidate_method_families=candidate_method_families,
        top_k_each=top_k_each,
    )

    execution_gate: OperatorExecutionGateReport | None = None
    gate_active = require_pre_action_receipt or pre_action_receipt is not None
    if gate_active:
        resolved_operator = _resolve_intended_operator_id(pre_action_receipt, intended_operator_id)
        resolved_falsifier = _resolve_intended_falsifier(pre_action_receipt, intended_falsifier)
        execution_gate = gate_consequential_operator_execution(
            pre_action_receipt,
            intended_operator_id=resolved_operator,
            intended_fibre_snapshot_hash=fibre.snapshot_hash,
            intended_falsifier=resolved_falsifier,
            intended_atom_id=task.atom.atom_id,
            intended_context_hash=task.atom.context_hash,
            intended_task_id=task.task_id,
        )
        if not execution_gate.may_execute:
            joined = (
                ",".join(execution_gate.reasons)
                if execution_gate.reasons
                else execution_gate.verdict.value
            )
            raise ValueError(
                "consequential learning turn blocked by pre-action fibre receipt gate "
                f"({execution_gate.verdict.value}): {joined}"
            )

    result = driver(DriverRequest(task=task, fibre=fibre))
    evidence_pointers = result.evidence_pointers
    if pre_action_receipt is not None:
        pointer = pre_action_receipt.episode_pointer
        if pointer not in evidence_pointers:
            evidence_pointers = evidence_pointers + (pointer,)
    episode_draft = TaskEpisode(
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
        evidence_pointers=evidence_pointers,
        artifact_hash="",
        timestamp=task.timestamp,
        cost=result.cost,
    )
    # Driver-provided strings are observations only.  Episode identity is always
    # recomputed from the exact frozen episode bytes.
    episode = replace(
        episode_draft,
        artifact_hash=sha256(episode_content_bytes(episode_draft)).hexdigest(),
    )
    failure_spec = failure_spec_factory(result) if failure_spec_factory is not None else None
    if failure_spec is not None and result.outcome is EpisodeOutcome.SUCCESS:
        raise ValueError("failure_spec_factory returned a failure projection for a successful result")
    next_state = record_task_episode(state, episode, failure_spec=failure_spec)
    chronology_binding = audit_pre_action_binding(pre_action_receipt, episode)
    return LearningTurnReport(
        next_state,
        fibre,
        episode,
        result,
        chronology_binding=chronology_binding,
        execution_gate=execution_gate,
    )
