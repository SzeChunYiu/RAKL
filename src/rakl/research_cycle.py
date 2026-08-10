from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Tuple


class ResearchStage(str, Enum):
    REGISTER_TASK = "REGISTER_TASK"
    INGEST_EVIDENCE = "INGEST_EVIDENCE"
    DECOMPOSE_SOURCE = "DECOMPOSE_SOURCE"
    PROJECT_CONTEXT = "PROJECT_CONTEXT"
    NORMALIZE_OBJECT = "NORMALIZE_OBJECT"
    RESOLVE_IDENTITY = "RESOLVE_IDENTITY"
    BIND_PROVENANCE = "BIND_PROVENANCE"
    UPDATE_ATLAS = "UPDATE_ATLAS"
    MAP_RELATIONS = "MAP_RELATIONS"
    COMPILE_WORKING_CONTEXT = "COMPILE_WORKING_CONTEXT"
    GENERATE_PROPOSAL = "GENERATE_PROPOSAL"
    VERIFY_PROPOSAL = "VERIFY_PROPOSAL"
    CANONICAL_UPDATE = "CANONICAL_UPDATE"
    DIAGNOSE_RESIDUAL = "DIAGNOSE_RESIDUAL"
    SELECT_NEXT_ACTION = "SELECT_NEXT_ACTION"
    CHECK_SATURATION = "CHECK_SATURATION"
    CONSOLIDATE_METHOD_EXPERIENCE = "CONSOLIDATE_METHOD_EXPERIENCE"


class StorageTier(str, Enum):
    TIER0_CANONICAL_ARCHIVE = "TIER0_CANONICAL_ARCHIVE"
    TIER1_REBUILDABLE_VIEW = "TIER1_REBUILDABLE_VIEW"
    TIER2_WORKING_SET = "TIER2_WORKING_SET"
    TIER3_LLM_PROMPT = "TIER3_LLM_PROMPT"
    METHOD_MEMORY = "METHOD_MEMORY"


class StageAuthority(str, Enum):
    NONE = "NONE"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    REPRESENTATION_ONLY = "REPRESENTATION_ONLY"
    EXTERNAL_VERIFICATION_REQUIRED = "EXTERNAL_VERIFICATION_REQUIRED"
    CANONICAL_UPDATE_GATED = "CANONICAL_UPDATE_GATED"


class TraceVerdict(str, Enum):
    VALID_SCOPED_TRACE = "VALID_SCOPED_TRACE"
    INVALID_TRACE = "INVALID_TRACE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class StageContract:
    stage: ResearchStage
    purpose: str
    typed_inputs: Tuple[str, ...]
    typed_outputs: Tuple[str, ...]
    state_read_set: Tuple[str, ...]
    state_write_set: Tuple[str, ...]
    storage_tier: StorageTier
    llm_may_propose: bool
    external_verification_required: bool
    authority_effect: StageAuthority
    failure_semantics: Tuple[str, ...]
    implementation_owners: Tuple[str, ...]

    def problems(self) -> Tuple[str, ...]:
        problems: list[str] = []
        required = {
            "purpose": (self.purpose,),
            "typed_inputs": self.typed_inputs,
            "typed_outputs": self.typed_outputs,
            "state_read_set": self.state_read_set,
            "state_write_set": self.state_write_set,
            "failure_semantics": self.failure_semantics,
            "implementation_owners": self.implementation_owners,
        }
        for label, values in required.items():
            if not values or any(not str(value).strip() for value in values):
                problems.append(f"{label}_missing")
        if self.llm_may_propose and self.authority_effect not in {
            StageAuthority.NONE,
            StageAuthority.PROPOSAL_ONLY,
            StageAuthority.REPRESENTATION_ONLY,
            StageAuthority.EXTERNAL_VERIFICATION_REQUIRED,
        }:
            problems.append("llm_stage_cannot_directly_mint_canonical_authority")
        if self.stage is ResearchStage.CANONICAL_UPDATE and self.authority_effect is not StageAuthority.CANONICAL_UPDATE_GATED:
            problems.append("canonical_update_must_be_gated")
        return tuple(problems)


@dataclass(frozen=True)
class ResearchArtifactRef:
    artifact_id: str
    kind: str
    storage_tier: StorageTier
    source_ids: Tuple[str, ...] = ()
    canonical: bool = False
    lossy: bool = False
    erasure_tags: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.kind:
            raise ValueError("artifact_id and kind are required")
        if self.lossy and self.canonical:
            raise ValueError("lossy derived artifacts cannot be canonical truth")
        if self.lossy and not self.source_ids:
            raise ValueError("lossy artifacts require source_ids for rehydration")
        if self.lossy and not self.erasure_tags:
            raise ValueError("lossy artifacts require erasure_tags")


@dataclass(frozen=True)
class ResearchStep:
    step_id: str
    cycle_index: int
    stage: ResearchStage
    input_ids: Tuple[str, ...]
    output_ids: Tuple[str, ...]
    llm_used: bool
    external_verification_observed: bool | None
    mandatory_context_complete: bool | None = None
    raw_evidence_rehydrated: bool | None = None
    strong_authority_operation: bool = False
    token_cost: int = 0

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("step_id is required")
        if self.cycle_index < 0:
            raise ValueError("cycle_index cannot be negative")
        if self.token_cost < 0:
            raise ValueError("token_cost cannot be negative")


@dataclass(frozen=True)
class ResearchTraceReport:
    verdict: TraceVerdict
    reasons: Tuple[str, ...]
    stage_counts: Tuple[Tuple[str, int], ...]
    total_llm_tokens: int
    canonical_artifact_ids: Tuple[str, ...]
    lossy_artifact_ids: Tuple[str, ...]

    @property
    def grants_scientific_truth(self) -> bool:
        return False

    @property
    def grants_independent_review_credit(self) -> bool:
        return False


_STAGE_ORDER = {stage: index for index, stage in enumerate(ResearchStage)}


def stage_contracts() -> Tuple[StageContract, ...]:
    """Canonical atomic lifecycle for one scoped RAKL research operation.

    The contracts describe who may propose information, where each artifact lives,
    and which stages can alter canonical state. They are intentionally more
    explicit than a conventional agent prompt so that coding agents and later
    runtimes can validate traces independently of model prose.
    """

    C = StageContract
    S = ResearchStage
    T = StorageTier
    A = StageAuthority
    return (
        C(S.REGISTER_TASK, "freeze object, QoI, context, evidence cutoff, budgets and blockers", ("research_request",), ("registered_task",), ("user_request",), ("task_registry",), T.TIER0_CANONICAL_ARCHIVE, False, False, A.NONE, ("BLOCKED", "CANNOT_CHECK"), ("project_runtime.py", "formalism.py")),
        C(S.INGEST_EVIDENCE, "store source payloads immutably and bind source identity", ("registered_task", "source_payload"), ("source_snapshot",), ("task_registry",), ("raw_evidence_archive",), T.TIER0_CANONICAL_ARCHIVE, False, False, A.NONE, ("SOURCE_INVALID", "CANNOT_CHECK"), ("project_runtime.py", "claim_evidence.py")),
        C(S.DECOMPOSE_SOURCE, "split source contribution into atomic claim/evidence candidates", ("source_snapshot",), ("claim_candidates",), ("raw_evidence_archive",), ("proposal_workspace",), T.TIER1_REBUILDABLE_VIEW, True, True, A.PROPOSAL_ONLY, ("CANNOT_CHECK",), ("core.py", "claim_evidence.py")),
        C(S.PROJECT_CONTEXT, "bind each candidate to population, regime, scale, units, observation model and QoI", ("claim_candidates", "registered_task"), ("contextual_projections",), ("proposal_workspace", "task_registry"), ("proposal_workspace",), T.TIER1_REBUILDABLE_VIEW, True, True, A.REPRESENTATION_ONLY, ("CONTEXT_MISSING", "CANNOT_CHECK"), ("core.py", "atlas_gluing.py")),
        C(S.NORMALIZE_OBJECT, "normalize terminology, units and mathematical representation without changing authority", ("contextual_projections",), ("normalized_objects",), ("proposal_workspace",), ("rebuildable_indexes",), T.TIER1_REBUILDABLE_VIEW, True, True, A.REPRESENTATION_ONLY, ("NORMALIZATION_AMBIGUOUS", "CANNOT_CHECK"), ("core.py", "measurement.py", "metrology.py")),
        C(S.RESOLVE_IDENTITY, "collapse exact identities while preserving aliases, versions and ancestry", ("normalized_objects",), ("identity_resolution",), ("rebuildable_indexes", "evidence_lineage"), ("identity_ledger",), T.TIER0_CANONICAL_ARCHIVE, False, False, A.NONE, ("IDENTITY_AMBIGUOUS", "CANNOT_CHECK"), ("identity.py", "identity_saturation.py")),
        C(S.BIND_PROVENANCE, "attach exact source spans, lineage and derivation ancestry", ("identity_resolution", "source_snapshot"), ("provenance_bound_objects",), ("identity_ledger", "raw_evidence_archive"), ("provenance_ledger",), T.TIER0_CANONICAL_ARCHIVE, False, True, A.EXTERNAL_VERIFICATION_REQUIRED, ("PROVENANCE_INCOMPLETE", "CANNOT_CHECK"), ("claim_evidence.py", "evidence_lineage.py")),
        C(S.UPDATE_ATLAS, "insert evidence-bearing contextual objects without forcing global consistency", ("provenance_bound_objects",), ("atlas_delta",), ("provenance_ledger", "knowledge_atlas"), ("knowledge_atlas",), T.TIER0_CANONICAL_ARCHIVE, False, True, A.CANONICAL_UPDATE_GATED, ("BLOCKED", "CANNOT_CHECK"), ("typed_lattice.py", "atlas_gluing.py")),
        C(S.MAP_RELATIONS, "test typed equivalence, compatibility, contradiction, derivation and transition witnesses", ("atlas_delta",), ("relation_witnesses", "obstructions"), ("knowledge_atlas", "identity_ledger"), ("knowledge_atlas", "obstruction_ledger"), T.TIER0_CANONICAL_ARCHIVE, True, True, A.EXTERNAL_VERIFICATION_REQUIRED, ("RELATION_UNKNOWN", "OBSTRUCTED", "CANNOT_CHECK"), ("similarity.py", "atlas_gluing.py", "bridge_composition.py")),
        C(S.COMPILE_WORKING_CONTEXT, "materialize the smallest epistemically sufficient target-conditioned working set", ("registered_task", "knowledge_atlas"), ("working_set", "prompt_packet"), ("knowledge_atlas", "negative_history", "obstruction_ledger"), ("execution_workspace",), T.TIER2_WORKING_SET, False, False, A.NONE, ("CANNOT_COMPILE",), ("context_compiler.py", "multires_memory.py")),
        C(S.GENERATE_PROPOSAL, "ask the replaceable LLM or symbolic proposer for a claim, model, experiment or method candidate", ("prompt_packet",), ("proposal",), ("execution_workspace",), ("proposal_workspace",), T.TIER3_LLM_PROMPT, True, True, A.PROPOSAL_ONLY, ("NO_VALID_PROPOSAL", "CANNOT_CHECK"), ("execution.py", "formalism.py", "invention.py")),
        C(S.VERIFY_PROPOSAL, "test proposal against evidence, assumptions, falsifiers and protected benchmarks", ("proposal", "knowledge_atlas"), ("verification_report",), ("proposal_workspace", "knowledge_atlas"), ("verification_ledger",), T.TIER0_CANONICAL_ARCHIVE, False, True, A.EXTERNAL_VERIFICATION_REQUIRED, ("REFUTED", "PARTIALLY_IDENTIFIED", "BLOCKED", "CANNOT_CHECK"), ("formalism.py", "model_criticism.py", "assumption_sensitivity.py")),
        C(S.CANONICAL_UPDATE, "apply only licensed verification outcomes to canonical epistemic state", ("verification_report",), ("canonical_state_delta",), ("verification_ledger", "knowledge_atlas"), ("knowledge_atlas", "negative_history"), T.TIER0_CANONICAL_ARCHIVE, False, True, A.CANONICAL_UPDATE_GATED, ("NO_UPDATE", "BLOCKED", "CANNOT_CHECK"), ("promotion.py", "core.py")),
        C(S.DIAGNOSE_RESIDUAL, "convert unexplained discrepancy, obstruction or failure into a typed residual", ("canonical_state_delta", "verification_report"), ("residual",), ("knowledge_atlas", "negative_history"), ("residual_ledger",), T.TIER0_CANONICAL_ARCHIVE, True, True, A.PROPOSAL_ONLY, ("RESIDUAL_UNREPRESENTABLE", "CANNOT_CHECK"), ("model_criticism.py", "metacognition.py", "missing_operator.py")),
        C(S.SELECT_NEXT_ACTION, "choose search, experiment, assimilation, invention, help or stop action under cost and validity constraints", ("residual", "registered_task"), ("next_action",), ("residual_ledger", "research_portfolio"), ("research_portfolio",), T.METHOD_MEMORY, True, True, A.PROPOSAL_ONLY, ("BLOCKED", "CANNOT_CHECK"), ("search_controller.py", "challenge_learning.py", "invention.py")),
        C(S.CHECK_SATURATION, "measure semantic and evidence-lineage novelty and decide whether the scoped route is flat", ("knowledge_atlas", "residual", "next_action"), ("saturation_report",), ("knowledge_atlas", "evidence_lineage", "negative_history"), ("saturation_state",), T.TIER0_CANONICAL_ARCHIVE, False, True, A.EXTERNAL_VERIFICATION_REQUIRED, ("ACTIVE_NON_FLAT", "BLOCKED", "CANNOT_CHECK"), ("saturation.py", "identity_saturation.py")),
        C(S.CONSOLIDATE_METHOD_EXPERIENCE, "convert validated trajectories into candidate reusable method knowledge without self-authorizing the skill", ("research_trace", "saturation_report"), ("method_experience_candidate",), ("research_trace", "method_memory"), ("method_memory",), T.METHOD_MEMORY, True, True, A.PROPOSAL_ONLY, ("NO_TRANSFER_EVIDENCE", "META_OVERFIT", "CANNOT_CHECK"), ("evolution.py", "assimilation.py", "self_bootstrap.py")),
    )


def validate_stage_contracts(contracts: Iterable[StageContract] | None = None) -> Tuple[str, ...]:
    contracts = tuple(stage_contracts() if contracts is None else contracts)
    by_stage: dict[ResearchStage, list[StageContract]] = {}
    for contract in contracts:
        by_stage.setdefault(contract.stage, []).append(contract)
    problems: list[str] = []
    for stage in ResearchStage:
        group = by_stage.get(stage, [])
        if len(group) != 1:
            problems.append(f"stage_contract_count:{stage.value}:{len(group)}")
        for contract in group:
            problems.extend(f"{stage.value}:{problem}" for problem in contract.problems())
    for stage in by_stage:
        if stage not in ResearchStage:
            problems.append(f"unknown_stage:{stage}")
    return tuple(problems)


def validate_research_trace(
    artifacts: Iterable[ResearchArtifactRef],
    steps: Iterable[ResearchStep],
    *,
    require_full_cycle: bool = True,
) -> ResearchTraceReport:
    artifact_tuple = tuple(artifacts)
    step_tuple = tuple(steps)
    artifact_by_id: Mapping[str, ResearchArtifactRef] = {a.artifact_id: a for a in artifact_tuple}
    if len(artifact_by_id) != len(artifact_tuple):
        return ResearchTraceReport(TraceVerdict.INVALID_TRACE, ("duplicate_artifact_id",), (), 0, (), ())
    if len({s.step_id for s in step_tuple}) != len(step_tuple):
        return ResearchTraceReport(TraceVerdict.INVALID_TRACE, ("duplicate_step_id",), (), 0, (), ())

    contract_problems = validate_stage_contracts()
    if contract_problems:
        return ResearchTraceReport(TraceVerdict.INVALID_TRACE, contract_problems, (), 0, (), ())
    contracts = {contract.stage: contract for contract in stage_contracts()}

    reasons: list[str] = []
    unknown: list[str] = []
    counts: dict[str, int] = {stage.value: 0 for stage in ResearchStage}
    produced_at: dict[str, int] = {}
    verification_seen_by_cycle: dict[int, int] = {}

    last_cycle = -1
    last_rank = -1
    for index, step in enumerate(step_tuple):
        counts[step.stage.value] += 1
        contract = contracts[step.stage]
        if step.cycle_index < last_cycle:
            reasons.append(f"cycle_index_regressed:{step.step_id}")
        if step.cycle_index != last_cycle:
            last_cycle = step.cycle_index
            last_rank = -1
        rank = _STAGE_ORDER[step.stage]
        if rank < last_rank and step.stage is not ResearchStage.REGISTER_TASK:
            reasons.append(f"stage_order_regressed_without_new_cycle:{step.step_id}")
        last_rank = rank

        if step.llm_used and not contract.llm_may_propose:
            reasons.append(f"llm_used_in_nonproposal_stage:{step.step_id}:{step.stage.value}")
        if contract.external_verification_required:
            if step.external_verification_observed is None:
                unknown.append(f"verification_unknown:{step.step_id}")
            elif not step.external_verification_observed:
                reasons.append(f"required_external_verification_missing:{step.step_id}")
        if step.stage is ResearchStage.COMPILE_WORKING_CONTEXT:
            if step.mandatory_context_complete is None:
                unknown.append(f"mandatory_context_unknown:{step.step_id}")
            elif not step.mandatory_context_complete:
                reasons.append(f"mandatory_context_incomplete:{step.step_id}")

        for artifact_id in step.input_ids:
            artifact = artifact_by_id.get(artifact_id)
            if artifact is None:
                reasons.append(f"unknown_input_artifact:{step.step_id}:{artifact_id}")
                continue
            if artifact_id in produced_at and produced_at[artifact_id] >= index:
                reasons.append(f"artifact_consumed_before_produced:{step.step_id}:{artifact_id}")
            if step.strong_authority_operation and artifact.lossy:
                if step.raw_evidence_rehydrated is None:
                    unknown.append(f"rehydration_unknown:{step.step_id}:{artifact_id}")
                elif not step.raw_evidence_rehydrated:
                    reasons.append(f"lossy_view_used_without_rehydration:{step.step_id}:{artifact_id}")

        for artifact_id in step.output_ids:
            if artifact_id not in artifact_by_id:
                reasons.append(f"unknown_output_artifact:{step.step_id}:{artifact_id}")
            produced_at.setdefault(artifact_id, index)

        if step.stage is ResearchStage.VERIFY_PROPOSAL:
            verification_seen_by_cycle[step.cycle_index] = index
        if step.stage is ResearchStage.CANONICAL_UPDATE:
            verified_index = verification_seen_by_cycle.get(step.cycle_index)
            if verified_index is None or verified_index >= index:
                reasons.append(f"canonical_update_without_prior_verification:{step.step_id}")

    if require_full_cycle:
        for stage in ResearchStage:
            if counts[stage.value] == 0:
                reasons.append(f"required_stage_missing:{stage.value}")

    if reasons:
        verdict = TraceVerdict.INVALID_TRACE
        final_reasons = tuple(reasons + unknown)
    elif unknown:
        verdict = TraceVerdict.CANNOT_CHECK
        final_reasons = tuple(unknown)
    else:
        verdict = TraceVerdict.VALID_SCOPED_TRACE
        final_reasons = (
            "all_registered_atomic_stages_owned",
            "llm_proposal_authority_separated_from_canonical_update",
            "canonical_update_follows_verification",
            "mandatory_context_checked",
            "lossy_views_require_rehydration_for_strong_authority",
        )

    return ResearchTraceReport(
        verdict=verdict,
        reasons=final_reasons,
        stage_counts=tuple((stage.value, counts[stage.value]) for stage in ResearchStage),
        total_llm_tokens=sum(step.token_cost for step in step_tuple if step.llm_used),
        canonical_artifact_ids=tuple(sorted(a.artifact_id for a in artifact_tuple if a.canonical)),
        lossy_artifact_ids=tuple(sorted(a.artifact_id for a in artifact_tuple if a.lossy)),
    )
