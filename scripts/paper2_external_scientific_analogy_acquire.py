#!/usr/bin/env python3
"""Acquire/bind the frozen P2 external scientific-analogy corpus from local bytes.

This script performs no model inference.  It accepts local copies of the two
pre-frozen external files, verifies their Git-blob identities, hashes exact
bytes, applies the pre-outcome preview quarantines, and emits a public opaque
case stream plus a separately protected gold stream.  Both streams are hashed
before any later model call.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha1, sha256
import io
import json
from pathlib import Path
from typing import Any, Iterable

SEED = 202608141701
SCAR_BLOB_SHA = "214464cc4274f1af5a0bc1008a194b133c214e15"
PROPARA_BLOB_SHA = "e6aa2fa366c7da25b6b4f7fcb70b76e79487c7d9"
SCAR_QUARANTINE = frozenset(range(1, 11))
PROPARA_QUARANTINE = frozenset(range(0, 11))
MISSING_EVIDENCE_N = 50
MISSING_TARGET = "Target mechanism evidence is unavailable in the supplied material."


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def git_blob_sha(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def opaque_case_id(corpus: str, row_identity: str, role: str) -> str:
    return "ext-" + sha256(f"{SEED}|{corpus}|{row_identity}|{role}".encode()).hexdigest()[:24]


def order_rank(case_id: str) -> str:
    return sha256(f"{SEED}|order|{case_id}".encode()).hexdigest()


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(canonical_json_bytes(row) + b"\n" for row in rows)


def parse_scar(data: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        item = json.loads(raw)
        required = {
            "id", "lang", "system_a", "system_b", "mappings",
            "system_a_background", "system_b_background",
        }
        missing = required - set(item)
        if missing:
            raise ValueError(f"SCAR line {line_no} missing fields: {sorted(missing)}")
        if item["lang"] != "en":
            raise ValueError(f"SCAR line {line_no} is not English")
        rows.append(item)
    ids = [int(item["id"]) for item in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("SCAR ids are not unique")
    return rows


def parse_propara(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "source_paragraph", "target_paragraph", "relations",
        "distractor_target_paragraph", "random_target_paragraph",
    }
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError(f"ProPara-Logy schema mismatch: {reader.fieldnames}")
    rows = [dict(row) for row in reader]
    if not rows:
        raise ValueError("ProPara-Logy contains no rows")
    return rows


def build_manifests(
    scar_data: bytes,
    propara_data: bytes,
    *,
    expected_scar_blob: str = SCAR_BLOB_SHA,
    expected_propara_blob: str = PROPARA_BLOB_SHA,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    scar_git = git_blob_sha(scar_data)
    propara_git = git_blob_sha(propara_data)
    if scar_git != expected_scar_blob:
        raise ValueError(f"SCAR Git blob mismatch: {scar_git}")
    if propara_git != expected_propara_blob:
        raise ValueError(f"ProPara-Logy Git blob mismatch: {propara_git}")

    scar = parse_scar(scar_data)
    propara = parse_propara(propara_data)
    public: list[dict[str, Any]] = []
    gold: list[dict[str, Any]] = []

    for item in scar:
        sid = int(item["id"])
        if sid in SCAR_QUARANTINE:
            continue
        case_id = opaque_case_id("SCAR", str(sid), "TRUE")
        public.append({
            "case_id": case_id,
            "source_text": item["system_a_background"],
            "target_text": item["system_b_background"],
        })
        gold.append({
            "case_id": case_id,
            "corpus": "SCAR",
            "source_identity": sid,
            "role": "TRUE_ANALOGY",
            "gold_decision": "LICENSED",
            "gold_mappings": item["mappings"],
        })

    propara_nonquarantined: list[tuple[int, dict[str, str]]] = []
    for row_index, row in enumerate(propara):
        if row_index in PROPARA_QUARANTINE:
            continue
        propara_nonquarantined.append((row_index, row))
        for role, target, decision in (
            ("TRUE", row["target_paragraph"], "LICENSED"),
            ("CHALLENGING", row["distractor_target_paragraph"], "REJECTED"),
            ("RANDOM", row["random_target_paragraph"], "REJECTED"),
        ):
            case_id = opaque_case_id("PROPARA_LOGY", str(row_index), role)
            public.append({
                "case_id": case_id,
                "source_text": row["source_paragraph"],
                "target_text": target,
            })
            gold.append({
                "case_id": case_id,
                "corpus": "PROPARA_LOGY",
                "source_identity": row_index,
                "role": role,
                "gold_decision": decision,
                "gold_relations": row["relations"] if role == "TRUE" else "",
            })

    ranked = sorted(
        propara_nonquarantined,
        key=lambda pair: sha256(f"{SEED}|missing|{pair[0]}".encode()).hexdigest(),
    )[:MISSING_EVIDENCE_N]
    if len(ranked) != MISSING_EVIDENCE_N:
        raise ValueError("insufficient ProPara-Logy rows for missing-evidence controls")
    for row_index, row in ranked:
        case_id = opaque_case_id("PROPARA_LOGY", str(row_index), "MISSING")
        public.append({
            "case_id": case_id,
            "source_text": row["source_paragraph"],
            "target_text": MISSING_TARGET,
        })
        gold.append({
            "case_id": case_id,
            "corpus": "PROPARA_LOGY",
            "source_identity": row_index,
            "role": "MISSING_EVIDENCE",
            "gold_decision": "CANNOT_CHECK",
            "gold_relations": "",
        })

    public.sort(key=lambda row: order_rank(row["case_id"]))
    gold_by_id = {row["case_id"]: row for row in gold}
    if len(gold_by_id) != len(gold):
        raise ValueError("duplicate protected case id")
    gold = [gold_by_id[row["case_id"]] for row in public]

    public_bytes = _jsonl_bytes(public)
    gold_bytes = _jsonl_bytes(gold)
    binding = {
        "schema_version": "paper2-external-scientific-analogy-corpus-binding-v1",
        "seed": SEED,
        "grants_scientific_authority": False,
        "sources": {
            "SCAR": {
                "git_blob_sha": scar_git,
                "sha256": sha256_hex(scar_data),
                "bytes": len(scar_data),
                "rows": len(scar),
                "quarantined_ids": sorted(SCAR_QUARANTINE),
                "usable_rows": sum(int(item["id"]) not in SCAR_QUARANTINE for item in scar),
            },
            "PROPARA_LOGY": {
                "git_blob_sha": propara_git,
                "sha256": sha256_hex(propara_data),
                "bytes": len(propara_data),
                "rows": len(propara),
                "quarantined_csv_indices": sorted(PROPARA_QUARANTINE),
                "usable_rows": len(propara_nonquarantined),
            },
        },
        "cases": {
            "public_n": len(public),
            "protected_n": len(gold),
            "missing_evidence_n": MISSING_EVIDENCE_N,
            "public_manifest_sha256": sha256_hex(public_bytes),
            "protected_gold_manifest_sha256": sha256_hex(gold_bytes),
        },
        "candidate_visible_gold": False,
        "model_calls_performed": 0,
    }
    return binding, public, gold


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scar", type=Path, required=True)
    parser.add_argument("--propara", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    scar_data = args.scar.read_bytes()
    propara_data = args.propara.read_bytes()
    binding, public, gold = build_manifests(scar_data, propara_data)
    args.outdir.mkdir(parents=True, exist_ok=True)
    public_bytes = _jsonl_bytes(public)
    gold_bytes = _jsonl_bytes(gold)
    (args.outdir / "PUBLIC_CASE_MANIFEST.jsonl").write_bytes(public_bytes)
    (args.outdir / "PROTECTED_GOLD_MANIFEST.jsonl").write_bytes(gold_bytes)
    (args.outdir / "EXTERNAL_CORPUS_BINDING.json").write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(binding, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
