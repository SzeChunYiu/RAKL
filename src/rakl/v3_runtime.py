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
from .experience_substrate import (
    EpisodeAdmissionReceipt as SubstrateAdmissionReceipt,
    ExperienceLedger,
    Lesson,
    LessonKind,
    TaskEpisode,
    add_admission_receipt,
    add_episode,
    add_lesson,
)
from .episode_admission import (
    EpisodeAdmissionReceipt as ProposalEpisodeAdmissionReceipt,
    ProtectedConsumer,
    filter_canonical_inventory_episodes,
    require_protected_consumer_admission,
    retain_proposal_shadow_episode,
)
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
from .v3_authority import ProtectedAuthorityContext
from .v3_scientific_authority import (
    ScientificAuthorityProjection,
    ScientificEvidenceBinding,
    ScientificTransitionOutcome,
    promote_scientific_authority,
    register_scientific_claim,
    register_scientific_evidence,
    revoke_scientific_authority,
    supersede_scientific_authority,
)

__all__ = [
    "ConsolidationOutcome",
    "FailureProjectionSpec",
    "RAKLV3State",
    "ScientificAuthorityProjection",
    "ScientificEvidenceBinding",
    "ScientificTransitionOutcome",
    "ToolProjectionSpec",
    "compile_state_fibre",
    "consolidate_lesson",
    "materialize_state_substrate",
    "promote_scientific_authority",
    "protected_canonical_inventory",
    "record_saturation_round",
    "record_task_episode",
    "register_scientific_claim",
    "register_scientific_evidence",
    "require_protected_inventory_admission",
    "revoke_scientific_authority",
    "state_fingerprint",
    "state_fingerprint_v2",
    "state_fingerprint_v3",
    "supersede_scientific_authority",
]


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
    projection_attestation_id: str | None = None
    projection_authority_context: ProtectedAuthorityContext | None = None
    projection_artifact_id: str | None = None


@dataclass(frozen=True)
class RAKLV3State:
    """Persistent external learning state used by a replaceable LLM driver.

    ``scientific_authority`` is appended last so positional construction by
    existing v3 consumers keeps working, and it defaults to an empty projection
    so experience-only callers are unaffected (refs #242).
    """

    experience: ExperienceLedger = ExperienceLedger()
    tools: ResearchToolInventory = ResearchToolInventory()
    failures: FailureExperienceLattice = FailureExperienceLattice()
    saturation: SaturationVectorState = SaturationVectorState()
    evolution: EvolutionArchive | None = None
    scientific_authority: ScientificAuthorityProjection = ScientificAuthorityProjection()


@dataclass(frozen=True)
class ConsolidationOutcome:
    state: RAKLV3State
    report: LessonConsolidationReport
    promoted_lesson_id: str | None
    projected_tool_id: str | None


#: Coordinates covered by the v1 fingerprint contract, in their original order.
#: Frozen: appending a coordinate here would silently change historical benchmark
#: identity, which issue #242 §7 forbids. New coordinates go into v2.
_V1_FINGERPRINT_FIELDS: Tuple[str, ...] = (
    "experience",
    "tools",
    "failures",
    "saturation",
    "evolution",
)


def state_fingerprint(state: RAKLV3State) -> str:
    """Return the **v1** deterministic identity for a frozen v3 value state.

    The v1 contract covers the experience-side coordinates only, reproducing the
    exact bytes hashed before the scientific-authority coordinate was composed in
    (refs #242).  Historical benchmark identities therefore remain valid: a state
    carrying no scientific authority fingerprints exactly as it did on the
    pre-integration revision.

    This is a benchmark/version identity, not a cryptographic attestation of
    external artifacts referenced by the state.  Use
    :func:`state_fingerprint_v2` when scientific authority must be part of the
    identity.
    """

    body = ", ".join(f"{name}={getattr(state, name)!r}" for name in _V1_FINGERPRINT_FIELDS)
    return sha256(f"RAKLV3State({body})".encode("utf-8")).hexdigest()


def state_fingerprint_v2(state: RAKLV3State) -> str:
    """Return the **v2** identity, covering scientific authority as well.

    Two states that differ only in their scientific-authority projection share a
    v1 fingerprint and differ under v2.  Benchmarks that must be sensitive to
    authority movement have to pin v2 explicitly rather than inherit it.
    """

    return sha256(("v2:" + repr(state)).encode("utf-8")).hexdigest()



def state_fingerprint_v3(state: RAKLV3State, *, sequence: int = 0, previous_digest: str | None = None) -> str:
    """Return the **v3** canonical commitment digest (dual-write surface).

    This is the context-independent canonical encoding of the full state from
    :mod:, introduced for migration fingerprinting.  It is
    additive: v1 (experience-side benchmark identity) and v2 (repr-based
    authority-aware identity) remain unchanged, so historical benchmark
    identities still hold.  New cross-runtime replay and migration paths should
    dual-write this v3 digest alongside v1/v2 rather than re-keying either.

    The commitment grants no scientific authority; it is an integrity digest.
    """
    from .v3_commitment import state_commitment_v3

    return state_commitment_v3(state, sequence=sequence, previous_digest=previous_digest).digest


def record_task_episode(
    state: RAKLV3State,
    episode: TaskEpisode,
    *,
    failure_spec: FailureProjectionSpec | None = None,
    admission_receipt: SubstrateAdmissionReceipt | None = None,
    proposal_admission_receipt: ProposalEpisodeAdmissionReceipt | None = None,
    protected_consumer: ProtectedConsumer | None = None,
    claimed_path_or_name_hint: str | None = None,
) -> RAKLV3State:
    """Fast learning loop: persist the episode immediately, then record failure evidence.

    Failure projection defaults to OBSERVED_ONLY.  Root-cause support must be
    supplied explicitly; merely failing cannot mint a reusable obstruction.

    Admission wiring (issue #395):

    * ``admission_receipt`` — ledger-native substrate receipt stored on the
      experience ledger for exhaustive inventory membership.
    * ``proposal_admission_receipt`` — proposal-only
      :mod:`rakl.episode_admission` receipt. When ``protected_consumer`` is set,
      the pair is fail-closed audited before persistence; shadow-only receipts
      are retained for search/failure learning and never counted as canonical
      merely because a path/extension hint was supplied.
    """

    if protected_consumer is not None:
        require_protected_consumer_admission(
            episode,
            proposal_admission_receipt,
            protected_consumer=protected_consumer,
            claimed_path_or_name_hint=claimed_path_or_name_hint,
        )
    elif proposal_admission_receipt is not None:
        retain_proposal_shadow_episode(
            episode,
            proposal_admission_receipt,
            claimed_path_or_name_hint=claimed_path_or_name_hint,
        )

    experience = add_episode(state.experience, episode)
    if admission_receipt is not None:
        experience = add_admission_receipt(experience, admission_receipt)
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


def require_protected_inventory_admission(
    episode: TaskEpisode,
    receipt: ProposalEpisodeAdmissionReceipt | None,
    *,
    protected_consumer: ProtectedConsumer = ProtectedConsumer.CANONICAL_INVENTORY,
    claimed_path_or_name_hint: str | None = None,
):
    """Runtime alias: fail closed unless episode_admission admits the episode."""

    return require_protected_consumer_admission(
        episode,
        receipt,
        protected_consumer=protected_consumer,
        claimed_path_or_name_hint=claimed_path_or_name_hint,
    )


def protected_canonical_inventory(
    pairs: Iterable[tuple[TaskEpisode, ProposalEpisodeAdmissionReceipt | None]],
    *,
    claimed_path_or_name_hint: str | None = None,
) -> Tuple[TaskEpisode, ...]:
    """Runtime inventory consumer bound to episode_admission receipts."""

    return filter_canonical_inventory_episodes(
        pairs,
        claimed_path_or_name_hint=claimed_path_or_name_hint,
    )


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
    experience = add_lesson(experience, promoted, authority_context=evidence.authority_context)
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
            authority_context=tool_spec.projection_authority_context or evidence.authority_context,
            projection_attestation_id=tool_spec.projection_attestation_id,
            projection_artifact_id=tool_spec.projection_artifact_id,
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
        evolution=state.evolution,
    )


def record_saturation_round(state: RAKLV3State, round_: NoveltyRound) -> RAKLV3State:
    return replace(state, saturation=add_novelty_round(state.saturation, round_))
