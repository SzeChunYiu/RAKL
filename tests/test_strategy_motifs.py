from __future__ import annotations

from rakl.problem_solving_algebra import (
    DEFAULT_OPERATOR_ATLAS,
    ObstructionKind,
    ProblemSignature,
    ProblemState,
)
from rakl.strategy_motifs import (
    DEFAULT_STRATEGY_MOTIFS,
    StrategyMotif,
    instantiate_strategy_motif,
    rank_strategy_motifs,
    validate_strategy_motif,
)


def _state(*blockers: ObstructionKind) -> ProblemState:
    return ProblemState(
        state_id="P",
        signature=ProblemSignature(domain="mathematics"),
        obstructions=frozenset(blockers),
    )


def test_unknown_operator_in_motif_fails_validation() -> None:
    motif = StrategyMotif("bad", ("does_not_exist",))
    assert validate_strategy_motif(motif, DEFAULT_OPERATOR_ATLAS) == (
        "unknown_operator:does_not_exist",
    )


def test_motif_instantiation_respects_partial_composition() -> None:
    motif = next(
        item for item in DEFAULT_STRATEGY_MOTIFS if item.motif_id == "verified_discovery_closeout"
    )
    state = _state(
        ObstructionKind.FORMALIZATION_GAP,
        ObstructionKind.FORMALIZATION_ALIGNMENT_GAP,
        ObstructionKind.PROOF_GAP,
        ObstructionKind.NOVELTY_GAP,
        ObstructionKind.RESEARCH_VALUE_GAP,
    )
    result = instantiate_strategy_motif(state, motif, DEFAULT_OPERATOR_ATLAS)
    assert result.applicable_prefix[:2] == (
        "formalize_target",
        "audit_formalization_alignment",
    )
    assert result.blocked_at is None
    assert result.obstruction_relief == 5


def test_ranked_motif_prefers_one_that_reliefs_current_blocker() -> None:
    state = _state(ObstructionKind.MISSING_REPRESENTATION)
    ranked = rank_strategy_motifs(state, DEFAULT_STRATEGY_MOTIFS, DEFAULT_OPERATOR_ATLAS)
    assert ranked[0].motif_id == "representation_bridge_invariant"
    assert ranked[0].applicable_prefix == ("change_representation",)
