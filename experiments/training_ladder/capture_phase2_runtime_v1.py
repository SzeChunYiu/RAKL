from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

CRITICAL_PACKAGES = (
    "torch",
    "transformers",
    "tokenizers",
    "huggingface-hub",
    "peft",
    "accelerate",
    "safetensors",
    "numpy",
)


def _version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _pip_freeze() -> list[str]:
    out = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze", "--all"], text=True
    )
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def capture() -> dict[str, Any]:
    import torch

    freeze = _pip_freeze()
    freeze_bytes = ("\n".join(freeze) + "\n").encode()
    loaded_modules = tuple(
        item for item in os.environ.get("LOADEDMODULES", "").split(":") if item
    )
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    capability = (
        list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None
    )
    return {
        "schema_version": "rakl-paper4-phase2-runtime-capture-v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "torch": {
            "version": torch.__version__,
            "cuda_build": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_name": gpu_name,
            "gpu_capability": capability,
            "cudnn_version": torch.backends.cudnn.version(),
        },
        "critical_packages": {name: _version(name) for name in CRITICAL_PACKAGES},
        "loaded_modules": list(loaded_modules),
        "pip_freeze": freeze,
        "pip_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "environment": {
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
        },
        "phase2_outcome_accessed": False,
        "grants_scientific_authority": False,
    }


def validate_capture(capture: dict[str, Any]) -> None:
    if capture.get("schema_version") != "rakl-paper4-phase2-runtime-capture-v1":
        raise RuntimeError("runtime_capture_schema_mismatch")
    if capture.get("phase2_outcome_accessed") is not False:
        raise RuntimeError("runtime_capture_must_be_preoutcome")
    if capture.get("grants_scientific_authority") is not False:
        raise RuntimeError("runtime_capture_cannot_grant_authority")
    torch = capture.get("torch", {})
    if torch.get("cuda_available") is not True:
        raise RuntimeError("runtime_capture_cuda_unavailable")
    if not str(torch.get("gpu_name") or "").strip():
        raise RuntimeError("runtime_capture_gpu_identity_missing")
    packages = capture.get("critical_packages", {})
    missing = [name for name in CRITICAL_PACKAGES if not packages.get(name)]
    if missing:
        raise RuntimeError("runtime_capture_critical_packages_missing:" + ",".join(missing))
    if not capture.get("pip_freeze") or len(str(capture.get("pip_freeze_sha256", ""))) != 64:
        raise RuntimeError("runtime_capture_pip_freeze_missing")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = capture()
    validate_capture(result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "runtime_capture": str(args.out),
        "python": result["python"]["version"],
        "torch": result["torch"]["version"],
        "cuda_build": result["torch"]["cuda_build"],
        "gpu": result["torch"]["gpu_name"],
        "critical_packages": result["critical_packages"],
        "pip_freeze_sha256": result["pip_freeze_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
