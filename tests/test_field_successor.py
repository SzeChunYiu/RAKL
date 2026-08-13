"""#538: field-construction successor library + promotion-gate wiring tests.

Covers the three root-cause fixes and the honesty guard:
  * exact_goal_set_cost_to_go is the admissible oracle (goal=0, monotone along
    every successor edge, lower bound) -- fixes cause 2 (true transition distances)
    and cause 1 (goal CONDITION ``target in s``, not a single representative).
  * greedy_best_first_search: phi=None (BFS) and the exact field both find a
    reachable goal; the exact field never expands more than BFS on a clean chain.
  * PatternDatabaseFieldConstructor target_aware=True keeps the goal variable in
    the pattern (the FAIR strong parent); target_aware=False omits it (strawman).
  * GoalSetExactFieldConstructor yields an admissible field (phi <= true h*) that
    equals the oracle over the full cone, with a finite nonnegative default
    (cause 3 fix: not 999999.0).
  * the field_construction_successor gate candidate is wired to the live artifact
    and the LIVE verdict is honestly KEEP_PROPOSAL_ONLY with COMPLETE telemetry --
    a guard against ever tuning a dominated mechanic positive.
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rakl.field_successor import (  # noqa: E402
    forward_reachable, exact_goal_set_cost_to_go, greedy_best_first_search,
    GoalSetExactFieldConstructor, PatternDatabaseFieldConstructor,
)
from promotion_gate import verdict_for, CANDIDATES  # noqa: E402

Proposition = int
State = FrozenSet[Proposition]


@dataclass(frozen=True)
class _Rule:
    premises: Tuple[Proposition, ...]
    conclusion: Proposition
    cost: float = 1.0

    def can_apply(self, s: State) -> bool:
        return all(p in s for p in self.premises)

    def apply(self, s: State) -> State:
        return s | {self.conclusion}


class _TinyChainDomain:
    """Monotone add-only proof domain: chain 0->1->2 (target=2) + distractor 0->3."""
    domain_id = "tiny_chain_test"
    cost_algebra_id = "additive_positive"
    n_propositions = 4
    axioms = frozenset({0})
    rules = [_Rule((0,), 1), _Rule((1,), 2), _Rule((0,), 3)]

    def successors(self, state: State):
        return [(r.apply(state), r.cost) for r in self.rules if r.can_apply(state)]

    def predecessors(self, state: State):
        out = []
        for r in self.rules:
            if r.conclusion in state:
                ps = state - {r.conclusion}
                if all(p in ps for p in r.premises):
                    out.append((ps, r.cost))
        return out

    def all_goal_states(self, target: Proposition):
        return [s for s in forward_reachable(self, [self.axioms]) if target in s]


@pytest.fixture
def chain():
    return _TinyChainDomain()


# --------------------------------------------------------------------------- #
# exact goal-set cost-to-go: the admissible oracle
# --------------------------------------------------------------------------- #
def test_exact_cost_to_go_goal_zero_and_chain_distances(chain):
    target = 2
    cone = forward_reachable(chain, [chain.axioms])
    h, _ = exact_goal_set_cost_to_go(chain, cone, target)
    assert h[frozenset({0, 1, 2})] == 0.0      # goal condition: target in state
    assert h[frozenset({0, 1})] == 1.0         # one chain step to goal
    assert h[frozenset({0})] == 2.0            # two chain steps to goal


def test_exact_cost_to_go_admissible_and_monotone(chain):
    target = 2
    cone = forward_reachable(chain, [chain.axioms])
    h, _ = exact_goal_set_cost_to_go(chain, cone, target)
    # admissible + monotone: h(s) <= c + h(s') along every successor edge
    for s in cone:
        for s2, c in chain.successors(s):
            if s2 in h:
                assert h[s] <= c + h[s2] + 1e-9


def test_exact_cost_to_go_all_finite_nonnegative(chain):
    target = 3
    cone = forward_reachable(chain, [chain.axioms])
    h, _ = exact_goal_set_cost_to_go(chain, cone, target)
    # contract requires finite nonnegative values (dead ends cap, not inf)
    assert all(v >= 0.0 and v != float("inf") for v in h.values())


# --------------------------------------------------------------------------- #
# greedy best-first search
# --------------------------------------------------------------------------- #
def test_bfs_and_exact_field_both_find_reachable_goal(chain):
    target = 2
    start = frozenset({0})
    bfs = greedy_best_first_search(chain, None, start, target, 1000)
    assert bfs["found"] is True
    field = GoalSetExactFieldConstructor().construct(chain, target)
    guided = greedy_best_first_search(chain, field.phi, start, target, 1000)
    assert guided["found"] is True
    # the exact oracle climbs the chain directly: never more expansions than BFS
    assert guided["expanded"] <= bfs["expanded"]


def test_unreachable_target_not_found(chain):
    start = frozenset({0, 1, 2, 3})  # saturated; target 5 absent from the universe
    res = greedy_best_first_search(chain, None, start, 5, 50)
    assert res["found"] is False


# --------------------------------------------------------------------------- #
# pattern database: target-aware fairness (the strong parent)
# --------------------------------------------------------------------------- #
def test_pdb_target_aware_includes_goal_variable(chain):
    field = PatternDatabaseFieldConstructor(pattern_size=2, target_aware=True).construct(chain, 2)
    assert field.provenance["target_in_pattern"] is True
    assert field.phi(frozenset({0})) >= 0.0


def test_pdb_target_aware_false_omits_goal_when_pattern_small(chain):
    # pattern = first 2 propositions {0,1}; goal variable 2 is omitted -> no info
    field = PatternDatabaseFieldConstructor(pattern_size=2, target_aware=False).construct(chain, 2)
    assert field.provenance["target_in_pattern"] is False


# --------------------------------------------------------------------------- #
# goal-set exact field admissibility (the successor oracle ceiling)
# --------------------------------------------------------------------------- #
def test_goalset_exact_field_is_the_admissible_oracle(chain):
    target = 2
    cone = forward_reachable(chain, [chain.axioms])
    truth, _ = exact_goal_set_cost_to_go(chain, cone, target)
    field = GoalSetExactFieldConstructor().construct(chain, target)
    # admissible: phi(s) <= true h*(s); over the full cone the exact field IS the oracle
    for s in cone:
        assert field.phi(s) <= truth[s] + 1e-9
        assert abs(field.phi(s) - truth[s]) < 1e-9
    assert field.construction_cost.total_node_equivalents() >= 0


# --------------------------------------------------------------------------- #
# promotion-gate wiring + LIVE honesty guard
# --------------------------------------------------------------------------- #
RESULT = ROOT / "research/unified_problem_solving_v1/results/field_construction_successor.json"


def test_gate_candidate_registered_and_wired():
    assert "field_construction_successor" in CANDIDATES
    spec = CANDIDATES["field_construction_successor"]
    assert "net_advantage_over_strongest_parent" in spec["net_keys"]
    assert spec["artifact"].name == "field_construction_successor.json"
    assert spec["claim_class"] == "EFFICIENCY"
    assert spec["cost_fields"] == ["construction_cost"]


def test_live_artifact_is_honest_keep_proposal_only():
    """The successor is a CORRECT oracle (rho~1.0, correctness gate passes) but is
    dominated by cheaper parents. The live head-to-head CI must lie entirely below
    zero and the verdict MUST be KEEP_PROPOSAL_ONLY -- the guard against tuning a
    dominated mechanic positive."""
    art = json.loads(RESULT.read_text())
    assert art["grants_scientific_authority"] is False
    assert art["correctness_hard_gate_passed"] is True
    hh = art["net_advantage_over_strongest_parent"]
    assert hh["hi"] < 0.0, hh                       # statistically dominated
    assert hh["mean"] < 0.0, hh
    v = verdict_for("field_construction_successor", CANDIDATES["field_construction_successor"])
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["telemetry"]["status"] == "COMPLETE", v
    assert "blocked_promotion" not in v


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
