"""Tests for AND-composition over the support hypergraph.

The load-bearing test is the real-data one: the dependency graph of
``formal/RaklFormal.lean`` — every edge kernel-checked — is parsed into
hyperedges and a real theorem is re-derived from the axiom-free base by
traversal alone. No reasoning engine in the loop. That is the operator's
"solving is mechanical" claim demonstrated on the repository's own mathematics.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rakl.derivation import (
    DerivationOutcome,
    HyperEdge,
    derive,
)
from rakl.support_solver import Obstruction

REPO = Path(__file__).resolve().parents[1]


def E(edge_id, premises, conclusion, *, cost=1.0, licensed_at=0):
    return HyperEdge(edge_id, frozenset(premises), conclusion, cost, licensed_at)


# --- basic mechanics ---------------------------------------------------------------


def test_chain_derivation():
    report = derive([E("e1", {"a"}, "b"), E("e2", {"b"}, "c")], {"a"}, "c")
    assert report.outcome is DerivationOutcome.DERIVED
    assert [e.edge_id for e in report.dag.fired] == ["e1", "e2"]
    assert report.dag.cost == 2.0


def test_and_composition_needs_every_premise():
    """The case an OR-route solver cannot express: c requires a AND b."""
    edges = [E("join", {"a", "b"}, "c")]
    partial = derive(edges, {"a"}, "c")
    assert partial.outcome is DerivationOutcome.UNDERIVABLE_IN_PRINCIPLE
    assert "b" in partial.missing

    full = derive(edges, {"a", "b"}, "c")
    assert full.outcome is DerivationOutcome.DERIVED
    assert full.dag.fired[0].premises == {"a", "b"}


def test_target_in_base_is_trivially_derived():
    report = derive([], {"a"}, "a")
    assert report.outcome is DerivationOutcome.DERIVED
    assert report.dag.fired == ()


def test_missing_atoms_are_named():
    """The AND-side epistemic cut: what the space would have to acquire."""
    report = derive([E("e", {"lemma1", "lemma2"}, "goal")], {"lemma1"}, "goal")
    assert report.outcome is DerivationOutcome.UNDERIVABLE_IN_PRINCIPLE
    assert set(report.missing) == {"lemma2", "goal"}


def test_authority_blocked_is_distinguished_and_names_the_edges():
    """Derivable with weaker licensing is a different finding from underivable."""
    edges = [E("weak", {"a"}, "goal", licensed_at=1)]
    blocked = derive(edges, {"a"}, "goal", required_authority=5)
    assert blocked.outcome is DerivationOutcome.AUTHORITY_BLOCKED
    assert blocked.blocked_edges == ("weak",)

    ok = derive(edges, {"a"}, "goal", required_authority=1)
    assert ok.outcome is DerivationOutcome.DERIVED


def test_obstructed_derivation_is_refused_with_a_control():
    """Obstruction-blindness is unsound for AND-composition too."""
    edges = [E("e1", {"x"}, "y"), E("e2", {"x", "y"}, "z"), E("e3", {"z"}, "goal")]
    obstruction = Obstruction("OBS", frozenset({"x", "y", "z"}))

    refused = derive(edges, {"x"}, "goal", obstructions=[obstruction])
    assert refused.outcome is DerivationOutcome.OBSTRUCTED
    assert refused.realized_obstructions == ("OBS",)

    control = derive(edges, {"x"}, "goal")
    assert control.outcome is DerivationOutcome.DERIVED


def test_cheaper_producer_is_preferred():
    edges = [
        E("dear", {"a"}, "b", cost=5.0),
        E("cheap", {"a"}, "b", cost=1.0),
        E("out", {"b"}, "goal", cost=1.0),
    ]
    report = derive(edges, {"a"}, "goal")
    assert report.outcome is DerivationOutcome.DERIVED
    assert {e.edge_id for e in report.dag.fired} == {"cheap", "out"}
    assert report.dag.cost == 2.0


def test_minimality_is_not_claimed():
    report = derive([E("e", {"a"}, "goal")], {"a"}, "goal")
    assert report.minimal_cost_claimed is False


def test_edge_may_not_presuppose_its_conclusion():
    with pytest.raises(ValueError, match="presuppose"):
        E("circular", {"a", "goal"}, "goal")


def test_derivation_grants_no_authority():
    report = derive([E("e", {"a"}, "goal")], {"a"}, "goal")
    assert report.grants_scientific_authority is False


# --- real data: the repository's own kernel-checked mathematics --------------------


def _lean_dependency_hypergraph() -> tuple[list[HyperEdge], frozenset[str]]:
    """Parse formal/RaklFormal.lean into a real dependency hypergraph.

    Every theorem in that file is kernel-checked and axiom-free (enforced in CI),
    so each hyperedge below is a *verified* inference step: premises = the other
    theorems referenced in the proof body, conclusion = the theorem itself.
    """
    source = (REPO / "formal" / "RaklFormal.lean").read_text(encoding="utf-8")
    heads = [
        (m.start(), m.group(1))
        for m in re.finditer(r"^theorem\s+([A-Za-z_][A-Za-z0-9_.']*)", source, re.M)
    ]
    names = [name for _, name in heads]
    edges: list[HyperEdge] = []
    base: set[str] = set()
    for index, (start, name) in enumerate(heads):
        end = heads[index + 1][0] if index + 1 < len(heads) else len(source)
        body = source[start:end]
        deps = frozenset(
            other
            for other in names
            if other != name and re.search(rf"\b{re.escape(other)}\b", body)
        )
        if deps:
            edges.append(HyperEdge(f"lean::{name}", deps, name, 1.0, 9))
        else:
            base.add(name)
    return edges, frozenset(base)


def test_real_lean_theorem_is_rederived_mechanically():
    """Mechanical traversal of a kernel-verified space re-derives a real theorem."""
    edges, base = _lean_dependency_hypergraph()
    assert len(edges) + len(base) >= 20, "parser lost the development; investigate"

    report = derive(
        edges, base, "no_pairwise_predicate_decides_global_realizability",
        required_authority=9,
    )
    assert report.outcome is DerivationOutcome.DERIVED
    fired = {e.conclusion: e for e in report.dag.fired}
    premises = fired["no_pairwise_predicate_decides_global_realizability"].premises
    assert {"covers_agree_on_pairwise_data", "covers_differ_on_global_realizability"} <= premises


def test_the_lean_graph_genuinely_contains_and_composition():
    """At least one real theorem needs several theorem-premises at once —
    the case that is inexpressible as an OR-route."""
    edges, _ = _lean_dependency_hypergraph()
    assert any(len(e.premises) >= 2 for e in edges)


def test_underivability_is_real_on_the_lean_graph():
    """Remove a load-bearing base lemma and the target must become underivable,
    with the missing lemma named. The no-alarm direction of the real-data test."""
    edges, base = _lean_dependency_hypergraph()
    weakened = base - {"covers_agree_on_pairwise_data"}
    report = derive(
        edges, weakened, "no_pairwise_predicate_decides_global_realizability",
        required_authority=9,
    )
    assert report.outcome is DerivationOutcome.UNDERIVABLE_IN_PRINCIPLE
    assert "covers_agree_on_pairwise_data" in report.missing
