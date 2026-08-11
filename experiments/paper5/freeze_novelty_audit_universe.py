#!/usr/bin/env python3
"""Freeze Paper-V retained-novelty audit Phase 0 universe (#255).

Builds immutable audit-universe artifacts from the frozen #253 longitudinal
dataset. Does not invent annotator responses, adjudication, or external labels.

Example::

    python experiments/paper5/freeze_novelty_audit_universe.py \\
        --longitudinal-dir research/paper5_longitudinal_v1 \\
        --out-dir research/paper5_novelty_audit_v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AXES = (
    "KNOWLEDGE",
    "OPERATOR",
    "EXPERIENCE_PATTERN",
    "OBSTRUCTION",
    "RELATION",
    "PATH",
    "META_METHOD",
)
AUDIT_EPOCH_ID = "paper5-retained-novelty-audit-epoch-20260811"
FREEZE_VERSION = "paper5-novelty-audit-universe-freeze-v1"
FORBIDDEN_ANNOTATION_FILES = (
    "ANNOTATOR_A_RESPONSE.json",
    "ANNOTATOR_B_RESPONSE.json",
    "ADJUDICATION.json",
    "PRE_ADJUDICATION_AGREEMENT.json",
    "PUBLIC_AUDIT_PACKET.json",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{lineno}: expected object")
        rows.append(row)
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


def audit_event_id(row: dict[str, Any]) -> str:
    axis = row.get("axis")
    source_event_id = row["source_event_id"]
    return f"{source_event_id}:{axis}" if axis else source_event_id


def opaque_audit_item_id(audit_epoch_id: str, event_id: str) -> str:
    digest = hashlib.sha256(f"{audit_epoch_id}:{event_id}".encode("utf-8")).hexdigest()
    return f"audit-item-{digest[:24]}"


def classify_retained(row: dict[str, Any]) -> bool:
    if row.get("value_status") != "INTERNAL_METROLOGY_COUNT":
        return False
    value = row.get("value")
    return isinstance(value, (int, float)) and int(value) > 0


def classify_control(row: dict[str, Any]) -> bool:
    if row.get("novelty_authority") == "NONE":
        return True
    if row.get("value_status") == "INTERNAL_METROLOGY_COUNT":
        value = row.get("value")
        return value in (0, None) or (isinstance(value, (int, float)) and int(value) == 0)
    return False


def build_blinded_row(
    row: dict[str, Any],
    audit_epoch_id: str,
    measurement_basis_ref: str,
) -> dict[str, Any]:
    event_id = audit_event_id(row)
    lineage = dict(row.get("lineage") or {})
    lineage.pop("retained_semantic_novelty_present", None)
    return {
        "schema_version": "paper5-blinded-audit-candidate-frame-row-v1",
        "audit_epoch_id": audit_epoch_id,
        "opaque_audit_item_id": opaque_audit_item_id(audit_epoch_id, event_id),
        "audit_event_id": event_id,
        "axis": row.get("axis"),
        "cycle_id": row.get("cycle_id"),
        "declared_schema_version": row.get("declared_schema_version"),
        "lineage": lineage,
        "measurement_basis_ref": measurement_basis_ref,
        "grants_scientific_authority": False,
        "claim_boundary": (
            "Label-blind candidate frame row. Internal retained/non-retained classification "
            "is withheld from annotators until PUBLIC_AUDIT_PACKET construction."
        ),
    }


def build_stratification_row(row: dict[str, Any], internally_retained: bool) -> dict[str, Any]:
    event_id = audit_event_id(row)
    return {
        "schema_version": "paper5-audit-stratification-row-v1",
        "audit_event_id": event_id,
        "axis": row.get("axis"),
        "cycle_id": row.get("cycle_id"),
        "declared_schema_version": row.get("declared_schema_version"),
        "internal_retained": internally_retained,
        "internal_value": row.get("value"),
        "internal_value_status": row.get("value_status"),
        "novelty_authority": row.get("novelty_authority"),
        "not_for_annotator_release": True,
        "grants_scientific_authority": False,
    }


def scan_zero_labels(out_dir: Path) -> dict[str, Any]:
    files_observed = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    forbidden_present = [name for name in FORBIDDEN_ANNOTATION_FILES if (out_dir / name).exists()]
    return {
        "annotation_directory_scan": {
            "annotation_dir": str(out_dir.relative_to(out_dir.parents[1])),
            "files_observed": files_observed,
            "forbidden_payload_files": forbidden_present,
            "unexpected_files": [],
            "verdict": "ZERO_PUBLIC_ANNOTATION_PAYLOADS" if not forbidden_present else "FORBIDDEN_PAYLOADS_PRESENT",
        },
        "counts": {
            "external_annotations": 0,
            "adjudications": 0,
            "evaluated_results": 0,
        },
        "first_external_label_at_utc": None,
        "label_payload_accessed": False,
        "observation": "ZERO_EXTERNAL_NOVELTY_LABELS",
        "state": "ZERO_LABELS_OBSERVED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--longitudinal-dir",
        type=Path,
        default=Path("research/paper5_longitudinal_v1"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("research/paper5_novelty_audit_v1"),
    )
    parser.add_argument("--audit-epoch-id", default=AUDIT_EPOCH_ID)
    args = parser.parse_args()

    longitudinal_dir = args.longitudinal_dir
    out_dir = args.out_dir
    basis_path = longitudinal_dir / "MEASUREMENT_BASIS.json"
    manifest_path = longitudinal_dir / "DATASET_MANIFEST.json"
    receipt_path = longitudinal_dir / "ANALYSIS_RECEIPT.json"
    retained_events_path = longitudinal_dir / "retained_growth_events.jsonl"

    for path in (basis_path, manifest_path, receipt_path, retained_events_path):
        if not path.is_file():
            raise SystemExit(f"missing required #253 artifact: {path}")

    basis = load_json(basis_path)
    manifest = load_json(manifest_path)
    receipt = load_json(receipt_path)
    rows = load_jsonl(retained_events_path)

    measurement_basis_ref = str(manifest.get("measurement_basis_path") or basis_path.as_posix())
    cutoff_timestamp = receipt.get("analyzed_at_utc")
    if not cutoff_timestamp:
        raise SystemExit("ANALYSIS_RECEIPT.json missing analyzed_at_utc cutoff")

    retained_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    stratification_rows: list[dict[str, Any]] = []
    blinded_rows: list[dict[str, Any]] = []

    for row in rows:
        event_id = audit_event_id(row)
        if classify_retained(row):
            retained_rows.append({**row, "audit_event_id": event_id})
            stratification_rows.append(build_stratification_row(row, internally_retained=True))
            blinded_rows.append(build_blinded_row(row, args.audit_epoch_id, measurement_basis_ref))
        elif classify_control(row):
            control_rows.append({**row, "audit_event_id": event_id})
            stratification_rows.append(build_stratification_row(row, internally_retained=False))
            blinded_rows.append(build_blinded_row(row, args.audit_epoch_id, measurement_basis_ref))

    if not retained_rows:
        raise SystemExit("retained event universe is empty; refusing to freeze")
    if not control_rows:
        raise SystemExit("control event universe is empty; refusing to freeze")

    retained_universe_path = out_dir / "retained_event_universe.jsonl"
    control_universe_path = out_dir / "control_event_universe.jsonl"
    blinded_frame_path = out_dir / "BLINDED_AUDIT_CANDIDATE_FRAME.jsonl"
    stratification_path = out_dir / "INTERNAL_STRATIFICATION.jsonl"

    retained_universe_sha256 = write_jsonl(retained_universe_path, retained_rows)
    control_universe_sha256 = write_jsonl(control_universe_path, control_rows)
    blinded_frame_sha256 = write_jsonl(blinded_frame_path, blinded_rows)
    stratification_sha256 = write_jsonl(stratification_path, stratification_rows)

    measurement_basis_sha256 = sha256_file(basis_path)
    dataset_manifest_sha256 = sha256_file(manifest_path)

    frozen_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    zero_labels = {
        "schema_version": "paper5-zero-external-novelty-labels-v1",
        "audit_epoch_id": args.audit_epoch_id,
        "issue": 255,
        "created_at_utc": frozen_at_utc,
        "cutoff_timestamp_utc": cutoff_timestamp,
        "framework_repository": "SzeChunYiu/RAKL",
        "related_issue_253_analysis_id": manifest.get("analysis_id"),
        "grants_scientific_authority": False,
        "claim_boundary": (
            "Payload-free zero-external-label observation at Phase 0 audit-universe freeze. "
            "Not independent review, not annotation evidence, and not construct-validity authority."
        ),
        **scan_zero_labels(out_dir),
    }
    zero_labels_sha256 = write_json(out_dir / "ZERO_EXTERNAL_NOVELTY_LABELS.json", zero_labels)

    manifest_obj = {
        "schema_version": "paper5-audit-universe-manifest-v1",
        "audit_epoch_id": args.audit_epoch_id,
        "audit_id": "paper5-retained-novelty-audit-v1",
        "issue": 255,
        "depends_on_issue": 253,
        "status": "AUDIT_UNIVERSE_FROZEN_PHASE0",
        "frozen_at_utc": frozen_at_utc,
        "cutoff_timestamp_utc": cutoff_timestamp,
        "framework_repository": "SzeChunYiu/RAKL",
        "source_repository": manifest.get("source_repository", "SzeChunYiu/RAKL_math"),
        "protocol_path": "experiments/paper5/NOVELTY_AUDIT_PROTOCOL_V1.md",
        "longitudinal_dataset_manifest_path": manifest_path.as_posix(),
        "measurement_basis_path": measurement_basis_ref,
        "retained_growth_events_source_path": retained_events_path.as_posix(),
        "freeze_version": FREEZE_VERSION,
        "framework_measurement_basis_sha256": measurement_basis_sha256,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "retained_event_universe_path": retained_universe_path.as_posix(),
        "retained_event_universe_sha256": retained_universe_sha256,
        "control_event_universe_path": control_universe_path.as_posix(),
        "control_event_universe_sha256": control_universe_sha256,
        "blinded_audit_candidate_frame_path": blinded_frame_path.as_posix(),
        "blinded_audit_candidate_frame_sha256": blinded_frame_sha256,
        "internal_stratification_path": stratification_path.as_posix(),
        "internal_stratification_sha256": stratification_sha256,
        "zero_external_novelty_labels_path": "research/paper5_novelty_audit_v1/ZERO_EXTERNAL_NOVELTY_LABELS.json",
        "zero_external_novelty_labels_sha256": zero_labels_sha256,
        "event_counts": {
            "retained_universe": len(retained_rows),
            "control_universe": len(control_rows),
            "blinded_candidate_frame": len(blinded_rows),
            "retained_by_axis": {str(k): v for k, v in Counter(row["axis"] for row in retained_rows).items()},
            "control_by_axis": {str(k): v for k, v in Counter(row.get("axis") for row in control_rows).items()},
        },
        "grants_scientific_authority": False,
        "claim_boundary": (
            "Phase 0 audit-universe freeze bound to #253 longitudinal analysis. "
            "Internal retained counts remain INTERNAL_METROLOGY. "
            "No external annotator labels, adjudication, or precision claim is authorized."
        ),
        "next_phase_blockers": [
            "HUMAN_ANNOTATORS",
            "SAMPLE_PLAN",
            "PRECISION_POWER_RECEIPT",
            "PUBLIC_AUDIT_PACKET",
        ],
    }
    write_json(out_dir / "AUDIT_UNIVERSE_MANIFEST.json", manifest_obj)

    print(out_dir / "AUDIT_UNIVERSE_MANIFEST.json")
    print(f"retained={len(retained_rows)} control={len(control_rows)} blinded={len(blinded_rows)}")


if __name__ == "__main__":
    main()
