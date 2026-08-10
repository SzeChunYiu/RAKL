"""Tiny regression helpers for C013 quotient blow-up monotonicity.

The constructors lift complement edges and explicit cover pairs through row and
column quotient maps. They are intended for exact small-instance falsification
with ``full_cover_oracle.py``. They do not prove asymptotic cover or circuit
lower bounds.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


Edge = tuple[int, int]
Pair = tuple[frozenset[Edge], frozenset[Edge]]


def _validate_labels(base_vertices: int, labels: Sequence[int], name: str) -> None:
    if base_vertices < 2:
        raise ValueError("base_vertices must be at least 2")
    if not labels:
        raise ValueError(f"{name} labels must be non-empty")
    if any(label < 0 or label >= base_vertices for label in labels):
        raise ValueError(f"{name} label lies outside the base vertex set")
    if set(labels) != set(range(base_vertices)):
        raise ValueError(f"{name} labels must be surjective onto every base vertex")


def blowup_complement(
    base_vertices: int,
    base_complement: set[Edge],
    left_labels: Sequence[int],
    right_labels: Sequence[int] | None = None,
) -> set[Edge]:
    """Lift a base complement through surjective left/right quotient maps."""

    if right_labels is None:
        right_labels = left_labels
    _validate_labels(base_vertices, left_labels, "left")
    _validate_labels(base_vertices, right_labels, "right")
    if not base_complement or len(base_complement) == base_vertices * base_vertices:
        raise ValueError("base graph must be nontrivial")
    if any(
        u < 0 or v < 0 or u >= base_vertices or v >= base_vertices
        for u, v in base_complement
    ):
        raise ValueError("base complement edge lies outside the base graph")

    return {
        (u, v)
        for u, left_label in enumerate(left_labels)
        for v, right_label in enumerate(right_labels)
        if (left_label, right_label) in base_complement
    }


def lift_pair_family(
    pairs: Iterable[Pair],
    left_labels: Sequence[int],
    right_labels: Sequence[int] | None = None,
) -> tuple[Pair, ...]:
    """Lift explicit base-complement pair sets through quotient maps."""

    if right_labels is None:
        right_labels = left_labels

    def lift(edges: frozenset[Edge]) -> frozenset[Edge]:
        return frozenset(
            (u, v)
            for u, left_label in enumerate(left_labels)
            for v, right_label in enumerate(right_labels)
            if (left_label, right_label) in edges
        )

    return tuple((lift(e_set), lift(h_set)) for e_set, h_set in pairs)


def neq_two_vertex_complement() -> set[Edge]:
    """Complement of the one-bit NEQ graph."""

    return {(0, 0), (1, 1)}


def neq_two_vertex_pair_witness() -> tuple[Pair, ...]:
    return ((frozenset({(0, 0)}), frozenset({(1, 1)})),)


def eq_two_vertex_complement() -> set[Edge]:
    """Complement of the one-bit EQ graph."""

    return {(0, 1), (1, 0)}


def eq_two_vertex_pair_witness() -> tuple[Pair, ...]:
    return ((frozenset({(0, 1)}), frozenset({(1, 0)})),)
