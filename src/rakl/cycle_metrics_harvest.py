"""Prospective harvest instrumentation for ``rakl-cycle-metrics-v1`` (#446).

Harvest envelopes carry heterogeneous historical payloads verbatim.  This module
extracts denominator / reuse / cost metrology slices for stable v1 records,
emits fail-closed ``RAKL_CYCLE_METRICS`` documents when denominators are
unknown, and never coerces legacy blobs into the v1 schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from rakl.rakl_cycle_metrics import (
    SCHEMA_VERSION,
    audit_cycle_metrics,
    cannot_measure,
    is_cannot_measure,
    minimal_cycle_metrics_template,
)

INSTRUMENTATION_SCHEMA = "paper5-cycle-metrics-instrumentation-v1"
_METROLOGY_SECTIONS = ("opportunity_denominators", "reuse_funnel", "cost")


def payload_schema_class(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return "unparseable"
    version = payload.get("schema_version")
    if version == SCHEMA_VERSION:
        return SCHEMA_VERSION
    if version:
        return "legacy_declared"
    return "legacy_undeclared"


def _cycle_id_from_payload(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return "UNKNOWN-CYCLE"
    value = payload.get("cycle_id")
    if value:
        return str(value)
    atom = payload.get("atom_id")
    if atom:
        return str(atom)
    active_atom = payload.get("active_atom")
    if isinstance(active_atom, Mapping) and active_atom.get("atom_id"):
        return str(active_atom["atom_id"])
    return "UNKNOWN-CYCLE"


def _required_section_fields(section: str) -> tuple[str, ...]:
    if section == "opportunity_denominators":
        return (
            "eligible_memory_universe_count",
            "eligible_relevant_memory_ids",
            "eligible_negative_history_ids",
            "registered_route_options",
            "registered_falsifier_options",
        )
    if section == "reuse_funnel":
        return (
            "raw_episode",
            "candidate_lesson",
            "verified_lesson",
            "admitted_lesson",
            "later_retrieved",
            "changed_action",
            "successful_fresh_reuse",
            "failed_reuse",
            "out_of_scope_reuse",
            "superseded_before_reuse",
        )
    if section == "cost":
        return (
            "model_input_tokens",
            "model_output_tokens",
            "model_calls",
            "retrieval_calls",
            "tool_calls",
            "wall_time_seconds",
            "provider_cost",
        )
    raise KeyError(section)


def _section_or_cannot_measure(
    payload: Mapping[str, Any],
    section: str,
    *,
    reason: str,
) -> dict[str, Any]:
    value = payload.get(section)
    if isinstance(value, Mapping):
        return dict(value)
    return {field: cannot_measure(reason) for field in _required_section_fields(section)}


def slice_metrology_fields(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return denominator / reuse / cost slices with fail-closed ``CANNOT_MEASURE``."""
    if not isinstance(payload, Mapping):
        reason = "harvest payload is not a JSON object"
        return {
            section: {field: cannot_measure(reason) for field in _required_section_fields(section)}
            for section in _METROLOGY_SECTIONS
        }

    schema_class = payload_schema_class(payload)
    if schema_class != SCHEMA_VERSION:
        reason = (
            f"payload schema_version is {payload.get('schema_version')!r}; "
            "only rakl-cycle-metrics-v1 exposes frozen metrology sections"
        )
        return {
            section: {field: cannot_measure(reason) for field in _required_section_fields(section)}
            for section in _METROLOGY_SECTIONS
        }

    reason = "section absent from otherwise v1 payload"
    return {
        section: _section_or_cannot_measure(payload, section, reason=reason)
        for section in _METROLOGY_SECTIONS
    }


def emit_cycle_metrics_record(
    payload: Mapping[str, Any] | None,
    *,
    cycle_id: str | None = None,
    unknown_reason: str = "eligible memory universe not frozen before retrieval",
) -> dict[str, Any]:
    """Emit a ``rakl-cycle-metrics-v1`` record or a fail-closed template."""
    if isinstance(payload, Mapping) and payload_schema_class(payload) == SCHEMA_VERSION:
        return dict(payload)

    resolved_cycle_id = cycle_id or _cycle_id_from_payload(
        payload if isinstance(payload, Mapping) else None
    )
    return minimal_cycle_metrics_template(cycle_id=resolved_cycle_id, reason=unknown_reason)


def metrology_denominators_known(metrology_slice: Mapping[str, Any]) -> bool:
    denominators = metrology_slice.get("opportunity_denominators", {})
    universe = denominators.get("eligible_memory_universe_count")
    return not is_cannot_measure(universe)


def build_instrumentation_row(
    envelope: Mapping[str, Any],
    *,
    instrumented_at: str | None = None,
) -> dict[str, Any]:
    """Build one prospective instrumentation row for a harvest envelope."""
    payload = envelope.get("payload")
    payload_dict = payload if isinstance(payload, Mapping) else None
    schema_class = payload_schema_class(payload_dict)
    metrology = slice_metrology_fields(payload_dict)
    emitted = emit_cycle_metrics_record(payload_dict)
    if schema_class == SCHEMA_VERSION:
        audit_errors = audit_cycle_metrics(emitted)
        audit_passed = not audit_errors
    else:
        audit_errors = ()
        audit_passed = False

    return {
        "schema_version": INSTRUMENTATION_SCHEMA,
        "source_event_id": envelope.get("event_id") or envelope.get("git_blob_sha1"),
        "declared_schema_version": envelope.get("declared_schema_version"),
        "payload_schema_class": schema_class,
        "instrumented_at_utc": instrumented_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrology_slice": metrology,
        "denominators_known": metrology_denominators_known(metrology),
        "emitted_cycle_metrics": emitted,
        "emitted_schema_version": emitted.get("schema_version"),
        "audit_errors": list(audit_errors),
        "audit_passed": audit_passed,
        "claim_boundary": (
            "prospective harvest instrumentation only; legacy payloads are not coerced "
            "to rakl-cycle-metrics-v1; missing denominators remain CANNOT_MEASURE"
        ),
        "grants_scientific_authority": False,
    }


def instrumentation_coverage(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize prospective instrumentation across harvested envelopes."""
    by_class: dict[str, int] = {}
    denominators_known = 0
    audit_passed = 0
    for row in rows:
        schema_class = str(row.get("payload_schema_class", "unknown"))
        by_class[schema_class] = by_class.get(schema_class, 0) + 1
        if row.get("denominators_known"):
            denominators_known += 1
        if row.get("audit_passed"):
            audit_passed += 1

    return {
        "schema_version": "paper5-cycle-metrics-instrumentation-coverage-v1",
        "row_count": len(rows),
        "payload_schema_classes": by_class,
        "rows_with_known_denominators": denominators_known,
        "rows_passing_audit": audit_passed,
        "legacy_coercion_performed": False,
        "comparable_across_declared_versions": False,
        "claim_boundary": (
            "Instrumentation coverage only. Legacy heterogeneous payloads are carried "
            "verbatim in the harvest universe and receive fail-closed emitted records."
        ),
        "grants_scientific_authority": False,
    }
