"""Stage-by-stage diagnostics for one Orion run.

A pipeline you can only see the end of is a pipeline you cannot debug. This
measures every stage and reports numbers, so that when the outcome is wrong the
stage that went wrong is visible rather than inferred.

    stage 0  licence      was the search allowed to run, and why
    stage 1  space        how much structure was accumulated, and did it saturate
    stage 2  match        how many structures matched the problem, by verdict
    stage 3  coverage     which required roles are covered, and which are not
    stage 4  compose      atoms / edges / obstructions in the glued structure
    stage 5  reachability which required atoms have no inbound licensed edge
    stage 6  navigate     outcome, route length, route cost, cut
    stage 7  fibres       per fibre: state, rounds spent, growth trajectory
    stage 8  audit        what pursuit action the result licenses next

Each stage carries an `ok` flag with a stated criterion, so a run reads as a
checklist rather than a wall of numbers. The criteria are deliberately weak —
they detect a stage that produced nothing, not a stage that produced the wrong
thing — because a stronger criterion would be a hidden second solver.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .recursive_solver import RecursiveSolveReport, SolveEvent
from .structure_space import (
    MatchVerdict,
    ProblemStructure,
    StructureSpace,
    compose,
    match,
    unmatched_roles,
)


@dataclass(frozen=True)
class StageReport:
    """One stage, with its numbers and whether it met its own weak criterion."""

    stage: str
    ok: bool
    numbers: dict[str, object] = field(default_factory=dict)
    note: str = ""

    def render(self) -> str:
        mark = "ok " if self.ok else "!! "
        nums = "  ".join(f"{k}={v}" for k, v in self.numbers.items())
        tail = f"   {self.note}" if self.note else ""
        return f"  {mark}{self.stage:<13} {nums}{tail}"


@dataclass(frozen=True)
class RunDiagnostics:
    """Every stage of one run, in order."""

    stages: tuple[StageReport, ...]
    events: tuple[SolveEvent, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def first_failing_stage(self) -> str | None:
        for s in self.stages:
            if not s.ok:
                return s.stage
        return None

    def render(self, *, width: int = 78) -> str:
        bar = "-" * width
        lines = [bar, "ORION RUN DIAGNOSTICS", bar]
        lines += [s.render() for s in self.stages]
        first = self.first_failing_stage
        lines.append(bar)
        lines.append(
            "all stages met their criteria"
            if first is None
            else f"first stage failing its criterion: {first}"
        )
        lines.append(bar)
        return "\n".join(lines)


def diagnose_run(
    space: StructureSpace,
    problem: ProblemStructure,
    *,
    start: str,
    goal: str,
    result: RecursiveSolveReport,
    events: tuple[SolveEvent, ...] = (),
    licence: str = "",
    licence_reasons: tuple[str, ...] = (),
) -> RunDiagnostics:
    """Measure every stage of a completed run.

    Runs the match/compose stages again read-only, so the numbers reflect the
    space exactly as the solver left it.
    """

    stages: list[StageReport] = []

    # 0. licence
    if licence:
        stages.append(
            StageReport(
                "licence",
                ok=(licence == "LICENSED"),
                numbers={"licence": licence},
                note="; ".join(licence_reasons)[:80],
            )
        )

    # 1. space
    growth = list(space.growth_per_round)
    stages.append(
        StageReport(
            "space",
            ok=len(space.structures) > 0,
            numbers={
                "structures": len(space.structures),
                "roles": len(space.universe),
                "rounds": len(growth),
                "growth": growth[-8:],
                "saturation": space.saturation().name,
            },
        )
    )

    # 2. match
    matches = match(space, problem)
    by_verdict = {v.name: 0 for v in MatchVerdict}
    for m in matches:
        by_verdict[m.verdict.name] += 1
    stages.append(
        StageReport(
            "match",
            ok=by_verdict["LICENSED"] > 0,
            numbers={"total": len(matches), **by_verdict},
        )
    )

    # 3. coverage
    uncovered = sorted(unmatched_roles(space, problem))
    stages.append(
        StageReport(
            "coverage",
            ok=not uncovered,
            numbers={
                "required": len(problem.required_roles),
                "covered": len(problem.required_roles) - len(uncovered),
                "uncovered": uncovered,
            },
        )
    )

    # 4. compose
    composed = compose(space, problem, start=start, goal=goal)
    stages.append(
        StageReport(
            "compose",
            ok=len(composed.edges) > 0,
            numbers={
                "atoms": len(composed.atoms),
                "edges": len(composed.edges),
                "obstructions": len(composed.obstructions),
            },
        )
    )

    # 5. reachability — required atoms with no inbound licensed edge
    inbound = {e.target for e in composed.edges}
    disconnected = sorted(a for a in problem.required_roles if a != start and a not in inbound)
    stages.append(
        StageReport(
            "reachability",
            ok=not disconnected,
            numbers={"disconnected": disconnected},
            note="" if not disconnected else "covered but no edge reaches these",
        )
    )

    # 6. navigate
    rep = result.report
    route_len = len(rep.route.atoms) if rep.route else 0
    route_cost = getattr(rep.route, "total_cost", None) if rep.route else None
    stages.append(
        StageReport(
            "navigate",
            ok=(rep.outcome.name == "REACHED"),
            numbers={
                "outcome": rep.outcome.name,
                "route_atoms": route_len,
                "route_cost": route_cost,
                "cut": rep.cut is not None,
                "blocked_by": len(rep.blocked_by_obstruction),
            },
            note="; ".join(rep.reasons)[:80],
        )
    )

    # 7. fibres
    per_fibre = {
        f.atom: f"{f.state.name}/{len(f.growth_rounds)}r/{sum(f.growth_rounds):+d}"
        for f in result.fibers
    }
    exhausted = sum(1 for f in result.fibers if f.state.name == "EXHAUSTED")
    stages.append(
        StageReport(
            "fibres",
            ok=(exhausted == 0),
            numbers={
                "opened": len(result.fibers),
                "matched": sum(1 for f in result.fibers if f.state.name == "MATCHED"),
                "exhausted": exhausted,
                "rounds": result.research_rounds_spent,
                "inventions": len(result.inventions),
                "detail": per_fibre,
            },
            note="state/rounds/net-growth per fibre",
        )
    )

    # 8. events
    if events:
        kinds: dict[str, int] = {}
        for e in events:
            kinds[e.kind] = kinds.get(e.kind, 0) + 1
        stages.append(StageReport("events", ok=True, numbers=kinds))

    return RunDiagnostics(tuple(stages), tuple(events))


__all__ = ["RunDiagnostics", "StageReport", "diagnose_run"]
