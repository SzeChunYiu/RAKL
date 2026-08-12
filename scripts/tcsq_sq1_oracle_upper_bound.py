from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
from typing import Any, Mapping

from rakl.objective_transfer_benchmark import Decision, Task, generate, verify


SQ1_DEVELOPMENT_SEED = 20260812971
SQ1_N_PER_CELL = 20
PAPER2_CONFIRMATORY_SEED_DO_NOT_USE = 2026081202
TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _leaf_count(value: Any) -> int:
    if isinstance(value, Mapping):
        return sum(_leaf_count(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_leaf_count(item) for item in value)
    return 1


def _text_token_count(text: str) -> int:
    return len(TOKEN_RE.findall(text.lower()))


def oracle_quotient(task: Task) -> dict[str, Any]:
    """Keep only fields used by the registered exact family verifier.

    This is an oracle *representation* upper bound.  It uses the known verifier
    dependency graph and never reads item_type, perturbation, or the verifier outcome.
    It therefore says nothing about whether an LLM can discover the quotient.
    """

    p = task.public
    if task.family == "flow":
        src, tgt = p["source"], p["target"]
        return {
            "family": "flow",
            "source": {
                "path": src["path"],
                "demand": src["demand"],
                "qoi": src["qoi"],
                "mode": src["mode"],
            },
            "target": {
                "edges": tgt["edges"],
                "qoi": tgt["qoi"],
                "mode": tgt["mode"],
            },
            "mapping": p["mapping"],
        }
    if task.family == "logic":
        src, tgt = p["source"], p["target"]
        return {
            "family": "logic",
            "source": {"facts": src["facts"], "query": src["query"]},
            "target": {
                "facts": tgt["facts"],
                "rules": tgt["rules"],
                "qoi": tgt["qoi"],
                "boundary": tgt["boundary"],
            },
            "mapping": p["mapping"],
        }
    if task.family == "units":
        src, tgt = p["source"], p["target"]
        return {
            "family": "units",
            "source": {"qoi": src["qoi"], "boundary": src["boundary"]},
            "target": {
                "input_dims": tgt["input_dims"],
                "operation": tgt["operation"],
                "output_dim": tgt["output_dim"],
                "qoi": tgt["qoi"],
                "boundary": tgt["boundary"],
                "denominator_nonzero": tgt["denominator_nonzero"],
            },
        }
    if task.family == "state":
        return {
            "family": "state",
            "target": p["target"],
            "mapping": p["mapping"],
            "candidate_actions": p["candidate_actions"],
        }
    raise ValueError(f"unknown family: {task.family}")


def _logic_closure(facts: set[str], rules: list[tuple[tuple[str, ...], str]]) -> set[str]:
    out = set(facts)
    changed = True
    while changed:
        changed = False
        for antecedents, consequent in rules:
            if all(item in out for item in antecedents) and consequent not in out:
                out.add(consequent)
                changed = True
    return out


def _dim_sub(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(a - b for a, b in zip(left, right))


def verify_oracle_quotient(quotient: Mapping[str, Any]) -> Decision:
    """Decision procedure over the oracle quotient only."""

    family = quotient["family"]
    if family == "flow":
        src, tgt, mapping = quotient["source"], quotient["target"], quotient["mapping"]
        if tgt["qoi"] != src["qoi"]:
            return Decision.REJECT
        if tgt["mode"] != src["mode"]:
            return Decision.REJECT
        if any(str(node) not in mapping for node in src["path"]):
            return Decision.CANNOT_CHECK
        path = [mapping[str(node)] for node in src["path"]]
        edges = {(a, b): capacity for a, b, capacity in tgt["edges"]}
        for left, right in zip(path, path[1:]):
            if (left, right) not in edges:
                return Decision.REJECT
            capacity = edges[(left, right)]
            if capacity is None:
                return Decision.CANNOT_CHECK
            if capacity < src["demand"]:
                return Decision.REJECT
        return Decision.ACCEPT

    if family == "logic":
        src, tgt, mapping = quotient["source"], quotient["target"], quotient["mapping"]
        if tgt["qoi"] != "entailment":
            return Decision.REJECT
        if tgt["boundary"] != "horn":
            return Decision.REJECT
        needed = set(src["facts"] + [src["query"]])
        if not needed.issubset(mapping):
            return Decision.CANNOT_CHECK
        if any(consequent is None for _, consequent in tgt["rules"]):
            return Decision.CANNOT_CHECK
        rules = [(tuple(antecedents), consequent) for antecedents, consequent in tgt["rules"]]
        closure = _logic_closure(set(tgt["facts"]), rules)
        return Decision.ACCEPT if mapping[src["query"]] in closure else Decision.REJECT

    if family == "units":
        src, tgt = quotient["source"], quotient["target"]
        if tgt["qoi"] != src["qoi"]:
            return Decision.REJECT
        if tgt["boundary"] != src["boundary"]:
            return Decision.REJECT
        if any(item is None for item in tgt["input_dims"]):
            return Decision.CANNOT_CHECK
        if tgt["denominator_nonzero"] is None:
            return Decision.CANNOT_CHECK
        if tgt["denominator_nonzero"] is False:
            return Decision.REJECT
        left, right = tgt["input_dims"]
        if tgt["operation"] == "divide":
            derived = _dim_sub(tuple(left), tuple(right))
        elif tgt["operation"] == "reverse_divide":
            derived = _dim_sub(tuple(right), tuple(left))
        else:
            return Decision.CANNOT_CHECK
        return Decision.ACCEPT if tuple(tgt["output_dim"]) == derived else Decision.REJECT

    if family == "state":
        tgt, actions, mapping = quotient["target"], quotient["candidate_actions"], quotient["mapping"]
        if not {"s0", "s1", "s2", "s3"}.issubset(mapping):
            return Decision.CANNOT_CHECK
        if tgt["qoi"] != "reach_goal":
            return Decision.REJECT
        if tgt["boundary"] != "deterministic":
            return Decision.REJECT
        transitions = {(state, action): nxt for state, action, nxt in tgt["transitions"]}
        state = tgt["start"]
        for action in actions:
            if (state, action) not in transitions:
                return Decision.REJECT
            nxt = transitions[(state, action)]
            if nxt is None:
                return Decision.CANNOT_CHECK
            state = nxt
        return Decision.ACCEPT if state == tgt["goal"] else Decision.REJECT

    raise ValueError(f"unknown family: {family}")


def run_sq1(seed: int = SQ1_DEVELOPMENT_SEED, n_per_cell: int = SQ1_N_PER_CELL) -> dict[str, object]:
    if seed == PAPER2_CONFIRMATORY_SEED_DO_NOT_USE:
        raise ValueError("SQ1 must not use the Paper II confirmatory seed")

    tasks = generate(seed, n_per_cell=n_per_cell, include_controls=True)
    agreement = 0
    family_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    raw_leaves: list[int] = []
    quotient_leaves: list[int] = []
    raw_text_tokens: list[int] = []
    gold_counts: Counter[str] = Counter()

    for task in tasks:
        gold = verify(task).decision
        quotient = oracle_quotient(task)
        qdecision = verify_oracle_quotient(quotient)
        agree = int(qdecision is gold)
        agreement += agree
        family_counts[task.family][0] += agree
        family_counts[task.family][1] += 1
        raw_leaves.append(_leaf_count(task.public))
        quotient_leaves.append(_leaf_count(quotient))
        raw_text_tokens.append(_text_token_count(task.source_text) + _text_token_count(task.target_text))
        gold_counts[gold.value] += 1

    n = len(tasks)
    total_raw = sum(raw_leaves)
    total_quotient = sum(quotient_leaves)
    return {
        "schema": "rakl.tcsq.sq1.oracle_upper_bound.v0",
        "status": "DEVELOPMENT_ORACLE_UPPER_BOUND",
        "seed": seed,
        "n_per_cell": n_per_cell,
        "n": n,
        "paper2_confirmatory_seed_used": False,
        "claim_boundary": (
            "Oracle dependency reduction only. This does not test learned quotient discovery, "
            "LLM accuracy, token latency, or total end-to-end cost."
        ),
        "exact_original_verifier_agreement": agreement / n,
        "family_agreement": {
            family: correct / count for family, (correct, count) in sorted(family_counts.items())
        },
        "gold_counts": dict(sorted(gold_counts.items())),
        "mean_raw_public_primitive_count": sum(raw_leaves) / n,
        "mean_oracle_quotient_primitive_count": sum(quotient_leaves) / n,
        "aggregate_public_primitive_reduction_fraction": 1.0 - total_quotient / total_raw,
        "mean_raw_semantic_text_tokens_excluded_from_oracle_quotient": sum(raw_text_tokens) / n,
    }


if __name__ == "__main__":
    print(json.dumps(run_sq1(), indent=2, sort_keys=True))
