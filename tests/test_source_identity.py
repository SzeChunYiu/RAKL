"""Tests for scheme-aware source-identifier canonicalization.

Ordering mirrors the repair protocol: the no-false-merge and near-miss controls
are asserted before the attack-detection test, because a normalizer that
over-merges genuinely distinct sources is a worse defect than the attack it was
built to stop.
"""

from __future__ import annotations

import pytest

from rakl.identity import EvidenceIdentityLedger, EvidenceIdentityRelation
from rakl.source_identity import (
    SourceIdentityMapping,
    canonicalize_source_identifier,
    resolve_source_identities,
)

BASE_DOI = "doi:10.1038/s41586-019-1234-5"

BENIGN_DISTINCT = (
    BASE_DOI,
    "doi:10.1126/science.aaa1234",
    "arXiv:2401.00111v1",
    "arXiv:2312.09876v3",
    "https://example.org/dataset?id=1",
    "https://example.org/dataset?id=2",
    "isbn:978-0-13-235088-4",
    "https://records.example.org/Archive/Case-Alpha",
)

ATTACK_CORPUS = (
    BASE_DOI,
    f"{BASE_DOI}?v=1",
    f"{BASE_DOI}?v=2",
    "arXiv:1234.5678v1",
    BASE_DOI,
    f"{BASE_DOI}?v=3",
    "DOI: 10.1038/s41586-019-1234-5",
    f"{BASE_DOI}?v=4",
    f"{BASE_DOI}?v=5",
    "arXiv:1234.5678v1",
)


# --------------------------------------------------------------------------
# Controls: no false merges
# --------------------------------------------------------------------------


def test_benign_distinct_corpus_is_not_collapsed() -> None:
    resolution = resolve_source_identities(BENIGN_DISTINCT)
    assert resolution.distinct_canonical_count == len(BENIGN_DISTINCT)


@pytest.mark.parametrize(
    "left,right",
    [
        # adjacent DOIs
        (BASE_DOI, "doi:10.1038/s41586-019-1234-6"),
        # two arXiv papers by the same author, consecutive ids
        ("arXiv:2401.00111", "arXiv:2401.00112"),
        # identity-bearing URL query: NOT a DOI, so query survives
        ("https://example.org/paper?id=1", "https://example.org/paper?id=2"),
        # supplement suffix is part of the DOI
        (BASE_DOI, f"{BASE_DOI}.suppl"),
        # the pair the v1 normalizer over-merged
        ("doi:10.1000/x?v=1", "doi:10.1000/x1"),
        # opaque URL paths are case-sensitive
        (
            "https://records.example.org/Archive/Case-Alpha",
            "https://records.example.org/archive/case-alpha",
        ),
        # different arXiv archives
        ("arXiv:math.GT/0309136", "arXiv:math.AG/0309136"),
    ],
)
def test_near_miss_pairs_stay_separate(left: str, right: str) -> None:
    assert resolve_source_identities((left, right)).distinct_canonical_count == 2


def test_url_query_is_identity_bearing_for_opaque_sources() -> None:
    entry = canonicalize_source_identifier("https://example.org/paper?id=1#sec2")
    assert entry.scheme == "opaque"
    assert entry.canonical_id == "https://example.org/paper?id=1#sec2"


def test_non_doi_ten_dot_prefix_is_not_treated_as_doi() -> None:
    entry = canonicalize_source_identifier("https://example.org/10.1038/not-a-doi?id=1")
    assert entry.scheme == "opaque"
    assert entry.canonical_id.endswith("?id=1")


def test_arxiv_versions_are_distinct_entities_with_one_root() -> None:
    resolution = resolve_source_identities(("arXiv:2401.00111v1", "arXiv:2401.00111v2"))
    assert resolution.distinct_canonical_count == 2
    assert resolution.distinct_root_count == 1
    assert all(
        edge.relation is EvidenceIdentityRelation.VERSION_OF
        for edge in resolution.syntactic_edges
    )
    assert resolution.declared_edges == ()


# --------------------------------------------------------------------------
# Controls: trivially equivalent forms must collapse
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant",
    [
        BASE_DOI,
        "DOI: 10.1038/s41586-019-1234-5",
        "doi: 10.1038/S41586-019-1234-5",
        "10.1038/s41586-019-1234-5",
        "https://doi.org/10.1038/s41586-019-1234-5",
        "http://dx.doi.org/10.1038/s41586-019-1234-5",
        "https://doi.org/10.1038/s41586-019-1234-5#results",
        f"{BASE_DOI}?v=7",
        "  doi:10.1038/s41586-019-1234-5.  ",
        "info:doi/10.1038/s41586-019-1234-5",
    ],
)
def test_trivially_equivalent_doi_forms_share_one_canonical_id(variant: str) -> None:
    assert canonicalize_source_identifier(variant).canonical_id == BASE_DOI


@pytest.mark.parametrize(
    "variant",
    [
        "arXiv:1234.5678v1",
        "arxiv:1234.5678v1",
        "ARXIV: 1234.5678v1",
        "https://arxiv.org/abs/1234.5678v1",
        "https://arxiv.org/pdf/1234.5678v1.pdf",
    ],
)
def test_trivially_equivalent_arxiv_forms_share_one_canonical_id(variant: str) -> None:
    assert canonicalize_source_identifier(variant).canonical_id == "arxiv:1234.5678v1"


def test_empty_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonicalize_source_identifier("   ")


def test_canonicalization_is_idempotent() -> None:
    for raw in ATTACK_CORPUS + BENIGN_DISTINCT:
        once = canonicalize_source_identifier(raw).canonical_id
        assert canonicalize_source_identifier(once).canonical_id == once


# --------------------------------------------------------------------------
# Attack detection (asserted after the controls)
# --------------------------------------------------------------------------


def test_repetition_attack_collapses_to_two_canonical_sources() -> None:
    resolution = resolve_source_identities(ATTACK_CORPUS)
    assert resolution.distinct_canonical_count == 2
    assert resolution.distinct_canonical == frozenset({BASE_DOI, "arxiv:1234.5678v1"})


def test_repetition_attack_clears_the_unchanged_hard_gate() -> None:
    distinct = resolve_source_identities(ATTACK_CORPUS).distinct_canonical_count
    total = len(ATTACK_CORPUS)
    ratio = 1.0 - (distinct / total)
    # threshold copied from the frozen parent protocol; never modified here
    assert distinct < total
    assert ratio >= 0.5


def test_cross_venue_collapse_requires_a_declared_record() -> None:
    without = resolve_source_identities(ATTACK_CORPUS)
    assert without.distinct_root_count == 2  # DOI root and arXiv root stay separate

    with_record = resolve_source_identities(
        ATTACK_CORPUS,
        (SourceIdentityMapping(left="arXiv:1234.5678v1", right=BASE_DOI),),
    )
    assert with_record.distinct_root_count == 1
    assert with_record.declared_edges != ()


def test_declared_mapping_scope_version_binds_only_that_version() -> None:
    resolution = resolve_source_identities(
        ("arXiv:1234.5678v1", "arXiv:1234.5678v2", BASE_DOI),
        (
            SourceIdentityMapping(
                left="arXiv:1234.5678v2", right=BASE_DOI, scope="version"
            ),
        ),
    )
    # v1 still resolves to the bare arXiv root; only v2 was bound to the DOI
    assert "arxiv:1234.5678" in resolution.distinct_roots
    assert BASE_DOI in resolution.distinct_roots


def test_invalid_mapping_scope_is_rejected() -> None:
    with pytest.raises(ValueError):
        SourceIdentityMapping(left="a", right="b", scope="whatever")


# --------------------------------------------------------------------------
# Ledger extension
# --------------------------------------------------------------------------


def test_ancestry_roots_resolves_version_chains() -> None:
    ledger = EvidenceIdentityLedger.from_relations(
        [
            ("paper:v3", "paper:v2", EvidenceIdentityRelation.VERSION_OF),
            ("paper:v2", "paper:v1", EvidenceIdentityRelation.VERSION_OF),
        ]
    )
    assert ledger.ancestry_roots({"paper:v3", "paper:v2"}) == frozenset({"paper:v1"})


def test_ancestry_roots_keeps_unrelated_entities_separate() -> None:
    ledger = EvidenceIdentityLedger()
    assert ledger.ancestry_roots({"a", "b"}) == frozenset({"a", "b"})
