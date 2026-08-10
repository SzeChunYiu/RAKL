from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .problem_solving_algebra import (
    ObstructionKind,
    ProblemState,
    ResearchOperator,
    apply_operator_symbolic,
    operator_applicable,
)


@dataclass(frozen=True)
class StrategyMotif:
    motif_id: str
    operator_ids: Tuple[str, ...]
    target_obstructions: frozenset[ObstructionKind] = frozenset()
    description: str = ""
    failure_modes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.motif_id or not self.operator_ids:
            raise ValueError("strategy motifs require an identity and operator sequence")


@dataclass(frozen=True)
class MotifInstantiation:
    motif_id: str
    applicable_prefix: Tuple[str, ...]
    blocked_at: str | None
    resulting_state: ProblemState
    obstruction_relief: int


def validate_strategy_motif(
    motif: StrategyMotif,
    operators: Iterable[ResearchOperator],
) -> Tuple[str, ...]:
    atlas = {operator.operator_id: operator for operator in operators}
    reasons: list[str] = []
    for operator_id in motif.operator_ids:
        if operator_id not in atlas:
            reasons.append(f"unknown_operator:{operator_id}")
    return tuple(reasons)


def instantiate_strategy_motif(
    state: ProblemState,
    motif: StrategyMotif,
    operators: Iterable[ResearchOperator],
) -> MotifInstantiation:
    atlas = {operator.operator_id: operator for operator in operators}
    reasons = validate_strategy_motif(motif, atlas.values())
    if reasons:
        raise ValueError(";".join(reasons))

    initial = state.obstructions
    current = state
    prefix: list[str] = []
    blocked_at: str | None = None
    for operator_id in motif.operator_ids:
        operator = atlas[operator_id]
        if not operator_applicable(operator, current):
            blocked_at = operator_id
            break
        current = apply_operator_symbolic(operator, current)
        prefix.append(operator_id)

    return MotifInstantiation(
        motif_id=motif.motif_id,
        applicable_prefix=tuple(prefix),
        blocked_at=blocked_at,
        resulting_state=current,
        obstruction_relief=len(initial - current.obstructions),
    )


def rank_strategy_motifs(
    state: ProblemState,
    motifs: Iterable[StrategyMotif],
    operators: Iterable[ResearchOperator],
) -> Tuple[MotifInstantiation, ...]:
    instantiated = [
        instantiate_strategy_motif(state, motif, operators) for motif in motifs
    ]
    instantiated.sort(
        key=lambda item: (
            item.blocked_at is not None,
            -item.obstruction_relief,
            -len(item.applicable_prefix),
            item.motif_id,
        )
    )
    return tuple(instantiated)


DEFAULT_STRATEGY_MOTIFS: Tuple[StrategyMotif, ...] = (
    StrategyMotif(
        motif_id="representation_bridge_invariant",
        operator_ids=(
            "change_representation",
            "introduce_auxiliary_object",
            "search_invariant",
        ),
        target_obstructions=frozenset(
            {
                ObstructionKind.MISSING_REPRESENTATION,
                ObstructionKind.MISSING_BRIDGE,
                ObstructionKind.MISSING_INVARIANT,
            }
        ),
        description="Change coordinates, invent a bridge object, then search for a load-bearing invariant.",
        failure_modes=("representation_and_bridge_do_not_share_a_valid_scope",),
    ),
    StrategyMotif(
        motif_id="decompose_then_formalize",
        operator_ids=("decompose_problem", "formalize_target"),
        target_obstructions=frozenset(
            {ObstructionKind.SEARCH_EXPLOSION, ObstructionKind.FORMALIZATION_GAP}
        ),
        description="Reduce search horizon before binding exact formal obligations.",
    ),
    StrategyMotif(
        motif_id="counterexample_then_proof",
        operator_ids=(
            "counterexample_first",
            "formal_proof_search",
            "verify_proof_artifact",
        ),
        target_obstructions=frozenset({ObstructionKind.PROOF_GAP}),
        description="Attempt cheap falsification before expensive proof search and exact verification.",
    ),
    StrategyMotif(
        motif_id="verified_discovery_closeout",
        operator_ids=(
            "formalize_target",
            "audit_formalization_alignment",
            "formal_proof_search",
            "verify_proof_artifact",
            "search_prior_art",
            "review_research_value",
        ),
        target_obstructions=frozenset(
            {
                ObstructionKind.FORMALIZATION_GAP,
                ObstructionKind.FORMALIZATION_ALIGNMENT_GAP,
                ObstructionKind.PROOF_GAP,
                ObstructionKind.NOVELTY_GAP,
                ObstructionKind.RESEARCH_VALUE_GAP,
            }
        ),
        description="End-to-end candidate route from informal theorem to bounded new-mathematics review.",
        failure_modes=("planning_completion_is_not_authority",),
    ),
)
