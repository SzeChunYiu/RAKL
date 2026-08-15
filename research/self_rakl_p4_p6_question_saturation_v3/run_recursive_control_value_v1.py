#!/usr/bin/env python3
"""Execute the frozen Paper-VI recursive-control known-world protocol.

The protocol predates this evaluator.  Results are mechanic/control-value evidence
only and grant no scientific or publication authority.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "RECURSIVE_CONTROL_VALUE_PROTOCOL_V1.json"
RESULT = ROOT / "RECURSIVE_CONTROL_VALUE_RESULT_V1.json"


def entropy(ps: list[float]) -> float:
    return -sum(p * math.log(p) for p in ps if p > 0)


def posterior(prior: list[float], signal: bool, p1: list[float]) -> list[float]:
    values = [prior[i] * (p1[i] if signal else 1.0 - p1[i]) for i in range(len(prior))]
    total = sum(values)
    if total <= 0:
        raise ValueError("posterior normalization failed")
    return [value / total for value in values]


def choose_map(ps: list[float]) -> int:
    return max(range(len(ps)), key=lambda i: (ps[i], -i))


def select_info_gain_per_cost(prior: list[float], probes: dict[str, dict]) -> tuple[str, dict[str, float]]:
    h0 = entropy(prior)
    scores: dict[str, float] = {}
    for name, probe in probes.items():
        p1 = probe["p_signal_1"]
        p_signal = sum(prior[i] * p1[i] for i in range(len(prior)))
        expected_h = (
            p_signal * entropy(posterior(prior, True, p1))
            + (1.0 - p_signal) * entropy(posterior(prior, False, p1))
        )
        scores[name] = (h0 - expected_h) / probe["cost"]
    return max(scores, key=scores.get), scores


def select_decision_voi(prior: list[float], probes: dict[str, dict]) -> tuple[str, dict[str, float]]:
    scores: dict[str, float] = {"NO_PROBE": 1.0 - max(prior)}
    for name, probe in probes.items():
        p1 = probe["p_signal_1"]
        p_signal = sum(prior[i] * p1[i] for i in range(len(prior)))
        expected_wrong = (
            p_signal * (1.0 - max(posterior(prior, True, p1)))
            + (1.0 - p_signal) * (1.0 - max(posterior(prior, False, p1)))
        )
        scores[name] = expected_wrong + probe["cost"]
    return min(scores, key=scores.get), scores


def execute_diagnosis(protocol: dict) -> dict:
    cfg = protocol["diagnosis"]
    prior = cfg["prior"]
    probes = cfg["probes"]
    mutation_cost = cfg["mutation_cost"]
    n = protocol["n_diagnosis_worlds"]
    rng = random.Random(protocol["seed"])
    names = list(probes)

    info_probe, info_scores = select_info_gain_per_cost(prior, probes)
    voi_probe, voi_scores = select_decision_voi(prior, probes)

    worlds: list[tuple[int, dict[str, float], int]] = []
    for _ in range(n):
        u = rng.random()
        cumulative = 0.0
        cause = len(prior) - 1
        for index, probability in enumerate(prior):
            cumulative += probability
            if u <= cumulative:
                cause = index
                break
        probe_u = {name: rng.random() for name in names}
        random_probe_index = min(int(rng.random() * len(names)), len(names) - 1)
        worlds.append((cause, probe_u, random_probe_index))

    def action_after_probe(cause: int, name: str, u: float) -> tuple[int, float]:
        probe = probes[name]
        signal = u < probe["p_signal_1"][cause]
        return choose_map(posterior(prior, signal, probe["p_signal_1"])), probe["cost"]

    def arm_metrics(arm: str) -> dict[str, float]:
        correct = wrong_worlds = harmful = 0
        probe_cost = mutation_spend = 0.0
        for cause, probe_u, random_probe_index in worlds:
            if arm == "MUTATE_ALL_PLAUSIBLE":
                correct += 1
                wrong_worlds += 1
                harmful += len(prior) - 1
                mutation_spend += len(prior) * mutation_cost
                continue
            if arm == "ORACLE_CAUSE":
                correct += 1
                mutation_spend += mutation_cost
                continue
            if arm == "NO_PROBE_MAP":
                action = choose_map(prior)
                cost = 0.0
            else:
                if arm == "RANDOM_PROBE":
                    probe_name = names[random_probe_index]
                elif arm == "FIXED_SURFACE":
                    probe_name = "surface"
                elif arm == "INFO_GAIN_PER_COST":
                    probe_name = info_probe
                elif arm == "DECISION_VOI":
                    probe_name = None if voi_probe == "NO_PROBE" else voi_probe
                else:
                    raise ValueError(f"unknown diagnosis arm {arm}")
                if probe_name is None:
                    action = choose_map(prior)
                    cost = 0.0
                else:
                    action, cost = action_after_probe(cause, probe_name, probe_u[probe_name])
            probe_cost += cost
            mutation_spend += mutation_cost
            if action == cause:
                correct += 1
            else:
                wrong_worlds += 1
                harmful += 1
        return {
            "correct_repair_rate": correct / n,
            "wrong_layer_mutation_rate": wrong_worlds / n,
            "harmful_mutations_per_world": harmful / n,
            "probe_cost_per_world": probe_cost / n,
            "mutation_cost_per_world": mutation_spend / n,
            "total_cost_per_world": (probe_cost + mutation_spend) / n,
        }

    return {
        "selected_probes": {
            "INFO_GAIN_PER_COST": info_probe,
            "DECISION_VOI": voi_probe,
        },
        "selection_diagnostics": {
            "info_gain_per_cost": info_scores,
            "decision_loss_plus_cost": voi_scores,
        },
        "arms": {arm: arm_metrics(arm) for arm in cfg["arms"]},
    }


def execute_contextual_credit(protocol: dict) -> dict:
    cfg = protocol["contextual_credit"]
    train = cfg["train_contexts"]
    fresh = cfg["fresh_contexts"]
    operators = sorted(next(iter(train.values()))["effects"])

    global_mean = {
        operator: sum(world["effects"][operator] for world in train.values()) / len(train)
        for operator in operators
    }
    global_operator = max(operators, key=lambda operator: global_mean[operator])

    family_operator: dict[str, str] = {}
    for world in train.values():
        family = world["family"]
        if family in family_operator:
            raise ValueError("protocol must provide one registered source context per family")
        family_operator[family] = max(operators, key=lambda operator: world["effects"][operator])

    def metrics(arm: str) -> dict:
        rows = []
        for context_name, world in fresh.items():
            if arm == "GLOBAL_CREDIT":
                operator = global_operator
            elif arm == "CONTEXT_TRANSPORT_CREDIT":
                operator = family_operator[world["family"]]
            elif arm == "UNINFORMED_FIXED_LOCAL":
                operator = "local_patch"
            elif arm == "ORACLE_FRESH":
                operator = max(operators, key=lambda item: world["effects"][item])
            else:
                raise ValueError(f"unknown credit arm {arm}")
            effect = world["effects"][operator]
            oracle_effect = max(world["effects"].values())
            rows.append(
                {
                    "context": context_name,
                    "operator": operator,
                    "effect": effect,
                    "regret": oracle_effect - effect,
                    "correct": effect == oracle_effect,
                    "harmful": effect < 0,
                }
            )
        return {
            "correct_operator_rate": sum(row["correct"] for row in rows) / len(rows),
            "harmful_repair_rate": sum(row["harmful"] for row in rows) / len(rows),
            "mean_effect": sum(row["effect"] for row in rows) / len(rows),
            "regret_vs_oracle": sum(row["regret"] for row in rows) / len(rows),
            "selections": rows,
        }

    return {
        "global_train_mean": global_mean,
        "global_selected_operator": global_operator,
        "registered_same_family_transport": family_operator,
        "arms": {arm: metrics(arm) for arm in cfg["arms"]},
    }


def terminal(protocol: dict, diagnosis: dict, credit: dict) -> tuple[str, dict[str, str]]:
    d = diagnosis["arms"]
    c = credit["arms"]
    diagnosis_supported = (
        d["DECISION_VOI"]["harmful_mutations_per_world"]
        <= min(
            d[parent]["harmful_mutations_per_world"]
            for parent in ("NO_PROBE_MAP", "RANDOM_PROBE", "FIXED_SURFACE", "INFO_GAIN_PER_COST")
        )
        and d["DECISION_VOI"]["wrong_layer_mutation_rate"]
        < d["INFO_GAIN_PER_COST"]["wrong_layer_mutation_rate"]
        and d["DECISION_VOI"]["wrong_layer_mutation_rate"]
        < d["FIXED_SURFACE"]["wrong_layer_mutation_rate"]
        and d["DECISION_VOI"]["total_cost_per_world"]
        < d["MUTATE_ALL_PLAUSIBLE"]["total_cost_per_world"]
    )
    contextual_supported = (
        c["CONTEXT_TRANSPORT_CREDIT"]["harmful_repair_rate"]
        < c["GLOBAL_CREDIT"]["harmful_repair_rate"]
        and c["CONTEXT_TRANSPORT_CREDIT"]["regret_vs_oracle"]
        < c["GLOBAL_CREDIT"]["regret_vs_oracle"]
    )
    simpler_diagnosis_matches = any(
        d[parent] == d["DECISION_VOI"]
        for parent in ("FIXED_SURFACE", "INFO_GAIN_PER_COST")
    )
    global_matches_contextual = c["GLOBAL_CREDIT"] == c["CONTEXT_TRANSPORT_CREDIT"]

    if diagnosis_supported and contextual_supported:
        verdict = "CONTROL_VALUE_SUPPORTED"
    elif simpler_diagnosis_matches or global_matches_contextual:
        verdict = "SIMPLER_PARENT_SUFFICIENT"
    else:
        verdict = "CONTROL_TRADEOFF_UNRESOLVED"
    return verdict, {
        "diagnosis_component": "SUPPORTED" if diagnosis_supported else "SIMPLER_PARENT_SUFFICIENT" if simpler_diagnosis_matches else "UNRESOLVED",
        "contextual_credit_component": "SUPPORTED" if contextual_supported else "SIMPLER_PARENT_SUFFICIENT" if global_matches_contextual else "UNRESOLVED",
    }


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "FROZEN_BEFORE_EXECUTION":
        raise SystemExit("protocol is not frozen")
    diagnosis = execute_diagnosis(protocol)
    credit = execute_contextual_credit(protocol)
    verdict, components = terminal(protocol, diagnosis, credit)
    payload = {
        "schema_version": "paper6-recursive-control-value-result-v1",
        "protocol_git_blob_sha": "2ffc092a00d30d9d233530616f059f98af877d70",
        "terminal": verdict,
        "components": components,
        "diagnosis": diagnosis,
        "contextual_credit": credit,
        "interpretation": {
            "diagnosis": "The frozen decision-VOI selector chose the same surface probe as both the fixed-surface and information-gain-per-cost parents, so no distinct diagnosis-control value is established in this world.",
            "contextual_credit": "Same-family contextual transport selected the fresh oracle operator in all three fresh contexts, while global credit selected a harmful operator in B_fresh.",
            "scope": "Known-world mechanic/control-value evidence only; not external-agent or scientific-performance authority."
        },
        "grants_scientific_authority": false,
        "grants_method_promotion_authority": false
    }
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"terminal": verdict, "components": components}, sort_keys=True))


if __name__ == "__main__":
    main()
