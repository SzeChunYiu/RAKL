"""Powered two-arm pendulum comparison on a hosted model (GLM-5.2 via Z.AI).

NOT a sealed local run. No model-weight attestation is possible against a hosted
endpoint, so this can never substitute for the frozen local-provider confirmatory
protocol. Purpose: answer, quickly, the two questions that n=1 could never answer —
(1) does ANY available model clear the >=2/3 capability gate, and
(2) at that operating point, does the leak-free v4_4 RAKL context change performance.

Uses the registered v4_4 normalizer and the registered evaluator
(rakl.matched_microtrial::score_pendulum_answer). No bespoke scoring.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from math import comb, sqrt
from pathlib import Path

ROOT = Path("/Users/billy/RAKL")
sys.path.insert(0, str(ROOT / "src"))

from rakl.matched_microtrial import score_pendulum_answer  # noqa: E402
from rakl.paper2_pendulum_microtrial import _parse_answer  # noqa: E402
from rakl.paper2_pendulum_microtrial_v4_4 import normalize_pendulum_output_v4_4  # noqa: E402

V44 = ROOT / "research/paper2_microtrial_v4_4"
SYSTEM = (V44 / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8")
ARMS = {
    "DIRECT_CORPUS": (V44 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
    "RAKL_CONTEXT": (V44 / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
}
BASE = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
TOKEN = os.environ["ANTHROPIC_AUTH_TOKEN"]
MODEL = os.environ.get("RUN_MODEL", "glm-5.2")
N = int(os.environ.get("RUN_N", "30"))
TEMP = float(os.environ.get("RUN_TEMP", "1.0"))
GATE = 2.0 / 3.0

COORDS = [
    "small_angle_is_asymptotic",
    "finite_amplitude_increases_period",
    "context_distinct_claims_not_direct_contradictions",
    "ideal_period_is_mass_invariant",
    "context_alignment_required_before_contradiction",
]


def call(prompt: str) -> tuple[str | None, str | None]:
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "temperature": TEMP,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/v1/messages",
        data=body,
        headers={
            "x-api-key": TOKEN,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            payload = json.load(r)
        return "".join(c.get("text", "") for c in payload.get("content", []) if c.get("type") == "text"), None
    except Exception as exc:  # transport/provider failure is data, not a crash
        return None, f"{type(exc).__name__}: {exc}"


def trial(args):
    arm, idx = args
    raw, err = call(ARMS[arm])
    rec = {"arm": arm, "trial": idx, "transport_error": err, "parse_valid": False, "score": None}
    if raw is None:
        return rec
    try:
        answer = _parse_answer(normalize_pendulum_output_v4_4(raw))
    except Exception as exc:
        rec["parse_error"] = f"{type(exc).__name__}: {exc}"
        return rec
    rec["parse_valid"] = True
    rec["score"] = asdict(score_pendulum_answer(answer))
    rec["answer"] = {c: getattr(answer, c) for c in COORDS}
    return rec


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.959964, k / n
    den = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den
    mar = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, cen - mar), min(1.0, cen + mar))


def two_prop_p(k1, n1, k2, n2) -> float:
    """Two-sided z-test on two proportions."""
    if n1 == 0 or n2 == 0:
        return float("nan")
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs(p1 - p2) / se
    # normal tail via erfc
    from math import erfc
    return erfc(z / sqrt(2))


def main() -> int:
    jobs = [(arm, i) for arm in ARMS for i in range(N)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(trial, jobs))

    out = {"model": MODEL, "temperature": TEMP, "n_per_arm": N, "arms": {},
           "provenance": {
               "sealed_local_run": False,
               "provider_api_transaction": True,
               "model_weight_attestation": "IMPOSSIBLE_HOSTED_ENDPOINT",
               "substitutes_for_confirmatory_protocol": False,
               "prompts": "research/paper2_microtrial_v4_4 (leak-free)",
               "evaluator": "rakl.matched_microtrial::score_pendulum_answer",
               "normalizer": "normalize_pendulum_output_v4_4",
           }}
    for arm in ARMS:
        rs = [r for r in records if r["arm"] == arm]
        parsed = [r for r in rs if r["parse_valid"]]
        exact = [r for r in parsed if r["score"]["exact_conceptual_pass"]]
        concept = [r["score"]["conceptual_correct"] for r in parsed]
        out["arms"][arm] = {
            "n": len(rs),
            "transport_errors": sum(1 for r in rs if r["transport_error"]),
            "parse_valid": len(parsed),
            "parse_rate": len(parsed) / len(rs) if rs else 0,
            "exact_pass": len(exact),
            "exact_pass_rate": len(exact) / len(parsed) if parsed else 0,
            "exact_pass_ci95": wilson(len(exact), len(parsed)),
            "mean_conceptual": sum(concept) / len(concept) if concept else 0,
            "mean_conceptual_frac": (sum(concept) / len(concept) / 5) if concept else 0,
            "misalignment_recall": sum(r["score"]["misalignment_recall"] for r in parsed) / len(parsed) if parsed else 0,
            "refutation_recall": sum(r["score"]["refutation_recall"] for r in parsed) / len(parsed) if parsed else 0,
            "required_support_recall": sum(r["score"]["required_support_recall"] for r in parsed) / len(parsed) if parsed else 0,
        }

    d, rk = out["arms"]["DIRECT_CORPUS"], out["arms"]["RAKL_CONTEXT"]
    out["comparison"] = {
        "exact_pass_delta_rakl_minus_direct": rk["exact_pass_rate"] - d["exact_pass_rate"],
        "exact_pass_p_two_sided": two_prop_p(rk["exact_pass"], rk["parse_valid"], d["exact_pass"], d["parse_valid"]),
        "mean_conceptual_delta": rk["mean_conceptual"] - d["mean_conceptual"],
    }
    # capability gate: is the BEST arm above the >=2/3 floor?
    best = max(("DIRECT_CORPUS", d), ("RAKL_CONTEXT", rk), key=lambda kv: kv[1]["exact_pass_rate"])
    k, n = best[1]["exact_pass"], best[1]["parse_valid"]
    pval_meets = sum(comb(n, i) * GATE**i * (1 - GATE) ** (n - i) for i in range(0, k + 1)) if n else 1.0
    out["capability_gate"] = {
        "floor": GATE, "best_arm": best[0], "successes": k, "trials": n,
        "rate": k / n if n else 0, "ci95": wilson(k, n),
        "p_one_sided_reject_meets_floor": pval_meets,
        "gate_cleared_point_estimate": (k / n if n else 0) >= GATE,
    }
    out["records"] = records
    dest = Path(__file__).parent / "main-glm-powered-result.json"
    dest.write_text(json.dumps(out, indent=1))
    summary = {k: v for k, v in out.items() if k != "records"}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
