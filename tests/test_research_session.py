"""The research session loop — hostile tests.

The loop's only job is to refuse things the underlying mechanics would let
through, so most of these check that it blocks. Two are replays of this
session's own failures: an instrument spent against an uncharacterised
population, and a predicate outside its population's domain.
"""

from __future__ import annotations

import pytest

from rakl.construct_independence import (
    ConstructIndependenceDecision,
    ConstructVerdict,
)
from rakl.recursive_framework_audit import (
    AuditAction,
    AuditCoordinate,
    AuditNode,
    AuditResidual,
)
from rakl.research_session import (
    REVISION_ACTIONS,
    SessionLedger,
    SupportDeclaration,
    SupportVerdict,
    next_step,
)

OPEN = AuditNode(closure_coordinates_pass=False, material_open_residual=True)


def full_support(**over: object) -> SupportDeclaration:
    f: dict[str, object] = dict(
        population="ARN dev split, 326 items",
        predicate_in_domain=True,
        conditioning_variables=("distractor_similarity",),
        reachable_ceiling=0.88,
        ceiling_basis="contract-relative licensed-gold fraction",
    )
    f.update(over)
    return SupportDeclaration(**f)  # type: ignore[arg-type]


def admissible(instrument_id: str = "probe-v1") -> ConstructIndependenceDecision:
    return ConstructIndependenceDecision(instrument_id, ConstructVerdict.ADMISSIBLE)


# --- support gating ---------------------------------------------------------


def test_a_revision_without_declared_support_downgrades_to_cannot_check() -> None:
    step = next_step(
        target_id="t1",
        node=OPEN,
        residual=AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,)),
    )
    assert step.proposed_action is AuditAction.REVISE_MEASUREMENT
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert step.blocked is True
    assert step.support is SupportVerdict.UNDECLARED
    assert set(step.support_gaps) == {
        "population",
        "predicate_in_domain",
        "reachable_ceiling",
        "ceiling_basis",
    }
    assert "unrun check" in " ".join(step.reasons)


def test_declared_support_licenses_the_revision() -> None:
    step = next_step(
        target_id="t1",
        node=OPEN,
        residual=AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,)),
        support=full_support(),
    )
    assert step.licensed_action is AuditAction.REVISE_MEASUREMENT
    assert step.blocked is False
    assert step.support is SupportVerdict.DECLARED


def test_every_revision_action_is_gated_by_support() -> None:
    cases = {
        AuditAction.REFRAME_QUESTION: AuditResidual(plausible_causes=(AuditCoordinate.QUESTION,)),
        AuditAction.CHALLENGE_FRAMEWORK: AuditResidual(plausible_causes=(AuditCoordinate.FRAMEWORK,)),
        AuditAction.SPLIT: AuditResidual(split_required=True),
        AuditAction.MERGE: AuditResidual(merge_required=True),
        AuditAction.REPAIR_INTERFACE: AuditResidual(plausible_causes=(AuditCoordinate.INTERFACE,)),
        AuditAction.REVISE_MEASUREMENT: AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,)),
        AuditAction.ASCEND: AuditResidual(
            plausible_causes=(AuditCoordinate.ATOM,),
            parent_challenge_supported=True,
            distinct_local_repair_families_failed=2,
        ),
    }
    assert set(cases) == set(REVISION_ACTIONS)
    for action, residual in cases.items():
        blocked = next_step(target_id="t", node=OPEN, residual=residual)
        assert blocked.proposed_action is action, action
        assert blocked.licensed_action is AuditAction.CANNOT_CHECK, action
        licensed = next_step(target_id="t", node=OPEN, residual=residual, support=full_support())
        assert licensed.licensed_action is action, action


def test_out_of_domain_predicate_blocks_even_with_a_population() -> None:
    """Replay: the question-level probe, whose predicate postdated its corpus."""

    step = next_step(
        target_id="question-level-probe",
        node=OPEN,
        residual=AuditResidual(plausible_causes=(AuditCoordinate.QUESTION,)),
        support=full_support(predicate_in_domain=False),
    )
    assert step.support is SupportVerdict.OUT_OF_DOMAIN
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "outside the population's domain" in " ".join(step.reasons)


def test_non_revision_actions_are_not_support_gated() -> None:
    """SOLVE_CURRENT and STOP_BOUNDED change no pursuit object."""

    solve = next_step(target_id="t", node=OPEN, residual=AuditResidual())
    assert solve.proposed_action is AuditAction.SOLVE_CURRENT
    assert solve.licensed_action is AuditAction.SOLVE_CURRENT
    assert solve.blocked is False

    stop = next_step(
        target_id="t",
        node=AuditNode(closure_coordinates_pass=True, material_open_residual=False),
        residual=AuditResidual(),
    )
    assert stop.licensed_action is AuditAction.STOP_BOUNDED


def test_out_of_domain_blocks_every_action_not_only_revisions() -> None:
    """Replay: p1-l4-tight-resource-floor.

    The tight stratum's budget was declared outside PROMOTE scope, so both arms
    score 0.0 by construction. On first real use the loop licensed SOLVE_CURRENT
    there, because only revisions were gated. Solving at the current
    representation on a population that cannot express the predicate produces no
    evidence either.
    """

    step = next_step(
        target_id="p1-l4-tight-resource-floor",
        node=OPEN,
        residual=AuditResidual(),  # -> SOLVE_CURRENT, not a revision
        support=full_support(predicate_in_domain=False),
    )
    assert step.proposed_action is AuditAction.SOLVE_CURRENT
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "no action on this population produces evidence" in " ".join(step.reasons)


def test_a_ceiling_below_the_registered_gate_blocks_every_action() -> None:
    """Replay: p4-adaptive-lost-to-static.

    Its tier-3 rigorous harm-free ceiling is 0.0246 against a frozen 0.05 hard
    gate. No repair to the allocation policy changes a ceiling, so no action on
    that instrument can clear it. On first real use the loop licensed SPLIT,
    because the recorded ceiling was compared to nothing.
    """

    step = next_step(
        target_id="p4-adaptive-lost-to-static",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.0246, registered_gate=0.05),
    )
    assert step.proposed_action is AuditAction.SPLIT
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "below the registered gate" in " ".join(step.reasons)


def test_a_ceiling_above_the_gate_does_not_block() -> None:
    step = next_step(
        target_id="headroom",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.30, registered_gate=0.05),
    )
    assert step.licensed_action is AuditAction.SPLIT


def test_a_ceiling_without_a_gate_cannot_block() -> None:
    """A recorded ceiling with nothing to clear is not evidence of anything."""

    step = next_step(
        target_id="no-gate",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.001, registered_gate=None),
    )
    assert step.licensed_action is AuditAction.SPLIT


def test_out_of_domain_blocks_every_action_not_only_revisions() -> None:
    """Replay: p1-l4-tight-resource-floor.

    The tight stratum's budget was declared outside PROMOTE scope, so both arms
    score 0.0 by construction. On first real use the loop licensed SOLVE_CURRENT
    there, because only revisions were gated. Solving at the current
    representation on a population that cannot express the predicate produces no
    evidence either.
    """

    step = next_step(
        target_id="p1-l4-tight-resource-floor",
        node=OPEN,
        residual=AuditResidual(),  # -> SOLVE_CURRENT, not a revision
        support=full_support(predicate_in_domain=False),
    )
    assert step.proposed_action is AuditAction.SOLVE_CURRENT
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "no action on this population produces evidence" in " ".join(step.reasons)


def test_a_ceiling_below_the_registered_gate_blocks_every_action() -> None:
    """Replay: p4-adaptive-lost-to-static.

    Its tier-3 rigorous harm-free ceiling is 0.0246 against a frozen 0.05 hard
    gate. No repair to the allocation policy changes a ceiling, so no action on
    that instrument can clear it. On first real use the loop licensed SPLIT,
    because the recorded ceiling was compared to nothing.
    """

    step = next_step(
        target_id="p4-adaptive-lost-to-static",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.0246, registered_gate=0.05),
    )
    assert step.proposed_action is AuditAction.SPLIT
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "below the registered gate" in " ".join(step.reasons)


def test_a_ceiling_above_the_gate_does_not_block() -> None:
    step = next_step(
        target_id="headroom",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.30, registered_gate=0.05),
    )
    assert step.licensed_action is AuditAction.SPLIT


def test_a_ceiling_without_a_gate_cannot_block() -> None:
    """A recorded ceiling with nothing to clear is not evidence of anything."""

    step = next_step(
        target_id="no-gate",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(reachable_ceiling=0.001, registered_gate=None),
    )
    assert step.licensed_action is AuditAction.SPLIT


# --- instrument gating ------------------------------------------------------


def test_an_inadmissible_instrument_downgrades_to_revise_measurement() -> None:
    """Replay: ARN v2, whose statistic survived gold shuffling."""

    bad = ConstructIndependenceDecision(
        "arn-v2", ConstructVerdict.INADMISSIBLE, violated=("PERMUTATION_NULL",)
    )
    step = next_step(
        target_id="arn",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(),
        instrument=bad,
    )
    assert step.proposed_action is AuditAction.SPLIT
    assert step.licensed_action is AuditAction.REVISE_MEASUREMENT
    assert "PERMUTATION_NULL" in " ".join(step.reasons)


def test_an_unchecked_instrument_downgrades_to_cannot_check() -> None:
    unchecked = ConstructIndependenceDecision(
        "undeclared-v1", ConstructVerdict.CANNOT_CHECK, undeclared=("AUTHOR_SEPARATION",)
    )
    step = next_step(
        target_id="t",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        support=full_support(),
        instrument=unchecked,
    )
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "unrun check is not a pass" in " ".join(step.reasons)


def test_support_gate_precedes_the_instrument_gate() -> None:
    """An undeclared population is not rescued by an admissible instrument."""

    step = next_step(
        target_id="t",
        node=OPEN,
        residual=AuditResidual(split_required=True),
        instrument=admissible(),
    )
    assert step.licensed_action is AuditAction.CANNOT_CHECK
    assert "support undeclared" in " ".join(step.reasons)


def test_every_downgrade_moves_toward_abstention_never_toward_a_claim() -> None:
    weaker = {
        AuditAction.CANNOT_CHECK,
        AuditAction.REVISE_MEASUREMENT,
    }
    residuals = [
        AuditResidual(plausible_causes=(AuditCoordinate.QUESTION,)),
        AuditResidual(split_required=True),
        AuditResidual(merge_required=True),
    ]
    for residual in residuals:
        step = next_step(target_id="t", node=OPEN, residual=residual)
        if step.blocked:
            assert step.licensed_action in weaker


# --- authority and ledger ---------------------------------------------------


def test_nothing_in_the_loop_grants_authority() -> None:
    step = next_step(target_id="t", node=OPEN, residual=AuditResidual(), support=full_support())
    assert step.grants_scientific_authority is False
    assert step.grants_method_promotion_authority is False
    assert SupportDeclaration().grants_scientific_authority is False
    assert SessionLedger("t").grants_scientific_authority is False


def test_the_ledger_is_append_only_and_target_bound() -> None:
    ledger = SessionLedger("t")
    step = next_step(target_id="t", node=OPEN, residual=AuditResidual())
    grown = ledger.with_step(step)
    assert len(ledger.steps) == 0  # original untouched
    assert len(grown.steps) == 1
    with pytest.raises(ValueError, match="targets"):
        grown.with_step(next_step(target_id="other", node=OPEN, residual=AuditResidual()))


def test_step_digest_is_stable_and_sensitive() -> None:
    a = next_step(target_id="t", node=OPEN, residual=AuditResidual(), support=full_support())
    b = next_step(target_id="t", node=OPEN, residual=AuditResidual(), support=full_support())
    assert a.digest() == b.digest()
    c = next_step(target_id="t", node=OPEN, residual=AuditResidual())
    assert c.digest() != a.digest()
