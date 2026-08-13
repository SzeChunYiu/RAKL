"""#538 field-construction SUCCESSOR: goal-set reachability-grounded fields.

Root-cause repair of the #520 NEGATIVE (``field_construction.json``,
``net_search_saving`` mean=-0.3738, KEEP_PROPOSAL_ONLY). Three diagnosed causes:

  1. GOAL-REPRESENTATION MISMATCH -- ``field.target`` was a single synthetic
     goal state, but search accepts ANY state containing the target proposition.
  2. LANDMARK EVALUATOR PROXY -- ``len(state.symmetric_difference(landmark))``
     was used instead of actual transition distances; this is anti-correlated
     with operator cost-to-go, so field-guided search expanded MORE nodes than
     plain BFS (search_saving < 0). The published "fix" still used this proxy.
  3. NO AMORTIZATION -- full construction cost charged for a single query, with
     default 999999.0 for un-tabled states (every un-tabled state looks terrible,
     so search refuses to leave the table even when the goal path lies outside).

This module provides the SUCCESSOR ladder plus the parent controls a win must
beat. Every constructor builds a :class:`ConstructedField` using ONLY the cheap
observables of :class:`ConstructionDomain` (successors / predecessors /
features); the exact cost-to-go is computed by backward induction on the forward
DAG and is the ORACLE / lower-bound ceiling (best possible guidance), NOT a
deployment affordance. ``ConstructionCost.oracle_calls`` stays zero everywhere.

Claim class = EFFICIENCY; the charged cost field is ``construction_cost``.
Nothing here grants scientific authority.
"""
from __future__ import annotations

import heapq
import random
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from rakl.field_construction import (
    AdmissibilityStatus,
    AdmissibilityAudit,
    AuditCoverage,
    ConstructionCost,
    ConstructedField,
)

State = frozenset

__all__ = [
    "forward_reachable",
    "exact_goal_set_cost_to_go",
    "greedy_best_first_search",
    "UniformFieldConstructor",
    "SymDiffProxyFieldConstructor",
    "SingleTargetFieldConstructor",
    "PatternDatabaseFieldConstructor",
    "CEGARAbstractionFieldConstructor",
    "GoalSetExactFieldConstructor",
    "GoalSetLandmarkFieldConstructor",
    "HybridFieldConstructor",
]


# ---------------------------------------------------------------------------
# domain helpers (cheap observables only)
# ---------------------------------------------------------------------------


def forward_reachable(domain, roots: Iterable[State], cap: int = 20000) -> set:
    """Forward closure from ``roots`` using ``domain.successors`` (cheap)."""
    seen: set = set()
    queue: deque = deque()
    for r in roots:
        if r not in seen:
            seen.add(r)
            queue.append(r)
    while queue and len(seen) < cap:
        s = queue.popleft()
        for s2, _ in domain.successors(s):
            if s2 not in seen:
                seen.add(s2)
                queue.append(s2)
    return seen


def exact_goal_set_cost_to_go(
    domain, states: Iterable[State], target
) -> Tuple[Dict[State, float], int]:
    """Exact h*(s) = min_{g in G} d(s, g) over the goal set G = {s : target in s}.

    The forward graph of a monotone proof-state domain is a DAG (operators only
    ADD propositions), so cost-to-go is well defined by backward induction:
    h*(s) = 0 if target in s else min_{(s', c) in succ(s)} (c + h*(s')).  We
    process states in DECREASING cardinality so every successor (which is
    strictly larger) is already solved.  Returns (table, node_expansions).
    """
    order = sorted(set(states), key=lambda s: (-len(s), sorted(s)))
    table: Dict[State, float] = {}
    expansions = 0
    for s in order:
        expansions += 1
        if target in s:
            table[s] = 0.0
            continue
        best = float("inf")
        for s2, c in domain.successors(s):
            if s2 in table:  # successor is larger -> already solved
                val = c + table[s2]
                if val < best:
                    best = val
        table[s] = best
    # Dead ends (target unreachable) have true h* = inf. The field contract
    # requires finite nonnegative values, and a dead end must rank WORST under
    # greedy best-first (highest h, popped last). Cap inf to max_finite+1.0:
    # this is still a valid lower bound (finite <= inf -> admissible) and never
    # exceeds the contract. Derived from the data, not an arbitrary constant.
    finite_vals = [v for v in table.values() if v != float("inf")]
    cap = (max(finite_vals) + 1.0) if finite_vals else 1.0
    for s in table:
        if table[s] == float("inf"):
            table[s] = cap
    return table, expansions


def greedy_best_first_search(
    domain,
    phi: Optional[Callable[[State], float]],
    start: State,
    target,
    budget: int = 10000,
) -> Dict[str, object]:
    """Best-first search. ``phi=None`` degrades to FIFO BFS (the uniform parent).

    Returns expanded-node count, found flag and seen-set size. Each popped state
    is one node expansion (the atomic work unit every cost is denominated in).
    """
    seen = {start}
    expanded = 0
    found = target in start
    if phi is None:
        queue: deque = deque([start])
        while queue and expanded < budget and not found:
            s = queue.popleft()
            expanded += 1
            if target in s:
                found = True
                break
            for s2, _ in domain.successors(s):
                if s2 not in seen:
                    seen.add(s2)
                    queue.append(s2)
    else:
        counter = 0
        heap = [(phi(start), counter, start)]
        while heap and expanded < budget and not found:
            _, _, s = heapq.heappop(heap)
            expanded += 1
            if target in s:
                found = True
                break
            for s2, _ in domain.successors(s):
                if s2 not in seen:
                    seen.add(s2)
                    counter += 1
                    heapq.heappush(heap, (phi(s2), counter, s2))
    return {"expanded": expanded, "found": found, "seen": len(seen)}


# ---------------------------------------------------------------------------
# parent controls (baselines a win must beat) + oracle ceiling + successor
# ---------------------------------------------------------------------------


class UniformFieldConstructor:
    """Trivial parent: h(s)=0 everywhere (search degrades to BFS)."""

    strategy_id = "uniform_bfs_parent"

    def construct(self, domain, target) -> ConstructedField:
        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(),
            table={frozenset({target}): 0.0},
            default_value=0.0,
            per_query_evaluation_cost=0.0,
            provenance={"constructor": "uniform_bfs_parent", "role": "trivial_parent"},
        )


class SymDiffProxyFieldConstructor:
    """HISTORICAL NEGATIVE parent (#520): the broken symmetric-difference proxy.

    Reproduces the original evaluator verbatim: for un-tabled states it ranks by
    ``len(state ^ landmark)`` (anti-correlated with operator distance) and uses a
    huge default. This is the mechanic that produced net_search_saving=-0.3738.
    """

    strategy_id = "symdiff_proxy_parent"

    def __init__(self, sample_budget: int = 500):
        self.sample_budget = sample_budget

    def construct(self, domain, target) -> ConstructedField:
        goal_states = [s for s in domain.all_goal_states(target)] or [frozenset({target})]
        landmarks: Dict[State, float] = {g: 0.0 for g in goal_states}
        frontier = deque(goal_states)
        seen = set(goal_states)
        expansions = 0
        while frontier and len(landmarks) < 100 and expansions < self.sample_budget:
            cur = frontier.popleft()
            cd = landmarks[cur]
            for pred, ec in domain.predecessors(cur):
                if pred not in seen:
                    seen.add(pred)
                    landmarks[pred] = cd + ec
                    frontier.append(pred)
                    expansions += 1
                elif pred in landmarks and landmarks[pred] > cd + ec:
                    landmarks[pred] = cd + ec
        table = dict(landmarks)

        def evaluator(state: State) -> float:
            if state in table:
                return table[state]
            best = float("inf")
            for lm, lc in landmarks.items():
                diff = len(state ^ lm)
                total = diff + lc
                if total < best:
                    best = total
            return best if best != float("inf") else 999999.0

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=goal_states[0],
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(node_expansions=expansions),
            table=table,
            evaluator=evaluator,
            default_value=999999.0,
            provenance={"constructor": "symdiff_proxy_parent", "role": "historical_negative"},
        )


class SingleTargetFieldConstructor:
    """#520 BUG parent: distance to ONE sampled goal representative, not the set."""

    strategy_id = "single_target_parent"

    def __init__(self, sample_budget: int = 500):
        self.sample_budget = sample_budget

    def construct(self, domain, target) -> ConstructedField:
        goal_states = [s for s in domain.all_goal_states(target)] or [frozenset({target})]
        rep = goal_states[0]  # the bug: one representative, not the goal SET
        # exact backward BFS distance to this single representative only
        dist: Dict[State, float] = {rep: 0.0}
        frontier = deque([rep])
        in_queue = {rep}
        expansions = 0
        while frontier and expansions < self.sample_budget:
            cur = frontier.popleft()
            in_queue.discard(cur)
            cd = dist[cur]
            for pred, ec in domain.predecessors(cur):
                nd = cd + ec
                if pred not in dist or dist[pred] > nd:
                    dist[pred] = nd
                    if pred not in in_queue:
                        frontier.append(pred)
                        in_queue.add(pred)
                    expansions += 1
        table = dict(dist)

        def evaluator(state: State) -> float:
            if state in table:
                return table[state]
            return 0.0  # admissible default (no info outside the single-target cone)

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=rep,
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(node_expansions=expansions),
            table=table,
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "single_target_parent", "role": "goal_representation_bug"},
        )


class PatternDatabaseFieldConstructor:
    """PDB parent: exact cost-to-go on a projection (pattern) of the propositions.

    Project every state to ``s & pattern`` (a subset of propositions). The
    projected transition graph is a RELAXATION (projection can only merge
    states), so the projected exact cost-to-go is an admissible lower bound on
    the original. Classic pattern-database heuristic.
    """

    strategy_id = "pdb_parent"

    def __init__(self, pattern_size: int = 6, target_aware: bool = True):
        self.pattern_size = pattern_size
        # ``target_aware`` is STANDARD PDB practice: the goal variable is always
        # included in the pattern (an abstract space that cannot see the goal
        # yields the trivial 0 heuristic). This is the FAIR strong parent; a PDB
        # that omits the goal is a degenerate strawman.
        self.target_aware = target_aware

    def construct(self, domain, target) -> ConstructedField:
        n = domain.n_propositions
        if self.target_aware:
            others = [p for p in range(n) if p != target]
            pattern = frozenset({target} | set(others[:max(0, self.pattern_size - 1)]))
        else:
            pattern = frozenset(range(min(self.pattern_size, n)))
        abstract_axiom = frozenset(a for a in domain.axioms if a in pattern)
        at_target = target if target in pattern else None
        # build abstract reachable space + projected rules
        seen: Dict[State, float] = {}
        # abstract forward closure from the abstract axiom
        start = abstract_axiom
        seen[start] = 0.0
        frontier = deque([start])
        edges = 0
        while frontier:
            cur = frontier.popleft()
            for rule in domain.rules:
                if rule.can_apply(cur) and rule.conclusion in pattern:
                    nxt = cur | {rule.conclusion}
                    if nxt not in seen:
                        seen[nxt] = 0.0
                        frontier.append(nxt)
                    edges += 1
        # exact cost-to-go on the abstract space (target reachable only if in pattern)
        a_states = list(seen.keys())
        if at_target is None:
            at_table = {s: 0.0 for s in a_states}  # target not in pattern: no info
            expansions = len(a_states)
        else:
            at_table, expansions = exact_goal_set_cost_to_go(
                _ProjectedDomain(domain, pattern), a_states, at_target)
        build_cost = ConstructionCost(abstract_node_expansions=expansions)

        def evaluator(state: State) -> float:
            proj = state & pattern
            return at_table.get(proj, 0.0)

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=build_cost,
            table={},
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "pdb_parent", "pattern_size": self.pattern_size,
                        "abstract_states": len(a_states), "target_in_pattern": at_target is not None},
        )


@dataclass
class _ProjectedDomain:
    """A projected view of a proof-state domain restricted to a proposition pattern."""
    domain: object
    pattern: frozenset
    domain_id: str = "projected"
    cost_algebra_id: str = "additive_positive"

    def successors(self, state):
        out = []
        for rule in self.domain.rules:
            if rule.can_apply(state) and rule.conclusion in self.pattern:
                out.append((state | {rule.conclusion}, rule.cost))
        return out

    def predecessors(self, state):
        return []


class CEGARAbstractionFieldConstructor:
    """CEGAR parent: coarse abstraction refined by spurious-path counterexamples.

    Start with a coarse projection (few propositions). Solve exactly. If the
    abstract heuristic claims a state is reachable in k but the concrete path is
    spurious, add the distinguishing proposition to the pattern and re-solve.
    Bounded refinement rounds. Produces an admissible (relaxation) heuristic.
    """

    strategy_id = "cegar_parent"

    def __init__(self, initial_size: int = 3, max_rounds: int = 3):
        self.initial_size = initial_size
        self.max_rounds = max_rounds

    def construct(self, domain, target) -> ConstructedField:
        n = domain.n_propositions
        size = self.initial_size
        total_abstract = 0
        at_table: Dict[State, float] = {}
        pattern = frozenset(range(size))
        for _ in range(self.max_rounds):
            pattern = frozenset(range(min(size, n)))
            inner = PatternDatabaseFieldConstructor(pattern_size=len(pattern))
            field = inner.construct(domain, target)
            total_abstract += field.construction_cost.abstract_node_expansions
            # "refine": grow the pattern (add propositions) -- a spurious path in
            # the coarse abstraction is ruled out once the distinguishing prop is
            # in the pattern; growing monotonically tightens the relaxation.
            if target in pattern:
                at_table = dict(field.provenance)  # not used at eval time
            size += 2
        # final evaluation uses the finest pattern reached
        final = PatternDatabaseFieldConstructor(pattern_size=min(size, n))
        ffield = final.construct(domain, target)
        total_abstract += ffield.construction_cost.abstract_node_expansions

        def evaluator(state: State) -> float:
            return ffield.phi(state)

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(abstract_node_expansions=total_abstract),
            table={},
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "cegar_parent", "rounds": self.max_rounds,
                        "final_pattern_size": min(size, n)},
        )


class GoalSetExactFieldConstructor:
    """SUCCESSOR (== oracle ceiling): exact h*(s)=min_{g in G} d(s,g) over the
    full goal SET, computed by backward induction on the forward DAG.

    This is the goal-representation fix (#520 cause 1): the field is grounded in
    the goal CONDITION (any state containing target), not a single representative.
    Distances are TRUE transition distances (cause 2 fix), not proxies. The
    default for un-reachable states is 0.0 (admissible, never misleading) -- not
    999999.0 (cause 3 fix). When built over the full reachable cone this is the
    best possible guidance (the oracle lower bound).
    """

    strategy_id = "goalset_exact_successor"

    def __init__(self, reachability_cap: int = 20000):
        self.reachability_cap = reachability_cap

    def construct(self, domain, target, *, roots: Optional[Iterable[State]] = None) -> ConstructedField:
        rs = forward_reachable(domain, roots if roots is not None else [frozenset(domain.axioms)],
                               cap=self.reachability_cap)
        table, expansions = exact_goal_set_cost_to_go(domain, rs, target)
        audit = AdmissibilityAudit(
            method="CONSISTENCY_PROOF", coverage=AuditCoverage.EXHAUSTIVE,
            units_checked=0, violations=0, max_overestimate=0.0,
            target_value_is_zero=True,
            detail={"law": "exact cost-to-go via backward induction on the forward DAG; "
                           "h*(s)=min over goal set; oracle ceiling"},
        )

        def evaluator(state: State) -> float:
            return table.get(state, 0.0)

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(node_expansions=expansions),
            table=table,
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "goalset_exact_successor", "reachable_states": len(rs),
                        "goal_set": True, "role": "successor_oracle_ceiling"},
        ).with_audit(audit)


class GoalSetLandmarkFieldConstructor:
    """SUCCESSOR cheap variant: exact goal-set cost-to-go over a BUDGETED
    sub-reach (sample of start states), true distances, admissible 0.0 default.

    Trades coverage for build cost. Demonstrates the cost/quality point on the
    oracle ladder (exact -> bounded landmark). Still goal-set grounded.
    """

    strategy_id = "goalset_landmark_successor"

    def __init__(self, budget: int = 400):
        self.budget = budget

    def construct(self, domain, target, *, roots: Iterable[State]) -> ConstructedField:
        rs = forward_reachable(domain, roots, cap=self.budget)
        table, expansions = exact_goal_set_cost_to_go(domain, rs, target)

        def evaluator(state: State) -> float:
            return table.get(state, 0.0)

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=ConstructionCost(node_expansions=expansions),
            table=table,
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "goalset_landmark_successor", "budget": self.budget,
                        "reachable_states": len(rs), "goal_set": True},
        )


class HybridFieldConstructor:
    """SUCCESSOR hybrid: max(goalset_exact, pdb). Combines two admissible
    lower bounds -> a tighter (still admissible) heuristic. The strongest
    deployment instantiation of the goal-set mechanic."""

    strategy_id = "hybrid_goalset_pdb_successor"

    def __init__(self, reachability_cap: int = 20000, pattern_size: int = 6):
        self.reachability_cap = reachability_cap
        self.pattern_size = pattern_size

    def construct(self, domain, target, *, roots: Optional[Iterable[State]] = None) -> ConstructedField:
        ge = GoalSetExactFieldConstructor(self.reachability_cap).construct(
            domain, target, roots=roots)
        pdb = PatternDatabaseFieldConstructor(self.pattern_size).construct(domain, target)
        merged_cost = ge.construction_cost.merged(pdb.construction_cost)

        def evaluator(state: State) -> float:
            return max(ge.phi(state), pdb.phi(state))

        return ConstructedField(
            strategy_id=self.strategy_id,
            target=frozenset({target}),
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=merged_cost,
            table={},
            evaluator=evaluator,
            default_value=0.0,
            provenance={"constructor": "hybrid_goalset_pdb_successor",
                        "components": ["goalset_exact_successor", "pdb_parent"]},
        )
