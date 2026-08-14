#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_DEFAULT = ROOT / "research" / "paper3_independent_oracle_action_v1" / "PROTOCOL.json"
ORACLE_PATH = ROOT / "experiments" / "paper3" / "independent_action_oracle_v1.py"
CANDIDATE_PATH = ROOT / "experiments" / "orion_closure" / "run_p3_structured_experience_action.py"

VISIBLE_FIELDS = (
    "candidate_present",
    "lesson_verified",
    "scope_match",
    "version_current",
    "not_refuted",
    "lineage_valid",
    "target_context_match",
    "failure_signature_match",
    "strategy_family_match",
    "negative_history_block",
    "validity_known",
    "successor_verified",
    "successor_scope_match",
    "successor_current",
)
COMPOSITE_PARENT_FIELDS = (
    "candidate_present",
    "failure_signature_match",
    "negative_history_block",
    "lineage_valid",
    "strategy_family_match",
)
OUTCOMES = ("APPLY_VERIFIED_LESSON", "APPLY_SUCCESSOR", "FALLBACK_SEARCH", "CANNOT_CHECK")


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def independence_audit() -> dict[str, Any]:
    source = ORACLE_PATH.read_text()
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    forbidden_tokens = ["strict_action", "run_p3_structured_experience_action", "orion_closure"]
    hits = [token for token in forbidden_tokens if token in source]
    candidate_import_hits = [name for name in imported if "orion_closure" in name or "structured_experience_action" in name]
    return {
        "oracle_forbidden_token_hits": hits,
        "oracle_candidate_import_hits": candidate_import_hits,
        "passes": not hits and not candidate_import_hits,
        "oracle_sha256": _sha(ORACLE_PATH),
        "candidate_sha256": _sha(CANDIDATE_PATH),
    }


def _base() -> dict[str, bool]:
    return {
        "candidate_present": True,
        "lesson_verified": True,
        "scope_match": True,
        "version_current": True,
        "not_refuted": True,
        "lineage_valid": True,
        "target_context_match": True,
        "failure_signature_match": True,
        "strategy_family_match": True,
        "negative_history_block": False,
        "validity_known": True,
        "successor_verified": False,
        "successor_scope_match": False,
        "successor_current": False,
    }


def _opaque_id(seed: int, index: int) -> str:
    return "P3O-" + sha256(f"{seed}:{index}".encode()).hexdigest()[:16]


def build_cases(protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    seed = int(protocol["fresh_panel"]["seed"])
    n = int(protocol["fresh_panel"]["n_cases"])
    if n % 4:
        raise ValueError("n_cases must be divisible by four")
    per = n // 4
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    index = 0

    # Stratum 1: legitimate primary application.
    for _ in range(per):
        row = _base()
        # Random successor flags are irrelevant to the primary decision and
        # prevent the surface from being one constant template.
        row["successor_verified"] = rng.random() < 0.5
        row["successor_scope_match"] = rng.random() < 0.5
        row["successor_current"] = rng.random() < 0.5
        rows.append({"case_id": _opaque_id(seed, index), **row})
        index += 1

    # Stratum 2: legitimate verified successor after predecessor disqualification.
    for i in range(per):
        row = _base()
        reason = i % 3
        if reason == 0:
            row["not_refuted"] = False
        elif reason == 1:
            row["version_current"] = False
        else:
            row["negative_history_block"] = True
        row["successor_verified"] = True
        row["successor_scope_match"] = True
        row["successor_current"] = True
        rows.append({"case_id": _opaque_id(seed, index), **row})
        index += 1

    # Stratum 3: epistemically unknown validity. Every record is otherwise
    # primary-valid so a candidate that treats UNKNOWN as valid is exposed.
    for _ in range(per):
        row = _base()
        row["validity_known"] = False
        rows.append({"case_id": _opaque_id(seed, index), **row})
        index += 1

    # Stratum 4: fallback controls. Cycle single-coordinate blockers so every
    # registered relax-one-check mutant has a direct unsafe counterexample.
    blockers = (
        "lesson_verified",
        "scope_match",
        "version_current",
        "not_refuted",
        "lineage_valid",
        "target_context_match",
        "failure_signature_match",
        "strategy_family_match",
        "negative_history_block",
        "candidate_present",
    )
    for i in range(per):
        row = _base()
        blocker = blockers[i % len(blockers)]
        row[blocker] = True if blocker == "negative_history_block" else False
        rows.append({"case_id": _opaque_id(seed, index), **row})
        index += 1

    rng.shuffle(rows)
    allowed = {"case_id", *VISIBLE_FIELDS}
    for row in rows:
        extra = set(row) - allowed
        if extra:
            raise AssertionError(f"candidate surface has forbidden fields: {sorted(extra)}")
    return rows


def metrics(cases: Sequence[Mapping[str, Any]], gold: Mapping[str, str], pred: Mapping[str, str]) -> dict[str, float]:
    n = len(cases)
    exact = sum(pred[c["case_id"]] == gold[c["case_id"]] for c in cases) / n
    unsafe = sum(
        pred[c["case_id"]].startswith("APPLY") and not gold[c["case_id"]].startswith("APPLY")
        for c in cases
    ) / n
    cc = [c for c in cases if gold[c["case_id"]] == "CANNOT_CHECK"]
    apply = [c for c in cases if gold[c["case_id"]].startswith("APPLY")]
    return {
        "exact_action_accuracy": exact,
        "unsafe_apply_rate": unsafe,
        "cannot_check_recall": sum(pred[c["case_id"]] == "CANNOT_CHECK" for c in cc) / len(cc),
        "legitimate_apply_recall": sum(pred[c["case_id"]] == gold[c["case_id"]] for c in apply) / len(apply),
    }


def information_ceiling(cases: Sequence[Mapping[str, Any]], gold: Mapping[str, str], fields: Sequence[str]) -> float:
    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row in cases:
        groups[tuple(row[field] for field in fields)].append(gold[row["case_id"]])
    correct = 0
    for labels in groups.values():
        correct += Counter(labels).most_common(1)[0][1]
    return correct / len(cases)


def candidate_prediction(candidate: Any, cases: Sequence[Mapping[str, Any]], mutant: str | None = None) -> dict[str, str]:
    pred: dict[str, str] = {}
    for row in cases:
        case_id = str(row["case_id"])
        payload = {field: row[field] for field in VISIBLE_FIELDS}
        if mutant == "ALWAYS_APPLY_PRIMARY":
            action = "APPLY_VERIFIED_LESSON" if payload["candidate_present"] else "FALLBACK_SEARCH"
        else:
            action = candidate.strict_action(payload, mutant)
            if mutant == "NEVER_CANNOT_CHECK" and action == "CANNOT_CHECK":
                action = "FALLBACK_SEARCH"
        pred[case_id] = action
    return pred


def run(protocol: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit = independence_audit()
    oracle = _load(ORACLE_PATH, "p3_independent_oracle_v1")
    candidate = _load(CANDIDATE_PATH, "p3_structured_candidate_v1")
    cases = build_cases(protocol)
    gold = {row["case_id"]: oracle.oracle_action({field: row[field] for field in VISIBLE_FIELDS}) for row in cases}
    counts = Counter(gold.values())

    base_pred = candidate_prediction(candidate, cases)
    base_metrics = metrics(cases, gold, base_pred)
    parent_ceiling = information_ceiling(cases, gold, COMPOSITE_PARENT_FIELDS)

    mutant_rows: dict[str, Any] = {}
    for mutant in protocol["registered_candidate_mutants"]:
        pred = candidate_prediction(candidate, cases, mutant)
        m = metrics(cases, gold, pred)
        changed = [key for key, value in m.items() if value != base_metrics[key]]
        mutant_rows[mutant] = {"metrics": m, "changed_metrics": changed}

    thresholds = protocol["primary_metrics"]
    gate = {
        "independent_oracle": bool(audit["passes"]),
        "all_outcomes_present": all(counts[outcome] > 0 for outcome in OUTCOMES),
        "candidate_exact": base_metrics["exact_action_accuracy"] >= thresholds["exact_action_accuracy_min"],
        "candidate_unsafe": base_metrics["unsafe_apply_rate"] <= thresholds["unsafe_apply_rate_max"],
        "candidate_cannot_check": base_metrics["cannot_check_recall"] >= thresholds["cannot_check_recall_min"],
        "candidate_legitimate_apply": base_metrics["legitimate_apply_recall"] >= thresholds["legitimate_apply_recall_min"],
        "composite_parent_residual": parent_ceiling <= thresholds["composite_simple_information_ceiling_max"],
        "all_mutants_change_candidate_metric": all(row["changed_metrics"] for row in mutant_rows.values()),
    }

    metric_failures = {
        "exact_action_accuracy": [
            name for name, row in mutant_rows.items()
            if row["metrics"]["exact_action_accuracy"] < thresholds["exact_action_accuracy_min"]
        ],
        "unsafe_apply_rate": [
            name for name, row in mutant_rows.items()
            if row["metrics"]["unsafe_apply_rate"] > thresholds["unsafe_apply_rate_max"]
        ],
        "cannot_check_recall": [
            name for name, row in mutant_rows.items()
            if row["metrics"]["cannot_check_recall"] < thresholds["cannot_check_recall_min"]
        ],
        "legitimate_apply_recall": [
            name for name, row in mutant_rows.items()
            if row["metrics"]["legitimate_apply_recall"] < thresholds["legitimate_apply_recall_min"]
        ],
    }
    gate["all_candidate_metric_gates_demonstrably_falsifiable"] = all(metric_failures.values())
    all_pass = all(gate.values())

    receipt = {
        "schema_version": "rakl-p3-independent-oracle-action-result-v1",
        "protocol_parent_main_sha": protocol["parent_main_sha"],
        "n_cases": len(cases),
        "gold_outcome_counts": dict(sorted(counts.items())),
        "independence_audit": audit,
        "candidate_metrics": base_metrics,
        "composite_simple_parent_information_ceiling": parent_ceiling,
        "registered_mutants": mutant_rows,
        "metric_gate_falsifiability_witnesses": metric_failures,
        "gate": gate,
        "all_gates_pass": all_pass,
        "terminal": protocol["allowed_positive_terminal"] if all_pass else protocol["negative_terminal"],
        "claim_boundary": protocol["claim_boundary"],
        "historical_self_grading_receipt_preserved": True,
        "grants_scientific_authority": False,
        "grants_model_level_efficacy": False,
    }
    return cases, receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default=str(PROTOCOL_DEFAULT))
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    cases, receipt = run(protocol)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "CASES.jsonl").open("w") as f:
        for row in cases:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    (out / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
