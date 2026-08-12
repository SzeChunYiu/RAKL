from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any, Callable

from rakl.objective_transfer_benchmark import Decision, Task, generate, verify


SQ2_DEVELOPMENT_SEED = 20260812981
PAPER2_CONFIRMATORY_SEED_DO_NOT_USE = 2026081202


# Exact code-level public dependencies of the frozen family verifiers.  This is used only
# to score the intervention audit, not to decide which coordinates the audit retains.
EXACT_REQUIRED_PATHS: dict[str, frozenset[str]] = {
    "flow": frozenset(
        {
            "public.source.path",
            "public.source.demand",
            "public.target.edges",
            "public.target.qoi",
            "public.target.mode",
            "public.mapping",
        }
    ),
    "logic": frozenset(
        {
            "public.source.facts",
            "public.source.query",
            "public.target.facts",
            "public.target.rules",
            "public.target.qoi",
            "public.target.boundary",
            "public.mapping",
        }
    ),
    "units": frozenset(
        {
            "public.target.input_dims",
            "public.target.operation",
            "public.target.output_dim",
            "public.target.qoi",
            "public.target.boundary",
            "public.target.denominator_nonzero",
        }
    ),
    "state": frozenset(
        {
            "public.target.transitions",
            "public.target.start",
            "public.target.goal",
            "public.target.qoi",
            "public.target.boundary",
            "public.mapping",
            "public.candidate_actions",
        }
    ),
}


ALL_CANDIDATE_PATHS: dict[str, tuple[str, ...]] = {
    "flow": (
        "source_text",
        "target_text",
        "public.source.edges",
        "public.source.path",
        "public.source.demand",
        "public.source.qoi",
        "public.source.mode",
        "public.target.edges",
        "public.target.qoi",
        "public.target.mode",
        "public.mapping",
    ),
    "logic": (
        "source_text",
        "target_text",
        "public.source.facts",
        "public.source.rules",
        "public.source.query",
        "public.target.facts",
        "public.target.rules",
        "public.target.qoi",
        "public.target.boundary",
        "public.mapping",
    ),
    "units": (
        "source_text",
        "target_text",
        "public.source.input_dims",
        "public.source.operation",
        "public.source.output_dim",
        "public.source.qoi",
        "public.source.boundary",
        "public.target.input_dims",
        "public.target.operation",
        "public.target.output_dim",
        "public.target.qoi",
        "public.target.boundary",
        "public.target.denominator_nonzero",
    ),
    "state": (
        "source_text",
        "target_text",
        "public.source.start",
        "public.source.goal",
        "public.source.actions",
        "public.source.qoi",
        "public.source.boundary",
        "public.target.transitions",
        "public.target.start",
        "public.target.goal",
        "public.target.qoi",
        "public.target.boundary",
        "public.mapping",
        "public.candidate_actions",
    ),
}


def _adversarial_value(family: str, path: str, value: Any) -> Any:
    """Registered type-safe intervention intended to expose decision dependence."""

    if path in {"source_text", "target_text"}:
        return "INTERVENTION_SEMANTIC_TEXT_ONLY"

    table: dict[tuple[str, str], Any] = {
        ("flow", "public.source.edges"): [],
        ("flow", "public.source.path"): [0, 2],
        ("flow", "public.source.demand"): 10**6,
        ("flow", "public.source.qoi"): "irrelevant_source_qoi_probe",
        ("flow", "public.source.mode"): "irrelevant_source_mode_probe",
        ("flow", "public.target.edges"): [],
        ("flow", "public.target.qoi"): "probe_qoi",
        ("flow", "public.target.mode"): "probe_mode",
        ("flow", "public.mapping"): {},
        ("logic", "public.source.facts"): ["UNMAPPED_PROBE_FACT"],
        ("logic", "public.source.rules"): [],
        ("logic", "public.source.query"): "UNMAPPED_PROBE_QUERY",
        ("logic", "public.target.facts"): [],
        ("logic", "public.target.rules"): [],
        ("logic", "public.target.qoi"): "probe_qoi",
        ("logic", "public.target.boundary"): "probe_boundary",
        ("logic", "public.mapping"): {},
        ("units", "public.source.input_dims"): [(9, 9, 9), (8, 8, 8)],
        ("units", "public.source.operation"): "probe_source_operation",
        ("units", "public.source.output_dim"): (9, 9, 9),
        ("units", "public.source.qoi"): "probe_source_qoi",
        ("units", "public.source.boundary"): "probe_source_boundary",
        ("units", "public.target.input_dims"): [(1, 0, 0), None],
        ("units", "public.target.operation"): "probe_operation",
        ("units", "public.target.output_dim"): (9, 9, 9),
        ("units", "public.target.qoi"): "probe_qoi",
        ("units", "public.target.boundary"): "probe_boundary",
        ("units", "public.target.denominator_nonzero"): None,
        ("state", "public.source.start"): "probe_source_start",
        ("state", "public.source.goal"): "probe_source_goal",
        ("state", "public.source.actions"): ["probe_source_action"],
        ("state", "public.source.qoi"): "probe_source_qoi",
        ("state", "public.source.boundary"): "probe_source_boundary",
        ("state", "public.target.transitions"): [],
        ("state", "public.target.start"): "probe_start",
        ("state", "public.target.goal"): "probe_goal",
        ("state", "public.target.qoi"): "probe_qoi",
        ("state", "public.target.boundary"): "probe_boundary",
        ("state", "public.mapping"): {},
        ("state", "public.candidate_actions"): ["probe_action"],
    }
    key = (family, path)
    if key not in table:
        raise KeyError(f"no registered intervention for {key}")
    return table[key]


def _set_public_path(public: dict[str, Any], path: str, new_value: Any) -> None:
    parts = path.split(".")
    if parts[0] != "public":
        raise ValueError("not a public path")
    cursor: dict[str, Any] = public
    for part in parts[1:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = new_value


def intervene(task: Task, path: str) -> Task:
    if path == "source_text":
        return replace(task, source_text=_adversarial_value(task.family, path, task.source_text))
    if path == "target_text":
        return replace(task, target_text=_adversarial_value(task.family, path, task.target_text))

    public = deepcopy(dict(task.public))
    parts = path.split(".")
    cursor: Any = public
    for part in parts[1:]:
        cursor = cursor[part]
    _set_public_path(public, path, _adversarial_value(task.family, path, cursor))
    return replace(task, public=public)


def discover_sensitive_paths(tasks: list[Task]) -> dict[str, frozenset[str]]:
    """Mark a path sensitive iff its registered intervention changes any verifier decision."""

    by_family: dict[str, list[Task]] = {family: [] for family in ALL_CANDIDATE_PATHS}
    for task in tasks:
        by_family[task.family].append(task)

    output: dict[str, frozenset[str]] = {}
    for family, paths in ALL_CANDIDATE_PATHS.items():
        sensitive: set[str] = set()
        for path in paths:
            for task in by_family[family]:
                baseline = verify(task).decision
                changed = verify(intervene(task, path)).decision
                if changed is not baseline:
                    sensitive.add(path)
                    break
        output[family] = frozenset(sensitive)
    return output


def run_sq2(seed: int = SQ2_DEVELOPMENT_SEED, n_per_cell: int = 4) -> dict[str, object]:
    if seed == PAPER2_CONFIRMATORY_SEED_DO_NOT_USE:
        raise ValueError("SQ2 must not use the Paper II confirmatory seed")

    tasks = generate(seed, n_per_cell=n_per_cell, include_controls=True)
    discovered = discover_sensitive_paths(tasks)
    family: dict[str, dict[str, object]] = {}
    total_tp = total_fp = total_fn = total_tn = 0

    for fam, paths in ALL_CANDIDATE_PATHS.items():
        expected = EXACT_REQUIRED_PATHS[fam]
        predicted = discovered[fam]
        universe = set(paths)
        tp = len(predicted & expected)
        fp = len(predicted - expected)
        fn = len(expected - predicted)
        tn = len(universe - predicted - expected)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_tn += tn
        family[fam] = {
            "expected_required": sorted(expected),
            "discovered_sensitive": sorted(predicted),
            "erased_as_nuisance": sorted(universe - predicted),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
            "exact_dependency_recovery": predicted == expected,
        }

    precision = total_tp / max(1, total_tp + total_fp)
    recall = total_tp / max(1, total_tp + total_fn)
    specificity = total_tn / max(1, total_tn + total_fp)

    return {
        "schema": "rakl.tcsq.sq2.intervention_fidelity.v0",
        "status": "DEVELOPMENT_FINITE_INTERVENTION_DEPENDENCY_AUDIT",
        "seed": seed,
        "n_per_cell": n_per_cell,
        "n": len(tasks),
        "paper2_confirmatory_seed_used": False,
        "family": family,
        "aggregate": {
            "true_positive": total_tp,
            "false_positive": total_fp,
            "false_negative": total_fn,
            "true_negative": total_tn,
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "all_family_exact_dependency_recovery": all(
                row["exact_dependency_recovery"] for row in family.values()
            ),
        },
        "sq1_v0_note": (
            "The first SQ1 oracle quotient was intentionally safe but over-preserved some "
            "source-side fields. SQ2 scores against exact code-level public dependencies and "
            "therefore measures over-preservation as well as false erasure."
        ),
        "claim_boundary": (
            "Finite registered interventions over a known exact verifier; candidate field schema "
            "and interventions are human-specified. This is not natural-language quotient "
            "discovery, an LLM result, or proof of total-cost improvement."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_sq2(), indent=2, sort_keys=True))
