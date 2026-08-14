"""A deterministic narrative reducer: raw text -> ReducedStructure.

This is the registered reduction operator of the Paper II external-corpus epoch
(``research/paper2_external_corpus_v1/PROTOCOL.json``). It is deliberately the
simplest real reducer the framework interface admits: no trained weights, no
network, no corpus-specific vocabulary. Its job in that epoch is to be honestly
admissible under ``admit_reducer`` — it reads the text (scrambling the text
changes its output), it surfaces negation/contrast obstructions (the parity
calibration source yields one), and its validation labels are third-party — so
that whatever the confirmatory then measures is a fact about the programme's
extraction capability, not about the apparatus.

Frozen before first dataset contact. Proposal-only; grants no authority.
"""

from __future__ import annotations

import hashlib
import re

from .structure_space import ReducedStructure
from .support_solver import Atom, Obstruction, SupportEdge, SupportStructure

#: Frozen stopword list. Small on purpose: the reducer must not smuggle in a
#: tuned vocabulary. Function words and copulas only.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then else when while of to in on at by for with from
    as is are was were be been being am do does did done have has had having
    will would shall should can could may might must not no nor so than that
    this these those there here it its it's he she they them his her their our
    your my we you i me him us who whom which what where why how all any both
    each few more most other some such only own same too very s t just don now
    """.split()
)

#: Frozen negation/contrast markers. A sentence containing one of these and at
#: least two role tokens is read as declaring a joint incompatibility among the
#: roles it mentions — the reducer's obstruction-harvest rule.
CONTRAST_MARKERS: frozenset[str] = frozenset(
    {"no", "not", "never", "cannot", "however", "but", "differs", "unless",
     "fails", "without", "neither", "nothing", "none"}
)

MAX_ROLES = 12
RELATION_WINDOW = 4

_SENTENCE_SPLIT = re.compile(r"[.!?;]+")
_TOKEN = re.compile(r"[a-z]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    """Stopword-filtered content tokens of length >= 3, in order."""
    return [t for t in _tokens(text) if t not in STOPWORDS and len(t) >= 3]


def reduce_narrative(text: str) -> ReducedStructure:
    """Reduce one narrative to a support structure. Deterministic; fail-closed.

    Empty or content-free text yields an empty-role structure — the downstream
    witness arm treats that as insufficient evidence (CANNOT_CHECK), never as a
    licence.
    """
    counts: dict[str, int] = {}
    for token in content_tokens(text):
        counts[token] = counts.get(token, 0) + 1
    # Top-MAX_ROLES by frequency, alphabetical tie-break: deterministic.
    roles = frozenset(
        sorted(counts, key=lambda t: (-counts[t], t))[:MAX_ROLES]
    )

    relations: set[tuple[str, str]] = set()
    obstructions: list[Obstruction] = []
    for index, sentence in enumerate(_SENTENCE_SPLIT.split(text.lower())):
        sentence_tokens = _tokens(sentence)
        role_positions = [
            (position, token)
            for position, token in enumerate(sentence_tokens)
            if token in roles
        ]
        for (p1, t1), (p2, t2) in zip(role_positions, role_positions[1:]):
            if t1 != t2 and p2 - p1 <= RELATION_WINDOW:
                relations.add((t1, t2))
        sentence_roles = frozenset(token for _, token in role_positions)
        if len(sentence_roles) >= 2 and any(
            token in CONTRAST_MARKERS for token in sentence_tokens
        ):
            obstructions.append(
                Obstruction(
                    obstruction_id=f"contrast::{index}",
                    cover=sentence_roles,
                    detail=sentence.strip()[:160],
                )
            )

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    atoms = tuple(Atom(atom_id=role) for role in sorted(roles))
    edges = tuple(
        SupportEdge(source=s, target=t, cost=1.0, licensed_at=0)
        for s, t in sorted(relations)
    )
    structure = SupportStructure(
        structure_id=f"narrative::{digest[:16]}",
        atoms=atoms,
        edges=edges,
        obstructions=tuple(obstructions),
    )
    return ReducedStructure(
        structure=structure,
        roles=roles,
        relations=frozenset(relations),
        provenance=f"sha256:{digest}",
    )
