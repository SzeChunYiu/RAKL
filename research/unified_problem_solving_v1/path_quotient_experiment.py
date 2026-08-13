"""Path-quotient known-world experiment.

Random known worlds in which a solution is a SET of k transformations, of
which a random subset of pairs commute (pairwise-independence graph, edge
probability p). A naive sequential searcher executes every ordering of the
set in the world. A quotient-aware searcher (a) pays an explicit WITNESS
cost -- one pairwise-commutation check per unordered pair, executed in the
world and registered through ``rakl.path_equivalence.PathEquivalenceWitness``
-- and (b) executes only one world run per distinct equivalence class, where
class identity is computed THROUGH the rakl path-equivalence API
(``canonical_partial_order_trace`` signatures, spot-checked against
``equivalent_under_declared_partial_order``), never through a private
reimplementation of the quotient.

Honesty notes (also recorded in the output JSON):
- The world realizes commutation physically: each transformation applies a
  distinct affine map to its registers; a conflict pair shares a register,
  a commuting pair does not. Commutation is DISCOVERED by executing both
  orders and comparing state hashes, not read off the generative graph.
- Class counts are cross-checked against distinct world outcomes, which are
  computed independently of the API. Mismatches are reported, not hidden.
- Net saving = naive_executions - (class_executions + witness_checks) and
  is reported per cell including the fraction of instances where it is
  NEGATIVE (quotienting did not pay).

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
CLAIM_BOUNDARY = (
    "development known-world evidence; grants no scientific or "
    "method-promotion authority"
)


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
        self.executions += 1
        state = dict(self.initial_state)
        for index in ordering:
            self.apply(state, index)
        return _state_hash(state)


def build_instance(k: int, p: float, rng: random.Random) -> KnownWorld:
    conflict = frozenset(
        (a, b) for a, b in combinations(range(k), 2) if rng.random() >= p
    )
    return KnownWorld(k, conflict)


def witness_phase(
    world: KnownWorld, instance_label: str
) -> tuple[frozenset[tuple[int, int]], list[PathEquivalenceWitness], int]:
    """Check every unordered pair by two-order execution; register witnesses.

    Returns (verified conflict pairs, registered witnesses, check count).
    The conflict set handed to the quotient searcher comes ONLY from these
    executed checks, never from the generative graph.
    """
    checks = 0
    witnesses: list[PathEquivalenceWitness] = []
    conflicts: set[tuple[int, int]] = set()
    source_hash = _state_hash(world.initial_state)
    for a, b in combinations(range(world.k), 2):
        checks += 1
        forward = world.execute((a, b))
        backward = world.execute((b, a))
        if forward == backward:
            witnesses.append(
                PathEquivalenceWitness(
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
            )
        else:
            conflicts.add((a, b))
    return frozenset(conflicts), witnesses, checks


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
    # Witness phase: pay for every pairwise commutation check up front.
    conflicts, witnesses, witness_checks = witness_phase(world, label)

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
    # equivalence predicate (both positive and negative directions).
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
            left_hist, right_hist, left_deps
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
) -> tuple[float, float]:
    resampled = rng.choice(values, size=(BOOTSTRAP_RESAMPLES, len(values)))
    means = resampled.mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)


def run_cell(k: int, p: float) -> dict:
    cell_seed = SEED * 1_000_000 + k * 10_000 + int(round(p * 10)) * 100
    rng = random.Random(cell_seed)
    rows = [run_instance(k, p, i, rng) for i in range(N_INSTANCES)]

    ratios = np.array([row["reduction_ratio"] for row in rows], dtype=float)
    nets = np.array([row["net_saving"] for row in rows], dtype=float)
    classes = np.array([row["classes"] for row in rows], dtype=float)

    boot_rng = np.random.default_rng([SEED, k, int(round(p * 10))])
    ratio_ci = bootstrap_ci(ratios, boot_rng)
    net_ci = bootstrap_ci(nets, boot_rng)

    return {
        "k": k,
        "commute_probability": p,
        "n_instances": N_INSTANCES,
        "naive_executions": factorial(k),
        "witness_checks_per_instance": k * (k - 1) // 2,
        "classes_mean": float(classes.mean()),
        "classes_min": float(classes.min()),
        "classes_max": float(classes.max()),
        "reduction_ratio_mean": float(ratios.mean()),
        "reduction_ratio_ci95": list(ratio_ci),
        "net_saving_mean": float(nets.mean()),
        "net_saving_ci95": list(net_ci),
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
    }


def generate_results() -> dict:
    cells = [run_cell(k, p) for k in K_VALUES for p in P_VALUES]
    negative_cells = [
        {"k": cell["k"], "p": cell["commute_probability"],
         "net_saving_mean": cell["net_saving_mean"],
         "negative_net_fraction": cell["negative_net_fraction"]}
        for cell in cells
        if cell["negative_net_fraction"] > 0.0
    ]
    return {
        "schema_version": "orion-path-quotient-savings-v1",
        "status": "DEVELOPMENT_KNOWN_WORLD_MECHANISM_EVIDENCE_ONLY",
        "seed": SEED,
        "n_instances_per_cell": N_INSTANCES,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "claim_boundary": CLAIM_BOUNDARY,
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        "design": {
            "world": (
                "k transformations on integer registers; each owns a private "
                "register; each conflict pair shares one register; distinct "
                "affine maps make shared-register pairs non-commuting"
            ),
            "naive_searcher": "executes all k! orderings in the world",
            "quotient_searcher": (
                "executes both orders of every pair (witness checks), "
                "registers rakl PathEquivalenceWitness objects for verified "
                "commuting pairs, then executes one world run per distinct "
                "canonical_partial_order_trace signature; signatures spot-"
                "checked against equivalent_under_declared_partial_order"
            ),
            "net_saving_definition": (
                "naive_executions - (class_executions + witness_checks)"
            ),
            "cross_check": (
                "API class count compared against distinct world outcomes "
                "computed without the API"
            ),
        },
        "api_notes": [
            "PathEquivalenceWitness enforces conditions + verifier_ids for "
            "COMMUTES_WITH_WITNESS and exposes grants_proof_authority=False",
            "canonical_partial_order_trace provides the canonical class "
            "signature used to collapse orderings",
            "equivalent_under_declared_partial_order is reflexive only on "
            "dependency-respecting histories; histories violating the "
            "declared partial order are equivalent to nothing, including "
            "themselves, so dependencies must be induced from the candidate "
            "history's own orientation of verified conflict pairs",
        ],
        "cells": cells,
        "cells_with_negative_net_saving": negative_cells,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = generate_results()
    RESULT_FILE.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    total_mismatches = sum(c["class_outcome_mismatches"] for c in result["cells"])
    total_spot_failures = sum(
        c["equivalence_spot_failures"] for c in result["cells"]
    )
    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print(f"SEED={SEED}")
    print(f"CLASS_OUTCOME_MISMATCHES={total_mismatches}")
    print(f"EQUIVALENCE_SPOT_FAILURES={total_spot_failures}")
    print(
        "NEGATIVE_NET_CELLS="
        + json.dumps(result["cells_with_negative_net_saving"])
    )
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
