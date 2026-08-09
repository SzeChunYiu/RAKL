from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterable, Mapping, Optional, Sequence, Tuple

from .formalism import (
    FormalEquation,
    FormalSymbol,
    Formalism,
    MechanismEdge,
    MechanismGraph,
    MechanismNode,
    VerificationReport,
    VerificationVerdict,
)


class ResidualKind(str, Enum):
    DISTRIBUTION = "DISTRIBUTION"
    TEMPORAL = "TEMPORAL"
    REGIME = "REGIME"
    TAIL = "TAIL"
    VOLATILITY = "VOLATILITY"
    CROSS_ASSET = "CROSS_ASSET"
    CROSS_VENUE = "CROSS_VENUE"
    FLOW_LIQUIDITY = "FLOW_LIQUIDITY"
    OBSERVATION = "OBSERVATION"
    CLOCK = "CLOCK"
    CAUSAL = "CAUSAL"
    IDENTIFIABILITY = "IDENTIFIABILITY"
    CALIBRATION = "CALIBRATION"
    TRANSPORT = "TRANSPORT"
    PREDICTIVE = "PREDICTIVE"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ResidualSignature:
    residual_id: str
    kinds: Tuple[ResidualKind, ...]
    description: str
    implicated_fiber_ids: Tuple[str, ...] = ()
    failed_candidate_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    diagnostics: Mapping[str, float | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.residual_id:
            raise ValueError("residual_id cannot be empty")
        if not self.kinds:
            raise ValueError("at least one residual kind is required")
        if not self.description:
            raise ValueError("residual description cannot be empty")


class InventionOperator(str, Enum):
    COMPOSE = "COMPOSE"
    RECOMBINE = "RECOMBINE"
    ADD_LATENT_STATE = "ADD_LATENT_STATE"
    REMOVE_LATENT_STATE = "REMOVE_LATENT_STATE"
    SPLIT_REGIME = "SPLIT_REGIME"
    MERGE_REGIME = "MERGE_REGIME"
    CHANGE_CLOCK = "CHANGE_CLOCK"
    COARSE_GRAIN = "COARSE_GRAIN"
    FINE_GRAIN = "FINE_GRAIN"
    GENERALIZE = "GENERALIZE"
    SPECIALIZE = "SPECIALIZE"
    TAKE_LIMIT = "TAKE_LIMIT"
    DUALIZE = "DUALIZE"
    STOCHASTICIZE = "STOCHASTICIZE"
    DETERMINIZE = "DETERMINIZE"
    ADD_FEEDBACK = "ADD_FEEDBACK"
    REMOVE_FEEDBACK = "REMOVE_FEEDBACK"
    ADD_COUPLING = "ADD_COUPLING"
    REMOVE_COUPLING = "REMOVE_COUPLING"
    ADD_INTERACTION = "ADD_INTERACTION"
    RELAX_ASSUMPTION = "RELAX_ASSUMPTION"
    STRENGTHEN_ASSUMPTION = "STRENGTHEN_ASSUMPTION"
    ADD_INVARIANT = "ADD_INVARIANT"
    BREAK_SYMMETRY = "BREAK_SYMMETRY"
    ADD_SYMMETRY = "ADD_SYMMETRY"
    NONLINEARIZE = "NONLINEARIZE"
    LINEARIZE = "LINEARIZE"
    IMPORT_ANALOGICAL_MOTIF = "IMPORT_ANALOGICAL_MOTIF"
    CHANGE_OBSERVATION_MAP = "CHANGE_OBSERVATION_MAP"
    EXPLAIN_RESIDUAL = "EXPLAIN_RESIDUAL"


@dataclass(frozen=True)
class InventionTask:
    task_id: str
    operator: InventionOperator
    question: str
    residual_ids: Tuple[str, ...]
    source_fiber_ids: Tuple[str, ...]
    required_inputs: Tuple[str, ...]
    falsifier_requirements: Tuple[str, ...]


@dataclass(frozen=True)
class InventionMove:
    """Typed delta that mutates one candidate theory into another.

    The proposer may be an LLM, symbolic search, a domain solver, or a human. RAKL
    requires the proposal to be materialized as typed deltas and provenance before
    the result can enter the candidate population.
    """

    move_id: str
    operator: InventionOperator
    rationale: str
    residual_ids: Tuple[str, ...]
    source_fiber_ids: Tuple[str, ...] = ()
    source_witness_ids: Tuple[str, ...] = ()
    add_symbols: Tuple[FormalSymbol, ...] = ()
    remove_symbol_names: Tuple[str, ...] = ()
    add_equations: Tuple[FormalEquation, ...] = ()
    remove_equation_ids: Tuple[str, ...] = ()
    add_mechanism_nodes: Tuple[MechanismNode, ...] = ()
    remove_mechanism_node_ids: Tuple[str, ...] = ()
    add_mechanism_edges: Tuple[MechanismEdge, ...] = ()
    remove_mechanism_edge_ids: Tuple[str, ...] = ()
    add_assumptions: Tuple[str, ...] = ()
    remove_assumptions: Tuple[str, ...] = ()
    add_regimes: Tuple[str, ...] = ()
    remove_regimes: Tuple[str, ...] = ()
    add_symmetries: Tuple[str, ...] = ()
    remove_symmetries: Tuple[str, ...] = ()
    declared_before_evaluation: Optional[bool] = None

    def __post_init__(self) -> None:
        if not self.move_id:
            raise ValueError("move_id cannot be empty")
        if not self.rationale:
            raise ValueError("move rationale cannot be empty")
        if not self.residual_ids:
            raise ValueError("an invention move must target at least one residual")


@dataclass(frozen=True)
class CandidateTheory:
    candidate_id: str
    formalism: Formalism
    parent_candidate_ids: Tuple[str, ...] = ()
    move_history: Tuple[str, ...] = ()
    targeted_residual_ids: Tuple[str, ...] = ()
    generation: int = 0

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id cannot be empty")
        if self.generation < 0:
            raise ValueError("generation cannot be negative")


class CandidateMutationVerdict(str, Enum):
    CREATED = "CREATED"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CandidateMutationReport:
    verdict: CandidateMutationVerdict
    reasons: Tuple[str, ...]
    candidate: Optional[CandidateTheory] = None


def _dedupe_by(items: Iterable, key) -> tuple:
    seen = set()
    output = []
    for item in items:
        item_key = key(item)
        if item_key in seen:
            raise ValueError(f"duplicate typed invention object: {item_key}")
        seen.add(item_key)
        output.append(item)
    return tuple(output)


def apply_invention_move(
    parent: CandidateTheory,
    move: InventionMove,
    *,
    candidate_id: str,
    formalism_id: str,
) -> CandidateMutationReport:
    if move.declared_before_evaluation is None:
        return CandidateMutationReport(
            CandidateMutationVerdict.CANNOT_CHECK,
            ("invention_move_chronology_unknown",),
        )
    if move.declared_before_evaluation is False:
        return CandidateMutationReport(
            CandidateMutationVerdict.REJECT,
            ("post_result_invention_move_not_admissible_for_certifying_lane",),
        )

    try:
        removed_symbols = set(move.remove_symbol_names)
        symbols = tuple(
            symbol for symbol in parent.formalism.symbols if symbol.name not in removed_symbols
        ) + move.add_symbols
        symbols = _dedupe_by(symbols, lambda item: item.name)

        removed_equations = set(move.remove_equation_ids)
        equations = tuple(
            equation
            for equation in parent.formalism.equations
            if equation.equation_id not in removed_equations
        ) + move.add_equations
        equations = _dedupe_by(equations, lambda item: item.equation_id)

        removed_nodes = set(move.remove_mechanism_node_ids)
        nodes = tuple(
            node
            for node in parent.formalism.mechanism.nodes
            if node.node_id not in removed_nodes
        ) + move.add_mechanism_nodes
        nodes = _dedupe_by(nodes, lambda item: item.node_id)

        removed_edges = set(move.remove_mechanism_edge_ids)
        edges = tuple(
            edge
            for edge in parent.formalism.mechanism.edges
            if edge.edge_id not in removed_edges
            and edge.source not in removed_nodes
            and edge.target not in removed_nodes
            and edge.mediator not in removed_nodes
        ) + move.add_mechanism_edges
        edges = _dedupe_by(edges, lambda item: item.edge_id)
    except ValueError as exc:
        return CandidateMutationReport(
            CandidateMutationVerdict.REJECT,
            (str(exc),),
        )

    assumptions = tuple(
        item
        for item in parent.formalism.assumptions
        if item not in set(move.remove_assumptions)
    ) + tuple(item for item in move.add_assumptions if item not in parent.formalism.assumptions)
    regimes = tuple(
        item for item in parent.formalism.regimes if item not in set(move.remove_regimes)
    ) + tuple(item for item in move.add_regimes if item not in parent.formalism.regimes)
    symmetries = tuple(
        item
        for item in parent.formalism.symmetries
        if item not in set(move.remove_symmetries)
    ) + tuple(item for item in move.add_symmetries if item not in parent.formalism.symmetries)

    mechanism = replace(
        parent.formalism.mechanism,
        mechanism_id=f"{parent.formalism.mechanism.mechanism_id}::{move.move_id}",
        nodes=nodes,
        edges=edges,
        source_fiber_ids=tuple(
            dict.fromkeys(parent.formalism.mechanism.source_fiber_ids + move.source_fiber_ids)
        ),
    )
    formalism = replace(
        parent.formalism,
        formalism_id=formalism_id,
        symbols=symbols,
        equations=equations,
        mechanism=mechanism,
        assumptions=tuple(dict.fromkeys(assumptions)),
        regimes=tuple(dict.fromkeys(regimes)),
        symmetries=tuple(dict.fromkeys(symmetries)),
        parent_formalism_ids=tuple(
            dict.fromkeys(parent.formalism.parent_formalism_ids + (parent.formalism.formalism_id,))
        ),
        invention_move_ids=parent.formalism.invention_move_ids + (move.move_id,),
    )
    candidate = CandidateTheory(
        candidate_id=candidate_id,
        formalism=formalism,
        parent_candidate_ids=(parent.candidate_id,),
        move_history=parent.move_history + (move.move_id,),
        targeted_residual_ids=tuple(
            dict.fromkeys(parent.targeted_residual_ids + move.residual_ids)
        ),
        generation=parent.generation + 1,
    )
    return CandidateMutationReport(
        CandidateMutationVerdict.CREATED,
        (
            "typed_invention_delta_applied",
            "candidate_lineage_preserved",
            "targeted_residuals_preserved",
        ),
        candidate,
    )


def recombine_candidates(
    left: CandidateTheory,
    right: CandidateTheory,
    move: InventionMove,
    *,
    candidate_id: str,
    formalism_id: str,
) -> CandidateMutationReport:
    if move.operator not in {
        InventionOperator.COMPOSE,
        InventionOperator.RECOMBINE,
        InventionOperator.IMPORT_ANALOGICAL_MOTIF,
    }:
        return CandidateMutationReport(
            CandidateMutationVerdict.REJECT,
            ("multi_parent_recombination_requires_composition_operator",),
        )
    if move.declared_before_evaluation is not True:
        return CandidateMutationReport(
            CandidateMutationVerdict.CANNOT_CHECK,
            ("recombination_move_must_be_frozen_before_evaluation",),
        )

    merged_move = replace(
        move,
        add_symbols=right.formalism.symbols + move.add_symbols,
        add_equations=right.formalism.equations + move.add_equations,
        add_mechanism_nodes=right.formalism.mechanism.nodes + move.add_mechanism_nodes,
        add_mechanism_edges=right.formalism.mechanism.edges + move.add_mechanism_edges,
        add_assumptions=right.formalism.assumptions + move.add_assumptions,
        add_regimes=right.formalism.regimes + move.add_regimes,
        add_symmetries=right.formalism.symmetries + move.add_symmetries,
        source_fiber_ids=tuple(
            dict.fromkeys(
                move.source_fiber_ids
                + left.formalism.mechanism.source_fiber_ids
                + right.formalism.mechanism.source_fiber_ids
            )
        ),
    )
    result = apply_invention_move(
        left,
        merged_move,
        candidate_id=candidate_id,
        formalism_id=formalism_id,
    )
    if result.candidate is None:
        return result
    return replace(
        result,
        candidate=replace(
            result.candidate,
            parent_candidate_ids=(left.candidate_id, right.candidate_id),
            generation=max(left.generation, right.generation) + 1,
        ),
    )


_RESIDUAL_OPERATOR_MAP: Mapping[ResidualKind, Tuple[InventionOperator, ...]] = {
    ResidualKind.DISTRIBUTION: (
        InventionOperator.STOCHASTICIZE,
        InventionOperator.NONLINEARIZE,
        InventionOperator.ADD_LATENT_STATE,
    ),
    ResidualKind.TEMPORAL: (
        InventionOperator.ADD_LATENT_STATE,
        InventionOperator.ADD_FEEDBACK,
        InventionOperator.CHANGE_CLOCK,
    ),
    ResidualKind.REGIME: (
        InventionOperator.SPLIT_REGIME,
        InventionOperator.ADD_LATENT_STATE,
        InventionOperator.BREAK_SYMMETRY,
    ),
    ResidualKind.TAIL: (
        InventionOperator.STOCHASTICIZE,
        InventionOperator.NONLINEARIZE,
        InventionOperator.IMPORT_ANALOGICAL_MOTIF,
    ),
    ResidualKind.VOLATILITY: (
        InventionOperator.ADD_LATENT_STATE,
        InventionOperator.ADD_FEEDBACK,
        InventionOperator.STOCHASTICIZE,
    ),
    ResidualKind.CROSS_ASSET: (
        InventionOperator.ADD_COUPLING,
        InventionOperator.COMPOSE,
        InventionOperator.IMPORT_ANALOGICAL_MOTIF,
    ),
    ResidualKind.CROSS_VENUE: (
        InventionOperator.ADD_COUPLING,
        InventionOperator.CHANGE_OBSERVATION_MAP,
        InventionOperator.COMPOSE,
    ),
    ResidualKind.FLOW_LIQUIDITY: (
        InventionOperator.ADD_INTERACTION,
        InventionOperator.ADD_FEEDBACK,
        InventionOperator.FINE_GRAIN,
    ),
    ResidualKind.OBSERVATION: (
        InventionOperator.CHANGE_OBSERVATION_MAP,
        InventionOperator.FINE_GRAIN,
        InventionOperator.ADD_LATENT_STATE,
    ),
    ResidualKind.CLOCK: (
        InventionOperator.CHANGE_CLOCK,
        InventionOperator.FINE_GRAIN,
        InventionOperator.COARSE_GRAIN,
    ),
    ResidualKind.CAUSAL: (
        InventionOperator.ADD_INTERACTION,
        InventionOperator.ADD_LATENT_STATE,
        InventionOperator.RECOMBINE,
    ),
    ResidualKind.IDENTIFIABILITY: (
        InventionOperator.CHANGE_OBSERVATION_MAP,
        InventionOperator.SPECIALIZE,
        InventionOperator.ADD_INVARIANT,
    ),
    ResidualKind.CALIBRATION: (
        InventionOperator.SPLIT_REGIME,
        InventionOperator.STOCHASTICIZE,
        InventionOperator.SPECIALIZE,
    ),
    ResidualKind.TRANSPORT: (
        InventionOperator.SPLIT_REGIME,
        InventionOperator.GENERALIZE,
        InventionOperator.IMPORT_ANALOGICAL_MOTIF,
    ),
    ResidualKind.PREDICTIVE: (
        InventionOperator.ADD_LATENT_STATE,
        InventionOperator.ADD_COUPLING,
        InventionOperator.NONLINEARIZE,
    ),
    ResidualKind.UNCLASSIFIED: (
        InventionOperator.EXPLAIN_RESIDUAL,
        InventionOperator.IMPORT_ANALOGICAL_MOTIF,
        InventionOperator.RECOMBINE,
    ),
}


def invention_tasks_for_residual(
    residual: ResidualSignature,
    *,
    max_operators: int = 8,
) -> Tuple[InventionTask, ...]:
    operators: list[InventionOperator] = []
    for kind in residual.kinds:
        for operator in _RESIDUAL_OPERATOR_MAP[kind]:
            if operator not in operators:
                operators.append(operator)
    operators = operators[:max_operators]

    return tuple(
        InventionTask(
            task_id=f"{residual.residual_id}::{operator.value}",
            operator=operator,
            question=(
                f"Construct a typed candidate using {operator.value} that explains residual "
                f"{residual.residual_id}: {residual.description}. State what structure is "
                "added/removed, derive measurable implications, and predeclare a falsifier."
            ),
            residual_ids=(residual.residual_id,),
            source_fiber_ids=residual.implicated_fiber_ids,
            required_inputs=(
                "current_candidate_formalism",
                "relevant_knowledge_fibers",
                "residual_evidence_packet",
            ),
            falsifier_requirements=(
                "observable_implication",
                "regime_scope",
                "failure_condition",
                "candidate_identity_frozen_before_test",
            ),
        )
        for operator in operators
    )


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    descriptive_coverage: float
    residual_closure: float
    predictive_value: float
    identification: float
    falsifiability: float
    robustness: float
    novelty: float
    complexity: float

    def __post_init__(self) -> None:
        bounded = (
            self.descriptive_coverage,
            self.residual_closure,
            self.predictive_value,
            self.identification,
            self.falsifiability,
            self.robustness,
            self.novelty,
        )
        if any(value < 0 or value > 1 for value in bounded):
            raise ValueError("candidate quality dimensions must lie in [0, 1]")
        if self.complexity < 0:
            raise ValueError("complexity cannot be negative")

    def objectives(self) -> tuple[float, ...]:
        return (
            self.descriptive_coverage,
            self.residual_closure,
            self.predictive_value,
            self.identification,
            self.falsifiability,
            self.robustness,
            self.novelty,
            -self.complexity,
        )


def _dominates(left: CandidateScore, right: CandidateScore) -> bool:
    left_values = left.objectives()
    right_values = right.objectives()
    return all(a >= b for a, b in zip(left_values, right_values)) and any(
        a > b for a, b in zip(left_values, right_values)
    )


def pareto_frontier(scores: Iterable[CandidateScore]) -> Tuple[CandidateScore, ...]:
    values = tuple(scores)
    frontier = []
    for candidate in values:
        if any(
            other.candidate_id != candidate.candidate_id and _dominates(other, candidate)
            for other in values
        ):
            continue
        frontier.append(candidate)
    return tuple(frontier)


@dataclass(frozen=True)
class PositiveGoalContract:
    """Immutable success target for a goal-seeking research lane.

    Negative candidate results are evidence and search signals, never terminal project
    success. This contract does not guarantee that nature/data contain a satisfying
    mechanism; it guarantees that RAKL will not rename failure as positive closure.
    """

    contract_id: str
    min_descriptive_coverage: float
    min_residual_closure: float
    min_predictive_value: float
    min_identification: float
    min_falsifiability: float
    min_robustness: float
    max_complexity: Optional[float] = None
    verification_required: bool = True
    thresholds_frozen_before_results: Optional[bool] = None
    negative_results_terminal: bool = False

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise ValueError("contract_id cannot be empty")
        for value in (
            self.min_descriptive_coverage,
            self.min_residual_closure,
            self.min_predictive_value,
            self.min_identification,
            self.min_falsifiability,
            self.min_robustness,
        ):
            if value < 0 or value > 1:
                raise ValueError("goal thresholds must lie in [0, 1]")
        if self.max_complexity is not None and self.max_complexity < 0:
            raise ValueError("max_complexity cannot be negative")
        if self.negative_results_terminal:
            raise ValueError(
                "goal-seeking contract forbids treating negative candidate results as terminal"
            )


class GoalAssessmentVerdict(str, Enum):
    GOAL_ACHIEVED = "GOAL_ACHIEVED"
    CANDIDATE_REJECTED_CONTINUE = "CANDIDATE_REJECTED_CONTINUE"
    CANNOT_CHECK = "CANNOT_CHECK"
    BLOCKED_INTEGRITY = "BLOCKED_INTEGRITY"


@dataclass(frozen=True)
class GoalAssessment:
    verdict: GoalAssessmentVerdict
    reasons: Tuple[str, ...]
    unmet_criteria: Tuple[str, ...] = ()
    next_action: Optional[str] = None


def evaluate_positive_goal(
    contract: PositiveGoalContract,
    score: CandidateScore,
    verification: Optional[VerificationReport],
) -> GoalAssessment:
    if contract.thresholds_frozen_before_results is None:
        return GoalAssessment(
            GoalAssessmentVerdict.CANNOT_CHECK,
            ("goal_threshold_chronology_unknown",),
            next_action="freeze_success_thresholds_before evaluating candidate outcomes",
        )
    if contract.thresholds_frozen_before_results is False:
        return GoalAssessment(
            GoalAssessmentVerdict.BLOCKED_INTEGRITY,
            ("success_thresholds_modified_after_results",),
            next_action="restore a pre-result goal contract before certifying any positive",
        )
    if score.candidate_id == "":
        return GoalAssessment(
            GoalAssessmentVerdict.CANNOT_CHECK,
            ("candidate_identity_missing",),
        )

    unmet: list[str] = []
    comparisons = (
        ("descriptive_coverage", score.descriptive_coverage, contract.min_descriptive_coverage),
        ("residual_closure", score.residual_closure, contract.min_residual_closure),
        ("predictive_value", score.predictive_value, contract.min_predictive_value),
        ("identification", score.identification, contract.min_identification),
        ("falsifiability", score.falsifiability, contract.min_falsifiability),
        ("robustness", score.robustness, contract.min_robustness),
    )
    for name, value, threshold in comparisons:
        if value < threshold:
            unmet.append(f"{name}:{value:.6g}<{threshold:.6g}")
    if contract.max_complexity is not None and score.complexity > contract.max_complexity:
        unmet.append(f"complexity:{score.complexity:.6g}>{contract.max_complexity:.6g}")

    if contract.verification_required:
        if verification is None:
            return GoalAssessment(
                GoalAssessmentVerdict.CANNOT_CHECK,
                ("formal_verification_report_missing",),
                tuple(unmet),
                "run the registered verification oracles on the exact candidate",
            )
        if verification.verdict is VerificationVerdict.CANNOT_CHECK:
            return GoalAssessment(
                GoalAssessmentVerdict.CANNOT_CHECK,
                ("formal_verification_incomplete",) + verification.reasons,
                tuple(unmet),
                "complete unresolved verification checks before certification",
            )
        if verification.verdict is VerificationVerdict.FAIL:
            unmet.extend(f"verification:{item}" for item in verification.failed_checks)

    if unmet:
        return GoalAssessment(
            GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE,
            (
                "candidate_did_not_satisfy_locked_positive_goal",
                "negative_candidate_result_is_nonterminal",
                "convert_failure_into_residual_signature_and generate the next candidate family",
            ),
            tuple(unmet),
            "diagnose residual -> reopen fibers -> generate/mutate/recombine -> verify -> retest",
        )

    return GoalAssessment(
        GoalAssessmentVerdict.GOAL_ACHIEVED,
        (
            "all_predeclared_positive_goal_thresholds_met",
            "required_verification_passed",
            "candidate may advance to independent review and narrow promotion",
        ),
    )


def continuation_required(assessment: GoalAssessment) -> bool:
    """True whenever the research objective has not been positively achieved."""

    return assessment.verdict is not GoalAssessmentVerdict.GOAL_ACHIEVED
