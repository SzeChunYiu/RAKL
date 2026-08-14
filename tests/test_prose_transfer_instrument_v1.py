"""Invariants the prose-transfer instrument must hold before any score means anything.

These are the checks whose absence let two predecessor instruments report
extraction scores while their text was inert.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace

import pytest

from rakl.objective_transfer_benchmark import Decision
from rakl.prose_transfer_extractor_v1 import full_prose_extractor
from rakl.prose_transfer_instrument_v1 import (
    _FILLER,
    _HEDGE,
    _QUAL_ABOVE,
    _QUAL_BELOW,
    _QUAL_COMPLETE,
    _QUAL_INCOMPLETE,
    _QUAL_PRECOND_FAILS,
    _QUAL_PRECOND_HOLDS,
    COORDINATES,
    UNKNOWN_MODES,
    generate,
)

BANKS = (
    _QUAL_BELOW,
    _QUAL_ABOVE,
    _QUAL_COMPLETE,
    _QUAL_INCOMPLETE,
    _QUAL_PRECOND_HOLDS,
    _QUAL_PRECOND_FAILS,
    _HEDGE,
    _FILLER,
)


def test_candidate_surface_carries_no_pre_parsed_answer():
    """The defect shared by both refuted predecessors."""
    tasks, _ = generate(11, n_per_cell=2, bank="heldout")
    for task in tasks:
        assert task.public == {}


def test_gold_is_a_function_of_what_the_text_says():
    tasks, specs = generate(12, n_per_cell=3, bank="heldout")
    for spec in specs:
        for name in COORDINATES:
            cs = spec.coords[name]
            if cs.mode in UNKNOWN_MODES:
                assert cs.decision is Decision.CANNOT_CHECK
            else:
                assert cs.decision is (Decision.ACCEPT if cs.value else Decision.REJECT)
        expected = Decision.ACCEPT
        decisions = [spec.coords[c].decision for c in COORDINATES]
        if Decision.REJECT in decisions:
            expected = Decision.REJECT
        elif Decision.CANNOT_CHECK in decisions:
            expected = Decision.CANNOT_CHECK
        assert spec.gold is expected
    assert len(tasks) == len(specs)


@pytest.mark.parametrize("bank", BANKS)
def test_dev_and_heldout_banks_are_disjoint(bank):
    assert set(bank["dev"]).isdisjoint(set(bank["heldout"]))


def test_destroying_the_text_destroys_the_arm():
    """Probe G as a unit test: the acceptance condition, not an afterthought."""
    tasks, specs = generate(13, n_per_cell=4, bank="heldout")
    gold = [s.gold for s in specs]
    clean = [full_prose_extractor(t) for t in tasks]

    rng = random.Random(5)
    words = ("zqx", "vpl", "mtr", "kbd", "wfn")
    scrambled = [
        replace(
            t,
            source_text=" ".join(rng.choice(words) for _ in t.source_text.split()),
            target_text=" ".join(rng.choice(words) for _ in t.target_text.split()),
        )
        for t in tasks
    ]
    noisy = [full_prose_extractor(t) for t in scrambled]

    n = len(tasks)
    clean_exact = sum(g is p for g, p in zip(gold, clean)) / n
    noisy_exact = sum(g is p for g, p in zip(gold, noisy)) / n
    assert clean_exact - noisy_exact > 0.5, (clean_exact, noisy_exact)


def test_every_coordinate_is_the_sole_discriminator_somewhere():
    """Probe-F repair: no arm may be zeroed by construction."""
    _, specs = generate(14, n_per_cell=24, bank="heldout")
    sole = Counter(s.sole_discriminator for s in specs if s.sole_discriminator)
    assert set(sole) == set(COORDINATES), sole
    assert min(sole.values()) > 0


def test_no_arm_can_reach_the_latent_spec_from_a_task():
    tasks, _ = generate(15, n_per_cell=2, bank="heldout")
    fields = set(vars(tasks[0]))
    assert fields == {"item_id", "family", "source_text", "target_text", "public"}
