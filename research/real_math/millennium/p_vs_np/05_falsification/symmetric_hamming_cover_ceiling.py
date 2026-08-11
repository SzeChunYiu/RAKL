"""Exact finite witnesses for C017 symmetric-Hamming cover pruning.

The construction explicitly carries each Boolean set with its complement, so it
never treats negation of an intermediate set as free.  It computes coordinate
XOR bits, population count via carry-save plus ripple full adders, then decodes
all weight classes by a prefix tree.  These finite set equalities are calibration
for the proof draft, not an asymptotic proof certificate.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable


Edge = tuple[int, int]


@dataclass(frozen=True)
class SignalPair:
    value: frozenset[Edge]
    complement: frozenset[Edge]


@dataclass(frozen=True)
class SymmetricHammingWitness:
    coordinates: int
    accepted_weights: frozenset[int]
    accepted: frozenset[Edge]
    direct_accepted: frozenset[Edge]
    weight_bits: tuple[SignalPair, ...]
    intersection_count: int
    full_adder_count: int
    decoder_intersections: int


def _ambient(t: int) -> frozenset[Edge]:
    if t < 1:
        raise ValueError("t must be positive")
    if t > 6:
        raise ValueError("finite calibration guard: use t <= 6")
    n = 1 << t
    return frozenset((x, y) for x in range(n) for y in range(n))


def _validate_pair(pair: SignalPair, ambient: frozenset[Edge]) -> None:
    if pair.value.intersection(pair.complement):
        raise AssertionError("signal and complement overlap")
    if pair.value.union(pair.complement) != ambient:
        raise AssertionError("signal pair does not partition ambient space")


def _intersection2(a: frozenset[Edge], b: frozenset[Edge]) -> frozenset[Edge]:
    return a.intersection(b)


def _intersection3(
    a: frozenset[Edge], b: frozenset[Edge], c: frozenset[Edge]
) -> frozenset[Edge]:
    # Two counted pairwise intersections.
    return a.intersection(b).intersection(c)


def _full_adder(
    a: SignalPair,
    b: SignalPair,
    c: SignalPair,
    ambient: frozenset[Edge],
) -> tuple[SignalPair, SignalPair, int]:
    """Return (sum_pair, carry_pair, counted_intersections=22)."""

    av, an = a.value, a.complement
    bv, bn = b.value, b.complement
    cv, cn = c.value, c.complement

    sum_value = frozenset().union(
        _intersection3(av, bv, cv),
        _intersection3(av, bn, cn),
        _intersection3(an, bv, cn),
        _intersection3(an, bn, cv),
    )
    sum_complement = frozenset().union(
        _intersection3(an, bn, cn),
        _intersection3(an, bv, cv),
        _intersection3(av, bn, cv),
        _intersection3(av, bv, cn),
    )

    carry_value = frozenset().union(
        _intersection2(av, bv),
        _intersection2(av, cv),
        _intersection2(bv, cv),
    )
    carry_complement = frozenset().union(
        _intersection2(an, bn),
        _intersection2(an, cn),
        _intersection2(bn, cn),
    )

    sum_pair = SignalPair(sum_value, sum_complement)
    carry_pair = SignalPair(carry_value, carry_complement)
    _validate_pair(sum_pair, ambient)
    _validate_pair(carry_pair, ambient)
    return sum_pair, carry_pair, 22


def _xor_signal_pair(
    t: int, bit: int, ambient: frozenset[Edge]
) -> tuple[SignalPair, int]:
    if not (0 <= bit < t):
        raise ValueError("bit is outside coordinate range")

    x_one = frozenset(edge for edge in ambient if (edge[0] >> bit) & 1)
    x_zero = ambient.difference(x_one)
    y_one = frozenset(edge for edge in ambient if (edge[1] >> bit) & 1)
    y_zero = ambient.difference(y_one)

    xor_value = (x_one.union(y_one)).intersection(x_zero.union(y_zero))
    xor_complement = (x_one.union(y_zero)).intersection(x_zero.union(y_one))
    pair = SignalPair(frozenset(xor_value), frozenset(xor_complement))
    _validate_pair(pair, ambient)
    return pair, 2


def _population_count_bits(
    t: int, ambient: frozenset[Edge]
) -> tuple[tuple[SignalPair, ...], int, int]:
    """Return binary Hamming-weight bits, intersections, and full-adder count."""

    # One explicit empty-set construction x & ~x is charged once.  The ambient
    # universe is the free union x | ~x.  The Python sets below are the exact
    # finite realizations of those constants.
    zero = SignalPair(frozenset(), ambient)
    intersection_count = 1

    columns: dict[int, list[SignalPair]] = defaultdict(list)
    for bit in range(t):
        pair, cost = _xor_signal_pair(t, bit, ambient)
        columns[0].append(pair)
        intersection_count += cost

    full_adders = 0
    column = 0
    while column <= max(columns):
        while len(columns[column]) >= 3:
            a = columns[column].pop()
            b = columns[column].pop()
            c = columns[column].pop()
            sum_pair, carry_pair, cost = _full_adder(a, b, c, ambient)
            columns[column].append(sum_pair)
            columns[column + 1].append(carry_pair)
            intersection_count += cost
            full_adders += 1
        column += 1

    # At most two signals remain in each column.  Ripple-add those two rows.
    highest_column = max(columns)
    carry = zero
    bits: list[SignalPair] = []
    for column in range(highest_column + 1):
        items = columns[column]
        a = items[0] if items else zero
        b = items[1] if len(items) > 1 else zero
        sum_pair, carry, cost = _full_adder(a, b, carry, ambient)
        bits.append(sum_pair)
        intersection_count += cost
        full_adders += 1

    # Carry is the next binary bit.  Keep it only when it is not identically 0.
    if carry.value:
        bits.append(carry)

    # Exact finite semantic check.
    for edge in ambient:
        encoded = sum(
            (1 << bit) if edge in pair.value else 0
            for bit, pair in enumerate(bits)
        )
        expected = (edge[0] ^ edge[1]).bit_count()
        if encoded != expected:
            raise AssertionError("population-count construction is incorrect")

    return tuple(bits), intersection_count, full_adders


def _decode_weight_classes(
    bits: tuple[SignalPair, ...],
    t: int,
    ambient: frozenset[Edge],
) -> tuple[dict[int, frozenset[Edge]], int]:
    if not bits:
        raise AssertionError("population count produced no bits")

    # One-bit prefixes need no new operation because both sets already exist.
    prefixes: dict[int, frozenset[Edge]] = {
        0: bits[0].complement,
        1: bits[0].value,
    }
    count = 0

    for bit_index in range(1, len(bits)):
        next_prefixes: dict[int, frozenset[Edge]] = {}
        pair = bits[bit_index]
        for prefix_value, prefix_set in prefixes.items():
            next_prefixes[prefix_value] = prefix_set.intersection(pair.complement)
            next_prefixes[prefix_value | (1 << bit_index)] = prefix_set.intersection(
                pair.value
            )
            count += 2
        prefixes = next_prefixes

    # Retain exact valid Hamming weights only.  Invalid binary leaves are empty.
    classes = {weight: prefixes.get(weight, frozenset()) for weight in range(t + 1)}
    union = frozenset().union(*classes.values())
    if union != ambient:
        raise AssertionError("valid Hamming-weight classes do not cover ambient space")
    for left in range(t + 1):
        for right in range(left + 1, t + 1):
            if classes[left].intersection(classes[right]):
                raise AssertionError("Hamming-weight classes overlap")
    return classes, count


def symmetric_hamming_witness(
    t: int, accepted_weights: Iterable[int]
) -> SymmetricHammingWitness:
    ambient = _ambient(t)
    weights = frozenset(accepted_weights)
    if any(weight < 0 or weight > t for weight in weights):
        raise ValueError("accepted weights must lie in [0,t]")

    bits, count, full_adders = _population_count_bits(t, ambient)
    classes, decoder_count = _decode_weight_classes(bits, t, ambient)
    accepted = frozenset().union(*(classes[weight] for weight in weights))
    direct = frozenset(
        edge
        for edge in ambient
        if (edge[0] ^ edge[1]).bit_count() in weights
    )
    if accepted != direct:
        raise AssertionError("decoded symmetric predicate disagrees with direct evaluation")

    total = count + decoder_count
    if total > 80 * t:
        raise AssertionError("finite witness exceeded conservative C017 ceiling")

    return SymmetricHammingWitness(
        coordinates=t,
        accepted_weights=weights,
        accepted=accepted,
        direct_accepted=direct,
        weight_bits=bits,
        intersection_count=total,
        full_adder_count=full_adders,
        decoder_intersections=decoder_count,
    )


def residue_weights(t: int, modulus: int, residues: Iterable[int]) -> frozenset[int]:
    if modulus < 1:
        raise ValueError("modulus must be positive")
    residue_set = {residue % modulus for residue in residues}
    return frozenset(
        weight for weight in range(t + 1) if weight % modulus in residue_set
    )


def threshold_weights(t: int, threshold: int) -> frozenset[int]:
    if threshold < 0 or threshold > t + 1:
        raise ValueError("threshold must lie in [0,t+1]")
    return frozenset(range(threshold, t + 1))


if __name__ == "__main__":
    for bits in range(1, 6):
        weights = residue_weights(bits, max(1, bits), {0})
        witness = symmetric_hamming_witness(bits, weights)
        print(bits, witness.intersection_count, sorted(weights))
