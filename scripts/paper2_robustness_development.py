from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
import random
import statistics

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    RobustTask,
    components,
    generate,
    lexical_score,
    mechanism_predict,
    relational_predict,
    verify,
)

DEVELOPMENT_SEED = 2026081211
REGISTERED_MDE = 0.05

PERTURBATION_COMPONENT = {
    "unstable_effect": "effect",
    "collider_conditioning": "effect",
    "unsorted_precondition": "precondition",
    "unblocked_backdoor": "effect",
    "infeasible_stationary": "precondition",
    "global_obstruction": "precondition",
    "direction": "direction",
    "qoi": "qoi",
    "time_regime": "boundary",
    "boundary": "boundary",
    "mapping_unknown": "relation",
    "graph_unknown": "effect",
    "conditioning_unknown": "effect",
    "array_unknown": "effect",
    "comparator_unknown": "precondition",
    "positivity_unknown": "precondition",
    "transport_unknown": "precondition",
    "constraint_unknown": "precondition",
    "cq_unknown": "precondition",
    "equations_unknown": "effect",
    "interface_unknown": "precondition",
}


def merge(values):
    if Decision.REJECT in values:
        return Decision.REJECT
    if Decision.CANNOT_CHECK in values:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT


def twin_predict(task: RobustTask) -> Decision:
    assessment = components(task)
    fields = {
        "qoi": assessment.qoi,
        "boundary": assessment.boundary,
        "direction": assessment.direction,
        "relation": assessment.relation,
        "precondition": assessment.precondition,
        "effect": assessment.effect,
    }
    omitted = PERTURBATION_COMPONENT.get(task.hidden_perturbation)
    if omitted is not None:
        fields.pop(omitted)
    return merge(tuple(fields.values()))


def fit_lexical_threshold(tasks: list[RobustTask]) -> float:
    rows = [(lexical_score(task), verify(task)) for task in tasks if verify(task) is not Decision.CANNOT_CHECK]
    values = sorted(set(score for score, _ in rows))
    candidates = [0.0] + [(a + b) / 2 for a, b in zip(values, values[1:])] + [1.0]
    best = None
    for threshold in candidates:
        accuracy = sum(
            (Decision.ACCEPT if score >= threshold else Decision.REJECT) is gold
            for score, gold in rows
        ) / len(rows)
        candidate = (accuracy, -abs(threshold - statistics.median(values)), threshold)
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    return best[2]


def lexical_predict(task: RobustTask, threshold: float) -> Decision:
    return Decision.ACCEPT if lexical_score(task) >= threshold else Decision.REJECT


def binary_probability(decision: Decision) -> float:
    return 0.98 if decision is Decision.ACCEPT else 0.02 if decision is Decision.REJECT else 0.50


def lexical_probability(task: RobustTask, threshold: float, temperature: float = 0.08) -> float:
    x = max(-20.0, min(20.0, (lexical_score(task) - threshold) / temperature))
    return 1.0 / (1.0 + math.exp(-x))


def brier(probability: float, gold: Decision) -> float:
    y = 1.0 if gold is Decision.ACCEPT else 0.0
    return (probability - y) ** 2


def accuracy(tasks, predictor):
    return sum(predictor(task) is verify(task) for task in tasks) / len(tasks)


def semantic_permutation(tasks: list[RobustTask], seed: int, reps: int = 4000):
    result = {}
    for offset, family in enumerate(FAMILIES):
        accept = [lexical_score(task) for task in tasks if task.family == family and verify(task) is Decision.ACCEPT]
        reject = [lexical_score(task) for task in tasks if task.family == family and verify(task) is Decision.REJECT]
        observed = abs(statistics.mean(accept) - statistics.mean(reject))
        values = accept + reject
        n_accept = len(accept)
        rng = random.Random(seed + offset)
        exceed = 0
        for _ in range(reps):
            shuffled = values[:]
            rng.shuffle(shuffled)
            diff = abs(statistics.mean(shuffled[:n_accept]) - statistics.mean(shuffled[n_accept:]))
            exceed += diff >= observed - 1e-15
        result[family] = {
            "accept_mean": statistics.mean(accept),
            "reject_mean": statistics.mean(reject),
            "mean_diff": statistics.mean(accept) - statistics.mean(reject),
            "permutation_p": (exceed + 1) / (reps + 1),
        }
    return result


def summarize(n_per_cell: int = 24) -> dict:
    tasks = generate(DEVELOPMENT_SEED, n_per_cell)
    threshold = fit_lexical_threshold(tasks)
    decidable = [task for task in tasks if verify(task) is not Decision.CANNOT_CHECK]
    valid = [task for task in tasks if verify(task) is Decision.ACCEPT]
    invalid = [task for task in tasks if verify(task) is Decision.REJECT]
    unknown = [task for task in tasks if verify(task) is Decision.CANNOT_CHECK]

    arms = {
        "lexical": lambda task: lexical_predict(task, threshold),
        "relational": relational_predict,
        "mechanism": mechanism_predict,
        "twin": twin_predict,
        "full": verify,
    }
    arm_result = {}
    for name, predictor in arms.items():
        arm_result[name] = {
            "exact3": accuracy(tasks, predictor),
            "valid_accept": sum(predictor(task) is Decision.ACCEPT for task in valid) / len(valid),
            "invalid_false_accept": sum(predictor(task) is Decision.ACCEPT for task in invalid) / len(invalid),
            "unknown_abstain": sum(predictor(task) is Decision.CANNOT_CHECK for task in unknown) / len(unknown),
        }

    paired = []
    lexical_loss = []
    mechanism_loss = []
    full_loss = []
    for task in decidable:
        gold = verify(task)
        lp = lexical_probability(task, threshold)
        mp = binary_probability(mechanism_predict(task))
        fp = binary_probability(verify(task))
        ll = brier(lp, gold)
        ml = brier(mp, gold)
        fl = brier(fp, gold)
        lexical_loss.append(ll)
        mechanism_loss.append(ml)
        full_loss.append(fl)
        paired.append(ml - fl)

    sigma = statistics.stdev(paired)
    z_alpha = 1.95996398454
    z_power = 0.84162123357
    required_decidable = math.ceil(((z_alpha + z_power) * sigma / REGISTERED_MDE) ** 2)
    known_fraction = len(decidable) / len(tasks)
    required_total = math.ceil(required_decidable / known_fraction)
    # Generator contributes 54*n_per_cell cases; round upward to that complete
    # family/cell granularity for the future confirmatory freeze.
    confirmatory_n_per_cell = max(1, math.ceil(required_total / 54))
    confirmatory_total = 54 * confirmatory_n_per_cell

    family = {}
    for family_name in FAMILIES:
        subset = [task for task in tasks if task.family == family_name]
        family[family_name] = {
            "n": len(subset),
            "full_exact3": accuracy(subset, verify),
            "mechanism_exact3": accuracy(subset, mechanism_predict),
            "full_minus_mechanism_exact3": accuracy(subset, verify) - accuracy(subset, mechanism_predict),
            "mechanism_invalid_false_accept": sum(
                mechanism_predict(task) is Decision.ACCEPT
                for task in subset
                if verify(task) is Decision.REJECT
            ) / sum(verify(task) is Decision.REJECT for task in subset),
        }

    return {
        "schema": "paper2-robustness-development-v1",
        "seed": DEVELOPMENT_SEED,
        "n_per_cell": n_per_cell,
        "n": len(tasks),
        "gold_counts": dict(Counter(verify(task).value for task in tasks)),
        "lexical_threshold": threshold,
        "lexical_decidable_accuracy": sum(
            lexical_predict(task, threshold) is verify(task) for task in decidable
        ) / len(decidable),
        "arms": arm_result,
        "paired_binary_brier": {
            "lexical": statistics.mean(lexical_loss),
            "mechanism": statistics.mean(mechanism_loss),
            "full": statistics.mean(full_loss),
            "mechanism_minus_full": statistics.mean(paired),
            "sigma_d": sigma,
        },
        "semantic_decorrelation": semantic_permutation(tasks, DEVELOPMENT_SEED + 700),
        "family": family,
        "registered_mde": REGISTERED_MDE,
        "required_decidable_n": required_decidable,
        "required_total_before_rounding": required_total,
        "confirmatory_n_per_cell_candidate": confirmatory_n_per_cell,
        "confirmatory_total_candidate": confirmatory_total,
        "claim_boundary": "DEVELOPMENT_ONLY; confirmatory seed/outcomes not accessed",
    }


if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2, sort_keys=True))
