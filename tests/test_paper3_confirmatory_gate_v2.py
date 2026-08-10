from __future__ import annotations

import json
import hashlib
from copy import deepcopy
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

import rakl.paper3_confirmatory_gate as gate_module

from rakl.paper3_annotation import (
    REQUIRED_V1_BENCHMARK_CANONICAL_SHA256,
    canonical_sha256,
)
from rakl.paper3_confirmatory_gate import (
    EXPECTED_SUPPORT_REQUIREMENTS,
    build_confirmatory_gate_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def _benchmark() -> dict:
    cases = []
    for family in ("alpha", "beta", "gamma"):
        for quadrant, valid, invariant, boundary in (
            ("Q1", True, True, True),
            ("Q2", True, True, True),
            ("Q3", False, False, False),
            ("Q4", False, False, False),
        ):
            high_semantic = quadrant in {"Q1", "Q3"}
            judgements = {
                "semantic_similarity_high": high_semantic,
                "structural_match": valid,
                "roles_preserved": valid,
                "typed_relations_preserved": valid,
                "invariant_preserved": invariant,
                "boundary_matched": boundary,
                "qoi_matched": quadrant != "Q4",
                "directional_mapping_complete": quadrant != "Q4",
                "transfer_valid": valid,
            }
            cases.append(
                {
                    "case_id": f"{family}-{quadrant}",
                    "family": family,
                    "source_domain": f"source-{family}",
                    "target_domain": f"target-{family}",
                    "quadrant": quadrant,
                    "source_surface_terms": ["shared", "terms"] if high_semantic else ["source"],
                    "target_surface_terms": ["shared", "terms"] if high_semantic else ["target"],
                    "source_skill_tags": ["skill"],
                    "target_skill_tags": ["skill"] if quadrant != "Q4" else ["other"],
                    "source_dependencies": ["a>b", "b>c"],
                    "target_dependencies": ["a>b", "b>c"] if quadrant != "Q4" else ["x>y"],
                    "candidate_load_bearing_invariant": "synthetic invariant",
                    "candidate_load_bearing_boundary": "synthetic boundary",
                    "qoi": "synthetic transfer validity",
                    "source_evidence": [f"evidence:source:{family}:{quadrant}"],
                    "target_evidence": [f"evidence:target:{family}:{quadrant}"],
                    **judgements,
                    "confirmatory_eligible": True,
                    "annotation_records": [
                        {
                            "annotator_id": "annotator-a",
                            "annotation_id": f"{family}-{quadrant}:annotator-a",
                            "annotator_type": "externally_provenanced_human_or_domain_expert",
                            "human_or_expert": True,
                            "independent_of_benchmark_author": True,
                            "status": "final",
                            "judgements": judgements,
                            "rationale": "synthetic independent judgement",
                            "evidence_refs": [f"evidence:source:{family}:{quadrant}"],
                            "completed_at_utc": "2026-08-10T20:00:00Z",
                        },
                        {
                            "annotator_id": "annotator-b",
                            "annotation_id": f"{family}-{quadrant}:annotator-b",
                            "annotator_type": "externally_provenanced_human_or_domain_expert",
                            "human_or_expert": True,
                            "independent_of_benchmark_author": True,
                            "status": "final",
                            "judgements": judgements,
                            "rationale": "synthetic independent judgement",
                            "evidence_refs": [f"evidence:target:{family}:{quadrant}"],
                            "completed_at_utc": "2026-08-10T20:05:00Z",
                        },
                    ],
                    "adjudication": {
                        "adjudicator_id": "adjudicator-c",
                        "human_or_expert": True,
                        "independent_of_benchmark_author": True,
                        "status": "final",
                        "judgements": judgements,
                        "resolution_rationale": "synthetic frozen adjudication",
                        "evidence_refs": [
                            f"evidence:source:{family}:{quadrant}",
                            f"evidence:target:{family}:{quadrant}",
                        ],
                        "completed_at_utc": "2026-08-10T21:00:00Z",
                    },
                }
            )
    return {
        "schema_version": "paper3-confirmatory-benchmark-v2",
        "benchmark_id": "synthetic-test-only",
        "authority_status": "independently_annotated_and_adjudicated_v2",
        "protocol_id": "paper3-confirmatory-gate-v2",
        "protocol_sha256": canonical_sha256(_protocol()),
        "rubric_id": "paper3-annotation-rubric-v2-20260810",
        "rubric_sha256": "c" * 64,
        "subject_sha": SHA,
        "source_set_id": "synthetic-source-set-v2",
        "source_set_sha256": "1" * 64,
        "source_set_frozen_at_utc": "2026-08-10T19:00:00Z",
        "packet_id": "synthetic-packet-v2",
        "packet_sha256": "2" * 64,
        "packet_frozen_at_utc": "2026-08-10T19:30:00Z",
        "provenance_audit_sha256": "3" * 64,
        "negative_history_benchmark_sha256": [REQUIRED_V1_BENCHMARK_CANONICAL_SHA256],
        "annotation_completed_at_utc": [
            "2026-08-10T20:00:00Z",
            "2026-08-10T20:05:00Z",
        ],
        "adjudication_completed_at_utc": "2026-08-10T21:00:00Z",
        "coordinate_exact_agreement": {
            field: 1.0
            for field in (
                "semantic_similarity_high",
                "structural_match",
                "roles_preserved",
                "typed_relations_preserved",
                "invariant_preserved",
                "boundary_matched",
                "qoi_matched",
                "directional_mapping_complete",
                "transfer_valid",
            )
        },
        "coordinate_conflict_count": {
            field: 0
            for field in (
                "semantic_similarity_high",
                "structural_match",
                "roles_preserved",
                "typed_relations_preserved",
                "invariant_preserved",
                "boundary_matched",
                "qoi_matched",
                "directional_mapping_complete",
                "transfer_valid",
            )
        },
        "cases": cases,
    }


def _protocol() -> dict:
    return json.loads(
        (ROOT / "research/PAPER3_CONFIRMATORY_GATE_PROTOCOL_V2_20260810.json").read_text()
    )


def _import_receipt(benchmark: dict, *, passed: bool = True) -> dict:
    return {
        "schema_version": "paper3-annotation-import-receipt-v2",
        "subject_sha": SHA,
        "protocol_id": "paper3-confirmatory-gate-v2",
        "protocol_sha256": canonical_sha256(_protocol()),
        "source_set_sha256": "1" * 64,
        "packet_sha256": "2" * 64,
        "submission_sha256": ["4" * 64, "5" * 64],
        "adjudication_sha256": "6" * 64,
        "provenance_audit_sha256": "3" * 64,
        "passed": passed,
        "failures": [] if passed else ["synthetic_annotation_import_not_passed"],
        "coordinate_exact_agreement": benchmark["coordinate_exact_agreement"] if passed else {},
        "coordinate_conflict_count": benchmark["coordinate_conflict_count"] if passed else {},
        "training_authorized": False,
        "benchmark_sha256": canonical_sha256(benchmark) if passed else None,
        "negative_history_benchmark_sha256": [REQUIRED_V1_BENCHMARK_CANONICAL_SHA256],
    }


def test_v2_gate_refuses_missing_annotation_import_before_model_fit() -> None:
    benchmark = _benchmark()
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=_protocol(),
        import_receipt=_import_receipt(benchmark, passed=False),
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["annotation_gate"]["passed"] is False
    assert receipt["diagnostic_signal_gate"]["status"] == "NOT_RUN"
    assert receipt["expensive_training_authorized"] is False
    assert receipt["gate_verdict"] == "FAIL_CLOSED_ANNOTATION_GATE"


def test_v2_protocol_freezes_exact_evaluator_sources_and_fit_parameters() -> None:
    protocol = _protocol()
    binding = protocol["evaluator_binding"]
    assert binding["evaluator_source_sha256"] == hashlib.sha256(
        (ROOT / binding["evaluator_path"]).read_bytes()
    ).hexdigest()
    assert binding["fit_source_sha256"] == hashlib.sha256(
        (ROOT / binding["fit_source_path"]).read_bytes()
    ).hexdigest()
    assert binding["fit_hyperparameters"] == {
        "initialization": "all_zero",
        "intercept_regularized": False,
        "iterations": 4000,
        "l2": 0.08,
        "learning_rate": 0.12,
    }
    assert protocol["support_requirements"] == EXPECTED_SUPPORT_REQUIREMENTS


@pytest.mark.parametrize("artifact", ["benchmark", "import_receipt"])
def test_v2_gate_schema_validates_full_inputs_before_fit(
    artifact: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark = _benchmark()
    import_receipt = _import_receipt(benchmark)
    if artifact == "benchmark":
        del benchmark["source_set_id"]
        import_receipt["benchmark_sha256"] = canonical_sha256(benchmark)
    else:
        del import_receipt["source_set_sha256"]

    def fit_must_not_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("fit executed before full schema validation")

    monkeypatch.setattr(gate_module, "_fit_logistic", fit_must_not_run)
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=_protocol(),
        import_receipt=import_receipt,
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["annotation_gate"]["passed"] is False
    assert f"{artifact}_schema_validation_failed" in receipt["annotation_gate"]["failures"]
    assert receipt["predictions"] == []
    assert receipt["expensive_training_authorized"] is False


def test_v2_gate_fails_closed_with_machine_readable_degenerate_lofo_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark = _benchmark()
    benchmark["cases"] = [
        case
        for case in benchmark["cases"]
        if not (case["family"] == "alpha" and case["transfer_valid"] is False)
    ]
    import_receipt = _import_receipt(benchmark)

    def fit_must_not_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("fit executed for degenerate LOFO split")

    monkeypatch.setattr(gate_module, "_fit_logistic", fit_must_not_run)
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=_protocol(),
        import_receipt=import_receipt,
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["annotation_gate"]["passed"] is True
    assert receipt["diagnostic_signal_gate"]["status"] == "NOT_RUN"
    assert receipt["diagnostic_signal_gate"]["passed"] is False
    assert receipt["diagnostic_signal_gate"]["support_requirements"] == EXPECTED_SUPPORT_REQUIREMENTS
    assert "minimum_negative_cases_per_family_not_met:alpha" in receipt[
        "diagnostic_signal_gate"
    ]["failures"]
    assert receipt["gate_verdict"] == "FAIL_CLOSED_DEGENERATE_LOFO_SUPPORT"
    assert receipt["predictions"] == []
    assert receipt["expensive_training_authorized"] is False


def test_v2_gate_fails_closed_when_frozen_evaluator_binding_is_changed() -> None:
    benchmark = _benchmark()
    protocol = _protocol()
    protocol["evaluator_binding"]["fit_hyperparameters"]["iterations"] = 3999
    benchmark["protocol_sha256"] = canonical_sha256(protocol)
    import_receipt = _import_receipt(benchmark)
    import_receipt["protocol_sha256"] = canonical_sha256(protocol)
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=protocol,
        import_receipt=import_receipt,
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["annotation_gate"]["passed"] is False
    assert "frozen_evaluator_binding_mismatch" in receipt["annotation_gate"]["failures"]
    assert receipt["diagnostic_signal_gate"]["status"] == "NOT_RUN"
    assert receipt["expensive_training_authorized"] is False


def test_v2_gate_rejects_any_proposal_field_in_confirmatory_benchmark() -> None:
    benchmark = _benchmark()
    benchmark["cases"][0]["transfer_valid_proposal"] = True
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=_protocol(),
        import_receipt=_import_receipt(benchmark),
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["expensive_training_authorized"] is False
    assert receipt["gate_verdict"] == "FAIL_CLOSED_PROPOSAL_FIELD_PRESENT"
    assert receipt["predictions"] == []


def test_v2_gate_rejects_subject_or_protocol_hash_mismatch() -> None:
    benchmark = _benchmark()
    import_receipt = _import_receipt(benchmark)
    benchmark["subject_sha"] = "0" * 40
    benchmark["protocol_sha256"] = "0" * 64
    import_receipt["benchmark_sha256"] = canonical_sha256(benchmark)
    receipt = build_confirmatory_gate_receipt(
        benchmark=benchmark,
        protocol=_protocol(),
        import_receipt=import_receipt,
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["annotation_gate"]["passed"] is False
    assert "benchmark_protocol_hash_mismatch" in receipt["annotation_gate"]["failures"]
    assert "annotation_import_subject_mismatch" in receipt["annotation_gate"]["failures"]
    assert "gate_subject_sha_mismatch" in receipt["annotation_gate"]["failures"]
    assert receipt["expensive_training_authorized"] is False


def test_v2_gate_uses_only_canonical_adjudicated_fields_and_frozen_thresholds() -> None:
    benchmark = _benchmark()
    receipt = build_confirmatory_gate_receipt(
        benchmark=deepcopy(benchmark),
        protocol=_protocol(),
        import_receipt=_import_receipt(benchmark),
        subject_sha=SHA,
        created_at_utc="2026-08-10T22:00:00Z",
    )
    assert receipt["split"] == "leave_one_family_out"
    assert receipt["annotation_gate"]["passed"] is True
    assert receipt["diagnostic_signal_gate"]["passed"] is True
    assert receipt["arm_metrics"]["witnessed_structure"]["q2_true_accept"] >= 0.8
    assert receipt["arm_metrics"]["witnessed_structure"]["q3_false_accept"] <= 0.2
    assert receipt["overall_cheap_gate_passed"] is True
    assert receipt["expensive_training_authorized"] is True
    assert receipt["gate_verdict"] == "PASS_AUTHORIZE_CONDITIONAL_NEXT_PHASE"
    schema = json.loads(
        (ROOT / "schemas/paper3-confirmatory-gate-result.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
