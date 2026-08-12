from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any


def stable_hash(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path: Any) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()
