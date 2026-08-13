"""Cost geometry with explicit algebraic laws: Lawvere quasimetric + budget sublevels.

Closes a formal gap found in hostile mathematical review: earlier statements indexed
the routing "distance" by a resource budget, d_{Omega,R,B}. A budget-constrained
cost-to-go is NOT a metric or quasimetric: the triangle inequality fails because the
budget remaining at an intermediate state depends on how it was reached (see
``budget_indexed_triangle_counterexample`` for a concrete 3-state violation).

The mathematically safe factorization, in the weakest adequate structure
(a Lawvere metric space, i.e. a category enriched over ([0, inf], +, >=)):

  1. INTRINSIC geometry  d_{Omega,R}(x, y) = infimum over operator paths x -> y of
     summed nonnegative step costs. By the inf-plus construction this satisfies
       d(x, x) = 0            (identity)
       d(x, z) <= d(x, y) + d(y, z)   (triangle inequality / composition law)
     Asymmetry and the value +inf are allowed (reachability is directed; +inf means
     "no path under the current operator basis/chart", never non-existence).
  2. BUDGET as a sublevel set, not a metric index:
       Feasible_B = { x : V(x) <= B },  V(x) = d(x, target).
  3. Policy/value functions live ON TOP of (1)+(2); they may be learned and wrong;
     they carry no authority.

Nothing here grants scientific, proof, or routing authority.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from math import inf, isfinite
from typing import Dict, Iterable, Mapping, Tuple

Edge = Tuple[str, str, float]  # (source, target, nonnegative step cost)


@dataclass(frozen=True)
class QuasimetricCertificate:
    identity_ok: bool
    triangle_ok: bool
    asymmetric_pairs: int
    infinite_pairs: int

    @property
    def is_lawvere_metric(self) -> bool:
        return self.identity_ok and self.triangle_ok

    @property
    def grants_scientific_authority(self) -> bool:
        return False


class OperatorCostGeometry:
    """Intrinsic directed cost geometry over an operator graph (inf-plus / Dijkstra)."""

    def __init__(self, edges: Iterable[Edge]):
        self._adj: Dict[str, list[tuple[str, float]]] = {}
        nodes = set()
        for src, dst, cost in edges:
            if not isfinite(cost) or cost < 0:
                raise ValueError(f"step cost must be finite and nonnegative: {src}->{dst}={cost}")
            self._adj.setdefault(src, []).append((dst, cost))
            nodes.add(src)
            nodes.add(dst)
        self.nodes = frozenset(nodes)

    def d(self, x: str, y: str) -> float:
        """d_{Omega,R}(x,y): infimum of summed costs over operator paths (inf = +inf)."""
        if x == y:
            return 0.0
        dist = {x: 0.0}
        heap = [(0.0, x)]
        while heap:
            dx, u = heapq.heappop(heap)
            if u == y:
                return dx
            if dx > dist.get(u, inf):
                continue
            for v, c in self._adj.get(u, ()):
                nd = dx + c
                if nd < dist.get(v, inf):
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return dist.get(y, inf)

    def value_function(self, target: str) -> Mapping[str, float]:
        return {n: self.d(n, target) for n in self.nodes}

    def budget_feasible_set(self, target: str, budget: float) -> frozenset[str]:
        """Feasible_B = sublevel set of the value function. Budget is NOT in the metric."""
        V = self.value_function(target)
        return frozenset(n for n, v in V.items() if v <= budget)

    def certify_quasimetric(self) -> QuasimetricCertificate:
        """Executable check of the Lawvere laws over all node triples."""
        ns = sorted(self.nodes)
        D = {(a, b): self.d(a, b) for a in ns for b in ns}
        identity_ok = all(D[(a, a)] == 0.0 for a in ns)
        triangle_ok = all(
            D[(a, c)] <= D[(a, b)] + D[(b, c)] + 1e-12 for a in ns for b in ns for c in ns
        )
        asym = sum(1 for a in ns for b in ns if a < b and D[(a, b)] != D[(b, a)])
        infs = sum(1 for a in ns for b in ns if D[(a, b)] == inf)
        return QuasimetricCertificate(identity_ok, triangle_ok, asym, infs)


def budget_indexed_triangle_counterexample() -> dict:
    """Concrete proof that budget-in-the-metric breaks the triangle inequality.

    World: x --(3)--> y --(3)--> z, and a direct edge x --(7)--> z.
    Define the budget-indexed quantity  d_B(a, b) = (cost of the cheapest a->b path
    whose TOTAL cost is <= B), else +inf, with B = 5 at every invocation (the naive
    reading of "distance under budget B").

      d_5(x, y) = 3   (affordable)
      d_5(y, z) = 3   (affordable)
      d_5(x, z) = +inf  (both routes cost 6 or 7 > 5)

    Triangle inequality demands d_5(x,z) <= d_5(x,y) + d_5(y,z) = 6 -- violated
    (inf > 6). The composite is affordable step-by-step but not under the global
    budget, because remaining budget at y depends on the path taken: the quantity is
    path-history-dependent and therefore not a function of endpoints. Hence budget
    must live in sublevel sets of the value function, not in the metric.
    """
    geo = OperatorCostGeometry([("x", "y", 3.0), ("y", "z", 3.0), ("x", "z", 7.0)])
    B = 5.0

    def d_budget(a: str, b: str) -> float:
        cost = geo.d(a, b)
        return cost if cost <= B else inf

    lhs = d_budget("x", "z")
    rhs = d_budget("x", "y") + d_budget("y", "z")
    intrinsic = geo.certify_quasimetric()
    return {
        "budget": B,
        "d_B(x,z)": lhs,
        "d_B(x,y)+d_B(y,z)": rhs,
        "triangle_violated": lhs > rhs,
        "intrinsic_geometry_is_lawvere_metric": intrinsic.is_lawvere_metric,
        "correct_object": "Feasible_B = {v : V(v) <= B} sublevel set; metric stays intrinsic",
        "grants_scientific_authority": False,
    }
