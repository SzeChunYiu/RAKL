from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Iterable, Tuple

from .breakthrough_learning import ExpertiseChunk
from .core import KnowledgeFiber
from .experience_learning import (
    ConsolidationVerdict,
    LessonConsolidationEvidence,
    LessonConsolidationReport,
    assess_lesson_consolidation,
    episode_to_failure_experience,
    lesson_to_research_tool,
    promoted_lesson_version,
)
from .experience_substrate import ExperienceLedger, Lesson, LessonKind, TaskEpisode, add_episode, add_lesson
from .evolution_archive import EvolutionArchive
from .failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperienceLattice,
    add_failure_experience,
)
from .problem_fibre import FibreKnowledgeItem, ProblemAtom, ProblemFibre, compile_problem_fibre
from .problem_solving_algebra import ProblemState, ResearchOperator
from .research_tool_inventory import ResearchToolInventory, add_research_tool
from .saturation_vector import NoveltyRound, SaturationVectorState, add_novelty_round
from .strategy_motifs import StrategyMotif
from .unified_substrate import UnifiedSubstrateSnapshot, materialize_unified_substrate


@dataclass(frozen=True)
class FailureProjectionSpec:
    failure_id: str
    candidate_id: str
    method_family: str
    failure_mode: str
    competing_diagnoses: Tuple[str, ...]
    selected_diagnosis: str = ""
    diagnosis_status: FailureDiagnosisStatus = FailureDiagnosisStatus.OBSERVED_ONLY
    broken_assumptions: Tuple[str, ...] = ()
    scope_conditions: Tuple[str, ...] = ()
    falsifier_or_attempt: str = "episode outcome"
    local_repair_attempts: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolProjectionSpec:
    tool_id: str
    name: str
    kind: str
    known_failure_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RAKLV3State:
    """Persistent external learning state used by a replaceable LLM driver."""

    experience: ExperienceLedger = ExperienceLedger()
    tools: ResearchToolInventory = ResearchToolInventory()
    failures: FailureExperienceLattice = FailureExperienceLattice()
    saturation: SaturationVectorState = SaturationVectorState()
    evolution: EvolutionArchive | None = None


@dataclass(frozen=True)
class ConsolidationOutcome:
    state: RAKLV3State
    report: LessonConsolidationReport
    promoted_lesson_id: str | None
    projected_tool_id: str | None


def state_fingerprint(state: RAKLV3State) -> str:
    """Return an opaque deterministic identity for a frozen v3 value state.

    The v3 state is composed of immutable dataclasses/tuples, so its repr is stable
    for equal in-process values.  This fingerprint is a benchmark/version identity,
    not a cryptographic attestation of external artifacts referenced by the state.
    """

    return sha256(repr(state).encode("utf-8")).hexdigest()


def record_task_episode(
    state: RAKLV3State,
    episode: TaskEpisode,
    *,
    failure_spec: FailureProjectionSpec | None = None,
) -> RAKLV3State:
    """Fast learning loop: persist the episode immediately, then record failure evidence.

    Failure projection defaults to OBSERVED_ONLY.  Root-cause support must be
    supplied explicitly; merely failing cannot mint a reusable obstruction.
    """

    experience = add_episode(state.experience, episode)
    failures = state.failures
    if failure_spec is not None:
        failure = episode_to_failure_experience(
            episode,
            failure_id=failure_spec.failure_id,
            candidate_id=failure_spec.candidate_id,
            method_family=failure_spec.method_family,
            failure_mode=failure_spec.failure_mode,
            competing_diagnoses=failure_spec.competing_diagnoses,
            selected_diagnosis=failure_spec.selected_diagnosis,
            diagnosis_status=failure_spec.diagnosis_status,
            broken_assumptions=failure_spec.broken_assumptions,
            scope_conditions=failure_spec.scope_conditions,
            falsifier_or_attempt=failure_spec.falsifier_or_attempt,
            local_repair_attempts=failure_spec.local_repair_attempts,
        )
        failures = add_failure_experience(failures, failure)
    return replace(state, experience=experience, failures=failures)


def consolidate_lesson(
    state: RAKLV3State,
    candidate: Lesson,
    evidence: LessonConsolidationEvidence,
    *,
    promoted_lesson_id: str,
    promoted_artifact_hash: str,
    tool_spec: ToolProjectionSpec | None = None,
) -> ConsolidationOutcome:
    """Slow learning loop: validate an abstraction, version it, and optionally expose it as a tool."""

    experience = state.experience
    recorded_by_id = {lesson.lesson_id: lesson for lesson in experience.lessons}
    recorded = recorded_by_id.get(candidate.lesson_id)
    if recorded is None:
        experience = add_lesson(experience, candidate)
    elif recorded != candidate:
        raise ValueError("candidate lesson identity already exists with different content")

    report = assess_lesson_consolidation(experience, candidate, evidence)
    if report.verdict in {ConsolidationVerdict.CANNOT_CHECK, ConsolidationVerdict.CANDIDATE_ONLY, ConsolidationVerdict.CONTRADICTED}:
        return ConsolidationOutcome(replace(state, experience=experience), report, None, None)

    promoted = promoted_lesson_version(
        candidate,
        new_lesson_id=promoted_lesson_id,
        artifact_hash=promoted_artifact_hash,
        report=report,
        evidence=evidence,
    )
    experience = add_lesson(experience, promoted)
    tools = state.tools
    projected_tool_id: str | None = None
    if tool_spec is not None:
        if promoted.kind not in {LessonKind.OPERATOR, LessonKind.STRATEGY, LessonKind.REPRESENTATION}:
            raise ValueError("tool projection requested for non-operational lesson")
        tool = lesson_to_research_tool(
            promoted,
            experience,
            tool_id=tool_spec.tool_id,
            name=tool_spec.name,
            kind=tool_spec.kind,
            known_failure_ids=tool_spec.known_failure_ids,
        )
        tools = add_research_tool(tools, tool)
        projected_tool_id = tool.tool_id
    return ConsolidationOutcome(
        replace(state, experience=experience, tools=tools),
        report,
        promoted.lesson_id,
        projected_tool_id,
    )


def compile_state_fibre(
    state: RAKLV3State,
    atom: ProblemAtom,
    *,
    knowledge_items: Iterable[FibreKnowledgeItem] = (),
    legacy_knowledge_fibers: Iterable[KnowledgeFiber] = (),
    strategy_motifs: Iterable[StrategyMotif] = (),
    operators: Iterable[ResearchOperator] = (),
    problem_state: ProblemState | None = None,
    expertise_chunks: Iterable[ExpertiseChunk] = (),
    candidate_method_families: Tuple[str, ...] = (),
    top_k_each: int = 12,
) -> ProblemFibre:
    return compile_problem_fibre(
        atom,
        knowledge_items=knowledge_items,
        legacy_knowledge_fibers=legacy_knowledge_fibers,
        tool_inventory=state.tools,
        failure_lattice=state.failures,
        experience_ledger=state.experience,
        strategy_motifs=strategy_motifs,
        operators=operators,
        problem_state=problem_state,
        expertise_chunks=expertise_chunks,
        candidate_method_families=candidate_method_families,
        top_k_each=top_k_each,
    )


def materialize_state_substrate(
    state: RAKLV3State,
    *,
    legacy_knowledge_fibers: Iterable[KnowledgeFiber] = (),
) -> UnifiedSubstrateSnapshot:
    """Create the common read-only substrate overlay for the current v3 state."""

    return materialize_unified_substrate(
        experience=state.experience,
        tools=state.tools,
        failures=state.failures,
        legacy_knowledge_fibers=legacy_knowledge_fibers,
    )


def record_saturation_round(state: RAKLV3State, round_: NoveltyRound) -> RAKLV3State:
    return replace(state, saturation=add_novelty_round(state.saturation, round_))
