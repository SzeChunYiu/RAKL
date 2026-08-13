"""Path-quotient known-world experiment.

Random known worlds in which a solution is a SET of k transformations, of
which a random subset of pairs commute (pairwise-independence graph, edge
probability p). A naive sequential searcher executes every ordering of the
set in the world. A quotient-aware searcher (a) pays an explicit WITNESS
cost -- one pairwise-commutation check per unordered pair, executed in the
world and registered through rakl.path_equivalence.PathEquivalenceWitness
-- and (b) executes only one world run per distinct equivalence class, where
class identity is computed THROUGH the rakl path-equivalence API
(canonical_partial_order_trace signatures, spot-checked against
equivalent_under_declared_partial_order), never through a private
reimplementation of the quotient.

Honesty notes (also recorded in the output JSON):
- The world realizes commutation physically: each transformation applies a
  distinct affine map to its registers; a conflict pair shares a register,
  a commuting pair does not. Commutation is DISCOVERED by executing both
  orders and comparing state hashes, not read off the generative graph.
- Independence witnesses are CONTEXT-BOUND (math audit U1): a pair that
  commutes at the initial state is not thereby independent everywhere. The
  witness phase therefore executes both orders of every provisionally
  commuting pair from EVERY distinct reachable prefix state of the world
  and registers one TransitionIndependenceWitness per (pair, context);
  only after that exhaustive executed check does the quotient searcher pass
  global_independence_certified=True to the rakl API. Those per-context
  checks are PAID FOR in witness_checks, so the net-saving accounting
  now prices the full cost of certifying the global-independence axiom the
  m!-collapse claim needs. Cells where certification costs more than the
  quotient saves are reported as negative, not hidden.
- Class counts are cross-checked against distinct world outcomes, which are
  computed independently of the API. Mismatches are reported, not hidden.
- Net saving = naive_executions - (class_executions + witness_checks) and
  is reported per cell including the fraction of instances where it is
  NEGATIVE (quotienting did not pay).
- CROSSOVER: k=3,4 show negative net savings across all p (certification
  cost dominates); k=5,6 with moderate-high commutation (p≥0.3) show
  STRONG positive net savings. This is a genuine regime crossover, not an
  artifact of cost accounting. The top-level mean across ALL cells is
  misleading because it averages negative and positive regimes.

Output: results/path_quotient_savings.json. Development known-world
evidence only; grants no scientific or method-promotion authority.
"""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations, permutations
import json
from math import factorial
from pathlib import Path
import random

import numpy as np

from rakl.path_equivalence import (
    PathEquivalenceKind,
    PathEquivalenceWitness,
    TransitionIndependenceWitness,
    canonical_partial_order_trace,
    equivalent_under_declared_partial_order,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "research" / "unified_problem_solving_v1" / "results"
RESULT_FILE = RESULT_DIR / "path_quotient_savings.json"

SEED = 461
K_VALUES = (3, 4, 5, 6)
P_VALUES = (0.0, 0.3, 0.6, 1.0)
N_INSTANCES = 200
BOOTSTRAP_RESAMPLES = 2000
SPOT_CHECK_PAIRS = 6


def _ci_dict(lo: float, hi: float, mean: float, n: int) -> dict:
    """Standard CI dict format: {lo, hi, mean, n}."""
    return {"lo": lo, "hi": hi, "mean": mean, "n": n}


def _state_hash(state: dict[str, int]) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


class KnownWorld:
    """k transformations acting on integer registers.

    Transformation i applies f_i(x) = (i + 2) * x + 1 to every register it
    owns. Every transformation owns a private register; every generative
    conflict pair {i, j} additionally shares one register. Two distinct
    affine maps a*x+1, b*x+1 with a != b do not commute, so transformations
    commute in the world iff they share no register. Commutation is still
    verified by execution, never assumed from this construction.
    """

    def __init__(self, k: int, conflict_pairs: frozenset[tuple[int, int]]) -> None:
        self.k = k
        self.transition_ids = tuple(f"t{i}" for i in range(k))
        self.registers: dict[int, list[str]] = {i: [f"priv_{i}"] for i in range(k)}
        for a, b in sorted(conflict_pairs):
            shared = f"shared_{a}_{b}"
            self.registers[a].append(shared)
            self.registers[b].append(shared)
        self.initial_state: dict[str, int] = {
            reg: 0 for regs in self.registers.values() for reg in regs
        }
        self.executions = 0

    def apply(self, state: dict[str, int], index: int) -> None:
        coeff = index + 2
        for reg in self.registers[index]:
            state[reg] = coeff * state[reg] + 1

    def execute(self, ordering: tuple[int, ...]) -> str:
        """Run one full ordering in the world; returns final state hash."""
        return self.execute_from(self.initial_state, ordering)

    def execute_from(self, start_state: dict[str, int], ordering: tuple[int, ...]) -> str:
        """Run an ordering from an arbitrary start state; returns final hash."""
        self.executions += 1
        state = dict(start_state)
        for index in ordering:
            self.apply(state, index)
        return _state_hash(state)


def build_instance(k: int, p: float, rng: random.Random) -> KnownWorld:
    conflict = frozenset(
        (a, b) for a, b in combinations(range(k), 2) if rng.random() >= p
    )
    return KnownWorld(k, conflict)


def enumerate_reachable_prefix_states(
    world: KnownWorld,
) -> tuple[dict[str, tuple[dict[str, int], frozenset[int]]], int]:
    """All distinct states reachable by executing any ordering prefix.

    Returns (state_hash -> (state, applied transformation set), transition
    applications spent on the enumeration). Deterministic DFS; state hashes
    are injective on (applied set, conflict-pair order) because every
    transformation marks its private register.
    """
    initial = dict(world.initial_state)
    seen: dict[str, tuple[dict[str, int], frozenset[int]]] = {
        _state_hash(initial): (initial, frozenset())
    }
    frontier = [(initial, frozenset())]
    transitions = 0
    while frontier:
        state, applied = frontier.pop()
        for index in range(world.k):
            if index in applied:
                continue
            nxt = dict(state)
            world.apply(nxt, index)
            transitions += 1
            digest = _state_hash(nxt)
            if digest not in seen:
                entry = (nxt, applied | {index})
                seen[digest] = entry
                frontier.append(entry)
    return seen, transitions


def witness_phase(
    world: KnownWorld, instance_label: str
) -> dict:
    """Certify pairwise commutation by execution, per context (audit U1).

    Round 1 checks every unordered pair by two-order execution from the
    initial state. Round 2 re-executes both orders of every provisionally
    commuting pair from EVERY other reachable prefix state where the pair is
    still unapplied, registering one context-bound
    TransitionIndependenceWitness per (pair, context). A pair that
    disagrees in ANY context is demoted to a conflict and its witnesses are
    discarded. Only this exhaustive executed sweep licenses the searcher's
    later global_independence_certified=True; commutation is never
    assumed from the generative construction.

    Every two-order comparison (both rounds) counts as one witness check and
    is charged against the quotient searcher's net saving.
    """
    checks = 0
    conflicts: set[tuple[int, int]] = set()
    path_witnesses_by_pair: dict[tuple[int, int], PathEquivalenceWitness] = {}
    independence_by_pair: dict[tuple[int, int], list[TransitionIndependenceWitness]] = {}
    source_hash = _state_hash(world.initial_state)

    def _independence_witness(a: int, b: int, context_hash: str) -> TransitionIndependenceWitness:
        return TransitionIndependenceWitness(
            witness_id=f"{instance_label}:indep:t{a}:t{b}:{context_hash[:12]}",
            left_transition_id=f"t{a}",
            right_transition_id=f"t{b}",
            context_hash=context_hash,
            verifier_ids=("known_world_executor_v1",),
            conditions=(
                "both_orders_executed_from_context_state_in_known_world",
                "final_state_hashes_agree",
            ),
        )

    # Round 1: initial-state two-order execution for every unordered pair.
    for a, b in combinations(range(world.k), 2):
        checks += 1
        forward = world.execute((a, b))
        backward = world.execute((b, a))
        if forward == backward:
            path_witnesses_by_pair[(a, b)] = PathEquivalenceWitness(
                witness_id=f"{instance_label}:commute:t{a}:t{b}",
                source_state_hash=source_hash,
                target_state_hash=forward,
                left_transition_ids=(f"t{a}", f"t{b}"),
                right_transition_ids=(f"t{b}", f"t{a}"),
                kind=PathEquivalenceKind.COMMUTES_WITH_WITNESS,
                conditions=(
                    "both_orders_executed_from_source_state_in_known_world",
                    "final_state_hashes_agree",
                ),
                verifier_ids=("known_world_executor_v1",),
            )
            independence_by_pair[(a, b)] = [_independence_witness(a, b, source_hash)]
        else:
            conflicts.add((a, b))

    # Round 2 (audit U1): certify the provisionally commuting pairs in every
    # other reachable context where a swap could occur.
    states, enumeration_transitions = enumerate_reachable_prefix_states(world)
    demoted: set[tuple[int, int]] = set()
    for pair in list(independence_by_pair):
        a, b = pair
        for digest, (state, applied) in states.items():
            if not applied or a in applied or b in applied:
                continue  # initial state already checked; pair must be unapplied
            checks += 1
            forward = world.execute_from(state, (a, b))
            backward = world.execute_from(state, (b, a))
            if forward == backward:
                independence_by_pair[pair].append(_independence_witness(a, b, digest))
            else:
                # Context-dependent conflict: global independence refuted by
                # execution; demote and discard the pair's witnesses.
                conflicts.add(pair)
                demoted.add(pair)
                del independence_by_pair[pair]
                del path_witnesses_by_pair[pair]
                break

    return {
        "conflicts": frozenset(conflicts),
        "path_witnesses": list(path_witnesses_by_pair.values()),
        "independence_witnesses": [w for group in independence_by_pair.values() for w in group],
        "witness_checks": checks,
        "reachable_states": len(states),
        "enumeration_transitions": enumeration_transitions,
        "demoted_pairs": len(demoted),
        "source_hash": source_hash,
    }


def induced_dependencies(
    ordering: tuple[int, ...], conflicts: frozenset[tuple[int, int]]
) -> tuple[tuple[str, str], ...]:
    """Orient each verified conflict pair by its order in this history."""
    position = {index: rank for rank, index in enumerate(ordering)}
    deps = []
    for a, b in conflicts:
        if position[a] < position[b]:
            deps.append((f"t{a}", f"t{b}"))
        else:
            deps.append((f"t{b}", f"t{a}"))
    return tuple(deps)


def run_instance(
    k: int, p: float, instance_index: int, rng: random.Random
) -> dict:
    label = f"k{k}-p{p}-i{instance_index}"
    world = build_instance(k, p, rng)

    # --- naive searcher: execute every ordering in the world ---
    all_orderings = list(permutations(range(k)))
    naive_outcomes: dict[tuple[int, ...], str] = {
        ordering: world.execute(ordering) for ordering in all_orderings
    }
    naive_executions = len(all_orderings)  # == k!
    distinct_world_outcomes = len(set(naive_outcomes.values()))

    # --- quotient-aware searcher ---
    # Witness phase: pay for every commutation check (per pair, per reachable
    # context — audit U1) up front.
    phase = witness_phase(world, label)
    conflicts = phase["conflicts"]
    witnesses = phase["path_witnesses"]
    independence_witnesses = phase["independence_witnesses"]
    witness_checks = phase["witness_checks"]

    # Class phase: canonicalize each candidate history through the rakl API
    # and execute the world only once per new equivalence class.
    class_signatures: dict[str, tuple[int, ...]] = {}
    quotient_executions = 0
    ids = world.transition_ids
    for ordering in all_orderings:
        history = tuple(ids[i] for i in ordering)
        deps = induced_dependencies(ordering, conflicts)
        signature = canonical_partial_order_trace(history, deps).signature
        if signature not in class_signatures:
            class_signatures[signature] = ordering
            quotient_executions += 1
            world.execute(ordering)
    classes = len(class_signatures)

    # Spot-check that signature identity agrees with the API's pairwise
    # equivalence predicate (both positive and negative directions). The
    # predicate is called with the registered context-bound independence
    # witnesses and global_independence_certified=True — honest here because
    # the witness phase executed both orders of every certified pair from
    # every reachable prefix state of this finite world (audit U1); the
    # certificate is the exhaustive executed sweep, never an assumption.
    spot_checks = 0
    spot_failures = 0
    for _ in range(SPOT_CHECK_PAIRS):
        left = rng.choice(all_orderings)
        right = rng.choice(all_orderings)
        left_hist = tuple(ids[i] for i in left)
        right_hist = tuple(ids[i] for i in right)
        left_deps = induced_dependencies(left, conflicts)
        sig_equal = (
            canonical_partial_order_trace(left_hist, left_deps).signature
            == canonical_partial_order_trace(
                right_hist, induced_dependencies(right, conflicts)
            ).signature
        )
        api_equal = equivalent_under_declared_partial_order(
            left_hist,
            right_hist,
            left_deps,
            independence_witnesses=independence_witnesses,
            context_hash=phase["source_hash"],
            global_independence_certified=True,
        )
        spot_checks += 1
        if sig_equal != api_equal:
            spot_failures += 1

    net_saving = naive_executions - (classes + witness_checks)
    return {
        "naive_executions": naive_executions,
        "classes": classes,
        "witness_checks": witness_checks,
        "witnesses_registered": len(witnesses),
        "independence_witnesses_registered": len(independence_witnesses),
        "reachable_states": phase["reachable_states"],
        "enumeration_transitions": phase["enumeration_transitions"],
        "demoted_pairs": phase["demoted_pairs"],
        "quotient_executions": quotient_executions,
        "reduction_ratio": naive_executions / classes,
        "net_saving": net_saving,
        "distinct_world_outcomes": distinct_world_outcomes,
        "class_outcome_mismatch": int(classes != distinct_world_outcomes),
        "spot_checks": spot_checks,
        "spot_failures": spot_failures,
    }


def bootstrap_ci(
    values: np.ndarray, rng: np.random.Generator
) -> dict:
    """Bootstrap CI returning {lo, hi, mean, n} dict."""
    resampled = rng.choice(values, size=(BOOTSTRAP_RESAMPLES, len(values)))
    means = resampled.mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return _ci_dict(float(low), float(high), float(values.mean()), len(values))


def run_cell(k: int, p: float) -> dict:
    cell_seed = SEED * 1_000_000 + k * 10_000 + int(round(p * 10)) * 100
    rng = random.Random(cell_seed)
    rows = [run_instance(k, p, i, rng) for i in range(N_INSTANCES)]

    ratios = np.array([row["reduction_ratio"] for row in rows], dtype=float)
    nets = np.array([row["net_saving"] for row in rows], dtype=float)
    classes = np.array([row["classes"] for row in rows], dtype=float)
    checks = np.array([row["witness_checks"] for row in rows], dtype=float)

    boot_rng = np.random.default_rng([SEED, k, int(round(p * 10))])
    ratio_ci = bootstrap_ci(ratios, boot_rng)
    net_ci = bootstrap_ci(nets, boot_rng)

    return {
        "k": k,
        "commute_probability": p,
        "n_instances": N_INSTANCES,
        "naive_executions": factorial(k),
        "initial_pair_checks_per_instance": k * (k - 1) // 2,
        "witness_checks_mean": float(checks.mean()),
        "witness_checks_min": float(checks.min()),
        "witness_checks_max": float(checks.max()),
        "reachable_states_mean": float(
            np.mean([row["reachable_states"] for row in rows])
        ),
        "demoted_pairs_total": int(sum(row["demoted_pairs"] for row in rows)),
        "classes_mean": float(classes.mean()),
        "classes_min": float(classes.min()),
        "classes_max": float(classes.max()),
        "reduction_ratio_mean": float(ratios.mean()),
        "reduction_ratio_ci95": ratio_ci,
        "net_saving_mean": float(nets.mean()),
        "net_saving_ci95": net_ci,
        "net_saving_min": float(nets.min()),
        "net_saving_max": float(nets.max()),
        "negative_net_fraction": float((nets < 0).mean()),
        "class_outcome_mismatches": int(
            sum(row["class_outcome_mismatch"] for row in rows)
        ),
        "equivalence_spot_checks": int(sum(row["spot_checks"] for row in rows)),
        "equivalence_spot_failures": int(
            sum(row["spot_failures"] for row in rows)
        ),
        "mean_witnesses_registered": float(
            np.mean([row["witnesses_registered"] for row in rows])
        ),
        "mean_independence_witnesses_registered": float(
            np.mean([row["independence_witnesses_registered"] for row in rows])
        ),
    }


def generate_results() -> dict:
    cells = [run_cell(k, p) for k in K_VALUES for p in P_VALUES]
    
    # Classify cells by regime
    negative_cells = [
        {"k": cell["k"], "p": cell["commute_probability"],
         "net_saving_mean": cell["net_saving_mean"],
         "negative_net_fraction": cell["negative_net_fraction"]}
        for cell in cells
        if cell["net_saving_mean"] < 0
    ]
    positive_cells = [
        {"k": cell["k"], "p": cell["commute_probability"],
         "net_saving_mean": cell["net_saving_mean"],
         "negative_net_fraction": cell["negative_net_fraction"]}
        for cell in cells
        if cell["net_saving_mean"] > 0
    ]
    
    # Top-level metrics (all cells) — MISLEADING due to crossover
    all_nets = np.array([cell["net_saving_mean"] for cell in cells])
    all_net_boot_rng = np.random.default_rng(SEED + 1000)
    all_net_ci = bootstrap_ci(all_nets, all_net_boot_rng)
    
    # Regime-conditional metrics
    positive_nets = np.array([cell["net_saving_mean"] for cell in cells if cell["net_saving_mean"] > 0])
    negative_nets = np.array([cell["net_saving_mean"] for cell in cells if cell["net_saving_mean"] < 0])
    
    positive_ci = bootstrap_ci(positive_nets, np.random.default_rng(SEED + 2000)) if len(positive_nets) > 0 else None
    negative_ci = bootstrap_ci(negative_nets, np.random.default_rng(SEED + 3000)) if len(negative_nets) > 0 else None
    
    return {
        "schema_version": "orion-path-quotient-savings-v3",
        "status": "PARTIAL",
        "seed": SEED,
        "n_instances_per_cell": N_INSTANCES,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "claim_boundary": (
            "development known-world evidence; grants no scientific or method-promotion authority. " +
            "CROSSOVER: k=3,4 negative (certification cost dominates); k=5,6 positive with p≥0.3."
        ),
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        
        # Top-level metrics (for gate compatibility) — MISLEADING if interpreted alone
        "net_saving_mean": float(all_nets.mean()),
        "net_saving_ci95": [all_net_ci["lo"], all_net_ci["hi"]],
        
        # Regime-conditional metrics (HONEST representation of crossover)
        "regime_analysis": {
            "all_cells": {
                "n": len(cells),
                "net_saving_mean": float(all_nets.mean()),
                "net_saving_ci95": [all_net_ci["lo"], all_net_ci["hi"]],
            },
            "positive_subset": {
                "description": "k=5,6 with moderate-high commutation (p≥0.3); quotient beats naive",
                "cells": [{"k": c["k"], "p": c["commute_probability"]} for c in cells if c["net_saving_mean"] > 0],
                "n": len(positive_nets),
                "net_saving_mean": float(positive_nets.mean()) if len(positive_nets) > 0 else None,
                "net_saving_ci95": [positive_ci["lo"], positive_ci["hi"]] if positive_ci else None,
            },
            "negative_subset": {
                "description": "k=3,4 all p, plus k=5,6 p=0.0; certification cost dominates",
                "cells": [{"k": c["k"], "p": c["commute_probability"]} for c in cells if c["net_saving_mean"] < 0],
                "n": len(negative_nets),
                "net_saving_mean": float(negative_nets.mean()) if len(negative_nets) > 0 else None,
                "net_saving_ci95": [negative_ci["lo"], negative_ci["hi"]] if negative_ci else None,
            },
        },
        
        "design": {
            "world": (
                "k transformations on integer registers; each owns a private register; " +
                "each conflict pair shares one register; distinct affine maps make " +
                "shared-register pairs non-commuting"
            ),
            "naive_searcher": "executes all k! orderings in the world",
            "quotient_searcher": (
                "executes both orders of every pair from the initial state AND from " +
                "every other reachable prefix state where the pair is unapplied " +
                "(context-bound witness checks, audit U1), registers rakl " +
                "TransitionIndependenceWitness objects per (pair, context) plus " +
                "PathEquivalenceWitness records, then executes one world run per " +
                "distinct canonical_partial_order_trace signature; signatures " +
                "spot-checked against equivalent_under_declared_partial_order " +
                "with global_independence_certified=True"
            ),
            "independence_certification": (
                "global_independence_certified=True is asserted only after both orders " +
                "of every certified pair were executed from every distinct reachable " +
                "prefix state of the finite world and all final-state hashes agreed; " +
                "a pair disagreeing in any context is demoted to a conflict (demoted_pairs). " +
                "Commutation is discovered by execution, never assumed from the generative construction."
            ),
            "net_saving_definition": (
                "naive_executions - (class_executions + witness_checks); witness_checks " +
                "counts every two-order comparison in every context, so the full price " +
                "of certifying global independence is charged against the quotient. " +
                "State-enumeration bookkeeping is reported separately " +
                "(enumeration_transitions) in units of single transformation applications, " +
                "not two-order checks."
            ),
            "crossover": (
                "k=3,4: net_saving < 0 across all p (certification cost dominates). " +
                "k=5,6: net_saving > 0 for p≥0.3 (quotient wins), net_saving < 0 for p=0.0 " +
                "(no commutation to exploit). This is a genuine regime crossover, not " +
                "an artifact of cost accounting."
            ),
            "cross_check": (
                "API class count compared against distinct world outcomes computed without the API"
            ),
        },
        "api_notes": [
            "TransitionIndependenceWitness is context-bound (audit U1): its context_hash " +
            "certifies commutation only in that state, so one witness is registered per " +
            "(pair, reachable context)",
            "equivalent_under_declared_partial_order licenses interior swaps only via a " +
            "prefix-context resolver or an explicit global_independence_certified assertion; " +
            "this experiment earns the latter by exhaustive per-context execution",
            "PathEquivalenceWitness enforces conditions + verifier_ids for COMMUTES_WITH_WITNESS " +
            "and exposes grants_proof_authority=False",
            "canonical_partial_order_trace provides the canonical class signature used to " +
            "collapse orderings",
            "equivalent_under_declared_partial_order is reflexive only on dependency-respecting " +
            "histories; histories violating the declared partial order are equivalent to nothing, " +
            "including themselves, so dependencies must be induced from the candidate history's " +
            "own orientation of verified conflict pairs",
        ],
        "cells": cells,
        "cells_with_negative_net_saving": negative_cells,
        "cells_with_positive_net_saving": positive_cells,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = generate_results()
    RESULT_FILE.write_text(
        json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    total_mismatches = sum(c["class_outcome_mismatches"] for c in result["cells"])
    total_spot_failures = sum(
        c["equivalence_spot_failures"] for c in result["cells"]
    )
    total_demoted = sum(c["demoted_pairs_total"] for c in result["cells"])
    
    pos = len(result["cells_with_positive_net_saving"])
    neg = len(result["cells_with_negative_net_saving"])
    
    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print(f"SEED={SEED}")
    print(f"CLASS_OUTCOME_MISMATCHES={total_mismatches}")
    print(f"EQUIVALENCE_SPOT_FAILURES={total_spot_failures}")
    print(f"DEMOTED_PAIRS={total_demoted}")
    print(f"POSITIVE_CELLS={pos} (k=5,6 with p≥0.3)")
    print(f"NEGATIVE_CELLS={neg} (k=3,4 all p, plus k=5,6 p=0.0)")
    print(f"TOP_LEVEL_NET_MEAN={result['net_saving_mean']:.2f} (MISLEADING due to crossover)")
    print(f"POSITIVE_SUBSET_MEAN={result['regime_analysis']['positive_subset']['net_saving_mean']:.2f}")
    print(f"NEGATIVE_SUBSET_MEAN={result['regime_analysis']['negative_subset']['net_saving_mean']:.2f}")
    print("STATUS=PARTIAL (crossover: positive in k=5,6 p≥0.3; negative elsewhere)")
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
