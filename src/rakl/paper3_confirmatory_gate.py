from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from . import paper3_cheap_gate as cheap_gate_module
from .inference import InferenceStatus, paired_lift_verdict
from .paper3_annotation import canonical_sha256, evaluate_annotation_gate_v2
from .paper3_cheap_gate import (
    ARM_FEATURES,
    CONTROL_ORDER,
    _fit_logistic,
    _jaccard,
    _metrics,
    _predict,
)


EXPECTED_FIT_HYPERPARAMETERS = {
    "initialization": "all_zero",
    "intercept_regularized": False,
    "iterations": 4000,
    "l2": 0.08,
    "learning_rate": 0.12,
}
EXPECTED_SUPPORT_REQUIREMENTS = {
    "minimum_family_count": 3,
    "minimum_cases_per_family": 4,
    "minimum_positive_cases_per_family": 1,
    "minimum_negative_cases_per_family": 1,
    "minimum_positive_training_cases_per_fold": 2,
    "minimum_negative_training_cases_per_fold": 2,
}

# Defaults used when the frozen protocol does not carry a statistical_inference
# block.  The confirmatory protocol on disk binds these values explicitly.
_DEFAULT_INFERENCE_CONFIG = {
    "alpha": 0.05,
    "bootstrap_resamples": 10000,
    "permutation_resamples": 10000,
    "seed": 20260810,
}


def _frozen_evaluator_binding_matches(protocol: dict[str, Any]) -> bool:
    binding = protocol.get("evaluator_binding", {})
    fit_path = Path(str(cheap_gate_module.__file__)).resolve()
    evaluator_path = Path(__file__).resolve()
    return bool(
        binding.get("evaluator_path") == "src/rakl/paper3_confirmatory_gate.py"
        and binding.get("fit_source_path") == "src/rakl/paper3_cheap_gate.py"
        and binding.get("evaluator_source_sha256")
        == hashlib.sha256(evaluator_path.read_bytes()).hexdigest()
        and binding.get("fit_source_sha256")
        == hashlib.sha256(fit_path.read_bytes()).hexdigest()
        and binding.get("fit_hyperparameters") == EXPECTED_FIT_HYPERPARAMETERS
        and protocol.get("support_requirements") == EXPECTED_SUPPORT_REQUIREMENTS
    )


def _inference_config(protocol: dict[str, Any]) -> dict[str, Any]:
    """Read the frozen statistical-inference block, falling back to defaults."""
    configured = protocol.get("statistical_inference") or {}
    return {
        "alpha": configured.get("alpha", _DEFAULT_INFERENCE_CONFIG["alpha"]),
        "bootstrap_resamples": configured.get(
            "bootstrap_resamples", _DEFAULT_INFERENCE_CONFIG["bootstrap_resamples"]
        ),
        "permutation_resamples": configured.get(
            "permutation_resamples", _DEFAULT_INFERENCE_CONFIG["permutation_resamples"]
        ),
        "seed": configured.get("seed", _DEFAULT_INFERENCE_CONFIG["seed"]),
    }


def _paired_brier_reduction_diffs(
    prediction_rows: list[dict[str, Any]],
    *,
    structural_arm: str,
    control_arm: str,
) -> list[float]:
    """Per-item paired Brier reduction (control minus structural).

    Each item contributes ``brier_control_i - brier_structural_i`` where
    ``brier = (probability - label) ** 2``.  A positive difference means the
    structural witness reduced Brier error on that item relative to the control.
    Items are paired by ``case_id``; items present in only one arm are dropped.
    """
    structural_by_case: dict[str, dict[str, Any]] = {}
    control_by_case: dict[str, dict[str, Any]] = {}
    for row in prediction_rows:
        arm = row["arm"]
        if arm == structural_arm:
            structural_by_case[row["case_id"]] = row
        elif arm == control_arm:
            control_by_case[row["case_id"]] = row
    diffs: list[float] = []
    for case_id in sorted(structural_by_case.keys() & control_by_case.keys()):
        structural = structural_by_case[case_id]
        control = control_by_case[case_id]
        label = int(structural["transfer_valid"])
        brier_structural = (float(structural["probability"]) - label) ** 2
        brier_control = (float(control["probability"]) - label) ** 2
        diffs.append(brier_control - brier_structural)
    return diffs


def _diagnostic_inference(
    prediction_rows: list[dict[str, Any]],
    *,
    structural_arm: str,
    control_arm: str,
    protocol: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """Run the paired uncertainty gate on item-level Brier reductions.

    Returns ``(check_passed, details)``.  When fewer than three paired items are
    available the bootstrap is unstable, so the check falls back to the legacy
    point-estimate path (does not block) and records the fallback status — this
    is the backward-compatibility escape hatch.  Otherwise the confirmatory
    verdict requires the bootstrap CI to exclude zero.
    """
    config = _inference_config(protocol)
    diffs = _paired_brier_reduction_diffs(
        prediction_rows,
        structural_arm=structural_arm,
        control_arm=control_arm,
    )
    paired_n = len(diffs)
    base = {
        "design": "paired_item_brier_reduction",
        "structural_arm": structural_arm,
        "control_arm": control_arm,
        "paired_n": paired_n,
        "alpha": config["alpha"],
        "bootstrap_resamples": config["bootstrap_resamples"],
        "permutation_resamples": config["permutation_resamples"],
        "seed": config["seed"],
    }
    if paired_n < 3:
        # Backward-compat fallback: cannot run reliable inference at this n.
        return True, {
            **base,
            "status": InferenceStatus.INSUFFICIENT_N.value,
            "point_estimate": (
                sum(diffs) / paired_n if paired_n else 0.0
            ),
            "ci_lo": None,
            "ci_hi": None,
            "p_value": None,
            "excludes_null": False,
            "check_passed": True,
            "fallback_reason": (
                "paired item count below the n>=3 floor; legacy point-estimate "
                "thresholds remain authoritative"
            ),
        }
    verdict = paired_lift_verdict(
        diffs,
        alpha=config["alpha"],
        n_boot=config["bootstrap_resamples"],
        n_perm=config["permutation_resamples"],
        seed=config["seed"],
    )
    return verdict.excludes_null, {
        **base,
        "status": verdict.status.value,
        "point_estimate": verdict.point_estimate,
        "ci_lo": verdict.ci_lo,
        "ci_hi": verdict.ci_hi,
        "p_value": verdict.p_value,
        "excludes_null": verdict.excludes_null,
        "check_passed": verdict.excludes_null,
    }


def _features(case: dict[str, Any]) -> dict[str, float]:
    return {
        "semantic": _jaccard(case["source_surface_terms"], case["target_surface_terms"]),
        "skill": _jaccard(case["source_skill_tags"], case["target_skill_tags"]),
        "dependency": _jaccard(case["source_dependencies"], case["target_dependencies"]),
        "invariant": float(case["invariant_preserved"]),
        "boundary": float(case["boundary_matched"]),
        "qoi": float(case["qoi_matched"]),
        "directional": float(case["directional_mapping_complete"]),
    }


def _proposal_fields(benchmark: dict[str, Any]) -> list[str]:
    return sorted(
        {
            key
            for case in benchmark.get("cases", [])
            for key in case
            if "proposal" in key.lower()
        }
    )


def _base_receipt(
    *, benchmark: dict[str, Any], protocol: dict[str, Any], subject_sha: str, created_at_utc: str
) -> dict[str, Any]:
    return {
        "schema_version": "paper3-confirmatory-gate-result-v2",
        "experiment_id": "paper3-confirmatory-gate-lofo-v2",
        "subject_sha": subject_sha,
        "created_at_utc": created_at_utc,
        "frozen_protocol_id": protocol["protocol_id"],
        "protocol_sha256": canonical_sha256(protocol),
        "benchmark_id": benchmark.get("benchmark_id"),
        "benchmark_sha256": canonical_sha256(benchmark),
        "claim_boundary": (
            "A passing receipt licenses only conditional Paper 3 training/inference pilots; "
            "it is not itself training efficiency, inference efficiency or break-even evidence."
        ),
        "split": "leave_one_family_out",
    }


def _schema_validation_failures(
    instance: dict[str, Any], *, schema_filename: str, artifact: str
) -> list[str]:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / schema_filename
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
        key=lambda error: (list(error.absolute_path), error.validator or ""),
    )
    if not errors:
        return []
    failures = [f"{artifact}_schema_validation_failed"]
    for error in errors:
        path = "/".join(str(part) for part in error.absolute_path) or "$"
        failures.append(f"{artifact}_schema:{path}:{error.validator}")
    return failures


def _lofo_support(
    cases: list[dict[str, Any]], requirements: dict[str, int]
) -> tuple[list[str], dict[str, Any]]:
    families = sorted({case["family"] for case in cases})
    failures: list[str] = []
    if len(families) < requirements["minimum_family_count"]:
        failures.append("minimum_family_count_not_met")
    family_support: dict[str, dict[str, int]] = {}
    training_support: dict[str, dict[str, int]] = {}
    for family in families:
        family_cases = [case for case in cases if case["family"] == family]
        positives = sum(case["transfer_valid"] is True for case in family_cases)
        negatives = sum(case["transfer_valid"] is False for case in family_cases)
        family_support[family] = {
            "case_count": len(family_cases),
            "positive_count": positives,
            "negative_count": negatives,
        }
        if len(family_cases) < requirements["minimum_cases_per_family"]:
            failures.append(f"minimum_cases_per_family_not_met:{family}")
        if positives < requirements["minimum_positive_cases_per_family"]:
            failures.append(f"minimum_positive_cases_per_family_not_met:{family}")
        if negatives < requirements["minimum_negative_cases_per_family"]:
            failures.append(f"minimum_negative_cases_per_family_not_met:{family}")
        training_cases = [case for case in cases if case["family"] != family]
        training_positives = sum(case["transfer_valid"] is True for case in training_cases)
        training_negatives = sum(case["transfer_valid"] is False for case in training_cases)
        training_support[family] = {
            "case_count": len(training_cases),
            "positive_count": training_positives,
            "negative_count": training_negatives,
        }
        if training_positives < requirements["minimum_positive_training_cases_per_fold"]:
            failures.append(
                f"minimum_positive_training_cases_per_fold_not_met:{family}"
            )
        if training_negatives < requirements["minimum_negative_training_cases_per_fold"]:
            failures.append(
                f"minimum_negative_training_cases_per_fold_not_met:{family}"
            )
    return failures, {
        "family_count": len(families),
        "by_family": family_support,
        "training_by_held_out_family": training_support,
    }


def build_confirmatory_gate_receipt(
    *,
    benchmark: dict[str, Any],
    protocol: dict[str, Any],
    import_receipt: dict[str, Any],
    subject_sha: str,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    if len(subject_sha) != 40 or any(character not in "0123456789abcdef" for character in subject_sha):
        raise ValueError("subject_sha must be a lowercase 40-character hexadecimal Git SHA")
    start = time.perf_counter()
    timestamp = created_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    base = _base_receipt(
        benchmark=benchmark,
        protocol=protocol,
        subject_sha=subject_sha,
        created_at_utc=timestamp,
    )
    if not _frozen_evaluator_binding_matches(protocol):
        failures = ["frozen_evaluator_binding_mismatch"]
        return {
            **base,
            "family_count": len({case.get("family") for case in benchmark.get("cases", [])}),
            "case_count": len(benchmark.get("cases", [])),
            "arm_metrics": {},
            "predictions": [],
            "annotation_gate": {"passed": False, "failures": failures},
            "diagnostic_signal_gate": {"status": "NOT_RUN", "passed": False, "checks": {}},
            "overall_cheap_gate_passed": False,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_ANNOTATION_GATE",
            "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
            "negative_history": failures,
        }
    schema_failures = [
        *_schema_validation_failures(
            benchmark,
            schema_filename="paper3-confirmatory-benchmark-v2.schema.json",
            artifact="benchmark",
        ),
        *_schema_validation_failures(
            import_receipt,
            schema_filename="paper3-annotation-import-receipt.schema.json",
            artifact="import_receipt",
        ),
    ]
    proposal_fields = _proposal_fields(benchmark)
    if proposal_fields:
        return {
            **base,
            "family_count": 0,
            "case_count": len(benchmark.get("cases", [])),
            "arm_metrics": {},
            "predictions": [],
            "annotation_gate": {
                "passed": False,
                "failures": ["proposal_fields_present"],
                "proposal_fields": proposal_fields,
            },
            "diagnostic_signal_gate": {"status": "NOT_RUN", "passed": False, "checks": {}},
            "overall_cheap_gate_passed": False,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_PROPOSAL_FIELD_PRESENT",
            "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
            "negative_history": ["confirmatory benchmark contained v1/proposal provenance fields"],
        }

    if schema_failures:
        annotation_gate = {
            "passed": False,
            "failures": schema_failures,
            "confirmatory_item_count": 0,
            "missing_or_ineligible_case_ids": [],
        }
        return {
            **base,
            "family_count": len(
                {case.get("family") for case in benchmark.get("cases", []) if isinstance(case, dict)}
            ),
            "case_count": len(benchmark.get("cases", [])),
            "arm_metrics": {},
            "predictions": [],
            "annotation_gate": annotation_gate,
            "diagnostic_signal_gate": {"status": "NOT_RUN", "passed": False, "checks": {}},
            "overall_cheap_gate_passed": False,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_ANNOTATION_GATE",
            "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
            "negative_history": schema_failures,
        }

    annotation_gate = evaluate_annotation_gate_v2(benchmark, protocol, import_receipt)
    if benchmark.get("subject_sha") != subject_sha or import_receipt.get("subject_sha") != subject_sha:
        annotation_gate["failures"].append("gate_subject_sha_mismatch")
        annotation_gate["failures"] = list(dict.fromkeys(annotation_gate["failures"]))
        annotation_gate["passed"] = False
    if not annotation_gate["passed"]:
        return {
            **base,
            "family_count": len({case.get("family") for case in benchmark.get("cases", [])}),
            "case_count": len(benchmark.get("cases", [])),
            "arm_metrics": {},
            "predictions": [],
            "annotation_gate": annotation_gate,
            "diagnostic_signal_gate": {"status": "NOT_RUN", "passed": False, "checks": {}},
            "overall_cheap_gate_passed": False,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_ANNOTATION_GATE",
            "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
            "negative_history": annotation_gate["failures"],
        }

    cases = benchmark["cases"]
    families = sorted({case["family"] for case in cases})
    support_requirements = protocol["support_requirements"]
    support_failures, observed_support = _lofo_support(cases, support_requirements)
    if support_failures:
        return {
            **base,
            "family_count": len(families),
            "case_count": len(cases),
            "arm_metrics": {},
            "predictions": [],
            "annotation_gate": annotation_gate,
            "diagnostic_signal_gate": {
                "status": "NOT_RUN",
                "passed": False,
                "checks": {},
                "support_requirements": support_requirements,
                "observed_support": observed_support,
                "failures": support_failures,
            },
            "overall_cheap_gate_passed": False,
            "expensive_training_authorized": False,
            "gate_verdict": "FAIL_CLOSED_DEGENERATE_LOFO_SUPPORT",
            "execution_cost": {"wall_time_ms": 0, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
            "negative_history": support_failures,
        }
    prediction_rows: list[dict[str, Any]] = []
    for held_out_family in families:
        train = [case for case in cases if case["family"] != held_out_family]
        test = [case for case in cases if case["family"] == held_out_family]
        for arm, feature_names in ARM_FEATURES.items():
            train_x = [[_features(case)[name] for name in feature_names] for case in train]
            train_y = [int(case["transfer_valid"]) for case in train]
            fit = protocol["evaluator_binding"]["fit_hyperparameters"]
            weights = _fit_logistic(
                train_x,
                train_y,
                iterations=fit["iterations"],
                learning_rate=fit["learning_rate"],
                l2=fit["l2"],
            )
            for case in test:
                feature_values = _features(case)
                probability = _predict(weights, [feature_values[name] for name in feature_names])
                prediction_rows.append(
                    {
                        "case_id": case["case_id"],
                        "held_out_family": held_out_family,
                        "quadrant": case["quadrant"],
                        "arm": arm,
                        "transfer_valid": case["transfer_valid"],
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
        "brier_improvement": structural["brier"] < control["brier"] if thresholds["require_brier_improvement"] else True,
        "q2_true_accept": structural["q2_true_accept"] >= thresholds["minimum_q2_true_accept"],
        "q3_false_accept": structural["q3_false_accept"] <= thresholds["maximum_q3_false_accept"],
    }
    # Uncertainty quantification (issue #161): layer a paired bootstrap CI on
    # top of the bare point-estimate thresholds.  When item-level paired
    # predictions exist, the confirmatory verdict additionally requires the CI
    # of the per-item Brier reduction to exclude zero.  The legacy point path
    # remains as a fallback when paired data is absent / below the n>=3 floor.
    inference_check, inference_details = _diagnostic_inference(
        prediction_rows,
        structural_arm="witnessed_structure",
        control_arm=strongest_control,
        protocol=protocol,
    )
    checks["paired_brier_lift_distinguishable"] = inference_check
    diagnostic_gate = {
        "status": "RUN",
        "passed": all(checks.values()),
        "strongest_control": strongest_control,
        "checks": checks,
        "thresholds": thresholds,
        "observed_deltas": {
            "roc_auc_gain": structural["roc_auc"] - control["roc_auc"],
            "average_precision_gain": structural["average_precision"] - control["average_precision"],
            "brier_reduction": control["brier"] - structural["brier"],
        },
        "statistical_inference": inference_details,
    }
    passed = diagnostic_gate["passed"]
    elapsed_ms = int(round((time.perf_counter() - start) * 1000))
    return {
        **base,
        "family_count": len(families),
        "case_count": len(cases),
        "arm_metrics": arm_metrics,
        "predictions": prediction_rows,
        "annotation_gate": annotation_gate,
        "diagnostic_signal_gate": diagnostic_gate,
        "overall_cheap_gate_passed": passed,
        "expensive_training_authorized": passed,
        "gate_verdict": "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE" if passed else "STOP_NARROW_DIAGNOSTIC_SIGNAL_GATE_FAILED",
        "execution_cost": {"wall_time_ms": elapsed_ms, "provider_cost_usd": 0.0, "gpu_seconds": 0.0},
        "negative_history": [] if passed else ["v2 diagnostic signal gate failed frozen thresholds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--import-receipt", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_confirmatory_gate_receipt(
        benchmark=json.loads(args.benchmark.read_text(encoding="utf-8")),
        protocol=json.loads(args.protocol.read_text(encoding="utf-8")),
        import_receipt=json.loads(args.import_receipt.read_text(encoding="utf-8")),
        subject_sha=args.subject_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0 if receipt["overall_cheap_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
