"""Tests for the framework layer ladder.

The live ladder is well-formed, which proves little on its own. Most of these
tests inject the ways a declared "progressive build" can be a fiction — a forward
dependency, a re-introduced atom, a layer standing on nothing — and require each
to be caught.
"""

from __future__ import annotations

import copy

import pytest

from rakl.framework_ladder import (
    implied_paper_dependencies,
    layers,
    load_ladder,
    missing_paper_citations,
    paper_layer_span,
    structural_problems,
    unhoused_layers,
)


@pytest.fixture
def ladder() -> dict:
    return load_ladder()


def test_live_ladder_is_a_wellfounded_progressive_build(ladder):
    assert structural_problems(ladder) == ()


def test_every_layer_has_a_paper(ladder):
    """An unhoused layer is a gap in the programme, not a filing detail."""
    assert unhoused_layers(ladder) == ()


def test_every_layer_states_a_benefit_obligation(ladder):
    for layer in layers(ladder):
        assert layer.benefit_obligation.strip(), f"{layer.layer_id} has no benefit obligation"


def test_every_layer_says_what_it_newly_expresses(ladder):
    """A layer that adds no expressive power is not a layer."""
    seen = set()
    for layer in layers(ladder):
        assert len(layer.expresses) > 60, f"{layer.layer_id}: thin expressiveness claim"
        assert layer.expresses not in seen
        seen.add(layer.expresses)


def test_the_measured_citation_gap_is_reported(ladder):
    """The finding this ladder exists to make precise."""
    gaps = missing_paper_citations(ladder)
    assert any(g.startswith("II depends on I") for g in gaps), gaps


def test_paper_covering_its_own_dependency_owes_no_citation(ladder):
    """Regression: the first implementation reported a spurious III->IV edge.

    Paper III covers L6-METHOD-EVOLUTION *and* L7-ASSIMILATION, so it carries its
    own foundation for L7 and owes Paper IV no citation for it. Only a paper
    standing on a layer it does not itself cover incurs the edge.
    """
    edges = implied_paper_dependencies(ladder)
    span = paper_layer_span(ladder)
    for downstream, upstream in edges:
        shared = set(span[downstream]) & set(span[upstream])
        for layer in layers(ladder):
            if layer.layer_id in span[downstream]:
                for dep in layer.depends_on:
                    if dep in span[downstream]:
                        assert dep not in shared or downstream != upstream
    assert ("III", "IV") not in edges


# --- the checker must be able to fail ----------------------------------------------


def test_forward_dependency_is_caught(ladder):
    """A layer depending on one above it makes the build order a fiction."""
    broken = copy.deepcopy(ladder)
    broken["layers"][1]["depends_on"] = ["L7-ASSIMILATION"]
    problems = structural_problems(broken)
    assert any("forward dependency" in p for p in problems)


def test_unknown_dependency_is_caught(ladder):
    broken = copy.deepcopy(ladder)
    broken["layers"][2]["depends_on"] = ["L99-DOES-NOT-EXIST"]
    assert any("unknown layer" in p for p in structural_problems(broken))


def test_reintroduced_atom_is_caught(ladder):
    """An atom introduced twice means the layers are not disjoint contributions."""
    broken = copy.deepcopy(ladder)
    first_atom = broken["layers"][0]["atoms_introduced"][0]
    broken["layers"][3]["atoms_introduced"] = list(
        broken["layers"][3]["atoms_introduced"]
    ) + [first_atom]
    assert any("re-introduces atom" in p for p in structural_problems(broken))


def test_non_base_layer_standing_on_nothing_is_caught(ladder):
    broken = copy.deepcopy(ladder)
    broken["layers"][4]["depends_on"] = []
    assert any("declares no dependency" in p for p in structural_problems(broken))


def test_missing_benefit_obligation_is_caught(ladder):
    broken = copy.deepcopy(ladder)
    broken["layers"][2]["benefit_obligation"] = "   "
    assert any("no benefit obligation" in p for p in structural_problems(broken))


def test_unhoused_layer_is_caught(ladder):
    broken = copy.deepcopy(ladder)
    broken["layers"][4]["papers_covering"] = []
    assert unhoused_layers(broken) == (broken["layers"][4]["layer_id"],)


def test_a_realized_citation_is_not_reported_as_missing(ladder):
    """No-alarm case: satisfy the II->I edge and it must stop being reported."""
    fixed = copy.deepcopy(ladder)
    fixed["measured_paper_coupling"]["edges"]["II"]["I"] = 3
    assert not any(g.startswith("II depends on I") for g in missing_paper_citations(fixed))


def test_ladder_grants_no_authority(ladder):
    assert ladder["grants_scientific_authority"] is False
