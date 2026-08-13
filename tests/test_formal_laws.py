"""Property tests for the algebraic laws closing the hostile-review formal gaps.

Gap 1: path quotient must be an equivalence relation (total on all histories) AND a
congruence under composition (trace-monoid laws) -- otherwise substituting
"equivalent" subpaths inside a larger proof is unsound.
Gap 2: the intrinsic cost geometry must satisfy the Lawvere quasimetric laws, and
the budget-indexed "distance" must be exhibited as violating the triangle
inequality (which is why budget lives in sublevel sets, not the metric).
"""
from __future__ import annotations

import itertools
import random

from rakl.cost_geometry import (
    OperatorCostGeometry,
    budget_indexed_triangle_counterexample,
)
from rakl.path_congruence import TraceMonoid, congruence_certificate


ALPHA = ["a", "b", "c", "d"]
INDEP = [("a", "b"), ("c", "d")]  # a,b commute; c,d commute; others dependent


def _random_words(rng: random.Random, n: int, max_len: int = 6) -> list[list[str]]:
    return [[rng.choice(ALPHA) for _ in range(rng.randint(0, max_len))] for _ in range(n)]


def test_trace_equivalence_is_total_and_reflexive_everywhere():
    """(E) reflexivity must hold for EVERY word -- including ones that would have
    violated 'declared dependencies' (the empirically observed domain defect)."""
    m = TraceMonoid.build(ALPHA, INDEP)
    rng = random.Random(461)
    for w in _random_words(rng, 200):
        assert m.equivalent(w, w)


def test_trace_equivalence_laws_on_sample():
    m = TraceMonoid.build(ALPHA, INDEP)
    rng = random.Random(462)
    words = _random_words(rng, 40, max_len=4)
    laws = m.check_equivalence_laws(words)
    assert laws == {"reflexive": True, "symmetric": True, "transitive": True}


def test_adjacent_independent_swap_is_equivalent_and_dependent_swap_is_not():
    m = TraceMonoid.build(ALPHA, INDEP)
    assert m.equivalent(["a", "b"], ["b", "a"])  # independent pair commutes
    assert not m.equivalent(["a", "c"], ["c", "a"])  # dependent pair does not


def test_congruence_under_composition():
    """(C): u ~ v implies p.u.q ~ p.v.q for random contexts -- substitution safety."""
    m = TraceMonoid.build(ALPHA, INDEP)
    rng = random.Random(463)
    contexts = [(rng_word, rng_word2) for rng_word, rng_word2 in zip(_random_words(rng, 25, 4), _random_words(rng, 25, 4))]
    # equivalent pair: any interleaving of independent letters
    u, v = ["a", "b", "c"], ["b", "a", "c"]
    assert m.equivalent(u, v)
    assert m.check_congruence(u, v, contexts)


def test_congruence_certificate_passes():
    rng = random.Random(464)
    cert = congruence_certificate(
        ALPHA,
        INDEP,
        sample_words=_random_words(rng, 25, 4),
        sample_contexts=[(w1, w2) for w1, w2 in zip(_random_words(rng, 12, 3), _random_words(rng, 12, 3))],
    )
    assert cert["equivalence_laws"] == {"reflexive": True, "symmetric": True, "transitive": True}
    assert cert["congruence_under_composition"] is True
    assert cert["grants_proof_authority"] is False


def test_foata_normal_form_counts_classes_correctly():
    """6 permutations of {a,b,c}; only a,b independent -> exactly 4 trace classes:
    [ab]c ~ [ba]c, a-c-b, b-c-a, c[ab] ~ c[ba] (c blocks commutation across it)."""
    m = TraceMonoid.build(ALPHA, INDEP)
    words = list(itertools.permutations(["a", "b", "c"]))
    classes = {m.foata_normal_form(w) for w in words}
    assert len(classes) == 4
    assert m.foata_normal_form(["a", "b", "c"]) == m.foata_normal_form(["b", "a", "c"])
    assert m.foata_normal_form(["c", "a", "b"]) == m.foata_normal_form(["c", "b", "a"])


def test_intrinsic_geometry_satisfies_lawvere_laws_on_random_graphs():
    rng = random.Random(465)
    for _ in range(20):
        n = rng.randint(3, 7)
        nodes = [f"n{i}" for i in range(n)]
        edges = []
        for a in nodes:
            for b in nodes:
                if a != b and rng.random() < 0.4:
                    edges.append((a, b, round(rng.uniform(0.0, 5.0), 3)))
        if not edges:
            continue
        cert = OperatorCostGeometry(edges).certify_quasimetric()
        assert cert.identity_ok and cert.triangle_ok, "inf-plus construction must be a Lawvere metric"


def test_budget_indexed_distance_violates_triangle_inequality():
    """The registered counterexample: d_B fails composition; intrinsic d does not."""
    ce = budget_indexed_triangle_counterexample()
    assert ce["triangle_violated"] is True
    assert ce["intrinsic_geometry_is_lawvere_metric"] is True
    assert ce["grants_scientific_authority"] is False


def test_budget_lives_in_sublevel_sets():
    geo = OperatorCostGeometry([("x", "y", 3.0), ("y", "z", 3.0), ("x", "z", 7.0)])
    feas = geo.budget_feasible_set("z", budget=5.0)
    assert "y" in feas and "z" in feas and "x" not in feas  # V(x)=6 > 5
