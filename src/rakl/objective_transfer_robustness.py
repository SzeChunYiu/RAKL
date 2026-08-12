from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from collections import deque
import hashlib
import itertools
import math
import random

from rakl.objective_transfer_benchmark import Decision, jaccard


FAMILIES = (
    "linear_systems",
    "pgm_dseparation",
    "algorithm_invariants",
    "causal_transport",
    "optimization",
    "local_global_gluing",
)

ITEM_TYPES = (
    "VALID_DISTANT_TRANSFER",
    "SEMANTIC_NEAR_MISS_INVALID_TRANSFER",
    "DIRECTION_REVERSED_INVALID",
    "BOUNDARY_QOI_MISMATCH",
    "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK",
    "VALID_NEAR_CONTROL",
    "INVALID_DISTANT_CONTROL",
)


@dataclass(frozen=True)
class RobustTask:
    item_id: str
    family: str
    item_type: str
    source_text: str
    target_text: str
    public: Mapping[str, Any]
    hidden_perturbation: str


@dataclass(frozen=True)
class ComponentAssessment:
    qoi: Decision
    boundary: Decision
    direction: Decision
    relation: Decision
    precondition: Decision
    effect: Decision

    @property
    def full(self) -> Decision:
        return merge_decisions((
            self.qoi,
            self.boundary,
            self.direction,
            self.relation,
            self.precondition,
            self.effect,
        ))

    @property
    def mechanism_only(self) -> Decision:
        return self.effect

    @property
    def relational_only(self) -> Decision:
        return merge_decisions((self.direction, self.relation))


def merge_decisions(values: Sequence[Decision]) -> Decision:
    if Decision.REJECT in values:
        return Decision.REJECT
    if Decision.CANNOT_CHECK in values:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT


def _status(condition: bool | None) -> Decision:
    if condition is None:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT if condition else Decision.REJECT


def _item_id(seed: int, index: int) -> str:
    return "rob-" + hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:16]


SEM_NEAR = {
    "linear_systems": ("linear state dynamics eigenvalue stability control", "linear state model eigenvalue stability control"),
    "pgm_dseparation": ("probabilistic graph dependency conditional independence", "probabilistic network dependency conditional independence"),
    "algorithm_invariants": ("ordered array binary search comparator", "sorted sequence binary search comparator"),
    "causal_transport": ("causal graph treatment outcome adjustment", "causal network exposure outcome adjustment"),
    "optimization": ("convex objective stationary point constraint", "optimization objective stationary point constraint"),
    "local_global_gluing": ("local assignment overlap compatibility", "local section overlap compatibility"),
}

SEM_FAR = {
    "linear_systems": ("aircraft attitude recurrence response", "ecological population recurrence response"),
    "pgm_dseparation": ("clinical symptom diagnostic network", "manufacturing fault dependency network"),
    "algorithm_invariants": ("library shelf lookup procedure", "genomic coordinate lookup procedure"),
    "causal_transport": ("drug exposure patient outcome", "policy intervention regional outcome"),
    "optimization": ("resource allocation optimum", "mechanical equilibrium design optimum"),
    "local_global_gluing": ("sensor patch calibration", "distributed database shard agreement"),
}


def _semantic_text(family: str, near: bool, rng: random.Random, salt: int) -> tuple[str, str]:
    left, right = (SEM_NEAR if near else SEM_FAR)[family]
    bridge = ["candidate", "transfer", "analysis"] if rng.random() < 0.5 else ["study", "mapping", "analysis"]
    return (
        " ".join(left.split() + bridge + [f"u{salt % 23}", f"k{rng.randrange(13)}"]),
        " ".join(right.split() + bridge + [f"v{salt % 29}", f"k{rng.randrange(13)}"]),
    )


def _near_for_type(item_type: str, k: int) -> bool:
    if item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER":
        return True
    if item_type == "INVALID_DISTANT_CONTROL":
        return False
    if item_type == "VALID_NEAR_CONTROL":
        return True
    if item_type == "VALID_DISTANT_TRANSFER":
        return False
    return k % 2 == 0


# ---------- linear systems ----------

def _linear_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    rho: float | None = 0.72
    qoi = "asymptotic_stability"
    boundary = "discrete_time_lti"
    direction: str | None = "source_to_target"
    mapping_rank: int | None = 2
    precondition: bool | None = True
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        rho = 1.08
        perturbation = "unstable_effect"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "finite_horizon_gain"
            perturbation = "qoi"
        else:
            boundary = "continuous_time_lti"
            perturbation = "time_regime"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            mapping_rank = None
            perturbation = "mapping_unknown"
        else:
            precondition = None
            perturbation = "precondition_unknown"
    source_text, target_text = _semantic_text("linear_systems", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "linear_systems",
        item_type,
        source_text,
        target_text,
        {
            "source": {"qoi": "asymptotic_stability", "boundary": "discrete_time_lti", "dimension": 2},
            "target": {"spectral_radius": rho, "qoi": qoi, "boundary": boundary, "lti_assumption": precondition},
            "map": {"direction": direction, "rank": mapping_rank, "required_rank": 2},
        },
        perturbation,
    )


def _linear_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(None if mp["rank"] is None else mp["rank"] >= mp["required_rank"])
    precondition = _status(tgt["lti_assumption"])
    rho = tgt["spectral_radius"]
    effect = _status(None if rho is None else rho < 1.0)
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


# ---------- d-separation ----------

def _ancestors(nodes: set[str], edges: list[tuple[str, str]]) -> set[str]:
    parents: dict[str, set[str]] = {}
    for a, b in edges:
        parents.setdefault(b, set()).add(a)
    out = set(nodes)
    queue = deque(nodes)
    while queue:
        node = queue.popleft()
        for parent in parents.get(node, ()):
            if parent not in out:
                out.add(parent)
                queue.append(parent)
    return out


def d_separated(edges: list[tuple[str, str]], x: str, y: str, conditioned: set[str]) -> bool:
    relevant = _ancestors({x, y} | conditioned, edges)
    undirected: dict[str, set[str]] = {node: set() for node in relevant}
    parents: dict[str, set[str]] = {node: set() for node in relevant}
    for a, b in edges:
        if a in relevant and b in relevant:
            undirected[a].add(b)
            undirected[b].add(a)
            parents[b].add(a)
    for child, ps in parents.items():
        for a, b in itertools.combinations(sorted(ps), 2):
            undirected[a].add(b)
            undirected[b].add(a)
    remaining = relevant - conditioned
    if x not in remaining or y not in remaining:
        return True
    queue = deque([x])
    seen = {x}
    while queue:
        node = queue.popleft()
        if node == y:
            return False
        for nxt in undirected.get(node, ()):
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return True


def _pgm_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    edges: list[list[str]] | None = [["X", "M"], ["M", "Y"]]
    conditioned: list[str] | None = ["M"]
    qoi = "conditional_independence"
    boundary = "observational_dag"
    direction: str | None = "source_to_target"
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        edges = [["X", "M"], ["Y", "M"]]
        conditioned = ["M"]  # conditioning on collider opens the path
        perturbation = "collider_conditioning"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "interventional_effect"
            perturbation = "qoi"
        else:
            boundary = "interventional_graph"
            perturbation = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            edges = None
            perturbation = "graph_unknown"
        else:
            conditioned = None
            perturbation = "conditioning_unknown"
    source_text, target_text = _semantic_text("pgm_dseparation", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "pgm_dseparation",
        item_type,
        source_text,
        target_text,
        {
            "source": {"qoi": "conditional_independence", "boundary": "observational_dag"},
            "target": {"edges": edges, "x": "X", "y": "Y", "conditioned": conditioned, "qoi": qoi, "boundary": boundary},
            "map": {"direction": direction, "role_map_complete": True},
        },
        perturbation,
    )


def _pgm_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(mp["role_map_complete"])
    precondition = _status(None if tgt["edges"] is None or tgt["conditioned"] is None else True)
    if tgt["edges"] is None or tgt["conditioned"] is None:
        effect = Decision.CANNOT_CHECK
    else:
        effect = _status(d_separated([tuple(e) for e in tgt["edges"]], tgt["x"], tgt["y"], set(tgt["conditioned"])))
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


# ---------- algorithm/data-structure invariants ----------

def binary_search(values: Sequence[int], target: int) -> bool:
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if values[mid] == target:
            return True
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


def _algorithm_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    values: list[int | None] = [1, 3, 5, 7, 9, 11, 13]
    target = 7
    qoi = "find_target"
    boundary = "ascending_total_order"
    direction: str | None = "source_to_target"
    comparator_consistent: bool | None = True
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        # target remains at the midpoint, so binary search appears to work while
        # the ordering precondition is actually false.
        values = [13, 1, 11, 7, 3, 9, 5]
        perturbation = "unsorted_precondition"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "first_occurrence"
            perturbation = "qoi"
        else:
            boundary = "descending_total_order"
            perturbation = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            values[5] = None
            perturbation = "array_unknown"
        else:
            comparator_consistent = None
            perturbation = "comparator_unknown"
    source_text, target_text = _semantic_text("algorithm_invariants", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "algorithm_invariants",
        item_type,
        source_text,
        target_text,
        {
            "source": {"algorithm": "binary_search", "qoi": "find_target", "boundary": "ascending_total_order"},
            "target": {"values": values, "target": target, "qoi": qoi, "boundary": boundary, "comparator_consistent": comparator_consistent},
            "map": {"direction": direction, "algorithm": "binary_search"},
        },
        perturbation,
    )


def _algorithm_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(mp["algorithm"] == "binary_search")
    values = tgt["values"]
    if any(v is None for v in values) or tgt["comparator_consistent"] is None:
        precondition = Decision.CANNOT_CHECK
    else:
        precondition = _status(tgt["comparator_consistent"] and list(values) == sorted(values))
    if any(v is None for v in values):
        effect = Decision.CANNOT_CHECK
    else:
        effect = _status(binary_search([int(v) for v in values], int(tgt["target"])))
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


# ---------- causal transport ----------

def _remove_outgoing(edges: list[tuple[str, str]], node: str) -> list[tuple[str, str]]:
    return [(a, b) for a, b in edges if a != node]


def _causal_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    edges: list[list[str]] | None = [["U", "X"], ["U", "Y"], ["X", "Y"]]
    adjustment: list[str] | None = ["U"]
    positivity: bool | None = True
    transport_invariant: bool | None = True
    qoi = "total_intervention_effect"
    boundary = "observational_adjustment_transport"
    direction: str | None = "source_to_target"
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        adjustment = []  # leaves U backdoor open
        perturbation = "unblocked_backdoor"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "associational_contrast"
            perturbation = "qoi"
        else:
            boundary = "selected_population_without_transport"
            perturbation = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            positivity = None
            perturbation = "positivity_unknown"
        else:
            transport_invariant = None
            perturbation = "transport_unknown"
    source_text, target_text = _semantic_text("causal_transport", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "causal_transport",
        item_type,
        source_text,
        target_text,
        {
            "source": {"qoi": "total_intervention_effect", "boundary": "observational_adjustment_transport"},
            "target": {"edges": edges, "x": "X", "y": "Y", "adjustment": adjustment, "positivity": positivity, "transport_invariant": transport_invariant, "qoi": qoi, "boundary": boundary},
            "map": {"direction": direction, "roles_complete": True},
        },
        perturbation,
    )


def _causal_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(mp["roles_complete"])
    if tgt["positivity"] is None or tgt["transport_invariant"] is None:
        precondition = Decision.CANNOT_CHECK
    else:
        precondition = _status(tgt["positivity"] and tgt["transport_invariant"])
    if tgt["edges"] is None or tgt["adjustment"] is None:
        effect = Decision.CANNOT_CHECK
    else:
        backdoor = _remove_outgoing([tuple(e) for e in tgt["edges"]], tgt["x"])
        effect = _status(d_separated(backdoor, tgt["x"], tgt["y"], set(tgt["adjustment"])))
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


# ---------- optimization ----------

def _optimization_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    a: float | None = 2.0
    b: float | None = -4.0
    candidate: float | None = 2.0
    lower: float | None = 0.0
    upper: float | None = 4.0
    cq: bool | None = True
    qoi = "global_minimum"
    boundary = "convex_box_constrained"
    direction: str | None = "source_to_target"
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        lower, upper = 3.0, 5.0  # stationary x=2 is infeasible
        perturbation = "infeasible_stationary"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "stationary_point"
            perturbation = "qoi"
        else:
            boundary = "nonconvex_unregistered"
            perturbation = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            upper = None
            perturbation = "constraint_unknown"
        else:
            cq = None
            perturbation = "cq_unknown"
    source_text, target_text = _semantic_text("optimization", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "optimization",
        item_type,
        source_text,
        target_text,
        {
            "source": {"qoi": "global_minimum", "boundary": "convex_box_constrained"},
            "target": {"a": a, "b": b, "candidate": candidate, "lower": lower, "upper": upper, "constraint_qualification": cq, "qoi": qoi, "boundary": boundary},
            "map": {"direction": direction, "variable_mapping_complete": True},
        },
        perturbation,
    )


def _optimization_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(mp["variable_mapping_complete"])
    vals = (tgt["a"], tgt["b"], tgt["candidate"], tgt["lower"], tgt["upper"], tgt["constraint_qualification"])
    if any(v is None for v in vals):
        precondition = Decision.CANNOT_CHECK
    else:
        precondition = _status(bool(tgt["constraint_qualification"]) and float(tgt["a"]) > 0 and float(tgt["lower"]) <= float(tgt["candidate"]) <= float(tgt["upper"]))
    if tgt["a"] is None or tgt["b"] is None or tgt["candidate"] is None:
        effect = Decision.CANNOT_CHECK
    else:
        gradient = float(tgt["a"]) * float(tgt["candidate"]) + float(tgt["b"])
        effect = _status(abs(gradient) < 1e-12)
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


# ---------- local/global gluing ----------

def global_parity_solution(equations: Sequence[tuple[str, str, int]]) -> bool:
    variables = sorted({v for a, b, _ in equations for v in (a, b)})
    for bits in itertools.product((0, 1), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if all((assignment[a] ^ assignment[b]) == parity for a, b, parity in equations):
            return True
    return False


def pairwise_parity_compatible(equations: Sequence[tuple[str, str, int]]) -> bool:
    return all(global_parity_solution(pair) for pair in itertools.combinations(equations, 2))


def _gluing_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> RobustTask:
    equations: list[list[Any]] | None = [["x", "y", 0], ["y", "z", 0], ["x", "z", 0]]
    qoi = "global_section"
    boundary = "exact_overlap"
    direction: str | None = "source_to_target"
    interface_complete: bool | None = True
    perturbation = "none"
    if item_type in {"SEMANTIC_NEAR_MISS_INVALID_TRANSFER", "INVALID_DISTANT_CONTROL"}:
        equations = [["x", "y", 0], ["y", "z", 0], ["x", "z", 1]]
        perturbation = "global_obstruction"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        direction = "target_to_source"
        perturbation = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "pairwise_overlap"
            perturbation = "qoi"
        else:
            boundary = "approximate_overlap"
            perturbation = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            equations = None
            perturbation = "equations_unknown"
        else:
            interface_complete = None
            perturbation = "interface_unknown"
    source_text, target_text = _semantic_text("local_global_gluing", near, rng, index)
    return RobustTask(
        _item_id(seed, index),
        "local_global_gluing",
        item_type,
        source_text,
        target_text,
        {
            "source": {"qoi": "global_section", "boundary": "exact_overlap"},
            "target": {"equations": equations, "qoi": qoi, "boundary": boundary, "interface_complete": interface_complete},
            "map": {"direction": direction, "chart_mapping_complete": True},
        },
        perturbation,
    )


def _gluing_components(task: RobustTask) -> ComponentAssessment:
    p = task.public
    tgt, mp = p["target"], p["map"]
    qoi = _status(tgt["qoi"] == p["source"]["qoi"])
    boundary = _status(tgt["boundary"] == p["source"]["boundary"])
    direction = _status(None if mp["direction"] is None else mp["direction"] == "source_to_target")
    relation = _status(mp["chart_mapping_complete"])
    precondition = _status(tgt["interface_complete"])
    if tgt["equations"] is None:
        effect = Decision.CANNOT_CHECK
    else:
        equations = [tuple(eq) for eq in tgt["equations"]]
        # Mechanism-level local compatibility is necessary but not sufficient.
        # Full gold below also requires a global section via precondition override.
        effect = _status(pairwise_parity_compatible(equations))
        if effect is Decision.ACCEPT and not global_parity_solution(equations):
            # encode the higher-order obstruction as the load-bearing applicability
            # precondition rather than silently changing the mechanism projection.
            precondition = Decision.REJECT
    return ComponentAssessment(qoi, boundary, direction, relation, precondition, effect)


BUILDERS = {
    "linear_systems": _linear_task,
    "pgm_dseparation": _pgm_task,
    "algorithm_invariants": _algorithm_task,
    "causal_transport": _causal_task,
    "optimization": _optimization_task,
    "local_global_gluing": _gluing_task,
}

COMPONENTS = {
    "linear_systems": _linear_components,
    "pgm_dseparation": _pgm_components,
    "algorithm_invariants": _algorithm_components,
    "causal_transport": _causal_components,
    "optimization": _optimization_components,
    "local_global_gluing": _gluing_components,
}


def components(task: RobustTask) -> ComponentAssessment:
    return COMPONENTS[task.family](task)


def verify(task: RobustTask) -> Decision:
    return components(task).full


def mechanism_predict(task: RobustTask) -> Decision:
    return components(task).mechanism_only


def relational_predict(task: RobustTask) -> Decision:
    return components(task).relational_only


def lexical_score(task: RobustTask) -> float:
    return jaccard(task.source_text, task.target_text)


def generate(seed: int, n_per_cell: int) -> list[RobustTask]:
    rng = random.Random(seed)
    out: list[RobustTask] = []
    index = 0
    for family in FAMILIES:
        builder = BUILDERS[family]
        for item_type in ITEM_TYPES:
            count = n_per_cell * (2 if item_type in {"VALID_DISTANT_TRANSFER", "VALID_NEAR_CONTROL"} else 1)
            for k in range(count):
                out.append(builder(seed, index, item_type, _near_for_type(item_type, k), rng))
                index += 1
    rng.shuffle(out)
    return out


def mutate_hidden_metadata(task: RobustTask, marker: str = "fabricated-hidden-marker") -> RobustTask:
    return RobustTask(
        task.item_id,
        task.family,
        task.item_type,
        task.source_text,
        task.target_text,
        task.public,
        marker,
    )
