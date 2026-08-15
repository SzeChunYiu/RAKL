"""Surface-form canonicalization of evidence source identifiers.

Motivating defect (Paper I, ``NEG-p1-source-monitoring-repetition-attack``):
a source-monitoring repetition attack succeeded because the identity normalizer
in front of the authority ledger was a blanket string rewrite
(``lower().replace("?v=", "").replace("doi:", "").replace("arxiv:", "")``).
That rewrite both **under-merged** (query-string and prefix variants of one DOI
stayed distinct, so ten submissions of one source looked like eight independent
supports) and could **over-merge** (``doi:10.1000/x?v=1`` and the genuinely
distinct ``doi:10.1000/x1`` both rewrite to ``10.1000/x1``).

This module replaces that rewrite with a scheme-aware canonicalizer. Its design
rule is that a transformation is applied only where the identifier scheme's own
specification says the transformed part is not identity-bearing:

* **DOI** handles are case-insensitive and carry no query string or fragment, so
  case folding and query/fragment stripping are sound for DOIs.
* **arXiv** identifiers are case-insensitive and carry an explicit ``vN``
  version suffix. The version is *not* dropped from the canonical id — two
  versions stay distinct entities linked by a ``VERSION_OF`` edge to a shared
  lineage root.
* **Everything else is opaque.** A bare URL keeps its case, path, query and
  fragment byte-exact, because ``?id=1`` and ``?id=2`` are identity-bearing
  there. Opaque identifiers are only whitespace-trimmed.

Cross-venue identity (a DOI and its arXiv preprint) is *not* derivable from the
identifier strings and is never guessed here. It is supplied as a declared
mapping record and carries provenance ``declared_record``, kept separate from
edges minted syntactically (provenance ``syntactic``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from .identity import EvidenceIdentityEdge, EvidenceIdentityLedger, EvidenceIdentityRelation

__all__ = [
    "CanonicalSourceIdentifier",
    "SourceIdentityMapping",
    "SourceIdentityResolution",
    "canonicalize_source_identifier",
    "resolve_source_identities",
]


_DOI_BODY = re.compile(r"^10\.\d{4,9}/\S+$")
_DOI_PREFIX = re.compile(r"^(doi|info:doi/|doi\.org/)\s*[:/]?\s*", re.IGNORECASE)
_DOI_HOST = re.compile(r"^https?://(dx\.)?doi\.org/", re.IGNORECASE)

# Modern (0704.0001) and legacy (math.GT/0309136) arXiv identifiers.
_ARXIV_MODERN = re.compile(r"^(?P<root>\d{4}\.\d{4,5})(?:v(?P<version>\d+))?$")
_ARXIV_LEGACY = re.compile(
    r"^(?P<root>[a-z][a-z-]*(?:\.[a-z]{2})?/\d{7})(?:v(?P<version>\d+))?$",
    re.IGNORECASE,
)
_ARXIV_PREFIX = re.compile(r"^arxiv\s*[:/]\s*", re.IGNORECASE)
_ARXIV_HOST = re.compile(r"^https?://(www\.)?arxiv\.org/(abs|pdf)/", re.IGNORECASE)

_TRAILING_PUNCT = ".,;:"


@dataclass(frozen=True)
class CanonicalSourceIdentifier:
    """One submitted identifier resolved to a canonical form.

    ``canonical_id`` is the identity used for independent-support counting.
    ``lineage_root`` is the work-level root: equal to ``canonical_id`` except for
    a versioned arXiv identifier, whose root is the version-stripped id.
    ``scheme`` is one of ``doi``, ``arxiv`` or ``opaque``.
    """

    raw: str
    canonical_id: str
    scheme: str
    lineage_root: str
    version: str | None = None

    @property
    def is_versioned(self) -> bool:
        return self.canonical_id != self.lineage_root


@dataclass(frozen=True)
class SourceIdentityMapping:
    """A declared cross-venue identity record.

    Cross-venue sameness (preprint <-> version of record) cannot be read off the
    identifier strings, so it must be asserted by a record. ``relation`` defaults
    to ``VERSION_OF``: the preprint is a version of the published work, which
    shares lineage without collapsing the two into one entity.

    ``scope`` says what the record is about. ``"work"`` (the default, and how
    published DOI<->arXiv records are actually expressed) resolves both endpoints
    to their lineage roots, so the statement covers every version of the work.
    ``"version"`` binds the exact submitted versions only, for records that
    genuinely single out one version; the bound version then has two ancestors
    (its syntactic arXiv root and the declared counterpart), so the resolution is
    deliberately multi-root — a version-scoped record is not evidence that the
    *work* is the same. The repetition-attack repair uses ``"work"`` only.
    """

    left: str
    right: str
    relation: EvidenceIdentityRelation = EvidenceIdentityRelation.VERSION_OF
    scope: str = "work"
    provenance: str = "declared_record"

    def __post_init__(self) -> None:
        if self.scope not in {"work", "version"}:
            raise ValueError("declared mapping scope must be 'work' or 'version'")


@dataclass(frozen=True)
class SourceIdentityResolution:
    canonical: tuple[CanonicalSourceIdentifier, ...]
    distinct_canonical: frozenset[str]
    distinct_roots: frozenset[str]
    syntactic_edges: tuple[EvidenceIdentityEdge, ...]
    declared_edges: tuple[EvidenceIdentityEdge, ...]

    @property
    def distinct_canonical_count(self) -> int:
        return len(self.distinct_canonical)

    @property
    def distinct_root_count(self) -> int:
        return len(self.distinct_roots)


def _strip_trailing_punct(value: str) -> str:
    while value and value[-1] in _TRAILING_PUNCT:
        value = value[:-1]
    return value


def _try_doi(value: str) -> str | None:
    """Return the canonical ``doi:...`` form, or ``None`` if not a DOI.

    A string counts as a DOI only when it is hosted at doi.org/dx.doi.org or
    carries an explicit ``doi``/``info:doi`` prefix, *and* the remaining body
    matches the ``10.NNNN/suffix`` DOI grammar. A bare ``10.NNNN/suffix`` body is
    also accepted. Anything else stays opaque, so ordinary URLs never inherit
    DOI's case-folding and query-stripping rules.
    """

    body = value
    explicit = False
    if _DOI_HOST.match(body):
        body = _DOI_HOST.sub("", body)
        explicit = True
    elif _DOI_PREFIX.match(body):
        body = _DOI_PREFIX.sub("", body)
        explicit = True

    body = body.strip()
    # A DOI carries no query string or fragment; both are transport decoration.
    body = body.split("?", 1)[0].split("#", 1)[0]
    body = _strip_trailing_punct(body.strip())
    if not body:
        return None
    if not _DOI_BODY.match(body):
        return None
    if not explicit and not body.lower().startswith("10."):
        return None
    # DOI handles are case-insensitive (ISO 26324 comparison rules).
    return f"doi:{body.lower()}"


def _try_arxiv(value: str) -> tuple[str, str, str | None] | None:
    """Return ``(canonical_id, lineage_root, version)`` for an arXiv identifier."""

    body = value
    if _ARXIV_HOST.match(body):
        body = _ARXIV_HOST.sub("", body)
        if body.lower().endswith(".pdf"):
            body = body[: -len(".pdf")]
    elif _ARXIV_PREFIX.match(body):
        body = _ARXIV_PREFIX.sub("", body)
    else:
        return None

    body = body.strip()
    # arXiv ids carry no query string or fragment.
    body = body.split("?", 1)[0].split("#", 1)[0]
    body = _strip_trailing_punct(body.strip())
    if not body:
        return None

    match = _ARXIV_MODERN.match(body) or _ARXIV_LEGACY.match(body)
    if match is None:
        return None
    root = match.group("root").lower()
    version = match.group("version")
    canonical = f"arxiv:{root}" if version is None else f"arxiv:{root}v{version}"
    return canonical, f"arxiv:{root}", version


def canonicalize_source_identifier(raw: str) -> CanonicalSourceIdentifier:
    """Canonicalize one submitted source identifier.

    Raises ``ValueError`` on an empty identifier. Never merges two identifiers
    that differ outside a scheme-declared non-identity-bearing part.
    """

    if raw is None or not raw.strip():
        raise ValueError("source identifier cannot be empty")
    value = raw.strip()

    doi = _try_doi(value)
    if doi is not None:
        return CanonicalSourceIdentifier(raw=raw, canonical_id=doi, scheme="doi", lineage_root=doi)

    arxiv = _try_arxiv(value)
    if arxiv is not None:
        canonical, root, version = arxiv
        return CanonicalSourceIdentifier(
            raw=raw, canonical_id=canonical, scheme="arxiv", lineage_root=root, version=version
        )

    # Opaque: preserve every byte after whitespace trimming. Case, path, query
    # and fragment are all potentially identity-bearing here.
    return CanonicalSourceIdentifier(
        raw=raw, canonical_id=value, scheme="opaque", lineage_root=value
    )


def resolve_source_identities(
    identifiers: Iterable[str],
    declared_mappings: Sequence[SourceIdentityMapping] = (),
) -> SourceIdentityResolution:
    """Canonicalize submitted identifiers and resolve them to lineage roots.

    Syntactic ``VERSION_OF`` edges (arXiv ``vN`` -> version-stripped root) and
    ``declared_mappings`` are kept in separate tuples so a receipt can show which
    collapses were derivable from the identifier grammar and which required an
    externally supplied record.
    """

    canonical = tuple(canonicalize_source_identifier(item) for item in identifiers)
    if not canonical:
        raise ValueError("source identity resolution requires at least one identifier")

    syntactic: set[EvidenceIdentityEdge] = set()
    for entry in canonical:
        if entry.is_versioned:
            syntactic.add(
                EvidenceIdentityEdge(
                    entry.canonical_id, entry.lineage_root, EvidenceIdentityRelation.VERSION_OF
                )
            )

    declared: set[EvidenceIdentityEdge] = set()
    for mapping in declared_mappings:
        left_entry = canonicalize_source_identifier(mapping.left)
        right_entry = canonicalize_source_identifier(mapping.right)
        if mapping.scope == "work":
            left, right = left_entry.lineage_root, right_entry.lineage_root
        else:
            left, right = left_entry.canonical_id, right_entry.canonical_id
        if left == right:
            continue
        declared.add(EvidenceIdentityEdge(left, right, mapping.relation))

    syntactic_edges = tuple(sorted(syntactic))
    declared_edges = tuple(sorted(declared))
    ledger = EvidenceIdentityLedger.from_relations(syntactic_edges + declared_edges)

    distinct_canonical = frozenset(entry.canonical_id for entry in canonical)
    distinct_roots = ledger.ancestry_roots(distinct_canonical)

    return SourceIdentityResolution(
        canonical=canonical,
        distinct_canonical=distinct_canonical,
        distinct_roots=distinct_roots,
        syntactic_edges=syntactic_edges,
        declared_edges=declared_edges,
    )
