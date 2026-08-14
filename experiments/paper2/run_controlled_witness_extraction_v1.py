from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from rakl.controlled_witness_extraction import (
    controlled_span_manifest,
    drop_semantic_field,
    extract_controlled_task,
    render_controlled_task,
)
from rakl.objective_transfer_benchmark import Decision, Task
from rakl.objective_transfer_benchmark_v2 import (
    extract as witness_extract,
    generate,
    mechanism_predict,
    verify,
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "research" / "paper2_controlled_witness_extraction_v1" / "PROTOCOL.json"


def _predict_from_text(task: Task, variant: int) -> Decision:
    text = render_controlled_task(task, variant=variant)
    expected = dict(controlled_span_manifest(text))
    parsed = extract_controlled_task(text, expected_span_sha256=expected)
    if not parsed.complete or parsed.task is None:
        return Decision.CANNOT_CHECK
    try:
        return verify(parsed.task).decision
    except (KeyError, TypeError, ValueError):
        return Decision.CANNOT_CHECK


def _qoi_boundary_parent(task: Task) -> Decision:
    # Strong bounded parent: it sees family/QoI/boundary but not mapping,
    # relational, precondition, invariant or derived-effect coordinates.
    ablate = frozenset({"mapping", "relations", "precondition", "effect", "invariant"})
    try:
        return witness_extract(task, ablate).decision
    except (KeyError, TypeError, ValueError):
        return Decision.CANNOT_CHECK


def _mutate_record(text: str, family: str, mutation: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if " :: " not in line:
            out.append(line)
            continue
        label, payload = line.split(" :: ", 1)
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            out.append(line)
            continue

        is_source = label in {"Source structural record", "Facts licensed at the source"}
        is_target = label in {"Target structural record", "Facts declared at the target"}
        if mutation == "DROP_QOI" and is_target and isinstance(value, dict):
            value.pop("qoi", None)
        elif mutation == "DROP_BOUNDARY" and is_target and isinstance(value, dict):
            value.pop("boundary", None)
            value.pop("mode", None)
            value.pop("regime", None)
            value.pop("sampling", None)
        elif mutation == "DROP_PRECONDITION" and is_target and isinstance(value, dict):
            if family == "flow" and "edges" in value and value["edges"]:
                value["edges"][0][2] = None
            elif family == "logic" and "rules" in value and value["rules"]:
                value["rules"][0][1] = None
            elif family == "units":
                value["denominator_nonzero"] = None
            elif family == "state" and "transitions" in value and value["transitions"]:
                value["transitions"][0][2] = None
            elif family == "sched" and "durations" in value:
                first = sorted(value["durations"])[0]
                value["durations"][first] = None
            elif family == "stat":
                value["prevalence"] = None
        elif mutation == "DROP_RELATION_OR_DIRECTION" and is_target and isinstance(value, dict):
            if family == "flow":
                value["edges"] = []
            elif family == "logic":
                value["rules"] = []
            elif family == "units":
                value["operation"] = "unknown"
            elif family == "state":
                value["transitions"] = []
            elif family == "sched":
                value["precedence"] = []
            elif family == "stat":
                value["conditioning"] = "unknown"
        elif mutation == "IGNORE_TARGET_VALUE" and is_target and isinstance(value, dict):
            # Replace the target record by a structurally empty record. This
            # models a parser that recognizes labels but not target values.
            value = {}
        elif mutation == "IGNORE_SOURCE_REQUIREMENT" and is_source and isinstance(value, dict):
            value = {}
        out.append(f"{label} :: {json.dumps(value, sort_keys=True, separators=(',', ':'))}")
    return "\n".join(out) + "\n"


def _mutation_error_count(tasks: list[Task], mutation: str) -> int:
    errors = 0
    for i, task in enumerate(tasks):
        variant = i % 2
        text = render_controlled_task(task, variant=variant)
        expected = dict(controlled_span_manifest(text))
        gold = verify(task).decision
        if mutation == "DROP_MAPPING":
            mutated = drop_semantic_field(text, "mapping")
            parsed = extract_controlled_task(mutated, expected_span_sha256=expected)
            pred = Decision.CANNOT_CHECK if not parsed.complete or parsed.task is None else verify(parsed.task).decision
        elif mutation == "DROP_SOURCE_SPAN_BINDING":
            # Keep the old manifest while changing a candidate-visible source
            # line. The correct extractor must reject the stale binding.
            mutated = text.replace(" :: ", " :: ", 1)
            lines = mutated.splitlines()
            for j, line in enumerate(lines):
                if "Target structural record" in line or "Facts declared at the target" in line:
                    lines[j] = line + " "
                    break
            parsed = extract_controlled_task("\n".join(lines) + "\n", expected_span_sha256=expected)
            pred = Decision.CANNOT_CHECK if not parsed.complete else verify(parsed.task).decision  # type: ignore[arg-type]
        elif mutation == "UNKNOWN_AS_REJECT":
            pred = _predict_from_text(task, variant)
            if pred is Decision.CANNOT_CHECK:
                pred = Decision.REJECT
        elif mutation == "UNKNOWN_AS_ACCEPT":
            pred = _predict_from_text(task, variant)
            if pred is Decision.CANNOT_CHECK:
                pred = Decision.ACCEPT
        else:
            mutated = _mutate_record(text, task.family, mutation)
            parsed = extract_controlled_task(mutated)
            if not parsed.complete or parsed.task is None:
                pred = Decision.CANNOT_CHECK
            else:
                try:
                    pred = verify(parsed.task).decision
                except (KeyError, TypeError, ValueError):
                    pred = Decision.CANNOT_CHECK
        errors += pred is not gold
    return errors


def run(out: Path) -> dict[str, Any]:
    protocol = json.loads(PROTOCOL.read_text())
    tasks = generate(int(protocol["fresh_seed"]), int(protocol["n_per_cell"]), True)
    gold = {t.item_id: verify(t).decision for t in tasks}

    full_rows = []
    for task in tasks:
        for variant in (0, 1):
            full_rows.append((task, variant, _predict_from_text(task, variant)))
    n = len(full_rows)
    exact = sum(pred is gold[t.item_id] for t, _, pred in full_rows) / n
    rejects = [(t, p) for t, _, p in full_rows if gold[t.item_id] is Decision.REJECT]
    accepts = [(t, p) for t, _, p in full_rows if gold[t.item_id] is Decision.ACCEPT]
    unknowns = [(t, p) for t, _, p in full_rows if gold[t.item_id] is Decision.CANNOT_CHECK]
    full_false_accept = sum(p is Decision.ACCEPT for _, p in rejects) / max(1, len(rejects))
    full_valid_accept = sum(p is Decision.ACCEPT for _, p in accepts) / max(1, len(accepts))
    full_cc = sum(p is Decision.CANNOT_CHECK for _, p in unknowns) / max(1, len(unknowns))

    parent_preds = {
        "MECHANISM_DERIVED_PARENT": [mechanism_predict(t) for t in tasks],
        "QOI_BOUNDARY_ONLY": [_qoi_boundary_parent(t) for t in tasks],
        "NO_UNKNOWN_STATE": [
            Decision.REJECT if verify(t).decision is Decision.CANNOT_CHECK else verify(t).decision
            for t in tasks
        ],
    }
    parent_exact = {
        name: sum(p is gold[t.item_id] for t, p in zip(tasks, preds)) / len(tasks)
        for name, preds in parent_preds.items()
    }

    mutations = {
        name: _mutation_error_count(tasks, name)
        for name in protocol["mutations"]
    }
    all_mutations_caught = all(count > 0 for count in mutations.values())
    strongest_parent = max(parent_exact.values())
    gates = protocol["hard_gates"]
    all_gates = (
        exact >= gates["full_exact_decision_min"]
        and full_false_accept <= gates["full_invalid_false_accept_max"]
        and full_cc >= gates["full_cannot_check_recall_min"]
        and full_valid_accept >= gates["full_valid_accept_min"]
        and strongest_parent <= gates["strongest_parent_exact_max"]
        and all_mutations_caught is gates["all_mutations_caught"]
    )

    receipt = {
        "schema_version": "paper2-controlled-witness-extraction-result-v1",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "n_base_tasks": len(tasks),
        "n_text_surfaces": n,
        "gold_counts": dict(Counter(g.value for g in gold.values())),
        "full_controlled_extractor": {
            "exact_decision": exact,
            "invalid_false_accept": full_false_accept,
            "cannot_check_recall": full_cc,
            "valid_accept": full_valid_accept,
        },
        "parents": parent_exact,
        "strongest_parent_exact": strongest_parent,
        "mutation_error_counts": mutations,
        "all_mutations_caught": all_mutations_caught,
        "all_gates_pass": all_gates,
        "terminal": protocol["promotion_if_green"] if all_gates else "RSHEA_SUCCESSOR_REQUIRED",
        "scope": protocol["scope"],
        "nonclaims": protocol["nonclaims"],
        "grants_scientific_authority": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.out)
    raise SystemExit(0 if result["all_gates_pass"] else 1)


if __name__ == "__main__":
    main()
