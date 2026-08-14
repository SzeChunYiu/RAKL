"""Stage A instrument validation for graded structure-space metric candidates.

Frozen BEFORE any result exists (see PROTOCOL_METRIC_V1.json). Deterministic,
stdlib-only. Validates candidate graded metrics on planted known-answer
structure worlds. This validates INSTRUMENTS, not analogy semantics: external
validation (Stage B, ARN third-party labels) is a separate, currently blocked
epoch — see the protocol.

Exit codes: 0 evaluated; 2 self-test failure; 3 CANNOT_CHECK.

Endpoint classification follows SRSU-P6-CLASSIFICATION-CORRECTION-V1:
CONFORMANCE_not_evidence cells are true by construction or by theorem and are
never reportable as measurements; MEASURED_evidence cells can genuinely fail.
"""

from __future__ import annotations

import itertools
import json
import random
import sys
import time
from collections import Counter

REFUSED = "REFUSED"

# ---------------------------------------------------------------- graphs

def nodes_of(edges: frozenset) -> frozenset:
    return frozenset(x for e in edges for x in e)


def signature(edges: frozenset):
    """Relation count + sorted (out, in) degree multiset (analogy_retrieval v1)."""
    out_d: Counter = Counter()
    in_d: Counter = Counter()
    for s, t in edges:
        out_d[s] += 1
        in_d[t] += 1
    ns = set(out_d) | set(in_d)
    return (len(edges), tuple(sorted((out_d[n], in_d[n]) for n in ns)))


def gen_base(seed: int) -> frozenset:
    rng = random.Random(f"base:{seed}")
    n = rng.randint(5, 7)
    m = rng.randint(6, 10)
    pool = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(pool)
    return frozenset(pool[:m])


def relabel(edges: frozenset, seed: int, prefix: str) -> frozenset:
    rng = random.Random(f"perm:{seed}:{prefix}")
    ns = sorted(nodes_of(edges))
    perm = list(range(len(ns)))
    rng.shuffle(perm)
    ren = {v: f"{prefix}{perm[i]}" for i, v in enumerate(ns)}
    return frozenset((ren[s], ren[t]) for s, t in edges)


def edit_k(edges: frozenset, k: int, seed: int) -> frozenset:
    """k cumulative edits (add/delete/rewire), never touching the same slot twice."""
    rng = random.Random(f"edit:{seed}:{k}")
    cur = set(edges)
    ns = sorted(nodes_of(edges))
    touched: set = set()
    ops = 0
    guard = 0
    while ops < k and guard < 1000:
        guard += 1
        op = rng.choice(("add", "del", "rewire"))
        if op == "add":
            cand = [(a, b) for a in ns for b in ns
                    if a != b and (a, b) not in cur and (a, b) not in touched]
            if not cand:
                continue
            e = rng.choice(sorted(cand))
            cur.add(e)
            touched.add(e)
        elif op == "del":
            cand = [e for e in sorted(cur) if e not in touched]
            if len(cur) <= 1 or not cand:
                continue
            e = rng.choice(cand)
            cur.remove(e)
            touched.add(e)
        else:
            cand = [e for e in sorted(cur) if e not in touched]
            if not cand:
                continue
            s, t = rng.choice(cand)
            tgt = [(s, b) for b in ns if b not in (s, t) and (s, b) not in cur
                   and (s, b) not in touched]
            if not tgt:
                continue
            new = rng.choice(sorted(tgt))
            cur.remove((s, t))
            cur.add(new)
            touched.add((s, t))
            touched.add(new)
        ops += 1
    if ops < k:
        raise RuntimeError("CANNOT_CHECK: edit budget not realizable")
    return frozenset(cur)


def isomorphic(e1: frozenset, e2: frozenset) -> bool:
    n1, n2 = sorted(nodes_of(e1)), sorted(nodes_of(e2))
    if len(n1) != len(n2) or len(e1) != len(e2):
        return False
    for perm in itertools.permutations(n2):
        m = dict(zip(n1, perm))
        if frozenset((m[s], m[t]) for s, t in e1) == e2:
            return True
    return False

# ---------------------------------------------------------------- metrics

def m0_exact_signature(e1, e2):
    return 0.0 if signature(e1) == signature(e2) else 1.0


def m1_signature_l1(e1, e2):
    (c1, d1), (c2, d2) = signature(e1), signature(e2)
    pad = max(len(d1), len(d2))
    a = list(d1) + [(0, 0)] * (pad - len(d1))
    b = list(d2) + [(0, 0)] * (pad - len(d2))
    a.sort()
    b.sort()
    num = abs(c1 - c2) + sum(abs(x[0] - y[0]) + abs(x[1] - y[1]) for x, y in zip(a, b))
    den = c1 + c2 + sum(x + y for p in d1 for x in [p[0]] for y in [p[1]]) \
        + sum(x + y for p in d2 for x in [p[0]] for y in [p[1]])
    return num / den if den else 0.0


def _wl_labels(edges: frozenset, depth: int):
    ns = sorted(nodes_of(edges))
    lab = {v: str((sum(1 for e in edges if e[0] == v),
                   sum(1 for e in edges if e[1] == v))) for v in ns}
    out = [Counter(lab.values())]
    for _ in range(depth):
        nxt = {}
        for v in ns:
            outs = sorted(lab[t] for s, t in edges if s == v)
            ins = sorted(lab[s] for s, t in edges if t == v)
            nxt[v] = str((lab[v], tuple(outs), tuple(ins)))
        lab = nxt
        out.append(Counter(lab.values()))
    return out


def m2_wl3(e1, e2):
    l1, l2 = _wl_labels(e1, 3), _wl_labels(e2, 3)
    sims = []
    for c1, c2 in zip(l1, l2):
        inter = sum((c1 & c2).values())
        union = sum((c1 | c2).values())
        sims.append(inter / union if union else 1.0)
    return 1.0 - sum(sims) / len(sims)


def m3_ged_exact(e1, e2):
    n1, n2 = sorted(nodes_of(e1)), sorted(nodes_of(e2))
    if len(n1) > len(n2):
        e1, e2, n1, n2 = e2, e1, n2, n1
    best = None
    for perm in itertools.permutations(n2, len(n1)):
        m = dict(zip(n1, perm))
        mapped = frozenset((m[s], m[t]) for s, t in e1)
        cost = len(mapped.symmetric_difference(e2)) + (len(n2) - len(n1))
        if best is None or cost < best:
            best = cost
    den = len(n1) + len(n2) + len(e1) + len(e2)
    return best / den if den else 0.0


def m_refuse_all(e1, e2):
    return 1.0


METRICS = {
    "M0_exact_signature_v1": m0_exact_signature,
    "M1_signature_l1": m1_signature_l1,
    "M2_wl3": m2_wl3,
    "M3_ged_exact": m3_ged_exact,
    "M_refuse_all_planted_fail": m_refuse_all,
}


def dist(name, e1, e2):
    if not e1 or not e2:
        return REFUSED
    return METRICS[name](e1, e2)

# ---------------------------------------------------------------- stats

def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)

# ---------------------------------------------------------------- worlds

N_BASE = 40
KS = (1, 2, 3, 4)
N_DECOY = 20


def build_worlds():
    worlds = {"iso": [], "graded": [], "decoy": []}
    for s in range(N_BASE):
        g = gen_base(s)
        worlds["iso"].append((relabel(g, s, "x"), relabel(g, s + 1000, "y")))
        row = []
        for k in KS:
            h = edit_k(g, k, s)
            row.append((k, relabel(g, s, "x"), relabel(h, s + 2000 + k, "y")))
        worlds["graded"].append(row)
    # decoys: signature-equal, verified non-isomorphic
    buckets: dict = {}
    found = 0
    for s in range(100000):
        if found >= N_DECOY:
            break
        g = gen_base(10000 + s)
        sig = signature(g)
        for other in buckets.get(sig, []):
            if found >= N_DECOY:
                break
            if not isomorphic(g, other):
                worlds["decoy"].append(
                    (relabel(other, s, "x"), relabel(g, s + 3000, "y")))
                found += 1
        buckets.setdefault(sig, []).append(g)
    if found < N_DECOY:
        print(f"CANNOT_CHECK: only {found}/{N_DECOY} decoys found", file=sys.stderr)
        sys.exit(3)
    return worlds


def evaluate(worlds):
    out = {}
    for name in METRICS:
        iso_d = [dist(name, a, b) for a, b in worlds["iso"]]
        iso_zero = sum(1 for d in iso_d if d == 0.0) / len(iso_d)
        rhos = []
        for row in worlds["graded"]:
            ks = [k for k, _, _ in row]
            ds = [dist(name, a, b) for _, a, b in row]
            if REFUSED in ds:
                rhos.append(None)
            else:
                rhos.append(spearman([float(k) for k in ks], ds))
        valid = [r for r in rhos if r is not None]
        dec_d = [dist(name, a, b) for a, b in worlds["decoy"]]
        decoy_sep = sum(1 for d in dec_d if d != REFUSED and d > 0.0) / len(dec_d)
        empty_refused = dist(name, frozenset(), frozenset({("a", "b")})) == REFUSED
        out[name] = {
            "iso_zero_rate": iso_zero,
            "graded_spearman_mean_k1_4": (sum(valid) / len(valid)) if valid else None,
            "graded_spearman_n": len(valid),
            "decoy_sep_rate": decoy_sep,
            "empty_refused": empty_refused,
            "tracks_graded_ge_0p80": (sum(valid) / len(valid) >= 0.80) if valid else False,
            "tier_discriminates_ge_0p50": decoy_sep >= 0.50,
        }
    return out

# ---------------------------------------------------------------- self-test

def selftest():
    g1 = frozenset({("a", "b"), ("b", "c")})
    g2 = frozenset({("x", "y")})
    assert abs(m3_ged_exact(g1, g2) - 0.25) < 1e-12, "hand-computed GED failed"
    iso_a = relabel(g1, 7, "p")
    iso_b = relabel(g1, 8, "q")
    for name in ("M0_exact_signature_v1", "M1_signature_l1", "M2_wl3", "M3_ged_exact"):
        assert dist(name, iso_a, iso_b) == 0.0, f"{name} nonzero on iso pair"
    assert dist("M_refuse_all_planted_fail", iso_a, iso_b) == 1.0
    assert dist("M2_wl3", frozenset(), g1) == REFUSED, "empty world not refused"
    r = spearman([1, 2, 3, 4], [0.1, 0.2, 0.3, 0.4])
    assert abs(r - 1.0) < 1e-12, "spearman broken"
    assert spearman([1, 2, 3, 4], [1, 1, 1, 1]) == 0.0, "degenerate spearman convention"
    w1 = gen_base(3)
    w2 = gen_base(3)
    assert w1 == w2, "world generation nondeterministic"


def main():
    try:
        selftest()
    except AssertionError as exc:
        print(f"SELFTEST_FAIL: {exc}", file=sys.stderr)
        sys.exit(2)
    t0 = time.time()
    worlds = build_worlds()
    r1 = evaluate(worlds)
    r2 = evaluate(build_worlds())
    if json.dumps(r1, sort_keys=True) != json.dumps(r2, sort_keys=True):
        print("SELFTEST_FAIL: run not deterministic", file=sys.stderr)
        sys.exit(2)
    # the evaluator must reject the planted-fail candidate
    if r1["M_refuse_all_planted_fail"]["iso_zero_rate"] != 0.0:
        print("SELFTEST_FAIL: planted-fail candidate not caught", file=sys.stderr)
        sys.exit(2)
    result = {
        "worlds": {"iso_pairs": N_BASE, "graded_rows": N_BASE, "ks": list(KS),
                   "decoy_pairs": N_DECOY},
        "runtime_seconds": round(time.time() - t0, 2),
        "metrics": r1,
        "grants_scientific_authority": False,
    }
    print(json.dumps(result, indent=1, sort_keys=True))
    sys.exit(0)


if __name__ == "__main__":
    main()
