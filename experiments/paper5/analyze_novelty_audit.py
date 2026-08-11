#!/usr/bin/env python3
"""Analyze independent Paper 5 retained-novelty audit annotations.

Expected JSONL fields per audit item:
  event_id: unique identifier
  axis: one of the seven RAKL novelty axes
  internal_retained: bool
  annotator_a_label: categorical label or null
  annotator_b_label: categorical label or null
  adjudicated_label: categorical label or null

Allowed labels:
  SEMANTICALLY_NEW, DUPLICATE_OR_EQUIVALENT, SUPERSESSION_ONLY,
  WRONG_AXIS, INSUFFICIENT_EVIDENCE

The script reports raw agreement, Cohen's kappa on complete two-annotator
pairs, retained-novelty precision, false-collapse rate, wrong-axis rate and
insufficient-evidence rate. It never treats missing adjudication as a negative
label.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
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
LABELS = (
    "SEMANTICALLY_NEW",
    "DUPLICATE_OR_EQUIVALENT",
    "SUPERSESSION_ONLY",
    "WRONG_AXIS",
    "INSUFFICIENT_EVIDENCE",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SystemExit(f"{path}:{lineno}: expected JSON object")
        rows.append(value)
    return rows


def validate(rows: list[dict[str, Any]]) -> None:
    ids = [row.get("event_id") for row in rows]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise SystemExit("event_id values must be non-empty and unique")
    for row in rows:
        if row.get("axis") not in AXES:
            raise SystemExit(f"{row.get('event_id')}: invalid axis")
        if not isinstance(row.get("internal_retained"), bool):
            raise SystemExit(f"{row.get('event_id')}: internal_retained must be boolean")
        for field in ("annotator_a_label", "annotator_b_label", "adjudicated_label"):
            value = row.get(field)
            if value is not None and value not in LABELS:
                raise SystemExit(f"{row.get('event_id')}: invalid {field}={value!r}")


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def cohen_kappa(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [
        row for row in rows
        if row.get("annotator_a_label") in LABELS and row.get("annotator_b_label") in LABELS
    ]
    if not complete:
        return {"complete_pair_count": 0, "raw_agreement": None, "cohen_kappa": None}
    n = len(complete)
    agree = sum(row["annotator_a_label"] == row["annotator_b_label"] for row in complete)
    a = Counter(row["annotator_a_label"] for row in complete)
    b = Counter(row["annotator_b_label"] for row in complete)
    p_o = agree / n
    p_e = sum((a[label] / n) * (b[label] / n) for label in LABELS)
    kappa = None if abs(1.0 - p_e) < 1e-15 else (p_o - p_e) / (1.0 - p_e)
    return {"complete_pair_count": n, "raw_agreement": p_o, "cohen_kappa": kappa}


def confusion(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = Counter()
    for row in rows:
        a = row.get("annotator_a_label")
        b = row.get("annotator_b_label")
        if a in LABELS and b in LABELS:
            table[(a, b)] += 1
    return [
        {"annotator_a_label": a, "annotator_b_label": b, "count": table[(a, b)]}
        for a in LABELS for b in LABELS
    ]


def axis_metrics(rows: list[dict[str, Any]], axis: str | None) -> dict[str, Any]:
    subset = rows if axis is None else [row for row in rows if row["axis"] == axis]
    adjudicated = [row for row in subset if row.get("adjudicated_label") in LABELS]
    retained = [row for row in adjudicated if row["internal_retained"]]
    zero = [row for row in adjudicated if not row["internal_retained"]]
    auditable_retained = [row for row in retained if row["adjudicated_label"] != "INSUFFICIENT_EVIDENCE"]
    auditable_zero = [row for row in zero if row["adjudicated_label"] != "INSUFFICIENT_EVIDENCE"]
    sem_new_retained = sum(row["adjudicated_label"] == "SEMANTICALLY_NEW" for row in auditable_retained)
    sem_new_zero = sum(row["adjudicated_label"] == "SEMANTICALLY_NEW" for row in auditable_zero)
    wrong_axis = sum(row["adjudicated_label"] == "WRONG_AXIS" for row in adjudicated)
    insufficient = sum(row["adjudicated_label"] == "INSUFFICIENT_EVIDENCE" for row in adjudicated)
    return {
        "axis": axis or "POOLED",
        "sample_count": len(subset),
        "adjudicated_count": len(adjudicated),
        "internally_retained_count": sum(row["internal_retained"] for row in subset),
        "internally_zero_retained_count": sum(not row["internal_retained"] for row in subset),
        "auditable_retained_count": len(auditable_retained),
        "auditable_zero_retained_count": len(auditable_zero),
        "retained_novelty_precision": safe_rate(sem_new_retained, len(auditable_retained)),
        "false_collapse_rate": safe_rate(sem_new_zero, len(auditable_zero)),
        "wrong_axis_rate": safe_rate(wrong_axis, len(adjudicated)),
        "insufficient_evidence_rate": safe_rate(insufficient, len(adjudicated)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = load_jsonl(args.annotations)
    if not rows:
        raise SystemExit("annotation file is empty")
    validate(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    metrics = [axis_metrics(rows, axis) for axis in AXES] + [axis_metrics(rows, None)]
    agreement = cohen_kappa(rows)
    confusion_rows = confusion(rows)
    write_csv(args.out_dir / "novelty_audit_metrics.csv", metrics)
    write_csv(args.out_dir / "annotator_confusion.csv", confusion_rows)

    summary = {
        "schema_version": "paper5-novelty-audit-analysis-v1",
        "annotations_sha256": hashlib.sha256(args.annotations.read_bytes()).hexdigest(),
        "event_count": len(rows),
        "metrics": metrics,
        "agreement": agreement,
        "unadjudicated_count": sum(row.get("adjudicated_label") is None for row in rows),
        "claim_boundary": (
            "Metrology audit only. Agreement/precision do not grant scientific authority to the audited research objects."
        ),
    }
    (args.out_dir / "novelty_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.out_dir / "novelty_audit_summary.json")


if __name__ == "__main__":
    main()
