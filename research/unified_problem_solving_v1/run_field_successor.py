#!/usr/bin/env python3
"""#538 field-construction SUCCESSOR experiment: goal-set reachability-grounded
field vs the parent ladder (CEGAR / PDB / abstraction / landmarks) + oracle ceiling.

BEFORE (historical NEGATIVE, preserved unchanged at results/field_construction.json):
    net_search_saving  mean=-0.3738  lo=-0.3919  hi=-0.3549  n=100  KEEP_PROPOSAL_ONLY

Diagnosed root causes (see run_field_construction.py header + this lane's brief):
  1. goal-representation mismatch (single synthetic target, not the goal SET);
  2. symmetric-difference PROXY ranker (anti-correlated -> expands MORE than BFS);
  3. no amortization + default 999999.0 (search refuses to leave the table).

This successor fixes all three and tests whether the goal-set field beats the
strongest parent on AMORTIZED net search saving, every stage cost charged, with
a correctness hard gate (a field that loses solvability cannot win) and the
exact cost-to-go field as the oracle ceiling.

Claim class = EFFICIENCY; cost field = construction_cost. No scientific authority.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import FrozenSet, List, Sequence, Tuple

import sys
sys.path.insert(0, "src")
from rakl.field_successor import (  # noqa: E402
    UniformFieldConstructor,
    SymDiffProxyFieldConstructor,
    SingleTargetFieldConstructor,
    PatternDatabaseFieldConstructor,
    CEGARAbstractionFieldConstructor,
    GoalSetExactFieldConstructor,
    GoalSetLandmarkFieldConstructor,
    HybridFieldConstructor,
    exact_goal_set_cost_to_go,
    forward_reachable,
    greedy_best_first_search,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "field_construction_successor.json"

# amortization sweep (preregistered)
QUERY_COUNTS = [1, 2, 5, 10, 20, 50, 100]

Proposition = int
State = FrozenSet[Proposition]


# ---------------------------------------------------------------------------
# Symbolic proof-state domain (same generative model as the historical run so
# BEFORE/AFTER are comparable; rewritten here to be self-contained).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InferenceRule:
    rule_id: str
    premises: Tuple[Proposition, ...]
    conclusion: Proposition
    cost: float = 1.0

    def can_apply(self, state: State) -> bool:
        return all(p in state for p in self.premises)

    def apply(self, state: State) -> State:
        return state | {self.conclusion}


class ProofStateDomain:
    domain_id = "proof_state_v1"
    cost_algebra_id = "additive_positive"

    def __init__(self, n_propositions: int, n_rules: int, seed: int = 42):
        self.rng = random.Random(seed)
        self.n_propositions = n_propositions
        self.rules: List[InferenceRule] = []
        for i in range(n_rules):
            n_premises = self.rng.randint(1, 3)
            max_premise = max(1, n_propositions // 2)
            premises = tuple(self.rng.sample(range(max_premise), n_premises))
            conclusion = self.rng.randint(n_propositions // 2, n_propositions - 1)
            self.rules.append(InferenceRule(f"rule_{i}", premises, conclusion, 1.0))
        self.axioms = frozenset(range(n_propositions // 3))

    @lru_cache(maxsize=20000)
    def successors(self, state: State):
        out = []
        for rule in self.rules:
            if rule.can_apply(state):
                out.append((rule.apply(state), rule.cost))
        return out

    @lru_cache(maxsize=20000)
    def predecessors(self, state: State):
        out = []
        for rule in self.rules:
            if rule.conclusion in state:
                ps = state - {rule.conclusion}
                if all(p in ps for p in rule.premises):
                    out.append((ps, rule.cost))
        return out

    def feature_names(self):
        return ["n_proven", "remaining", "remaining"]

    def features(self, state, target):
        return [float(len(state)), float(self.n_propositions - len(state))] * 1 + [0.0]

    def is_goal(self, state, target):
        return target in state

    def random_state(self, min_size: int = 1) -> State:
        size = self.rng.randint(min_size, max(min_size, self.n_propositions // 2))
        return frozenset(self.rng.sample(range(self.n_propositions), size))

    def all_goal_states(self, target) -> List[State]:
        out = []
        for _ in range(200):
            s = self.random_state()
            if target in s:
                out.append(s)
        return out


class ChainDistractorDomain:
    """Deep-search regime: a dependency chain c0->c1->...->cK (target=cK) plus a
    bushy cone of irrelevant distractor propositions/rules. BFS wastes effort on
    the distractor cone; an exact goal-set field climbs the chain directly.

    This is the regime where heuristic guidance is APPLICABLE (standard
    heuristic-search benchmark structure: a thin goal path buried in irrelevant
    operators). Propositions 0..K are the chain; K+1.. are distractors.
    """

    domain_id = "chain_distractor_proof_v1"
    cost_algebra_id = "additive_positive"

    def __init__(self, K: int, n_distractor: int, n_distractor_rules: int, seed: int):
        self.K = K
        self.n_propositions = K + 1 + n_distractor
        self.axioms = frozenset({0})
        rules: List[InferenceRule] = []
        for i in range(1, K + 1):
            rules.append(InferenceRule(f"chain_{i}", (i - 1,), i, 1.0))
        rng = random.Random(seed + 1)
        for j in range(n_distractor_rules):
            pre_count = rng.randint(1, 2)
            pool = list(range(0, K + 1)) + list(range(K + 1, K + 1 + n_distractor))
            premises = tuple(rng.sample(pool, pre_count))
            concl = rng.choice(list(range(K + 1, K + 1 + n_distractor)))
            rules.append(InferenceRule(f"dist_{j}", premises, concl, 1.0))
        self.rules = rules

    @lru_cache(maxsize=100000)
    def successors(self, state: State):
        return [(r.apply(state), r.cost) for r in self.rules if r.can_apply(state)]

    @lru_cache(maxsize=100000)
    def predecessors(self, state: State):
        out = []
        for r in self.rules:
            if r.conclusion in state:
                ps = state - {r.conclusion}
                if all(p in ps for p in r.premises):
                    out.append((ps, r.cost))
        return out

    def feature_names(self):
        return ["n_proven", "chain_progress", "remaining"]

    def features(self, state, target):
        return [float(len(state)), 0.0, 0.0]

    def is_goal(self, state, target):
        return target in state

    def all_goal_states(self, target) -> List[State]:
        cone = forward_reachable(self, [self.axioms])
        return [s for s in cone if target in s][:200]


# ---------------------------------------------------------------------------
# statistics helpers
# ---------------------------------------------------------------------------


def bootstrap_ci(values: List[float], seed: int, B: int = 4000):
    if not values:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(seed)
    mean = sum(values) / len(values)
    samples = []
    for _ in range(B):
        s = sum(values[rng.randrange(len(values))] for _ in values) / len(values)
        samples.append(s)
    samples.sort()
    return {"mean": round(mean, 4), "lo": round(samples[int(0.025 * B)], 4),
            "hi": round(samples[int(0.975 * B)], 4), "n": len(values)}


def spearman_rho(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 3:
        return 0.0

    def ranks(vs):
        idx = sorted(range(len(vs)), key=lambda i: vs[i])
        r = [0.0] * len(vs)
        i = 0
        while i < len(vs):
            j = i
            while j + 1 < len(vs) and vs[idx[j + 1]] == vs[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if vx == 0 or vy == 0:
        return 0.0
    return cov / (vx * vy)


# ---------------------------------------------------------------------------
# per-domain evaluation of the full ladder
# ---------------------------------------------------------------------------


def evaluate_ladder(domain: ProofStateDomain, target: Proposition,
                    starts: List[State], task_budget: int) -> dict:
    roots = list(starts)
    # oracle / true cost-to-go over the union reachability cone (for rank corr)
    reachable = forward_reachable(domain, roots)
    true_ctg, _ = exact_goal_set_cost_to_go(domain, reachable, target)

    constructors = {
        "uniform_bfs_parent": lambda: UniformFieldConstructor().construct(domain, target),
        "symdiff_proxy_parent": lambda: SymDiffProxyFieldConstructor().construct(domain, target),
        "single_target_parent": lambda: SingleTargetFieldConstructor().construct(domain, target),
        "pdb_naive_parent": lambda: PatternDatabaseFieldConstructor(6, target_aware=False).construct(domain, target),
        "pdb_target_aware_parent": lambda: PatternDatabaseFieldConstructor(6, target_aware=True).construct(domain, target),
        "cegar_parent": lambda: CEGARAbstractionFieldConstructor(3, 3).construct(domain, target),
        "goalset_landmark_successor": lambda: GoalSetLandmarkFieldConstructor(150).construct(
            domain, target, roots=roots),
        "goalset_exact_successor": lambda: GoalSetExactFieldConstructor().construct(
            domain, target, roots=roots),
        "hybrid_goalset_pdb_successor": lambda: HybridFieldConstructor().construct(
            domain, target, roots=roots),
    }

    per_candidate = {}
    for cid, build in constructors.items():
        t0 = time.perf_counter()
        field = build()
        build_s = time.perf_counter() - t0
        ccost = field.construction_cost.total_node_equivalents()
        # baseline (uniform) search is identical for every candidate; compute once
        # via the uniform parent's own phi=None path, but to keep expansions
        # comparable we run BFS (phi=None) here.
        baseline_expansions: List[int] = []
        field_expansions: List[int] = []
        found_agree = True
        for s in starts:
            base = greedy_best_first_search(domain, None, s, target, task_budget)
            fres = greedy_best_first_search(domain, field.phi, s, target, task_budget)
            baseline_expansions.append(base["expanded"])
            field_expansions.append(fres["expanded"])
            if bool(base["found"]) != bool(fres["found"]):
                found_agree = False
        savings = [b - f for b, f in zip(baseline_expansions, field_expansions)]
        # amortization: cumulative net = sum(savings[:q]) - ccost
        amort = []
        for q in QUERY_COUNTS:
            cum = sum(savings[:q]) - ccost
            amort.append({"q": q, "cumulative_net": round(cum, 4),
                          "net_per_query": round(cum / q, 4)})
        crossover = next((a["q"] for a in amort if a["cumulative_net"] > 0), None)
        # rank correlation of field h vs true cost-to-go on reachable states
        sample_states = list(true_ctg.keys())[:300]
        xs = [field.phi(st) for st in sample_states]
        ys = [true_ctg[st] for st in sample_states]
        rho = spearman_rho(xs, ys)
        # false-descent rate: fraction of reachable edges s->s' with h(s') > h(s)
        # (a perfect goal-bound ranker is non-increasing along shortest paths).
        climbs = 0
        edges = 0
        for st in list(true_ctg.keys())[:300]:
            hs = field.phi(st)
            for st2, _ in domain.successors(st):
                edges += 1
                if field.phi(st2) > hs + 1e-9:
                    climbs += 1
        per_candidate[cid] = {
            "construction_cost_node_equiv": round(ccost, 4),
            "build_wall_time_s": round(build_s, 6),
            "mean_baseline_expanded": round(sum(baseline_expansions) / len(baseline_expansions), 4),
            "mean_field_expanded": round(sum(field_expansions) / len(field_expansions), 4),
            "mean_search_saving": round(sum(savings) / len(savings), 4),
            "savings_per_query": savings,
            "amortization": amort,
            "crossover_query": crossover,
            "final_net_per_query": amort[-1]["net_per_query"],
            "final_cumulative_net": amort[-1]["cumulative_net"],
            "found_agrees_with_baseline": found_agree,
            "rank_correlation_with_true_ctg": round(rho, 4),
            "false_descent_rate": round(climbs / edges, 4) if edges else 0.0,
            "admissibility_status": field.admissibility_status.value,
            "table_entries": len(field.table),
        }
    return per_candidate


SUCC_KEY = "goalset_exact_successor"
PARENT_IDS = ["uniform_bfs_parent", "symdiff_proxy_parent", "single_target_parent",
              "pdb_naive_parent", "pdb_target_aware_parent", "cegar_parent"]


def run_experiment(n_domains=100, n_queries=100, n_propositions=12, n_rules=15,
                   seed=572, task_budget=4000, regime="shallow") -> dict:
    """Run one stratum. ``regime='deep'`` uses ChainDistractorDomain with deep
    starts (the APPLICABLE regime); ``regime='shallow'`` uses the original
    random monotone domain (the APPLICABILITY BOUNDARY). Returns a regime-result
    dict (no envelope); :func:`main` wraps both strata in the final artifact."""
    rng = random.Random(seed)
    domains_out = []
    completed = 0
    ladder = [(6, 6), (7, 7), (8, 8), (8, 9), (9, 8), (10, 8)]
    for i in range(n_domains):
        if regime == "deep":
            K, nd = ladder[i % len(ladder)]
            domain = ChainDistractorDomain(K, nd, nd * 2, seed=seed + i)
            target = K
            cone = forward_reachable(domain, [domain.axioms], cap=20000)
            deep = [s for s in cone if target not in s
                    and max([j for j in range(K + 1) if j in s], default=0) <= 2]
            if len(deep) < 5:
                continue
            rng2 = random.Random(seed + 1000 + i)
            rng2.shuffle(deep)
            starts = deep[:n_queries]
        else:
            domain = ProofStateDomain(n_propositions, n_rules, seed=seed + i)
            target = rng.randint(n_propositions // 2, n_propositions - 1)
            starts = []
            while len(starts) < n_queries:
                s = domain.random_state(1)
                if target not in s:
                    starts.append(s)
        try:
            per = evaluate_ladder(domain, target, starts, task_budget)
        except Exception:
            import traceback
            traceback.print_exc()
            continue
        domains_out.append(per)
        completed += 1

    succ_finals = [d[SUCC_KEY]["final_net_per_query"] for d in domains_out]
    succ_ci = bootstrap_ci(succ_finals, seed + 10000)
    cand_summary = {}
    for cid in domains_out[0].keys():
        finals = [d[cid]["final_net_per_query"] for d in domains_out]
        cum = [d[cid]["final_cumulative_net"] for d in domains_out]
        ccost = [d[cid]["construction_cost_node_equiv"] for d in domains_out]
        cross = [d[cid]["crossover_query"] for d in domains_out if d[cid]["crossover_query"]]
        rho = [d[cid]["rank_correlation_with_true_ctg"] for d in domains_out]
        fd = [d[cid]["false_descent_rate"] for d in domains_out]
        found_ok = all(d[cid]["found_agrees_with_baseline"] for d in domains_out)
        cand_summary[cid] = {
            "net_per_query_ci": bootstrap_ci(finals, seed + 10001 + abs(hash(cid)) % 9000),
            "cumulative_net_ci": bootstrap_ci(cum, seed + 20001 + abs(hash(cid)) % 9000),
            "construction_cost_ci": bootstrap_ci(ccost, seed + 30001 + abs(hash(cid)) % 9000),
            "fraction_crossover": round(len(cross) / completed, 4),
            "mean_crossover_query": round(sum(cross) / len(cross), 1) if cross else None,
            "mean_rank_correlation": round(sum(rho) / len(rho), 4),
            "mean_false_descent_rate": round(sum(fd) / len(fd), 4),
            "found_agrees_with_baseline_all_domains": found_ok,
        }

    strongest_parent = max(PARENT_IDS,
                           key=lambda c: cand_summary[c]["net_per_query_ci"]["mean"])
    # HEAD-TO-HEAD: successor total-cost advantage over the strongest parent, per
    # query at q=100. Both sides share the same uniform-BFS baseline and both
    # charge their own one-time construction cost, so this difference IS the
    # fully-costed successor-vs-best-available-mechanic advantage (RSHEA #538).
    hh = [d[SUCC_KEY]["final_net_per_query"] - d[strongest_parent]["final_net_per_query"]
          for d in domains_out]
    hh_ci = bootstrap_ci(hh, seed + 50000)

    correctness_gate = cand_summary[SUCC_KEY]["found_agrees_with_baseline_all_domains"]
    hh_positive = (hh_ci["lo"] > 0 and correctness_gate)
    beats_strongest_parent = (hh_ci["mean"] > 0)
    if not correctness_gate:
        verdict = "NEGATIVE"
        verdict_reason = "correctness hard gate failed: field lost solvability vs baseline"
    elif hh_positive:
        verdict = "POSITIVE"
        verdict_reason = (f"successor statistically beats strongest parent "
                          f"({strongest_parent}) with all costs charged")
    elif hh_ci["hi"] < 0:
        verdict = "KEEP_PROPOSAL_ONLY"
        verdict_reason = (f"dominated by strongest parent ({strongest_parent}); "
                          f"head-to-head total-cost advantage CI below zero - the exact "
                          f"field's perfect guidance does not amortize vs cheaper proxies/abstractions")
    else:
        verdict = "KEEP_PROPOSAL_ONLY"
        verdict_reason = (f"no statistical advantage over strongest parent "
                          f"({strongest_parent}); head-to-head CI includes zero")

    return {
        "regime": regime, "n_completed": completed, "sample": completed,
        "task_budget": task_budget, "candidate_summary": cand_summary,
        "strongest_parent": strongest_parent,
        "strongest_parent_net": cand_summary[strongest_parent]["net_per_query_ci"],
        # gate headline: successor vs strongest parent, both construction charged
        "net_advantage_over_strongest_parent": hh_ci,
        # diagnostic: successor vs uniform-BFS baseline (own construction charged)
        "net_vs_baseline_bfs": succ_ci,
        "net_search_saving": succ_ci,
        "construction_cost": cand_summary[SUCC_KEY]["construction_cost_ci"],
        "verdict": verdict, "verdict_reason": verdict_reason,
        "correctness_hard_gate_passed": correctness_gate,
        "successor_beats_strongest_parent": beats_strongest_parent,
        "successor_mean_net_per_query": round(succ_ci["mean"], 4),
        "successor_head_to_head_mean": round(hh_ci["mean"], 4),
        "successor_crossover_fraction": cand_summary[SUCC_KEY]["fraction_crossover"],
        "successor_mean_crossover_query": cand_summary[SUCC_KEY]["mean_crossover_query"],
        "successor_mean_rank_correlation": cand_summary[SUCC_KEY]["mean_rank_correlation"],
        "successor_mean_false_descent_rate": cand_summary[SUCC_KEY]["mean_false_descent_rate"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=572)
    ap.add_argument("--deep-domains", type=int, default=60)
    ap.add_argument("--shallow-domains", type=int, default=40)
    a = ap.parse_args()
    t0 = time.perf_counter()
    deep = run_experiment(n_domains=a.deep_domains, seed=a.seed, regime="deep", task_budget=12000)
    shallow = run_experiment(n_domains=a.shallow_domains, seed=a.seed + 50000, regime="shallow", task_budget=4000)
    elapsed = time.perf_counter() - t0

    claim = ("development known-world evidence; #538 field-construction successor; "
             "goal-set reachability-grounded exact field vs uniform/symdiff/single-target/"
             "PDB(naive+target-aware)/CEGAR parents + bounded-landmark + hybrid; "
             "amortized net search saving over deep-search chain-distractor regime "
             "(applicable); shallow random-monotone regime reported as applicability "
             "boundary; grants no scientific authority")

    out = {
        "schema_version": "orion-field-construction-successor-v1-issue538",
        "grants_scientific_authority": False,
        "seed": a.seed,
        "n_completed": deep["n_completed"] + shallow["n_completed"],
        "n": deep["n_completed"] + shallow["n_completed"],
        "sample": deep["n_completed"] + shallow["n_completed"],
        "independent_unit": "domain",
        "n_queries_per_domain": 100,
        "query_counts_amortization": QUERY_COUNTS,
        "wall_time_s": round(elapsed, 3),
        "claim_class": "EFFICIENCY",
        "measured_quantity": "net_search_saving_per_query (states-expanded units)",
        "claim_boundary": claim,
        # HEADLINE = deep (applicable) regime. The promotion gate reads the
        # successor's fully-costed advantage over its STRONGEST parent
        # (net_advantage_over_strongest_parent); net_vs_baseline_bfs is diagnostic.
        "net_advantage_over_strongest_parent": deep["net_advantage_over_strongest_parent"],
        "net_vs_baseline_bfs": deep["net_vs_baseline_bfs"],
        "net_search_saving": deep["net_search_saving"],
        "construction_cost": deep["construction_cost"],
        "successor_strategy": SUCC_KEY,
        "oracle_ceiling_strategy": SUCC_KEY,
        "verdict": deep["verdict"],
        "verdict_reason": deep["verdict_reason"],
        "correctness_hard_gate_passed": deep["correctness_hard_gate_passed"],
        "successor_beats_strongest_parent": deep["successor_beats_strongest_parent"],
        "strongest_parent": deep["strongest_parent"],
        "strongest_parent_net": deep["strongest_parent_net"],
        "successor_mean_net_per_query": deep["successor_mean_net_per_query"],
        "successor_head_to_head_mean": deep["successor_head_to_head_mean"],
        "successor_mean_rank_correlation": deep["successor_mean_rank_correlation"],
        "successor_mean_false_descent_rate": deep["successor_mean_false_descent_rate"],
        "successor_crossover_fraction": deep["successor_crossover_fraction"],
        "successor_mean_crossover_query": deep["successor_mean_crossover_query"],
        "applicable_regime": deep,
        "applicability_boundary_regime": shallow,
        "before_historical": {
            "source": "results/field_construction.json (preserved unchanged)",
            "net_search_saving": {"mean": -0.3738, "lo": -0.3919, "hi": -0.3549, "n": 100},
            "verdict": "KEEP_PROPOSAL_ONLY",
        },
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(out, indent=2))
    print(f"WROTE={RESULT.name}")
    print(f"VERDICT={out['verdict']}  ({out['verdict_reason']})")
    print(f"AFTER (deep) net_advantage_over_strongest_parent: {out['net_advantage_over_strongest_parent']}")
    print(f"   (diagnostic) net_vs_baseline_bfs: {out['net_vs_baseline_bfs']}")
    print(f"strongest_parent={out['strongest_parent']} net_vs_bfs={out['strongest_parent_net']}")
    print(f"correctness_gate={out['correctness_hard_gate_passed']} "
          f"beats_parent={out['successor_beats_strongest_parent']}")
    print(f"BEFORE: {out['before_historical']['net_search_saving']}")
    print(f"boundary (shallow) hh={shallow['net_advantage_over_strongest_parent']} verdict={shallow['verdict']}")
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
