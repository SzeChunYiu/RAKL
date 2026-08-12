"""Run the graded battery: 4 difficulty levels x 2 arms x N on a hosted model.

Leak controls are re-asserted at runtime and the run ABORTS if either fails:
  * mechanical (all-dimension) baseline must NOT solve the task
  * no per-source disposition may appear in either prompt
"""
from __future__ import annotations

import json
import os
import random
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from math import erfc, sqrt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main_battery import (  # noqa: E402
    direct_prompt, disposition_scan, generate, mechanical_baseline, rakl_prompt, score,
)

BASE = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
TOKEN = os.environ["ANTHROPIC_AUTH_TOKEN"]
MODEL = os.environ.get("RUN_MODEL", "glm-5.2")
N = int(os.environ.get("RUN_N", "30"))
LEVELS = [("L1", 8, 2, 2), ("L2", 14, 4, 4), ("L3", 20, 4, 7), ("L4", 26, 5, 10)]


def call(prompt: str) -> tuple[str | None, str | None]:
    body = json.dumps({"model": MODEL, "max_tokens": 1500, "temperature": 1.0,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(f"{BASE}/v1/messages", data=body, headers={
        "x-api-key": TOKEN, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            p = json.load(r)
        return "".join(c.get("text", "") for c in p.get("content", []) if c.get("type") == "text"), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def parse(raw: str) -> dict | None:
    s = raw.strip()
    if "```" in s:
        seg = s.split("```")
        for part in seg:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                s = part
                break
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0:
        return None
    try:
        return json.loads(s[i:j + 1])
    except Exception:
        return None


def one(job):
    lvl, arm, task = job
    raw, err = call(direct_prompt(task) if arm == "DIRECT" else rakl_prompt(task))
    if raw is None:
        return {"level": lvl, "arm": arm, "ok": False, "transport_error": err}
    pred = parse(raw)
    if pred is None:
        return {"level": lvl, "arm": arm, "ok": False, "parse_error": True}
    return {"level": lvl, "arm": arm, "ok": True, **score(pred, task)}


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = sqrt(va / len(a) + vb / len(b))
    if se == 0:
        return ma - mb, 1.0
    t = (ma - mb) / se
    return ma - mb, erfc(abs(t) / sqrt(2))


def main() -> int:
    rng = random.Random(20260812)
    tasks, controls = {}, {}
    for lvl, ns, nd, nm in LEVELS:
        ts = [generate(rng, n_sources=ns, n_dims=nd, n_near_miss=nm, idx=i) for i in range(N)]
        tasks[lvl] = ts
        mech = [score(mechanical_baseline(t), t) for t in ts]
        leaks = sorted({f"{a}:{x}" for t in ts for a, xs in disposition_scan(t).items() for x in xs})
        controls[lvl] = {"mechanical_exact": sum(m["exact_pass"] for m in mech) / len(mech),
                         "mechanical_mean_f1": sum(m["mean_f1"] for m in mech) / len(mech),
                         "disposition_leaks": leaks}
        if controls[lvl]["mechanical_exact"] > 0.05 or leaks:
            print(f"ABORT {lvl}: leak control failed -> {controls[lvl]}")
            return 1

    jobs = [(lvl, arm, t) for lvl, ts in tasks.items() for arm in ("DIRECT", "RAKL") for t in ts]
    with ThreadPoolExecutor(max_workers=8) as pool:
        recs = list(pool.map(one, jobs))

    out = {"model": MODEL, "n_per_cell": N, "controls": controls, "levels": {},
           "provenance": {"sealed_local_run": False, "provider_api_transaction": True,
                          "model_weight_attestation": "IMPOSSIBLE_HOSTED_ENDPOINT",
                          "ground_truth": "verifier over generator structure; never 'which coordinate was perturbed'",
                          "rakl_arm": "normalized context coordinates only; no target comparison, no relevance filter, no disposition"}}
    for lvl, ns, nd, nm in LEVELS:
        cell = {}
        for arm in ("DIRECT", "RAKL"):
            rs = [r for r in recs if r["level"] == lvl and r["arm"] == arm]
            ok = [r for r in rs if r["ok"]]
            cell[arm] = {
                "n": len(rs), "usable": len(ok),
                "parse_fail": sum(1 for r in rs if r.get("parse_error")),
                "transport_fail": sum(1 for r in rs if r.get("transport_error")),
                "exact_pass_rate": sum(r["exact_pass"] for r in ok) / len(ok) if ok else 0,
                "mean_f1": sum(r["mean_f1"] for r in ok) / len(ok) if ok else 0,
                "misaligned_f1": sum(r["misaligned_f1"] for r in ok) / len(ok) if ok else 0,
                "support_f1": sum(r["support_f1"] for r in ok) / len(ok) if ok else 0,
                "_f1s": [r["mean_f1"] for r in ok],
                "_ex": [1.0 if r["exact_pass"] else 0.0 for r in ok],
            }
        df1, pf1 = welch(cell["RAKL"]["_f1s"], cell["DIRECT"]["_f1s"])
        dex, pex = welch(cell["RAKL"]["_ex"], cell["DIRECT"]["_ex"])
        for a in ("DIRECT", "RAKL"):
            cell[a].pop("_f1s"); cell[a].pop("_ex")
        out["levels"][lvl] = {"sources": ns, "dims": nd, "near_miss": nm, "arms": cell,
                              "delta_mean_f1": df1, "p_mean_f1": pf1,
                              "delta_exact": dex, "p_exact": pex,
                              "mechanical_mean_f1": controls[lvl]["mechanical_mean_f1"]}
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main-battery-result.json")
    with open(dest, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
