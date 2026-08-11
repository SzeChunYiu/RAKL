#!/usr/bin/env python3
"""Build durable cycle registry + honest Paper-V longitudinal analysis tables (#253).

Reads the frozen harvest universe (coverage observation only) and emits:

- a cycle registry with durability / completeness / schema-version classes
- seven-axis retained-growth *events* labelled ``INTERNAL_METROLOGY``
- experience-conversion / failure / routing / process / resource tables
- figure 2/3/4/7 *source data* that refuse pooled trajectories

Hard rules (breaking any of them invents a longitudinal win):

1. Never impute missing fields as zero.
2. Never pool retained-novelty across declared ``schema_version`` values.
3. Never treat retrieval as successful reuse.
4. Never treat repository/file/commit growth as semantic growth.
5. Never claim prospective credit for retrospective chronology.
6. Never mint scientific authority; novelty remains internal until #255.

Example::

    python experiments/paper5/analyze_longitudinal_universe.py \\
        --universe research/paper5_longitudinal_v1/longitudinal_event_universe.jsonl \\
        --out-dir research/paper5_longitudinal_v1
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ANALYZER_VERSION = "paper5-longitudinal-analysis-v1"
AXES = (
    "KNOWLEDGE",
    "OPERATOR",
    "EXPERIENCE_PATTERN",
    "OBSTRUCTION",
    "RELATION",
    "PATH",
    "META_METHOD",
)
PROCESS_SURFACE_KEYS = (
    "process_surfaces_invoked",
    "canonical_process_surfaces_invoked",
    "canonical_method_specs_surfaces_invoked",
    "canonical_process_surfaces",
    "canonical_method_specs_process_surfaces",
    "canonical_method_specs_process_surfaces_invoked",
)
CHANGED_ACTION_KEY_RE = re.compile(r"changed_action|action_attribution|changed_preference", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_universe(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{lineno}: expected object")
        rows.append(row)
    if not rows:
        raise SystemExit("universe is empty")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return sha256_file(path)


def write_json(path: Path, obj: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return sha256_bytes(text.encode("utf-8"))


def declared_schema_version(envelope: dict[str, Any]) -> str:
    if envelope.get("declared_schema_version_present"):
        return str(envelope.get("declared_schema_version"))
    return "<absent>"


def payload_of(envelope: dict[str, Any]) -> dict[str, Any] | None:
    payload = envelope.get("payload")
    return payload if isinstance(payload, dict) else None


def cycle_id_of(envelope: dict[str, Any]) -> str | None:
    payload = payload_of(envelope)
    if not payload:
        return None
    value = payload.get("cycle_id")
    return str(value) if value else None


def chronology_class(payload: dict[str, Any] | None) -> str:
    if not payload:
        return "CANNOT_ESTABLISH_CHRONOLOGY"
    for key in ("recorded_at_utc", "recorded_at", "timestamp", "frozen_at"):
        if payload.get(key):
            # Harvest envelopes are retrospective wrappers; cycle timestamps inside
            # payloads are observational labels, not a frozen pre-action receipt.
            return "RETROSPECTIVE_ONLY"
    return "CANNOT_ESTABLISH_CHRONOLOGY"


def completeness_class(envelope: dict[str, Any]) -> str:
    if envelope.get("parse_error"):
        return "CANNOT_MEASURE"
    payload = payload_of(envelope)
    if payload is None:
        return "CANNOT_MEASURE"
    has_cycle = bool(payload.get("cycle_id"))
    rsn = payload.get("retained_semantic_novelty")
    has_axes = isinstance(rsn, dict) and all(axis in rsn for axis in AXES)
    has_schema = bool(envelope.get("declared_schema_version_present"))
    has_resources = any(k in payload for k in ("resource_proxies", "resources"))
    has_memory = "memory" in payload or any(CHANGED_ACTION_KEY_RE.search(k) for k in payload)
    if has_cycle and has_axes and has_schema and (has_resources or has_memory):
        # Still not PROSPECTIVE_FULL: harvest is retrospective to this analysis.
        return "PROSPECTIVE_PARTIAL"
    if has_cycle and (has_axes or has_memory or has_resources):
        return "RETROSPECTIVE_RECONSTRUCTABLE"
    if has_cycle or has_axes:
        return "RETROSPECTIVE_INCOMPLETE"
    return "CANNOT_MEASURE"


def durability_class(envelope: dict[str, Any]) -> str:
    # All harvested envelopes are durable once stored in the framework universe.
    # Reachability from RAKL_math main is a separate source-of-truth property.
    if envelope.get("reachable_from_main_history"):
        return "DURABLE_MAIN_HISTORY_AND_FRAMEWORK_ARCHIVE"
    return "DURABLE_FRAMEWORK_ARCHIVE_ONLY_BRANCH_SOURCE"


def count_id_list(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, list):
        return len(value)
    if isinstance(value, (int, float)) and int(value) == value and value >= 0:
        return int(value)
    return None


def new_ids_counts(payload: dict[str, Any]) -> dict[str, int | None]:
    new_ids = payload.get("new_ids")
    if not isinstance(new_ids, dict):
        return {
            "episode_ids": None,
            "diagnosis_ids": None,
            "lesson_ids": None,
            "tool_ids": None,
            "motif_ids": None,
            "failure_ids": None,
            "obstruction_ids": None,
        }
    return {key: count_id_list(new_ids.get(key)) for key in (
        "episode_ids",
        "diagnosis_ids",
        "lesson_ids",
        "tool_ids",
        "motif_ids",
        "failure_ids",
        "obstruction_ids",
    )}


def extract_axis_value(rsn: dict[str, Any], axis: str) -> tuple[Any, str]:
    if axis not in rsn:
        return None, "ABSENT"
    value = rsn[axis]
    if isinstance(value, bool):
        return value, "NON_NUMERIC"
    if isinstance(value, (int, float)) and int(value) == value and value >= 0:
        return int(value), "INTERNAL_METROLOGY_COUNT"
    if isinstance(value, str) and value.startswith("CANNOT_"):
        return value, "CANNOT_MEASURE"
    if value is None:
        return None, "ABSENT"
    return value, "NON_NUMERIC"


def process_surfaces(payload: dict[str, Any]) -> tuple[str | None, list[str]]:
    for key in PROCESS_SURFACE_KEYS:
        value = payload.get(key)
        if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
            return key, list(value)
    return None, []


def changed_action_observation(payload: dict[str, Any]) -> dict[str, Any]:
    hits = {key: payload[key] for key in payload if CHANGED_ACTION_KEY_RE.search(key)}
    if not hits:
        return {
            "status": "CANNOT_MEASURE",
            "reason": "no memory-changed-action / attribution field present",
            "fields": {},
        }
    # Presence of a typed field is observational; do not coerce prose into a rate.
    return {
        "status": "FIELD_PRESENT_OBSERVATIONAL",
        "reason": "typed changed-action/attribution fields present; not normalized into a pooled rate",
        "fields": hits,
    }


def build_registry_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    return {
        "schema_version": "paper5-longitudinal-cycle-registry-v1",
        "analysis_id": analysis_id,
        "event_id": envelope.get("event_id") or envelope.get("git_blob_sha1"),
        "git_blob_sha1": envelope.get("git_blob_sha1"),
        "payload_sha256": envelope.get("payload_sha256"),
        "cycle_id": cycle_id_of(envelope),
        "source_repository": envelope.get("source_repository", "SzeChunYiu/RAKL_math"),
        "source_paths": envelope.get("source_paths") or [],
        "source_refs": envelope.get("source_refs") or [],
        "reachable_from_main_history": bool(envelope.get("reachable_from_main_history")),
        "durability_class": durability_class(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "completeness_class": completeness_class(envelope),
        "chronology_class": chronology_class(payload),
        "parse_error": envelope.get("parse_error"),
        "unmeasured_markers": envelope.get("unmeasured_markers") or {},
        "grants_scientific_authority": False,
    }


def build_retained_growth_events(envelope: dict[str, Any], analysis_id: str) -> list[dict[str, Any]]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return [{
            "schema_version": "paper5-longitudinal-retained-growth-event-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "cycle_id": None,
            "declared_schema_version": declared_schema_version(envelope),
            "axis": None,
            "value": None,
            "value_status": "CANNOT_MEASURE",
            "novelty_authority": "NONE",
            "lineage": {
                "git_blob_sha1": envelope.get("git_blob_sha1"),
                "payload_sha256": envelope.get("payload_sha256"),
                "source_paths": envelope.get("source_paths") or [],
            },
            "reason_classified_retained": "payload unparseable or absent",
            "grants_scientific_authority": False,
        }]

    rsn = payload.get("retained_semantic_novelty")
    if not isinstance(rsn, dict):
        return [{
            "schema_version": "paper5-longitudinal-retained-growth-event-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "cycle_id": cycle_id_of(envelope),
            "declared_schema_version": declared_schema_version(envelope),
            "axis": None,
            "value": None,
            "value_status": "CANNOT_MEASURE",
            "novelty_authority": "NONE",
            "lineage": {
                "git_blob_sha1": envelope.get("git_blob_sha1"),
                "payload_sha256": envelope.get("payload_sha256"),
                "source_paths": envelope.get("source_paths") or [],
                "retained_semantic_novelty_present": False,
            },
            "reason_classified_retained": "retained_semantic_novelty absent",
            "grants_scientific_authority": False,
        }]

    rows: list[dict[str, Any]] = []
    for axis in AXES:
        value, status = extract_axis_value(rsn, axis)
        rows.append({
            "schema_version": "paper5-longitudinal-retained-growth-event-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "cycle_id": cycle_id_of(envelope),
            "declared_schema_version": declared_schema_version(envelope),
            "axis": axis,
            "value": value,
            "value_status": status,
            "novelty_authority": "INTERNAL_METROLOGY",
            "lineage": {
                "git_blob_sha1": envelope.get("git_blob_sha1"),
                "payload_sha256": envelope.get("payload_sha256"),
                "source_paths": envelope.get("source_paths") or [],
                "retained_semantic_novelty_present": True,
            },
            "reason_classified_retained": (
                "source payload declared retained_semantic_novelty count; "
                "independent audit (#255) not executed"
            ),
            "supersession_contradiction_status": "NOT_AUDITED",
            "measurement_basis_ref": "research/paper5_longitudinal_v1/MEASUREMENT_BASIS.json",
            "grants_scientific_authority": False,
        })
    return rows


def build_experience_conversion_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return {
            "schema_version": "paper5-longitudinal-experience-conversion-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "cycle_id": None,
            "declared_schema_version": declared_schema_version(envelope),
            "status": "CANNOT_MEASURE",
            "stages": {},
            "negative_branches": {},
            "grants_scientific_authority": False,
        }

    ids = new_ids_counts(payload)
    reuse = count_id_list(payload.get("successful_reuse_ids"))
    if reuse is None:
        reuse = count_id_list(payload.get("successful_reuses"))
    changed = changed_action_observation(payload)
    stages = {
        "task_episode_ids_declared": ids["episode_ids"],
        "diagnosis_ids_declared": ids["diagnosis_ids"],
        "lesson_ids_declared": ids["lesson_ids"],
        "tool_ids_declared": ids["tool_ids"],
        "motif_ids_declared": ids["motif_ids"],
        "successful_reuse_ids_declared": reuse,
        "memory_changed_action": changed,
    }
    # Missing stages stay None / CANNOT_MEASURE — never coerced to 0.
    missing = [key for key, value in stages.items() if value is None]
    numeric_present = any(
        stages.get(key) is not None
        for key in (
            "task_episode_ids_declared",
            "diagnosis_ids_declared",
            "lesson_ids_declared",
            "tool_ids_declared",
            "motif_ids_declared",
            "successful_reuse_ids_declared",
        )
    )
    if numeric_present or changed["status"] != "CANNOT_MEASURE":
        status = (
            "PARTIAL_OBSERVATION_WITH_ABSENT_STAGES"
            if missing
            else "PARTIAL_OBSERVATION"
        )
    else:
        status = "CANNOT_MEASURE"
    return {
        "schema_version": "paper5-longitudinal-experience-conversion-v1",
        "analysis_id": analysis_id,
        "source_event_id": event_id,
        "cycle_id": cycle_id_of(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "status": status,
        "stages": stages,
        "absent_stages": missing,
        "negative_branches": {
            "failure_ids_declared": ids["failure_ids"],
            "obstruction_ids_declared": ids["obstruction_ids"],
            "note": "contradicted/rejected lesson branches are CANNOT_MEASURE unless explicitly present",
        },
        "retrieval_is_not_reuse": True,
        "grants_scientific_authority": False,
    }


def build_failure_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return {
            "schema_version": "paper5-longitudinal-failure-event-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "status": "CANNOT_MEASURE",
            "grants_scientific_authority": False,
        }
    ids = new_ids_counts(payload)
    signature = payload.get("failure_signature")
    return {
        "schema_version": "paper5-longitudinal-failure-event-v1",
        "analysis_id": analysis_id,
        "source_event_id": event_id,
        "cycle_id": cycle_id_of(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "failure_ids_declared": ids["failure_ids"],
        "failure_signature_present": signature is not None,
        "failure_signature": signature if signature is not None else None,
        "repeated_failure_rate": "CANNOT_MEASURE",
        "new_vs_repeated_split": "CANNOT_MEASURE",
        "time_to_supported_diagnosis": "CANNOT_MEASURE",
        "reason": "no frozen prospective failure-signature similarity rule bound to this harvest epoch",
        "status": "PARTIAL_OBSERVATION" if ids["failure_ids"] is not None or signature is not None else "CANNOT_MEASURE",
        "grants_scientific_authority": False,
    }


def build_routing_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return {
            "schema_version": "paper5-longitudinal-routing-event-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "status": "CANNOT_MEASURE",
            "grants_scientific_authority": False,
        }
    saturation = payload.get("saturation")
    route_shadow = payload.get("route_family_health_shadow")
    changed = changed_action_observation(payload)
    return {
        "schema_version": "paper5-longitudinal-routing-event-v1",
        "analysis_id": analysis_id,
        "source_event_id": event_id,
        "cycle_id": cycle_id_of(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "saturation_present": saturation is not None,
        "route_family_health_shadow_present": route_shadow is not None,
        "saturated_route_retry_rate": "CANNOT_MEASURE",
        "route_switch_latency": "CANNOT_MEASURE",
        "memory_changed_action": changed,
        "status": "PARTIAL_OBSERVATION" if saturation is not None or route_shadow is not None or changed["status"] != "CANNOT_MEASURE" else "CANNOT_MEASURE",
        "grants_scientific_authority": False,
    }


def build_process_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return {
            "schema_version": "paper5-longitudinal-process-inventory-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "status": "CANNOT_MEASURE",
            "grants_scientific_authority": False,
        }
    key, surfaces = process_surfaces(payload)
    return {
        "schema_version": "paper5-longitudinal-process-inventory-v1",
        "analysis_id": analysis_id,
        "source_event_id": event_id,
        "cycle_id": cycle_id_of(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "source_field": key,
        "process_surfaces": surfaces,
        "process_surface_count": len(surfaces) if surfaces else None,
        "status": "CYCLE_INVENTORY_NOT_PROCESS_TELEMETRY" if surfaces else "CANNOT_MEASURE",
        "note": (
            "Cycle-metric process-surface lists are inventory observations. "
            "They are not schemas/process-telemetry.schema.json invocation rows and "
            "must not feed Figure 7's process dashboard as if they were."
        ),
        "grants_scientific_authority": False,
    }


def build_resource_row(envelope: dict[str, Any], analysis_id: str) -> dict[str, Any]:
    payload = payload_of(envelope)
    event_id = envelope.get("event_id") or envelope.get("git_blob_sha1")
    if payload is None:
        return {
            "schema_version": "paper5-longitudinal-resource-metrics-v1",
            "analysis_id": analysis_id,
            "source_event_id": event_id,
            "status": "CANNOT_MEASURE",
            "grants_scientific_authority": False,
        }
    proxies = payload.get("resource_proxies") if isinstance(payload.get("resource_proxies"), dict) else None
    resources = payload.get("resources") if isinstance(payload.get("resources"), dict) else None
    return {
        "schema_version": "paper5-longitudinal-resource-metrics-v1",
        "analysis_id": analysis_id,
        "source_event_id": event_id,
        "cycle_id": cycle_id_of(envelope),
        "declared_schema_version": declared_schema_version(envelope),
        "resource_proxies": proxies,
        "resources": resources,
        "status": "PARTIAL_OBSERVATION" if proxies or resources else "CANNOT_MEASURE",
        "costs_comparable_across_cycles": False,
        "note": "resource policy identities retained per row; cross-cycle cost pooling refused",
        "grants_scientific_authority": False,
    }


def cohort_axis_summary(growth_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-schema-version INTERNAL_METROLOGY sums — never a pooled total."""
    by_version: dict[str, dict[str, Any]] = {}
    for event in growth_events:
        if event.get("axis") not in AXES:
            continue
        version = str(event.get("declared_schema_version"))
        bucket = by_version.setdefault(
            version,
            {
                "declared_schema_version": version,
                "event_count": 0,
                "numeric_axis_event_count": 0,
                "cannot_measure_axis_event_count": 0,
                "axis_sums": {axis: None for axis in AXES},
                "_axis_acc": {axis: 0 for axis in AXES},
                "_axis_numeric": {axis: 0 for axis in AXES},
            },
        )
        bucket["event_count"] += 1
        axis = event["axis"]
        if event.get("value_status") == "INTERNAL_METROLOGY_COUNT":
            bucket["numeric_axis_event_count"] += 1
            bucket["_axis_acc"][axis] += int(event["value"])
            bucket["_axis_numeric"][axis] += 1
        elif event.get("value_status") == "CANNOT_MEASURE":
            bucket["cannot_measure_axis_event_count"] += 1

    cohorts: list[dict[str, Any]] = []
    for version, bucket in sorted(by_version.items(), key=lambda item: (-item[1]["event_count"], item[0])):
        axis_sums: dict[str, Any] = {}
        for axis in AXES:
            if bucket["_axis_numeric"][axis]:
                axis_sums[axis] = bucket["_axis_acc"][axis]
            else:
                axis_sums[axis] = "CANNOT_MEASURE"
        cohorts.append({
            "declared_schema_version": version,
            "retained_growth_axis_row_count": bucket["event_count"],
            "numeric_axis_event_count": bucket["numeric_axis_event_count"],
            "cannot_measure_axis_event_count": bucket["cannot_measure_axis_event_count"],
            "axis_sums_internal_metrology_only": axis_sums,
            "novelty_authority": "INTERNAL_METROLOGY",
            "pooled_with_other_versions": False,
        })
    return {
        "pooled_trajectory_across_schema_versions": "CANNOT_MEASURE",
        "pooled_trajectory_reason": "MEASUREMENT_BASIS.cross_version_pooling_authorized is false",
        "cohorts": cohorts,
    }


def figure_source_payloads(
    registry: list[dict[str, Any]],
    growth_events: list[dict[str, Any]],
    conversion: list[dict[str, Any]],
    routing: list[dict[str, Any]],
    process_rows: list[dict[str, Any]],
    cohort_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    # Figure 2: refuse a single pooled growth curve; emit cohort panels + refusal.
    fig2_series: list[dict[str, Any]] = []
    by_version: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for event in growth_events:
        if event.get("value_status") == "INTERNAL_METROLOGY_COUNT" and event.get("axis") in AXES:
            by_version[str(event["declared_schema_version"])].append(event)
    for version, events in sorted(by_version.items(), key=lambda item: -len(item[1])):
        # One point per source cycle (sum of axes already separate).
        per_cycle: dict[str, dict[str, int]] = collections.OrderedDict()
        for event in events:
            cycle = event.get("cycle_id") or event.get("source_event_id")
            point = per_cycle.setdefault(str(cycle), {axis: 0 for axis in AXES})
            point[event["axis"]] = int(event["value"])
        if len(per_cycle) < 1:
            continue
        cumulative = {axis: 0 for axis in AXES}
        points = []
        for cycle_id, deltas in per_cycle.items():
            for axis in AXES:
                cumulative[axis] += deltas[axis]
            points.append({"cycle_id": cycle_id, "cumulative": dict(cumulative), "delta": deltas})
        fig2_series.append({
            "declared_schema_version": version,
            "n_cycles": len(points),
            "points": points,
            "label": "INTERNAL_METROLOGY",
        })

    fig2 = {
        "figure": "paper5_fig2_retained_growth",
        "status": "COHORT_INTERNAL_METROLOGY_ONLY",
        "pooled_trajectory": "CANNOT_MEASURE",
        "novelty_authority": "INTERNAL_METROLOGY",
        "independent_audit_issue": 255,
        "series_by_schema_version": fig2_series,
        "claim_boundary": (
            "Per-schema-version cumulative INTERNAL_METROLOGY only. "
            "No cross-version pooled growth curve is authorized."
        ),
    }

    # Figure 3: funnel only where stage fields exist; absent stages stay CANNOT_MEASURE.
    stage_keys = [
        "task_episode_ids_declared",
        "diagnosis_ids_declared",
        "lesson_ids_declared",
        "tool_ids_declared",
        "motif_ids_declared",
        "successful_reuse_ids_declared",
    ]
    present_counts = {key: 0 for key in stage_keys}
    summed = {key: 0 for key in stage_keys}
    observed_rows = 0
    for row in conversion:
        stages = row.get("stages") or {}
        if not any(stages.get(key) is not None for key in stage_keys):
            continue
        observed_rows += 1
        for key in stage_keys:
            value = stages.get(key)
            if value is None:
                continue
            present_counts[key] += 1
            summed[key] += int(value)
    fig3_stages = {}
    for key in stage_keys:
        if present_counts[key] == 0:
            fig3_stages[key] = "CANNOT_MEASURE"
        else:
            fig3_stages[key] = {
                "rows_with_field": present_counts[key],
                "sum_of_declared_ids": summed[key],
                "note": "sum of declared id-list lengths where present; not a validated conversion rate",
            }
    fig3 = {
        "figure": "paper5_fig3_experience_conversion",
        "status": "PARTIAL_OBSERVATION" if observed_rows else "CANNOT_MEASURE",
        "rows_with_any_stage_field": observed_rows,
        "stages": fig3_stages,
        "retrieval_is_not_reuse": True,
        "pooled_conversion_rate_across_schema_versions": "CANNOT_MEASURE",
        "claim_boundary": (
            "Declared id-list lengths only. Missing stages remain CANNOT_MEASURE; "
            "no fabricated funnel completeness."
        ),
    }

    # Figure 4: dynamics mostly CANNOT_MEASURE; report observational changed-action presence.
    changed_present = sum(
        1 for row in routing
        if isinstance(row.get("memory_changed_action"), dict)
        and row["memory_changed_action"].get("status") == "FIELD_PRESENT_OBSERVATIONAL"
    )
    fig4 = {
        "figure": "paper5_fig4_routing_failure_dynamics",
        "status": "MOSTLY_CANNOT_MEASURE",
        "repeated_failure_rate_series": "CANNOT_MEASURE",
        "saturated_route_retry_rate_series": "CANNOT_MEASURE",
        "route_switch_latency_series": "CANNOT_MEASURE",
        "memory_changed_action_rate_series": "CANNOT_MEASURE",
        "memory_changed_action_field_present_rows": changed_present,
        "memory_changed_action_field_present_denominator": len(routing),
        "claim_boundary": (
            "No frozen prospective failure-signature / route-switch latency series is available "
            "in this harvest epoch. Field presence is observational only."
        ),
    }

    # Figure 7: refuse process-dashboard coercion; emit inventory presence only.
    surface_counter: collections.Counter[str] = collections.Counter()
    inventory_rows = 0
    for row in process_rows:
        if row.get("status") != "CYCLE_INVENTORY_NOT_PROCESS_TELEMETRY":
            continue
        inventory_rows += 1
        for surface in row.get("process_surfaces") or []:
            surface_counter[surface] += 1
    fig7 = {
        "figure": "paper5_fig7_process_dashboard",
        "status": "CANNOT_MEASURE_AS_PROCESS_TELEMETRY_DASHBOARD",
        "reason": (
            "Cycle-metric artifacts list process surfaces but do not satisfy "
            "schemas/process-telemetry.schema.json invocation records required by "
            "analyze_process_telemetry.py / plot_process_dashboard.py."
        ),
        "cycle_inventory_rows_with_surfaces": inventory_rows,
        "surface_mention_counts_observational": dict(surface_counter.most_common()),
        "process_telemetry_dashboard_csv": "CANNOT_MEASURE",
        "claim_boundary": (
            "Observational surface-mention inventory only. Not a Figure-7 process dashboard."
        ),
    }

    return {
        "fig2": fig2,
        "fig3": fig3,
        "fig4": fig4,
        "fig7": fig7,
        "registry_summary": {
            "n_events": len(registry),
            "reachable_from_main_history": sum(1 for row in registry if row["reachable_from_main_history"]),
            "durable_framework_archive_only": sum(
                1 for row in registry if row["durability_class"] == "DURABLE_FRAMEWORK_ARCHIVE_ONLY_BRANCH_SOURCE"
            ),
            "completeness_classes": dict(collections.Counter(row["completeness_class"] for row in registry)),
            "chronology_classes": dict(collections.Counter(row["chronology_class"] for row in registry)),
            "declared_schema_versions": dict(
                collections.Counter(row["declared_schema_version"] for row in registry).most_common()
            ),
        },
        "cohort_summary": cohort_summary,
    }


def try_plot_figures(figure_sources: dict[str, Any], out_dir: Path) -> list[str]:
    """Best-effort matplotlib renders; source JSON remains canonical if plotting fails."""
    emitted: list[str] = []
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        emitted.append(f"SKIP plots: matplotlib unavailable ({exc})")
        return emitted

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig2 = figure_sources["fig2"]
    series = fig2.get("series_by_schema_version") or []
    # Prefer largest cohorts for a readable multi-panel INTERNAL_METROLOGY figure.
    series = [item for item in series if item.get("n_cycles", 0) >= 2][:4]
    if series:
        fig, axes = plt.subplots(len(series), 1, figsize=(11, 3.2 * len(series)), sharex=False)
        if len(series) == 1:
            axes = [axes]
        for ax, item in zip(axes, series):
            points = item["points"]
            x = list(range(len(points)))
            for axis in AXES:
                ax.plot(
                    x,
                    [point["cumulative"][axis] for point in points],
                    marker="o",
                    markersize=3,
                    linewidth=1.1,
                    label=axis,
                )
            ax.set_xticks(x, [point["cycle_id"] for point in points], rotation=50, ha="right", fontsize=6)
            ax.set_ylabel("Cumulative (internal)")
            ax.set_title(f"{item['declared_schema_version']} — INTERNAL_METROLOGY (n={item['n_cycles']})")
            ax.legend(frameon=False, fontsize=6, ncol=4)
        fig.suptitle("Fig 2 — cohort retained growth (pooled trajectory CANNOT_MEASURE)")
        fig.tight_layout()
        path = fig_dir / "paper5_fig2_retained_growth_cohorts.pdf"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        emitted.append(str(path))
    else:
        emitted.append("SKIP fig2 pdf: no schema cohort with >=2 numeric cycles")

    # Figs 3/4/7: status panels that preserve CANNOT_MEASURE rather than empty charts.
    for key, title in (
        ("fig3", "Fig 3 — experience conversion"),
        ("fig4", "Fig 4 — routing / failure dynamics"),
        ("fig7", "Fig 7 — process dashboard"),
    ):
        payload = figure_sources[key]
        fig, ax = plt.subplots(figsize=(10.5, 4.8))
        ax.axis("off")
        lines = [
            title,
            f"status: {payload.get('status')}",
            "",
            "Honest residuals (not imputed):",
        ]
        for field, value in payload.items():
            if field in {"figure", "claim_boundary", "surface_mention_counts_observational", "stages"}:
                continue
            lines.append(f"- {field}: {value}")
        if key == "fig3":
            lines.append("")
            lines.append("stages:")
            for stage, value in (payload.get("stages") or {}).items():
                lines.append(f"  - {stage}: {value}")
        if key == "fig7":
            mentions = payload.get("surface_mention_counts_observational") or {}
            lines.append("")
            lines.append(f"observational surface mentions (top 12 of {len(mentions)}):")
            for surface, count in list(mentions.items())[:12]:
                lines.append(f"  - {surface}: {count}")
        lines.append("")
        lines.append(str(payload.get("claim_boundary", "")))
        ax.text(0.01, 0.99, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=8)
        path = fig_dir / f"paper5_{key}_status.pdf"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        emitted.append(str(path))

    return emitted


def materialize_durable_blob_index(universe: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    """Index envelopes into a durable blob map without rewriting payload bytes.

    Original git blob bytes are not reconstructed here (universe carries parsed
    JSON). Durability is the framework-hosted universe + this index binding
    ``git_blob_sha1`` / ``payload_sha256``.
    """
    rows = []
    for envelope in universe:
        rows.append({
            "git_blob_sha1": envelope.get("git_blob_sha1"),
            "payload_sha256": envelope.get("payload_sha256"),
            "payload_bytes": envelope.get("payload_bytes"),
            "reachable_from_main_history": bool(envelope.get("reachable_from_main_history")),
            "durability_class": durability_class(envelope),
            "source_paths": envelope.get("source_paths") or [],
            "source_refs": envelope.get("source_refs") or [],
            "cycle_id": cycle_id_of(envelope),
            "declared_schema_version": declared_schema_version(envelope),
        })
    path = out_dir / "DURABLE_BLOB_INDEX.jsonl"
    digest = write_jsonl(path, rows)
    try:
        repo_root = Path(__file__).resolve().parents[2]
        rel = str(path.relative_to(repo_root))
    except Exception:
        rel = str(path)
    return {
        "path": rel,
        "sha256": digest,
        "n": len(rows),
        "at_risk_branch_source_archived_here": sum(1 for row in rows if not row["reachable_from_main_history"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--analysis-id", default=None)
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args()

    universe_path = args.universe.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    analyzed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    analysis_id = args.analysis_id or f"paper5-longitudinal-analysis-{analyzed_at[:10].replace('-', '')}"

    universe = load_universe(universe_path)
    universe_sha = sha256_file(universe_path)

    registry = [build_registry_row(env, analysis_id) for env in universe]
    growth_events: list[dict[str, Any]] = []
    for env in universe:
        growth_events.extend(build_retained_growth_events(env, analysis_id))
    conversion = [build_experience_conversion_row(env, analysis_id) for env in universe]
    failure_rows = [build_failure_row(env, analysis_id) for env in universe]
    routing_rows = [build_routing_row(env, analysis_id) for env in universe]
    process_rows = [build_process_row(env, analysis_id) for env in universe]
    resource_rows = [build_resource_row(env, analysis_id) for env in universe]
    cohort_summary = cohort_axis_summary(growth_events)
    figure_sources = figure_source_payloads(
        registry, growth_events, conversion, routing_rows, process_rows, cohort_summary
    )

    artifacts = {
        "CYCLE_REGISTRY.jsonl": write_jsonl(out_dir / "CYCLE_REGISTRY.jsonl", registry),
        "retained_growth_events.jsonl": write_jsonl(out_dir / "retained_growth_events.jsonl", growth_events),
        "experience_conversion_events.jsonl": write_jsonl(
            out_dir / "experience_conversion_events.jsonl", conversion
        ),
        "failure_events.jsonl": write_jsonl(out_dir / "failure_events.jsonl", failure_rows),
        "routing_events.jsonl": write_jsonl(out_dir / "routing_events.jsonl", routing_rows),
        "process_telemetry_inventory.jsonl": write_jsonl(
            out_dir / "process_telemetry_inventory.jsonl", process_rows
        ),
        "resource_metrics.jsonl": write_jsonl(out_dir / "resource_metrics.jsonl", resource_rows),
        "seven_axis_cohort_summary.json": write_json(
            out_dir / "seven_axis_cohort_summary.json",
            {
                "schema_version": "paper5-longitudinal-seven-axis-cohort-summary-v1",
                "analysis_id": analysis_id,
                "novelty_authority": "INTERNAL_METROLOGY",
                "grants_scientific_authority": False,
                **cohort_summary,
            },
        ),
        "figure_sources.json": write_json(out_dir / "figure_sources.json", {
            "schema_version": "paper5-longitudinal-figure-sources-v1",
            "analysis_id": analysis_id,
            "grants_scientific_authority": False,
            **figure_sources,
        }),
    }

    durable = materialize_durable_blob_index(universe, out_dir)
    artifacts["DURABLE_BLOB_INDEX.jsonl"] = durable["sha256"]

    plot_notes = [] if args.skip_plots else try_plot_figures(figure_sources, out_dir)
    # Prefer repo-relative plot paths in the receipt.
    try:
        repo_root = Path(__file__).resolve().parents[2]
        plot_notes = [
            str(Path(note).relative_to(repo_root)) if note.startswith("/") else note
            for note in plot_notes
        ]
    except Exception:
        pass

    residual_axes = [
        "POOLED seven-axis longitudinal trajectory across schema versions: CANNOT_MEASURE (pooling refused)",
        "Independent retained-novelty audit / semantic authority: blocked on #255 (human annotators)",
        "Prospective repeated-failure rate / saturated-route retry / route-switch latency series: CANNOT_MEASURE",
        "Validated experience-conversion rates with complete denominators under one basis: CANNOT_MEASURE",
        "Figure 7 process-telemetry dashboard (schemas/process-telemetry.schema.json): CANNOT_MEASURE",
        "Causal task-performance claims: reserved for #250/#251 (not unblocked here)",
    ]

    receipt = {
        "schema_version": "paper5-longitudinal-analysis-receipt-v1",
        "analysis_id": analysis_id,
        "analyzer_version": ANALYZER_VERSION,
        "analyzed_at_utc": analyzed_at,
        "issue": 253,
        "universe_path": str(universe_path),
        "universe_sha256": universe_sha,
        "event_count": len(universe),
        "artifacts": {name: {"sha256": digest} for name, digest in artifacts.items()},
        "durable_blob_index": durable,
        "figure_plot_notes": plot_notes,
        "pooling_authorized": False,
        "grants_scientific_authority": False,
        "novelty_authority": "INTERNAL_METROLOGY",
        "claim_boundary": (
            "Durable registry + honest missingness tables + cohort-only INTERNAL_METROLOGY figure "
            "sources. Does not authorize pooled longitudinal growth claims, independent novelty "
            "authority, confirmatory four-arm results, or manuscript result ingest."
        ),
        "residual_axes_keeping_issue_open": residual_axes,
        "acceptance_progress": {
            "real_cycle_registry": True,
            "measurement_basis_frozen": True,
            "seven_axis_retained_events_with_lineage": True,
            "experience_conversion_table_with_cannot_measure": True,
            "repeated_failure_metrics_where_possible": "CANNOT_MEASURE_SERIES",
            "memory_changed_action_prospective_rates": "FIELD_PRESENCE_ONLY",
            "routing_dynamics_measured": "PARTIAL_SATURATION_PRESENCE_ONLY",
            "process_telemetry_dataset": "INVENTORY_ONLY_NOT_PROCESS_TELEMETRY_SCHEMA",
            "missing_historical_as_cannot_measure": True,
            "resources_retained_per_row": True,
            "fig_2_3_4_7_source_data": True,
            "dataset_manifest_binds_source_states": True,
            "pooled_growth_claim": False,
            "independent_novelty_audit": False,
        },
        "status": "ANALYSIS_ADVANCED_RESIDUAL_OPEN",
    }

    # Prefer repo-relative universe path in receipt when possible.
    try:
        repo_root = Path(__file__).resolve().parents[2]
        receipt["universe_path"] = str(universe_path.relative_to(repo_root))
    except Exception:
        receipt["universe_path"] = str(universe_path)

    artifacts["ANALYSIS_RECEIPT.json"] = write_json(out_dir / "ANALYSIS_RECEIPT.json", receipt)

    manifest = {
        "schema_version": "paper5-longitudinal-dataset-manifest-v1",
        "analysis_id": analysis_id,
        "issue": 253,
        "source_repository": "SzeChunYiu/RAKL_math",
        "framework_repository": "SzeChunYiu/RAKL",
        "universe_path": receipt["universe_path"],
        "universe_sha256": universe_sha,
        "measurement_basis_path": "research/paper5_longitudinal_v1/MEASUREMENT_BASIS.json",
        "coverage_observation_path": "research/paper5_longitudinal_v1/COVERAGE_OBSERVATION_20260811.json",
        "artifacts": [
            "CYCLE_REGISTRY.jsonl",
            "DURABLE_BLOB_INDEX.jsonl",
            "retained_growth_events.jsonl",
            "experience_conversion_events.jsonl",
            "failure_events.jsonl",
            "routing_events.jsonl",
            "process_telemetry_inventory.jsonl",
            "resource_metrics.jsonl",
            "seven_axis_cohort_summary.json",
            "figure_sources.json",
            "ANALYSIS_RECEIPT.json",
        ],
        "artifact_sha256": {name: digest for name, digest in artifacts.items()},
        "cross_version_pooling_authorized": False,
        "grants_scientific_authority": False,
        "status": "DATASET_MANIFEST_FROZEN_POOLING_REFUSED",
    }
    write_json(out_dir / "DATASET_MANIFEST.json", manifest)

    print(out_dir / "ANALYSIS_RECEIPT.json")
    print(f"  events                 {len(universe)}")
    print(f"  registry rows          {len(registry)}")
    print(f"  retained-growth rows   {len(growth_events)}")
    print(f"  durable branch-source  {durable['at_risk_branch_source_archived_here']}")
    print(f"  pooled trajectory      CANNOT_MEASURE")
    print(f"  status                 {receipt['status']}")
    for note in plot_notes:
        print(f"  plot                   {note}")


if __name__ == "__main__":
    main()
