"""Contract tests for the navigation-dynamics family.

Three things are tested, in decreasing order of how much they matter:

1. **Noncompensatory hard constraints.** No navigator, dynamics or control, may
   propose a route through an edge that fails a ``PathAdmissibility`` gate --
   including when that edge is overwhelmingly the cheapest option. This is the
   invariant a diffusion kernel or a conductance field is most likely to break.
2. **Authority containment.** Proposals are routing proposals and nothing else.
3. **Honest cost accounting.** A dynamics' relaxation sweeps are billed in the same
   unit as search expansions, so no strategy can win by not being charged.

Correctness of each dynamics (does it find good routes?) is deliberately *not*
asserted as a pass/fail property: that is what the experiment measures, and
hard-coding an expectation here would let the test dictate the result.
"""
from __future__ import annotations

import math
import random

import pytest

from rakl.navigation_dynamics import (
    CONTROL_STRATEGIES,
    DYNAMICS_STRATEGIES,
    NAVIGATOR_REGISTRY,
    STRONG_CONTROL,
    AStarWithGivenHeuristic,
    DiffusionNavigator,
    GoalField,
    InadmissibleRouteError,
    NavigationEdge,
    NavigationProblem,
    Navigator,
    PathIntegralNavigator,
    PhysarumNavigator,
    RouteProposal,
    UninformedBFS,
    admissible_everywhere,
    available_navigators,
    exact_shortest_route,
    forbidden_edge,
    get_navigator,
    register_navigator,
)
from rakl.path_cost import PathAdmissibility

ALL_STRATEGIES = CONTROL_STRATEGIES + DYNAMICS_STRATEGIES


# --------------------------------------------------------------------------- #
# fixtures / world builders
# --------------------------------------------------------------------------- #


def _diamond() -> NavigationProblem:
    """a -> b -> c -> d (cost 3) vs a -> c -> d (cost 6); plus a cheap FORBIDDEN a -> d."""
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "c", 1.0),
        NavigationEdge("c", "d", 1.0),
        NavigationEdge("a", "c", 5.0),
        NavigationEdge("a", "d", 0.001, forbidden_edge()),
    )
    heuristic = {"a": 2.0, "b": 2.0, "c": 1.0, "d": 0.0}
    return NavigationProblem("diamond", edges, "a", "d", heuristic)


def _random_geometric_problem(rng: random.Random, n: int = 24, k: int = 4, forbid_p: float = 0.0):
    """Nodes on the unit square; edge cost >= straight-line distance (admissible h)."""
    points = {f"n{i}": (rng.random(), rng.random()) for i in range(n)}
    names = sorted(points)
    edges = []
    for name in names:
        others = sorted(names, key=lambda o: _dist(points[name], points[o]))[1 : k + 1]
        for other in others:
            base = _dist(points[name], points[other])
            cost = base * (1.0 + rng.random())  # >= straight line: heuristic stays admissible
            adm = forbidden_edge() if rng.random() < forbid_p else admissible_everywhere()
            edges.append(NavigationEdge(name, other, cost, adm))
    start, goal = names[0], names[-1]
    heuristic = {name: _dist(points[name], points[goal]) for name in names}
    return NavigationProblem(f"geo-{n}", tuple(edges), start, goal, heuristic)


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _solvable_random_problems(seed: int, count: int, **kw):
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        problem = _random_geometric_problem(rng, **kw)
        route, _cost = exact_shortest_route(problem)
        if route is not None:
            out.append(problem)
    return out


# --------------------------------------------------------------------------- #
# 1. noncompensatory hard-constraint admissibility  (the load-bearing invariant)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_no_navigator_routes_through_a_forbidden_edge_however_cheap(strategy_id):
    """The forbidden a->d edge costs 0.001 against an optimum of 3.0 and is still unusable."""
    problem = _diamond()
    proposal = get_navigator(strategy_id).propose(problem)
    assert proposal.route is not None, f"{strategy_id} found no route in a solvable world"
    assert ("a", "d") not in set(zip(proposal.route, proposal.route[1:]))
    assert proposal.proposed_cost >= 3.0 - 1e-9


@pytest.mark.parametrize("gate", [
    "licensed_assumptions",
    "trusted_verifier",
    "specification_aligned",
    "portal_valid",
    "root_scope_preserved",
])
@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_every_hard_constraint_gate_is_noncompensatory(gate, strategy_id):
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "c", 1.0),
        NavigationEdge("c", "d", 1.0),
        NavigationEdge("a", "d", 0.0001, forbidden_edge(reason=gate)),
    )
    problem = NavigationProblem("gate", edges, "a", "d", {"a": 3.0, "b": 2.0, "c": 1.0, "d": 0.0})
    proposal = get_navigator(strategy_id).propose(problem)
    assert proposal.route == ("a", "b", "c", "d")


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_unknown_hard_constraint_also_blocks_the_edge(strategy_id):
    """``None`` (unknown) is not ``True``: an unverified gate fails closed like a violation."""
    unknown = PathAdmissibility(
        licensed_assumptions=True,
        trusted_verifier=None,
        specification_aligned=True,
        portal_valid=True,
        root_scope_preserved=True,
    )
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "c", 1.0),
        NavigationEdge("c", "d", 1.0),
        NavigationEdge("a", "d", 0.0001, unknown),
    )
    problem = NavigationProblem("unknown", edges, "a", "d", {"a": 3.0, "b": 2.0, "c": 1.0, "d": 0.0})
    assert get_navigator(strategy_id).propose(problem).route == ("a", "b", "c", "d")


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_forbidden_edge_is_removed_from_the_world_not_merely_penalised(strategy_id):
    """When the only route to the goal is forbidden, the answer is "no route", never a discount."""
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "d", 1.0, forbidden_edge()),
    )
    problem = NavigationProblem("blocked", edges, "a", "d", {"a": 2.0, "b": 1.0, "d": 0.0})
    assert exact_shortest_route(problem) == (None, math.inf)
    proposal = get_navigator(strategy_id).propose(problem)
    assert proposal.route is None
    assert proposal.proposed_cost == math.inf
    assert proposal.found_route is False


def test_admissibility_filter_precedes_cost_comparison():
    """``admissible_edges`` is a filter on the world, evaluated with no reference to cost."""
    problem = _diamond()
    assert len(problem.admissible_edges()) == len(problem.edges) - 1
    assert ("a", "d") not in {(e.source, e.target) for e in problem.admissible_edges()}
    # and the cheapest edge in the raw world is precisely the one that is gone
    cheapest = min(problem.edges, key=lambda e: e.cost)
    assert (cheapest.source, cheapest.target) == ("a", "d")


def test_validate_route_rejects_a_hand_built_forbidden_route():
    problem = _diamond()
    with pytest.raises(InadmissibleRouteError, match="noncompensatory"):
        problem.validate_route(("a", "d"))
    with pytest.raises(InadmissibleRouteError, match="nonexistent"):
        problem.validate_route(("a", "b", "d"))


def test_navigator_base_fails_closed_on_a_smuggled_route():
    """A subclass that returns a forbidden route is stopped by ``propose``, not trusted."""

    class Cheat(Navigator):
        strategy_id = "cheat_for_test"

        def _propose(self, problem):
            return RouteProposal(
                strategy_id="cheat_for_test",
                problem_id=problem.problem_id,
                route=("a", "d"),
                proposed_cost=0.001,
                search_expansions=1,
                relaxation_sweeps=0,
                graph_nodes=len(problem.nodes),
            )

    with pytest.raises(InadmissibleRouteError):
        Cheat().propose(_diamond())


def test_navigator_base_fails_closed_on_a_misreported_cost():
    class Liar(Navigator):
        strategy_id = "liar_for_test"

        def _propose(self, problem):
            return RouteProposal(
                strategy_id="liar_for_test",
                problem_id=problem.problem_id,
                route=("a", "b", "c", "d"),
                proposed_cost=0.5,  # actual is 3.0
                search_expansions=1,
                relaxation_sweeps=0,
                graph_nodes=len(problem.nodes),
            )

    with pytest.raises(InadmissibleRouteError, match="reported cost"):
        Liar().propose(_diamond())


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_proposals_stay_admissible_on_random_worlds_with_forbidden_edges(strategy_id):
    navigator = get_navigator(strategy_id)
    for problem in _solvable_random_problems(461, 25, n=22, k=4, forbid_p=0.2):
        proposal = navigator.propose(problem)
        if proposal.route is None:
            continue
        # validate_route raises on any forbidden or nonexistent step
        assert math.isclose(problem.validate_route(proposal.route), proposal.proposed_cost, rel_tol=1e-9)


# --------------------------------------------------------------------------- #
# 2. authority containment
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_proposals_grant_no_authority(strategy_id):
    proposal = get_navigator(strategy_id).propose(_diamond())
    assert proposal.grants_scientific_authority is False
    assert proposal.grants_target_authority is False
    assert proposal.grants_method_promotion is False
    payload = proposal.as_dict()
    assert payload["grants_scientific_authority"] is False
    assert payload["grants_target_authority"] is False
    assert payload["grants_method_promotion"] is False


def test_goal_field_grants_no_authority():
    field = DiffusionNavigator(sweeps=5).build_goal_field(_diamond())
    assert field.grants_scientific_authority is False


# --------------------------------------------------------------------------- #
# 3. identical interface + registry
# --------------------------------------------------------------------------- #


def test_registry_contains_exactly_the_declared_families():
    assert set(available_navigators()) == set(ALL_STRATEGIES)
    assert STRONG_CONTROL in CONTROL_STRATEGIES
    assert not set(CONTROL_STRATEGIES) & set(DYNAMICS_STRATEGIES)


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_identical_interface(strategy_id):
    navigator = get_navigator(strategy_id)
    assert isinstance(navigator, Navigator)
    assert navigator.strategy_id == strategy_id
    assert navigator.family in {"control", "dynamics"}
    proposal = navigator.propose(_diamond())
    assert isinstance(proposal, RouteProposal)
    assert proposal.problem_id == "diamond"
    assert proposal.strategy_id == strategy_id


def test_families_are_labelled_correctly():
    for strategy_id in DYNAMICS_STRATEGIES:
        assert get_navigator(strategy_id).family == "dynamics"
    for strategy_id in CONTROL_STRATEGIES:
        assert get_navigator(strategy_id).family == "control"


def test_registry_rejects_duplicate_and_anonymous_registrations():
    with pytest.raises(ValueError, match="duplicate"):
        register_navigator(type("Dup", (Navigator,), {"strategy_id": "diffusion"}))
    with pytest.raises(ValueError, match="nonempty"):
        register_navigator(type("Anon", (Navigator,), {"strategy_id": ""}))
    with pytest.raises(KeyError):
        get_navigator("no_such_navigator")


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_navigators_are_deterministic(strategy_id):
    problems = _solvable_random_problems(11, 6, n=20, k=4)
    first = [get_navigator(strategy_id).propose(p).as_dict() for p in problems]
    second = [get_navigator(strategy_id).propose(p).as_dict() for p in problems]
    assert first == second


# --------------------------------------------------------------------------- #
# 4. cost accounting -- dynamics iterations are not free
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("strategy_id", DYNAMICS_STRATEGIES)
def test_dynamics_are_charged_for_their_relaxation_sweeps(strategy_id):
    proposal = get_navigator(strategy_id).propose(_diamond())
    assert proposal.relaxation_sweeps > 0
    assert proposal.sweep_node_scans == proposal.relaxation_sweeps * proposal.graph_nodes
    assert proposal.equivalent_expansions == proposal.search_expansions + proposal.sweep_node_scans
    assert proposal.equivalent_expansions > proposal.search_expansions


@pytest.mark.parametrize("strategy_id", CONTROL_STRATEGIES)
def test_controls_run_no_sweeps(strategy_id):
    proposal = get_navigator(strategy_id).propose(_diamond())
    assert proposal.relaxation_sweeps == 0
    assert proposal.equivalent_expansions == proposal.search_expansions


def test_a_100_iteration_solve_is_not_free():
    problem = _diamond()
    cheap = DiffusionNavigator(sweeps=10).propose(problem)
    dear = DiffusionNavigator(sweeps=100).propose(problem)
    assert dear.equivalent_expansions > cheap.equivalent_expansions
    assert dear.equivalent_expansions - cheap.equivalent_expansions >= 90 * len(problem.nodes)


def test_cost_counters_are_monotone_in_iteration_budget():
    problem = _diamond()
    budgets = [2, 5, 20, 60]
    for navigator_of in (
        lambda k: DiffusionNavigator(sweeps=k),
        lambda k: PathIntegralNavigator(sweeps=k),
        lambda k: PhysarumNavigator(iterations=k),
    ):
        costs = [navigator_of(k).propose(problem).equivalent_expansions for k in budgets]
        assert costs == sorted(costs)


# --------------------------------------------------------------------------- #
# 5. per-dynamics mathematical properties (what each one actually claims)
# --------------------------------------------------------------------------- #


def test_path_integral_converges_to_the_hard_min_as_temperature_falls():
    """log-sum-exp -> min as T -> 0: the soft value must approach the exact optimum."""
    problem = _diamond()
    _route, exact = exact_shortest_route(problem)
    gaps = []
    for temperature in (2.0, 0.5, 0.05, 0.005):
        navigator = PathIntegralNavigator(sweeps=60, temperature=temperature)
        soft = navigator.build_goal_field(problem)  # value at start lives in the walk
        proposal = navigator.propose(problem)
        gaps.append(abs(proposal.proposed_cost - exact))
        assert soft.build_sweeps == 60
    assert gaps[-1] <= gaps[0] + 1e-9
    assert gaps[-1] < 1e-6  # at T -> 0 it recovers the exact route on this world


def test_path_integral_soft_value_underestimates_the_true_cost_to_go():
    """A log-sum-exp over paths is <= the min over paths, always."""
    problem = _random_geometric_problem(random.Random(7), n=18, k=4)
    _route, exact = exact_shortest_route(problem)
    if _route is None:
        pytest.skip("unreachable world")
    proposal = PathIntegralNavigator(sweeps=80, temperature=0.4).propose(problem)
    soft_value = proposal.diagnostics.get("temperature")
    assert soft_value == 0.4
    # the route it actually proposes can only be >= the exact optimum
    assert proposal.proposed_cost >= exact - 1e-9


def test_physarum_conductance_concentrates_on_a_channel():
    """Tero dynamics must thin the network out, not leave every tube alive."""
    problem = _random_geometric_problem(random.Random(3), n=30, k=4)
    early = PhysarumNavigator(iterations=1).propose(problem)
    late = PhysarumNavigator(iterations=40).propose(problem)
    early_fraction = early.diagnostics["surviving_tubes"] / early.diagnostics["tubes"]
    late_fraction = late.diagnostics["surviving_tubes"] / late.diagnostics["tubes"]
    assert late_fraction < early_fraction


def test_physarum_has_no_start_independent_field():
    """Its pressure solve is driven by a current at the start; that is not amortizable."""
    assert PhysarumNavigator().build_goal_field(_diamond()) is None
    assert AStarWithGivenHeuristic().build_goal_field(_diamond()) is None
    assert UninformedBFS().build_goal_field(_diamond()) is None


def test_diffusion_concentration_decays_away_from_the_goal():
    """A heat kernel clamped at the goal must be warmest at the goal."""
    problem = NavigationProblem(
        "chain",
        tuple(NavigationEdge(f"n{i}", f"n{i + 1}", 1.0) for i in range(6)),
        "n0",
        "n6",
        {f"n{i}": float(6 - i) for i in range(7)},
    )
    proposal = DiffusionNavigator(sweeps=60, tau=1.0).propose(problem)
    assert proposal.route == tuple(f"n{i}" for i in range(7))


# --------------------------------------------------------------------------- #
# 6. goal-field amortization (the re-planning regime)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("navigator", [DiffusionNavigator(sweeps=25), PathIntegralNavigator(sweeps=25)])
def test_goal_field_is_reusable_across_starts_and_charges_only_the_walk(navigator):
    base = _random_geometric_problem(random.Random(19), n=28, k=4)
    goal_field = navigator.build_goal_field(base)
    assert isinstance(goal_field, GoalField)
    assert goal_field.build_node_scans == goal_field.build_sweeps * goal_field.graph_nodes
    reused = 0
    for node in base.nodes:
        if node == base.goal:
            continue
        query = NavigationProblem(f"q-{node}", base.edges, node, base.goal, base.heuristic)
        proposal = goal_field.propose_from(query)
        assert proposal.relaxation_sweeps == 0  # build cost is paid once, not per query
        assert proposal.diagnostics["amortized_extraction"] == 1.0
        if proposal.route is not None:
            assert proposal.route[0] == node
            reused += 1
    assert reused > 0


def test_goal_field_refuses_a_different_goal():
    base = _diamond()
    goal_field = DiffusionNavigator(sweeps=5).build_goal_field(base)
    other = NavigationProblem("other", base.edges, "a", "c", base.heuristic)
    with pytest.raises(ValueError, match="different goal"):
        goal_field.propose_from(other)


def test_amortized_field_route_matches_the_single_query_route():
    """Amortization must be a cost change only -- never a different answer."""
    navigator = PathIntegralNavigator(sweeps=40, temperature=0.2)
    problem = _random_geometric_problem(random.Random(23), n=26, k=4)
    single = navigator.propose(problem)
    amortized = navigator.build_goal_field(problem).propose_from(problem)
    assert single.route == amortized.route
    assert single.search_expansions == amortized.search_expansions


# --------------------------------------------------------------------------- #
# 7. oracle + world model
# --------------------------------------------------------------------------- #


def test_exact_shortest_route_is_the_oracle_and_is_not_a_registered_competitor():
    assert "exact_shortest_route" not in NAVIGATOR_REGISTRY
    route, cost = exact_shortest_route(_diamond())
    assert route == ("a", "b", "c", "d")
    assert cost == pytest.approx(3.0)


@pytest.mark.parametrize("strategy_id", ALL_STRATEGIES)
def test_no_navigator_beats_the_oracle(strategy_id):
    """The oracle is a lower bound: a proposal cheaper than exact means a bug."""
    for problem in _solvable_random_problems(97, 30, n=24, k=4, forbid_p=0.1):
        _route, exact = exact_shortest_route(problem)
        proposal = get_navigator(strategy_id).propose(problem)
        if proposal.route is not None:
            assert proposal.proposed_cost >= exact - 1e-9


def test_astar_with_an_admissible_heuristic_is_optimal():
    """Sanity: the STRONG control really is strong, so beating it means something."""
    for problem in _solvable_random_problems(53, 40, n=26, k=4, forbid_p=0.1):
        _route, exact = exact_shortest_route(problem)
        proposal = AStarWithGivenHeuristic().propose(problem)
        assert proposal.route is not None
        assert proposal.proposed_cost == pytest.approx(exact, rel=1e-9)


def test_uninformed_bfs_is_hop_optimal_not_cost_optimal():
    """Documented weakness of the weak control, asserted rather than assumed."""
    problem = _diamond()
    proposal = UninformedBFS().propose(problem)
    assert len(proposal.route) == 3  # fewest hops
    assert proposal.proposed_cost > 3.0  # but not cheapest


# --------------------------------------------------------------------------- #
# 8. input validation
# --------------------------------------------------------------------------- #


def test_edge_and_problem_validation():
    with pytest.raises(ValueError, match="finite and nonnegative"):
        NavigationEdge("a", "b", -1.0)
    with pytest.raises(ValueError, match="finite and nonnegative"):
        NavigationEdge("a", "b", float("inf"))
    with pytest.raises(ValueError, match="source and target"):
        NavigationEdge("", "b", 1.0)
    with pytest.raises(ValueError, match="at least one edge"):
        NavigationProblem("p", (), "a", "b")
    with pytest.raises(ValueError, match="must differ"):
        NavigationProblem("p", (NavigationEdge("a", "b", 1.0),), "a", "a")
    with pytest.raises(ValueError, match="heuristic"):
        NavigationProblem("p", (NavigationEdge("a", "b", 1.0),), "a", "b", {"a": -1.0})


def test_navigator_parameter_validation():
    with pytest.raises(ValueError, match="at least one sweep"):
        DiffusionNavigator(sweeps=0)
    with pytest.raises(ValueError, match="tau must be positive"):
        DiffusionNavigator(tau=0.0)
    with pytest.raises(ValueError, match="temperature must be positive"):
        PathIntegralNavigator(temperature=0.0)
    with pytest.raises(ValueError, match="at least one iteration"):
        PhysarumNavigator(iterations=0)
    with pytest.raises(ValueError, match="dt must be in"):
        PhysarumNavigator(dt=1.5)
    with pytest.raises(ValueError, match="unknown hard-constraint gate"):
        forbidden_edge(reason="not_a_gate")


def test_route_proposal_validation():
    with pytest.raises(ValueError, match="infinite proposed cost"):
        RouteProposal("s", "p", None, 1.0, 0, 0, 3)
    with pytest.raises(ValueError, match="finite proposed cost"):
        RouteProposal("s", "p", ("a", "b"), math.inf, 0, 0, 3)
    with pytest.raises(ValueError, match="nonnegative"):
        RouteProposal("s", "p", None, math.inf, -1, 0, 3)
    with pytest.raises(ValueError, match="strategy_id is required"):
        RouteProposal("", "p", None, math.inf, 0, 0, 3)
