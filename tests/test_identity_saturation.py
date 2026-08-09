import pytest

from rakl.identity import EvidenceIdentityLedger, EvidenceIdentityRelation
from rakl.identity_saturation import IdentityAwareSaturationTracker
from rakl.saturation import ResearchRound, SaturationState, SaturationTracker


def _rr(round_id, objects=(), *, lineage=(), independent=True, complete=True):
    return ResearchRound.from_objects(
        round_id,
        "A",
        f"ctx-{round_id}",
        objects,
        independent=independent,
        evidence_lineage=lineage,
        lineage_complete=complete,
    )


def _primed_tracker(ledger, *, required=3):
    tracker = IdentityAwareSaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=required,
        identity_ledger=ledger,
    )
    tracker.record(_rr("seed", {"M1"}, independent=False, complete=False))
    tracker.record(_rr("flat", {"M1"}, independent=False, complete=False))
    return tracker


def test_exact_aliases_collapse_deterministically_regardless_of_relation_order():
    relations = [
        ("doi:10.x/data", "url:https://repo/data", "IDENTICAL_TO"),
        ("url:https://repo/data", "ark:123", "IDENTICAL_TO"),
    ]
    forward = EvidenceIdentityLedger.from_relations(relations)
    reverse = EvidenceIdentityLedger.from_relations(reversed(relations))

    expected = "ark:123"
    for ledger in (forward, reverse):
        assert ledger.canonical_id("doi:10.x/data") == expected
        assert ledger.canonical_id("url:https://repo/data") == expected
        assert ledger.canonical_id("ark:123") == expected


def test_versions_share_family_ancestry_without_becoming_exact_identity():
    ledger = EvidenceIdentityLedger.from_relations(
        [
            ("dataset:v1", "dataset:family", EvidenceIdentityRelation.VERSION_OF),
            ("dataset:v2", "dataset:family", EvidenceIdentityRelation.VERSION_OF),
        ]
    )

    v1 = ledger.normalize_lineage({"dataset:v1"})
    v2 = ledger.normalize_lineage({"dataset:v2"})

    assert v1.canonical_entities == frozenset({"dataset:v1"})
    assert v2.canonical_entities == frozenset({"dataset:v2"})
    assert v1.canonical_entities != v2.canonical_entities
    assert "dataset:family" in v1.ancestry_tokens & v2.ancestry_tokens


def test_derived_artifacts_retain_transitive_common_ancestry():
    ledger = EvidenceIdentityLedger.from_relations(
        [
            ("derived:a", "intermediate:a", "DERIVED_FROM"),
            ("intermediate:a", "raw:root", "DERIVED_FROM"),
            ("derived:b", "raw:root", "DERIVED_FROM"),
        ]
    )

    left = ledger.normalize_lineage({"derived:a"})
    right = ledger.normalize_lineage({"derived:b"})

    assert "raw:root" in left.ancestry_tokens
    assert "raw:root" in right.ancestry_tokens
    assert left.canonical_entities == frozenset({"derived:a"})


def test_possible_alias_is_partial_identification_not_guessed_identity():
    ledger = EvidenceIdentityLedger.from_relations(
        [("dataset:a", "dataset:b", "POSSIBLE_ALIAS")]
    )

    resolution = ledger.normalize_lineage({"dataset:a"})

    assert not resolution.identity_resolved
    assert resolution.unresolved_identity_pairs == (("dataset:a", "dataset:b"),)
    assert resolution.canonical_entities == frozenset({"dataset:a"})


def test_cyclic_version_or_derivation_ancestry_is_rejected():
    with pytest.raises(ValueError, match="acyclic"):
        EvidenceIdentityLedger.from_relations(
            [
                ("A", "B", "DERIVED_FROM"),
                ("B", "A", "VERSION_OF"),
            ]
        )


def test_alias_hidden_shared_dataset_cannot_fake_independent_saturation():
    ledger = EvidenceIdentityLedger.from_relations(
        [("doi:10.x/data", "url:https://repo/data", "IDENTICAL_TO")]
    )
    tracker = _primed_tracker(ledger, required=2)
    tracker.record(_rr("i1", {"M1"}, lineage={"doi:10.x/data"}))
    tracker.record(_rr("i2", {"M1"}, lineage={"url:https://repo/data"}))

    diagnostic = tracker.independence_diagnostic()

    assert diagnostic["status"] == "DEPENDENCE_IDENTIFIED"
    assert diagnostic["conservative_full_independent_rounds"] == 1
    assert diagnostic["overlap_pairs"][0]["shared_lineage"] == ["doi:10.x/data"]
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_1


def test_version_siblings_share_ancestry_for_full_independence_credit():
    ledger = EvidenceIdentityLedger.from_relations(
        [
            ("dataset:v1", "dataset:family", "VERSION_OF"),
            ("dataset:v2", "dataset:family", "VERSION_OF"),
        ]
    )
    tracker = _primed_tracker(ledger, required=2)
    tracker.record(_rr("i1", {"M1"}, lineage={"dataset:v1"}))
    tracker.record(_rr("i2", {"M1"}, lineage={"dataset:v2"}))

    diagnostic = tracker.independence_diagnostic()

    assert diagnostic["conservative_full_independent_rounds"] == 1
    assert diagnostic["canonical_entities"]["i1"] != diagnostic["canonical_entities"]["i2"]
    assert "dataset:family" in diagnostic["overlap_pairs"][0]["shared_lineage"]


def test_derived_siblings_share_raw_ancestor_for_independence_credit():
    ledger = EvidenceIdentityLedger.from_relations(
        [
            ("derived:a", "raw:root", "DERIVED_FROM"),
            ("derived:b", "raw:root", "DERIVED_FROM"),
        ]
    )
    tracker = _primed_tracker(ledger, required=2)
    tracker.record(_rr("i1", {"M1"}, lineage={"derived:a"}))
    tracker.record(_rr("i2", {"M1"}, lineage={"derived:b"}))

    diagnostic = tracker.independence_diagnostic()

    assert diagnostic["conservative_full_independent_rounds"] == 1
    assert "raw:root" in diagnostic["overlap_pairs"][0]["shared_lineage"]


def test_unresolved_alias_blocks_full_independence_certificate():
    ledger = EvidenceIdentityLedger.from_relations(
        [("dataset:a", "dataset:b", "POSSIBLE_ALIAS")]
    )
    tracker = _primed_tracker(ledger, required=1)
    tracker.record(_rr("i1", {"M1"}, lineage={"dataset:a"}))
    tracker.record(_rr("i2", {"M1"}, lineage={"dataset:b"}))

    diagnostic = tracker.independence_diagnostic()

    assert diagnostic["status"] == "PARTIALLY_IDENTIFIED_LINEAGE"
    assert diagnostic["conservative_full_independent_rounds"] == 0
    assert diagnostic["unknown_or_incomplete_lineage_rounds"] == ["i1", "i2"]
    assert tracker.state == SaturationState.SAME_CONTEXT_PLATEAU


def test_disjoint_resolved_entities_still_receive_full_credit():
    tracker = _primed_tracker(EvidenceIdentityLedger(), required=3)
    for idx, lineage in enumerate(({"D1"}, {"D2"}, {"D3"}), start=1):
        tracker.record(_rr(f"i{idx}", {"M1"}, lineage=lineage))

    diagnostic = tracker.independence_diagnostic()

    assert diagnostic["status"] == "FULL_LINEAGE_DISJOINT"
    assert diagnostic["conservative_full_independent_rounds"] == 3
    assert tracker.state == SaturationState.SATURATED_SCOPED


def test_incumbent_tracker_behavior_is_unchanged_without_identity_ledger():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=2,
    )
    tracker.record(_rr("seed", {"M1"}, independent=False, complete=False))
    tracker.record(_rr("flat", {"M1"}, independent=False, complete=False))
    tracker.record(_rr("i1", {"M1"}, lineage={"D1"}))
    tracker.record(_rr("i2", {"M1"}, lineage={"D2"}))

    assert tracker.independent_flat_count() == 2
    assert tracker.state == SaturationState.SATURATED_SCOPED


def test_new_semantic_object_reopens_even_with_alias_normalization():
    ledger = EvidenceIdentityLedger.from_relations(
        [("dataset:a", "dataset:b", "IDENTICAL_TO")]
    )
    tracker = _primed_tracker(ledger, required=1)
    tracker.record(_rr("i1", {"M1"}, lineage={"dataset:a"}))
    assert tracker.state == SaturationState.SATURATED_SCOPED

    tracker.record(_rr("i2", {"M1", "NEW_MECHANISM"}, lineage={"dataset:b"}))
    assert tracker.state == SaturationState.ACTIVE_NON_FLAT
