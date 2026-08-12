from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


def stable_hash(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def paired_normal_summary(a: Sequence[float], b: Sequence[float]) -> dict[str, float | int]:
    if len(a) != len(b):
        raise ValueError("paired samples must have equal length")
    n = len(a)
    if n == 0:
        return {"n": 0, "delta": 0.0, "se": 0.0, "ci95_lo": 0.0, "ci95_hi": 0.0, "p_two_sided": 1.0}
    d = [x - y for x, y in zip(a, b)]
    md = mean(d)
    if n < 2:
        se = 0.0
    else:
        var = sum((x - md) ** 2 for x in d) / (n - 1)
        se = math.sqrt(var / n)
    p = 1.0 if se == 0 else math.erfc(abs(md / se) / math.sqrt(2))
    return {
        "n": n,
        "delta": md,
        "se": se,
        "ci95_lo": md - 1.96 * se,
        "ci95_hi": md + 1.96 * se,
        "p_two_sided": p,
    }


def f1(pred: Iterable[str], gold: Iterable[str]) -> float:
    p, g = set(pred), set(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    tp = len(p & g)
    precision = tp / len(p)
    recall = tp / len(g)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def deterministic_sample(items: Sequence[Any], k: int, seed: int) -> list[Any]:
    rng = random.Random(seed)
    if k >= len(items):
        return list(items)
    idx = list(range(len(items)))
    rng.shuffle(idx)
    return [items[i] for i in idx[:k]]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
