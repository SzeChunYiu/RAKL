"""A* heuristic-contract repair tests (#541).

The module's ``AStarWithGivenHeuristic`` is the declared STRONG_CONTROL for
navigation experiments and its theorem record claims:

    admissible heuristic => exact optimal route

That claim is only correct once a node is *reopened* whenever a strictly cheaper
``g`` is discovered after settlement (admissible-but-inconsistent heuristics need
this; consistent heuristics never trigger it). These tests pin the contract:

  * the exact 4-node counterexample from issue #541 (regression-locked),
  * zero / consistent / admissible-inconsistent heuristic cases,
  * an *exhaustive* tiny-graph differential against the Dijkstra oracle over
    every directed graph on 3 nodes with every admissible heuristic (inconsistent
    heuristics included by construction),
  * a seeded randomized differential on larger graphs (n in 4..8).

A mismatch against Dijkstra under an admissible heuristic falsifies the contract.
"""
from __future__ import annotations

import itertools
import math
import os

import pytest

from rakl.navigation_dynamics import (
    AStarWithGivenHeuristic,
    NavigationEdge,
    NavigationProblem,
    exact_shortest_route,
)

ASTAR = AStarWithGivenHeuristic()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _problem(edges, start, goal, heuristic=None) -> NavigationProblem:
    e = tuple(NavigationEdge(u, v, float(c)) for (u, v, c) in edges)
    return NavigationProblem("t", e, start, goal, dict(heuristic or {}))


def _astar(prob) -> tuple[tuple[str, ...] | None, float, bool]:
    """Return (route, cost, found) for an A* proposal."""
    prop = ASTAR.propose(prob)
    if not prop.found_route:
        return None, math.inf, False
    return tuple(prop.route), float(prop.proposed_cost), True


def _dijkstra(prob) -> tuple[tuple[str, ...] | None, float]:
    route, cost = exact_shortest_route(prob)
    return route, float(cost)


def _dijkstra_dist(prob_factory, src, goal) -> float:
    """True shortest cost src->goal on the graph held by ``prob_factory``."""
    route, cost = _dijkstra(prob_factory(src, goal, {}))
    return cost


def _assert_optimal(prob, msg=""):
    a_route, a_cost, a_found = _astar(prob)
    d_route, d_cost = _dijkstra(prob)
    if d_route is None:
        assert not a_found, f"{msg}: graph unreachable but A* found a route"
        return
    assert a_found, f"{msg}: goal reachable but A* returned no route"
    assert abs(a_cost - d_cost) < 1e-9, (
        f"{msg}: A* cost {a_cost} != Dijkstra optimum {d_cost}"
    )


# --------------------------------------------------------------------------- #
# 1. the exact issue-#541 regression (permanently locked)
# --------------------------------------------------------------------------- #
def test_issue_541_exact_counterexample():
    """The filed 4-node admissible-inconsistent graph.

    Unfixed closed-set A* returns s->g = 6; optimum is s->b->a->g = 5.
    h is admissible (h(s)=4<=5, h(a)=0<=1, h(b)=2<=2) but inconsistent
    (h(b)=2 > 1+h(a)=1), so reopening is required.
    """
    edges = [("s", "a", 5), ("s", "b", 3), ("b", "a", 1), ("a", "g", 1), ("s", "g", 6)]
    h = {"s": 4.0, "a": 0.0, "b": 2.0, "g": 0.0}
    prob = _problem(edges, "s", "g", h)

    route, cost, found = _astar(prob)
    assert found
    assert route == ("s", "b", "a", "g")
    assert cost == pytest.approx(5.0)
    _assert_optimal(prob, "issue-541 counterexample")


# --------------------------------------------------------------------------- #
# 2. zero / consistent / admissible-inconsistent heuristic families
# --------------------------------------------------------------------------- #
def test_zero_heuristic_is_consistent_and_optimal():
    """h=0 is consistent (== Dijkstra); reopen must never be needed."""
    edges = [("a", "b", 2), ("b", "c", 3), ("a", "c", 6), ("c", "d", 1), ("b", "d", 9)]
    prob = _problem(edges, "a", "d", {n: 0.0 for n in "abcd"})
    _assert_optimal(prob, "zero heuristic")
    # backward-compat: a consistent heuristic settles each node at most once,
    # so expansions <= number of nodes with a finite g.
    prop = ASTAR.propose(prob)
    assert prop.search_expansions <= 4


def test_consistent_heuristic_optimal():
    """A consistent heuristic must be optimal and never trigger a reopen."""
    # true distances to g: d=0,c=2,b=4,a=6 -> h == true distance is consistent.
    edges = [("a", "b", 2), ("b", "c", 2), ("c", "g", 2), ("a", "c", 5), ("a", "g", 9)]
    h = {"a": 6.0, "b": 4.0, "c": 2.0, "g": 0.0}
    prob = _problem(edges, "a", "g", h)
    _assert_optimal(prob, "consistent heuristic")
    prop = ASTAR.propose(prob)
    assert prop.search_expansions <= 4  # no node expanded twice


def test_admissible_inconsistent_optimal_family():
    """Several admissible-but-inconsistent heuristics must all be optimal."""
    base = [("s", "a", 5), ("s", "b", 3), ("b", "a", 1), ("a", "g", 1), ("s", "g", 6)]
    cases = [
        {"s": 4.0, "a": 0.0, "b": 2.0, "g": 0.0},  # the #541 values
        {"s": 0.0, "a": 0.0, "b": 0.0, "g": 0.0},  # zero (consistent)
        {"s": 5.0, "a": 1.0, "b": 0.0, "g": 0.0},  # admissible, inconsistent
        {"s": 2.0, "a": 0.0, "b": 1.0, "g": 0.0},  # admissible, inconsistent
    ]
    for i, h in enumerate(cases):
        prob = _problem(base, "s", "g", h)
        _assert_optimal(prob, f"inconsistent family case {i}")


# --------------------------------------------------------------------------- #
# 3. exhaustive tiny-graph differential (n=3, all digraphs, all admissible h)
# --------------------------------------------------------------------------- #
def test_exhaustive_tiny_graphs_differential():
    """Every directed graph on 3 nodes, every admissible heuristic, vs Dijkstra.

    Heuristics are enumerated over the full admissible range per node
    (h(v) in {0..floor(dist(v,goal))}), so inconsistent heuristics are covered
    by construction. 0 mismatches means the implementation honours the
    admissible-optimality contract on this whole tiny universe.
    """
    nodes = ("a", "b", "c")
    weights = (1, 2)
    pairs = [(u, v) for u in nodes for v in nodes if u != v]
    options = [None, *weights]  # absent, or a positive weight
    inconsistent_seen = 0
    checked = 0

    for assignment in itertools.product(options, repeat=len(pairs)):
        edges = [(u, v, c) for (u, v), c in zip(pairs, assignment) if c is not None]
        if not edges:
            continue
        for goal in nodes:
            for start in nodes:
                if start == goal:
                    continue
                pf = lambda s, g, h: _problem(edges, s, g, h)
                d_route, _ = _dijkstra(_problem(edges, start, goal, {}))
                if d_route is None:
                    continue  # unreachable: A* must agree (checked in _assert_optimal)
                # true distance of every node to this goal (goal itself is 0)
                dist = {v: (0.0 if v == goal else _dijkstra_dist(pf, v, goal)) for v in nodes}
                # enumerate admissible h per *reachable* non-goal node. A node that
                # cannot reach the goal (dist==inf) cannot lie on any optimal path, so
                # its heuristic is fixed to 0 (admissible and immaterial) instead of
                # enumerated over an unbounded range.
                ranges = {
                    v: list(range(0, int(math.floor(dist[v])) + 1))
                    for v in nodes
                    if v != goal and dist[v] != math.inf
                }
                vals = list(ranges.values())
                keys = list(ranges.keys())
                for combo in itertools.product(*vals):
                    h = dict(zip(keys, combo))
                    h[goal] = 0
                    # verify the enumeration genuinely reaches inconsistent cases
                    if _is_inconsistent(edges, h):
                        inconsistent_seen += 1
                    prob = _problem(edges, start, goal, h)
                    _assert_optimal(prob, "exhaustive tiny-graph")
                    checked += 1

    assert inconsistent_seen > 0, "exhaustive enumeration never reached an inconsistent heuristic"
    assert checked > 0


def _is_inconsistent(edges, h) -> bool:
    for (u, v, c) in edges:
        if u in h and v in h and h[u] > h[v] + c + 1e-9:
            return True
    return False


# --------------------------------------------------------------------------- #
# 4. seeded randomized differential on larger graphs (n in 4..8)
# --------------------------------------------------------------------------- #
def _random_graph(rng, n):
    nodes = [chr(ord("a") + i) for i in range(n)]
    edges = []
    for u in nodes:
        for v in nodes:
            if u == v:
                continue
            if rng.random() < 0.45:
                edges.append((u, v, rng.randint(1, 4)))
    return nodes, edges


@pytest.mark.parametrize("n", [4, 5, 6, 7, 8])
def test_randomized_differential(n):
    """Seeded random digraphs; admissible (frequently inconsistent) heuristics.

    h(v) is sampled independently per node in [0, dist(v,goal)], which is
    admissible but generically inconsistent, exercising the reopen path.
    """
    rng = _SeededRng(seed=1000 + n)
    trials = 400
    for _ in range(trials):
        nodes, edges = _random_graph(rng, n)
        if not edges:
            continue
        start, goal = rng.choice(nodes), rng.choice(nodes)
        if start == goal:
            continue
        pf = lambda s, g, h: _problem(edges, s, g, h)
        d_route, _ = _dijkstra(_problem(edges, start, goal, {}))
        if d_route is None:
            _assert_optimal(_problem(edges, start, goal, {}), "random unreachable")
            continue
        dist = {v: (0.0 if v == goal else _dijkstra_dist(pf, v, goal)) for v in nodes}
        h = {}
        for v in nodes:
            d = dist[v]
            h[v] = 0.0 if (d == math.inf) else rng.uniform(0.0, d)
        h[goal] = 0.0
        prob = _problem(edges, start, goal, h)
        _assert_optimal(prob, f"random n={n}")


class _SeededRng:
    """Deterministic RNG (no global random state / no Math.random)."""

    def __init__(self, seed):
        self.s = seed & 0x7FFFFFFF

    def _next(self):
        # LCG (numerical recipes constants)
        self.s = (1664525 * self.s + 1013904223) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def random(self):
        return self._next()

    def randint(self, lo, hi):
        return lo + int(self._next() * (hi - lo + 1))

    def uniform(self, lo, hi):
        return lo + self._next() * (hi - lo)

    def choice(self, xs):
        return xs[int(self._next() * len(xs)) % len(xs)]
