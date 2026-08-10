from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from heapq import heappop, heappush
from itertools import count
from typing import Iterable, Tuple


class OperatorFamily(str, Enum):
    GOAL_TRANSFORM = "GOAL_TRANSFORM"
    REPRESENTATION = "REPRESENTATION"
    DECOMPOSITION = "DECOMPOSITION"
    REDUCTION = "REDUCTION"
    INVARIANT = "INVARIANT"
    RELAXATION = "RELAXATION"
    EXTREMAL = "EXTREMAL"
    SYMMETRY = "SYMMETRY"
    LOCAL_GLOBAL = "LOCAL_GLOBAL"
    COMPUTATIONAL = "COMPUTATIONAL"
    FORMAL_VERIFICATION = "FORMAL_VERIFICATION"
    NOVELTY = "NOVELTY"
    META_DISCOVERY = "META_DISCOVERY"


class ObstructionKind(str, Enum):
    MISSING_REPRESENTATION = "MISSING_REPRESENTATION"
    MISSING_BRIDGE = "MISSING_BRIDGE"
    MISSING_INVARIANT = "MISSING_INVARIANT"
    SEARCH_EXPLOSION = "SEARCH_EXPLOSION"
    FORMALIZATION_GAP = "FORMALIZATION_GAP"
    FORMALIZATION_ALIGNMENT_GAP = "FORMALIZATION_ALIGNMENT_GAP"
    PROOF_GAP = "PROOF_GAP"
    NOVELTY_GAP = "NOVELTY_GAP"
    RESEARCH_VALUE_GAP = "RESEARCH_VALUE_GAP"
    ILL_POSED = "ILL_POSED"
    INDEPENDENCE_BARRIER = "INDEPENDENCE_BARRIER"


class TerminalKind(str, Enum):
    OPEN = "OPEN"
    PROOF = "PROOF"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    INDEPENDENCE_RELATIVE = "INDEPENDENCE_RELATIVE"
    REFORMULATED = "REFORMULATED"
    PARTIAL_RESULT = "PARTIAL_RESULT"


@dataclass(frozen=True)
class ProblemSignature:
    objects: Tuple[str, ...] = ()
    relations: Tuple[str, ...] = ()
    quantifiers: Tuple[str, ...] = ()
    symmetries: Tuple[str, ...] = ()
    domain: str = ""
    goal_type: str = ""
    constraints: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ProblemState:
    state_id: str
    signature: ProblemSignature
    facts: frozenset[str] = frozenset()
    obligations: frozenset[str] = frozenset()
    representations: frozenset[str] = frozenset()
    obstructions: frozenset[ObstructionKind] = frozenset()
    applied_operators: Tuple[str, ...] = ()
    terminal: TerminalKind = TerminalKind.OPEN


@dataclass(frozen=True)
class ResearchOperator:
    operator_id: str
    family: OperatorFamily
    requires_facts: frozenset[str] = frozenset()
    adds_facts: frozenset[str] = frozenset()
    adds_representations: frozenset[str] = frozenset()
    targets: frozenset[ObstructionKind] = frozenset()
    clears: frozenset[ObstructionKind] = frozenset()
    introduces_obligations: frozenset[str] = frozenset()
    cost: float = 1.0
    verification_debt: float = 0.0
    boundary_risk: float = 0.0
    failure_modes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.operator_id:
            raise ValueError("operator_id must be nonempty")
        if self.cost < 0 or self.verification_debt < 0 or self.boundary_risk < 0:
            raise ValueError("operator costs and risks must be nonnegative")
        if not self.clears.issubset(self.targets | self.clears):
            raise ValueError("invalid obstruction declaration")


@dataclass(frozen=True)
class TerminalCertificate:
    kind: TerminalKind
    verified: bool
    scope: str
    artifact_id: str
    checker: str = ""

    def __post_init__(self) -> None:
        if self.kind is TerminalKind.OPEN:
            raise ValueError("OPEN is not a closure certificate")
        if not self.scope or not self.artifact_id:
            raise ValueError("closure certificates require scope and artifact identity")


@dataclass(frozen=True)
class PathCandidate:
    operators: Tuple[str, ...]
    resulting_state: ProblemState
    estimated_cost: float
    obstruction_relief: int
    verification_debt: float
    boundary_risk: float
    score: float


def operator_applicable(operator: ResearchOperator, state: ProblemState) -> bool:
    if state.terminal is not TerminalKind.OPEN:
        return False
    if not operator.requires_facts.issubset(state.facts):
        return False
    if operator.targets and not (operator.targets & state.obstructions):
        return False
    return True


def apply_operator_symbolic(operator: ResearchOperator, state: ProblemState) -> ProblemState:
    """Project a candidate research move without minting terminal authority.

    This function is a planning transition.  It may update candidate facts,
    representations, obligations and modeled blockers, but it can never close a
    mathematical/scientific problem.  Closure requires ``close_with_certificate``.
    """

    if not operator_applicable(operator, state):
        raise ValueError(f"operator {operator.operator_id!r} is not applicable")
    return replace(
        state,
        facts=state.facts | operator.adds_facts,
        obligations=state.obligations | operator.introduces_obligations,
        representations=state.representations | operator.adds_representations,
        obstructions=state.obstructions - operator.clears,
        applied_operators=state.applied_operators + (operator.operator_id,),
        terminal=TerminalKind.OPEN,
    )


def close_with_certificate(
    state: ProblemState, certificate: TerminalCertificate
) -> ProblemState:
    if state.terminal is not TerminalKind.OPEN:
        raise ValueError("state is already terminal")
    if not certificate.verified:
        raise ValueError("unverified certificate cannot close a problem")
    return replace(state, terminal=certificate.kind)


def _path_score(
    *,
    remaining_obstructions: int,
    relief: int,
    cost: float,
    verification_debt: float,
    boundary_risk: float,
) -> float:
    return (
        cost
        + 2.0 * verification_debt
        + 2.0 * boundary_risk
        + float(remaining_obstructions)
        - 3.0 * float(relief)
    )


def search_operator_paths(
    state: ProblemState,
    operators: Iterable[ResearchOperator],
    *,
    max_depth: int = 4,
    top_k: int = 8,
) -> Tuple[PathCandidate, ...]:
    """Best-first search over typed partial operators.

    The search is obstruction-guided and deliberately operates over planning
    states.  A returned path is a candidate research route, never a proof or
    authority certificate.
    """

    if max_depth < 1 or top_k < 1:
        raise ValueError("max_depth and top_k must be positive")
    atlas = tuple(operators)
    initial_obstructions = state.obstructions
    serial = count()
    queue: list[tuple[float, int, ProblemState, float, float, float]] = []
    heappush(queue, (0.0, next(serial), state, 0.0, 0.0, 0.0))
    candidates: list[PathCandidate] = []
    seen: dict[tuple[frozenset[str], frozenset[ObstructionKind], Tuple[str, ...]], float] = {}

    while queue:
        _, _, current, cost_so_far, debt_so_far, risk_so_far = heappop(queue)
        depth = len(current.applied_operators) - len(state.applied_operators)
        relief = len(initial_obstructions - current.obstructions)
        if depth > 0:
            score = _path_score(
                remaining_obstructions=len(current.obstructions),
                relief=relief,
                cost=cost_so_far,
                verification_debt=debt_so_far,
                boundary_risk=risk_so_far,
            )
            candidates.append(
                PathCandidate(
                    operators=current.applied_operators[len(state.applied_operators) :],
                    resulting_state=current,
                    estimated_cost=cost_so_far,
                    obstruction_relief=relief,
                    verification_debt=debt_so_far,
                    boundary_risk=risk_so_far,
                    score=score,
                )
            )
        if depth >= max_depth:
            continue

        for operator in atlas:
            if operator.operator_id in current.applied_operators[len(state.applied_operators) :]:
                continue
            if not operator_applicable(operator, current):
                continue
            nxt = apply_operator_symbolic(operator, current)
            new_cost = cost_so_far + operator.cost
            new_debt = debt_so_far + operator.verification_debt
            new_risk = risk_so_far + operator.boundary_risk
            key = (nxt.facts, nxt.obstructions, nxt.applied_operators[len(state.applied_operators) :])
            scalar = new_cost + new_debt + new_risk
            if key in seen and seen[key] <= scalar:
                continue
            seen[key] = scalar
            new_relief = len(initial_obstructions - nxt.obstructions)
            priority = _path_score(
                remaining_obstructions=len(nxt.obstructions),
                relief=new_relief,
                cost=new_cost,
                verification_debt=new_debt,
                boundary_risk=new_risk,
            )
            heappush(queue, (priority, next(serial), nxt, new_cost, new_debt, new_risk))

    candidates.sort(key=lambda candidate: (candidate.score, candidate.estimated_cost, candidate.operators))
    return tuple(candidates[:top_k])


DEFAULT_OPERATOR_ATLAS: Tuple[ResearchOperator, ...] = (
    ResearchOperator(
        "change_representation",
        OperatorFamily.REPRESENTATION,
        targets=frozenset({ObstructionKind.MISSING_REPRESENTATION}),
        clears=frozenset({ObstructionKind.MISSING_REPRESENTATION}),
        adds_facts=frozenset({"alternate_representation_candidate"}),
        adds_representations=frozenset({"alternate_representation"}),
        introduces_obligations=frozenset({"validate_representation_equivalence"}),
        verification_debt=0.5,
        boundary_risk=0.25,
        failure_modes=("representation_not_equivalent", "boundary_information_lost"),
    ),
    ResearchOperator(
        "introduce_auxiliary_object",
        OperatorFamily.META_DISCOVERY,
        targets=frozenset({ObstructionKind.MISSING_BRIDGE}),
        clears=frozenset({ObstructionKind.MISSING_BRIDGE}),
        adds_facts=frozenset({"auxiliary_bridge_candidate"}),
        introduces_obligations=frozenset({"validate_auxiliary_bridge"}),
        verification_debt=0.75,
        boundary_risk=0.25,
        failure_modes=("bridge_is_only_analogical",),
    ),
    ResearchOperator(
        "search_invariant",
        OperatorFamily.INVARIANT,
        targets=frozenset({ObstructionKind.MISSING_INVARIANT}),
        clears=frozenset({ObstructionKind.MISSING_INVARIANT}),
        adds_facts=frozenset({"candidate_invariant"}),
        introduces_obligations=frozenset({"prove_invariant"}),
        verification_debt=0.75,
        failure_modes=("invariant_holds_only_on_test_cases",),
    ),
    ResearchOperator(
        "decompose_problem",
        OperatorFamily.DECOMPOSITION,
        targets=frozenset({ObstructionKind.SEARCH_EXPLOSION}),
        clears=frozenset({ObstructionKind.SEARCH_EXPLOSION}),
        adds_facts=frozenset({"subproblem_decomposition"}),
        introduces_obligations=frozenset({"prove_decomposition_complete"}),
        cost=0.75,
        verification_debt=0.5,
    ),
    ResearchOperator(
        "reformulate_ill_posed_target",
        OperatorFamily.GOAL_TRANSFORM,
        targets=frozenset({ObstructionKind.ILL_POSED}),
        clears=frozenset({ObstructionKind.ILL_POSED}),
        adds_facts=frozenset({"reformulated_target_candidate"}),
        introduces_obligations=frozenset({"review_reformulation_scope"}),
        boundary_risk=0.5,
    ),
    ResearchOperator(
        "formalize_target",
        OperatorFamily.FORMAL_VERIFICATION,
        targets=frozenset({ObstructionKind.FORMALIZATION_GAP}),
        clears=frozenset({ObstructionKind.FORMALIZATION_GAP}),
        adds_facts=frozenset({"formal_statement_candidate"}),
        introduces_obligations=frozenset({"audit_formalization_alignment"}),
        verification_debt=0.5,
    ),
    ResearchOperator(
        "audit_formalization_alignment",
        OperatorFamily.FORMAL_VERIFICATION,
        requires_facts=frozenset({"formal_statement_candidate"}),
        targets=frozenset({ObstructionKind.FORMALIZATION_ALIGNMENT_GAP}),
        clears=frozenset({ObstructionKind.FORMALIZATION_ALIGNMENT_GAP}),
        adds_facts=frozenset({"formalization_alignment_candidate"}),
        verification_debt=0.25,
    ),
    ResearchOperator(
        "counterexample_first",
        OperatorFamily.COMPUTATIONAL,
        targets=frozenset({ObstructionKind.PROOF_GAP}),
        adds_facts=frozenset({"counterexample_screen_complete"}),
        cost=0.5,
        failure_modes=("no_counterexample_found_is_not_proof",),
    ),
    ResearchOperator(
        "formal_proof_search",
        OperatorFamily.FORMAL_VERIFICATION,
        requires_facts=frozenset({"formal_statement_candidate"}),
        targets=frozenset({ObstructionKind.PROOF_GAP}),
        adds_facts=frozenset({"proof_candidate"}),
        introduces_obligations=frozenset({"verify_exact_proof_artifact"}),
        cost=2.0,
        verification_debt=0.5,
    ),
    ResearchOperator(
        "verify_proof_artifact",
        OperatorFamily.FORMAL_VERIFICATION,
        requires_facts=frozenset({"proof_candidate"}),
        targets=frozenset({ObstructionKind.PROOF_GAP}),
        clears=frozenset({ObstructionKind.PROOF_GAP}),
        adds_facts=frozenset({"verified_proof_candidate"}),
        cost=0.75,
        failure_modes=("axiom_or_checker_trust_failure", "statement_hash_mismatch"),
    ),
    ResearchOperator(
        "search_prior_art",
        OperatorFamily.NOVELTY,
        requires_facts=frozenset({"verified_proof_candidate"}),
        targets=frozenset({ObstructionKind.NOVELTY_GAP}),
        clears=frozenset({ObstructionKind.NOVELTY_GAP}),
        adds_facts=frozenset({"bounded_novelty_candidate"}),
        introduces_obligations=frozenset({"independent_novelty_review"}),
        cost=1.5,
        verification_debt=0.5,
        boundary_risk=0.5,
        failure_modes=("rediscovery_under_changed_notation", "corpus_coverage_gap"),
    ),
    ResearchOperator(
        "review_research_value",
        OperatorFamily.META_DISCOVERY,
        requires_facts=frozenset({"verified_proof_candidate"}),
        targets=frozenset({ObstructionKind.RESEARCH_VALUE_GAP}),
        clears=frozenset({ObstructionKind.RESEARCH_VALUE_GAP}),
        adds_facts=frozenset({"research_value_screen_candidate"}),
        introduces_obligations=frozenset({"external_mathematical_review"}),
        cost=1.0,
        boundary_risk=0.25,
    ),
)
