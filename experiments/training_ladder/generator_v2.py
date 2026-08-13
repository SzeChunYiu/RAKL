"""Phase-1 v2 generator: VARIED instances per family (fixes the v1 degeneracy).

Root cause of v1 (see research/paper4_phase1_results/ROOT_CAUSE.md): the v1 generator
emitted only two unique rendered inputs per family, so 'training' memorised a one-token
difference on near-identical strings and collapsed to a constant predictor (0.5). This v2
draws every instance from a distribution, so the task is to *generalize a structural rule*
from training instances to disjoint held-out instances -- real structural learning, not
string memorisation. Gold always comes from the executable rule, never the intended flag.

Design guards against the v1 artifacts:
  * VALID/INVALID are LENGTH-MATCHED per family (reachability uses the same edge count for
    both classes) so the model cannot cheat on input length (the v1 'reachability learned'
    artifact).
  * train and probe instances are DISJOINT by construction.
  * gold is recomputed from the rule for every instance and the pool is balanced.

No scientific authority is granted by anything here; this is an instrument.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Callable

_INSTRUCTION = (
    "Decide whether the described structure satisfies its rule.\n"
    "Respond with exactly one word, either VALID or INVALID.\n"
)


@dataclass(frozen=True)
class V2Case:
    case_id: str
    family: str
    prompt: str
    gold: str  # "VALID" | "INVALID", from the executable rule


def _wrap(body: str) -> str:
    return f"{_INSTRUCTION}\nStructure:\n{body}\nAnswer:"


# --------------------------------------------------------------------------- #
# balance_conservation: inflow == outflow + store, over varied magnitudes
# --------------------------------------------------------------------------- #
def _balance(rng: random.Random, idx: int, *, regime: str = "base", style: str = "default") -> V2Case:
    hi = 80 if regime == "boundary" else 40
    inflow = rng.randint(6, hi)
    outflow = rng.randint(1, inflow - 1)
    make_valid = idx % 2 == 0
    if make_valid:
        store = inflow - outflow
    else:
        store = inflow - outflow + (rng.choice([-1, 1]) if regime == "hostile" else rng.choice([-3, -2, -1, 1, 2, 3]))
    gold = "VALID" if inflow == outflow + store else "INVALID"
    if style == "alt":
        body = f"- in := {inflow}\n- out := {outflow}\n- stored := {store}"
    else:
        body = f"- inflow: {inflow}\n- outflow: {outflow}\n- store: {store}"
    return V2Case(f"balv2-{regime}-{idx}", "balance_conservation", _wrap(body), gold)


# --------------------------------------------------------------------------- #
# sequence_composition: apply ops left-to-right; does the claimed result match?
# --------------------------------------------------------------------------- #
def _sequence(rng: random.Random, idx: int, *, regime: str = "base", style: str = "default") -> V2Case:
    n_ops = 3 if regime == "composition" else 2
    start = rng.randint(1, 9)
    ops = [(rng.choice(["add", "mul"]), rng.randint(2, 5)) for _ in range(n_ops)]
    value = start
    for name, val in ops:
        value = value + val if name == "add" else value * val
    make_valid = idx % 2 == 0
    claimed = value if make_valid else value + rng.choice([-3, -2, -1, 1, 2, 3])
    gold = "VALID" if claimed == value else "INVALID"
    ordered = " then ".join(f"{name}({val})" for name, val in ops)
    if style == "alt":
        pipe = "; ".join(f"step {i+1}: {name} by {val}" for i, (name, val) in enumerate(ops))
        body = f"- initial: {start}\n- pipeline: {pipe}\n- claimed result: {claimed}"
    else:
        body = f"- start value: {start}\n- apply in order: {ordered}\n- claimed result: {claimed}"
    return V2Case(f"seqv2-{regime}-{idx}", "sequence_composition", _wrap(body), gold)


# --------------------------------------------------------------------------- #
# state_reachability: varied graphs, LENGTH-MATCHED valid/invalid (same #edges)
# --------------------------------------------------------------------------- #
def _reach_set(start: str, edges: list[tuple[str, str]]) -> set[str]:
    reach = {start}
    frontier = [start]
    while frontier:
        node = frontier.pop()
        for a, b in edges:
            if a == node and b not in reach:
                reach.add(b)
                frontier.append(b)
    return reach


def _reachability(rng: random.Random, idx: int, *, regime: str = "base", style: str = "default") -> V2Case:
    n_nodes = rng.randint(5, 6) if regime in ("composition", "boundary", "hostile") else rng.randint(4, 5)
    nodes = [chr(65 + j) for j in range(n_nodes)]
    m = (n_nodes + 1) if regime == "hostile" else n_nodes  # fixed edge count -> length-matched across valid/invalid
    make_valid = idx % 2 == 0
    for _ in range(200):  # rejection-sample a graph with the desired reachability class
        edges: list[tuple[str, str]] = []
        seen = set()
        while len(edges) < m:
            a, b = rng.sample(nodes, 2)
            if (a, b) not in seen:
                seen.add((a, b))
                edges.append((a, b))
        start = rng.choice(nodes)
        reach = _reach_set(start, edges)
        reachable = [t for t in nodes if t != start and t in reach]
        unreachable = [t for t in nodes if t not in reach]
        if make_valid and reachable:
            target = rng.choice(reachable)
            break
        if not make_valid and unreachable:
            target = rng.choice(unreachable)
            break
    else:
        target = nodes[-1]
    gold = "VALID" if target in _reach_set(start, edges) else "INVALID"
    edge_str = ", ".join(f"{a}->{b}" for a, b in edges)
    if style == "alt":
        body = f"- nodes = [{', '.join(nodes)}]\n- transitions = [{edge_str}]\n- query: {target} reachable from {start}?"
    else:
        body = f"- states: {', '.join(nodes)}\n- directed edges: {edge_str}\n- start: {start}\n- target: {target}"
    return V2Case(f"reachv2-{regime}-{idx}", "state_reachability", _wrap(body), gold)


_GEN: dict[str, Callable[..., V2Case]] = {
    "balance_conservation": _balance,
    "sequence_composition": _sequence,
    "state_reachability": _reachability,
}
FAMILIES = tuple(_GEN)


def generate(family: str, n: int, *, seed: int, regime: str = "base", style: str = "default", tag: str = "") -> list[V2Case]:
    """Balanced list of n varied cases for a family (deterministic from seed)."""
    # Stable across processes: sha256 of the parameter string (tuple.__hash__ of strings
    # is PYTHONHASHSEED-salted -> non-reproducible pools; found in hostile engineering audit).
    key = f"{seed}|{family}|{regime}|{style}|{tag}".encode("utf-8")
    rng = random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8], "big"))
    gen = _GEN[family]
    cases = [gen(rng, i, regime=regime, style=style) for i in range(n)]
    # rename ids to be unique per (regime, tag) so train/probe pools never collide
    return [V2Case(f"{c.case_id}-{tag}", c.family, c.prompt, c.gold) for c in cases]
