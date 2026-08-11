#!/usr/bin/env python3
"""Attest the exact eight-file Paper-2 snapshot around native inference."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

import jsonschema


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    ).stdout.strip()


def attest(
    *,
    repo: Path,
    packet_path: Path,
    model_manifest_path: Path,
    tokenizer_manifest_path: Path,
    schema_path: Path,
    phase: str,
    output_path: Path,
    result_path: Path | None,
) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    model = json.loads(model_manifest_path.read_text(encoding="utf-8"))
    tokenizer = json.loads(tokenizer_manifest_path.read_text(encoding="utf-8"))
    snapshot = Path(model["snapshot_path"])
    if tokenizer["snapshot_path"] != str(snapshot):
        raise RuntimeError("model/tokenizer snapshot path mismatch")

    entries: list[dict[str, object]] = []
    for role, manifest in (("model", model), ("tokenizer", tokenizer)):
        for expected in manifest["files"]:
            path = snapshot / expected["path"]
            observed = {
                "role": role,
                "path": expected["path"],
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            if observed["bytes"] != expected["bytes"] or observed["sha256"] != expected["sha256"]:
                raise RuntimeError(f"snapshot identity mismatch:{role}:{expected['path']}")
            entries.append(observed)
    entries.sort(key=lambda row: (str(row["role"]), str(row["path"])))
    if len(entries) != 8 or len({str(row["path"]) for row in entries}) != 8:
        raise RuntimeError("snapshot must contain eight unique bound files")
    canonical = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError("execution checkout is dirty during snapshot attestation")
    if phase == "POST_INFERENCE" and (result_path is None or not result_path.is_file()):
        raise RuntimeError("post-inference attestation requires the result receipt")
    if phase == "PRE_INFERENCE" and result_path is not None:
        raise RuntimeError("pre-inference attestation cannot bind a result")

    receipt = {
        "schema_version": "paper2-model-snapshot-attestation-v4",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "phase": phase,
        "packet_parent_sha": packet["subject_sha"],
        "execution_checkout": {
            "head_sha": _git(repo, "rev-parse", "HEAD"),
            "tree_sha": _git(repo, "rev-parse", "HEAD^{tree}"),
            "status_entry_count": 0,
        },
        "snapshot_path": str(snapshot),
        "files": entries,
        "snapshot_canonical_sha256": canonical,
        "result_receipt_sha256": _sha256(result_path) if result_path is not None else None,
        "claim_boundary": "Snapshot immutability attestation only; not a model score or comparison.",
    }
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(receipt)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--model-manifest", type=Path, required=True)
    parser.add_argument("--tokenizer-manifest", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--phase", choices=("PRE_INFERENCE", "POST_INFERENCE"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    attest(
        repo=args.repo,
        packet_path=args.packet,
        model_manifest_path=args.model_manifest,
        tokenizer_manifest_path=args.tokenizer_manifest,
        schema_path=args.schema,
        phase=args.phase,
        output_path=args.output,
        result_path=args.result,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
