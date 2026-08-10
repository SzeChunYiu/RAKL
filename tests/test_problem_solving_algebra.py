from __future__ import annotations

import pytest

from rakl.problem_solving_algebra import (
    DEFAULT_OPERATOR_ATLAS,
    ObstructionKind,
    OperatorFamily,
    ProblemSignature,
    ProblemState,
    ResearchOperator,
    TerminalCertificate,
    TerminalKind,
    apply_operator_symbolic,
    close_with_certificate,
    operator_applicable,
    search_operator_paths,
)


def _state(*blockers: ObstructionKind, facts: frozenset[str] = frozenset()) -> ProblemState:
    return ProblemState(
        state_id="P",
        signature=ProblemSignature(domain="mathematics", goal_type="prove theorem"),
        facts=facts,
        obstructions=frozenset(blockers),
    )


def test_operator_requires_matching_blocker_and_facts() -> None:
    proof_search = next(
        operator for operator in DEFAULT_OPERATOR_ATLAS if operator.operator_id == "formal_proof_search"
    )
    assert not operator_applicable(proof_search, _state(ObstructionKind.PROOF_GAP))
    assert operator_applicable(
        proof_search,
        _state(ObstructionKind.PROOF_GAP, facts=frozenset({"formal_statement_candidate"})),
    )


def test_symbolic_planning_move_cannot_mint_terminal_authority() -> None:
    state = _state(ObstructionKind.MISSING_REPRESENTATION)
    operator = next(
        operator for operator in DEFAULT_OPERATOR_ATLAS if operator.operator_id == "change_representation"
    )
    projected = apply_operator_symbolic(operator, state)
    assert projected.terminal is TerminalKind.OPEN
    assert ObstructionKind.MISSING_REPRESENTATION not in projected.obstructions
    assert "validate_representation_equivalence" in projected.obligations


def test_unverified_terminal_certificate_is_rejected() -> None:
    state = _state(ObstructionKind.PROOF_GAP)
    certificate = TerminalCertificate(
        kind=TerminalKind.PROOF,
        verified=False,
        scope="fixed theorem statement",
        artifact_id="proof-1",
    )
    with pytest.raises(ValueError, match="unverified"):
        close_with_certificate(state, certificate)


def test_verified_terminal_certificate_closes_only_requested_terminal_kind() -> None:
    state = _state(ObstructionKind.PROOF_GAP)
    certificate = TerminalCertificate(
        kind=TerminalKind.COUNTEREXAMPLE,
        verified=True,
        scope="universal conjecture",
        artifact_id="counterexample-17",
        checker="exact arithmetic",
    )
    closed = close_with_certificate(state, certificate)
    assert closed.terminal is TerminalKind.COUNTEREXAMPLE


def test_path_search_prefers_low_cost_obstruction_relief() -> None:
    state = _state(ObstructionKind.MISSING_INVARIANT)
    cheap = ResearchOperator(
        "cheap_invariant",
        OperatorFamily.INVARIANT,
        targets=frozenset({ObstructionKind.MISSING_INVARIANT}),
        clears=frozenset({ObstructionKind.MISSING_INVARIANT}),
        cost=1.0,
    )
    expensive = ResearchOperator(
        "expensive_invariant",
        OperatorFamily.INVARIANT,
        targets=frozenset({ObstructionKind.MISSING_INVARIANT}),
        clears=frozenset({ObstructionKind.MISSING_INVARIANT}),
        cost=10.0,
    )
    paths = search_operator_paths(state, (expensive, cheap), max_depth=1, top_k=2)
    assert paths[0].operators == ("cheap_invariant",)
    assert paths[0].obstruction_relief == 1


def test_operator_composition_is_partial_and_noncommutative() -> None:
    formalize = next(
        operator for operator in DEFAULT_OPERATOR_ATLAS if operator.operator_id == "formalize_target"
    )
    proof_search = next(
        operator for operator in DEFAULT_OPERATOR_ATLAS if operator.operator_id == "formal_proof_search"
    )
    state = _state(ObstructionKind.FORMALIZATION_GAP, ObstructionKind.PROOF_GAP)
    assert not operator_applicable(proof_search, state)
    after_formalize = apply_operator_symbolic(formalize, state)
    assert operator_applicable(proof_search, after_formalize)
