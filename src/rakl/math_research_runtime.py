from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .math_context import (
    REQUIRED_PRE_CANDIDATE_ACTIONS,
    ContextGateReport,
    ContextGateVerdict,
    MathContextFiber,
    audit_math_context_fiber,
)
from .math_research_assurance import (
    AssuranceReport,
    AssuranceVerdict,
    MathClaimStage,
    MathResearchRecord,
    audit_formalization,
    audit_novelty,
    audit_proof_receipt,
    classify_math_record,
)
from .problem_solving_algebra import (
    DEFAULT_OPERATOR_ATLAS,
    ObstructionKind,
    PathCandidate,
    ProblemSignature,
    ProblemState,
    ResearchOperator,
    search_operator_paths,
)
from .research_trace import (
    REQUIRED_TRACE_ACTIONS,
    MathResearchTrace,
    ResearchTraceReport,
    TraceGateVerdict,
    audit_pre_candidate_trace,
)


@dataclass(frozen=True)
class MathResearchPlan:
    assurance: AssuranceReport
    planning_state: ProblemState
    candidate_paths: Tuple[PathCandidate, ...]
    next_blockers: Tuple[ObstructionKind, ...]
    context_gate: ContextGateReport
    trace_gate: ResearchTraceReport
    pre_candidate_actions: Tuple[str, ...]
    candidate_generation_allowed: bool


def _facts_from_record(
    record: MathResearchRecord,
    context_fiber: MathContextFiber | None = None,
    research_trace: MathResearchTrace | None = None,
) -> frozenset[str]:
    facts: set[str] = set()
    context_report = audit_math_context_fiber(context_fiber)
    if context_report.verdict is ContextGateVerdict.PASS:
        facts.add("context_fiber_frozen")
        facts.add("analogue_method_transfer_mapped")
        facts.add("cross_domain_analogy_scan_complete")
        trace_report = audit_pre_candidate_trace(
            research_trace,
            atom_id=context_fiber.atom_id if context_fiber else record.claim_id,
            context_packet_hash=context_fiber.packet_hash if context_fiber else "",
        )
        if trace_report.verdict is TraceGateVerdict.PASS:
            facts.add("auditable_research_trace_complete")
    if record.computational_support:
        facts.add("counterexample_screen_complete")
    if record.formalization is not None:
        facts.add("formal_statement_candidate")
        if audit_formalization(record.formalization).verdict is AssuranceVerdict.PASS:
            facts.add("formalization_alignment_candidate")
    if record.proof is not None:
        facts.add("proof_candidate")
        if (
            record.formalization is not None
            and record.proof.theorem_statement_hash
            == record.formalization.formal_statement_hash
            and audit_proof_receipt(record.proof).verdict is AssuranceVerdict.PASS
        ):
            facts.add("verified_proof_candidate")
    if record.novelty is not None and audit_novelty(record.novelty).verdict is AssuranceVerdict.PASS:
        facts.add("bounded_novelty_candidate")
    if record.interestingness_screened:
        facts.add("interestingness_screened")
    if record.external_mathematical_review:
        facts.add("external_mathematical_review")
    return frozenset(facts)


def _obstructions_from_record(record: MathResearchRecord) -> frozenset[ObstructionKind]:
    blockers: set[ObstructionKind] = set()
    formalization = audit_formalization(record.formalization)
    if record.formalization is None:
        blockers.add(ObstructionKind.FORMALIZATION_GAP)
        blockers.add(ObstructionKind.FORMALIZATION_ALIGNMENT_GAP)
    elif formalization.verdict is not AssuranceVerdict.PASS:
        blockers.add(ObstructionKind.FORMALIZATION_ALIGNMENT_GAP)

    proof = audit_proof_receipt(record.proof)
    if proof.verdict is not AssuranceVerdict.PASS:
        blockers.add(ObstructionKind.PROOF_GAP)

    novelty = audit_novelty(record.novelty)
    if novelty.stage is not MathClaimStage.VERIFIED_REDISCOVERY and novelty.verdict is not AssuranceVerdict.PASS:
        blockers.add(ObstructionKind.NOVELTY_GAP)
    if not (record.interestingness_screened and record.external_mathematical_review):
        blockers.add(ObstructionKind.RESEARCH_VALUE_GAP)
    return frozenset(blockers)


def derive_planning_state(
    *,
    signature: ProblemSignature,
    record: MathResearchRecord,
    context_fiber: MathContextFiber | None = None,
    research_trace: MathResearchTrace | None = None,
) -> ProblemState:
    return ProblemState(
        state_id=record.claim_id,
        signature=signature,
        facts=_facts_from_record(record, context_fiber, research_trace),
        obstructions=_obstructions_from_record(record),
    )


def plan_math_research(
    *,
    signature: ProblemSignature,
    record: MathResearchRecord,
    context_fiber: MathContextFiber | None = None,
    research_trace: MathResearchTrace | None = None,
    operators: Tuple[ResearchOperator, ...] = DEFAULT_OPERATOR_ATLAS,
    max_depth: int = 4,
    top_k: int = 8,
) -> MathResearchPlan:
    """Compile assurance status into obstruction-guided research paths.

    Candidate generation is fail-closed behind two process gates.

    1. The context gate requires the atomic object, structural coordinates,
       equivalent formulations, solved/near-solved analogues, method-transfer
       assumptions/disanalogies, a witnessed cross-domain analogy scan, source
       anchors and pre-candidate chronology.
    2. The research-trace gate requires an append-only public decision ledger for
       atomization, context freeze, analogy scan, method transfer and proposed next
       step before any candidate is generated.

    These are discovery-process gates, not theorem-truth gates. Once they pass,
    returned paths are still planning objects only; theorem and novelty authority
    remain controlled by the mathematical assurance layer.
    """

    assurance = classify_math_record(record)
    context_gate = audit_math_context_fiber(context_fiber)

    if context_gate.verdict is ContextGateVerdict.PASS and context_fiber is not None:
        trace_gate = audit_pre_candidate_trace(
            research_trace,
            atom_id=context_fiber.atom_id,
            context_packet_hash=context_fiber.packet_hash,
        )
    else:
        trace_gate = ResearchTraceReport(
            TraceGateVerdict.CANNOT_CHECK,
            ("context_gate_must_pass_before_trace_gate",),
        )

    state = derive_planning_state(
        signature=signature,
        record=record,
        context_fiber=context_fiber,
        research_trace=research_trace,
    )

    if context_gate.verdict is not ContextGateVerdict.PASS:
        paths: Tuple[PathCandidate, ...] = ()
        pre_candidate_actions = REQUIRED_PRE_CANDIDATE_ACTIONS
        candidate_generation_allowed = False
    elif trace_gate.verdict is not TraceGateVerdict.PASS:
        paths = ()
        pre_candidate_actions = REQUIRED_TRACE_ACTIONS
        candidate_generation_allowed = False
    else:
        paths = search_operator_paths(
            state,
            operators,
            max_depth=max_depth,
            top_k=top_k,
        )
        pre_candidate_actions = ()
        candidate_generation_allowed = True

    return MathResearchPlan(
        assurance=assurance,
        planning_state=state,
        candidate_paths=paths,
        next_blockers=tuple(sorted(state.obstructions, key=lambda item: item.value)),
        context_gate=context_gate,
        trace_gate=trace_gate,
        pre_candidate_actions=pre_candidate_actions,
        candidate_generation_allowed=candidate_generation_allowed,
    )


def publication_ready(record: MathResearchRecord) -> bool:
    """Return true only for the strongest current bounded publication stage."""

    report = classify_math_record(record)
    return (
        report.verdict is AssuranceVerdict.PASS
        and report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    )
