#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path

PACKAGES = ("torch", "transformers", "peft", "accelerate", "huggingface-hub")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build() -> dict[str, object]:
    versions: dict[str, str] = {}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise SystemExit(f"RESOURCE_BLOCKED: required package missing: {name}") from exc
    try:
        import torch
    except Exception as exc:  # pragma: no cover - import failure is the result
        raise SystemExit(f"RESOURCE_BLOCKED: torch import failed: {type(exc).__name__}:{exc}") from exc
    payload: dict[str, object] = {
        "schema_version": "rakl-p4-phase2-environment-fingerprint-v2",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": str(Path(sys.executable).resolve()),
        "virtual_env": str(Path(os.environ.get("VIRTUAL_ENV", "")).resolve()) if os.environ.get("VIRTUAL_ENV") else "",
        "packages": versions,
        "torch_cuda_version": str(torch.version.cuda),
        "module_pytorch_root": os.environ.get("EBROOTPYTORCH", ""),
        "module_pytorch_version": os.environ.get("EBVERSIONPYTORCH", ""),
    }
    payload["canonical_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", type=Path)
    ap.add_argument("--expected", type=Path)
    args = ap.parse_args()
    payload = build()
    if args.expected:
        expected = json.loads(args.expected.read_text())
        if expected != payload:
            raise SystemExit(
                "RESOURCE_BLOCKED: environment fingerprint drift\nexpected="
                + json.dumps(expected, sort_keys=True)
                + "\nobserved="
                + json.dumps(payload, sort_keys=True)
            )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
