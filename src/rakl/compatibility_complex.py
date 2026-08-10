"""Honest name for the current atom/witness/path structure.

`TypedKnowledgeLattice` is retained for backward compatibility with the public RAKL API.
The implementation in `typed_lattice.py` does not by itself define an order-theoretic
lattice: it stores typed atoms, pairwise compatibility witnesses, and admissible
constructive paths. New code that depends only on those semantics should use
`TypedCompatibilityComplex`.

A mathematical lattice claim requires a separately declared scoped partial order and
verified meet/join or closure-system obligations.
"""

from .typed_lattice import (
    CompatibilityWitness,
    ConstructiveLatticePath,
    KnowledgeAtom,
    KnowledgeAtomKind,
    LatticeCompatibility,
    LatticeSynthesisSeed,
    TypedKnowledgeLattice,
    atoms_by_kind,
)

TypedCompatibilityComplex = TypedKnowledgeLattice

__all__ = [
    "CompatibilityWitness",
    "ConstructiveLatticePath",
    "KnowledgeAtom",
    "KnowledgeAtomKind",
    "LatticeCompatibility",
    "LatticeSynthesisSeed",
    "TypedCompatibilityComplex",
    "TypedKnowledgeLattice",
    "atoms_by_kind",
]
