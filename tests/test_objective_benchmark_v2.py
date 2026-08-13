"""Instrument-correctness tests for the six-family objective transfer extension.

These are instrument tests only. They use a non-registered instrument seed and
compute no confirmatory statistic.
"""
from __future__ import annotations

import json

import rakl.objective_transfer_benchmark as B
import rakl.objective_transfer_benchmark_v2 as V
from rakl.objective_transfer_benchmark_v2 import (
    Decision,
    FAMILIES,
    NEW_FAMILIES,
    extract,
    generate,
    mechanism_predict,
    mutate_hidden_metadata,
    verify,
)

INSTRUMENT_SEED = 20260813


def test_six_families_and_all_strata_are_constructible() -> None:
    tasks = generate(INSTRUMENT_SEED, 2, True)
    assert set(FAMILIES) == {t.family for t in tasks}
    assert len(FAMILIES) == 6
    for fam in FAMILIES:
        strata = {t.item_type for t in tasks if t.family == fam}
        assert strata == set(V.ALL_ITEM_TYPES)


def test_frozen_four_families_are_bit_identical_to_the_frozen_generator() -> None:
    """The extension is additive: it must not perturb the frozen four families."""
    v2 = [t for t in generate(4321, 3, True) if t.family in B.FAMILIES]
    v1 = B.generate(4321, 3, True)
    assert sorted(v2, key=lambda t: t.item_id) == sorted(v1, key=lambda t: t.item_id)
    for t in v1:
        assert verify(t) == B.verify(t)
        assert extract(t) == B.extract(t)


def test_generator_is_deterministic_and_gold_is_balanced() -> None:
    a = generate(1234, 4, True)
    b = generate(1234, 4, True)
    assert a == b
    counts = {d: 0 for d in Decision}
    for t in a:
        counts[verify(t).decision] += 1
    assert counts[Decision.ACCEPT] == counts[Decision.REJECT]
    assert counts[Decision.CANNOT_CHECK] > 0


def test_gold_never_depends_on_hidden_metadata() -> None:
    for t in generate(INSTRUMENT_SEED, 2, True):
        assert verify(mutate_hidden_metadata(t)) == verify(t)
        assert extract(mutate_hidden_metadata(t)) == extract(t)


def test_named_strata_carry_the_registered_gold_semantics() -> None:
    tasks = generate(INSTRUMENT_SEED, 3, True)
    expected = {
        "VALID_DISTANT_TRANSFER": Decision.ACCEPT,
        "VALID_NEAR_CONTROL": Decision.ACCEPT,
        "SEMANTIC_NEAR_MISS_INVALID_TRANSFER": Decision.REJECT,
        "DIRECTION_REVERSED_INVALID": Decision.REJECT,
        "BOUNDARY_QOI_MISMATCH": Decision.REJECT,
        "INVALID_DISTANT_CONTROL": Decision.REJECT,
        "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK": Decision.CANNOT_CHECK,
    }
    for t in tasks:
        assert verify(t).decision is expected[t.item_type], (t.family, t.item_type)


def test_full_applicability_contract_matches_the_exact_verifier_in_all_six_families() -> None:
    for t in generate(INSTRUMENT_SEED, 3, True):
        assert extract(t).decision is verify(t).decision, (t.family, t.item_type)


def test_mechanism_only_projection_is_informative_but_not_degenerate() -> None:
    """The mechanism arm must be neither perfect nor a constant strategy."""
    tasks = generate(INSTRUMENT_SEED, 4, True)
    for fam in NEW_FAMILIES:
        sub = [t for t in tasks if t.family == fam]
        preds = {mechanism_predict(t) for t in sub}
        assert len(preds) > 1, f"{fam} mechanism arm is a constant strategy"
        exact = sum(mechanism_predict(t) is verify(t).decision for t in sub) / len(sub)
        assert 0.3 < exact < 1.0, (fam, exact)
        rejects = [t for t in sub if verify(t).decision is Decision.REJECT]
        false_accept = sum(mechanism_predict(t) is Decision.ACCEPT for t in rejects) / len(rejects)
        assert 0.0 < false_accept < 1.0, (fam, false_accept)


def test_hard_decoys_are_hard_and_distant_controls_are_easy() -> None:
    """SEMANTIC_NEAR_MISS must be invisible to the mechanism projection; the
    INVALID_DISTANT_CONTROL stratum must be a genuine mechanism-level defect."""
    tasks = generate(INSTRUMENT_SEED, 3, True)
    for fam in NEW_FAMILIES:
        near = [t for t in tasks if t.family == fam
                and t.item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER"]
        far = [t for t in tasks if t.family == fam
               and t.item_type == "INVALID_DISTANT_CONTROL"]
        assert near and far
        assert all(mechanism_predict(t) is Decision.ACCEPT for t in near)
        assert all(mechanism_predict(t) is Decision.REJECT for t in far)


def test_no_length_cheat_between_valid_and_invalid_items() -> None:
    """Paper IV audit finding: gold must not be readable off payload length."""
    balance = V.surface_length_balance(generate(INSTRUMENT_SEED, 4, True))
    for fam, row in balance.items():
        assert row["abs_relative_gap"] < 0.02, (fam, row)


def test_surface_similarity_is_decorrelated_from_gold_in_every_family() -> None:
    tasks = generate(INSTRUMENT_SEED, 4, True)
    for fam, row in V.permutation_semantic_decorrelation(tasks, reps=600).items():
        assert abs(row["mean_diff"]) < 0.06, (fam, row)
        assert row["permutation_p"] > 0.05, (fam, row)


def test_lexical_control_stays_near_chance_on_decidable_items() -> None:
    tasks = generate(INSTRUMENT_SEED, 5, True)
    gold = {t.item_id: verify(t).decision for t in tasks}
    threshold = V.fit_threshold(tasks, gold)
    known = [t for t in tasks if gold[t.item_id] is not Decision.CANNOT_CHECK]
    acc = sum(V.lexical_predict(t, threshold) is gold[t.item_id] for t in known) / len(known)
    assert 0.35 <= acc <= 0.75, acc


def test_constant_and_family_label_strategies_fail() -> None:
    tasks = generate(INSTRUMENT_SEED, 4, True)
    gold = [verify(t).decision for t in tasks]
    for const in Decision:
        assert sum(g is const for g in gold) / len(gold) < 0.6


def test_new_family_verifiers_reject_for_the_stated_reason() -> None:
    """The verifier trace must name the coordinate that actually failed."""
    tasks = generate(INSTRUMENT_SEED, 2, True)
    reasons = {(t.family, t.item_type): verify(t).trace[0].split(":")[0]
               for t in tasks if t.family in NEW_FAMILIES}
    assert reasons[("sched", "SEMANTIC_NEAR_MISS_INVALID_TRANSFER")] == "precedence_violated"
    assert reasons[("sched", "DIRECTION_REVERSED_INVALID")] == "precedence_violated"
    assert reasons[("sched", "INVALID_DISTANT_CONTROL")] == "deadline_exceeded"
    assert reasons[("stat", "SEMANTIC_NEAR_MISS_INVALID_TRANSFER")] == "target_derived_value"
    assert reasons[("stat", "DIRECTION_REVERSED_INVALID")] == "conditioning_reversed"
    assert reasons[("stat", "INVALID_DISTANT_CONTROL")] == "parameter_out_of_support"


def test_candidate_visible_payload_fits_the_frozen_prompt_budget() -> None:
    """The frozen comparator truncates public facts at 1500 chars; nothing may be
    silently cut off in the new families."""
    for t in generate(INSTRUMENT_SEED, 2, True):
        assert len(json.dumps(t.public, sort_keys=True)) <= 1500, t.family


def test_new_families_are_structurally_distinct_from_the_frozen_four() -> None:
    tasks = generate(INSTRUMENT_SEED, 1, True)
    keys = {}
    for fam in FAMILIES:
        t = next(x for x in tasks if x.family == fam)
        keys[fam] = frozenset(t.public["target"].keys())
    for fam in NEW_FAMILIES:
        for old in B.FAMILIES:
            assert keys[fam] != keys[old]


def test_sign_test_arithmetic_matches_the_registered_target() -> None:
    sign_test = V.two_sided_sign_test
    # Paper II's stated four-family value, and the registered six-family target.
    assert abs(sign_test(4, 0) - 0.125) < 1e-12
    assert abs(sign_test(6, 0) - 0.03125) < 1e-12
    assert abs(sign_test(0, 6) - 0.03125) < 1e-12
    assert abs(sign_test(5, 1) - 0.21875) < 1e-12
    assert abs(sign_test(3, 3) - 1.0) < 1e-12
    assert sign_test(0, 0) == 1.0
    # Ties are dropped, reducing the effective n.
    assert abs(sign_test(4, 0, ties=2) - 0.125) < 1e-12
