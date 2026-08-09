import random

import pytest

from rakl.multires_memory import (
    MemoryView,
    MemoryViewKind,
    MemoryViewVerdict,
    SourcePin,
    canonical_source_closure,
    validate_memory_view,
)


def canonical(record_id: str, payload_hash: str | None = None, *, certs=()):
    return MemoryView(
        record_id=record_id,
        payload_hash=payload_hash or f"hash-{record_id}",
        kind=MemoryViewKind.CANONICAL,
        authority_certificates=tuple(certs),
    )


def pin(view: MemoryView) -> SourcePin:
    return SourcePin(view.record_id, view.payload_hash)


def test_canonical_leaf_is_valid_and_is_its_own_source_root():
    raw = canonical("raw")
    report = validate_memory_view("raw", [raw])
    assert report.verdict == MemoryViewVerdict.VALID_CANONICAL
    assert report.canonical_root_ids == ("raw",)


def test_pointer_backed_lossy_view_is_rehydratable_not_self_reconstructing():
    raw = canonical("raw")
    view = MemoryView(
        "summary",
        "hash-summary",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(raw),),
        transform_id="summarize-v1",
        erasure_tags=("exact-wording",),
    )
    report = validate_memory_view("summary", [view, raw])
    assert report.verdict == MemoryViewVerdict.SOURCE_REHYDRATABLE
    assert report.canonical_root_ids == ("raw",)


def test_lossy_view_cannot_claim_exact_reconstruction():
    raw = canonical("raw")
    with pytest.raises(ValueError, match="lossy views cannot claim exact reconstruction"):
        MemoryView(
            "summary",
            "hash-summary",
            MemoryViewKind.DERIVED_LOSSY,
            source_pins=(pin(raw),),
            transform_id="summarize-v1",
            erasure_tags=("detail",),
            reconstruction_verified=True,
            reconstruction_witness_id="witness",
        )


def test_dangling_source_fails_closed():
    view = MemoryView(
        "view",
        "hash-view",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("missing", "hash-missing"),),
        transform_id="normalize-v1",
    )
    report = validate_memory_view("view", [view])
    assert report.verdict == MemoryViewVerdict.INVALID
    assert "dangling_source:missing" in report.issues


def test_stale_source_hash_fails_closed():
    raw = canonical("raw", "current")
    view = MemoryView(
        "view",
        "hash-view",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("raw", "stale"),),
        transform_id="normalize-v1",
    )
    report = validate_memory_view("view", [raw, view])
    assert report.verdict == MemoryViewVerdict.INVALID
    assert "source_hash_mismatch:raw" in report.issues


def test_source_cycle_fails_closed():
    a = MemoryView(
        "a",
        "hash-a",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("b", "hash-b"),),
        transform_id="t",
    )
    b = MemoryView(
        "b",
        "hash-b",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("a", "hash-a"),),
        transform_id="t",
    )
    report = validate_memory_view("a", [a, b])
    assert report.verdict == MemoryViewVerdict.INVALID
    assert "source_cycle" in report.issues


def test_multilevel_view_reports_complete_canonical_source_closure():
    a = canonical("a")
    b = canonical("b")
    mid = MemoryView(
        "mid",
        "hash-mid",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(a), pin(b)),
        transform_id="summarize-v1",
        erasure_tags=("verbatim",),
    )
    top = MemoryView(
        "top",
        "hash-top",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(mid),),
        transform_id="abstract-v1",
        erasure_tags=("domain-detail",),
        required_canonical_ids=("a", "b"),
    )
    report = validate_memory_view("top", [top, b, mid, a])
    assert report.verdict == MemoryViewVerdict.SOURCE_REHYDRATABLE
    assert report.canonical_root_ids == ("a", "b")
    assert canonical_source_closure("top", [a, top, mid, b]) == ("a", "b")


def test_derived_view_cannot_mint_authority_certificate():
    raw = canonical("raw", certs=("SOURCE_SPAN_SUPPORT",))
    view = MemoryView(
        "view",
        "hash-view",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(pin(raw),),
        transform_id="normalize-v1",
        authority_certificates=("SOURCE_SPAN_SUPPORT", "MECHANISM_ANCESTRY_SUPPORTED"),
    )
    report = validate_memory_view("view", [raw, view])
    assert report.verdict == MemoryViewVerdict.INVALID
    assert "authority_escalation:MECHANISM_ANCESTRY_SUPPORTED" in report.issues


def test_derived_view_may_preserve_but_not_strengthen_existing_authority():
    raw = canonical("raw", certs=("SOURCE_SPAN_SUPPORT",))
    view = MemoryView(
        "view",
        "hash-view",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(pin(raw),),
        transform_id="normalize-v1",
        authority_certificates=("SOURCE_SPAN_SUPPORT",),
    )
    assert validate_memory_view("view", [view, raw]).valid


def test_contradiction_view_requires_both_registered_canonical_sides():
    side_a = canonical("side-a")
    side_b = canonical("side-b")
    both = MemoryView(
        "both",
        "hash-both",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(side_a), pin(side_b)),
        transform_id="contrast-v1",
        erasure_tags=("verbatim",),
        required_canonical_ids=("side-a", "side-b"),
    )
    report = validate_memory_view("both", [both, side_b, side_a])
    assert report.verdict == MemoryViewVerdict.SOURCE_REHYDRATABLE
    assert report.canonical_root_ids == ("side-a", "side-b")


def test_silently_dropped_contradiction_side_is_invalid():
    side_a = canonical("side-a")
    view = MemoryView(
        "summary",
        "hash-summary",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(side_a),),
        transform_id="contrast-v1",
        erasure_tags=("verbatim",),
        required_canonical_ids=("side-a", "side-b"),
    )
    report = validate_memory_view("summary", [side_a, view])
    assert report.verdict == MemoryViewVerdict.INVALID
    assert "required_canonical_unreachable:side-b" in report.issues


def test_verified_lossless_regeneration_requires_explicit_witness():
    raw = canonical("raw")
    view = MemoryView(
        "normalized",
        "hash-normalized",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(pin(raw),),
        transform_id="normalize-v1",
        reconstruction_verified=True,
        reconstruction_witness_id="replay-test-42",
    )
    report = validate_memory_view("normalized", [raw, view])
    assert report.verdict == MemoryViewVerdict.REGENERATION_VERIFIED


def test_transform_name_alone_does_not_claim_exact_regeneration():
    raw = canonical("raw")
    view = MemoryView(
        "normalized",
        "hash-normalized",
        MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(pin(raw),),
        transform_id="normalize-v1",
    )
    assert validate_memory_view("normalized", [raw, view]).verdict == MemoryViewVerdict.SOURCE_REHYDRATABLE


def test_negative_history_root_remains_reachable_through_current_view():
    old_refutation = canonical("old-refutation")
    current = canonical("current")
    view = MemoryView(
        "current-overview",
        "hash-overview",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(current), pin(old_refutation)),
        transform_id="overview-v1",
        erasure_tags=("verbatim",),
        required_canonical_ids=("old-refutation",),
    )
    report = validate_memory_view("current-overview", [view, current, old_refutation])
    assert report.verdict == MemoryViewVerdict.SOURCE_REHYDRATABLE
    assert "old-refutation" in report.canonical_root_ids


def test_validation_and_source_closure_are_deterministic_under_registry_permutation():
    a = canonical("a")
    b = canonical("b")
    view = MemoryView(
        "view",
        "hash-view",
        MemoryViewKind.DERIVED_LOSSY,
        source_pins=(pin(b), pin(a)),
        transform_id="summary-v1",
        erasure_tags=("detail",),
    )
    base = [a, b, view]
    expected = validate_memory_view("view", base)
    for seed in range(20):
        shuffled = list(base)
        random.Random(seed).shuffle(shuffled)
        actual = validate_memory_view("view", shuffled)
        assert actual.verdict == expected.verdict
        assert actual.canonical_root_ids == expected.canonical_root_ids
        assert actual.issues == expected.issues


def test_duplicate_record_identity_is_rejected():
    raw = canonical("raw")
    with pytest.raises(ValueError, match="duplicate memory view record_id"):
        validate_memory_view("raw", [raw, raw])
