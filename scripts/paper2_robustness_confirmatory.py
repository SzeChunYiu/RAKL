from __future__ import annotations

from collections import Counter
import json
import math
import random
import statistics

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    RobustTask,
    generate,
    lexical_score,
    mechanism_predict,
    relational_predict,
    verify,
)
from scripts.paper2_robustness_development import (
    binary_probability,
    brier,
    lexical_predict,
    twin_predict,
)

CONFIRMATORY_SEED = 2026081212
N_PER_CELL = 15
EXPECTED_N = 810
FROZEN_LEXICAL_THRESHOLD = 0.40064102564102566
REGISTERED_MDE = 0.05
BOOTSTRAP_REPS = 20_000
BOOTSTRAP_SEED = 2026081212001


def _accuracy(tasks: list[RobustTask], predictor) -> float:
    return sum(predictor(task) is verify(task) for task in tasks) / len(tasks)


def _binary_loss(task: RobustTask, predictor) -> float:
    gold = verify(task)
    if gold is Decision.CANNOT_CHECK:
        raise ValueError("binary Brier is defined only for decidable tasks")
    return brier(binary_probability(predictor(task)), gold)


def _arm_summary(tasks: list[RobustTask], predictor) -> dict[str, float]:
    valid = [task for task in tasks if verify(task) is Decision.ACCEPT]
    invalid = [task for task in tasks if verify(task) is Decision.REJECT]
    unknown = [task for task in tasks if verify(task) is Decision.CANNOT_CHECK]
    return {
        "exact3": _accuracy(tasks, predictor),
        "valid_accept": sum(predictor(task) is Decision.ACCEPT for task in valid) / len(valid),
        "invalid_false_accept": sum(predictor(task) is Decision.ACCEPT for task in invalid) / len(invalid),
        "unknown_abstain": sum(predictor(task) is Decision.CANNOT_CHECK for task in unknown) / len(unknown),
    }


def _paired_bootstrap_interval(differences: list[float], reps: int, seed: int) -> tuple[float, float]:
    if not differences:
        raise ValueError("paired bootstrap requires differences")
    rng = random.Random(seed)
    n = len(differences)
    draws = []
    for _ in range(reps):
        draws.append(sum(rng.choices(differences, k=n)) / n)
    draws.sort()
    lo = draws[max(0, math.floor(0.025 * reps))]
    hi = draws[min(reps - 1, math.ceil(0.975 * reps) - 1)]
    return lo, hi


def _two_sided_sign_p(positive: int, total: int) -> float:
    if total <= 0:
        raise ValueError("sign test requires families")
    extreme = min(positive, total - positive)
    tail = sum(math.comb(total, k) for k in range(extreme + 1)) / (2**total)
    return min(1.0, 2.0 * tail)


def summarize(
    seed: int = CONFIRMATORY_SEED,
    n_per_cell: int = N_PER_CELL,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    bootstrap_seed: int = BOOTSTRAP_SEED,
) -> dict[str, object]:
    tasks = generate(seed, n_per_cell)
    if seed == CONFIRMATORY_SEED and len(tasks) != EXPECTED_N:
        raise ValueError(f"confirmatory task count mismatch: {len(tasks)} != {EXPECTED_N}")

    arms = {
        "lexical": lambda task: lexical_predict(task, FROZEN_LEXICAL_THRESHOLD),
        "relational": relational_predict,
        "mechanism": mechanism_predict,
        "twin": twin_predict,
        "full": verify,
    }
    arm_result = {name: _arm_summary(tasks, predictor) for name, predictor in arms.items()}

    decidable = [task for task in tasks if verify(task) is not Decision.CANNOT_CHECK]
    paired_differences = [
        _binary_loss(task, mechanism_predict) - _binary_loss(task, verify)
        for task in decidable
    ]
    paired_gain = statistics.mean(paired_differences)
    interval = _paired_bootstrap_interval(paired_differences, bootstrap_reps, bootstrap_seed)

    family_result: dict[str, dict[str, float]] = {}
    family_positive = 0
    safety_reasons: list[str] = []
    for family in FAMILIES:
        subset = [task for task in tasks if task.family == family]
        family_decidable = [task for task in subset if verify(task) is not Decision.CANNOT_CHECK]
        family_differences = [
            _binary_loss(task, mechanism_predict) - _binary_loss(task, verify)
            for task in family_decidable
        ]
        gain = statistics.mean(family_differences)
        if gain > 0:
            family_positive += 1

        full = _arm_summary(subset, verify)
        mechanism = _arm_summary(subset, mechanism_predict)
        valid_retention_delta = full["valid_accept"] - mechanism["valid_accept"]
        invalid_delta = full["invalid_false_accept"] - mechanism["invalid_false_accept"]
        if valid_retention_delta < -0.02 - 1e-12:
            safety_reasons.append(f"VALID_RETENTION_HARM:{family}")
        if invalid_delta > 1e-12:
            safety_reasons.append(f"INVALID_FALSE_ACCEPT_HARM:{family}")

        family_result[family] = {
            "n": len(subset),
            "decidable_n": len(family_decidable),
            "full_minus_mechanism_brier_gain": gain,
            "full_exact3": full["exact3"],
            "mechanism_exact3": mechanism["exact3"],
            "full_valid_accept": full["valid_accept"],
            "mechanism_valid_accept": mechanism["valid_accept"],
            "valid_retention_delta_full_minus_mechanism": valid_retention_delta,
            "full_invalid_false_accept": full["invalid_false_accept"],
            "mechanism_invalid_false_accept": mechanism["invalid_false_accept"],
            "invalid_false_accept_delta_full_minus_mechanism": invalid_delta,
            "full_unknown_abstain": full["unknown_abstain"],
            "mechanism_unknown_abstain": mechanism["unknown_abstain"],
        }

    sign_p = _two_sided_sign_p(family_positive, len(FAMILIES))
    reasons = list(safety_reasons)
    if family_positive != len(FAMILIES):
        reasons.append(f"FAMILY_RESIDUAL_NOT_POSITIVE_IN_ALL_SIX:{family_positive}/{len(FAMILIES)}")
    if abs(sign_p - 0.03125) > 1e-12:
        reasons.append(f"FAMILY_SIGN_TEST_GATE_FAIL:p={sign_p}")
    if paired_gain < REGISTERED_MDE - 1e-12:
        reasons.append(f"PAIRED_BRIER_BELOW_MDE:{paired_gain}")
    if interval[0] <= 0:
        reasons.append(f"PAIRED_BRIER_INTERVAL_INCLUDES_ZERO:{interval[0]}")
    if arm_result["full"]["valid_accept"] < arm_result["mechanism"]["valid_accept"] - 0.02 - 1e-12:
        reasons.append("AGGREGATE_VALID_RETENTION_HARM")
    if arm_result["full"]["invalid_false_accept"] >= arm_result["mechanism"]["invalid_false_accept"] - 1e-12:
        reasons.append("AGGREGATE_INVALID_FALSE_ACCEPT_NOT_LOWER")

    broad_supported = not reasons
    return {
        "schema": "paper2-robustness-confirmatory-v1",
        "seed": seed,
        "n_per_cell": n_per_cell,
        "n": len(tasks),
        "development_selected_lexical_threshold": FROZEN_LEXICAL_THRESHOLD,
        "gold_counts": dict(Counter(verify(task).value for task in tasks)),
        "arms": arm_result,
        "primary_paired_binary_brier": {
            "mechanism_minus_full_gain": paired_gain,
            "registered_mde": REGISTERED_MDE,
            "bootstrap_reps": bootstrap_reps,
            "bootstrap_seed": bootstrap_seed,
            "bootstrap_95pct": [interval[0], interval[1]],
        },
        "family": family_result,
        "family_sign_test": {
            "positive_families": family_positive,
            "total_families": len(FAMILIES),
            "exact_two_sided_p": sign_p,
        },
        "broad_known_world_robustness_supported": broad_supported,
        "gate_reasons": reasons,
        "claim_boundary": (
            "KNOWN_WORLD_EXACT_VERIFIER_ROBUSTNESS_ONLY; does not establish learned witness "
            "extraction, frontier-model superiority, natural-domain transfer, independent-human "
            "validation, downstream action utility, or universal scientific applicability"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2, sort_keys=True))
