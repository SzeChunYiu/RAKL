#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SET = ROOT / "research" / "paper3" / "annotation" / "SOURCE_ITEM_SET_V2_1_20260810.json"
EXPECTED_SOURCE_FILE_SHA256 = "e865a1767ddedeac86da84fcae9bdd6c11659706edf3e76a00653761e6c5da68"
EXPECTED_ITEM_COUNT = 16
OUTDIR = ROOT / "research" / "paper2_real_source_span_v1"

FORBIDDEN_PUBLIC_KEYS = {
    "source_item_id",
    "family",
    "qoi",
    "candidate_load_bearing_boundary",
    "candidate_load_bearing_invariant",
    "source_dependencies",
    "target_dependencies",
    "source_skill_tags",
    "target_skill_tags",
    "source_surface_terms",
    "target_surface_terms",
    "source_domain",
    "target_domain",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _opaque_id(source_item_id: str) -> str:
    digest = hashlib.sha256(("P2-REAL-SOURCE-V1:" + source_item_id).encode("utf-8")).hexdigest()
    return "rs-" + digest[:16]


def _parse_reference(raw: str) -> dict[str, str]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("reference must be non-empty text")
    parts = [part.strip() for part in raw.split("|")]
    identifier = parts[0] if parts else raw.strip()
    title = parts[1] if len(parts) > 1 else ""
    locator = parts[2] if len(parts) > 2 else ""
    if not locator:
        for part in parts:
            if part.startswith(("https://", "http://")):
                locator = part
                break
    return {"identifier": identifier, "title": title, "locator": locator}


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    raw = SOURCE_SET.read_bytes()
    observed = _sha256_bytes(raw)
    if observed != EXPECTED_SOURCE_FILE_SHA256:
        raise RuntimeError(f"source set hash mismatch: {observed}")
    source = json.loads(raw)
    items = source.get("items")
    if not isinstance(items, list) or len(items) != EXPECTED_ITEM_COUNT:
        raise RuntimeError("unexpected source item count")

    public_rows: list[dict[str, Any]] = []
    linkage_rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise RuntimeError("source item must be an object")
        source_item_id = item.get("source_item_id")
        if not isinstance(source_item_id, str) or not source_item_id:
            raise RuntimeError("source item id missing")
        opaque = _opaque_id(source_item_id)
        source_refs = [_parse_reference(value) for value in item.get("source_evidence", [])]
        target_refs = [_parse_reference(value) for value in item.get("target_evidence", [])]
        if not source_refs or not target_refs:
            raise RuntimeError(f"{source_item_id}: missing primary-source references")
        public_rows.append(
            {
                "opaque_item_id": opaque,
                "source_reference": source_refs,
                "target_reference": target_refs,
                "instruction": (
                    "Using only exact primary-source text acquired and hash-bound under this item, "
                    "identify the target quantity of interest and determine whether a source structural "
                    "result or method is licensed for reuse in the target. Return explicit source/target "
                    "span bindings and LICENSED, REJECTED, or CANNOT_CHECK; do not infer missing evidence."
                ),
            }
        )
        linkage_rows.append(
            {
                "opaque_item_id": opaque,
                "source_item_id": source_item_id,
                "development_only_internal_coordinates": {
                    key: item.get(key)
                    for key in sorted(FORBIDDEN_PUBLIC_KEYS - {"source_item_id"})
                    if key in item
                },
            }
        )

    public_rows.sort(key=lambda row: row["opaque_item_id"])
    linkage_rows.sort(key=lambda row: row["opaque_item_id"])
    public_payload = {
        "schema_version": "paper2-real-source-acquisition-public-v1",
        "source_set_file_sha256": observed,
        "candidate_visible": True,
        "item_count": len(public_rows),
        "items": public_rows,
        "authority_boundary": "source acquisition/extraction instrument only; no gold, verdict or scientific authority",
    }
    public_payload["canonical_sha256"] = _sha256_bytes(_canonical_bytes(public_payload))
    linkage_payload = {
        "schema_version": "paper2-real-source-development-linkage-v1",
        "source_set_file_sha256": observed,
        "candidate_visible": False,
        "development_only": True,
        "item_count": len(linkage_rows),
        "items": linkage_rows,
        "claim_boundary": "internal development diagnosis only; cannot authorize confirmatory natural-domain extraction",
        "grants_scientific_authority": False,
    }
    linkage_payload["canonical_sha256"] = _sha256_bytes(_canonical_bytes(linkage_payload))
    return public_payload, linkage_payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    public_payload, linkage_payload = build()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        OUTDIR / "CANDIDATE_ACQUISITION_MANIFEST.json": public_payload,
        OUTDIR / "DEVELOPMENT_LINKAGE.json": linkage_payload,
    }
    for path, payload in outputs.items():
        text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f"generated artifact out of date: {path.relative_to(ROOT)}")
        else:
            path.write_text(text)
    print(json.dumps({
        "status": "PASS",
        "item_count": len(public_payload["items"]),
        "public_canonical_sha256": public_payload["canonical_sha256"],
        "linkage_canonical_sha256": linkage_payload["canonical_sha256"],
        "candidate_visible_internal_coordinate_count": sum(
            key in row for row in public_payload["items"] for key in FORBIDDEN_PUBLIC_KEYS
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
