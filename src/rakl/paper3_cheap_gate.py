from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ARM_FEATURES: dict[str, tuple[str, ...]] = {
    "semantic_calibrated": ("semantic",),
    "skill_aware": ("semantic", "skill"),
    "dependency_aware": ("semantic", "skill", "dependency"),
    "witnessed_structure": (
        "semantic",
        "skill",
        "dependency",
        "invariant",
        "boundary",
        "qoi",
        "directional",
    ),
}
CONTROL_ORDER = ("semantic_calibrated", "skill_aware", "dependency_aware")


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a = {item.strip().lower() for item in left if item.strip()}
    b = {item.strip().lower() for item in right if item.strip()}
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _features(case: dict[str, Any]) -> dict[str, float]:
    return {
        "semantic": _jaccard(case["source_surface_terms"], case["target_surface_terms"]),
        "skill": _jaccard(case["source_skill_tags"], case["target_skill_tags"]),
        "dependency": _jaccard(case["source_dependencies"], case["target_dependencies"]),
        "invariant": float(case["invariant_preserved_proposal"]),
        "boundary": float(case["boundary_matched_proposal"]),
        "qoi": float(case["qoi_matched_proposal"]),
        "directional": float(case["directional_mapping_complete_proposal"]),
    }


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _fit_logistic(
    x: list[list[float]],
    y: list[int],
    *,
    iterations: int = 4000,
    learning_rate: float = 0.12,
    l2: float = 0.08,
) -> list[float]:
    if not x or len({*y}) != 2:
        raise ValueError("each family-held-out training fold requires both labels")
    weights = [0.0] * (len(x[0]) + 1)
    n = len(x)
    for _ in range(iterations):
        gradient = [0.0] * len(weights)
        for row, label in zip(x, y, strict=True):
            probability = _sigmoid(weights[0] + sum(w * v for w, v in zip(weights[1:], row)))
            error = probability - label
            gradient[0] += error
            for index, value in enumerate(row, start=1):
                gradient[index] += error * value
        weights[0] -= learning_rate * gradient[0] / n
        for index in range(1, len(weights)):
            regularized = gradient[index] / n + l2 * weights[index]
            weights[index] -= learning_rate * regularized
    return weights


def _predict(weights: list[float], row: list[float]) -> float:
    return _sigmoid(weights[0] + sum(w * v for w, v in zip(weights[1:], row)))


def _roc_auc(labels: list[int], scores: list[float]) -> float:
    positives = [score for label, score in zip(labels, scores, strict=True) if label]
    negatives = [score for label, score in zip(labels, scores, strict=True) if not label]
    if not positives or not negatives:
        raise ValueError("ROC-AUC requires both labels")
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def _average_precision(labels: list[int], scores: list[float]) -> float:
    ranked = sorted(zip(scores, labels, strict=True), key=lambda item: -item[0])
    positive_count = sum(labels)
    if positive_count == 0:
        raise ValueError("average precision requires a positive label")
    true_positives = 0
    false_positives = 0
    previous_recall = 0.0
    area = 0.0
    index = 0
    while index < len(ranked):
        score = ranked[index][0]
        group_labels: list[int] = []
        while index < len(ranked) and ranked[index][0] == score:
            group_labels.append(ranked[index][1])
            index += 1
        true_positives += sum(group_labels)
        false_positives += len(group_labels) - sum(group_labels)
        recall = true_positives / positive_count
        precision = true_positives / (true_positives + false_positives)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def _metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    labels = [int(row["transfer_valid"]) for row in rows]
    scores = [float(row["probability"]) for row in rows]
    decisions = [score >= 0.5 for score in scores]
    epsilon = 1e-12
    q2 = [index for index, row in enumerate(rows) if row["quadrant"] == "Q2"]
    q3 = [index for index, row in enumerate(rows) if row["quadrant"] == "Q3"]
    brier = sum((score - label) ** 2 for score, label in zip(scores, labels, strict=True)) / len(labels)
    log_loss = -sum(
        label * math.log(max(score, epsilon))
        + (1 - label) * math.log(max(1 - score, epsilon))
        for score, label in zip(scores, labels, strict=True)
    ) / len(labels)
    calibration_total = 0.0
    for bin_index in range(5):
        lower = bin_index / 5
        upper = (bin_index + 1) / 5
        members = [
            index
            for index, score in enumerate(scores)
            if lower <= score < upper or (bin_index == 4 and score == 1.0)
        ]
        if members:
            mean_score = sum(scores[index] for index in members) / len(members)
            mean_label = sum(labels[index] for index in members) / len(members)
            calibration_total += len(members) / len(labels) * abs(mean_score - mean_label)
    return {
        "n": len(rows),
        "roc_auc": _roc_auc(labels, scores),
        "average_precision": _average_precision(labels, scores),
        "brier": brier,
        "log_loss": log_loss,
        "ece_5bin": calibration_total,
        "accuracy_at_0_5": sum(int(decision == bool(label)) for decision, label in zip(decisions, labels, strict=True)) / len(labels),
        "q2_true_accept": sum(int(decisions[index]) for index in q2) / len(q2),
        "q3_false_accept": sum(int(decisions[index]) for index in q3) / len(q3),
    }


def evaluate_annotation_gate(benchmark: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    requirement = protocol["annotation_gate"]
    minimum = requirement["minimum_independent_human_or_expert_annotations_per_confirmatory_item"]
    eligible = []
    failures = []
    cases = benchmark.get("cases", [])
    for case in cases:
        annotations = [
            annotation
            for annotation in case.get("annotation_records", [])
            if annotation.get("human_or_expert")
            and annotation.get("independent_of_benchmark_author")
        ]
        has_adjudication = case.get("adjudication") is not None
        passes = (
            case.get("confirmatory_eligible") is True
            and len(annotations) >= minimum
            and (has_adjudication or not requirement["adjudication_required"])
        )
        (eligible if passes else failures).append(case["case_id"])
    empty = not cases
    return {
        "passed": not failures and not empty,
        "confirmatory_item_count": len(eligible),
        "missing_or_ineligible_case_count": len(failures),
        "missing_or_ineligible_case_ids": failures,
        "requirement": requirement,
        "reason": (
            "benchmark has no evaluable cases"
            if empty
            else None
            if not failures
            else "independent annotations and adjudication unavailable"
        ),
    }


def build_pilot_receipt(
    *,
    benchmark: dict[str, Any],
    protocol: dict[str, Any],
    subject_sha: str,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    if len(subject_sha) != 40 or any(character not in "0123456789abcdef" for character in subject_sha):
        raise ValueError("subject_sha must be a lowercase 40-character hexadecimal Git SHA")
    start = time.perf_counter()
    cases = benchmark["cases"]
    families = sorted({case["family"] for case in cases})
    prediction_rows: list[dict[str, Any]] = []
    for held_out_family in families:
        train = [case for case in cases if case["family"] != held_out_family]
        test = [case for case in cases if case["family"] == held_out_family]
        for arm, feature_names in ARM_FEATURES.items():
            train_x = [[_features(case)[name] for name in feature_names] for case in train]
            train_y = [int(case["transfer_valid_proposal"]) for case in train]
            weights = _fit_logistic(train_x, train_y)
            for case in test:
                feature_values = _features(case)
                probability = _predict(weights, [feature_values[name] for name in feature_names])
                prediction_rows.append(
                    {
                        "case_id": case["case_id"],
                        "held_out_family": held_out_family,
                        "quadrant": case["quadrant"],
                        "arm": arm,
                        "transfer_valid": bool(case["transfer_valid_proposal"]),
                        "probability": probability,
                        "decision_at_0_5": probability >= 0.5,
                        "features": {name: feature_values[name] for name in feature_names},
                    }
                )
    arm_metrics = {
        arm: _metrics([row for row in prediction_rows if row["arm"] == arm])
        for arm in ARM_FEATURES
    }
    strongest_control = max(
        CONTROL_ORDER,
        key=lambda arm: (
            arm_metrics[arm]["roc_auc"],
            arm_metrics[arm]["average_precision"],
            -CONTROL_ORDER.index(arm),
        ),
    )
    control = arm_metrics[strongest_control]
    structural = arm_metrics["witnessed_structure"]
    thresholds = protocol["diagnostic_thresholds"]
    checks = {
        "roc_auc_gain": structural["roc_auc"] - control["roc_auc"] >= thresholds["minimum_roc_auc_gain"],
        "average_precision_gain": structural["average_precision"] - control["average_precision"] >= thresholds["minimum_average_precision_gain"],
        "brier_improvement": (
            structural["brier"] < control["brier"]
            if thresholds["require_brier_improvement"]
            else True
        ),
        "q2_true_accept": structural["q2_true_accept"] >= thresholds["minimum_q2_true_accept"],
        "q3_false_accept": structural["q3_false_accept"] <= thresholds["maximum_q3_false_accept"],
    }
    diagnostic_gate = {
        "passed": all(checks.values()),
        "strongest_control": strongest_control,
        "checks": checks,
        "thresholds": thresholds,
        "observed_deltas": {
            "roc_auc_gain": structural["roc_auc"] - control["roc_auc"],
            "average_precision_gain": structural["average_precision"] - control["average_precision"],
            "brier_reduction": control["brier"] - structural["brier"],
        },
    }
    annotation_gate = evaluate_annotation_gate(benchmark, protocol)
    overall = annotation_gate["passed"] and diagnostic_gate["passed"]
    if not annotation_gate["passed"]:
        verdict = "FAIL_CLOSED_MISSING_INDEPENDENT_ANNOTATION"
    elif not diagnostic_gate["passed"]:
        verdict = "STOP_NARROW_DIAGNOSTIC_SIGNAL_GATE_FAILED"
    else:
        verdict = "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
    elapsed_ms = int(round((time.perf_counter() - start) * 1000))
    return {
        "schema_version": "paper3-cheap-gate-result-v1",
        "experiment_id": "paper3-cheap-gate-lofo-v1-20260810",
        "subject_sha": subject_sha,
        "created_at_utc": created_at_utc
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "frozen_protocol_id": protocol["protocol_id"],
        "protocol_sha256": _canonical_hash(protocol),
        "benchmark_id": benchmark["benchmark_id"],
        "benchmark_sha256": _canonical_hash(benchmark),
        "claim_boundary": "Internal constructed diagnostic only; not independent annotation, natural generalization, training efficiency, or inference efficiency evidence.",
        "predictor": "deterministic local L2 logistic regression; no foundation-model judgement",
        "split": "leave_one_family_out",
        "family_count": len(families),
        "case_count": len(cases),
        "arm_metrics": arm_metrics,
        "predictions": prediction_rows,
        "annotation_gate": annotation_gate,
        "diagnostic_signal_gate": diagnostic_gate,
        "overall_cheap_gate_passed": overall,
        "expensive_training_authorized": overall,
        "gate_verdict": verdict,
        "execution_cost": {
            "wall_time_ms": elapsed_ms,
            "provider_cost_usd": 0.0,
            "gpu_seconds": 0.0,
            "external_model_calls": 0,
        },
        "negative_history": []
        if overall
        else [
            {
                "residual_id": "P3-EMP-01",
                "status": "OPEN_FAIL_CLOSED",
                "reason": annotation_gate["reason"] or "diagnostic signal gate failed",
                "supersession_rule": "retain until genuinely independent annotations and adjudication are received",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    receipt = build_pilot_receipt(
        benchmark=benchmark,
        protocol=protocol,
        subject_sha=args.subject_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
