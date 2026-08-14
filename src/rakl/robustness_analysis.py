from __future__ import annotations

import math

from .objective_transfer_benchmark import Decision
from .objective_transfer_robustness import RobustTask, components, lexical_score


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


def merge_decisions(values) -> Decision:
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
    return merge_decisions(tuple(fields.values()))


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
