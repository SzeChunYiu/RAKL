"""Stable RAKL_math cycle metrology (#446 / Paper V longitudinal lane).

Process evidence only.  Missing denominators and unavailable counters stay
``CANNOT_MEASURE``; they are never replaced by zero.  Rates may appear only
when the corresponding opportunity denominator is a non-negative integer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence, Tuple

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]

SCHEMA_VERSION = "rakl-cycle-metrics-v1"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "rakl-cycle-metrics.schema.json"

_RATE_FIELDS_REQUIRING_MEMORY_UNIVERSE = (
    "relevant_root_recall",
    "counterevidence_recall",
)
_RATE_FIELDS_REQUIRING_ROUTE_DENOMINATOR = ("route_change_rate",)


def schema_path() -> Path:
    return _SCHEMA_PATH


def load_schema() -> dict[str, Any]:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def is_cannot_measure(value: Any) -> bool:
    return isinstance(value, Mapping) and value.get("status") == "CANNOT_MEASURE"


def cannot_measure(reason: str) -> dict[str, str]:
    return {"status": "CANNOT_MEASURE", "reason": reason}


def measured_count(value: int) -> int:
    if value < 0:
        raise ValueError("measured count must be non-negative")
    return value


def validate_schema_document(document: Mapping[str, Any]) -> Tuple[str, ...]:
    """Validate ``document`` against the frozen JSON Schema."""
    if Draft202012Validator is None or FormatChecker is None:
        return ("jsonschema unavailable",)
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        f"{'.'.join(str(part) for part in err.path)}: {err.message}"
        for err in validator.iter_errors(document)
    )
    return tuple(errors)


def audit_rate_denominators(document: Mapping[str, Any]) -> Tuple[str, ...]:
    """Refuse numeric rates when required opportunity denominators are unknown."""
    reasons: list[str] = []
    denominators = document.get("opportunity_denominators", {})
    retrieval = document.get("retrieval", {})
    performance = document.get("longitudinal_performance_vector", {})
    search = performance.get("search_utility", {})

    universe = denominators.get("eligible_memory_universe_count")
    routes = denominators.get("registered_route_options")

    if is_cannot_measure(universe):
        for field in _RATE_FIELDS_REQUIRING_MEMORY_UNIVERSE:
            value = retrieval.get(field)
            if isinstance(value, (int, float)):
                reasons.append(
                    f"retrieval.{field} is numeric but "
                    "opportunity_denominators.eligible_memory_universe_count is CANNOT_MEASURE"
                )
            perf_value = search.get(field)
            if isinstance(perf_value, (int, float)):
                reasons.append(
                    f"longitudinal_performance_vector.search_utility.{field} is numeric but "
                    "opportunity_denominators.eligible_memory_universe_count is CANNOT_MEASURE"
                )

    if is_cannot_measure(routes):
        value = search.get("route_change_rate")
        if isinstance(value, (int, float)):
            reasons.append(
                "longitudinal_performance_vector.search_utility.route_change_rate is numeric but "
                "opportunity_denominators.registered_route_options is CANNOT_MEASURE"
            )

    return tuple(reasons)


def audit_cycle_metrics(document: Mapping[str, Any]) -> Tuple[str, ...]:
    """Schema validation plus denominator/rate consistency checks."""
    return validate_schema_document(document) + audit_rate_denominators(document)


def minimal_cycle_metrics_template(*, cycle_id: str, reason: str) -> dict[str, Any]:
    """Return a schema-valid skeleton with unknown denominators marked CANNOT_MEASURE."""
    cm = cannot_measure
    return {
        "schema_version": SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "recorded_at_utc": "2026-08-12T00:00:00Z",
        "subjects": {
            "framework_sha": "0" * 40,
            "method_version": "3.0.0",
            "application_base_sha": "1" * 40,
            "application_result_sha": cm("result commit not frozen at metrics emission"),
            "problem_root": "EXAMPLE_ROOT",
            "atom_id": "EXAMPLE-ATOM",
            "fibre_hash": "sha256:" + "a" * 64,
            "pre_action_receipt_hash": "b" * 64,
        },
        "opportunity_denominators": {
            "eligible_memory_universe_count": cm(reason),
            "eligible_relevant_memory_ids": cm(reason),
            "eligible_negative_history_ids": cm(reason),
            "registered_route_options": cm(reason),
            "registered_falsifier_options": cm(reason),
        },
        "retrieval": {
            "retrieved_count": measured_count(0),
            "selected_count": measured_count(0),
            "rejected_count": measured_count(0),
            "missed_known_relevant_count": cm(reason),
            "relevant_root_recall": cm(reason),
            "counterevidence_recall": cm(reason),
            "same_root_duplicate_count": measured_count(0),
            "stale_memory_selected_count": measured_count(0),
        },
        "action_change_attribution": {
            "pre_memory_pre_gate_action_preference": "example pre-memory preference",
            "post_memory_action_preference": "example post-memory preference",
            "post_governance_action": "example post-governance action",
            "memory_changed_action": cm(reason),
            "search_changed_action": cm(reason),
            "governance_changed_action": cm(reason),
            "attribution_note": "OBSERVATIONAL_NOT_CAUSAL",
        },
        "outcome": {
            "local_result_status": "UNKNOWN",
            "residual_before": "residual before cycle",
            "residual_after": "residual after cycle",
            "residual_contracted": cm(reason),
            "new_valid_obligation_closed_count": measured_count(0),
            "new_invalid_route_avoided_count": measured_count(0),
            "false_transfer": cm(reason),
            "authority_leak": False,
            "posthoc_chronology": False,
        },
        "reuse_funnel": {
            "raw_episode": measured_count(0),
            "candidate_lesson": measured_count(0),
            "verified_lesson": measured_count(0),
            "admitted_lesson": measured_count(0),
            "later_retrieved": measured_count(0),
            "changed_action": cm(reason),
            "successful_fresh_reuse": measured_count(0),
            "failed_reuse": measured_count(0),
            "out_of_scope_reuse": measured_count(0),
            "superseded_before_reuse": measured_count(0),
        },
        "cost": {
            "model_input_tokens": cm(reason),
            "model_output_tokens": cm(reason),
            "model_calls": cm(reason),
            "retrieval_calls": cm(reason),
            "tool_calls": cm(reason),
            "wall_time_seconds": cm(reason),
            "provider_cost": cm(reason),
        },
        "longitudinal_performance_vector": {
            "verified_progress": {
                "valid_residual_contraction": cm(reason),
                "registered_obligation_closure_count": measured_count(0),
                "local_scoped_result_rate": cm(reason),
            },
            "search_utility": {
                "relevant_root_recall": cm(reason),
                "counterevidence_recall": cm(reason),
                "missed_relevant_memory_count": cm(reason),
                "route_change_rate": cm(reason),
            },
            "reuse_utility": {
                "successful_fresh_reuse_count": measured_count(0),
                "false_or_out_of_scope_reuse_count": measured_count(0),
                "stale_reuse_count": measured_count(0),
            },
            "governance": {
                "prospective_chronology_capture": True,
                "authority_leakage_observed": False,
                "evidence_root_binding_verified": True,
                "negative_history_preserved": True,
            },
            "efficiency": {
                "progress_per_token": cm(reason),
                "progress_per_model_call": cm(reason),
                "progress_per_retrieval_call": cm(reason),
                "progress_per_wall_time": cm(reason),
            },
            "aggregate_scalar_score_forbidden": True,
        },
        "claim_boundary": (
            "process metrology only; no theorem, tool, gluing, review-independence "
            "or scientific authority"
        ),
        "grants_scientific_authority": False,
    }
