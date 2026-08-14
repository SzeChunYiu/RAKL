"""Frozen lexical retrieval routes over the Mathlib premise corpus.

Every route is purely lexical/symbolic — constant-symbol overlap, IDF, name
tokens. No pretrained embedder is used anywhere in the retrieval path, which is
what keeps model pretraining contamination out of the outcome: nothing in this
pipeline has ever seen the held-out proofs.

Routes are *evidence families*, not reorderings of one ranking. Each keys on a
different feature of the goal, so the fused ranking genuinely changes as routes
are added or withheld. That is what makes the two arms differ at the solve
interface rather than one holding a prefix of the other.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class Premise:
    name: str
    consts: frozenset[str]


def _name_tokens(name: str) -> frozenset[str]:
    parts: list[str] = []
    for chunk in name.split("."):
        parts.extend(re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+|\d+", chunk))
    return frozenset(p.lower() for p in parts if len(p) > 1)


class PremiseIndex:
    """Inverted index over constants occurring in premise types."""

    def __init__(self, premises: list[Premise]) -> None:
        self.premises = premises
        self.by_name = {p.name: p for p in premises}
        self.postings: dict[str, list[int]] = {}
        for i, p in enumerate(premises):
            for c in p.consts:
                self.postings.setdefault(c, []).append(i)
        n = max(len(premises), 1)
        self.idf = {
            c: math.log(1.0 + n / (1.0 + len(ids))) for c, ids in self.postings.items()
        }
        self.tokens = [_name_tokens(p.name) for p in premises]

    def _candidates(self, consts: frozenset[str], cap: int = 60000) -> list[int]:
        seen: set[int] = set()
        for c in sorted(consts, key=lambda c: len(self.postings.get(c, ()))):
            for i in self.postings.get(c, ()):
                seen.add(i)
                if len(seen) >= cap:
                    return list(seen)
        return list(seen)

    # ---- routes -------------------------------------------------------
    # Each returns a ranked list of premise names, best first.

    def route_jaccard(self, goal: frozenset[str], k: int) -> list[str]:
        scored = []
        for i in self._candidates(goal):
            c = self.premises[i].consts
            inter = len(c & goal)
            if inter:
                scored.append((inter / len(c | goal), -len(c), self.premises[i].name))
        scored.sort(key=lambda t: (-t[0], t[1], t[2]))
        return [name for _, _, name in scored[:k]]

    def route_idf(self, goal: frozenset[str], k: int) -> list[str]:
        scored = []
        for i in self._candidates(goal):
            shared = self.premises[i].consts & goal
            if shared:
                scored.append((sum(self.idf.get(c, 0.0) for c in shared), self.premises[i].name))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [name for _, name in scored[:k]]

    def route_rarest(self, goal: frozenset[str], k: int) -> list[str]:
        if not goal:
            return []
        rare = sorted(goal, key=lambda c: (len(self.postings.get(c, ())), c))[:3]
        rare_set = frozenset(rare)
        scored = []
        for i in self._candidates(rare_set):
            shared = self.premises[i].consts & rare_set
            if shared:
                scored.append((-len(shared), len(self.premises[i].consts), self.premises[i].name))
        scored.sort()
        return [name for _, _, name in scored[:k]]

    def route_containment(self, goal: frozenset[str], k: int) -> list[str]:
        scored = []
        for i in self._candidates(goal):
            c = self.premises[i].consts
            if c and c <= goal:
                scored.append((-len(c), self.premises[i].name))
        scored.sort()
        return [name for _, name in scored[:k]]

    def route_name_token(self, goal: frozenset[str], k: int) -> list[str]:
        goal_tokens: set[str] = set()
        for c in goal:
            goal_tokens |= _name_tokens(c)
        if not goal_tokens:
            return []
        scored = []
        for i in self._candidates(goal):
            overlap = len(self.tokens[i] & goal_tokens)
            if overlap:
                scored.append((-overlap, len(self.premises[i].consts), self.premises[i].name))
        scored.sort()
        return [name for _, _, name in scored[:k]]

    def route_pair(self, goal: frozenset[str], k: int) -> list[str]:
        scored = []
        for i in self._candidates(goal):
            shared = self.premises[i].consts & goal
            if len(shared) >= 2:
                scored.append(
                    (-sum(self.idf.get(c, 0.0) for c in shared), self.premises[i].name)
                )
        scored.sort()
        return [name for _, name in scored[:k]]

    def route_two_hop(self, goal: frozenset[str], k: int) -> list[str]:
        seeds = self.route_idf(goal, 12)
        expanded: set[str] = set()
        for s in seeds:
            expanded |= self.by_name[s].consts
        expanded -= goal
        if not expanded:
            return []
        top = frozenset(sorted(expanded, key=lambda c: -self.idf.get(c, 0.0))[:8])
        scored = []
        for i in self._candidates(top):
            shared = self.premises[i].consts & top
            if shared and (self.premises[i].consts & goal):
                scored.append(
                    (-sum(self.idf.get(c, 0.0) for c in shared), self.premises[i].name)
                )
        scored.sort()
        return [name for _, name in scored[:k]]


#: Frozen route order. Changing this changes the mechanism under test.
ROUTES = (
    "jaccard",
    "idf",
    "rarest",
    "containment",
    "name_token",
    "pair",
    "two_hop",
)


def run_route(index: PremiseIndex, route: str, goal: frozenset[str], k: int) -> list[str]:
    return getattr(index, f"route_{route}")(goal, k)


def rrf_fuse(rankings: list[list[str]], m: int, *, k0: int = 60) -> list[str]:
    """Reciprocal-rank fusion, then truncate to exactly ``m`` premises.

    Truncation is what keeps the solve interface budget-identical across arms:
    both arms hand the tactic the same number of premises, so they differ in
    *which* premises they chose, never in how many.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, name in enumerate(ranking):
            scores[name] = scores.get(name, 0.0) + 1.0 / (k0 + rank + 1)
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in ordered[:m]]
