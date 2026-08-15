"""E9: the solver, wired to the licence it is supposed to run under.

The fibre's falsifier is exact:

    solver runs on an unlicensed/stale knowledge state, or search continues
    after valid bounded saturation without reason

`solve_recursive` is a competent search: it decomposes, researches each fibre,
and returns a fibre tree naming what it could not close. What it does not do is
ask whether it is *allowed to run at all*. It consults neither
`assess_knowledge_saturation` nor `evaluate_hard_gates`, so nothing stops it
searching on a stale knowledge state, and nothing stops it continuing after
acquisition has validly saturated.

This is the wiring, not a second solver. `solve_recursive` is untouched and
still owns the search. What is added is the precondition and the stop:

    stale knowledge      -> refuse to start, name the refresh required
    failed hard gate     -> refuse to start, name the gate
    bounded saturation   -> stop, and record that stopping was licensed
    otherwise            -> run the search, and carry the licence into the report

A solver that runs regardless of its knowledge state is a search engine. The
difference between that and this framework is whether the run was licensed, so
the licence is computed before the search and travels with the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Tuple

from .hard_gates import HardGateContract, HardGateObservation, HardGateReport, HardGateState, evaluate_hard_gates
from .recursive_solver import RecursiveSolveReport, solve_recursive
from .research_machine_workflow import (
    KnowledgeAcquisitionRound,
    KnowledgeSaturationPolicy,
    assess_knowledge_saturation,
)


class SolveLicence(str, Enum):
    """Whether the search was allowed to run, and why not when it was not."""

    LICENSED = "LICENSED"
    REFUSED_STALE_KNOWLEDGE = "REFUSED_STALE_KNOWLEDGE"
    REFUSED_ACTIVE_RESIDUAL = "REFUSED_ACTIVE_RESIDUAL"
    REFUSED_HARD_GATE = "REFUSED_HARD_GATE"
    STOPPED_BOUNDED_SATURATION = "STOPPED_BOUNDED_SATURATION"


@dataclass(frozen=True)
class GovernedSolveReport:
    """A search result plus the licence under which it ran — or did not."""

    licence: SolveLicence
    reasons: Tuple[str, ...] = ()
    saturation_terminal: str = ""
    hard_gate_state: str = ""
    snapshot_id: str = ""
    solve: RecursiveSolveReport | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def ran(self) -> bool:
        return self.solve is not None


def _saturation_says_stop(terminal: object) -> bool:
    """True when acquisition has validly saturated and search should not continue."""

    name = getattr(terminal, "name", None) or getattr(terminal, "value", None) or str(terminal)
    return "SATURATED" in str(name).upper() and "NOT" not in str(name).upper()


def governed_solve(
    space: object,
    problem: object,
    *,
    start: str,
    goal: str,
    researcher: Callable[..., object],
    decomposer: Callable[..., object],
    inventor: Callable[..., object] | None = None,
    snapshot_id: str = "",
    rounds: Iterable[KnowledgeAcquisitionRound] = (),
    policy: KnowledgeSaturationPolicy | None = None,
    active_knowledge_residual_ids: Tuple[str, ...] = (),
    freshness_stale: bool = False,
    hard_gate_contract: HardGateContract | None = None,
    hard_gate_observations: Tuple[HardGateObservation, ...] = (),
    candidate_id: str = "",
    max_depth: int = 4,
    max_rounds_per_fiber: int = 8,
) -> GovernedSolveReport:
    """Run the recursive solver only when the knowledge state licenses it.

    Fail-closed and ordered. Staleness and active residuals are checked before
    the gates, and both before the search, because a search on a stale state
    spends effort whose result cannot be attributed. Bounded saturation stops
    the search rather than refusing it: acquisition finishing is a licensed
    reason to stop, not a defect.
    """

    reasons: list[str] = []
    saturation_terminal = ""

    if policy is not None:
        assessment = assess_knowledge_saturation(
            rounds,
            policy=policy,
            active_knowledge_residual_ids=active_knowledge_residual_ids,
            freshness_stale=freshness_stale,
        )
        terminal = getattr(assessment, "terminal", None) or getattr(assessment, "decision", None)
        saturation_terminal = str(getattr(terminal, "name", terminal))

        if active_knowledge_residual_ids:
            reasons.append(
                "active knowledge residual forces targeted refresh before any search: "
                f"{list(active_knowledge_residual_ids)}"
            )
            return GovernedSolveReport(
                SolveLicence.REFUSED_ACTIVE_RESIDUAL,
                tuple(reasons),
                saturation_terminal,
                snapshot_id=snapshot_id,
            )
        if freshness_stale:
            reasons.append("knowledge freshness is stale; an incremental refresh is required first")
            return GovernedSolveReport(
                SolveLicence.REFUSED_STALE_KNOWLEDGE,
                tuple(reasons),
                saturation_terminal,
                snapshot_id=snapshot_id,
            )

    gate_state = ""
    if hard_gate_contract is not None:
        report: HardGateReport = evaluate_hard_gates(
            hard_gate_contract, hard_gate_observations, candidate_id=candidate_id
        )
        state = getattr(report, "state", None) or getattr(report, "verdict", None)
        gate_state = str(getattr(state, "name", state))
        if state is HardGateState.FAIL or gate_state == "FAIL":
            reasons.append(f"hard gate failed for candidate {candidate_id!r}; search is not licensed")
            return GovernedSolveReport(
                SolveLicence.REFUSED_HARD_GATE,
                tuple(reasons),
                saturation_terminal,
                gate_state,
                snapshot_id,
            )
        if state is HardGateState.CANNOT_CHECK or gate_state == "CANNOT_CHECK":
            reasons.append(
                f"hard gate could not be checked for candidate {candidate_id!r}; "
                "an unrun gate is not a pass"
            )
            return GovernedSolveReport(
                SolveLicence.REFUSED_HARD_GATE,
                tuple(reasons),
                saturation_terminal,
                gate_state,
                snapshot_id,
            )

    if saturation_terminal and _saturation_says_stop(saturation_terminal):
        reasons.append(
            f"knowledge acquisition reached {saturation_terminal}; continuing the search would "
            "be search after valid bounded saturation"
        )
        return GovernedSolveReport(
            SolveLicence.STOPPED_BOUNDED_SATURATION,
            tuple(reasons),
            saturation_terminal,
            gate_state,
            snapshot_id,
        )

    solve = solve_recursive(
        space,
        problem,
        start=start,
        goal=goal,
        researcher=researcher,
        decomposer=decomposer,
        inventor=inventor,
        max_depth=max_depth,
        max_rounds_per_fiber=max_rounds_per_fiber,
    )
    reasons.append("knowledge state licenses the search")
    return GovernedSolveReport(
        SolveLicence.LICENSED,
        tuple(reasons),
        saturation_terminal,
        gate_state,
        snapshot_id,
        solve,
    )


def render_governed_solve(report: GovernedSolveReport, *, width: int = 78) -> str:
    """Render the run for an operator: what it was allowed to do, and what it found."""

    bar = "-" * width
    lines = [bar, f"licence   {report.licence.value}"]
    if report.snapshot_id:
        lines.append(f"snapshot  {report.snapshot_id}")
    if report.saturation_terminal:
        lines.append(f"saturation {report.saturation_terminal}")
    if report.hard_gate_state:
        lines.append(f"hard gate {report.hard_gate_state}")
    for reason in report.reasons:
        lines.append(f"  . {reason}")
    if report.solve is not None:
        lines.append(f"outcome   {report.solve.report.outcome.name}")
        lines.append(f"fibers    {len(report.solve.fibers)}  rounds {report.solve.research_rounds_spent}")
        for fiber in report.solve.fibers:
            lines.append(f"    {fiber.atom}: {fiber.state.name}")
    else:
        lines.append("outcome   (search did not run)")
    lines.append(bar)
    return "\n".join(lines)


__all__ = [
    "GovernedSolveReport",
    "SolveLicence",
    "governed_solve",
    "render_governed_solve",
]
