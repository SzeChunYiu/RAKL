from __future__ import annotations

import json
import inspect
from pathlib import Path

from rakl.paper3_cheap_gate import build_pilot_receipt, evaluate_annotation_gate
from rakl.paper3_cheap_gate_figure import generate_cheap_gate_figure


ROOT = Path(__file__).resolve().parents[1]


def _toy_benchmark() -> dict:
    cases = []
    for family in ("alpha", "beta", "gamma"):
        for quadrant, valid, semantic, dependency, invariant, boundary in (
            ("Q1", True, ("shared", "terms"), ("a>b", "b>c"), True, True),
            ("Q2", True, ("source",), ("a>b", "b>c"), True, True),
            ("Q3", False, ("shared", "terms"), ("a>b", "b>c"), False, False),
            ("Q4", False, ("source",), ("x>y",), False, False),
        ):
            target_terms = semantic if quadrant in {"Q1", "Q3"} else ("target",)
            cases.append(
                {
                    "case_id": f"{family}-{quadrant}",
                    "family": family,
                    "quadrant": quadrant,
                    "source_surface_terms": list(semantic),
                    "target_surface_terms": list(target_terms),
                    "source_skill_tags": ["skill"],
                    "target_skill_tags": ["skill"] if quadrant != "Q4" else ["other"],
                    "source_dependencies": ["a>b", "b>c"],
                    "target_dependencies": list(dependency),
                    "invariant_preserved_proposal": invariant,
                    "boundary_matched_proposal": boundary,
                    "qoi_matched_proposal": quadrant != "Q4",
                    "directional_mapping_complete_proposal": quadrant != "Q4",
                    "transfer_valid_proposal": valid,
                    "confirmatory_eligible": False,
                    "annotation_records": [],
                    "adjudication": None,
                }
            )
    return {
        "schema_version": "toy",
        "benchmark_id": "toy",
        "authority_status": "internal_proposal_only",
        "cases": cases,
    }


def _protocol() -> dict:
    return {
        "protocol_id": "toy-protocol",
        "diagnostic_thresholds": {
            "minimum_roc_auc_gain": 0.05,
            "minimum_average_precision_gain": 0.05,
            "require_brier_improvement": True,
            "minimum_q2_true_accept": 0.8,
            "maximum_q3_false_accept": 0.2,
        },
        "annotation_gate": {
            "minimum_independent_human_or_expert_annotations_per_confirmatory_item": 2,
            "adjudication_required": True,
            "all_evaluated_items_confirmatory_eligible": True,
        },
    }


def test_annotation_gate_fails_closed_for_same_session_proposals() -> None:
    benchmark = json.loads(
        (ROOT / "research" / "PAPER3_CHEAP_GATE_BENCHMARK_PROPOSAL_20260810.json").read_text()
    )
    result = evaluate_annotation_gate(benchmark, _protocol())
    assert result["passed"] is False
    assert result["confirmatory_item_count"] == 0
    assert result["missing_or_ineligible_case_count"] == 44


def test_annotation_gate_fails_closed_when_benchmark_is_empty() -> None:
    result = evaluate_annotation_gate({"cases": []}, _protocol())
    assert result["passed"] is False
    assert result["reason"] == "benchmark has no evaluable cases"


def test_incremental_pilot_is_family_held_out_and_scale_fails_without_annotations() -> None:
    receipt = build_pilot_receipt(
        benchmark=_toy_benchmark(),
        protocol=_protocol(),
        subject_sha="a" * 40,
        created_at_utc="2026-08-10T00:00:00Z",
    )
    assert receipt["split"] == "leave_one_family_out"
    assert {row["held_out_family"] for row in receipt["predictions"]} == {
        "alpha",
        "beta",
        "gamma",
    }
    assert receipt["diagnostic_signal_gate"]["passed"] is True
    assert receipt["annotation_gate"]["passed"] is False
    assert receipt["overall_cheap_gate_passed"] is False
    assert receipt["expensive_training_authorized"] is False
    assert receipt["gate_verdict"] == "FAIL_CLOSED_MISSING_INDEPENDENT_ANNOTATION"


def test_receipt_preserves_arm_metrics_and_q2_q3_safety() -> None:
    receipt = build_pilot_receipt(
        benchmark=_toy_benchmark(),
        protocol=_protocol(),
        subject_sha="b" * 40,
        created_at_utc="2026-08-10T00:00:00Z",
    )
    metrics = receipt["arm_metrics"]
    assert set(metrics) == {
        "semantic_calibrated",
        "skill_aware",
        "dependency_aware",
        "witnessed_structure",
    }
    assert metrics["witnessed_structure"]["q2_true_accept"] >= 0.8
    assert metrics["witnessed_structure"]["q3_false_accept"] <= 0.2
    assert receipt["claim_boundary"].startswith("Internal constructed diagnostic")


def test_figure_is_receipt_driven_vector_output_without_data_callouts(tmp_path: Path) -> None:
    receipt = build_pilot_receipt(
        benchmark=_toy_benchmark(),
        protocol=_protocol(),
        subject_sha="c" * 40,
        created_at_utc="2026-08-10T00:00:00Z",
    )
    output_prefix = tmp_path / "cheap_gate"
    outputs = generate_cheap_gate_figure(receipt=receipt, output_prefix=output_prefix)
    assert {path.suffix for path in outputs} == {".pdf", ".svg", ".png"}
    assert all(path.stat().st_size > 1000 for path in outputs)
    source = inspect.getsource(generate_cheap_gate_figure)
    assert ".annotate(" not in source
    assert ".text(" not in source
    assert "arrow" not in source.lower()


def test_checked_receipt_preserves_fail_closed_scale_decision() -> None:
    receipt = json.loads(
        (ROOT / "research" / "receipts" / "PAPER3_CHEAP_GATE_RESULT_20260810.json").read_text()
    )
    assert receipt["subject_sha"] == "f2701f732f832698508fa5310e9b309b20e10734"
    assert receipt["family_count"] == 11
    assert receipt["case_count"] == 44
    assert receipt["diagnostic_signal_gate"]["passed"] is True
    assert receipt["annotation_gate"]["confirmatory_item_count"] == 0
    assert receipt["overall_cheap_gate_passed"] is False
    assert receipt["expensive_training_authorized"] is False
    assert receipt["gate_verdict"] == "FAIL_CLOSED_MISSING_INDEPENDENT_ANNOTATION"
