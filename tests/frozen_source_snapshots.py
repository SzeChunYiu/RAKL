"""Execution-time snapshot resolution for frozen microtrial artifacts.

Frozen batch contracts and execution packets bind source files by repository
path and sha256 as the bytes existed when the experiment was frozen and
executed. Source files legitimately evolve afterwards; historical artifacts
must never be regenerated to track the live tree. The registry below redirects
a frozen binding to its archived snapshot only for the exact (path, sha256)
pair, and every caller still asserts that the resolved bytes hash to the
sha256 recorded in the frozen artifact — a snapshot can never bless drift.

See research/paper2_microtrial_frozen_sources/README.md for provenance.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

FROZEN_SOURCE_SNAPSHOTS: dict[tuple[str, str], str] = {
    (
        "src/rakl/paper2_pendulum_microtrial.py",
        "51f3e992206dcfeccceea98388fb799848c5f0b600361c7a52c1047dd9ce9590",
    ): "research/paper2_microtrial_frozen_sources/paper2_pendulum_microtrial_51f3e992.py.frozen",
}


def resolve_frozen_binding(root: Path, path: str, sha256: str) -> Path:
    """Resolve a frozen binding target, preferring the archived execution-time
    snapshot when the bound (path, sha256) pair names one."""
    snapshot = FROZEN_SOURCE_SNAPSHOTS.get((path, sha256))
    return root / snapshot if snapshot is not None else root / path


def _iter_bindings(bindings: object):
    if isinstance(bindings, dict):
        yield from bindings.values()
    elif isinstance(bindings, list):
        yield from bindings


def execution_time_base_dir(root: Path, packet: dict, base_dir: Path) -> Path:
    """Materialize the packet's bound files into ``base_dir`` exactly as they
    existed at execution time, substituting archived snapshots where the live
    file has since evolved. ``audit_execution_packet`` run against the result
    verifies the frozen artifact against its own execution-time tree instead
    of the moving live tree."""
    for binding in _iter_bindings(packet.get("bindings")):
        if not isinstance(binding, dict):
            continue
        raw_path = binding.get("path")
        sha256 = binding.get("sha256")
        if not isinstance(raw_path, str) or Path(raw_path).is_absolute():
            continue
        source = resolve_frozen_binding(root, raw_path, sha256 or "")
        if not source.is_file():
            continue
        target = base_dir / raw_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        # Secondary artifacts referenced from within a bound JSON file (for
        # example an evaluator's implementation_source_path) resolve relative
        # to base_dir as well; copy them when present in the live tree.
        if raw_path.endswith(".json"):
            try:
                loaded = json.loads(target.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if (
                        key.endswith("_source_path")
                        and isinstance(value, str)
                        and not Path(value).is_absolute()
                        and (root / value).is_file()
                    ):
                        secondary = base_dir / value
                        secondary.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(root / value, secondary)
    return base_dir


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
