#!/usr/bin/env python3
"""Field construction net-cost experiment on a symbolic non-metric domain.

Operational definition of the "field" (Φ:X→ℝ): a SCALAR POTENTIAL over a symbolic
problem space that ranks best-first expansions. It is charged at construction +
sweep + invalidation cost. It is explicitly NOT an algebraic norm/trace/étale-descent.

Domain: Proof-state graph
  * States: frozensets of proven propositions (symbolic, non-metric)
  * Operators: inference rules that derive new propositions from existing ones
  * Goal: reach a target theorem
  * This is truly symbolic — no coordinates, no vector space, no metric structure

Field construction: Landmark-based ALT-style heuristic
  * Sample a bounded training subgraph via random walk from the goal
  * Compute exact cost-to-go on this subgraph (these are landmarks)
  * Field value = min over landmarks of (cost to landmark + cost from landmark to goal)
  * Construction cost = every node expansion during sampling + BFS cost computation

Comparison (matched task budget):
  * FIELD arm: best-first search guided by Φ, with construction cost charged
  * BASELINE arm: plain BFS with NO constructed field

Net metric = (search ops saved by field guidance) − (field construction cost)

Honesty invariants:
  * grants_scientific_authority = False (development/known-world only)
  * Bootstrap 95% CI over ≥100 task replicates
  * A NEGATIVE net is an EXPECTED, honest result — do NOT manufacture a positive
"""
from __future__ import annotations

import argparse
import heapq
import json
import random
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import FrozenSet, Sequence, List, Tuple, Dict

# Import rakl modules
import sys
sys.path.insert(0, 'src')
from rakl.field_construction import (
    ConstructionCost,
    ConstructedField,
    ConstructionDomain,
    AuditCoverage,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "field_construction.json"


# ---------------------------------------------------------------------------
# Symbolic proof-state domain
# ---------------------------------------------------------------------------

Proposition = int
State = FrozenSet[Proposition]

@dataclass(frozen=True)
class InferenceRule:
    """An inference rule: derives conclusion from premises."""
    rule_id: str
    premises: Tuple[Proposition, ...]
    conclusion: Proposition
    cost: float = 1.0

    def can_apply(self, state: State) -> bool:
        return all(p in state for p in self.premises)

    def apply(self, state: State) -> State:
        if not self.can_apply(state):
            raise ValueError(f"Rule {self.rule_id} cannot apply to state {state}")
        return state | {self.conclusion}


class ProofStateDomain:
    """A symbolic proof-state graph implementing ConstructionDomain protocol.

    States are sets of proven propositions. Operators are inference rules.
    This is NON-METRIC — there's no coordinate space, no distance, just symbolic structure.
    """

    def __init__(
        self,
        n_propositions: int,
        n_rules: int,
        seed: int = 42,
    ):
        self.domain_id = "proof_state_v1"
        self.cost_algebra_id = "additive_positive"
        self.rng = random.Random(seed)
        self.n_propositions = n_propositions

        # Generate random inference rules
        self.rules = []
        for i in range(n_rules):
            n_premises = self.rng.randint(1, 3)
            max_premise = max(1, n_propositions // 2)
            premises = tuple(self.rng.sample(range(max_premise), n_premises))
            conclusion = self.rng.randint(n_propositions // 2, n_propositions - 1)
            self.rules.append(InferenceRule(
                rule_id=f"rule_{i}",
                premises=premises,
                conclusion=conclusion,
                cost=1.0,
            ))

        # Axioms (base propositions that are initially true)
        self.axioms = frozenset(range(n_propositions // 3))

    @lru_cache(maxsize=10000)
    def successors(self, state: State) -> List[Tuple[State, float]]:
        """Return all successor states + their costs."""
        succ = []
        for rule in self.rules:
            if rule.can_apply(state):
                new_state = rule.apply(state)
                succ.append((new_state, rule.cost))
        return succ

    @lru_cache(maxsize=10000)
    def predecessors(self, state: State) -> List[Tuple[State, float]]:
        """Return all predecessor states + their costs (reverse inference)."""
        pred = []
        for rule in self.rules:
            if rule.conclusion in state:
                pred_state = state - {rule.conclusion}
                if all(p in pred_state for p in rule.premises):
                    pred.append((pred_state, rule.cost))
        return pred

    def feature_names(self) -> Sequence[str]:
        return ["n_proven", "min_distance_to_target", "max_unchained_premise"]
    
    def features(self, state: State, target: Proposition) -> List[float]:
        """Cheap structural features for regression-based construction."""
        n_proven = len(state)
        remaining = self.n_propositions - len(state)
        return [float(n_proven), float(remaining), float(remaining)]

    def abstractions(self) -> Sequence:
        """No abstractions implemented for this domain."""
        return []

    def is_goal(self, state: State, target: Proposition) -> bool:
        return target in state

    def random_state(self, min_size: int = 1) -> State:
        """Generate a random state (for training subgraph sampling)."""
        size = self.rng.randint(min_size, self.n_propositions // 2)
        return frozenset(self.rng.sample(range(self.n_propositions), size))


# ---------------------------------------------------------------------------
# Landmark-based field constructor
# ---------------------------------------------------------------------------

@dataclass
class LandmarkConstructor:
    """ALT-style landmark-based field constructor.

    Samples a bounded training subgraph from the goal, computes exact costs
    within that subgraph, and uses the minimum landmark distance as the field value.
    """
    strategy_id: str = "landmark_alt"
    n_landmarks: int = 50
    sample_budget: int = 200

    def construct(
        self,
        domain: ProofStateDomain,
        start: State,
        target: Proposition,
    ) -> ConstructedField:
        """Build a landmark-based field."""
        cost = ConstructionCost()
        
        # Find a goal state (one that contains the target)
        goal_state = None
        for _ in range(100):
            s = domain.random_state()
            if target in s:
                goal_state = s
                break
        
        if goal_state is None:
            # Fallback: create a synthetic goal state
            base = domain.random_state()
            goal_state = base | {target}
        
        # Sample landmarks via limited backward search from goal
        landmarks = {goal_state: 0.0}
        frontier = deque([goal_state])
        seen = {goal_state}
        
        expansions = 0
        while frontier and len(landmarks) < self.n_landmarks and expansions < self.sample_budget:
            current = frontier.popleft()
            
            for pred, edge_cost in domain.predecessors(current):
                if pred not in seen:
                    seen.add(pred)
                    new_dist = landmarks[current] + edge_cost
                    if pred not in landmarks or new_dist < landmarks[pred]:
                        landmarks[pred] = new_dist
                    frontier.append(pred)
                expansions += 1
        
        cost = ConstructionCost(node_expansions=expansions)
        
        # Build field evaluator
        table = dict(landmarks)
        
        def evaluator(state: State) -> float:
            best = float('inf')
            for landmark, landmark_cost in landmarks.items():
                diff = len(state.symmetric_difference(landmark))
                dist_estimate = float(diff)
                total = dist_estimate + landmark_cost
                if total < best:
                    best = total
            return best if best != float('inf') else 0.0
        
        return ConstructedField(
            strategy_id=self.strategy_id,
            target=goal_state,
            intrinsic_geometry_id=domain.domain_id,
            cost_algebra_id=domain.cost_algebra_id,
            construction_cost=cost,
            table=table,
            evaluator=evaluator,
            default_value=0.0,
            per_query_evaluation_cost=0.0,
            provenance={"constructor": "landmark_alt", "n_landmarks": len(landmarks)},
        )


# ---------------------------------------------------------------------------
# Search algorithms
# ---------------------------------------------------------------------------

def bfs_search(
    domain: ProofStateDomain,
    start: State,
    target: Proposition,
    budget: int = 10000,
) -> Dict:
    """Plain BFS without any field guidance."""
    seen = {start}
    q = deque([start])
    expanded = 0
    found = False
    
    while q and expanded < budget:
        state = q.popleft()
        expanded += 1
        
        if domain.is_goal(state, target):
            found = True
            break
        
        for succ, _ in domain.successors(state):
            if succ not in seen:
                seen.add(succ)
                q.append(succ)
    
    return {
        "expanded": expanded,
        "found": found,
        "seen": len(seen),
    }


def field_guided_search(
    domain: ProofStateDomain,
    field: ConstructedField,
    start: State,
    target: Proposition,
    budget: int = 10000,
) -> Dict:
    """Best-first search guided by the constructed field."""
    seen = {start}
    heap = [(field(start), 0, start)]
    expanded = 0
    found = False
    tie_breaker = 1
    
    field.reset_evaluation_counter()
    
    while heap and expanded < budget:
        _, _, state = heapq.heappop(heap)
        expanded += 1
        
        if domain.is_goal(state, target):
            found = True
            break
        
        for succ, _ in domain.successors(state):
            if succ not in seen:
                seen.add(succ)
                heapq.heappush(heap, (field(succ), tie_breaker, succ))
                tie_breaker += 1
    
    return {
        "expanded": expanded,
        "found": found,
        "seen": len(seen),
        "field_evaluations": field.evaluations,
    }


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_ci(values: List[float], seed: int, B: int = 5000) -> Dict:
    """Compute bootstrap 95% CI."""
    if not values:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    
    rng = random.Random(seed)
    mean = sum(values) / len(values)
    
    samples = []
    for _ in range(B):
        sample = [values[rng.randrange(len(values))] for _ in values]
        samples.append(sum(sample) / len(sample))
    
    samples.sort()
    lo = samples[int(0.025 * B)]
    hi = samples[int(0.975 * B)]
    
    return {
        "mean": round(mean, 4),
        "lo": round(lo, 4),
        "hi": round(hi, 4),
        "n": len(values),
    }


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_one(
    domain: ProofStateDomain,
    start: State,
    target: Proposition,
    seed: int,
    budget: int = 10000,
) -> Dict:
    """Run a single task comparison."""
    
    # Construct the field
    constructor = LandmarkConstructor(n_landmarks=30, sample_budget=100)
    field = constructor.construct(domain, start, target)
    
    construction_cost = field.construction_cost.total_node_equivalents()
    
    # Run baseline (BFS)
    baseline_result = bfs_search(domain, start, target, budget)
    
    # Run field-guided search
    field_result = field_guided_search(domain, field, start, target, budget)
    
    # Compute net savings
    search_savings = baseline_result["expanded"] - field_result["expanded"]
    net_saving = search_savings - construction_cost
    
    return {
        "baseline_expanded": baseline_result["expanded"],
        "field_expanded": field_result["expanded"],
        "construction_cost": round(construction_cost, 4),
        "search_savings": search_savings,
        "net_saving": round(net_saving, 4),
        "baseline_found": baseline_result["found"],
        "field_found": field_result["found"],
        "field_evaluations": field_result["field_evaluations"],
        "construction_cost_breakdown": field.construction_cost.as_dict(),
    }


def run_experiment(
    n_tasks: int = 120,
    n_propositions: int = 15,
    n_rules: int = 20,
    seed: int = 571,
    task_budget: int = 5000,
) -> Dict:
    """Run full experiment with bootstrap CI."""
    rng = random.Random(seed)
    
    results = []
    completed = 0
    
    for i in range(n_tasks):
        task_seed = seed + i
        domain = ProofStateDomain(
            n_propositions=n_propositions,
            n_rules=n_rules,
            seed=task_seed,
        )
        
        # Pick a random start state and target proposition
        start = domain.random_state(min_size=1)
        available = [p for p in range(domain.n_propositions) if p not in start]
        if not available:
            continue
        target = rng.choice(available)
        
        try:
            result = run_one(domain, start, target, task_seed, task_budget)
            results.append(result)
            completed += 1
        except Exception as e:
            continue
    
    # Extract metrics for bootstrap
    net_savings = [r["net_saving"] for r in results]
    search_savings = [r["search_savings"] for r in results]
    construction_costs = [r["construction_cost"] for r in results]
    
    bs_seed = seed + 10000
    
    claim = (
        "development known-world evidence; field construction net-cost experiment "         "on symbolic proof-state domain; field = landmark-based ALT heuristic; "         "compares field-guided best-first vs plain BFS; "         "net metric = search savings - construction cost; grants no scientific authority."
    )
    
    return {
        "schema_version": "orion-field-construction-v1",
        "seed": seed,
        "n_completed": completed,
        "n_propositions": n_propositions,
        "n_rules": n_rules,
        "task_budget": task_budget,
        "strategy_id": "landmark_alt",
        "claim_boundary": claim,
        "grants_scientific_authority": False,
        "status": "DEVELOPMENT_KNOWN_WORLD_FIELD_CONSTRUCTION_INSTRUMENT_ONLY",
        "net_search_saving": bootstrap_ci(net_savings, bs_seed),
        "search_savings": bootstrap_ci(search_savings, bs_seed + 1),
        "construction_cost": bootstrap_ci(construction_costs, bs_seed + 2),
        "fraction_net_positive": round(sum(1 for x in net_savings if x > 0) / len(net_savings), 4) if net_savings else 0.0,
        "fraction_found_by_both": round(sum(1 for r in results if r["baseline_found"] and r["field_found"]) / len(results), 4) if results else 0.0,
        "per_task": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=571)
    ap.add_argument("--tasks", type=int, default=120)
    ap.add_argument("--propositions", type=int, default=15)
    ap.add_argument("--rules", type=int, default=20)
    ap.add_argument("--budget", type=int, default=5000)
    a = ap.parse_args()
    
    result = run_experiment(
        n_tasks=a.tasks,
        n_propositions=a.propositions,
        n_rules=a.rules,
        seed=a.seed,
        task_budget=a.budget,
    )
    
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2))
    
    print(f"WROTE={RESULT.relative_to(HERE.parents[1])}")
    print(f"Tasks completed: {result['n_completed']}")
    print(f"Net search saving: {result['net_search_saving']}")
    print(f"Search savings (before construction cost): {result['search_savings']}")
    print(f"Construction cost: {result['construction_cost']}")
    print(f"Fraction net positive: {result['fraction_net_positive']}")
    print("AUTHORITY_GRANTED=false")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
