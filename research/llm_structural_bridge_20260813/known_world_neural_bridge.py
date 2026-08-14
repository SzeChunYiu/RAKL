#!/usr/bin/env python3
"""Development-only known world for the RAKL Neural Structural Bridge.

This is NOT an LLM experiment and grants no scientific authority.  It is a cheap
mechanism screen designed to answer three questions before expensive model work:

1. Can one learned representation change its equivalence geometry with the QoI?
2. Can the same representation support fresh-domain structural retrieval while
   rejecting same-surface structural/boundary decoys?
3. Does explicit RAKL structural supervision add anything beyond a strong generic
   QoI-conditioned metric learner?

The honest terminal for the frozen five-seed run is:

    FEASIBILITY_SUPPORTED_RAKL_SPECIFIC_RESIDUAL_NOT_ESTABLISHED

because the generic conditional-metric parent already explains most of the gain.

Dependencies are intentionally research-local: PyTorch only.  The base RAKL package
does not add torch as a required runtime dependency.
"""
from __future__ import annotations

import json
import random
import statistics
import time

import torch
import torch.nn as nn
import torch.nn.functional as F


torch.set_num_threads(4)


class World:
    """Exact synthetic factors; domain/surface nuisance dominates raw cosine."""

    def __init__(self, seed: int = 0, pK: int = 8, cK: int = 6, dK: int = 6, nK: int = 32, dim_each: int = 10):
        g = torch.Generator().manual_seed(seed)
        self.pK, self.cK, self.dK, self.nK = pK, cK, dK, nK
        self.ep = F.normalize(torch.randn(pK, dim_each, generator=g), dim=-1)
        self.ec = F.normalize(torch.randn(cK, dim_each, generator=g), dim=-1)
        self.eb = F.normalize(torch.randn(2, dim_each, generator=g), dim=-1)
        self.ed = F.normalize(torch.randn(dK, dim_each, generator=g), dim=-1)
        self.en = F.normalize(torch.randn(nK, dim_each, generator=g), dim=-1)
        self.dim = dim_each * 5

    def sample(self, rng: random.Random, *, p=None, c=None, b=None, d=None, n=None):
        p = rng.randrange(self.pK) if p is None else p
        c = rng.randrange(self.cK) if c is None else c
        b = rng.randrange(2) if b is None else b
        d = rng.randrange(self.dK) if d is None else d
        n = rng.randrange(self.nK) if n is None else n
        x = torch.cat(
            [
                1.05 * self.ep[p],
                1.05 * self.ec[c],
                1.15 * self.eb[b],
                2.30 * self.ed[d],
                2.00 * self.en[n],
            ]
        )
        x = x + 0.04 * torch.randn_like(x)
        return x, (p, c, b, d, n)


def make_triplet(world: World, rng: random.Random, q: int, domains):
    """Positive preserves QoI-relevant structure+boundary; negative is surface-near decoy.

    q=0: quotient key=(principle,boundary), composition is nuisance.
    q=1: quotient key=(composition,boundary), principle is nuisance.
    """
    da = rng.choice(domains)
    dp = rng.choice([d for d in domains if d != da])
    nuisance = rng.randrange(world.nK)
    p, c, b = rng.randrange(world.pK), rng.randrange(world.cK), rng.randrange(2)
    xa, ma = world.sample(rng, p=p, c=c, b=b, d=da, n=nuisance)

    if q == 0:
        pp, cp, bp = p, (c + rng.randrange(1, world.cK)) % world.cK, b
        if rng.random() < 0.5:
            pn, bn = (p + rng.randrange(1, world.pK)) % world.pK, b
        else:
            pn, bn = p, 1 - b
        cn = c
    else:
        cp, pp, bp = c, (p + rng.randrange(1, world.pK)) % world.pK, b
        if rng.random() < 0.5:
            cn, bn = (c + rng.randrange(1, world.cK)) % world.cK, b
        else:
            cn, bn = c, 1 - b
        pn = p

    xp, mp = world.sample(rng, p=pp, c=cp, b=bp, d=dp, n=rng.randrange(world.nK))
    xn, mn = world.sample(rng, p=pn, c=cn, b=bn, d=da, n=nuisance)
    return xa, xp, xn, q, ma, mp, mn


def batch(world: World, rng: random.Random, n: int, domains):
    rows = [make_triplet(world, rng, rng.randrange(2), domains) for _ in range(n)]
    return (
        torch.stack([r[0] for r in rows]),
        torch.stack([r[1] for r in rows]),
        torch.stack([r[2] for r in rows]),
        torch.tensor([r[3] for r in rows]),
        torch.tensor([r[4][0] for r in rows]),
        torch.tensor([r[4][1] for r in rows]),
        torch.tensor([r[4][2] for r in rows]),
    )


class QEncoder(nn.Module):
    """QoI-conditioned representation; optional explicit structural heads."""

    def __init__(self, dim: int, pK: int = 8, cK: int = 6, hidden: int = 56, out: int = 20):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(dim + 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
        )
        self.e0 = nn.Linear(hidden, out)
        self.e1 = nn.Linear(hidden, out)
        self.hp = nn.Linear(hidden, pK)
        self.hc = nn.Linear(hidden, cK)
        self.hb = nn.Linear(hidden, 2)

    def forward(self, x, q, heads: bool = False):
        h = self.trunk(torch.cat([x, F.one_hot(q.long(), 2).float()], -1))
        z = torch.where((q == 0).unsqueeze(-1), self.e0(h), self.e1(h))
        z = F.normalize(z, dim=-1)
        if heads:
            return z, self.hp(h), self.hc(h), self.hb(h)
        return z


class UEncoder(nn.Module):
    """Strong structural but QoI-unconditioned comparator."""

    def __init__(self, dim: int, pK: int = 8, cK: int = 6, hidden: int = 56, out: int = 20):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
        )
        self.e = nn.Linear(hidden, out)
        self.hp = nn.Linear(hidden, pK)
        self.hc = nn.Linear(hidden, cK)
        self.hb = nn.Linear(hidden, 2)

    def forward(self, x, q, heads: bool = False):
        del q
        h = self.trunk(x)
        z = F.normalize(self.e(h), dim=-1)
        if heads:
            return z, self.hp(h), self.hc(h), self.hb(h)
        return z


def triplet_loss(za, zp, zn):
    return F.relu(0.45 - (za * zp).sum(-1) + (za * zn).sum(-1)).mean() + 0.10 * (
        1 - (za * zp).sum(-1)
    ).mean()


def train(seed: int, kind: str, steps: int = 150):
    torch.manual_seed(seed)
    random.seed(seed)
    world = World(10000 + seed)
    model = UEncoder(world.dim, world.pK, world.cK) if kind == "unconditioned_structural" else QEncoder(world.dim, world.pK, world.cK)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    rng = random.Random(20000 + seed)

    for _ in range(steps):
        a, p, n, q, pa, ca, ba = batch(world, rng, 112, [0, 1, 2])
        if kind in ("explicit_rakl", "unconditioned_structural"):
            za, lp, lc, lb = model(a, q, heads=True)
            zp, zn = model(p, q), model(n, q)
            loss = triplet_loss(za, zp, zn)
            if kind == "explicit_rakl":
                # Explicitly expose the registered boundary and only the QoI-relevant
                # structural coordinate to the auxiliary objective.
                aux = F.cross_entropy(lb, ba)
                m0, m1 = q == 0, q == 1
                if m0.any():
                    aux = aux + F.cross_entropy(lp[m0], pa[m0])
                if m1.any():
                    aux = aux + F.cross_entropy(lc[m1], ca[m1])
            else:
                aux = F.cross_entropy(lb, ba) + F.cross_entropy(lp, pa) + F.cross_entropy(lc, ca)
            loss = loss + aux
        else:
            # Strong parent: exactly the QoI-conditioned triplet objective, no explicit
            # RAKL structural auxiliary labels.
            za, zp, zn = model(a, q), model(p, q), model(n, q)
            loss = triplet_loss(za, zp, zn)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return world, model


def rawz(x, q):
    del q
    return F.normalize(x, dim=-1)


def key(meta, q):
    p, c, b, _d, _n = meta
    return (p, b) if q == 0 else (c, b)


def eval_triplet(model, world: World, seed: int, n: int = 400):
    rng = random.Random(seed)
    a, p, neg, q, *_ = batch(world, rng, n, [3, 4, 5])
    f = rawz if model is None else model
    with torch.no_grad():
        za, zp, zn = f(a, q), f(p, q), f(neg, q)
        sp, sn = (za * zp).sum(-1), (za * zn).sum(-1)
    return float((sp > sn).float().mean())


def examples(world: World, rng: random.Random, n: int, domains):
    xs, metas = [], []
    for _ in range(n):
        x, meta = world.sample(rng, d=rng.choice(domains))
        xs.append(x)
        metas.append(meta)
    return torch.stack(xs), metas


def eval_retrieval(model, world: World, seed: int, n_mem: int = 400, n_query: int = 180):
    rng = random.Random(seed)
    xm, mm = examples(world, rng, n_mem, [0, 1, 2])
    xq, mq = examples(world, rng, n_query, [3, 4, 5])
    f = rawz if model is None else model
    scores = []
    for qv in (0, 1):
        qm = torch.full((n_mem,), qv)
        qq = torch.full((n_query,), qv)
        with torch.no_grad():
            idx = (f(xq, qq) @ f(xm, qm).T).argmax(-1).tolist()
        scores.append(sum(key(mq[i], qv) == key(mm[j], qv) for i, j in enumerate(idx)) / n_query)
    return sum(scores) / 2


def eval_qoi_flip(model, world: World, seed: int, n: int = 350):
    rng = random.Random(seed)
    xs, ys = [], []
    for _ in range(n):
        p = rng.randrange(world.pK)
        c = rng.randrange(world.cK)
        c2 = (c + rng.randrange(1, world.cK)) % world.cK
        b = rng.randrange(2)
        x, _ = world.sample(rng, p=p, c=c, b=b, d=rng.randrange(3))
        y, _ = world.sample(rng, p=p, c=c2, b=b, d=rng.randrange(3, 6))
        xs.append(x)
        ys.append(y)
    x, y = torch.stack(xs), torch.stack(ys)
    q0, q1 = torch.zeros(n, dtype=torch.long), torch.ones(n, dtype=torch.long)
    f = rawz if model is None else model
    with torch.no_grad():
        s0 = (f(x, q0) * f(y, q0)).sum(-1)
        s1 = (f(x, q1) * f(y, q1)).sum(-1)
    return float((s0 > s1).float().mean()), float((s0 - s1).mean())


def eval_boundary(model, world: World, seed: int, n: int = 500):
    rng = random.Random(seed)
    anchors, positives, negatives, qs = [], [], [], []
    for _ in range(n):
        q = rng.randrange(2)
        p, c, b = rng.randrange(world.pK), rng.randrange(world.cK), rng.randrange(2)
        d1, d2, nuisance = rng.randrange(3, 6), rng.randrange(3, 6), rng.randrange(world.nK)
        a, _ = world.sample(rng, p=p, c=c, b=b, d=d1, n=nuisance)
        if q == 0:
            pos, _ = world.sample(rng, p=p, c=(c + 1) % world.cK, b=b, d=d2)
        else:
            pos, _ = world.sample(rng, p=(p + 1) % world.pK, c=c, b=b, d=d2)
        neg, _ = world.sample(rng, p=p, c=c, b=1 - b, d=d1, n=nuisance)
        anchors.append(a)
        positives.append(pos)
        negatives.append(neg)
        qs.append(q)
    a, p, neg, q = torch.stack(anchors), torch.stack(positives), torch.stack(negatives), torch.tensor(qs)
    f = rawz if model is None else model
    with torch.no_grad():
        sp = (f(a, q) * f(p, q)).sum(-1)
        sn = (f(a, q) * f(neg, q)).sum(-1)
    return float((sp > sn).float().mean()), float((sp - sn).mean())


def run_one(seed: int):
    raw_world = World(10000 + seed)
    arms = {"raw": (raw_world, None)}
    for kind in ("unconditioned_structural", "conditional_metric", "explicit_rakl"):
        arms[kind] = train(seed, kind)

    result = {"seed": seed, "arms": {}}
    for name, (world, model) in arms.items():
        flip, qgap = eval_qoi_flip(model, world, 50000 + seed)
        bacc, bgap = eval_boundary(model, world, 60000 + seed)
        result["arms"][name] = {
            "triplet_acc": eval_triplet(model, world, 30000 + seed),
            "retrieval_acc": eval_retrieval(model, world, 40000 + seed),
            "qoi_flip_success": flip,
            "qoi_gap": qgap,
            "boundary_acc": bacc,
            "boundary_gap": bgap,
        }
    return result


def summarize(rows):
    out = {}
    for arm in rows[0]["arms"]:
        out[arm] = {}
        for metric in rows[0]["arms"][arm]:
            values = [r["arms"][arm][metric] for r in rows]
            out[arm][metric] = {
                "mean": statistics.mean(values),
                "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values),
                "values": values,
            }
    return out


def main() -> int:
    started = time.time()
    rows = [run_one(seed) for seed in range(5)]
    result = {
        "schema": "rakl.neural_bridge.known_world.development.v1",
        "status": "FEASIBILITY_SUPPORTED_RAKL_SPECIFIC_RESIDUAL_NOT_ESTABLISHED",
        "seeds": 5,
        "steps": 150,
        "rows": rows,
        "summary": summarize(rows),
        "elapsed_seconds": time.time() - started,
        "grants_scientific_authority": False,
        "claim_boundary": [
            "Synthetic development known-world only; not LLM or natural-domain evidence.",
            "QoI-conditioned metric learning is a strong parent and explains most of the learned-geometry gain.",
            "Explicit RAKL structural auxiliary supervision is not established as a distinct causal advantage by this experiment.",
            "The result supports feasibility of a QoI-conditioned embedding reused for fresh-domain retrieval and boundary-aware matching.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
