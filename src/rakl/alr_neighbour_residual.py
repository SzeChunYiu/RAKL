"""Neighbouring-benchmark residual audit for the ALR panel (#154).

Upgrades the PROTOCOL_V1 neighbouring-benchmark stub from provisional intent to
an explicit residual demonstration. Novelty is still not licensed: several
parents remain ABSTRACT_ONLY / CANNOT_CHECK, and no model has been evaluated.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence, Tuple

__all__ = [
    "AUDIT_PATH",
    "NeighbourBenchmarkRow",
    "NeighbourResidualAudit",
    "load_audit",
    "validate_audit",
]

_REPO = Path(__file__).resolve().parents[2]
AUDIT_PATH = (
    _REPO
    / "research"
    / "paper2_alr_neighbour_residual"
    / "NEIGHBOUR_BENCHMARK_RESIDUAL_AUDIT.json"
)


@dataclass(frozen=True)
class NeighbourBenchmarkRow:
    benchmark_id: str
    unit_of_evaluation: str
    labels_scientific_authority_deltas: str
    separates_pred_mech_ident: str
    separates_experience_from_evidence: str
    evidence_level: str
    residual_gap: str
    claim_allowed_today: str


@dataclass(frozen=True)
class NeighbourResidualAudit:
    schema_version: str
    status: str
    novelty_licensed: bool
    grants_scientific_authority: bool
    rows: Tuple[NeighbourBenchmarkRow, ...]
    artifact_hash: str


def load_audit(path: Path | None = None) -> Mapping[str, object]:
    target = path or AUDIT_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def validate_audit(payload: Mapping[str, object] | None = None) -> NeighbourResidualAudit:
    data = dict(payload) if payload is not None else dict(load_audit())
    if data.get("grants_scientific_authority") is not False:
        raise AssertionError("neighbour residual audit cannot grant authority")
    if data.get("novelty_licensed") is not False:
        raise AssertionError("benchmark novelty must remain unlicensed")
    if data.get("status") not in {"RESIDUAL_DEMONSTRATED_NOVELTY_UNLICENSED", "CANNOT_CHECK"}:
        raise AssertionError(f"unexpected status: {data.get('status')}")
    rows_raw = data.get("rows")
    if not isinstance(rows_raw, list) or len(rows_raw) < 4:
        raise AssertionError("expected at least four neighbour rows")
    rows: list[NeighbourBenchmarkRow] = []
    required = {
        "benchmark_id",
        "unit_of_evaluation",
        "labels_scientific_authority_deltas",
        "separates_pred_mech_ident",
        "separates_experience_from_evidence",
        "evidence_level",
        "residual_gap",
        "claim_allowed_today",
    }
    for row in rows_raw:
        if not isinstance(row, dict) or set(required) - set(row):
            raise AssertionError(f"malformed row: {row!r}")
        rows.append(
            NeighbourBenchmarkRow(
                benchmark_id=str(row["benchmark_id"]),
                unit_of_evaluation=str(row["unit_of_evaluation"]),
                labels_scientific_authority_deltas=str(row["labels_scientific_authority_deltas"]),
                separates_pred_mech_ident=str(row["separates_pred_mech_ident"]),
                separates_experience_from_evidence=str(row["separates_experience_from_evidence"]),
                evidence_level=str(row["evidence_level"]),
                residual_gap=str(row["residual_gap"]),
                claim_allowed_today=str(row["claim_allowed_today"]),
            )
        )
    # Residual demonstration: no neighbour may already claim full typed ALR.
    for row in rows:
        if row.benchmark_id == "ALR_V2_THIS_PROTOCOL":
            continue
        if row.labels_scientific_authority_deltas.lower() in {"yes", "full", "typed_axes"}:
            raise AssertionError(
                f"{row.benchmark_id} already labels typed authority deltas; residual collapses"
            )
    digest = hashlib.sha256(
        json.dumps(
            {k: v for k, v in data.items() if k != "artifact_hash"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    if data.get("artifact_hash") != digest:
        raise AssertionError("artifact_hash mismatch")
    return NeighbourResidualAudit(
        schema_version=str(data["schema_version"]),
        status=str(data["status"]),
        novelty_licensed=False,
        grants_scientific_authority=False,
        rows=tuple(rows),
        artifact_hash=digest,
    )
