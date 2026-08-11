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
from .research_memory import (
    REQUIRED_MEMORY_ACTIONS,
    ResearchMemoryReport,
    ResearchMemoryReview,
    ResearchMemoryVerdict,
    audit_research_memory_review,
)
from .research_trace import (
    REQUIRED_TRACE_ACTIONS,
    MathResearchTrace,
    ResearchTraceReport,
    TraceGateVerdict,
    audit_pre_candidate_trace,
)
from .root_coordinate_preservation import (
    REQUIRED_PRESERVATION_ACTIONS,
    PreservationGateReport,
    RootCoordinatePreservationReceipt,
    gate_expensive_candidate_search,
)
from .semantic_shortcut import (
    REQUIRED_SHORTCUT_ACTIONS,
    ObstructionTransformationReview,
    ShortcutMode,
    ShortcutReviewReport,
    ShortcutReviewVerdict,
    audit_obstruction_transformation_review,
)


@dataclass(frozen=True)
class MathResearchPlan:
    assurance: AssuranceReport
    planning_state: ProblemState
    candidate_paths: Tuple[PathCandidate, ...]
    next_blockers: Tuple[ObstructionKind, ...]
    context_gate: ContextGateReport
    memory_gate: ResearchMemoryReport
    shortcut_gate: ShortcutReviewReport
    trace_gate: ResearchTraceReport
    pre_candidate_actions: Tuple[str, ...]
    candidate_generation_allowed: bool
    preservation_gate: PreservationGateReport | None = None


def _facts_from_record(
    record: MathResearchRecord,
    context_fiber: MathContextFiber | None = None,
    memory_review: ResearchMemoryReview | None = None,
    shortcut_review: ObstructionTransformationReview | None = None,
    research_trace: MathResearchTrace | None = None,
) -> frozenset[str]:
    facts: set[str] = set()
    context_report = audit_math_context_fiber(context_fiber)
    if context_report.verdict is ContextGateVerdict.PASS and context_fiber is not None:
        facts.add("context_fiber_frozen")
        facts.add("analogue_method_transfer_mapped")
        facts.add("cross_domain_analogy_scan_complete")
        memory_report = audit_research_memory_review(
            memory_review,
            atom_id=context_fiber.atom_id,
            context_hash=context_fiber.packet_hash,
        )
        if memory_report.verdict is ResearchMemoryVerdict.PASS and memory_review is not None:
            facts.add("success_and_failure_experience_reviewed")
            shortcut_report = audit_obstruction_transformation_review(
                shortcut_review,
                atom_id=context_fiber.atom_id,
                context_hash=context_fiber.packet_hash,
                research_memory_review_hash=memory_review.artifact_hash,
            )
            if (
                shortcut_report.verdict is ShortcutReviewVerdict.PASS
                and shortcut_review is not None
            ):
                facts.add("obstruction_transformation_review_complete")
                facts.add(f"semantic_shortcut_mode:{shortcut_report.selected_mode.value}")
                trace_report = audit_pre_candidate_trace(
                    research_trace,
                    atom_id=context_fiber.atom_id,
                    context_packet_hash=context_fiber.packet_hash,
                    obstruction_transformation_review_hash=shortcut_review.artifact_hash,
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
    memory_review: ResearchMemoryReview | None = None,
    shortcut_review: ObstructionTransformationReview | None = None,
    research_trace: MathResearchTrace | None = None,
) -> ProblemState:
    return ProblemState(
        state_id=record.claim_id,
        signature=signature,
        facts=_facts_from_record(
            record,
            context_fiber,
            memory_review,
            shortcut_review,
            research_trace,
        ),
        obstructions=_obstructions_from_record(record),
    )


def plan_math_research(
    *,
    signature: ProblemSignature,
    record: MathResearchRecord,
    context_fiber: MathContextFiber | None = None,
    memory_review: ResearchMemoryReview | None = None,
    shortcut_review: ObstructionTransformationReview | None = None,
    research_trace: MathResearchTrace | None = None,
    preservation_receipt: RootCoordinatePreservationReceipt | None = None,
    require_preservation_gate: bool = False,
    expected_preservation_sha256: str | None = None,
    operators: Tuple[ResearchOperator, ...] = DEFAULT_OPERATOR_ATLAS,
    max_depth: int = 4,
    top_k: int = 8,
) -> MathResearchPlan:
    """Compile assurance status into obstruction-guided research paths.

    Candidate generation is fail-closed behind discovery-process gates:

    1. **Context gate** — understand the active atom across structural coordinates,
       equivalent formulations, solved/near-solved analogues, method-transfer
       assumptions/disanalogies and witnessed cross-domain analogy search.
    2. **Experience-memory gate** — query both the scoped success-derived tool
       inventory and global failure-experience lattice, recording applicable tools,
       prior failure warnings, reuse scope/difference witnesses, and empty searches.
    3. **Semantic-shortcut gate** — fingerprint the relational obstruction and
       select an invention-last SEARCH/JUMP/GLUE/LIFT route. JUMP needs an explicit
       structural mapping witness, GLUE needs a composition witness, and LIFT needs
       bounded exhaustion plus repeated residual structure and emits only a missing-
       transformation specification.
    4. **Trace gate** — preserve the chronological public decision ledger including
       atomization, context, analogy, expert review, experience-memory review,
       obstruction-transformation review and the proposed next step before any
       candidate is generated.
    5. **Preservation gate** (issue #124) — when required, or when a surrogate→root
       preservation receipt is supplied, missing/stale/refuted receipts fail closed
       before expensive candidate search. Free-form brainstorming that neither
       requires nor supplies a receipt leaves this gate inactive.

    These gates govern reproducible discovery, not theorem truth. Returned paths
    remain planning objects only; theorem and novelty authority stay controlled by
    the mathematical assurance layer.
    """

    assurance = classify_math_record(record)
    context_gate = audit_math_context_fiber(context_fiber)

    if context_gate.verdict is ContextGateVerdict.PASS and context_fiber is not None:
        memory_gate = audit_research_memory_review(
            memory_review,
            atom_id=context_fiber.atom_id,
            context_hash=context_fiber.packet_hash,
        )
    else:
        memory_gate = ResearchMemoryReport(
            ResearchMemoryVerdict.CANNOT_CHECK,
            ("context_gate_must_pass_before_memory_gate",),
        )

    if (
        context_gate.verdict is ContextGateVerdict.PASS
        and memory_gate.verdict is ResearchMemoryVerdict.PASS
        and context_fiber is not None
        and memory_review is not None
    ):
        shortcut_gate = audit_obstruction_transformation_review(
            shortcut_review,
            atom_id=context_fiber.atom_id,
            context_hash=context_fiber.packet_hash,
            research_memory_review_hash=memory_review.artifact_hash,
        )
    else:
        shortcut_gate = ShortcutReviewReport(
            ShortcutReviewVerdict.CANNOT_CHECK,
            ("context_and_memory_gates_must_pass_before_shortcut_gate",),
            False,
            ShortcutMode.CANNOT_CHECK,
        )

    if (
        context_gate.verdict is ContextGateVerdict.PASS
        and memory_gate.verdict is ResearchMemoryVerdict.PASS
        and shortcut_gate.verdict is ShortcutReviewVerdict.PASS
        and context_fiber is not None
        and shortcut_review is not None
    ):
        trace_gate = audit_pre_candidate_trace(
            research_trace,
            atom_id=context_fiber.atom_id,
            context_packet_hash=context_fiber.packet_hash,
            obstruction_transformation_review_hash=shortcut_review.artifact_hash,
        )
    else:
        trace_gate = ResearchTraceReport(
            TraceGateVerdict.CANNOT_CHECK,
            ("context_memory_and_shortcut_gates_must_pass_before_trace_gate",),
        )

    preservation_required = require_preservation_gate or preservation_receipt is not None
    preservation_gate = gate_expensive_candidate_search(
        preservation_receipt,
        expected_root_claim_id=record.claim_id,
        expected_canonical_sha256=expected_preservation_sha256,
        required=preservation_required,
    )

    state = derive_planning_state(
        signature=signature,
        record=record,
        context_fiber=context_fiber,
        memory_review=memory_review,
        shortcut_review=shortcut_review,
        research_trace=research_trace,
    )

    if context_gate.verdict is not ContextGateVerdict.PASS:
        paths: Tuple[PathCandidate, ...] = ()
        pre_candidate_actions = REQUIRED_PRE_CANDIDATE_ACTIONS
        candidate_generation_allowed = False
    elif memory_gate.verdict is not ResearchMemoryVerdict.PASS:
        paths = ()
        pre_candidate_actions = REQUIRED_MEMORY_ACTIONS
        candidate_generation_allowed = False
    elif shortcut_gate.verdict is not ShortcutReviewVerdict.PASS:
        paths = ()
        pre_candidate_actions = REQUIRED_SHORTCUT_ACTIONS
        candidate_generation_allowed = False
    elif trace_gate.verdict is not TraceGateVerdict.PASS:
        paths = ()
        pre_candidate_actions = REQUIRED_TRACE_ACTIONS
        candidate_generation_allowed = False
    elif not preservation_gate.licenses_expensive_candidate_search:
        paths = ()
        pre_candidate_actions = REQUIRED_PRESERVATION_ACTIONS
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
        memory_gate=memory_gate,
        shortcut_gate=shortcut_gate,
        trace_gate=trace_gate,
        pre_candidate_actions=pre_candidate_actions,
        candidate_generation_allowed=candidate_generation_allowed,
        preservation_gate=preservation_gate,
    )


def publication_ready(record: MathResearchRecord) -> bool:
    """Return true only for the strongest current bounded publication stage."""

    report = classify_math_record(record)
    return (
        report.verdict is AssuranceVerdict.PASS
        and report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    )
